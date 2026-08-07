from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


class ContractViolation(ValueError):
    """A validation-only formal contract failed closed."""


def _canonical_value(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, bytes):
        return {"$bytes_utf8": value.decode("utf-8")}
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class Envelope:
    kind: str
    core: Any
    core_digest: str

    @classmethod
    def seal(cls, kind: str, core: Any) -> "Envelope":
        return cls(kind=kind, core=core, core_digest=digest(core))

    def verify(self) -> None:
        if digest(self.core) != self.core_digest:
            raise ContractViolation(f"{self.kind}: digest mismatch")


@dataclass(frozen=True)
class CriterionObligation:
    obligation_id: str
    need_id: str
    ordinal: int
    role: str
    dimension: str

    def validate(self) -> None:
        allowed = {
            "DIRECT_SUPPORT",
            "ENUMERATION_COVERAGE",
            "COUNTEREXAMPLE_CHECK",
            "CONFLICT_DISCLOSURE",
            "UNKNOWN_OR_LIMITATION_DISCLOSURE",
        }
        if self.role not in allowed:
            raise ContractViolation(f"unknown obligation role: {self.role}")
        if self.ordinal < 0 or not self.dimension.strip():
            raise ContractViolation("invalid obligation ordinal or dimension")


@dataclass(frozen=True)
class RequirementNeed:
    need_id: str
    ordinal: int
    question: str
    sufficiency_criterion: str
    obligations: tuple[CriterionObligation, ...]
    required: bool = True

    def validate(self) -> None:
        if not self.required or not self.question.strip() or not self.sufficiency_criterion.strip():
            raise ContractViolation(f"{self.need_id}: incomplete required Need")
        if not self.obligations:
            raise ContractViolation(f"{self.need_id}: no criterion obligations")
        if tuple(item.ordinal for item in self.obligations) != tuple(range(len(self.obligations))):
            raise ContractViolation(f"{self.need_id}: obligation ordinals are not contiguous")
        if any(item.need_id != self.need_id for item in self.obligations):
            raise ContractViolation(f"{self.need_id}: foreign obligation")
        if len({item.obligation_id for item in self.obligations}) != len(self.obligations):
            raise ContractViolation(f"{self.need_id}: duplicate obligation")
        for item in self.obligations:
            item.validate()


@dataclass(frozen=True)
class JointConstraint:
    constraint_id: str
    need_ids: tuple[str, ...]
    criterion: str

    def validate(self, known_needs: set[str]) -> None:
        if len(self.need_ids) < 2 or len(set(self.need_ids)) != len(self.need_ids):
            raise ContractViolation(f"{self.constraint_id}: invalid Need set")
        if not set(self.need_ids).issubset(known_needs) or not self.criterion.strip():
            raise ContractViolation(f"{self.constraint_id}: unresolved joint constraint")


@dataclass(frozen=True)
class RequirementRevision:
    revision_id: str
    needs: tuple[RequirementNeed, ...]
    joint_constraints: tuple[JointConstraint, ...]

    def validate(self, *, expected_need_ids: Sequence[str] | None = None) -> None:
        if tuple(item.ordinal for item in self.needs) != tuple(range(len(self.needs))):
            raise ContractViolation("Need ordinals are not contiguous")
        need_ids = tuple(item.need_id for item in self.needs)
        if len(set(need_ids)) != len(need_ids):
            raise ContractViolation("duplicate Need")
        if expected_need_ids is not None and need_ids != tuple(expected_need_ids):
            raise ContractViolation("Need manifest differs from frozen requirement")
        for need in self.needs:
            need.validate()
        for constraint in self.joint_constraints:
            constraint.validate(set(need_ids))


FULL_OID = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class BuildBudget:
    max_tool_steps: int
    max_files_read: int
    max_source_bytes: int
    max_model_calls: int

    def validate(self) -> None:
        if min(asdict(self).values()) <= 0:
            raise ContractViolation("all build budget limits must be positive")


