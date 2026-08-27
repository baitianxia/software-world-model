from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from software_world_model.application_services.java_source_semantics import (
    JavaSourceSemanticsError,
    JavaSourceSemanticsInput,
    evaluate_java_source_semantics,
)
from software_world_model.application_services.java_static_call import (
    JavaSourceEvidenceMetadata,
)
from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.world_model_answering import (
    WorldModelAnsweringService,
    WorldModelQueryPlanProposal,
    WorldModelQueryStepProposal,
)
from software_world_model.application_services.structure_read_bundle import (
    JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF,
    StructureBusinessDiscoveryRecallBinding,
    StructureBusinessDiscoveryRecallVerdict,
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
)
from software_world_model.application_services.structure_read_session import (
    StructureReadPurpose,
    StructureReadSessionService,
)
from software_world_model.application_services.structure_view import (
    StructureEntityArgument,
    StructureViewOperation,
    StructureViewService,
    _feature_tokens,
)
from software_world_model.ai_infrastructure.model_egress_gateway import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE,
)
from software_world_model.ai_infrastructure.versioned_world_model_answer_strategy import (
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_INVESTIGATION,
)
from software_world_model.application_services.maven_structure import GitEntryMetadata
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    IdempotencyKey,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    EntityType,
    JavaImplementationAtomKind,
    JavaSemanticDisposition,
    ObservationModality,
    RelationPredicate,
    StructureEvidence,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaDefinition,
)
from software_world_model.interface.world_model_product import (
    JAVA_SOURCE_SEMANTICS_PRODUCT_STRATEGY_REF,
    WorldModelProductAnswerService,
)
from software_world_model.interface.world_model_evaluation import (
    BOUNDED_WORLD_MODEL_EVALUATION_PAGE_FORMAT,
    world_model_evaluation_page_payload,
)
from software_world_model.interface.world_model_runtime_assets import (
    bounded_java_source_semantics_answer_workload,
)
from tests import test_structure_publication as _publication_tests
from tests.test_java_static_call import _snapshot_bundle


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_007"
    / "fixtures"
    / "development"
)
SOURCE_ROOT = "src/main/java"


def _stable(kind: str, value: str) -> StableId:
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[-32:]
    return StableId(f"{kind}_{suffix}")


