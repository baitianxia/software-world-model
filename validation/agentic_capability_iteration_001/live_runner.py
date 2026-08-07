"""Run the six production model roles against sealed capability fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Mapping

from software_world_model.ai_infrastructure import (
    AgenticEvaluationOutput,
    AgenticEvaluationRole,
    AgenticKnowledgeStrategyBundle,
    AgenticModelStrategyConfiguration,
)
from software_world_model.application_services import (
    AnswerNeedEvidence,
    BuildObjective,
    CanonicalBuildTarget,
    CoverageObligation,
    KnowledgeNeed,
    KnowledgeReadSet,
    KnowledgeRequirement,
    KnowledgeUpdateRequest,
    NeedStatus,
    RequirementFidelity,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.infrastructure import SqliteModelGatewayRepository
from software_world_model.knowledge_engine import (
    FormalKnowledgeRecord,
    KnowledgeObjectKind,
)
from software_world_model.source_integration import SourceArtifact, TargetKind

from .manifest import case_entry, verify_capability_suite


CAPABILITY_OUTPUT_DOCUMENT_SCHEMA = "swm.agentic-capability-case-output@4"


class LiveCapabilityCaseRunner:
    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: object,
        configuration: AgenticModelStrategyConfiguration,
        expected_model_fingerprint: str,
    ) -> None:
        self._database = database
        self._strategy = AgenticKnowledgeStrategyBundle.create(
            gateway, configuration
        )
        self._expected_model_fingerprint = expected_model_fingerprint

    def execute(
        self,
        *,
        suite: Mapping[str, object],
        role: AgenticEvaluationRole,
    ) -> tuple[AgenticEvaluationOutput, dict[str, object]]:
        verify_capability_suite(suite)
        case = case_entry(suite, role)
        frozen_case_id = f"{role.value.lower()}:{case['case_id']}"
        output = self._execute_role(role, case["fixture"], frozen_case_id)
        usage = _usage(self._database)
        if usage["actual_model_fingerprint"] != self._expected_model_fingerprint:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability case used an unexpected actual model",
            )
        fixture_digest = digest_of(case["fixture"])
        output_digest = digest_of(output)
        sink = {
            "suite_digest": suite["suite_digest"],
            "case_id": frozen_case_id,
            "role": role.value,
            "fixture_digest": fixture_digest.value,
            "output_digest": output_digest.value,
            "strategy_implementation_digest": (
                self._strategy.implementation_digest.value
            ),
            "provider_request_ids": usage["provider_request_ids"],
            "authorized_manifests_digest": digest_of(
                usage["authorized_manifests"]
            ).value,
            "isolation_receipts_digest": digest_of(
                usage["isolation_receipts"]
            ).value,
            "model_call_outcomes_digest": digest_of(
                usage["model_call_outcomes"]
            ).value,
        }
        evaluation_output = AgenticEvaluationOutput.create(
            case_id=frozen_case_id,
            fixture_digest=fixture_digest,
            output_ref=f"capability-output:{frozen_case_id}:{output_digest.value}",
            output_digest=output_digest,
            sink_manifest_ref=f"capability-sink:{frozen_case_id}",
            sink_manifest_digest=digest_of(sink),
            generator_origin="volcengine-ark-agentic-role-output",
            actual_model_fingerprint=usage["actual_model_fingerprint"],
            provider_request_ids=usage["provider_request_ids"],
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            usage_complete=True,
        )
        document_core = {
            "schema": CAPABILITY_OUTPUT_DOCUMENT_SCHEMA,
            "suite_id": suite["suite_id"],
            "suite_version": suite["suite_version"],
            "suite_digest": suite["suite_digest"],
            "case_id": frozen_case_id,
            "role": role.value,
            "fixture": case["fixture"],
            "fixture_digest": fixture_digest.value,
            "oracle_ref": (
                f"{suite['suite_id']}:oracle:{role.value}:{case['case_id']}"
            ),
            "oracle_digest": digest_of(case["oracle"]).value,
            "domain_output": output,
            "authorized_manifests": usage["authorized_manifests"],
            "isolation_receipts": usage["isolation_receipts"],
            "model_call_outcomes": usage["model_call_outcomes"],
            "sink_manifest": sink,
            "evaluation_output": _evaluation_output_document(evaluation_output),
        }
        document = {
            **document_core,
            "document_digest": digest_of(document_core).value,
        }
        return evaluation_output, document

    def _execute_role(
        self,
        role: AgenticEvaluationRole,
        fixture: Mapping[str, object],
        case_id: str,
    ) -> dict[str, object]:
        if role is AgenticEvaluationRole.REQUIREMENT_FIDELITY:
            plan = self._strategy.requirement_planner.plan(
                original_request=str(fixture["original_request"])
            )
            return {
                "needs": [
                    {
                        "need_id": item.need_id,
                        "question": item.question,
                        "required_kinds": [kind.value for kind in item.required_kinds],
                        "required_type_names": list(item.required_type_names),
                        "required_terms": list(item.required_terms),
                        "minimum_support_count": item.minimum_support_count,
                    }
                    for item in plan.needs
                ],
                "joint_constraints": [
                    {
                        "constraint_id": item.constraint_id,
                        "need_ids": list(item.need_ids),
                        "description": item.description,
                    }
                    for item in plan.joint_constraints
                ],
            }
        if role is AgenticEvaluationRole.SOURCE_INVESTIGATION:
            request = _update_request(fixture, case_id)
            proposal = self._strategy.source_planner.propose(
                request=request, completed_operations=(), ordinal=1
            )
            return {
                "stop": proposal.stop,
                "tool": proposal.tool.value if proposal.tool is not None else None,
                "parameters": dict(proposal.parameters),
                "rationale": proposal.rationale,
            }
        if role is AgenticEvaluationRole.FORMAL_FACT_GROUNDING:
            request = _update_request(fixture, case_id)
            artifact = _artifact(fixture)
            bundle = self._strategy.knowledge_builder.build(
                request=request,
                target=request.target,
                artifacts=(artifact,),
            )
            return {
                "evidence": [
                    {
                        "evidence_key": item.evidence_key,
                        "artifact_id": item.artifact.artifact_id.value,
                        "byte_start": item.byte_start,
                        "byte_end": item.byte_end,
                        "locator": item.locator,
                        "excerpt": item.artifact.payload[
                            item.byte_start : item.byte_end
                        ].decode("utf-8"),
                    }
                    for item in bundle.evidence
                ],
                "entities": [
                    {
                        "candidate_key": item.candidate_key,
                        "entity_type": item.entity_type,
                        "label": item.label,
                        "evidence_keys": list(item.evidence_keys),
                    }
                    for item in bundle.entities
                ],
                "facts": [
                    {
                        "candidate_key": item.candidate_key,
                        "predicate": item.predicate,
                        "object_value": item.object_value,
                        "evidence_keys": list(item.evidence_keys),
                        "reviewed_grounding": (
                            {
                                "candidate_key": item.reviewed_grounding.candidate_key,
                                "proposer_model_call_id": (
                                    item.reviewed_grounding.proposer_model_call_id.value
                                ),
                                "reviewer_model_call_id": (
                                    item.reviewed_grounding.reviewer_model_call_id.value
                                ),
                                "digest": item.reviewed_grounding.digest.value,
                            }
                            if item.reviewed_grounding is not None
                            else None
                        ),
                    }
                    for item in bundle.facts
                ],
            }
        requirement, need, read_set, record = _formal_need_state(fixture)
        if role is AgenticEvaluationRole.NEED_SUFFICIENCY:
            decision = self._strategy.sufficiency_evaluator.evaluate(
                requirement=requirement, need=need, read_set=read_set
            )
            return {
                "status": decision.status.value,
                "supporting_references": [
                    item.value for item in decision.supporting_references
                ],
                "gap": decision.gap,
                "counterexamples": [item.value for item in decision.counterexamples],
                "conflicts": [item.value for item in decision.conflicts],
                "unknowns": list(decision.unknowns),
                "limitations": list(decision.limitations),
            }
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=(str(fixture["limitation"]),),
        )
        if role is AgenticEvaluationRole.ANSWER_SOURCE_CLOSURE:
            plan = self._strategy.answer_planner.plan(
                original_request=need.question, needs=(evidence,)
            )
            return {
                "selections": [
                    {
                        "need_id": item.need_id,
                        "formal_references": [
                            reference.value for reference in item.formal_references
                        ],
                    }
                    for item in plan.selections
                ]
            }
        assessment = _assessment(need, record, fixture)
        candidate = _candidate(requirement, need, record, fixture)
        decision = self._strategy.answer_reviewer.review(
            task=SimpleNamespace(original_request=requirement.original_request),
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )
        return {
            "approved": decision.approved,
            "failed_dimensions": [
                item.value for item in decision.failed_dimensions
            ],
            "findings": list(decision.findings),
        }


def save_capability_output_document(
    document: Mapping[str, object], result_directory: str | Path
) -> Path:
    _verify_output_document(document)
    target = Path(result_directory) / f"{document['case_id'].replace(':', '--')}.json"
    write_capability_document_once(target, document)
    return target


def write_capability_document_once(
    target: str | Path, document: Mapping[str, object]
) -> None:
    """Atomically create an immutable capability artifact or accept an exact replay."""

    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(document) + b"\n"
    if path.exists():
        if path.read_bytes() != payload:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "capability evidence path already contains different content",
            )
        return
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        try:
            os.link(temporary_name, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "capability evidence was concurrently changed",
                )
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def load_capability_output_document(
    path: str | Path,
) -> tuple[AgenticEvaluationOutput, dict[str, object]]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability case output cannot be loaded",
        ) from exc
    _verify_output_document(document)
    raw = document["evaluation_output"]
    try:
        output = AgenticEvaluationOutput(
            case_id=raw["case_id"],
            fixture_digest=Digest(raw["fixture_digest"]),
            output_ref=raw["output_ref"],
            output_digest=Digest(raw["output_digest"]),
            sink_manifest_ref=raw["sink_manifest_ref"],
            sink_manifest_digest=Digest(raw["sink_manifest_digest"]),
            generator_origin=raw["generator_origin"],
            actual_model_fingerprint=raw["actual_model_fingerprint"],
            provider_request_ids=tuple(raw["provider_request_ids"]),
            input_tokens=raw["input_tokens"],
            output_tokens=raw["output_tokens"],
            usage_complete=raw["usage_complete"],
            digest=Digest(raw["digest"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability evaluation output is invalid",
        ) from exc
    if (
        not output.verify_digest()
        or output.output_digest != digest_of(document["domain_output"])
        or output.sink_manifest_digest != digest_of(document["sink_manifest"])
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability evaluation output digest is invalid",
        )
    return output, document


def verify_capability_output_against_suite(
    output: AgenticEvaluationOutput,
    document: Mapping[str, object],
    suite: Mapping[str, object],
) -> None:
    """Require a sealed output to match one exact case in the pinned suite."""

    verify_capability_suite(suite)
    expected = next(
        (
            case
            for case in suite["cases"]
            if f"{str(case['role']).lower()}:{case['case_id']}" == output.case_id
        ),
        None,
    )
    if (
        expected is None
        or document.get("suite_id") != suite["suite_id"]
        or document.get("suite_version") != suite["suite_version"]
        or document.get("suite_digest") != suite["suite_digest"]
        or document.get("role") != expected["role"]
        or document.get("fixture") != expected["fixture"]
        or output.fixture_digest != digest_of(expected["fixture"])
        or document.get("oracle_ref")
        != f"{suite['suite_id']}:oracle:{expected['role']}:{expected['case_id']}"
        or document.get("oracle_digest") != digest_of(expected["oracle"]).value
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability output does not match the pinned suite case",
        )


def _update_request(
    fixture: Mapping[str, object], case_id: str
) -> KnowledgeUpdateRequest:
    revision = str(fixture["revision"])
    target_core = {
        "target_kind": TargetKind.REPOSITORY_REVISION.value,
        "canonical_identity": (("revision", revision),),
        "resolution_receipt_id": "resolution_receipt_00000000000000000000000000000001",
        "resolution_receipt_digest": digest_of({"revision": revision}).value,
        "obligation": CoverageObligation.REQUIRED.value,
        "boundary": "EXACT",
        "canonicalization_contract": "capability-fixture@1",
    }
    target_digest = digest_of(target_core)
    target = CanonicalBuildTarget(
        target_id=StableId(f"build_target_{target_digest.value[-32:]}"),
        target_kind=TargetKind.REPOSITORY_REVISION,
        canonical_identity=(("revision", revision),),
        resolution_receipt_id=StableId(target_core["resolution_receipt_id"]),
        resolution_receipt_digest=Digest(target_core["resolution_receipt_digest"]),
        obligation=CoverageObligation.REQUIRED,
        boundary="EXACT",
        digest=target_digest,
    )
    question = str(fixture["question"])
    return KnowledgeUpdateRequest(
        idempotency_key=IdempotencyKey(f"capability-case:{case_id}"),
        objective=BuildObjective.create(
            objective_id=f"capability-objective:{case_id}",
            description=question,
            unacceptable_outcomes=("invented source behavior",),
        ),
        target=target,
        scope_id=StableId("scope_00000000000000000000000000000001"),
        scope_revision=Revision(1),
        source_id=StableId("source_00000000000000000000000000000001"),
        source_revision=Revision(1),
        binding_id=StableId("binding_00000000000000000000000000000001"),
        binding_revision=Revision(1),
        expected_current_snapshot_id=None,
        max_steps=4,
        max_items_per_step=20,
        max_bytes_per_step=4096,
        classification="INTERNAL",
        actor="capability-evaluation-runner",
        correlation_ref=CorrelationRef(f"capability-evaluation:{case_id}"),
    )


def _artifact(fixture: Mapping[str, object]) -> SourceArtifact:
    payload = str(fixture["content"]).encode("utf-8")
    content_digest = Digest(
        "sha256:" + hashlib.sha256(payload).hexdigest()
    )
    return SourceArtifact(
        artifact_id=StableId("artifact_00000000000000000000000000000001"),
        artifact_kind="LOCAL_GIT_FILE@1",
        payload_schema_version="LOCAL_GIT_FILE@1",
        source_id=StableId("source_00000000000000000000000000000001"),
        source_revision=Revision(1),
        source_context_id=StableId(
            "source_context_00000000000000000000000000000001"
        ),
        source_native_identity=str(fixture["path"]),
        content_digest=content_digest,
        payload=payload,
        classification="INTERNAL",
        truncated=False,
        truncation_offset=None,
        identity_digest=digest_of(
            {"path": fixture["path"], "content": content_digest.value}
        ),
    )


def _formal_need_state(fixture: Mapping[str, object]):
    fact_text = (
        f"{fixture['formal_fact']} Limitation: {fixture['limitation']}"
    )
    record = FormalKnowledgeRecord(
        kind=KnowledgeObjectKind.FACT,
        object_id=StableId(
            "knowledge_fact_00000000000000000000000000000001"
        ),
        object_digest=digest_of(fact_text),
        type_name="HAS_VALUE",
        text=fact_text,
        context_digest=digest_of({"revision": "a" * 40}),
        support_references=(
            StableId("evidence_00000000000000000000000000000001"),
        ),
    )
    need = KnowledgeNeed(
        need_id="need:maximum-attempts",
        question=str(fixture["question"]),
        required_kinds=(KnowledgeObjectKind.FACT,),
        required_type_names=("HAS_VALUE",),
        required_terms=("RetryClient", "attempt"),
        minimum_support_count=1,
    )
    requirement = KnowledgeRequirement.create(
        requirement_id=StableId(
            "requirement_00000000000000000000000000000001"
        ),
        revision=Revision(1),
        fidelity=RequirementFidelity.ORIGINAL,
        original_request=need.question,
        needs=(need,),
    )
    read_set = KnowledgeReadSet(
        need_id=need.need_id,
        records=(record,),
        query_digest=digest_of({"need": need.need_id}),
        complete=True,
        digest=digest_of(
            {
                "need": need.need_id,
                "record": record.object_digest.value,
                "complete": True,
            }
        ),
    )
    return requirement, need, read_set, record


def _assessment(need, record, fixture):
    proof = SimpleNamespace(supporting_references=(record.object_id,))
    return SimpleNamespace(
        assessment_id=StableId(
            "assessment_00000000000000000000000000000001"
        ),
        digest=digest_of("capability-assessment"),
        sufficient=True,
        joint_constraint_failures=(),
        items=(
            SimpleNamespace(
                need_id=need.need_id,
                status=NeedStatus.SATISFIED,
                proof=proof,
                gap=None,
                unknowns=(),
                limitations=(str(fixture["limitation"]),),
                conflicts=(),
            ),
        ),
    )


def _candidate(requirement, need, record, fixture):
    body = record.text
    return SimpleNamespace(
        candidate_id=StableId(
            "answer_candidate_00000000000000000000000000000001"
        ),
        digest=digest_of(body),
        response_kind=SimpleNamespace(value="KNOWLEDGE_COMPLETE"),
        body=body,
        claims=(
            SimpleNamespace(
                claim_id="claim:maximum-attempts",
                need_id=need.need_id,
                kind=SimpleNamespace(value="FORMAL_KNOWLEDGE"),
                text=record.text,
                formal_reference=record.object_id,
                gap=None,
            ),
            SimpleNamespace(
                claim_id="limitation:maximum-attempts",
                need_id=need.need_id,
                kind=SimpleNamespace(value="APPLICATION_LIMITATION"),
                text=str(fixture["limitation"]),
                formal_reference=None,
                gap=None,
            ),
        ),
    )


def _usage(database: SqliteDatabase) -> dict[str, object]:
    with database.read() as connection:
        roots = connection.execute(
            "SELECT current_state FROM ai_model_call_roots"
        ).fetchall()
        outputs = connection.execute(
            """SELECT output.provider_request_id,
                      output.actual_model_fingerprint,
                      output.input_tokens, output.output_tokens,
                      output.usage_complete, output.model_call_id,
                      output.output_digest, revision.failure_code
               FROM ai_model_call_outputs AS output
               JOIN ai_model_call_roots AS root
                 ON root.model_call_id = output.model_call_id
               JOIN ai_model_call_revisions AS revision
                 ON revision.model_call_id = root.model_call_id
                AND revision.revision = root.current_revision
               ORDER BY root.created_at, output.model_call_id"""
        ).fetchall()
    if (
        not outputs
        or len(outputs) != len(roots)
        or any(row["current_state"] != "COMPLETED" for row in roots)
        or any(
            not row["provider_request_id"]
            or not row["actual_model_fingerprint"]
            or row["input_tokens"] is None
            or row["output_tokens"] is None
            or row["usage_complete"] != 1
            for row in outputs
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability case model usage is incomplete",
        )
    fingerprints = {row["actual_model_fingerprint"] for row in outputs}
    request_ids = tuple(row["provider_request_id"] for row in outputs)
    if len(fingerprints) != 1 or len(set(request_ids)) != len(request_ids):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability case changed model identity or reused a provider request",
        )
    repository = SqliteModelGatewayRepository(database)
    authorized_manifests = []
    isolation_receipts = []
    for row in outputs:
        model_call_id = StableId(row["model_call_id"])
        authorized_manifests.append(
            _manifest_document(
                repository.get_manifest(model_call_id), model_call_id
            )
        )
        isolation_receipts.append(
            _receipt_document(
                repository.recover_by_id(model_call_id).isolation_receipt,
                model_call_id,
            )
        )
    return {
        "actual_model_fingerprint": next(iter(fingerprints)),
        "provider_request_ids": request_ids,
        "input_tokens": sum(row["input_tokens"] for row in outputs),
        "output_tokens": sum(row["output_tokens"] for row in outputs),
        "authorized_manifests": authorized_manifests,
        "isolation_receipts": isolation_receipts,
        "model_call_outcomes": [
            {
                "model_call_id": row["model_call_id"],
                "provider_request_id": row["provider_request_id"],
                "actual_model_fingerprint": row["actual_model_fingerprint"],
                "input_tokens": row["input_tokens"],
                "output_tokens": row["output_tokens"],
                "usage_complete": bool(row["usage_complete"]),
                "output_digest": row["output_digest"],
                "failure_code": row["failure_code"],
            }
            for row in outputs
        ],
    }


def _manifest_document(manifest, model_call_id: StableId) -> dict[str, object]:
    return {
        "model_call_id": model_call_id.value,
        "manifest_id": manifest.manifest_id.value,
        "version": manifest.version.value,
        "capability_id": manifest.capability_id,
        "strategy_ref": manifest.strategy_ref,
        "execution_stage": manifest.execution_stage,
        "calling_module": manifest.calling_module,
        "proposal_vocabulary_ref": manifest.proposal_vocabulary_ref,
        "items": [
            {
                "item_id": item.item_id,
                "schema_ref": item.schema_ref,
                "classification": item.classification,
                "purpose": item.purpose,
                "authority_reference": item.authority_reference,
                "disposition": item.disposition.value,
                "content": item.content,
                "transformation_ref": item.transformation_ref,
                "content_digest": item.content_digest.value,
            }
            for item in manifest.items
        ],
        "digest": manifest.digest.value,
    }


def _receipt_document(receipt, model_call_id: StableId) -> dict[str, object]:
    return {
        "model_call_id": model_call_id.value,
        "receipt_id": receipt.receipt_id.value,
        "manifest_digest": receipt.manifest_digest.value,
        "provider_request_digest": receipt.provider_request_digest.value,
        "provider_type": receipt.provider_type,
        "adapter_version": receipt.adapter_version,
        "provider_configuration_fingerprint": (
            receipt.provider_configuration_fingerprint.value
        ),
        "runtime_access_mode": receipt.runtime_access_mode.value,
        "platform_proposal_mode": receipt.platform_proposal_mode.value,
        "conformance_result_ref": receipt.conformance_result_ref,
        "issued_at": receipt.issued_at.isoformat(),
        "digest": receipt.digest.value,
    }


def _evaluation_output_document(output: AgenticEvaluationOutput) -> dict[str, object]:
    return {
        "case_id": output.case_id,
        "fixture_digest": output.fixture_digest.value,
        "output_ref": output.output_ref,
        "output_digest": output.output_digest.value,
        "sink_manifest_ref": output.sink_manifest_ref,
        "sink_manifest_digest": output.sink_manifest_digest.value,
        "generator_origin": output.generator_origin,
        "actual_model_fingerprint": output.actual_model_fingerprint,
        "provider_request_ids": list(output.provider_request_ids),
        "input_tokens": output.input_tokens,
        "output_tokens": output.output_tokens,
        "usage_complete": output.usage_complete,
        "digest": output.digest.value,
    }


def _verify_output_document(document: object) -> None:
    required = {
        "schema",
        "suite_id",
        "suite_version",
        "suite_digest",
        "case_id",
        "role",
        "fixture",
        "fixture_digest",
        "oracle_ref",
        "oracle_digest",
        "domain_output",
        "authorized_manifests",
        "isolation_receipts",
        "model_call_outcomes",
        "sink_manifest",
        "evaluation_output",
        "document_digest",
    }
    if (
        not isinstance(document, dict)
        or set(document) != required
        or document.get("schema") != CAPABILITY_OUTPUT_DOCUMENT_SCHEMA
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability case output document fields are invalid",
        )
    core = {key: value for key, value in document.items() if key != "document_digest"}
    if (
        document["document_digest"] != digest_of(core).value
        or document["fixture_digest"] != digest_of(document["fixture"]).value
        or not isinstance(document["evaluation_output"], dict)
        or not isinstance(document["authorized_manifests"], list)
        or not isinstance(document["isolation_receipts"], list)
        or not isinstance(document["model_call_outcomes"], list)
        or not isinstance(document["sink_manifest"], dict)
        or document["sink_manifest"].get("authorized_manifests_digest")
        != digest_of(document["authorized_manifests"]).value
        or document["sink_manifest"].get("isolation_receipts_digest")
        != digest_of(document["isolation_receipts"]).value
        or document["sink_manifest"].get("model_call_outcomes_digest")
        != digest_of(document["model_call_outcomes"]).value
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability case output document digest is invalid",
        )