@dataclass(frozen=True)
class RevisionImpactBuildTarget:
    repository_identity: str
    target_commit: str
    base_commit: str
    requirement: RequirementRevision
    budget: BuildBudget

    def validate(
        self,
        *,
        parent_resolver: Callable[[str], Sequence[str]],
        expected_need_ids: Sequence[str] | None = None,
    ) -> None:
        if not FULL_OID.fullmatch(self.target_commit) or not FULL_OID.fullmatch(self.base_commit):
            raise ContractViolation("BuildTarget requires full 40-character object IDs")
        parents = tuple(parent_resolver(self.target_commit))
        if parents != (self.base_commit,):
            raise ContractViolation("base commit is not the target's unique explicit parent")
        self.requirement.validate(expected_need_ids=expected_need_ids)
        self.budget.validate()


@dataclass(frozen=True)
class AuthorizedInputItem:
    kind: str
    authority_ref: str
    payload: Any

    @property
    def item_digest(self) -> str:
        return digest(self)


@dataclass(frozen=True)
class RenderedInputItem:
    item_digest: str
    rendering_step_ref: str
    role: str
    content: str


@dataclass(frozen=True)
class AuthorizedInputManifest:
    role: str
    capability_ref: str
    strategy_ref: str
    prompt_contract_ref: str
    output_contract_ref: str
    items: tuple[AuthorizedInputItem, ...]

    def validate(self, allowed_kinds: Iterable[str]) -> None:
        if not self.items:
            raise ContractViolation("empty Authorized Input Manifest")
        if any(item.kind not in set(allowed_kinds) for item in self.items):
            raise ContractViolation(f"{self.role}: unauthorized input variant")
        item_digests = tuple(item.item_digest for item in self.items)
        if len(set(item_digests)) != len(item_digests):
            raise ContractViolation("duplicate Authorized Input Item")


def render_manifest(
    manifest: AuthorizedInputManifest,
    *,
    rendering_step_ref: str,
    allowed_kinds: Iterable[str],
) -> tuple[RenderedInputItem, ...]:
    manifest.validate(allowed_kinds)
    rendered = []
    for item in manifest.items:
        rendered.append(
            RenderedInputItem(
                item_digest=item.item_digest,
                rendering_step_ref=rendering_step_ref,
                role="system" if item.kind == "PROMPT_INSTRUCTION" else "user",
                content=canonical_bytes(item.payload).decode("utf-8"),
            )
        )
    return tuple(rendered)


REQUIRED_REQUEST_KEYS = {
    "model",
    "input",
    "tools",
    "tool_choice",
    "parallel_tool_calls",
    "store",
    "background",
    "stream",
    "truncation",
    "text",
    "max_output_tokens",
    "reasoning",
    "metadata",
}

ALLOWED_METADATA_KEYS = {
    "call_id",
    "capability_id",
    "manifest_digest",
    "baseline_id",
}