def _content_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _fixture_input(
    revision: str = "visible-development",
    *,
    scope_id: StableId | None = None,
    source_binding_id: StableId | None = None,
) -> JavaSourceSemanticsInput:
    pairs = tuple(
        (path.relative_to(FIXTURE_ROOT).as_posix(), path.read_bytes())
        for path in sorted(FIXTURE_ROOT.rglob("*.java"))
    )
    source_context_id = _stable("source_context", revision)
    entries = {
        path: GitEntryMetadata(
            mode="100644",
            object_type="blob",
            object_id=hashlib.sha1(payload).hexdigest(),
        )
        for path, payload in pairs
    }
    source_evidence = {
        path: JavaSourceEvidenceMetadata(
            artifact_id=_stable("source_artifact", f"{revision}:{path}"),
            source_context_id=source_context_id,
            artifact_content_digest=_content_digest(payload),
            locator=path,
        )
        for path, payload in pairs
    }
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path, metadata in sorted(entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    tree_evidence = StructureEvidence.create(
        artifact_id=_stable("source_artifact", f"tree:{revision}"),
        source_context_id=source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=f"git-tree:{revision}:all",
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )
    return JavaSourceSemanticsInput(
        owning_scope_id=scope_id or _stable("scope", revision),
        source_binding_id=source_binding_id or _stable("binding", revision),
        source_revision=revision,
        knowledge_context_digest=digest_of(
            {"source_revision": revision, "profile": "java-source-semantics"}
        ),
        source_bytes=dict(pairs),
        git_entries=entries,
        source_evidence=source_evidence,
        tree_evidence=(tree_evidence,),
        logical_source_root=SOURCE_ROOT,
    )


def _replace_fixture_source(
    value: JavaSourceSemanticsInput, payload: bytes
) -> JavaSourceSemanticsInput:
    path = next(iter(value.source_bytes))
    entries = {
        path: replace(
            value.git_entries[path],
            object_id=hashlib.sha1(payload).hexdigest(),
        )
    }
    source_evidence = {
        path: replace(
            value.source_evidence[path],
            artifact_content_digest=_content_digest(payload),
        )
    }
    tree_excerpt = json.dumps(
        {
            "is_symlink": entries[path].is_symlink,
            "mode": entries[path].mode,
            "object_id": entries[path].object_id,
            "path": path,
            "type": entries[path].object_type,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    tree_payload = tree_excerpt.encode()
    previous = value.tree_evidence[0]
    tree_evidence = StructureEvidence.create(
        artifact_id=previous.artifact_id,
        source_context_id=previous.source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=previous.locator,
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )
    return replace(
        value,
        source_bytes={path: payload},
        git_entries=entries,
        source_evidence=source_evidence,
        tree_evidence=(tree_evidence,),
    )


def _method_signature(record: object) -> str:
    fields = record.root.root_fields
    parameters = ",".join(str(item) for item in fields["parameter_types"])
    return (
        f"{fields['declaring_type_qualified_name']}#"
        f"{fields['method_name']}({parameters})"
    )


class _QualifiedSemanticsFixtureModel:
    strategy_ref = JAVA_SOURCE_SEMANTICS_PRODUCT_STRATEGY_REF

    def __init__(
        self,
        *,
        search_terms: tuple[str, ...] = ("credentials", "failure", "session"),
    ) -> None:
        self.provider_call_count = 0
        self.network_operation_count = 0
        self.capabilities: list[str] = []
        self.sealed_inputs: list[object] = []
        self.search_terms = search_terms

    def propose(
        self,
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: tuple[str, ...] = (),
    ) -> object:
        del case_id
        self.provider_call_count += 1
        self.network_operation_count += 1
        self.capabilities.append(capability)
        self.sealed_inputs.append(sealed_input)
        if capability == IMPLEMENTATION_INVESTIGATION:
            step_index = sealed_input["step_index"]
            evidence_requests = (
                [
                    {
                        "operation": "method_implementations",
                        "relation_intent": None,
                    }
                ]
                if step_index == 1
                else list(
                    sealed_input["previous_result"]["evidence_requests"]
                )
            )
            base = {
                "step_index": step_index,
                "trace_digest": sealed_input["trace_digest"],
                "operation": "FINISH",
                "snapshot_id": None,
                "search_terms": [],
                "limit": None,
                "candidate_result_id": None,
                "candidate_result_digest": None,
                "method_refs": [],
                "entity_refs": [],
                "direction": None,
                "predicate": None,
                "max_depth": None,
                "max_paths": None,
                "max_expansions": None,
                "finish_reason": "typed-support-or-boundary-complete",
                "evidence_requests": evidence_requests,
            }
            if step_index == 1:
                return SimpleNamespace(
                    normalized_result={
                        **base,
                        "operation": "implementation_candidates",
                        "snapshot_id": sealed_input["read_authority"][
                            "snapshot_ids"
                        ][-1],
                        "search_terms": list(self.search_terms),
                        "limit": 5,
                        "finish_reason": None,
                    }
                )
            previous = sealed_input["previous_result"]
            if step_index == 2:
                if available_operations == ("FINISH",):
                    return SimpleNamespace(normalized_result=base)
                candidate_result = previous["results"][0]
                candidates = candidate_result["payload"]["candidates"]
                if candidates:
                    return SimpleNamespace(
                        normalized_result={
                            **base,
                            "operation": "method_implementations",
                            "candidate_result_id": candidate_result["result_id"],
                            "candidate_result_digest": candidate_result["digest"],
                            "method_refs": [
                                {
                                    "source_result_id": candidate_result[
                                        "result_id"
                                    ],
                                    "source_result_digest": candidate_result[
                                        "digest"
                                    ],
                                    "entity_root_id": item["method"]["root_id"],
                                    "entity_state_id": item["method"]["state_id"],
                                }
                                for item in candidates[:3]
                            ],
                            "finish_reason": None,
                        }
                    )
                raise AssertionError("zero candidates must schedule FINISH")
            return SimpleNamespace(
                normalized_result=base
            )
        if capability == IMPLEMENTATION_ANSWER_DRAFTING:
            disposition = sealed_input["assessment_disposition"]
            answer = (
                "凭据无效分支会记录失败并抛出异常；有效分支调用会话签发方法并返回其布尔结果。"
                if disposition == "SUPPORTED"
                else "正式实现索引没有候选，因此这是知识缺口。"
                if disposition == "KNOWLEDGE_GAP"
                else "候选不唯一，当前不能选择具体方法。"
            )
            return SimpleNamespace(
                normalized_result={
                    "disposition": disposition,
                    "answer": answer,
                    "step_result_ids": list(
                        sealed_input["authorized_step_result_ids"]
                    ),
                    "support_digests": list(
                        sealed_input["authorized_support_digests"]
                    ),
                    "gap_code": sealed_input["assessment_gap_code"],
                    "limitation_codes": list(
                        sealed_input["assessment_limitation_codes"]
                    ),
                }
            )
        if capability == IMPLEMENTATION_ANSWER_REVIEW:
            return SimpleNamespace(
                normalized_result={
                    "decision": "APPROVE",
                    "finding_codes": [],
                    "checked_need_ids": list(
                        sealed_input["required_checked_need_ids"]
                    ),
                    "checked_step_result_ids": list(
                        sealed_input["required_checked_step_result_ids"]
                    ),
                    "checked_support_digests": list(
                        sealed_input["required_checked_support_digests"]
                    ),
                }
            )
        raise AssertionError(f"unexpected capability: {capability}")


class _FormalSemanticsFixtureModel(_QualifiedSemanticsFixtureModel):
    def __init__(
        self,
        *,
        search_terms: tuple[str, ...] = ("credentials", "failure", "session"),
    ) -> None:
        super().__init__(search_terms=search_terms)
        self.audits: list[object] = []

    def propose(self, **arguments) -> object:
        proposal = super().propose(**arguments)
        ordinal = self.provider_call_count
        manifest_digest = digest_of({"formal-manifest": ordinal})
        output_digest = digest_of({"formal-output": ordinal})
        call_id = StableId(f"model_call_{ordinal:032x}")
        gateway_result = SimpleNamespace(
            call=SimpleNamespace(
                manifest_digest=manifest_digest,
                model_call_id=call_id,
                actual_model_fingerprint="glm-5.2",
            ),
            response=SimpleNamespace(output_digest=output_digest),
            eligibility=SimpleNamespace(
                digest=digest_of({"formal-eligibility": ordinal})
            ),
        )
        self.audits.append(
            SimpleNamespace(
                canonical_value=lambda ordinal=ordinal: {
                    "ordinal": ordinal,
                    "status": "RESULT",
                }
            )
        )
        return SimpleNamespace(
            normalized_result=proposal.normalized_result,
            capability=arguments["capability"],
            digest=digest_of(
                {
                    "formal-proposal": ordinal,
                    "capability": arguments["capability"],
                }
            ),
            gateway_result=gateway_result,
        )


class _InvalidReviewCodeFixtureModel(_QualifiedSemanticsFixtureModel):
    def propose(self, **arguments) -> object:
        proposal = super().propose(**arguments)
        if arguments["capability"] != IMPLEMENTATION_ANSWER_REVIEW:
            return proposal
        return SimpleNamespace(
            normalized_result={
                **proposal.normalized_result,
                "decision": "REJECT",
                "finding_codes": ["DRAFT_OMITS_QUERY_RESULT_ATOMS"],
            }
        )


class _MixedPositiveAndZeroCandidateFixtureModel(
    _QualifiedSemanticsFixtureModel
):
    def propose(self, **arguments) -> object:
        proposal = super().propose(**arguments)
        sealed_input = arguments["sealed_input"]
        if (
            arguments["capability"] == IMPLEMENTATION_INVESTIGATION
            and sealed_input["step_index"] == 2
        ):
            normalized = proposal.normalized_result
            return SimpleNamespace(
                normalized_result={
                    **normalized,
                    "operation": "implementation_candidates",
                    "snapshot_id": sealed_input["read_authority"][
                        "snapshot_ids"
                    ][-1],
                    "search_terms": ["definitelyAbsentFeature"],
                    "limit": 5,
                    "candidate_result_id": None,
                    "candidate_result_digest": None,
                    "method_refs": [],
                    "finish_reason": None,
                }
            )
        return proposal


class JavaSourceSemanticsEvaluatorTests(TestCase):
    def test_visible_walking_skeleton_emits_typed_semantics_and_exact_calls(self) -> None:
        result = evaluate_java_source_semantics(_fixture_input())

        result.batch.require_admissible()
        self.assertEqual(result.report.source_file_count, 1)
        self.assertEqual(result.report.type_count, 1)
        self.assertEqual(result.report.method_count, 3)
        self.assertEqual(result.report.state_slot_count, 1)
        self.assertEqual(result.report.implementation_atom_count, 8)
        self.assertEqual(result.report.legacy_call_relation_count, 2)
        self.assertEqual(result.report.legacy_call_site_count, 3)
        self.assertEqual(
            {item.root.entity_type for item in result.entities},
            {
                EntityType.JAVA_SOURCE_FILE,
                EntityType.JAVA_TYPE,
                EntityType.JAVA_METHOD,
                EntityType.JAVA_STATE_SLOT,
                EntityType.JAVA_IMPLEMENTATION_ATOM,
            },
        )
        self.assertTrue(
            all(
                item.state.state_payload_fields["method_disposition"]
                == JavaSemanticDisposition.SEMANTICS_COMPLETE.value
                for item in result.methods
            )
        )

        method_by_id = {
            item.root_id: _method_signature(item) for item in result.methods
        }
        calls = {
            (
                method_by_id[item.root.subject.entity_root_id],
                method_by_id[item.root.object.entity_root_id],
                item.state.predicate_state_payload_fields["call_site_count"],
            )
            for item in result.relations
            if item.root.predicate is RelationPredicate.CALLS
        }
        self.assertEqual(
            calls,
            {
                (
                    "dev.acme.auth.LoginService#authenticate(boolean)",
                    "dev.acme.auth.LoginService#recordFailure()",
                    2,
                ),
                (
                    "dev.acme.auth.LoginService#authenticate(boolean)",
                    "dev.acme.auth.LoginService#issueSession()",
                    1,
                ),
            },
        )
        self.assertEqual(
            {
                item.root.observation_modality
                for item in result.relations
                if item.root.predicate is RelationPredicate.CALLS
            },
            {ObservationModality.JAVA_SOURCE_STATIC_CALL},
        )

        atoms = [
            item
            for item in result.implementation_atoms
            if item.root.root_fields["method_entity_root_id"]
            == next(
                method.root_id.value
                for method in result.methods
                if _method_signature(method).endswith("#authenticate(boolean)")
            )
        ]
        self.assertEqual(
            [item.root.root_fields["atom_kind"] for item in atoms],
            [
                JavaImplementationAtomKind.BRANCH.value,
                JavaImplementationAtomKind.CALL_SITE.value,
                JavaImplementationAtomKind.CALL_SITE.value,
                JavaImplementationAtomKind.THROW.value,
                JavaImplementationAtomKind.CALL_SITE.value,
                JavaImplementationAtomKind.RETURN.value,
            ],
        )
        self.assertEqual(
            sum(
                item.root.predicate is RelationPredicate.CONTROLS
                for item in result.relations
            ),
            3,
        )
        self.assertEqual(
            sum(
                item.root.predicate is RelationPredicate.NEXT_IN_SOURCE
                for item in result.relations
            ),
            5,
        )

    def test_entity_and_relation_state_do_not_contain_raw_source_payload(self) -> None:
        result = evaluate_java_source_semantics(_fixture_input())
        serialized = json.dumps(
            {
                "entities": [
                    {
                        "root": item.root.root_fields.as_dict(),
                        "state": item.state.state_payload_fields.as_dict(),
                    }
                    for item in result.entities
                ],
                "relations": [
                    {
                        "predicate": item.root.predicate.value,
                        "state": item.state.predicate_state_payload_fields.as_dict(),
                    }
                    for item in result.relations
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )

        self.assertNotIn("if (!credentialsValid)", serialized)
        self.assertNotIn("throw new IllegalStateException", serialized)
        self.assertNotIn("多字节字符只用于验证", serialized)
        self.assertNotIn("return issueSession()", serialized)

    def test_common_java_constructs_publish_dispositioned_positive_calls(self) -> None:
        source = b"""package dev.acme.auth;

@interface Audited {}

class LoginService {
    private String state;

    @Audited
    public String authenticate(String input) {
        audit(input);
        return input;
    }

    private void audit(String input) {
        System.out.println(input);
    }
}
"""

        result = evaluate_java_source_semantics(
            _replace_fixture_source(_fixture_input(), source)
        )

        result.batch.require_admissible()
        self.assertEqual(result.report.source_file_count, 1)
        self.assertEqual(result.report.type_count, 2)
        self.assertEqual(result.report.method_count, 2)
        self.assertEqual(result.report.implementation_atom_count, 1)
        self.assertEqual(result.report.legacy_call_relation_count, 0)
        self.assertEqual(
            {
                item.state.state_payload_fields["method_disposition"]
                for item in result.methods
            },
            {JavaSemanticDisposition.UNSUPPORTED_EXCLUDED.value},
        )
        self.assertEqual(
            sum(
                item.root.predicate is RelationPredicate.CALL_SITE_TARGETS
                for item in result.relations
            ),
            1,
        )
        self.assertFalse(
            any(
                item.root.predicate is RelationPredicate.CALLS
                for item in result.relations
            )
        )

    def test_dispositioned_declaration_does_not_invent_wildcard_type_namespace(self) -> None:
        source = b"""package dev.acme.auth;

import ext.types.*;
import java.util.List;

class LoginService {
    public void audit(RemoteType input, List<RemoteType> values) {}
}
"""

        result = evaluate_java_source_semantics(
            _replace_fixture_source(_fixture_input(), source)
        )

        result.batch.require_admissible()
        method = result.methods[0]
        self.assertEqual(
            method.root.root_fields["parameter_types"],
            ("RemoteType", "java.util.List<RemoteType>"),
        )
        self.assertNotIn(
            "dev.acme.auth.RemoteType",
            method.root.root_fields["parameter_types"],
        )

    def test_dispositioned_calls_do_not_cross_anonymous_executable_boundary(self) -> None:
        source = b"""package dev.acme.auth;

class LoginService {
    public void authenticate() {
        audit();
        Runnable deferred = new Runnable() {
            public void run() {
                audit();
            }
        };
    }

    private void audit() {}
}
"""

        result = evaluate_java_source_semantics(
            _replace_fixture_source(_fixture_input(), source)
        )

        result.batch.require_admissible()
        self.assertEqual(result.report.type_count, 1)
        self.assertEqual(result.report.method_count, 2)
        self.assertEqual(result.report.implementation_atom_count, 1)
        self.assertEqual(
            sum(
                item.root.predicate is RelationPredicate.CALL_SITE_TARGETS
                for item in result.relations
            ),
            1,
        )

    def test_disposition_manifest_includes_nested_enum_member_methods(self) -> None:
        source = b"""package dev.acme.auth;

class LoginService {
    public void authenticate() {}

    enum AuditMode {
        ENABLED;

        public void record() {}
    }
}
"""

        result = evaluate_java_source_semantics(
            _replace_fixture_source(_fixture_input(), source)
        )

        result.batch.require_admissible()
        self.assertEqual(result.report.type_count, 2)
        self.assertEqual(result.report.method_count, 2)
        self.assertEqual(result.report.declaration_count, 2)

    def test_parse_error_fails_the_complete_candidate(self) -> None:
        value = _fixture_input()
        path = next(iter(value.source_bytes))
        payload = value.source_bytes[path][:-2]
        entries = {
            **value.git_entries,
            path: replace(
                value.git_entries[path],
                object_id=hashlib.sha1(payload).hexdigest(),
            ),
        }
        source_evidence = {
            **value.source_evidence,
            path: replace(
                value.source_evidence[path],
                artifact_content_digest=_content_digest(payload),
            ),
        }
        tree_excerpt = "\n".join(
            json.dumps(
                {
                    "is_symlink": metadata.is_symlink,
                    "mode": metadata.mode,
                    "object_id": metadata.object_id,
                    "path": entry_path,
                    "type": metadata.object_type,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            for entry_path, metadata in sorted(entries.items())
        )
        tree_payload = tree_excerpt.encode()
        previous = value.tree_evidence[0]
        tree_evidence = StructureEvidence.create(
            artifact_id=previous.artifact_id,
            source_context_id=previous.source_context_id,
            byte_start=0,
            byte_end=len(tree_payload),
            locator=previous.locator,
            excerpt=tree_excerpt,
            artifact_content_digest=_content_digest(tree_payload),
        )

        with self.assertRaises(JavaSourceSemanticsError) as caught:
            evaluate_java_source_semantics(
                replace(
                    value,
                    source_bytes={**value.source_bytes, path: payload},
                    git_entries=entries,
                    source_evidence=source_evidence,
                    tree_evidence=(tree_evidence,),
                )
            )

        self.assertEqual(caught.exception.reason_code, "JAVA_FRONTEND_PARSE_ERROR")

    def test_schema_definition_is_initial_system_schema(self) -> None:
        definition = StructureSchemaDefinition.java_source_semantics()

        definition.require_valid()
        self.assertEqual(definition.schema_ref, "JAVA-SOURCE-SEMANTICS@1.0.0")


class JavaImplementationViewTests(TestCase):
    def setUp(self) -> None:
        self.fixture = _publication_tests.StructurePublicationTests(
            methodName="runTest"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.registry.register(
            definition=StructureSchemaDefinition.java_source_semantics(),
            idempotency_key=IdempotencyKey("register-java-source-semantics-schema"),
            proposal_ref="ITER-007-PROPOSAL",
            review_ref="ITER-007-READINESS",
            registered_by="test",
            reason="ITER-007 frozen Java source-semantics definition",
        )
        evaluation = evaluate_java_source_semantics(
            _fixture_input(
                scope_id=self.fixture.scope.scope_id,
                source_binding_id=self.fixture.binding,
            )
        )
        receipt = self.fixture.publish(
            evaluation.batch,
            key="java-semantics-view",
            expected=None,
        )
        snapshot = self.fixture.repository.get_snapshot(
            receipt.snapshot.snapshot_id
        )
        bundle = _snapshot_bundle(self.fixture.repository, snapshot.snapshot_id)
        sessions = StructureReadSessionService(
            SqliteStructureReadSessionRepository(self.fixture.database),
            self.fixture.repository,
            self.fixture.scopes,
            clock=self.fixture.clock,
        )
        session = sessions.open_ordered(
            scope_id=self.fixture.scope.scope_id,
            scope_revision=self.fixture.scope.definition_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "9" * 32),
                task_revision=Revision(1),
                scope_id=self.fixture.scope.scope_id,
                purpose=StructureReadPurpose.EXACT_SNAPSHOT.value,
                classification="INTERNAL",
            ),
            caller_ref="java-implementation-view-test",
            snapshot_ids=(snapshot.snapshot_id,),
            idempotency_key=IdempotencyKey("java-implementation-view-session"),
        )
        file_digest = digest_of({"file": "java-semantics-bundle"})
        binding = session.snapshots[0]
        envelope = StructureOrderedReadBundle.create(
            session=session,
            snapshots=(
                StructureSnapshotBundleReference(
                    ordinal=0,
                    snapshot_id=snapshot.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=file_digest,
                ),
            ),
        )
        self.snapshot_id = snapshot.snapshot_id
        self.bundle = bundle
        self.envelope = envelope
        self.session = session
        self.service = StructureViewService(envelope, ((bundle, file_digest),))

    def _view_with_complete_discovery_recall(self) -> StructureViewService:
        recall = StructureBusinessDiscoveryRecallBinding.create(
            oracle_ref="fixture-pre-question-discovery-oracle@1",
            oracle_result_digest=digest_of(
                "fixture-pre-question-discovery-result"
            ),
            profile_ref=JAVA_SOURCE_SEMANTICS_PROFILE_REF,
            discovery_contract_ref=(
                JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
            ),
            snapshot_id=self.snapshot_id,
            snapshot_bundle_digest=self.bundle.digest,
            counterexample_classes=("naming", "synonym", "alternate-entry"),
            verdict=StructureBusinessDiscoveryRecallVerdict.COMPLETE,
        )
        envelope = StructureOrderedReadBundle.create(
            session=self.session,
            snapshots=self.envelope.snapshots,
            business_discovery_recall_bindings=(recall,),
        )
        return StructureViewService(
            envelope,
            ((self.bundle, envelope.snapshots[0].file_digest),),
        )

    def test_feature_search_ranks_cross_domain_method_without_symbol_input(self) -> None:
        result = self.service.implementation_candidates(
            snapshot_id=self.snapshot_id,
            search_terms=("credentials", "failure", "session"),
            limit=10,
        )

        self.assertEqual(result.operation, StructureViewOperation.IMPLEMENTATION_CANDIDATES)
        self.assertEqual(result.payload["query_status"], "SUPPORTED")
        self.assertEqual(result.payload["candidate_count"], 3)
        candidates = result.payload["candidates"]
        self.assertEqual(
            candidates[0]["canonical_signature"],
            "dev.acme.auth.LoginService#authenticate(boolean)",
        )
        self.assertEqual(
            candidates[0]["matched_terms"],
            ("credentials", "failure", "session"),
        )
        self.assertTrue(result.support_map)
        self.assertEqual(
            result,
            self.service.implementation_candidates(
                snapshot_id=self.snapshot_id,
                search_terms=("credentials", "failure", "session"),
                limit=10,
            ),
        )

    def test_feature_search_tokenization_accepts_unicode_identifiers(self) -> None:
        self.assertEqual(
            _feature_tokens("登录Flow2FA"),
            ("2", "fa", "flow", "登录"),
        )

        result = self.service.implementation_candidates(
            snapshot_id=self.snapshot_id,
            search_terms=("登录", "流程"),
            limit=10,
        )

        self.assertEqual(result.payload["query_status"], "KNOWLEDGE_GAP")
        self.assertEqual(result.payload["normalized_terms"], ("流程", "登录"))
        self.assertEqual(
            result.limitations,
            ("IMPLEMENTATION_CANDIDATES_ZERO",),
        )

    def test_unique_candidate_proof_reads_ordered_method_implementation(self) -> None:
        candidates = self.service.implementation_candidates(
            snapshot_id=self.snapshot_id,
            search_terms=("credentials",),
            limit=10,
        )
        argument = StructureEntityArgument.from_unique_candidate(candidates)

        result = self.service.method_implementation(method=argument)

        self.assertEqual(result.operation, StructureViewOperation.METHOD_IMPLEMENTATION)
        self.assertEqual(result.payload["query_status"], "SUPPORTED")
        self.assertTrue(result.payload["negative_conclusion_supported"])
        atoms = result.payload["ordered_atoms"]
        self.assertEqual(
            tuple(item["root_fields"]["atom_kind"] for item in atoms),
            ("BRANCH", "CALL_SITE", "CALL_SITE", "THROW", "CALL_SITE", "RETURN"),
        )
        relations = result.payload["implementation_relations"]
        self.assertEqual(
            sum(item["predicate"] == "CONTROLS" for item in relations),
            3,
        )
        self.assertEqual(len(result.payload["legacy_calls"]), 2)
        self.assertEqual(result.payload["legacy_calls_direction"], "OUTGOING")
        serialized = canonical_json_bytes(result.canonical_value()).decode("utf-8")
        self.assertNotIn("if (!credentialsValid)", serialized)
        self.assertNotIn("throw new IllegalStateException", serialized)

    def test_product_uses_bounded_multi_method_implementation_chain(self) -> None:
        model = _QualifiedSemanticsFixtureModel()

        execution = WorldModelProductAnswerService(
            view=self.service,
            snapshot_bundles=(self.bundle,),
            model_strategy=model,
            gateway_counters=model,
        ).execute(
            request_ref="iter-007-visible-cross-domain",
            original_question="凭据无效时系统怎样处理，成功时又怎样建立会话？",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("iter-007-visible-permission"),
        )

        execution.chain.require_valid()
        self.assertEqual(
            model.capabilities,
            [
                IMPLEMENTATION_INVESTIGATION,
                IMPLEMENTATION_INVESTIGATION,
                IMPLEMENTATION_INVESTIGATION,
                IMPLEMENTATION_ANSWER_DRAFTING,
                IMPLEMENTATION_ANSWER_REVIEW,
            ],
        )
        self.assertEqual(execution.chain.provider_call_count, 5)
        self.assertEqual(execution.chain.network_operation_count, 5)
        self.assertEqual(len(execution.model_proposals), 5)
        self.assertEqual(
            tuple(item.operation for item in execution.chain.plan.steps),
            (
                StructureViewOperation.IMPLEMENTATION_CANDIDATES,
                StructureViewOperation.METHOD_IMPLEMENTATION,
                StructureViewOperation.METHOD_IMPLEMENTATION,
                StructureViewOperation.METHOD_IMPLEMENTATION,
            ),
        )
        self.assertEqual(len(execution.chain.result_set.step_results), 4)
        method_results = tuple(
            item.view_result
            for item in execution.chain.result_set.step_results[1:]
        )
        self.assertTrue(
            all(item.payload["query_status"] == "SUPPORTED" for item in method_results)
        )
        self.assertEqual(
            tuple(item.payload["canonical_signature"] for item in method_results),
            (
                "dev.acme.auth.LoginService#authenticate(boolean)",
                "dev.acme.auth.LoginService#issueSession()",
                "dev.acme.auth.LoginService#recordFailure()",
            ),
        )
        self.assertIn("记录失败并抛出异常", execution.chain.draft.body)
        self.assertEqual(
            execution.chain.question.model_route,
            BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE,
        )
        planning_input = json.dumps(
            model.sealed_inputs[0], ensure_ascii=False, sort_keys=True
        )
        self.assertNotIn("query_results", planning_input)
        self.assertNotIn("ordered_atoms", planning_input)
        page = world_model_evaluation_page_payload(
            execution.chain,
            "0" * 40,
        )
        self.assertEqual(page["execution_boundary"]["provider_call_count"], 5)
        self.assertEqual(
            [item["status"] for item in page["candidate_resolutions"]["resolutions"]],
            ["UNIQUE", "UNIQUE", "UNIQUE"],
        )

        plan = execution.chain.plan
        tampered_proposal = WorldModelQueryPlanProposal(
            requirement_id=plan.requirement_id,
            requirement_digest=plan.requirement_digest,
            read_set_digest=plan.read_authority.read_set_digest,
            ordered_bundle_digest=plan.read_authority.ordered_bundle_digest,
            selectors=tuple(
                item.selector
                for item in execution.chain.resolutions.resolutions
            ),
            steps=tuple(
                WorldModelQueryStepProposal(
                    step_id=item.step_id,
                    need_ids=item.need_ids,
                    operation=item.operation,
                    arguments=item.arguments,
                    parameters=item.parameters,
                    constraint_ids=item.constraint_ids,
                )
                for item in reversed(plan.steps)
            ),
            explicit_gaps=plan.explicit_gaps,
            invocation_id=plan.planning_invocation.invocation_id,
            invocation_digest=plan.planning_invocation.digest,
            investigation_trace=plan.investigation_trace,
        )
        with self.assertRaisesRegex(DomainError, "exactly replay"):
            WorldModelAnsweringService._validate_investigation_plan_binding(
                tampered_proposal
            )

    def test_product_rejects_a_review_code_outside_the_versioned_vocabulary(self) -> None:
        model = _InvalidReviewCodeFixtureModel()

        with self.assertRaisesRegex(
            DomainError,
            "did not close the exact independent checklist",
        ):
            WorldModelProductAnswerService(
                view=self.service,
                snapshot_bundles=(self.bundle,),
                model_strategy=model,
                gateway_counters=model,
            ).execute(
                request_ref="iter-007-invalid-review-code",
                original_question="凭据无效时系统怎样处理？",
                response_language="zh-CN",
                classification="INTERNAL",
                permission_digest=digest_of("iter-007-visible-permission"),
            )

    def test_formal_answer_workload_uses_sealed_recall_for_bounded_absence(self) -> None:
        model = _FormalSemanticsFixtureModel(
            search_terms=("definitelyAbsentFeature",)
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            snapshot_path = root / "snapshot.json"
            ordered_path = root / "ordered.json"
            page_path = root / "evaluation.json"
            summary_path = root / "summary.json"
            citations = root / "citations"
            citations.mkdir()
            store = FileStructureReadBundleStore()
            stored_snapshot = store.write_snapshot(
                str(snapshot_path), self.bundle
            )
            binding = self.session.snapshots[0]
            envelope = StructureOrderedReadBundle.create(
                session=self.session,
                snapshots=(
                    StructureSnapshotBundleReference(
                        ordinal=0,
                        snapshot_id=self.snapshot_id,
                        snapshot_binding_digest=binding.digest,
                        snapshot_manifest_digest=(
                            binding.snapshot_manifest_digest
                        ),
                        bundle_digest=self.bundle.digest,
                        file_digest=stored_snapshot.file_digest,
                    ),
                ),
                business_discovery_recall_bindings=(
                    StructureBusinessDiscoveryRecallBinding.create(
                        oracle_ref="formal-pre-question-recall-oracle@1",
                        oracle_result_digest=digest_of(
                            "formal-pre-question-recall-result"
                        ),
                        profile_ref=JAVA_SOURCE_SEMANTICS_PROFILE_REF,
                        discovery_contract_ref=(
                            JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
                        ),
                        snapshot_id=self.snapshot_id,
                        snapshot_bundle_digest=self.bundle.digest,
                        counterexample_classes=(
                            "naming",
                            "synonym",
                            "alternate-entry",
                        ),
                        verdict=(
                            StructureBusinessDiscoveryRecallVerdict.COMPLETE
                        ),
                    ),
                ),
            )
            stored_ordered = store.write_ordered(
                str(ordered_path), envelope
            )
            payload = {
                "case_id": "ITER-008-FORMAL-ABSENCE-ASSET-TEST",
                "question_variant": "请解释这个不存在的功能如何实现。",
                "resolved_snapshot_ids": [self.snapshot_id.value],
            }
            import base64

            encoded = base64.b64encode(canonical_json_bytes(payload)).decode(
                "ascii"
            )
            arguments = [
                "--product-payload-base64",
                encoded,
                "--ordered-bundle",
                stored_ordered.locator,
                "--snapshot-bundle",
                stored_snapshot.locator,
                "--gateway-socket",
                str(root / "unopened-gateway.sock"),
                "--conformance-result-ref",
                "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
                "--run-ref",
                "formal-asset-test",
                "--implementation-commit",
                "1" * 40,
                "--authority-page-output",
                str(page_path),
                "--citation-seal-output-directory",
                str(citations),
                "--summary-output",
                str(summary_path),
            ]

            with (
                patch.object(
                    bounded_java_source_semantics_answer_workload,
                    "UnixSocketModelGatewayClient",
                    return_value=model,
                ),
                patch.object(
                    bounded_java_source_semantics_answer_workload,
                    "WorldModelCapabilityStrategy",
                    return_value=model,
                ),
                patch.dict(
                    bounded_java_source_semantics_answer_workload.os.environ,
                    {},
                    clear=True,
                ),
                redirect_stdout(StringIO()),
            ):
                code = bounded_java_source_semantics_answer_workload.main(
                    arguments
                )

            self.assertEqual(code, 0)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["provider_call_count"], 4)
            self.assertEqual(summary["network_operation_count"], 4)
            self.assertEqual(
                summary["model_capabilities"],
                [
                    IMPLEMENTATION_INVESTIGATION,
                    IMPLEMENTATION_INVESTIGATION,
                    IMPLEMENTATION_ANSWER_DRAFTING,
                    IMPLEMENTATION_ANSWER_REVIEW,
                ],
            )
            self.assertEqual(len(summary["model_call_ids"]), 4)
            self.assertEqual(len(summary["gateway_audits"]), 4)
            self.assertEqual(summary["product_oracle_read_count"], 0)
            model_input = json.dumps(
                model.sealed_inputs,
                ensure_ascii=False,
                sort_keys=True,
            )
            self.assertNotIn("oracle_ref", model_input)
            self.assertNotIn("oracle_result_digest", model_input)
            self.assertNotIn("discovery_oracle", model_input)
            self.assertIn("business_discovery_recall", model_input)
            page_envelope = json.loads(page_path.read_bytes())
            self.assertEqual(
                page_envelope["format_ref"],
                BOUNDED_WORLD_MODEL_EVALUATION_PAGE_FORMAT,
            )
            self.assertIn(
                "BOUNDED_ABSENCE",
                page_path.read_text(encoding="utf-8"),
            )
            self.assertTrue(page_path.is_file())
            self.assertTrue(any(citations.iterdir()))

    def test_zero_candidate_is_limited_and_multiple_candidates_are_investigated(self) -> None:
        cases = (
            (("definitelyAbsentFeature",), "LIMITATION", 1, 4, self.service),
            (
                ("definitelyAbsentFeature",),
                "KNOWLEDGE_GAP",
                1,
                4,
                self._view_with_complete_discovery_recall(),
            ),
            (("login",), "SUPPORTED", 4, 5, self.service),
        )
        for (
            terms,
            expected_disposition,
            expected_result_count,
            expected_call_count,
            view,
        ) in cases:
            with self.subTest(terms=terms, disposition=expected_disposition):
                model = _QualifiedSemanticsFixtureModel(search_terms=terms)
                execution = WorldModelProductAnswerService(
                    view=view,
                    snapshot_bundles=(self.bundle,),
                    model_strategy=model,
                    gateway_counters=model,
                ).execute(
                    request_ref="iter-007-boundary-" + terms[0],
                    original_question="请解释这个功能如何实现。",
                    response_language="zh-CN",
                    classification="INTERNAL",
                    permission_digest=digest_of(
                        {"iter-007-boundary": terms}
                    ),
                )

                self.assertEqual(model.provider_call_count, expected_call_count)
                self.assertEqual(
                    model.sealed_inputs[-2]["assessment_disposition"],
                    expected_disposition,
                )
                self.assertEqual(
                    len(execution.chain.result_set.step_results),
                    expected_result_count,
                )
                self.assertTrue(
                    all(item.state.value == "READY" for item in execution.chain.plan.steps)
                )

    def test_post_compiler_candidate_restart_is_rejected(self) -> None:
        view = self._view_with_complete_discovery_recall()
        model = _MixedPositiveAndZeroCandidateFixtureModel()

        with self.assertRaisesRegex(
            DomainError,
            "frozen evidence transition",
        ):
            WorldModelProductAnswerService(
                view=view,
                snapshot_bundles=(self.bundle,),
                model_strategy=model,
                gateway_counters=model,
            ).execute(
                request_ref="ITER-008-MIXED-CANDIDATE-NEGATIVE",
                original_question="请解释凭据处理功能是否存在。",
                response_language="zh-CN",
                classification="INTERNAL",
                permission_digest=digest_of("iter-008-mixed-candidate"),
            )
