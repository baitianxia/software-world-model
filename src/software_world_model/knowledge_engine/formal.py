"""Formal knowledge admission and single-scope snapshot publication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from .scope import KnowledgeScopeService, ScopePurpose

if TYPE_CHECKING:
    from software_world_model.source_integration.operations import SourceArtifact


# Retrieval terms only widen the bounded candidate set. Semantic sufficiency is
# decided separately and must never be inferred from a lexical match alone.
KNOWLEDGE_TERM_MATCH_POLICY = "ANY_HINT_MATCH_CASEFOLD@1"


class AdmissionStatus(str, Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


class KnowledgeObjectKind(str, Enum):
    ENTITY = "ENTITY"
    FACT = "FACT"
    INFERENCE = "INFERENCE"


@dataclass(frozen=True, slots=True)
class KnowledgeSchema:
    schema_id: str
    version: str
    allowed_entity_types: tuple[str, ...]
    allowed_fact_predicates: tuple[str, ...]
    allowed_inference_types: tuple[str, ...]
    digest: Digest

    @classmethod
    def initial(cls) -> "KnowledgeSchema":
        core = {
            "schema_id": "SWM-KNOWLEDGE-SCHEMA",
            "version": "INITIAL@1",
            "allowed_entity_types": (
                "SOFTWARE_SYSTEM",
                "MODULE",
                "SOURCE_FILE",
                "CODE_SYMBOL",
                "ENDPOINT",
                "CONFIGURATION",
            ),
            "allowed_fact_predicates": (
                "DECLARES",
                "CALLS",
                "DEPENDS_ON",
                "EXPOSES",
                "HAS_VALUE",
                "CHANGED_IN",
                "DESCRIBED_AS",
            ),
            "allowed_inference_types": (
                "STRUCTURE",
                "BEHAVIOR",
                "HISTORY_IMPACT",
                "BUSINESS_CAPABILITY",
                "BUSINESS_CONSTRAINT",
            ),
        }
        return cls(**core, digest=digest_of(core))


@dataclass(frozen=True, slots=True)
class KnowledgeContext:
    terms: tuple[tuple[str, str], ...]
    digest: Digest

    @classmethod
    def create(cls, terms: Mapping[str, str] | None = None) -> "KnowledgeContext":
        normalized: list[tuple[str, str]] = []
        for key, value in (terms or {}).items():
            normalized.append((_text(key, "context dimension"), _text(value, "context value")))
        normalized.sort()
        if len({key for key, _ in normalized}) != len(normalized):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "context dimensions must be unique")
        frozen = tuple(normalized)
        return cls(terms=frozen, digest=digest_of({"context": frozen, "canonicalization": "1"}))


@dataclass(frozen=True, slots=True)
class EvidenceProposal:
    evidence_key: str
    artifact: SourceArtifact
    byte_start: int
    byte_end: int
    locator: str


@dataclass(frozen=True, slots=True)
class EntityProposal:
    candidate_key: str
    entity_type: str
    natural_key: str
    label: str
    context: KnowledgeContext
    evidence_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FactProposal:
    candidate_key: str
    subject_candidate_key: str | None
    subject_entity_id: StableId | None
    predicate: str
    object_value: str
    context: KnowledgeContext
    evidence_keys: tuple[str, ...]
    reviewed_grounding: "ReviewedFactGrounding | None" = None


@dataclass(frozen=True, slots=True)
class ReviewedFactGrounding:
    """Tamper-evident references to separate proposal and review model calls."""

    schema_version: str
    candidate_key: str
    proposer_model_call_id: StableId
    proposer_output_digest: Digest
    reviewer_model_call_id: StableId
    reviewer_output_digest: Digest
    actual_model_fingerprint: str
    need_ids: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        candidate_key: str,
        proposer_model_call_id: StableId,
        proposer_output_digest: Digest,
        reviewer_model_call_id: StableId,
        reviewer_output_digest: Digest,
        actual_model_fingerprint: str,
        need_ids: tuple[str, ...] = ("OBJECTIVE",),
    ) -> "ReviewedFactGrounding":
        if proposer_model_call_id == reviewer_model_call_id:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "fact proposal and review must use distinct model calls",
            )
        normalized_need_ids = tuple(
            _text(item, "reviewed fact Need ID") for item in need_ids
        )
        if not normalized_need_ids or len(normalized_need_ids) != len(
            set(normalized_need_ids)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "reviewed fact Need IDs must be non-empty and unique",
            )
        core = {
            "schema_version": "REVIEWED_FACT_GROUNDING@2",
            "candidate_key": _text(candidate_key, "reviewed fact candidate key"),
            "proposer_model_call_id": proposer_model_call_id.value,
            "proposer_output_digest": proposer_output_digest.value,
            "reviewer_model_call_id": reviewer_model_call_id.value,
            "reviewer_output_digest": reviewer_output_digest.value,
            "actual_model_fingerprint": _text(
                actual_model_fingerprint, "reviewed fact actual model fingerprint"
            ),
            "need_ids": normalized_need_ids,
        }
        return cls(
            schema_version="REVIEWED_FACT_GROUNDING@2",
            candidate_key=core["candidate_key"],
            proposer_model_call_id=proposer_model_call_id,
            proposer_output_digest=proposer_output_digest,
            reviewer_model_call_id=reviewer_model_call_id,
            reviewer_output_digest=reviewer_output_digest,
            actual_model_fingerprint=core["actual_model_fingerprint"],
            need_ids=normalized_need_ids,
            digest=digest_of(core),
        )

    def verify_digest(self) -> bool:
        core = {
            "schema_version": self.schema_version,
            "candidate_key": self.candidate_key,
            "proposer_model_call_id": self.proposer_model_call_id.value,
            "proposer_output_digest": self.proposer_output_digest.value,
            "reviewer_model_call_id": self.reviewer_model_call_id.value,
            "reviewer_output_digest": self.reviewer_output_digest.value,
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "need_ids": self.need_ids,
        }
        return (
            self.schema_version == "REVIEWED_FACT_GROUNDING@2"
            and self.proposer_model_call_id != self.reviewer_model_call_id
            and bool(self.need_ids)
            and len(self.need_ids) == len(set(self.need_ids))
            and digest_of(core) == self.digest
        )


@dataclass(frozen=True, slots=True)
class InferenceProposal:
    candidate_key: str
    inference_type: str
    proposition: str
    premise_references: tuple[StableId, ...]
    rule_ref: str
    context: KnowledgeContext
    reviewed_need_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeCandidateBundle:
    schema_version: str
    evidence: tuple[EvidenceProposal, ...]
    entities: tuple[EntityProposal, ...]
    facts: tuple[FactProposal, ...]
    inferences: tuple[InferenceProposal, ...]


@dataclass(frozen=True, slots=True)
class EvidenceSnapshot:
    evidence_id: StableId
    artifact_id: StableId
    source_context_id: StableId
    byte_start: int
    byte_end: int
    locator: str
    excerpt: str
    excerpt_digest: Digest
    artifact_content_digest: Digest
    digest: Digest


@dataclass(frozen=True, slots=True)
class KnowledgeEntity:
    entity_id: StableId
    schema_version: str
    entity_type: str
    natural_key: str
    label: str
    context: KnowledgeContext
    evidence_references: tuple[StableId, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    fact_id: StableId
    schema_version: str
    subject_entity_id: StableId
    predicate: str
    object_value: str
    context: KnowledgeContext
    evidence_references: tuple[StableId, ...]
    reviewed_grounding: ReviewedFactGrounding | None
    digest: Digest


@dataclass(frozen=True, slots=True)
class KnowledgeInference:
    inference_id: StableId
    schema_version: str
    inference_type: str
    proposition: str
    premise_references: tuple[StableId, ...]
    rule_ref: str
    context: KnowledgeContext
    reviewed_need_ids: tuple[str, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class SnapshotMember:
    kind: KnowledgeObjectKind
    object_id: StableId
    object_digest: Digest


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    snapshot_id: StableId
    scope_id: StableId
    snapshot_revision: Revision
    previous_snapshot_id: StableId | None
    schema_version: str
    members: tuple[SnapshotMember, ...]
    manifest_digest: Digest
    published_at: datetime


@dataclass(frozen=True, slots=True)
class FormalKnowledgeRecord:
    kind: KnowledgeObjectKind
    object_id: StableId
    object_digest: Digest
    type_name: str
    text: str
    context_digest: Digest
    support_references: tuple[StableId, ...]
    reviewed_need_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationFinding:
    code: str
    candidate_key: str
    message: str


@dataclass(frozen=True, slots=True)
class KnowledgeAdmissionResult:
    admission_id: StableId
    status: AdmissionStatus
    request_digest: Digest
    findings: tuple[VerificationFinding, ...]
    snapshot: KnowledgeSnapshot | None
    entity_references: tuple[StableId, ...]
    fact_references: tuple[StableId, ...]
    inference_references: tuple[StableId, ...]
    decided_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class ValidatedKnowledgeBatch:
    evidence: tuple[EvidenceSnapshot, ...]
    entities: tuple[KnowledgeEntity, ...]
    facts: tuple[KnowledgeFact, ...]
    inferences: tuple[KnowledgeInference, ...]


class FormalKnowledgeRepository(Protocol):
    def current_snapshot(self, scope_id: StableId) -> KnowledgeSnapshot | None: ...

    def get_snapshot(self, snapshot_id: StableId) -> KnowledgeSnapshot: ...

    def member_exists(self, snapshot_id: StableId, object_id: StableId) -> bool: ...

    def query_snapshot(
        self,
        *,
        snapshot_id: StableId,
        kinds: tuple[KnowledgeObjectKind, ...],
        type_names: tuple[str, ...],
        terms: tuple[str, ...],
        cursor: int,
        limit: int,
    ) -> tuple[tuple[FormalKnowledgeRecord, ...], int | None]: ...

    def get_record(self, snapshot_id: StableId, object_id: StableId) -> FormalKnowledgeRecord: ...

    def get_evidence(self, evidence_id: StableId) -> EvidenceSnapshot: ...

    def record_rejection(
        self,
        *,
        scope_id: StableId,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        findings: tuple[VerificationFinding, ...],
        decided_at: datetime,
    ) -> KnowledgeAdmissionResult: ...

    def admit_and_publish(
        self,
        *,
        scope_id: StableId,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        schema: KnowledgeSchema,
        batch: ValidatedKnowledgeBatch,
        decided_at: datetime,
    ) -> KnowledgeAdmissionResult: ...


class ReviewedFactGroundingVerifier(Protocol):
    def verify(
        self,
        *,
        proposal: FactProposal,
        subject_proposal: EntityProposal | None,
        evidence_proposals: tuple[EvidenceProposal, ...],
    ) -> bool: ...


class FormalKnowledgeService:
    def __init__(
        self,
        repository: FormalKnowledgeRepository,
        scopes: KnowledgeScopeService,
        *,
        schema: KnowledgeSchema | None = None,
        reviewed_fact_verifier: ReviewedFactGroundingVerifier | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        self._schema = schema or KnowledgeSchema.initial()
        self._reviewed_fact_verifier = reviewed_fact_verifier
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def admit_and_publish(
        self,
        *,
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        bundle: KnowledgeCandidateBundle,
        caller_ref: str,
        classification: str,
    ) -> KnowledgeAdmissionResult:
        now = self._now()
        self._scopes.read_scope_state_assertion(
            scope_id=scope_id,
            expected_revision=expected_scope_revision,
            purpose=ScopePurpose.SNAPSHOT_PUBLICATION,
            caller_ref=_text(caller_ref, "caller reference"),
            request_ref=idempotency_key.value,
            classification=_text(classification, "classification"),
        )
        request_digest = _bundle_digest(scope_id, expected_current_snapshot_id, bundle)
        findings, batch = self._validate_bundle(
            scope_id, expected_current_snapshot_id, bundle
        )
        if findings:
            return self._repository.record_rejection(
                scope_id=scope_id,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
                findings=findings,
                decided_at=now,
            )
        return self._repository.admit_and_publish(
            scope_id=scope_id,
            expected_current_snapshot_id=expected_current_snapshot_id,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            schema=self._schema,
            batch=batch,
            decided_at=now,
        )

    def current_snapshot(self, scope_id: StableId) -> KnowledgeSnapshot | None:
        return self._repository.current_snapshot(scope_id)

    def get_snapshot(self, snapshot_id: StableId) -> KnowledgeSnapshot:
        return self._repository.get_snapshot(snapshot_id)

    def query_snapshot(
        self,
        *,
        snapshot_id: StableId,
        kinds: tuple[KnowledgeObjectKind, ...],
        type_names: tuple[str, ...] = (),
        terms: tuple[str, ...] = (),
        cursor: int = 0,
        limit: int = 50,
    ) -> tuple[tuple[FormalKnowledgeRecord, ...], int | None]:
        if cursor < 0 or limit < 1 or limit > 500:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "knowledge query cursor or limit is invalid")
        return self._repository.query_snapshot(
            snapshot_id=snapshot_id,
            kinds=kinds,
            type_names=type_names,
            terms=terms,
            cursor=cursor,
            limit=limit,
        )

    def get_record(self, snapshot_id: StableId, object_id: StableId) -> FormalKnowledgeRecord:
        return self._repository.get_record(snapshot_id, object_id)

    def source_locators(
        self, snapshot_id: StableId, object_id: StableId
    ) -> tuple[str, ...]:
        """Resolve one formal record to its exact, repository-relative evidence."""

        locators: list[str] = []
        visited: set[StableId] = set()

        def visit(reference: StableId) -> None:
            if reference in visited:
                return
            visited.add(reference)
            if not self._repository.member_exists(snapshot_id, reference):
                locator = self._repository.get_evidence(reference).locator
                if locator not in locators:
                    locators.append(locator)
                return
            record = self._repository.get_record(snapshot_id, reference)
            for support in record.support_references:
                visit(support)

        visit(object_id)
        return tuple(locators)

    def _validate_bundle(
        self,
        scope_id: StableId,
        expected_snapshot_id: StableId | None,
        bundle: KnowledgeCandidateBundle,
    ) -> tuple[tuple[VerificationFinding, ...], ValidatedKnowledgeBatch]:
        findings: list[VerificationFinding] = []
        if not (bundle.entities or bundle.facts or bundle.inferences):
            findings.append(
                VerificationFinding("EMPTY_BUNDLE", "bundle", "admission bundle has no knowledge candidates")
            )
        if bundle.schema_version != self._schema.version:
            findings.append(
                VerificationFinding("SCHEMA_MISMATCH", "bundle", "candidate schema is not INITIAL")
            )
        all_keys = [
            *(item.evidence_key for item in bundle.evidence),
            *(item.candidate_key for item in bundle.entities),
            *(item.candidate_key for item in bundle.facts),
            *(item.candidate_key for item in bundle.inferences),
        ]
        if len(all_keys) != len(set(all_keys)):
            findings.append(
                VerificationFinding("DUPLICATE_CANDIDATE_KEY", "bundle", "candidate keys are not unique")
            )

        evidence_by_key: dict[str, EvidenceSnapshot] = {}
        for proposal in bundle.evidence:
            artifact = proposal.artifact
            if artifact.truncated:
                findings.append(
                    VerificationFinding(
                        "TRUNCATED_ARTIFACT", proposal.evidence_key, "truncated artifacts cannot prove full facts"
                    )
                )
                continue
            if not (0 <= proposal.byte_start < proposal.byte_end <= len(artifact.payload)):
                findings.append(
                    VerificationFinding(
                        "EVIDENCE_RANGE_INVALID", proposal.evidence_key, "evidence range exceeds artifact payload"
                    )
                )
                continue
            excerpt_bytes = artifact.payload[proposal.byte_start : proposal.byte_end]
            try:
                excerpt = excerpt_bytes.decode("utf-8")
            except UnicodeDecodeError:
                findings.append(
                    VerificationFinding(
                        "EVIDENCE_ENCODING_UNSUPPORTED", proposal.evidence_key, "INITIAL schema requires UTF-8 text"
                    )
                )
                continue
            core = {
                "artifact_id": artifact.artifact_id.value,
                "source_context_id": artifact.source_context_id.value,
                "byte_start": proposal.byte_start,
                "byte_end": proposal.byte_end,
                "locator": proposal.locator,
                "excerpt_digest": digest_of(excerpt).value,
                "artifact_content_digest": artifact.content_digest.value,
            }
            digest = digest_of(core)
            evidence_by_key[proposal.evidence_key] = EvidenceSnapshot(
                evidence_id=_stable("evidence", digest),
                artifact_id=artifact.artifact_id,
                source_context_id=artifact.source_context_id,
                byte_start=proposal.byte_start,
                byte_end=proposal.byte_end,
                locator=_text(proposal.locator, "evidence locator"),
                excerpt=excerpt,
                excerpt_digest=digest_of(excerpt),
                artifact_content_digest=artifact.content_digest,
                digest=digest,
            )

        entities: list[KnowledgeEntity] = []
        entity_by_candidate: dict[str, StableId] = {}
        entity_proposal_by_candidate = {
            item.candidate_key: item for item in bundle.entities
        }
        for proposal in bundle.entities:
            if proposal.entity_type not in self._schema.allowed_entity_types:
                findings.append(
                    VerificationFinding("ENTITY_TYPE_INVALID", proposal.candidate_key, "entity type is not in schema")
                )
                continue
            evidence_refs, missing = _resolve_evidence(proposal.evidence_keys, evidence_by_key)
            if missing or not evidence_refs:
                findings.append(
                    VerificationFinding("ENTITY_EVIDENCE_MISSING", proposal.candidate_key, "entity requires valid evidence")
                )
                continue
            identity = digest_of(
                {
                    "schema_version": self._schema.version,
                    "entity_type": proposal.entity_type,
                    "natural_key": proposal.natural_key,
                    "label": proposal.label,
                    "context_digest": proposal.context.digest.value,
                    "evidence_references": tuple(
                        item.value for item in evidence_refs
                    ),
                }
            )
            entity_id = _stable("knowledge_entity", identity)
            core = {
                "entity_id": entity_id.value,
                "schema_version": self._schema.version,
                "entity_type": proposal.entity_type,
                "natural_key": _text(proposal.natural_key, "entity natural key"),
                "label": _text(proposal.label, "entity label"),
                "context": proposal.context,
                "evidence_references": tuple(item.value for item in evidence_refs),
            }
            entity = KnowledgeEntity(
                entity_id=entity_id,
                schema_version=self._schema.version,
                entity_type=proposal.entity_type,
                natural_key=proposal.natural_key,
                label=proposal.label,
                context=proposal.context,
                evidence_references=evidence_refs,
                digest=digest_of(core),
            )
            entities.append(entity)
            entity_by_candidate[proposal.candidate_key] = entity_id

        facts: list[KnowledgeFact] = []
        for proposal in bundle.facts:
            if proposal.predicate not in self._schema.allowed_fact_predicates:
                findings.append(
                    VerificationFinding("FACT_PREDICATE_INVALID", proposal.candidate_key, "predicate is not in schema")
                )
                continue
            subject = proposal.subject_entity_id
            if proposal.subject_candidate_key is not None:
                subject = entity_by_candidate.get(proposal.subject_candidate_key)
            if subject is None:
                findings.append(
                    VerificationFinding("FACT_SUBJECT_DANGLING", proposal.candidate_key, "fact subject is unresolved")
                )
                continue
            if proposal.subject_entity_id is not None:
                if expected_snapshot_id is None or not self._repository.member_exists(
                    expected_snapshot_id, proposal.subject_entity_id
                ):
                    findings.append(
                        VerificationFinding("FACT_SUBJECT_DANGLING", proposal.candidate_key, "formal subject is not in base snapshot")
                    )
                    continue
            evidence_refs, missing = _resolve_evidence(proposal.evidence_keys, evidence_by_key)
            evidence_text = tuple(
                evidence_by_key[key].excerpt for key in proposal.evidence_keys if key in evidence_by_key
            )
            if missing or not evidence_refs:
                findings.append(
                    VerificationFinding(
                        "FACT_OUTSIDE_EVIDENCE",
                        proposal.candidate_key,
                        "fact requires valid exact evidence",
                    )
                )
                continue
            directly_contained = any(
                proposal.object_value in text for text in evidence_text
            )
            if proposal.reviewed_grounding is not None:
                evidence_proposals = tuple(
                    item
                    for key in proposal.evidence_keys
                    for item in bundle.evidence
                    if item.evidence_key == key
                )
                try:
                    reviewed = (
                        self._reviewed_fact_verifier is not None
                        and proposal.reviewed_grounding.verify_digest()
                        and self._reviewed_fact_verifier.verify(
                            proposal=proposal,
                            subject_proposal=(
                                entity_proposal_by_candidate.get(
                                    proposal.subject_candidate_key
                                )
                                if proposal.subject_candidate_key is not None
                                else None
                            ),
                            evidence_proposals=evidence_proposals,
                        )
                    )
                except (DomainError, ValueError, TypeError):
                    reviewed = False
                if not reviewed:
                    findings.append(
                        VerificationFinding(
                            "FACT_REVIEW_GROUNDING_INVALID",
                            proposal.candidate_key,
                            "reviewed semantic fact is not bound to valid proposal and review calls",
                        )
                    )
                    continue
            elif not directly_contained:
                findings.append(
                    VerificationFinding(
                        "FACT_OUTSIDE_EVIDENCE",
                        proposal.candidate_key,
                        "direct fact value is not contained in its exact evidence",
                    )
                )
                continue
            identity = digest_of(
                {
                    "schema_version": self._schema.version,
                    "subject_entity_id": subject.value,
                    "predicate": proposal.predicate,
                    "object_value": proposal.object_value,
                    "context_digest": proposal.context.digest.value,
                    "evidence_references": tuple(
                        item.value for item in evidence_refs
                    ),
                    "reviewed_grounding_digest": (
                        proposal.reviewed_grounding.digest.value
                        if proposal.reviewed_grounding is not None
                        else None
                    ),
                }
            )
            fact_id = _stable("knowledge_fact", identity)
            core = {
                "fact_id": fact_id.value,
                "schema_version": self._schema.version,
                "subject_entity_id": subject.value,
                "predicate": proposal.predicate,
                "object_value": proposal.object_value,
                "context": proposal.context,
                "evidence_references": tuple(item.value for item in evidence_refs),
                "reviewed_grounding_digest": (
                    proposal.reviewed_grounding.digest.value
                    if proposal.reviewed_grounding is not None
                    else None
                ),
            }
            facts.append(
                KnowledgeFact(
                    fact_id=fact_id,
                    schema_version=self._schema.version,
                    subject_entity_id=subject,
                    predicate=proposal.predicate,
                    object_value=proposal.object_value,
                    context=proposal.context,
                    evidence_references=evidence_refs,
                    reviewed_grounding=proposal.reviewed_grounding,
                    digest=digest_of(core),
                )
            )

        inferences: list[KnowledgeInference] = []
        for proposal in bundle.inferences:
            if proposal.inference_type not in self._schema.allowed_inference_types:
                findings.append(
                    VerificationFinding("INFERENCE_TYPE_INVALID", proposal.candidate_key, "inference type is not in schema")
                )
                continue
            # Premises must already be formal in the exact base snapshot; newly
            # admitted candidates cannot bootstrap their own inference authority.
            missing_premises = expected_snapshot_id is None or any(
                not self._repository.member_exists(expected_snapshot_id, premise)
                for premise in proposal.premise_references
            )
            if not proposal.premise_references or missing_premises:
                findings.append(
                    VerificationFinding(
                        "INFERENCE_PREMISE_NOT_FORMAL",
                        proposal.candidate_key,
                        "every inference premise must be published in the base snapshot",
                    )
                )
                continue
            if (
                len(proposal.reviewed_need_ids)
                != len(set(proposal.reviewed_need_ids))
                or any(
                    not isinstance(item, str)
                    or not item
                    or item != item.strip()
                    for item in proposal.reviewed_need_ids
                )
            ):
                findings.append(
                    VerificationFinding(
                        "INFERENCE_NEED_LINK_INVALID",
                        proposal.candidate_key,
                        "reviewed inference Need IDs must be unique non-empty values",
                    )
                )
                continue
            identity = digest_of(
                {
                    "schema_version": self._schema.version,
                    "inference_type": proposal.inference_type,
                    "proposition": proposal.proposition,
                    "premises": tuple(item.value for item in proposal.premise_references),
                    "rule_ref": proposal.rule_ref,
                    "context_digest": proposal.context.digest.value,
                    "reviewed_need_ids": proposal.reviewed_need_ids,
                }
            )
            inference_id = _stable("knowledge_inference", identity)
            core = {
                "inference_id": inference_id.value,
                "schema_version": self._schema.version,
                "inference_type": proposal.inference_type,
                "proposition": _text(proposal.proposition, "inference proposition"),
                "premises": tuple(item.value for item in proposal.premise_references),
                "rule_ref": _text(proposal.rule_ref, "inference rule"),
                "context": proposal.context,
                "reviewed_need_ids": proposal.reviewed_need_ids,
            }
            inferences.append(
                KnowledgeInference(
                    inference_id=inference_id,
                    schema_version=self._schema.version,
                    inference_type=proposal.inference_type,
                    proposition=proposal.proposition,
                    premise_references=proposal.premise_references,
                    rule_ref=proposal.rule_ref,
                    context=proposal.context,
                    reviewed_need_ids=proposal.reviewed_need_ids,
                    digest=digest_of(core),
                )
            )
        return (
            tuple(findings),
            ValidatedKnowledgeBatch(
                evidence=tuple(evidence_by_key.values()),
                entities=tuple(entities),
                facts=tuple(facts),
                inferences=tuple(inferences),
            ),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _resolve_evidence(
    keys: tuple[str, ...], values: Mapping[str, EvidenceSnapshot]
) -> tuple[tuple[StableId, ...], bool]:
    resolved = tuple(values[key].evidence_id for key in keys if key in values)
    return resolved, len(resolved) != len(keys)


def _bundle_digest(
    scope_id: StableId,
    expected_snapshot_id: StableId | None,
    bundle: KnowledgeCandidateBundle,
) -> Digest:
    return digest_of(
        {
            "command": "AdmitAndPublishKnowledge@1",
            "scope_id": scope_id.value,
            "expected_snapshot_id": expected_snapshot_id.value if expected_snapshot_id else None,
            "schema_version": bundle.schema_version,
            "evidence": tuple(
                {
                    "key": item.evidence_key,
                    "artifact_id": item.artifact.artifact_id.value,
                    "artifact_digest": item.artifact.content_digest.value,
                    "range": (item.byte_start, item.byte_end),
                    "locator": item.locator,
                }
                for item in bundle.evidence
            ),
            "entities": bundle.entities,
            "facts": bundle.facts,
            "inferences": bundle.inferences,
        }
    )


def _stable(kind: str, digest: Digest) -> StableId:
    return StableId(f"{kind}_{digest.value[-32:]}")


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