def validate_no_tools_request(request: Mapping[str, Any]) -> None:
    """Validate the exact provider envelope before a transport can see it.

    This is deliberately structural rather than a serialized-text denylist.
    Authorized inline text may legitimately mention provider field names, while
    attachment, conversation, tool, and hidden-prompt channels must be
    impossible to represent in the envelope itself.
    """

    if set(request) != REQUIRED_REQUEST_KEYS:
        raise ContractViolation("Provider Request field allowlist mismatch")
    if not isinstance(request["model"], str) or not request["model"].strip():
        raise ContractViolation("Provider Request requires an exact model reference")
    if request["tools"] != [] or request["tool_choice"] != "none":
        raise ContractViolation("Provider tools are not disabled")
    for field_name in ("parallel_tool_calls", "store", "background", "stream"):
        if request[field_name] is not False:
            raise ContractViolation(
                f"Provider runtime field must be false: {field_name}"
            )
    if request["truncation"] != "disabled":
        raise ContractViolation("Provider truncation must fail closed")

    input_items = request["input"]
    if not isinstance(input_items, list) or not input_items:
        raise ContractViolation("Provider Request requires inline input_text items")
    for item in input_items:
        if not isinstance(item, Mapping) or set(item) != {"role", "content"}:
            raise ContractViolation("Provider input item field allowlist mismatch")
        if item["role"] not in {"system", "user"}:
            raise ContractViolation("Provider input role is not allowed")
        content_items = item["content"]
        if not isinstance(content_items, list) or len(content_items) != 1:
            raise ContractViolation("Provider input item must contain one inline text item")
        content = content_items[0]
        if not isinstance(content, Mapping) or set(content) != {"type", "text"}:
            raise ContractViolation("Provider content field allowlist mismatch")
        if content["type"] != "input_text" or not isinstance(content["text"], str):
            raise ContractViolation("Provider content must be literal input_text")

    text = request["text"]
    if not isinstance(text, Mapping) or set(text) != {"format"}:
        raise ContractViolation("Provider text configuration field allowlist mismatch")
    output_format = text["format"]
    if not isinstance(output_format, Mapping):
        raise ContractViolation("Provider output format must be an object")
    if output_format.get("type") == "text":
        if set(output_format) != {"type"}:
            raise ContractViolation("Plain text output format has unknown fields")
    elif output_format.get("type") == "json_schema":
        if set(output_format) != {"type", "name", "strict", "schema"}:
            raise ContractViolation("Structured output format field allowlist mismatch")
        if (
            not isinstance(output_format["name"], str)
            or not output_format["name"].strip()
            or output_format["strict"] is not True
            or not isinstance(output_format["schema"], Mapping)
        ):
            raise ContractViolation("Structured output format is incomplete")
    else:
        raise ContractViolation("Provider output format is not supported")

    max_output_tokens = request["max_output_tokens"]
    if (
        isinstance(max_output_tokens, bool)
        or not isinstance(max_output_tokens, int)
        or max_output_tokens <= 0
    ):
        raise ContractViolation("max_output_tokens must be a positive integer")
    if not isinstance(request["reasoning"], Mapping):
        raise ContractViolation("reasoning must be an exact Strategy object")

    metadata = request["metadata"]
    if not isinstance(metadata, Mapping) or set(metadata) != ALLOWED_METADATA_KEYS:
        raise ContractViolation("Provider metadata field allowlist mismatch")
    if any(not isinstance(value, str) or not value for value in metadata.values()):
        raise ContractViolation("Provider metadata values must be non-empty strings")


def build_no_tools_request(
    manifest: AuthorizedInputManifest,
    rendered: Sequence[RenderedInputItem],
    *,
    model: str,
    max_output_tokens: int,
    reasoning: Mapping[str, Any],
    metadata: Mapping[str, str],
    output_schema: Mapping[str, Any],
) -> dict[str, Any]:
    expected = tuple(item.item_digest for item in manifest.items)
    actual = tuple(item.item_digest for item in rendered)
    if actual != expected or len(set(actual)) != len(actual):
        raise ContractViolation("Rendered Request does not bidirectionally cover Manifest Items")
    if any(not item.rendering_step_ref for item in rendered):
        raise ContractViolation("Rendered Item lacks Rendering Step reference")
    for authorized, rendered_item in zip(manifest.items, rendered, strict=True):
        expected_role = (
            "system" if authorized.kind == "PROMPT_INSTRUCTION" else "user"
        )
        expected_content = canonical_bytes(authorized.payload).decode("utf-8")
        if (
            rendered_item.role != expected_role
            or rendered_item.content != expected_content
        ):
            raise ContractViolation(
                "Rendered Request content differs from its Manifest Item"
            )
    if metadata.get("manifest_digest") != digest(manifest):
        raise ContractViolation("Provider metadata is not bound to the Manifest")
    if metadata.get("capability_id") != manifest.capability_ref:
        raise ContractViolation("Provider metadata is not bound to the Capability")
    request = {
        "model": model,
        "input": [
            {
                "role": item.role,
                "content": [{"type": "input_text", "text": item.content}],
            }
            for item in rendered
        ],
        "tools": [],
        "tool_choice": "none",
        "parallel_tool_calls": False,
        "store": False,
        "background": False,
        "stream": False,
        "truncation": "disabled",
        "text": {"format": dict(output_schema)},
        "max_output_tokens": max_output_tokens,
        "reasoning": dict(reasoning),
        "metadata": dict(metadata),
    }
    validate_no_tools_request(request)
    return request


