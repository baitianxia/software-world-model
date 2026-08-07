from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import uuid

from swm_demo.artifact_contract import SourceCollection
from swm_demo.knowledge_engine import KnowledgeEngine
from swm_demo.knowledge_contract import KnowledgeBuildTarget
from swm_demo.knowledge_requirement import KnowledgeSufficiencyAssessment
from swm_demo.knowledge_update import (
    BuildIntent,
    CandidateBundle,
    InvestigationHandle,
    InvestigationState,
    KnowledgeUpdateResult,
)
from swm_demo.semantic_view import SemanticViewRegistry, StructureViewEngine
from swm_demo.source_integration import SourceAccessError, SourceIntegration
from swm_demo.storage import KnowledgeStoreError, SQLiteKnowledgeStore
from swm_demo.validation_profile import (
    mall_full_artifact_request,
    mall_full_knowledge_target,
)


class ApplicationError(RuntimeError):
    pass


@dataclass
class _InvestigationSession:
    intent: BuildIntent
    handle: InvestigationHandle
    previous_snapshot_id: str
    collection: SourceCollection | None = None


class ApplicationServices:
    """Entry-independent Management, Knowledge Update, and Knowledge Use cases."""

    def __init__(
        self,
        database: Path,
        knowledge_engine: KnowledgeEngine | None = None,
    ):
        self.store = SQLiteKnowledgeStore(database)
        self.knowledge_engine = knowledge_engine or KnowledgeEngine()
        self.knowledge_engine.bind_repository(self.store)
        self.source_integration = SourceIntegration(self.store)
        self.structure_view = StructureViewEngine(self.knowledge_engine)
        self.semantic_views = SemanticViewRegistry(self.knowledge_engine)
        self._investigations: dict[str, _InvestigationSession] = {}

    def close(self) -> None:
        self.store.close()

    def configure_scope(
        self,
        scope_id: str,
        name: str,
        source_path: Path,
        expected_revision: str | None = None,
    ) -> dict[str, object]:
        self.knowledge_engine.configure_scope(scope_id=scope_id, name=name)
        self.source_integration.bind_local_git(
            scope_id=scope_id,
            source_path=source_path,
            expected_revision=expected_revision,
        )
        return {
            "use_case": "Management.ConfigureKnowledgeScope",
            "scope_id": scope_id,
            "name": name,
            "source_path": str(source_path.resolve()),
            "expected_revision": expected_revision,
        }

    def update_knowledge(
        self, scope_id: str, build_profile: str = "structure-core"
    ) -> dict[str, object]:
        try:
            if build_profile == "structure-core":
                collection = self.source_integration.collect_structure_sources(scope_id)
                build_target = KnowledgeBuildTarget()
            elif build_profile == "full-validation":
                collection = self.source_integration.collect_sources(
                    scope_id, mall_full_artifact_request()
                )
                build_target = mall_full_knowledge_target()
            else:
                raise ApplicationError(f"unknown build profile: {build_profile}")
        except (KnowledgeStoreError, SourceAccessError) as error:
            raise ApplicationError(str(error)) from error

        snapshot_id = self.knowledge_engine.begin_update(
            scope_id, collection.revision
        )
        try:
            self.source_integration.record_artifacts(snapshot_id, collection)
            build = self.knowledge_engine.admit_and_publish(
                snapshot_id, collection, build_target
            )
            if build.errors or build.package is None:
                errors = build.errors or ("Knowledge Engine returned no package",)
                raise ApplicationError("knowledge admission failed:\n" + "\n".join(errors))
        except ApplicationError:
            raise
        except Exception as error:
            self.knowledge_engine.fail_update(snapshot_id, error)
            raise ApplicationError(f"Knowledge Update failed: {error}") from error

        counts = self.knowledge_engine.snapshot_counts(snapshot_id)
        return {
            "use_case": "KnowledgeUpdate.RebuildCurrentSnapshot",
            "scope_id": scope_id,
            "snapshot_id": snapshot_id,
            "revision": collection.revision,
            "status": "CURRENT",
            "build_profile": collection.build_profile,
            "diagnostic_count": len(build.diagnostics),
            "diagnostics": list(build.diagnostics),
            **counts,
        }

    def query_structure(self, scope_id: str) -> dict[str, object]:
        try:
            return self.structure_view.render(scope_id)
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def query_endpoint_structure(
        self, scope_id: str, endpoint_name: str
    ) -> dict[str, object]:
        try:
            return self.structure_view.endpoint_chain(scope_id, endpoint_name)
        except KnowledgeStoreError as error:
            raise ApplicationError(str(error)) from error

    def query_semantic_view(
        self, scope_id: str, view_name: str
    ) -> dict[str, object]:
        try:
            return self.semantic_views.render(view_name, scope_id)
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def explain_fact(self, scope_id: str, fact_id: str) -> dict[str, object]:
        try:
            return self.knowledge_engine.explain_fact(scope_id, fact_id)
        except KnowledgeStoreError as error:
            raise ApplicationError(str(error)) from error

    def explain_inference(
        self, scope_id: str, inference_id: str
    ) -> dict[str, object]:
        try:
            return self.knowledge_engine.explain_inference(scope_id, inference_id)
        except KnowledgeStoreError as error:
            raise ApplicationError(str(error)) from error

    def current_snapshot(self, scope_id: str) -> dict[str, object]:
        try:
            return self.knowledge_engine.current_snapshot(scope_id)
        except KnowledgeStoreError as error:
            raise ApplicationError(str(error)) from error

    def validate_sufficiency_assessment(
        self, assessment: KnowledgeSufficiencyAssessment
    ) -> dict[str, object]:
        try:
            return self.knowledge_engine.validate_sufficiency_assessment(assessment)
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def start_model_led_update(
        self, intent: BuildIntent, model_context_id: str
    ) -> InvestigationHandle:
        """Open task-time Investigation state without exposing a new module."""

        validation = self.validate_sufficiency_assessment(intent.assessment)
        if not validation["mechanically_valid"]:
            raise ApplicationError(
                "Build Intent assessment is not mechanically valid: "
                + "; ".join(str(item) for item in validation["errors"])
            )
        current = self.current_snapshot(intent.scope_id)
        if current["snapshot_id"] != intent.assessment.snapshot_id:
            raise ApplicationError("Build Intent is based on a stale Snapshot")
        if current["revision"] != intent.target_revision:
            raise ApplicationError(
                "Build Intent target revision differs from the current source context"
            )
        for kind, identifiers in (
            ("FACT", intent.build_target.premise_fact_ids),
            ("INFERENCE", intent.build_target.premise_inference_ids),
        ):
            if not identifiers:
                continue
            resolved = self.knowledge_engine.explain_formal_knowledge_batch(
                intent.scope_id,
                str(current["snapshot_id"]),
                kind,
                identifiers,
            )
            if resolved["missing_ids"]:
                raise ApplicationError(
                    "Build Intent formal premises are absent from its exact Base "
                    f"Snapshot: {resolved['missing_ids']}"
                )
        run_id = f"investigation:{uuid.uuid4()}"
        handle = InvestigationHandle(
            run_id=run_id,
            intent_id=intent.intent_id,
            model_context_id=model_context_id,
            state=InvestigationState.OPEN,
        )
        self._investigations[run_id] = _InvestigationSession(
            intent=intent,
            handle=handle,
            previous_snapshot_id=str(current["snapshot_id"]),
        )
        return handle

    def collect_investigation_sources(self, run_id: str) -> SourceCollection:
        session = self._open_investigation(run_id)
        try:
            collection = self.source_integration.collect_sources(
                session.intent.scope_id, session.intent.artifact_request
            )
        except (KnowledgeStoreError, SourceAccessError) as error:
            session.handle = replace(
                session.handle, state=InvestigationState.FAILED
            )
            raise ApplicationError(str(error)) from error
        if collection.revision != session.intent.target_revision:
            session.handle = replace(
                session.handle, state=InvestigationState.FAILED
            )
            raise ApplicationError(
                "Investigation source revision differs from the frozen Build Intent"
            )
        session.collection = collection
        return collection

    def investigation_formal_premises(
        self, run_id: str
    ) -> dict[str, object]:
        """Resolve only frozen, already-published premises from the exact Base."""

        session = self._open_investigation(run_id)
        current = self.current_snapshot(session.intent.scope_id)
        if current["snapshot_id"] != session.previous_snapshot_id:
            raise ApplicationError(
                "Investigation formal premises are based on a stale Snapshot"
            )
        resolved: dict[str, object] = {
            "snapshot_id": session.previous_snapshot_id,
            "facts": [],
            "inferences": [],
        }
        for kind, identifiers, key in (
            ("FACT", session.intent.build_target.premise_fact_ids, "facts"),
            (
                "INFERENCE",
                session.intent.build_target.premise_inference_ids,
                "inferences",
            ),
        ):
            if not identifiers:
                continue
            explained = self.knowledge_engine.explain_formal_knowledge_batch(
                session.intent.scope_id,
                session.previous_snapshot_id,
                kind,
                identifiers,
            )
            if explained["missing_ids"]:
                raise ApplicationError(
                    "Investigation formal premises disappeared from the exact Base "
                    f"Snapshot: {explained['missing_ids']}"
                )
            resolved[key] = explained["items"]
        return resolved

    def submit_investigation_candidates(
        self, run_id: str, bundle: CandidateBundle
    ) -> KnowledgeUpdateResult:
        session = self._open_investigation(run_id)
        intent = session.intent
        if bundle.intent_id != intent.intent_id or bundle.scope_id != intent.scope_id:
            raise ApplicationError("Candidate Bundle and Investigation identity differ")
        decided_need_ids = set(
            (*bundle.covered_need_ids, *bundle.unresolved_need_ids)
        )
        if decided_need_ids != set(intent.gap_need_ids):
            raise ApplicationError(
                "Candidate Bundle must account for every frozen Gap Need"
            )
        if bundle.unresolved_need_ids:
            return KnowledgeUpdateResult(
                intent_id=intent.intent_id,
                run_id=run_id,
                previous_snapshot_id=session.previous_snapshot_id,
                published_snapshot_id=None,
                status="NEEDS_MORE_KNOWLEDGE",
                admitted_reference_ids=(),
                rejected_candidate_ids=(),
                unresolved_need_ids=bundle.unresolved_need_ids,
            )
        collection = session.collection
        if collection is None:
            raise ApplicationError(
                "Investigation sources must be collected before Candidate submission"
            )
        session.handle = replace(
            session.handle, state=InvestigationState.PUBLISHING
        )
        snapshot_id = self.knowledge_engine.begin_update(
            intent.scope_id, collection.revision
        )
        try:
            self.source_integration.record_artifacts(snapshot_id, collection)
            build = self.knowledge_engine.admit_and_publish(
                snapshot_id,
                collection,
                intent.build_target,
                bundle,
                base_snapshot_id=session.previous_snapshot_id,
            )
        except Exception as error:
            session.handle = replace(
                session.handle, state=InvestigationState.FAILED
            )
            self.knowledge_engine.fail_update(snapshot_id, error)
            return KnowledgeUpdateResult(
                intent_id=intent.intent_id,
                run_id=run_id,
                previous_snapshot_id=session.previous_snapshot_id,
                published_snapshot_id=None,
                status="FAILED",
                admitted_reference_ids=(),
                rejected_candidate_ids=tuple(
                    sorted(
                        {
                            *(item.fact_id for item in bundle.fact_candidates),
                            *(
                                item.inference_id
                                for item in bundle.inference_candidates
                            ),
                        }
                    )
                ),
                unresolved_need_ids=intent.gap_need_ids,
            )
        if build.errors or build.package is None:
            session.handle = replace(
                session.handle, state=InvestigationState.FAILED
            )
            return KnowledgeUpdateResult(
                intent_id=intent.intent_id,
                run_id=run_id,
                previous_snapshot_id=session.previous_snapshot_id,
                published_snapshot_id=None,
                status="FAILED",
                admitted_reference_ids=(),
                rejected_candidate_ids=tuple(
                    sorted(
                        {
                            *(item.fact_id for item in bundle.fact_candidates),
                            *(
                                item.inference_id
                                for item in bundle.inference_candidates
                            ),
                        }
                    )
                ),
                unresolved_need_ids=intent.gap_need_ids,
            )
        admitted = {
            item.fact_id for item in bundle.fact_candidates
        } | {
            item.inference_id for item in bundle.inference_candidates
        }
        published_ids = {
            item.fact_id for item in build.package.facts
        } | {
            item.inference_id for item in build.package.inferences
        }
        session.handle = replace(
            session.handle, state=InvestigationState.PUBLISHED
        )
        return KnowledgeUpdateResult(
            intent_id=intent.intent_id,
            run_id=run_id,
            previous_snapshot_id=session.previous_snapshot_id,
            published_snapshot_id=snapshot_id,
            status="PUBLISHED",
            admitted_reference_ids=tuple(sorted(admitted & published_ids)),
            rejected_candidate_ids=tuple(sorted(admitted - published_ids)),
            unresolved_need_ids=(),
        )

    def abort_investigation(self, run_id: str) -> InvestigationHandle:
        session = self._open_investigation(run_id)
        session.handle = replace(session.handle, state=InvestigationState.ABORTED)
        return session.handle

    def investigation_handle(self, run_id: str) -> InvestigationHandle:
        session = self._investigations.get(run_id)
        if session is None:
            raise ApplicationError(f"Investigation does not exist: {run_id}")
        return session.handle

    def release_investigation(self, run_id: str) -> InvestigationHandle:
        """Discard source-bearing task state after a terminal investigation."""

        session = self._investigations.get(run_id)
        if session is None:
            raise ApplicationError(f"Investigation does not exist: {run_id}")
        if session.handle.state not in {
            InvestigationState.PUBLISHED,
            InvestigationState.FAILED,
            InvestigationState.ABORTED,
        }:
            raise ApplicationError(
                f"Investigation is not terminal: {run_id} "
                f"({session.handle.state.value})"
            )
        handle = session.handle
        del self._investigations[run_id]
        return handle

    def _open_investigation(self, run_id: str) -> _InvestigationSession:
        session = self._investigations.get(run_id)
        if session is None:
            raise ApplicationError(f"Investigation does not exist: {run_id}")
        if session.handle.state is not InvestigationState.OPEN:
            raise ApplicationError(
                f"Investigation is not OPEN: {run_id} ({session.handle.state.value})"
            )
        return session

    def open_knowledge_context(self, scope_id: str) -> dict[str, object]:
        """Open the fixed Snapshot context used by generic knowledge tools."""

        try:
            return self.knowledge_engine.open_knowledge_context(scope_id)
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def search_knowledge(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        query: str,
        match_mode: str = "CONTAINS",
        type_name: str | None = None,
        limit: int = 20,
        cursor: int = 0,
    ) -> dict[str, object]:
        try:
            return self.knowledge_engine.search_formal_knowledge(
                scope_id=scope_id,
                snapshot_token=snapshot_token,
                kind=kind,
                query=query,
                match_mode=match_mode,
                type_name=type_name,
                limit=limit,
                cursor=cursor,
            )
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def query_knowledge_neighborhood(
        self,
        scope_id: str,
        snapshot_token: str,
        entity_ids: tuple[str, ...],
        direction: str = "BOTH",
        predicates: tuple[str, ...] = (),
        limit: int = 100,
        cursor: int = 0,
    ) -> dict[str, object]:
        try:
            return self.knowledge_engine.read_formal_neighborhood(
                scope_id=scope_id,
                snapshot_token=snapshot_token,
                entity_ids=entity_ids,
                direction=direction,
                predicates=predicates,
                limit=limit,
                cursor=cursor,
            )
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error

    def explain_knowledge_batch(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        knowledge_ids: tuple[str, ...],
    ) -> dict[str, object]:
        try:
            return self.knowledge_engine.explain_formal_knowledge_batch(
                scope_id=scope_id,
                snapshot_token=snapshot_token,
                kind=kind,
                knowledge_ids=knowledge_ids,
            )
        except (KnowledgeStoreError, ValueError) as error:
            raise ApplicationError(str(error)) from error