@dataclass(frozen=True)
class IsolationReceipt:
    request_digest: str
    adapter_profile_ref: str
    live_conformance_result_ref: str

    @classmethod
    def issue(
        cls,
        request: Mapping[str, Any],
        *,
        adapter_profile_ref: str,
        live_conformance_result_ref: str,
    ) -> "IsolationReceipt":
        validate_no_tools_request(request)
        if not live_conformance_result_ref:
            raise ContractViolation("Provider request is not eligible for an isolation receipt")
        return cls(digest(request), adapter_profile_ref, live_conformance_result_ref)

    def verify_dispatched_body(self, body: Mapping[str, Any]) -> None:
        if digest(body) != self.request_digest:
            raise ContractViolation("dispatched body differs from pre-dispatch receipt")


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    operation: str
    repository_identity: str
    revision: str
    path: str | None
    payload: bytes
    complete: bool
    terminal: bool


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    artifact_id: str
    start_byte: int
    end_byte: int
    selected_bytes: bytes

    @classmethod
    def materialize(
        cls,
        evidence_id: str,
        artifact: Artifact,
        start_byte: int,
        end_byte: int,
    ) -> "Evidence":
        if not 0 <= start_byte < end_byte <= len(artifact.payload):
            raise ContractViolation("Evidence range is outside its Artifact")
        return cls(
            evidence_id=evidence_id,
            artifact_id=artifact.artifact_id,
            start_byte=start_byte,
            end_byte=end_byte,
            selected_bytes=artifact.payload[start_byte:end_byte],
        )


def evidence_for_literal(evidence_id: str, artifact: Artifact, literal: bytes) -> Evidence:
    positions = []
    start = 0
    while True:
        found = artifact.payload.find(literal, start)
        if found < 0:
            break
        positions.append(found)
        start = found + 1
    if len(positions) != 1:
        raise ContractViolation(f"literal must occur exactly once, found {len(positions)}")
    return Evidence.materialize(evidence_id, artifact, positions[0], positions[0] + len(literal))


def verify_closed_change_set(
    artifact: Artifact,
    expected_members: Sequence[tuple[str, str]],
    *,
    declared_cardinality: int,
) -> None:
    if artifact.operation != "COMPARE" or not artifact.complete or not artifact.terminal:
        raise ContractViolation("change set Artifact is partial or non-terminal")
    actual: list[tuple[str, str]] = []
    for raw_line in artifact.payload.decode("utf-8").splitlines():
        fields = raw_line.split("\t")
        if len(fields) != 2:
            raise ContractViolation("unsupported change set member")
        actual.append((fields[0], fields[1]))
    if declared_cardinality != len(actual) or tuple(actual) != tuple(expected_members):
        raise ContractViolation("change set member/cardinality closure mismatch")


def verify_closed_literal_selection(
    artifact: Artifact,
    literal: bytes,
    expected_ranges: Sequence[tuple[int, int]],
    *,
    scanned_bytes: int,
    source_blob_bytes: int,
) -> None:
    if artifact.operation != "READ" or not artifact.complete or not artifact.terminal:
        raise ContractViolation("literal selection source is partial or non-terminal")
    if scanned_bytes != len(artifact.payload) or source_blob_bytes != len(artifact.payload):
        raise ContractViolation("literal selection did not scan the full source unit")
    actual = []
    start = 0
    while True:
        found = artifact.payload.find(literal, start)
        if found < 0:
            break
        actual.append((found, found + len(literal)))
        start = found + 1
    if tuple(actual) != tuple(expected_ranges):
        raise ContractViolation("literal selection range closure mismatch")


@dataclass(frozen=True)
class EntityState:
    entity_id: str
    kind: str
    external_key: str
    anchor_evidence_id: str


@dataclass(frozen=True)
class AtomicFact:
    fact_id: str
    subject_entity_id: str
    predicate: str
    role_terms: tuple[tuple[str, str], ...]
    modality: str
    evidence_id: str
    context_revision: str
    related_obligation_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClosedChangeSetFact:
    fact_id: str
    subject_entity_id: str
    members: tuple[tuple[str, str], ...]
    cardinality: int
    context_revision: str
    related_obligation_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClosedLiteralSelectionFact:
    fact_id: str
    subject_entity_id: str
    selector: str
    ranges: tuple[tuple[int, int], ...]
    context_revision: str
    related_obligation_ids: tuple[str, ...]


def review_atomic_fact(fact: AtomicFact, evidence: Evidence, entities: Mapping[str, EntityState]) -> None:
    if fact.subject_entity_id not in entities:
        raise ContractViolation("Fact subject is not a published Entity")
    if fact.evidence_id != evidence.evidence_id or not fact.role_terms:
        raise ContractViolation("Fact Evidence or role terms are invalid")
    for _, term in fact.role_terms:
        if term.encode("utf-8") not in evidence.selected_bytes:
            raise ContractViolation(f"Evidence does not directly entail term: {term}")
    forbidden = ("library default", "runtime behavior", "author intent")
    rendered = canonical_bytes(fact.role_terms).decode("utf-8").lower()
    if any(item in rendered for item in forbidden):
        raise ContractViolation("direct Fact contains non-observed semantics")


@dataclass(frozen=True)
class FormalInference:
    inference_id: str
    affected_entity_id: str
    aspect: str
    relation: str
    premise_ids: tuple[str, ...]
    context_revision: str
    related_obligation_ids: tuple[str, ...]
    unknown_boundary: str | None = None
    missing_premises: tuple[str, ...] = ()


def review_inference(
    inference: FormalInference,
    *,
    premise_snapshot_id: str,
    snapshot_id_by_knowledge_id: Mapping[str, str],
    entities: Mapping[str, EntityState],
) -> None:
    if inference.affected_entity_id not in entities or not inference.premise_ids:
        raise ContractViolation("Inference target or premise set is invalid")
    if any(snapshot_id_by_knowledge_id.get(ref) != premise_snapshot_id for ref in inference.premise_ids):
        raise ContractViolation("Inference premise is absent or belongs to another Snapshot")
    allowed_aspects = {
        "DEPENDENCY",
        "API_CALL",
        "DATA_FLOW",
        "CONTROL_FLOW",
        "EXCEPTION_FLOW",
        "VALUE_SEMANTICS",
        "REFRESH_BEHAVIOR",
        "REVISION_SCOPE",
    }
    allowed_relations = {
        "ADDS",
        "REMOVES",
        "REPLACES",
        "TRANSFORMS_TO",
        "VALIDATES_BEFORE",
        "RETURNS_WHEN",
        "TREATS_AS",
        "PRESERVES_WITHIN_BOUNDARY",
        "CHANGES_ORDER",
        "ENUMERATES_COMPLETE_SET",
        "NOT_ESTABLISHED_WITHIN_BOUNDARY",
    }
    if inference.aspect not in allowed_aspects or inference.relation not in allowed_relations:
        raise ContractViolation("Inference must contain one entity, aspect, and relation")
    if inference.unknown_boundary is not None and not inference.missing_premises:
        raise ContractViolation("bounded Unknown must name its missing formal premise")
    if inference.unknown_boundary is None and inference.missing_premises:
        raise ContractViolation("missing premises cannot be converted into a concrete conclusion")


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    namespace: str
    sequence: int
    entities: Mapping[str, EntityState]
    facts: Mapping[str, AtomicFact | ClosedChangeSetFact | ClosedLiteralSelectionFact]
    inferences: Mapping[str, FormalInference]


class ValidationAuthorityStore:
    def __init__(self, namespace: str):
        if namespace.startswith("production"):
            raise ContractViolation("validation store cannot use a production namespace")
        self.namespace = namespace
        self._snapshots: list[Snapshot] = []

    @property
    def current(self) -> Snapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def publish(
        self,
        *,
        entities: Iterable[EntityState] = (),
        facts: Iterable[AtomicFact | ClosedChangeSetFact | ClosedLiteralSelectionFact] = (),
        inferences: Iterable[FormalInference] = (),
    ) -> Snapshot:
        base = self.current
        entity_map = dict(base.entities) if base else {}
        fact_map = dict(base.facts) if base else {}
        inference_map = dict(base.inferences) if base else {}
        for entity in entities:
            entity_map[entity.entity_id] = entity
        for fact in facts:
            if fact.subject_entity_id not in entity_map:
                raise ContractViolation("Fact cannot publish before its Entity")
            fact_map[fact.fact_id] = fact
        knowledge_snapshot_map = {
            item_id: base.snapshot_id
            for item_id in tuple(base.facts) + tuple(base.inferences)
        } if base else {}
        for inference in inferences:
            review_inference(
                inference,
                premise_snapshot_id=base.snapshot_id if base else "",
                snapshot_id_by_knowledge_id=knowledge_snapshot_map,
                entities=entity_map,
            )
            inference_map[inference.inference_id] = inference
        snapshot = Snapshot(
            snapshot_id=f"{self.namespace}:snapshot:{len(self._snapshots) + 1}",
            namespace=self.namespace,
            sequence=len(self._snapshots) + 1,
            entities=entity_map,
            facts=fact_map,
            inferences=inference_map,
        )
        self._snapshots.append(snapshot)
        return snapshot


@dataclass(frozen=True)
class ObligationSupport:
    obligation_id: str
    snapshot_id: str
    formal_knowledge_ids: tuple[str, ...]


@dataclass(frozen=True)
class NeedAssessment:
    need_id: str
    outcome: str
    supports: tuple[ObligationSupport, ...]


@dataclass(frozen=True)
class JointConstraintAssessment:
    constraint_id: str
    outcome: str
    need_ids: tuple[str, ...]


def assess_overall(
    requirement: RequirementRevision,
    snapshot: Snapshot,
    need_assessments: Sequence[NeedAssessment],
    joint_assessments: Sequence[JointConstraintAssessment],
) -> str:
    by_need = {item.need_id: item for item in need_assessments}
    if set(by_need) != {item.need_id for item in requirement.needs}:
        return "NOT_SATISFIED"
    knowledge_ids = set(snapshot.facts) | set(snapshot.inferences)
    for need in requirement.needs:
        assessment = by_need[need.need_id]
        if assessment.outcome != "SATISFIED":
            return "NOT_SATISFIED"
        support_by_obligation = {item.obligation_id: item for item in assessment.supports}
        expected = {item.obligation_id for item in need.obligations}
        if set(support_by_obligation) != expected:
            return "NOT_SATISFIED"
        for support in support_by_obligation.values():
            if support.snapshot_id != snapshot.snapshot_id or not support.formal_knowledge_ids:
                return "NOT_SATISFIED"
            if not set(support.formal_knowledge_ids).issubset(knowledge_ids):
                return "NOT_SATISFIED"
    by_joint = {item.constraint_id: item for item in joint_assessments}
    if set(by_joint) != {item.constraint_id for item in requirement.joint_constraints}:
        return "NOT_SATISFIED"
    for constraint in requirement.joint_constraints:
        assessment = by_joint[constraint.constraint_id]
        if assessment.outcome != "SATISFIED" or assessment.need_ids != constraint.need_ids:
            return "NOT_SATISFIED"
    return "SATISFIED"


@dataclass(frozen=True)
class AnswerClaim:
    claim_id: str
    need_id: str
    text: str
    support: ObligationSupport


@dataclass(frozen=True)
class AnswerCandidate:
    snapshot_id: str
    claims: tuple[AnswerClaim, ...]
    answer_body: str


@dataclass(frozen=True)
class KnowledgeUseIsolationProof:
    source_operation_attempts: int = 0
    source_operations_executed: int = 0
    artifact_payload_read_attempts: int = 0
    evidence_content_read_attempts: int = 0
    investigation_attach_attempts: int = 0

    def validate(self) -> None:
        if any(asdict(self).values()):
            raise ContractViolation("Knowledge Use Session attempted a source-side operation")


def authorize_answer(
    requirement: RequirementRevision,
    snapshot: Snapshot,
    overall: str,
    candidate: AnswerCandidate,
    isolation: KnowledgeUseIsolationProof,
) -> str:
    isolation.validate()
    if overall != "SATISFIED" or candidate.snapshot_id != snapshot.snapshot_id:
        raise ContractViolation("Answer is not bound to a sufficient exact Snapshot")
    if {claim.need_id for claim in candidate.claims} != {need.need_id for need in requirement.needs}:
        raise ContractViolation("Answer omits a required Need")
    required_obligations = {
        obligation.obligation_id
        for need in requirement.needs
        for obligation in need.obligations
    }
    if {claim.support.obligation_id for claim in candidate.claims} != required_obligations:
        raise ContractViolation("Answer does not cover every Criterion Obligation")
    knowledge_ids = set(snapshot.facts) | set(snapshot.inferences)
    for claim in candidate.claims:
        if claim.support.snapshot_id != snapshot.snapshot_id:
            raise ContractViolation("Answer support belongs to another Snapshot")
        if not set(claim.support.formal_knowledge_ids).issubset(knowledge_ids):
            raise ContractViolation("Answer has unsupported Claim")
    if not candidate.answer_body.strip():
        raise ContractViolation("empty answer")
    return digest({"snapshot": snapshot.snapshot_id, "answer": candidate.answer_body})


@dataclass(frozen=True)
class DirectClaimOracleItem:
    claim_id: str
    semantic_key: str
    evidence_digest: str


def compare_claim_preservation(
    oracle: Sequence[DirectClaimOracleItem],
    delivered_semantic_keys: Sequence[str],
) -> None:
    expected = {item.semantic_key for item in oracle}
    actual = set(delivered_semantic_keys)
    if len(expected) != len(oracle):
        raise ContractViolation("Direct Claim Oracle contains duplicate semantic claims")
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ContractViolation(f"Claim preservation mismatch: missing={missing}, extra={extra}")


class ProductionReader:
    def read(self, snapshot: Snapshot) -> Snapshot:
        if not snapshot.namespace.startswith("production"):
            raise ContractViolation("production Reader rejects validation Snapshot")
        return snapshot


def assert_acyclic(edges: Mapping[str, Sequence[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ContractViolation("digest/reference graph contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for dependency in edges.get(node, ()):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for item in edges:
        visit(item)


class LocalGitReadOnlyProvider:
    """Small validation provider. It never reads the mutable worktree."""

    def __init__(self, repository: Path, repository_identity: str):
        self.repository = repository.resolve()
        self.repository_identity = repository_identity

    def _git(self, *args: str) -> bytes:
        result = subprocess.run(
            ["git", "-C", str(self.repository), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise ContractViolation(result.stderr.decode("utf-8", errors="replace").strip())
        return result.stdout

    def parents(self, commit: str) -> tuple[str, ...]:
        fields = self._git("show", "-s", "--format=%P", commit).decode("ascii").strip()
        return tuple(fields.split()) if fields else ()

    def resolve(self, revision: str) -> str:
        oid = self._git("rev-parse", f"{revision}^{{commit}}").decode("ascii").strip()
        if not FULL_OID.fullmatch(oid):
            raise ContractViolation("Provider did not resolve a full commit OID")
        return oid

    def compare(self, base: str, target: str) -> Artifact:
        payload = self._git("diff-tree", "--no-commit-id", "--name-status", "-r", base, target)
        return Artifact(
            artifact_id=f"compare:{digest(payload)}",
            operation="COMPARE",
            repository_identity=self.repository_identity,
            revision=target,
            path=None,
            payload=payload,
            complete=True,
            terminal=True,
        )

    def read(self, commit: str, path: str) -> Artifact:
        if path.startswith("/") or ".." in Path(path).parts:
            raise ContractViolation("invalid Git path")
        payload = self._git("show", f"{commit}:{path}")
        return Artifact(
            artifact_id=f"blob:{commit}:{path}:{digest(payload)}",
            operation="READ",
            repository_identity=self.repository_identity,
            revision=commit,
            path=path,
            payload=payload,
            complete=True,
            terminal=True,
        )
