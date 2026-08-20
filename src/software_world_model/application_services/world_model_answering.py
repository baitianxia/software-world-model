"""Bundle-only WORLD_MODEL answering and response authority.

This module deliberately has no Source, Evidence-observation, knowledge database,
Model Gateway, or network port.  It turns an already verified Structure read
bundle into an immutable query/answer authority chain.  Strategies may propose
requirements, plans, drafts, and reviews; the application revalidates and seals
every proposal before it can influence a later stage.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from threading import RLock
from typing import Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    EntityType,
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    RelationPredicate,
)

from .structure_view import (
    EntityResolutionStatus,
    NeighborhoodDirection,
    StructureEntityArgument,
    StructureViewArgumentOrigin,
    StructureViewCompleteness,
    StructureViewOperation,
    StructureViewResult,
    StructureViewService,
)
from .bounded_world_model_investigation import (
    BoundedInvestigationTrace,
    InvestigationEntityRef,
    InvestigationOperation,
    InvestigationTerminalStatus,
    validate_bounded_investigation_trace,
)


WORLD_MODEL_MODE = "WORLD_MODEL"
OFFLINE_STRATEGY_MODE = "DETERMINISTIC_OFFLINE"
QUALIFIED_MODEL_STRATEGY_MODE = "QUALIFIED_MODEL_EVALUATION"
EVALUATION_ONLY_SINK = "EVALUATION_ONLY"

_MAX_REQUIREMENT_NEEDS = 64
_MAX_JOINT_CONSTRAINTS = 64
_MAX_QUERY_SELECTORS = 64
_MAX_QUERY_STEPS = 128
_MAX_ANSWER_CLAIMS = 128
_MAX_QUESTION_CHARS = 32_768
_MAX_CLAIM_TEXT_CHARS = 65_536
_MAX_ANSWER_BODY_CHARS = 1_048_576
_MAX_ENTITY_CANDIDATES = 100
_MAX_PATH_DEPTH = 64
_MAX_PATHS = 1_000
_MAX_PATH_EXPANSIONS = 100_000
_MAX_TOTAL_ENTITY_CANDIDATES = 1_000
_MAX_TOTAL_PATHS = 2_000
_MAX_TOTAL_PATH_EXPANSIONS = 200_000
_MAX_PROVIDER_CALLS = 5
_LEGACY_FIXED_SEMANTICS_STRATEGY_REF = (
    "model-snapshot-first-world-model-answer@1.2.2"
)
_BOUNDED_SEMANTICS_STRATEGY_REF = (
    "model-snapshot-first-world-model-answer@1.5.9"
)


class OfflineStage(str, Enum):
    REQUIREMENT_PLANNING = "REQUIREMENT_PLANNING"
    REQUIREMENT_FIDELITY_REVIEW = "REQUIREMENT_FIDELITY_REVIEW"
    QUERY_PLANNING = "QUERY_PLANNING"
    ANSWER_DRAFTING = "ANSWER_DRAFTING"
    ANSWER_REVIEW = "ANSWER_REVIEW"


class EntitySelectorOrigin(str, Enum):
    MENTION = "MENTION"
    IMPLEMENTATION_FEATURES = "IMPLEMENTATION_FEATURES"
    SEALED_INVESTIGATION_RESULT = "SEALED_INVESTIGATION_RESULT"
    CALLER_EXACT_REF = "CALLER_EXACT_REF"


class QueryStepState(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"


class WorldModelNeedOutcome(str, Enum):
    SATISFIED = "SATISFIED"
    SATISFIED_SUPPORTED_NEGATIVE = "SATISFIED_SUPPORTED_NEGATIVE"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    LIMITATION = "LIMITATION"


class WorldModelJointConstraintKind(str, Enum):
    ALL_NEEDS = "ALL_NEEDS"
    ORDERED_READ_SET = "ORDERED_READ_SET"


class WorldModelClaimKind(str, Enum):
    QUERY_RESULT = "QUERY_RESULT"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    APPLICATION_LIMITATION = "APPLICATION_LIMITATION"


class WorldModelGapReason(str, Enum):
    UNSUPPORTED_STRUCTURE_SEMANTICS = "UNSUPPORTED_STRUCTURE_SEMANTICS"
    KNOWLEDGE_NOT_MODELED = "KNOWLEDGE_NOT_MODELED"
    CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE = (
        "CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE"
    )


class WorldModelReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    UNKNOWN = "UNKNOWN"


class WorldModelReviewDimension(str, Enum):
    REQUIREMENT_FIDELITY = "REQUIREMENT_FIDELITY"
    QUERY_COMPLETENESS = "QUERY_COMPLETENESS"
    RESULT_GROUNDING = "RESULT_GROUNDING"
    COMPARISON_DIRECTION = "COMPARISON_DIRECTION"
    RESPONSE_LANGUAGE = "RESPONSE_LANGUAGE"
    RELEVANCE_READABILITY = "RELEVANCE_READABILITY"


_REQUIRED_REVIEW_DIMENSIONS = tuple(WorldModelReviewDimension)


class WorldModelDeliveryState(str, Enum):
    PREPARED = "PREPARED"
    SENDING = "SENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class WorldModelReadAuthority:
    scope_id: StableId
    session_id: StableId
    session_digest: Digest
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    snapshot_ids: tuple[StableId, ...]
    snapshot_bundle_digests: tuple[Digest, ...]
    source_revisions: tuple[str, ...]
    profile_refs: tuple[str, ...]
    digest: Digest

    @classmethod
    def from_view(cls, view: StructureViewService) -> "WorldModelReadAuthority":
        session = view.read_session
        source_revisions: list[str] = []
        for binding in session.snapshots:
            revisions = {
                coverage.source_revision for coverage in binding.coverages
            }
            if len(revisions) != 1:
                raise _invalid(
                    "WORLD_MODEL_SNAPSHOT_REVISION_AMBIGUOUS",
                    "every Snapshot in a world-model Read Set must bind one exact source revision",
                )
            source_revisions.append(next(iter(revisions)))
        profile_refs = tuple(
            sorted(
                {
                    coverage.profile_ref
                    for binding in session.snapshots
                    for coverage in binding.coverages
                }
            )
        )
        core = {
            "scope_id": session.scope_id.value,
            "session_id": session.session_id.value,
            "session_digest": session.digest.value,
            "read_set_digest": session.read_set_digest.value,
            "ordered_bundle_digest": view.ordered_bundle_digest.value,
            "snapshot_ids": tuple(item.value for item in view.snapshot_ids),
            "snapshot_bundle_digests": tuple(
                item.value for item in view.snapshot_bundle_digests
            ),
            "source_revisions": tuple(source_revisions),
            "profile_refs": profile_refs,
        }
        value = cls(
            scope_id=session.scope_id,
            session_id=session.session_id,
            session_digest=session.digest,
            read_set_digest=session.read_set_digest,
            ordered_bundle_digest=view.ordered_bundle_digest,
            snapshot_ids=view.snapshot_ids,
            snapshot_bundle_digests=view.snapshot_bundle_digests,
            source_revisions=tuple(source_revisions),
            profile_refs=profile_refs,
            digest=digest_of(["WORLD_MODEL_READ_AUTHORITY@1", core]),
        )
        value.require_valid()
        return value

    def canonical_value(self) -> dict[str, object]:
        return {
            "scope_id": self.scope_id.value,
            "session_id": self.session_id.value,
            "session_digest": self.session_digest.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "snapshot_ids": tuple(item.value for item in self.snapshot_ids),
            "snapshot_bundle_digests": tuple(
                item.value for item in self.snapshot_bundle_digests
            ),
            "source_revisions": self.source_revisions,
            "profile_refs": self.profile_refs,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        if self.session_id.kind != "structure_read_session":
            raise _invalid(
                "WORLD_MODEL_READ_SESSION_INVALID",
                "world-model read authority requires a Structure read Session",
            )
        if (
            not self.snapshot_ids
            or len(self.snapshot_ids) != len(self.snapshot_bundle_digests)
            or len(self.snapshot_ids) != len(self.source_revisions)
            or len(set(self.snapshot_ids)) != len(self.snapshot_ids)
        ):
            raise _invalid(
                "WORLD_MODEL_READ_SET_INVALID",
                "world-model read authority has an invalid ordered Snapshot set",
            )
        if tuple(sorted(set(self.profile_refs))) != self.profile_refs:
            raise _invalid(
                "WORLD_MODEL_PROFILE_SET_INVALID",
                "world-model Profile refs are not canonical",
            )
        core = {
            key: value
            for key, value in self.canonical_value().items()
            if key != "digest"
        }
        if self.digest != digest_of(["WORLD_MODEL_READ_AUTHORITY@1", core]):
            raise _invalid(
                "WORLD_MODEL_READ_AUTHORITY_DIGEST_MISMATCH",
                "world-model read authority is not canonical",
            )


@dataclass(frozen=True, slots=True)
class WorldModelResourceLimits:
    max_needs: int = _MAX_REQUIREMENT_NEEDS
    max_joint_constraints: int = _MAX_JOINT_CONSTRAINTS
    max_query_selectors: int = _MAX_QUERY_SELECTORS
    max_query_steps: int = _MAX_QUERY_STEPS
    max_answer_claims: int = _MAX_ANSWER_CLAIMS
    max_question_chars: int = _MAX_QUESTION_CHARS
    max_claim_text_chars: int = _MAX_CLAIM_TEXT_CHARS
    max_answer_body_chars: int = _MAX_ANSWER_BODY_CHARS
    max_entity_candidates: int = _MAX_ENTITY_CANDIDATES
    max_path_depth: int = _MAX_PATH_DEPTH
    max_paths: int = _MAX_PATHS
    max_path_expansions: int = _MAX_PATH_EXPANSIONS
    max_total_entity_candidates: int = _MAX_TOTAL_ENTITY_CANDIDATES
    max_total_paths: int = _MAX_TOTAL_PATHS
    max_total_path_expansions: int = _MAX_TOTAL_PATH_EXPANSIONS

    def canonical_value(self) -> dict[str, int]:
        return {
            "max_needs": self.max_needs,
            "max_joint_constraints": self.max_joint_constraints,
            "max_query_selectors": self.max_query_selectors,
            "max_query_steps": self.max_query_steps,
            "max_answer_claims": self.max_answer_claims,
            "max_question_chars": self.max_question_chars,
            "max_claim_text_chars": self.max_claim_text_chars,
            "max_answer_body_chars": self.max_answer_body_chars,
            "max_entity_candidates": self.max_entity_candidates,
            "max_path_depth": self.max_path_depth,
            "max_paths": self.max_paths,
            "max_path_expansions": self.max_path_expansions,
            "max_total_entity_candidates": self.max_total_entity_candidates,
            "max_total_paths": self.max_total_paths,
            "max_total_path_expansions": self.max_total_path_expansions,
        }

    def require_valid(self) -> None:
        maxima = {
            "max_needs": _MAX_REQUIREMENT_NEEDS,
            "max_joint_constraints": _MAX_JOINT_CONSTRAINTS,
            "max_query_selectors": _MAX_QUERY_SELECTORS,
            "max_query_steps": _MAX_QUERY_STEPS,
            "max_answer_claims": _MAX_ANSWER_CLAIMS,
            "max_question_chars": _MAX_QUESTION_CHARS,
            "max_claim_text_chars": _MAX_CLAIM_TEXT_CHARS,
            "max_answer_body_chars": _MAX_ANSWER_BODY_CHARS,
            "max_entity_candidates": _MAX_ENTITY_CANDIDATES,
            "max_path_depth": _MAX_PATH_DEPTH,
            "max_paths": _MAX_PATHS,
            "max_path_expansions": _MAX_PATH_EXPANSIONS,
            "max_total_entity_candidates": _MAX_TOTAL_ENTITY_CANDIDATES,
            "max_total_paths": _MAX_TOTAL_PATHS,
            "max_total_path_expansions": _MAX_TOTAL_PATH_EXPANSIONS,
        }
        if any(
            type(getattr(self, name)) is not int
            or getattr(self, name) != maximum
            for name, maximum in maxima.items()
        ):
            raise _invalid(
                "WORLD_MODEL_RESOURCE_LIMIT_INVALID",
                "G3a world-model resource limits must equal the fixed offline caps",
            )

    @property
    def digest(self) -> Digest:
        self.require_valid()
        return digest_of(["WORLD_MODEL_RESOURCE_LIMITS@1", self.canonical_value()])


@dataclass(frozen=True, slots=True)
class WorldModelExplicitEntityRef:
    snapshot_id: StableId
    entity_root_id: StableId
    entity_state_id: StableId
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: StableId,
        entity_root_id: StableId,
        entity_state_id: StableId,
    ) -> "WorldModelExplicitEntityRef":
        core = {
            "snapshot_id": snapshot_id.value,
            "entity_root_id": entity_root_id.value,
            "entity_state_id": entity_state_id.value,
        }
        return cls(
            snapshot_id=snapshot_id,
            entity_root_id=entity_root_id,
            entity_state_id=entity_state_id,
            digest=digest_of(["WORLD_MODEL_EXPLICIT_ENTITY_REF@1", core]),
        )

    def canonical_value(self) -> dict[str, str]:
        return {
            "snapshot_id": self.snapshot_id.value,
            "entity_root_id": self.entity_root_id.value,
            "entity_state_id": self.entity_state_id.value,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        expected = WorldModelExplicitEntityRef.create(
            snapshot_id=self.snapshot_id,
            entity_root_id=self.entity_root_id,
            entity_state_id=self.entity_state_id,
        )
        if self != expected:
            raise _invalid(
                "WORLD_MODEL_EXPLICIT_ENTITY_REF_INVALID",
                "caller exact Entity ref is not canonical",
            )


@dataclass(frozen=True, slots=True)
class WorldModelQuestion:
    question_id: StableId
    revision: int
    request_ref: str
    mode: str
    original_question: str
    response_language: str
    classification: str
    permission_digest: Digest
    use_epoch: int
    resource_limits: WorldModelResourceLimits
    read_authority: WorldModelReadAuthority
    explicit_entity_refs: tuple[WorldModelExplicitEntityRef, ...]
    external_dispatch_allowed: bool
    model_route: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        original_question: str,
        response_language: str,
        classification: str,
        permission_digest: Digest,
        view: StructureViewService,
        resource_limits: WorldModelResourceLimits | None = None,
        explicit_entity_refs: Sequence[WorldModelExplicitEntityRef] = (),
        model_route: str | None = None,
    ) -> "WorldModelQuestion":
        read_authority = WorldModelReadAuthority.from_view(view)
        limits = resource_limits or WorldModelResourceLimits()
        limits.require_valid()
        refs = tuple(explicit_entity_refs)
        if len(refs) > limits.max_query_selectors:
            raise _invalid(
                "WORLD_MODEL_EXPLICIT_ENTITY_REF_LIMIT",
                "caller exact Entity refs exceed the fixed Question limit",
            )
        if len(
            {
                (item.snapshot_id, item.entity_root_id, item.entity_state_id)
                for item in refs
            }
        ) != len(refs):
            raise _invalid(
                "WORLD_MODEL_EXPLICIT_ENTITY_REF_DUPLICATE",
                "caller exact Entity refs must be unique",
            )
        for item in refs:
            expected = WorldModelExplicitEntityRef.create(
                snapshot_id=item.snapshot_id,
                entity_root_id=item.entity_root_id,
                entity_state_id=item.entity_state_id,
            )
            if item != expected or item.snapshot_id not in read_authority.snapshot_ids:
                raise _invalid(
                    "WORLD_MODEL_EXPLICIT_ENTITY_REF_INVALID",
                    "caller exact Entity ref is not canonical or outside the Read Set",
                )
        if model_route is not None:
            _text(model_route, "model route")
        external_dispatch_allowed = model_route is not None
        core = {
            "revision": 1,
            "request_ref": _text(request_ref, "request ref"),
            "mode": WORLD_MODEL_MODE,
            "original_question": _text(original_question, "original question"),
            "response_language": _text(response_language, "response language"),
            "classification": _text(classification, "classification"),
            "permission_digest": permission_digest.value,
            "use_epoch": 1,
            "resource_limits": limits.canonical_value(),
            "resource_limits_digest": limits.digest.value,
            "read_authority": read_authority.canonical_value(),
            "explicit_entity_refs": tuple(item.canonical_value() for item in refs),
            "external_dispatch_allowed": external_dispatch_allowed,
            "model_route": model_route,
        }
        if len(core["original_question"]) > limits.max_question_chars:
            raise _invalid(
                "WORLD_MODEL_QUESTION_SIZE_LIMIT",
                "original Question exceeds the fixed G3a text limit",
            )
        identity = digest_of(["WORLD_MODEL_QUESTION_ID@1", core])
        question_id = _stable("world_model_question", identity)
        value = cls(
            question_id=question_id,
            revision=1,
            request_ref=core["request_ref"],
            mode=WORLD_MODEL_MODE,
            original_question=core["original_question"],
            response_language=core["response_language"],
            classification=core["classification"],
            permission_digest=permission_digest,
            use_epoch=1,
            resource_limits=limits,
            read_authority=read_authority,
            explicit_entity_refs=refs,
            external_dispatch_allowed=external_dispatch_allowed,
            model_route=model_route,
            digest=digest_of(
                ["WORLD_MODEL_QUESTION@1", {"question_id": question_id.value, **core}]
            ),
        )
        value.require_valid()
        return value

    def canonical_value(self) -> dict[str, object]:
        return {
            "question_id": self.question_id.value,
            "revision": self.revision,
            "request_ref": self.request_ref,
            "mode": self.mode,
            "original_question": self.original_question,
            "response_language": self.response_language,
            "classification": self.classification,
            "permission_digest": self.permission_digest.value,
            "use_epoch": self.use_epoch,
            "resource_limits": self.resource_limits.canonical_value(),
            "resource_limits_digest": self.resource_limits.digest.value,
            "read_authority": self.read_authority.canonical_value(),
            "explicit_entity_refs": tuple(
                item.canonical_value() for item in self.explicit_entity_refs
            ),
            "external_dispatch_allowed": self.external_dispatch_allowed,
            "model_route": self.model_route,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        self.read_authority.require_valid()
        self.resource_limits.require_valid()
        refs = self.explicit_entity_refs
        if (
            not isinstance(refs, tuple)
            or len(refs) > self.resource_limits.max_query_selectors
            or any(
                not isinstance(item, WorldModelExplicitEntityRef)
                for item in refs
            )
            or len(
                {
                    (item.snapshot_id, item.entity_root_id, item.entity_state_id)
                    for item in refs
                }
            )
            != len(refs)
        ):
            raise _invalid(
                "WORLD_MODEL_EXPLICIT_ENTITY_REF_INVALID",
                "caller exact Entity refs are not a closed unique tuple",
            )
        for item in refs:
            item.require_valid()
            if item.snapshot_id not in self.read_authority.snapshot_ids:
                raise _invalid(
                    "WORLD_MODEL_EXPLICIT_ENTITY_REF_INVALID",
                    "caller exact Entity ref is outside the Read Set",
                )
        offline_boundary = (
            self.external_dispatch_allowed is False and self.model_route is None
        )
        qualified_model_boundary = (
            self.external_dispatch_allowed is True
            and isinstance(self.model_route, str)
            and bool(self.model_route)
            and self.model_route == self.model_route.strip()
        )
        if (
            self.question_id.kind != "world_model_question"
            or type(self.revision) is not int
            or self.revision != 1
            or type(self.use_epoch) is not int
            or self.use_epoch != 1
            or self.mode != WORLD_MODEL_MODE
            or not (offline_boundary or qualified_model_boundary)
            or len(self.original_question)
            > self.resource_limits.max_question_chars
        ):
            raise _invalid(
                "WORLD_MODEL_QUESTION_BOUNDARY_INVALID",
                "world-model Question has an invalid execution boundary",
            )
        for value, label in (
            (self.request_ref, "request ref"),
            (self.original_question, "original question"),
            (self.response_language, "response language"),
            (self.classification, "classification"),
        ):
            _text(value, label)
        core = {
            key: value
            for key, value in self.canonical_value().items()
            if key not in {"question_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_QUESTION_ID@1", core])
        expected_id = _stable("world_model_question", identity)
        expected_digest = digest_of(
            ["WORLD_MODEL_QUESTION@1", {"question_id": expected_id.value, **core}]
        )
        if self.question_id != expected_id or self.digest != expected_digest:
            raise _invalid(
                "WORLD_MODEL_QUESTION_DIGEST_MISMATCH",
                "world-model Question is not canonical",
            )


@dataclass(frozen=True, slots=True)
class OfflineStrategyInvocation:
    invocation_id: StableId
    stage: OfflineStage
    question_id: StableId
    question_digest: Digest
    input_digest: Digest
    strategy_ref: str
    execution_mode: str
    provider_route: None
    external_dispatch_allowed: bool
    digest: Digest

    @classmethod
    def issue(
        cls,
        *,
        stage: OfflineStage,
        question: WorldModelQuestion,
        input_digest: Digest,
        strategy_ref: str,
    ) -> "OfflineStrategyInvocation":
        core = {
            "stage": stage.value,
            "question_id": question.question_id.value,
            "question_digest": question.digest.value,
            "input_digest": input_digest.value,
            "strategy_ref": _text(strategy_ref, "strategy ref"),
            "execution_mode": OFFLINE_STRATEGY_MODE,
            "provider_route": None,
            "external_dispatch_allowed": False,
        }
        identity = digest_of(["OFFLINE_STRATEGY_INVOCATION_ID@1", core])
        invocation_id = _stable("offline_invocation", identity)
        return cls(
            invocation_id=invocation_id,
            stage=stage,
            question_id=question.question_id,
            question_digest=question.digest,
            input_digest=input_digest,
            strategy_ref=core["strategy_ref"],
            execution_mode=OFFLINE_STRATEGY_MODE,
            provider_route=None,
            external_dispatch_allowed=False,
            digest=digest_of(
                [
                    "OFFLINE_STRATEGY_INVOCATION@1",
                    {"invocation_id": invocation_id.value, **core},
                ]
            ),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "invocation_id": self.invocation_id.value,
            "stage": self.stage.value,
            "question_id": self.question_id.value,
            "question_digest": self.question_digest.value,
            "input_digest": self.input_digest.value,
            "strategy_ref": self.strategy_ref,
            "execution_mode": self.execution_mode,
            "provider_route": self.provider_route,
            "external_dispatch_allowed": self.external_dispatch_allowed,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        if (
            self.invocation_id.kind != "offline_invocation"
            or self.execution_mode != OFFLINE_STRATEGY_MODE
            or self.provider_route is not None
            or self.external_dispatch_allowed is not False
        ):
            raise _invalid(
                "OFFLINE_INVOCATION_BOUNDARY_INVALID",
                "G3a strategy invocation must deny Provider dispatch",
            )
        core = {
            key: value
            for key, value in self.canonical_value().items()
            if key not in {"invocation_id", "digest"}
        }
        identity = digest_of(["OFFLINE_STRATEGY_INVOCATION_ID@1", core])
        expected_id = _stable("offline_invocation", identity)
        expected_digest = digest_of(
            [
                "OFFLINE_STRATEGY_INVOCATION@1",
                {"invocation_id": expected_id.value, **core},
            ]
        )
        if self.invocation_id != expected_id or self.digest != expected_digest:
            raise _invalid(
                "OFFLINE_INVOCATION_DIGEST_MISMATCH",
                "offline strategy invocation is not canonical",
            )


@dataclass(frozen=True, slots=True)
class QualifiedModelStrategyInvocation:
    """Authority-issued invocation that permits only the exact model route.

    The invocation is issued before a model-backed proposal role runs.  It
    authorizes no Source, Evidence, repository, browser, or arbitrary network
    access; the concrete route is an evaluator-owned AF_UNIX gateway binding.
    """

    invocation_id: StableId
    stage: OfflineStage
    question_id: StableId
    question_digest: Digest
    input_digest: Digest
    strategy_ref: str
    execution_mode: str
    provider_route: str
    external_dispatch_allowed: bool
    digest: Digest

    @classmethod
    def issue(
        cls,
        *,
        stage: OfflineStage,
        question: WorldModelQuestion,
        input_digest: Digest,
        strategy_ref: str,
        provider_route: str,
    ) -> "QualifiedModelStrategyInvocation":
        question.require_valid()
        route = _text(provider_route, "provider route")
        if (
            question.external_dispatch_allowed is not True
            or question.model_route != route
        ):
            raise _invalid(
                "MODEL_INVOCATION_ROUTE_DENIED",
                "qualified model invocation is outside the Question route",
            )
        core = {
            "stage": stage.value,
            "question_id": question.question_id.value,
            "question_digest": question.digest.value,
            "input_digest": input_digest.value,
            "strategy_ref": _text(strategy_ref, "strategy ref"),
            "execution_mode": QUALIFIED_MODEL_STRATEGY_MODE,
            "provider_route": route,
            "external_dispatch_allowed": True,
        }
        identity = digest_of(["QUALIFIED_MODEL_STRATEGY_INVOCATION_ID@1", core])
        invocation_id = _stable("model_invocation", identity)
        return cls(
            invocation_id=invocation_id,
            stage=stage,
            question_id=question.question_id,
            question_digest=question.digest,
            input_digest=input_digest,
            strategy_ref=core["strategy_ref"],
            execution_mode=QUALIFIED_MODEL_STRATEGY_MODE,
            provider_route=route,
            external_dispatch_allowed=True,
            digest=digest_of(
                [
                    "QUALIFIED_MODEL_STRATEGY_INVOCATION@1",
                    {"invocation_id": invocation_id.value, **core},
                ]
            ),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "invocation_id": self.invocation_id.value,
            "stage": self.stage.value,
            "question_id": self.question_id.value,
            "question_digest": self.question_digest.value,
            "input_digest": self.input_digest.value,
            "strategy_ref": self.strategy_ref,
            "execution_mode": self.execution_mode,
            "provider_route": self.provider_route,
            "external_dispatch_allowed": self.external_dispatch_allowed,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        if (
            self.invocation_id.kind != "model_invocation"
            or self.execution_mode != QUALIFIED_MODEL_STRATEGY_MODE
            or not isinstance(self.provider_route, str)
            or not self.provider_route
            or self.provider_route != self.provider_route.strip()
            or self.external_dispatch_allowed is not True
        ):
            raise _invalid(
                "MODEL_INVOCATION_BOUNDARY_INVALID",
                "qualified model invocation has an invalid exact route",
            )
        core = {
            key: value
            for key, value in self.canonical_value().items()
            if key not in {"invocation_id", "digest"}
        }
        identity = digest_of(["QUALIFIED_MODEL_STRATEGY_INVOCATION_ID@1", core])
        expected_id = _stable("model_invocation", identity)
        expected_digest = digest_of(
            [
                "QUALIFIED_MODEL_STRATEGY_INVOCATION@1",
                {"invocation_id": expected_id.value, **core},
            ]
        )
        if self.invocation_id != expected_id or self.digest != expected_digest:
            raise _invalid(
                "MODEL_INVOCATION_DIGEST_MISMATCH",
                "qualified model invocation is not canonical",
            )


WorldModelStrategyInvocation = (
    OfflineStrategyInvocation | QualifiedModelStrategyInvocation
)


@dataclass(frozen=True, slots=True)
class WorldModelNeed:
    need_id: str
    question: str

    def __post_init__(self) -> None:
        _text(self.need_id, "Need ID")
        _text(self.question, "Need question")

    def canonical_value(self) -> dict[str, str]:
        return {"need_id": self.need_id, "question": self.question}


@dataclass(frozen=True, slots=True)
class WorldModelJointConstraint:
    constraint_id: str
    need_ids: tuple[str, ...]
    kind: WorldModelJointConstraintKind
    description: str
    base_snapshot_id: StableId | None = None
    target_snapshot_id: StableId | None = None

    def canonical_value(self) -> dict[str, object]:
        return {
            "constraint_id": self.constraint_id,
            "need_ids": self.need_ids,
            "kind": self.kind.value,
            "description": self.description,
            "base_snapshot_id": (
                self.base_snapshot_id.value if self.base_snapshot_id else None
            ),
            "target_snapshot_id": (
                self.target_snapshot_id.value if self.target_snapshot_id else None
            ),
        }


@dataclass(frozen=True, slots=True)
class WorldModelRequirementProposal:
    original_question: str
    response_language: str
    needs: tuple[WorldModelNeed, ...]
    joint_constraints: tuple[WorldModelJointConstraint, ...]
    invocation_id: StableId
    invocation_digest: Digest


@dataclass(frozen=True, slots=True)
class WorldModelRequirementFidelityProposal:
    decision: WorldModelReviewDecision
    accepted_need_ids: tuple[str, ...]
    accepted_constraint_ids: tuple[str, ...]
    original_question_preserved: bool
    all_material_questions_covered: bool
    findings: tuple[str, ...]
    invocation_id: StableId
    invocation_digest: Digest


class WorldModelRequirementPlanner(Protocol):
    strategy_ref: str

    def plan(
        self,
        *,
        question: WorldModelQuestion,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementProposal: ...


class WorldModelRequirementFidelityReviewer(Protocol):
    strategy_ref: str

    def review(
        self,
        *,
        question: WorldModelQuestion,
        proposal: WorldModelRequirementProposal,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelRequirementFidelityProposal: ...


@dataclass(frozen=True, slots=True)
class WorldModelRequirementRevision:
    requirement_id: StableId
    revision: int
    question_id: StableId
    question_digest: Digest
    original_question: str
    response_language: str
    needs: tuple[WorldModelNeed, ...]
    joint_constraints: tuple[WorldModelJointConstraint, ...]
    planning_invocation: WorldModelStrategyInvocation
    fidelity_review_invocation: WorldModelStrategyInvocation
    fidelity_decision: WorldModelReviewDecision
    fidelity_accepted_need_ids: tuple[str, ...]
    fidelity_accepted_constraint_ids: tuple[str, ...]
    fidelity_original_question_preserved: bool
    fidelity_all_material_questions_covered: bool
    fidelity_findings: tuple[str, ...]
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "requirement_id": self.requirement_id.value,
            "revision": self.revision,
            "question_id": self.question_id.value,
            "question_digest": self.question_digest.value,
            "original_question": self.original_question,
            "response_language": self.response_language,
            "needs": tuple(item.canonical_value() for item in self.needs),
            "joint_constraints": tuple(
                item.canonical_value() for item in self.joint_constraints
            ),
            "planning_invocation": self.planning_invocation.canonical_value(),
            "fidelity_review_invocation": (
                self.fidelity_review_invocation.canonical_value()
            ),
            "fidelity_decision": self.fidelity_decision.value,
            "fidelity_accepted_need_ids": self.fidelity_accepted_need_ids,
            "fidelity_accepted_constraint_ids": (
                self.fidelity_accepted_constraint_ids
            ),
            "fidelity_original_question_preserved": (
                self.fidelity_original_question_preserved
            ),
            "fidelity_all_material_questions_covered": (
                self.fidelity_all_material_questions_covered
            ),
            "fidelity_findings": self.fidelity_findings,
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelEntitySelectorProposal:
    selector_id: str
    need_ids: tuple[str, ...]
    snapshot_id: StableId
    origin: EntitySelectorOrigin
    mention: str | None = None
    entity_type: EntityType | None = None
    canonical_ga: str | None = None
    canonical_gav: str | None = None
    max_candidates: int = 100
    entity_root_id: StableId | None = None
    entity_state_id: StableId | None = None
    search_terms: tuple[str, ...] = ()
    source_result_id: StableId | None = None
    source_result_digest: Digest | None = None

    def canonical_value(self) -> dict[str, object]:
        value: dict[str, object] = {
            "selector_id": self.selector_id,
            "need_ids": self.need_ids,
            "snapshot_id": self.snapshot_id.value,
            "origin": self.origin.value,
            "mention": self.mention,
            "entity_type": self.entity_type.value if self.entity_type else None,
            "canonical_ga": self.canonical_ga,
            "canonical_gav": self.canonical_gav,
            "max_candidates": self.max_candidates,
            "entity_root_id": (
                self.entity_root_id.value if self.entity_root_id else None
            ),
            "entity_state_id": (
                self.entity_state_id.value if self.entity_state_id else None
            ),
            "search_terms": self.search_terms,
        }
        if (
            self.source_result_id is not None
            or self.source_result_digest is not None
        ):
            value["source_result_id"] = (
                self.source_result_id.value
                if self.source_result_id is not None
                else None
            )
            value["source_result_digest"] = (
                self.source_result_digest.value
                if self.source_result_digest is not None
                else None
            )
        return value


@dataclass(frozen=True, slots=True)
class WorldModelQueryStepProposal:
    step_id: str
    need_ids: tuple[str, ...]
    operation: StructureViewOperation
    arguments: CanonicalFields
    parameters: CanonicalFields
    constraint_ids: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        step_id: str,
        need_ids: Sequence[str],
        operation: StructureViewOperation,
        arguments: Mapping[str, object] | None = None,
        parameters: Mapping[str, object] | None = None,
        constraint_ids: Sequence[str] = (),
    ) -> "WorldModelQueryStepProposal":
        return cls(
            step_id=_text(step_id, "query step ID"),
            need_ids=tuple(need_ids),
            operation=operation,
            arguments=CanonicalFields(arguments or {}),
            parameters=CanonicalFields(parameters or {}),
            constraint_ids=tuple(constraint_ids),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "need_ids": self.need_ids,
            "operation": self.operation.value,
            "arguments": self.arguments,
            "parameters": self.parameters,
            "constraint_ids": self.constraint_ids,
        }


@dataclass(frozen=True, slots=True)
class WorldModelGapProposal:
    need_id: str
    reason_code: WorldModelGapReason
    detail: str

    def canonical_value(self) -> dict[str, str]:
        return {
            "need_id": self.need_id,
            "reason_code": self.reason_code.value,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class WorldModelQueryPlanProposal:
    requirement_id: StableId
    requirement_digest: Digest
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    selectors: tuple[WorldModelEntitySelectorProposal, ...]
    steps: tuple[WorldModelQueryStepProposal, ...]
    explicit_gaps: tuple[WorldModelGapProposal, ...]
    invocation_id: StableId
    invocation_digest: Digest
    investigation_trace: BoundedInvestigationTrace | None = None


class WorldModelQueryPlanner(Protocol):
    strategy_ref: str

    def plan(
        self,
        *,
        question: WorldModelQuestion,
        requirement: WorldModelRequirementRevision,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelQueryPlanProposal: ...


@dataclass(frozen=True, slots=True)
class WorldModelEntityResolution:
    resolution_id: StableId
    selector: WorldModelEntitySelectorProposal
    status: EntityResolutionStatus
    candidate_result: StructureViewResult | None
    argument: StructureEntityArgument | None
    limitations: tuple[str, ...]
    read_authority_digest: Digest
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "resolution_id": self.resolution_id.value,
            "selector": self.selector.canonical_value(),
            "status": self.status.value,
            "candidate_result": (
                self.candidate_result.canonical_value()
                if self.candidate_result is not None
                else None
            ),
            "argument": _entity_argument_value(self.argument),
            "limitations": self.limitations,
            "read_authority_digest": self.read_authority_digest.value,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelCandidateResolutionSet:
    resolution_set_id: StableId
    question_id: StableId
    requirement_id: StableId
    requirement_digest: Digest
    proposal_digest: Digest
    planning_invocation: WorldModelStrategyInvocation
    resolutions: tuple[WorldModelEntityResolution, ...]
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "resolution_set_id": self.resolution_set_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "requirement_digest": self.requirement_digest.value,
            "proposal_digest": self.proposal_digest.value,
            "planning_invocation": self.planning_invocation.canonical_value(),
            "resolutions": tuple(
                item.canonical_value() for item in self.resolutions
            ),
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelQueryStep:
    step_id: str
    need_ids: tuple[str, ...]
    operation: StructureViewOperation
    arguments: CanonicalFields
    parameters: CanonicalFields
    constraint_ids: tuple[str, ...]
    state: QueryStepState
    limitation_code: str | None
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "need_ids": self.need_ids,
            "operation": self.operation.value,
            "arguments": self.arguments,
            "parameters": self.parameters,
            "constraint_ids": self.constraint_ids,
            "state": self.state.value,
            "limitation_code": self.limitation_code,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelQueryPlan:
    plan_id: StableId
    question_id: StableId
    requirement_id: StableId
    requirement_digest: Digest
    resolution_set_id: StableId
    resolution_set_digest: Digest
    planning_invocation: WorldModelStrategyInvocation
    capability_registry_digest: Digest
    steps: tuple[WorldModelQueryStep, ...]
    explicit_gaps: tuple[WorldModelGapProposal, ...]
    investigation_trace: BoundedInvestigationTrace | None
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        value: dict[str, object] = {
            "plan_id": self.plan_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "requirement_digest": self.requirement_digest.value,
            "resolution_set_id": self.resolution_set_id.value,
            "resolution_set_digest": self.resolution_set_digest.value,
            "planning_invocation": self.planning_invocation.canonical_value(),
            "capability_registry_digest": self.capability_registry_digest.value,
            "steps": tuple(item.canonical_value() for item in self.steps),
            "explicit_gaps": tuple(
                item.canonical_value() for item in self.explicit_gaps
            ),
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }
        if self.investigation_trace is not None:
            value["investigation_trace"] = (
                self.investigation_trace.canonical_value()
            )
        return value


@dataclass(frozen=True, slots=True)
class WorldModelQueryStepResult:
    step_result_id: StableId
    step_id: str
    step_digest: Digest
    view_result: StructureViewResult
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "step_result_id": self.step_result_id.value,
            "step_id": self.step_id,
            "step_digest": self.step_digest.value,
            "view_result": self.view_result.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelQueryResultSet:
    result_set_id: StableId
    question_id: StableId
    requirement_id: StableId
    plan_id: StableId
    plan_digest: Digest
    step_results: tuple[WorldModelQueryStepResult, ...]
    read_authority: WorldModelReadAuthority
    support_map_digest: Digest
    evidence_allowlist_digest: Digest
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "result_set_id": self.result_set_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "plan_id": self.plan_id.value,
            "plan_digest": self.plan_digest.value,
            "step_results": tuple(
                item.canonical_value() for item in self.step_results
            ),
            "read_authority": self.read_authority.canonical_value(),
            "support_map_digest": self.support_map_digest.value,
            "evidence_allowlist_digest": self.evidence_allowlist_digest.value,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelNeedAssessment:
    need_id: str
    outcome: WorldModelNeedOutcome
    step_result_ids: tuple[StableId, ...]
    view_result_ids: tuple[StableId, ...]
    support_digests: tuple[Digest, ...]
    gap_code: str | None
    gap_detail: str | None
    limitations: tuple[str, ...]
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "need_id": self.need_id,
            "outcome": self.outcome.value,
            "step_result_ids": tuple(item.value for item in self.step_result_ids),
            "view_result_ids": tuple(item.value for item in self.view_result_ids),
            "support_digests": tuple(item.value for item in self.support_digests),
            "gap_code": self.gap_code,
            "gap_detail": self.gap_detail,
            "limitations": self.limitations,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelJointAssessment:
    constraint_id: str
    satisfied: bool
    need_ids: tuple[str, ...]
    step_result_ids: tuple[StableId, ...]
    view_result_ids: tuple[StableId, ...]
    support_digests: tuple[Digest, ...]
    finding: str | None
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "constraint_id": self.constraint_id,
            "satisfied": self.satisfied,
            "need_ids": self.need_ids,
            "step_result_ids": tuple(
                item.value for item in self.step_result_ids
            ),
            "view_result_ids": tuple(
                item.value for item in self.view_result_ids
            ),
            "support_digests": tuple(
                item.value for item in self.support_digests
            ),
            "finding": self.finding,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelAssessment:
    assessment_id: StableId
    question_id: StableId
    requirement_id: StableId
    requirement_digest: Digest
    plan_id: StableId
    plan_digest: Digest
    result_set_id: StableId
    result_set_digest: Digest
    needs: tuple[WorldModelNeedAssessment, ...]
    joint_constraints: tuple[WorldModelJointAssessment, ...]
    sufficient: bool
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "assessment_id": self.assessment_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "requirement_digest": self.requirement_digest.value,
            "plan_id": self.plan_id.value,
            "plan_digest": self.plan_digest.value,
            "result_set_id": self.result_set_id.value,
            "result_set_digest": self.result_set_digest.value,
            "needs": tuple(item.canonical_value() for item in self.needs),
            "joint_constraints": tuple(
                item.canonical_value() for item in self.joint_constraints
            ),
            "sufficient": self.sufficient,
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelAnswerClaimProposal:
    claim_id: str
    need_id: str
    kind: WorldModelClaimKind
    text: str
    step_result_ids: tuple[StableId, ...] = ()


@dataclass(frozen=True, slots=True)
class WorldModelDraftProposal:
    assessment_id: StableId
    assessment_digest: Digest
    claims: tuple[WorldModelAnswerClaimProposal, ...]
    invocation_id: StableId
    invocation_digest: Digest


class WorldModelDraftGenerator(Protocol):
    strategy_ref: str

    def draft(
        self,
        *,
        question: WorldModelQuestion,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelDraftProposal: ...


@dataclass(frozen=True, slots=True)
class WorldModelAnswerClaim:
    claim_id: str
    need_id: str
    kind: WorldModelClaimKind
    text: str
    step_result_ids: tuple[StableId, ...]
    view_result_ids: tuple[StableId, ...]
    support_digests: tuple[Digest, ...]
    evidence_references: tuple[StableId, ...]
    gap_code: str | None
    limitation_codes: tuple[str, ...]
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "need_id": self.need_id,
            "kind": self.kind.value,
            "text": self.text,
            "step_result_ids": tuple(item.value for item in self.step_result_ids),
            "view_result_ids": tuple(item.value for item in self.view_result_ids),
            "support_digests": tuple(item.value for item in self.support_digests),
            "evidence_references": tuple(
                item.value for item in self.evidence_references
            ),
            "gap_code": self.gap_code,
            "limitation_codes": self.limitation_codes,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelAnswerDraft:
    draft_id: StableId
    question_id: StableId
    requirement_id: StableId
    plan_id: StableId
    result_set_id: StableId
    assessment_id: StableId
    claims: tuple[WorldModelAnswerClaim, ...]
    body: str
    body_digest: Digest
    generation_invocation: WorldModelStrategyInvocation
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "plan_id": self.plan_id.value,
            "result_set_id": self.result_set_id.value,
            "assessment_id": self.assessment_id.value,
            "claims": tuple(item.canonical_value() for item in self.claims),
            "body": self.body,
            "body_digest": self.body_digest.value,
            "generation_invocation": self.generation_invocation.canonical_value(),
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelReviewDimensionAssessment:
    dimension: WorldModelReviewDimension
    decision: WorldModelReviewDecision
    finding_codes: tuple[str, ...] = ()

    def canonical_value(self) -> dict[str, object]:
        return {
            "dimension": self.dimension.value,
            "decision": self.decision.value,
            "finding_codes": self.finding_codes,
        }


@dataclass(frozen=True, slots=True)
class WorldModelReviewProposal:
    decision: WorldModelReviewDecision
    dimensions: tuple[WorldModelReviewDimensionAssessment, ...]
    checked_need_ids: tuple[str, ...]
    checked_constraint_ids: tuple[str, ...]
    checked_step_result_ids: tuple[StableId, ...]
    original_question_digest: Digest
    draft_digest: Digest
    read_set_digest: Digest
    finding_codes: tuple[str, ...]
    findings: tuple[str, ...]
    invocation_id: StableId
    invocation_digest: Digest


class WorldModelAnswerReviewer(Protocol):
    strategy_ref: str

    def review(
        self,
        *,
        question: WorldModelQuestion,
        requirement: WorldModelRequirementRevision,
        plan: WorldModelQueryPlan,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
        draft: WorldModelAnswerDraft,
        invocation: WorldModelStrategyInvocation,
    ) -> WorldModelReviewProposal: ...


@dataclass(frozen=True, slots=True)
class WorldModelAnswerReview:
    review_id: StableId
    question_id: StableId
    draft_id: StableId
    draft_digest: Digest
    decision: WorldModelReviewDecision
    dimensions: tuple[WorldModelReviewDimensionAssessment, ...]
    checked_need_ids: tuple[str, ...]
    checked_constraint_ids: tuple[str, ...]
    checked_step_result_ids: tuple[StableId, ...]
    finding_codes: tuple[str, ...]
    findings: tuple[str, ...]
    review_invocation: WorldModelStrategyInvocation
    generation_invocation_id: StableId
    read_authority: WorldModelReadAuthority
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "review_id": self.review_id.value,
            "question_id": self.question_id.value,
            "draft_id": self.draft_id.value,
            "draft_digest": self.draft_digest.value,
            "decision": self.decision.value,
            "dimensions": tuple(
                item.canonical_value() for item in self.dimensions
            ),
            "checked_need_ids": self.checked_need_ids,
            "checked_constraint_ids": self.checked_constraint_ids,
            "checked_step_result_ids": tuple(
                item.value for item in self.checked_step_result_ids
            ),
            "finding_codes": self.finding_codes,
            "findings": self.findings,
            "review_invocation": self.review_invocation.canonical_value(),
            "generation_invocation_id": self.generation_invocation_id.value,
            "read_authority": self.read_authority.canonical_value(),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelResponseAuthorization:
    authorization_id: StableId
    question_id: StableId
    requirement_id: StableId
    plan_id: StableId
    result_set_id: StableId
    assessment_id: StableId
    draft_id: StableId
    draft_digest: Digest
    review_id: StableId
    review_digest: Digest
    permission_digest: Digest
    read_authority: WorldModelReadAuthority
    chain_digest: Digest
    sink_id: str
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "authorization_id": self.authorization_id.value,
            "question_id": self.question_id.value,
            "requirement_id": self.requirement_id.value,
            "plan_id": self.plan_id.value,
            "result_set_id": self.result_set_id.value,
            "assessment_id": self.assessment_id.value,
            "draft_id": self.draft_id.value,
            "draft_digest": self.draft_digest.value,
            "review_id": self.review_id.value,
            "review_digest": self.review_digest.value,
            "permission_digest": self.permission_digest.value,
            "read_authority": self.read_authority.canonical_value(),
            "chain_digest": self.chain_digest.value,
            "sink_id": self.sink_id,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelDeliveryReceipt:
    receipt_id: str
    sink_id: str
    delivery_key: str
    body_digest: Digest
    projection_digest: Digest
    accepted: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        receipt_id: str,
        sink_id: str,
        delivery_key: str,
        body_digest: Digest,
        projection_digest: Digest,
        accepted: bool,
    ) -> "WorldModelDeliveryReceipt":
        if type(accepted) is not bool:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_RECEIPT_ACCEPTANCE_INVALID",
                "delivery receipt acceptance must be an exact boolean",
            )
        core = {
            "receipt_id": _text(receipt_id, "delivery receipt ID"),
            "sink_id": _text(sink_id, "delivery sink ID"),
            "delivery_key": _text(delivery_key, "delivery key"),
            "body_digest": body_digest.value,
            "projection_digest": projection_digest.value,
            "accepted": accepted,
        }
        return cls(
            receipt_id=core["receipt_id"],
            sink_id=core["sink_id"],
            delivery_key=core["delivery_key"],
            body_digest=body_digest,
            projection_digest=projection_digest,
            accepted=accepted,
            digest=digest_of(["WORLD_MODEL_DELIVERY_RECEIPT@1", core]),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "sink_id": self.sink_id,
            "delivery_key": self.delivery_key,
            "body_digest": self.body_digest.value,
            "projection_digest": self.projection_digest.value,
            "accepted": self.accepted,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelDelivery:
    delivery_id: StableId
    question_id: StableId
    authorization_id: StableId
    authorization_digest: Digest
    delivery_key: str
    sink_id: str
    body_digest: Digest
    projection_digest: Digest
    state: WorldModelDeliveryState
    receipt: WorldModelDeliveryReceipt | None
    failure_code: str | None
    revision: int
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "delivery_id": self.delivery_id.value,
            "question_id": self.question_id.value,
            "authorization_id": self.authorization_id.value,
            "authorization_digest": self.authorization_digest.value,
            "delivery_key": self.delivery_key,
            "sink_id": self.sink_id,
            "body_digest": self.body_digest.value,
            "projection_digest": self.projection_digest.value,
            "state": self.state.value,
            "receipt": self.receipt.canonical_value() if self.receipt else None,
            "failure_code": self.failure_code,
            "revision": self.revision,
            "digest": self.digest.value,
        }


class WorldModelEvaluationSink(Protocol):
    sink_id: str

    def deliver(
        self,
        *,
        delivery_key: str,
        body: str,
        body_digest: Digest,
        projection: Mapping[str, object],
        projection_digest: Digest,
    ) -> WorldModelDeliveryReceipt: ...


class InMemoryWorldModelEvaluationSink:
    """Closed local G3a sink; it has no Provider, Source, or network port."""

    sink_id = EVALUATION_ONLY_SINK

    def __init__(self) -> None:
        self._deliveries: dict[str, tuple[str, Digest, CanonicalFields, Digest]] = {}

    @property
    def delivery_count(self) -> int:
        return len(self._deliveries)

    def deliver(
        self,
        *,
        delivery_key: str,
        body: str,
        body_digest: Digest,
        projection: Mapping[str, object],
        projection_digest: Digest,
    ) -> WorldModelDeliveryReceipt:
        if digest_of(body) != body_digest or digest_of(
            ["WORLD_MODEL_EVALUATION_DELIVERY_PROJECTION@1", projection]
        ) != projection_digest:
            raise _invalid(
                "WORLD_MODEL_EVALUATION_SINK_INPUT_INVALID",
                "evaluation sink input digest does not verify",
            )
        frozen_projection = CanonicalFields(projection)
        value = (body, body_digest, frozen_projection, projection_digest)
        existing = self._deliveries.get(delivery_key)
        if existing is not None and existing != value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "evaluation sink delivery key already binds another body",
            )
        self._deliveries[delivery_key] = value
        return WorldModelDeliveryReceipt.create(
            receipt_id=_evaluation_receipt_id(delivery_key),
            sink_id=self.sink_id,
            delivery_key=delivery_key,
            body_digest=body_digest,
            projection_digest=projection_digest,
            accepted=True,
        )


@dataclass(frozen=True, slots=True)
class WorldModelAuthorityChain:
    question: WorldModelQuestion
    requirement: WorldModelRequirementRevision
    resolutions: WorldModelCandidateResolutionSet
    plan: WorldModelQueryPlan
    result_set: WorldModelQueryResultSet
    assessment: WorldModelAssessment
    draft: WorldModelAnswerDraft
    review: WorldModelAnswerReview
    authorization: WorldModelResponseAuthorization
    delivery: WorldModelDelivery
    provider_call_count: int
    network_operation_count: int
    digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "question": self.question.canonical_value(),
            "requirement": self.requirement.canonical_value(),
            "resolutions": self.resolutions.canonical_value(),
            "plan": self.plan.canonical_value(),
            "result_set": self.result_set.canonical_value(),
            "assessment": self.assessment.canonical_value(),
            "draft": self.draft.canonical_value(),
            "review": self.review.canonical_value(),
            "authorization": self.authorization.canonical_value(),
            "delivery": self.delivery.canonical_value(),
            "provider_call_count": self.provider_call_count,
            "network_operation_count": self.network_operation_count,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        self.question.require_valid()
        question_id = self.question.question_id
        read_authority = self.question.read_authority
        records = (
            self.requirement,
            self.resolutions,
            self.plan,
            self.result_set,
            self.assessment,
            self.draft,
            self.review,
            self.authorization,
        )
        if any(item.question_id != question_id for item in records):
            raise _invalid(
                "WORLD_MODEL_CHAIN_QUESTION_MISMATCH",
                "authority chain records belong to different Questions",
            )
        if any(item.read_authority != read_authority for item in records):
            raise _invalid(
                "WORLD_MODEL_CHAIN_READ_SET_MISMATCH",
                "authority chain records bind different Read Sets",
            )
        invocations = (
            self.requirement.planning_invocation,
            self.requirement.fidelity_review_invocation,
            self.resolutions.planning_invocation,
            self.plan.planning_invocation,
            self.draft.generation_invocation,
            self.review.review_invocation,
        )
        if (
            self.delivery.question_id != question_id
            or self.delivery.authorization_id
            != self.authorization.authorization_id
            or self.delivery.authorization_digest != self.authorization.digest
            or not _execution_boundary_is_valid(
                question=self.question,
                invocations=invocations,
                provider_call_count=self.provider_call_count,
                network_operation_count=self.network_operation_count,
            )
        ):
            raise _invalid(
                "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
                "authority chain violates its exact execution boundary",
            )
        _validate_exported_authority_chain(self)
        core = {
            key: value
            for key, value in self.canonical_value().items()
            if key != "digest"
        }
        if self.digest != digest_of(["WORLD_MODEL_AUTHORITY_CHAIN@1", core]):
            raise _invalid(
                "WORLD_MODEL_CHAIN_DIGEST_MISMATCH",
                "world-model authority chain is not canonical",
            )


class InMemoryWorldModelAuthorityStore:
    """Process-local authority used by the isolated answer worker.

    The final chain is exported as a sealed file by the interface layer.  This
    store is intentionally not the Knowledge authority database and exposes no
    payload or source-read capability.
    """

    _TYPES = (
        WorldModelQuestion,
        WorldModelRequirementRevision,
        WorldModelCandidateResolutionSet,
        WorldModelQueryPlan,
        WorldModelQueryResultSet,
        WorldModelAssessment,
        WorldModelAnswerDraft,
        WorldModelAnswerReview,
        WorldModelResponseAuthorization,
        WorldModelDelivery,
    )

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[type, dict[StableId, object]] = {
            item: {} for item in self._TYPES
        }
        self._stage_by_question: dict[tuple[type, StableId], StableId] = {}
        self._question_by_request_ref: dict[str, StableId] = {}

    def save(self, record):
        record_type = type(record)
        if record_type not in self._records:
            raise TypeError("unsupported world-model authority record")
        record_id = _record_id(record)
        question_id = record.question_id
        with self._lock:
            if record_type is WorldModelQuestion:
                current_question_id = self._question_by_request_ref.get(
                    record.request_ref
                )
                if current_question_id is not None:
                    current_question = self._records[WorldModelQuestion][
                        current_question_id
                    ]
                    if current_question != record:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "world-model request ref already binds another Question",
                        )
                    return current_question
            current_id = self._stage_by_question.get((record_type, question_id))
            if current_id is not None:
                current = self._records[record_type][current_id]
                if current != record:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "world-model stage already binds another authority record",
                    )
                return current
            existing = self._records[record_type].get(record_id)
            if existing is not None and existing != record:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "world-model authority identity conflict",
                )
            self._records[record_type][record_id] = record
            self._stage_by_question[(record_type, question_id)] = record_id
            if record_type is WorldModelQuestion:
                self._question_by_request_ref[record.request_ref] = record_id
            return record

    def get(self, record_type, record_id: StableId):
        with self._lock:
            try:
                return self._records[record_type][record_id]
            except KeyError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "world-model authority record was not found",
                ) from exc

    def get_for_question(self, record_type, question_id: StableId):
        with self._lock:
            try:
                record_id = self._stage_by_question[(record_type, question_id)]
                return self._records[record_type][record_id]
            except KeyError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "world-model authority stage was not found",
                ) from exc

    def prepare_delivery(
        self,
        *,
        question: WorldModelQuestion,
        authorization: WorldModelResponseAuthorization,
        draft: WorldModelAnswerDraft,
        projection_digest: Digest,
    ) -> WorldModelDelivery:
        with self._lock:
            key = (WorldModelDelivery, question.question_id)
            current_id = self._stage_by_question.get(key)
            if current_id is not None:
                current = self._records[WorldModelDelivery][current_id]
                if (
                    current.authorization_id != authorization.authorization_id
                    or current.authorization_digest != authorization.digest
                    or current.body_digest != draft.body_digest
                    or current.projection_digest != projection_digest
                ):
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "logical world-model delivery already binds another body",
                    )
                return current
            delivery_key = f"world-model:{digest_of(question.request_ref).value[-32:]}"
            core = {
                "question_id": question.question_id.value,
                "authorization_id": authorization.authorization_id.value,
                "authorization_digest": authorization.digest.value,
                "delivery_key": delivery_key,
                "sink_id": authorization.sink_id,
                "body_digest": draft.body_digest.value,
                "projection_digest": projection_digest.value,
                "state": WorldModelDeliveryState.PREPARED.value,
                "receipt": None,
                "failure_code": None,
                "revision": 1,
            }
            identity = digest_of(["WORLD_MODEL_DELIVERY_ID@1", core])
            record = WorldModelDelivery(
                delivery_id=_stable("world_model_delivery", identity),
                question_id=question.question_id,
                authorization_id=authorization.authorization_id,
                authorization_digest=authorization.digest,
                delivery_key=delivery_key,
                sink_id=authorization.sink_id,
                body_digest=draft.body_digest,
                projection_digest=projection_digest,
                state=WorldModelDeliveryState.PREPARED,
                receipt=None,
                failure_code=None,
                revision=1,
                digest=digest_of(["WORLD_MODEL_DELIVERY@1", core]),
            )
            self._records[WorldModelDelivery][record.delivery_id] = record
            self._stage_by_question[key] = record.delivery_id
            return record

    def transition_delivery(
        self,
        *,
        delivery_id: StableId,
        expected_revision: int,
        state: WorldModelDeliveryState,
        receipt: WorldModelDeliveryReceipt | None,
        failure_code: str | None,
    ) -> WorldModelDelivery:
        with self._lock:
            current = self.get(WorldModelDelivery, delivery_id)
            if current.revision != expected_revision:
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "world-model delivery revision is stale",
                )
            allowed = {
                WorldModelDeliveryState.PREPARED: {
                    WorldModelDeliveryState.SENDING
                },
                WorldModelDeliveryState.SENDING: {
                    WorldModelDeliveryState.DELIVERED,
                    WorldModelDeliveryState.FAILED,
                },
                WorldModelDeliveryState.DELIVERED: set(),
                WorldModelDeliveryState.FAILED: set(),
            }
            if state not in allowed[current.state]:
                raise DomainError(
                    ErrorCode.MANAGEMENT_STATE_CONFLICT,
                    "invalid world-model delivery transition",
                )
            if state is WorldModelDeliveryState.DELIVERED and receipt is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "delivered world-model result requires a receipt",
                )
            if state is WorldModelDeliveryState.DELIVERED:
                assert receipt is not None
                expected_receipt = WorldModelDeliveryReceipt.create(
                    receipt_id=_evaluation_receipt_id(current.delivery_key),
                    sink_id=receipt.sink_id,
                    delivery_key=receipt.delivery_key,
                    body_digest=receipt.body_digest,
                    projection_digest=receipt.projection_digest,
                    accepted=receipt.accepted,
                )
                if (
                    receipt != expected_receipt
                    or not receipt.accepted
                    or receipt.sink_id != current.sink_id
                    or receipt.delivery_key != current.delivery_key
                    or receipt.body_digest != current.body_digest
                    or receipt.projection_digest != current.projection_digest
                    or failure_code is not None
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "delivered world-model receipt does not bind the exact dispatch",
                    )
            elif receipt is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "non-delivered world-model state cannot carry a receipt",
                )
            if (
                state is WorldModelDeliveryState.FAILED
                and not failure_code
            ) or (
                state is WorldModelDeliveryState.SENDING
                and failure_code is not None
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "world-model delivery state has an invalid failure code",
                )
            core = {
                "question_id": current.question_id.value,
                "authorization_id": current.authorization_id.value,
                "authorization_digest": current.authorization_digest.value,
                "delivery_key": current.delivery_key,
                "sink_id": current.sink_id,
                "body_digest": current.body_digest.value,
                "projection_digest": current.projection_digest.value,
                "state": state.value,
                "receipt": receipt.canonical_value() if receipt else None,
                "failure_code": failure_code,
                "revision": current.revision + 1,
            }
            updated = replace(
                current,
                state=state,
                receipt=receipt,
                failure_code=failure_code,
                revision=current.revision + 1,
                digest=digest_of(["WORLD_MODEL_DELIVERY@1", core]),
            )
            self._records[WorldModelDelivery][delivery_id] = updated
            return updated


_ALLOWED_QUERY_OPERATIONS = (
    StructureViewOperation.CHILD_MODULE_INVENTORY,
    StructureViewOperation.DECLARED_METHOD_INVENTORY,
    StructureViewOperation.IMPLEMENTATION_CANDIDATES,
    StructureViewOperation.METHOD_IMPLEMENTATION,
    StructureViewOperation.DIRECT_NEIGHBORHOOD,
    StructureViewOperation.PATH_EXISTS,
    StructureViewOperation.ALL_SIMPLE_PATHS,
    StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
)
_QUERY_STEP_SCHEMAS: dict[
    StructureViewOperation,
    tuple[frozenset[str], frozenset[str], frozenset[str]],
] = {
    StructureViewOperation.CHILD_MODULE_INVENTORY: (
        frozenset({"system"}),
        frozenset(),
        frozenset(),
    ),
    StructureViewOperation.DECLARED_METHOD_INVENTORY: (
        frozenset({"java_type"}),
        frozenset(),
        frozenset(),
    ),
    StructureViewOperation.IMPLEMENTATION_CANDIDATES: (
        frozenset(),
        frozenset({"snapshot_id", "search_terms", "limit"}),
        frozenset(),
    ),
    StructureViewOperation.METHOD_IMPLEMENTATION: (
        frozenset({"method"}),
        frozenset(),
        frozenset(),
    ),
    StructureViewOperation.DIRECT_NEIGHBORHOOD: (
        frozenset({"entity"}),
        frozenset(),
        frozenset({"direction", "predicate"}),
    ),
    StructureViewOperation.PATH_EXISTS: (
        frozenset({"source", "target"}),
        frozenset(),
        frozenset({"predicate", "max_depth", "max_expansions"}),
    ),
    StructureViewOperation.ALL_SIMPLE_PATHS: (
        frozenset({"source", "target"}),
        frozenset(),
        frozenset(
            {"predicate", "max_depth", "max_paths", "max_expansions"}
        ),
    ),
    StructureViewOperation.ORDERED_SNAPSHOT_DIFF: (
        frozenset(),
        frozenset({"base_snapshot_id", "target_snapshot_id"}),
        frozenset(),
    ),
}
_QUERY_STEP_DEFAULTS: dict[StructureViewOperation, CanonicalFields] = {
    StructureViewOperation.CHILD_MODULE_INVENTORY: CanonicalFields({}),
    StructureViewOperation.DECLARED_METHOD_INVENTORY: CanonicalFields({}),
    StructureViewOperation.IMPLEMENTATION_CANDIDATES: CanonicalFields({}),
    StructureViewOperation.METHOD_IMPLEMENTATION: CanonicalFields({}),
    StructureViewOperation.DIRECT_NEIGHBORHOOD: CanonicalFields(
        {
            "direction": NeighborhoodDirection.BOTH.value,
            "predicate": None,
        }
    ),
    StructureViewOperation.PATH_EXISTS: CanonicalFields(
        {
            "predicate": RelationPredicate.DEPENDS_ON.value,
            "max_depth": _MAX_PATH_DEPTH,
            "max_expansions": _MAX_PATH_EXPANSIONS,
        }
    ),
    StructureViewOperation.ALL_SIMPLE_PATHS: CanonicalFields(
        {
            "predicate": RelationPredicate.DEPENDS_ON.value,
            "max_depth": _MAX_PATH_DEPTH,
            "max_paths": _MAX_PATHS,
            "max_expansions": _MAX_PATH_EXPANSIONS,
        }
    ),
    StructureViewOperation.ORDERED_SNAPSHOT_DIFF: CanonicalFields({}),
}
_QUERY_CAPABILITY_DEFINITIONS = tuple(
    {
        "operation": operation.value,
        "required_arguments": tuple(sorted(_QUERY_STEP_SCHEMAS[operation][0])),
        "required_parameters": tuple(sorted(_QUERY_STEP_SCHEMAS[operation][1])),
        "optional_parameters": tuple(sorted(_QUERY_STEP_SCHEMAS[operation][2])),
        "defaults": _QUERY_STEP_DEFAULTS[operation],
    }
    for operation in _ALLOWED_QUERY_OPERATIONS
)
WORLD_MODEL_QUERY_CAPABILITY_REGISTRY_DIGEST = digest_of(
    [
        "WORLD_MODEL_QUERY_CAPABILITY_REGISTRY@2",
        _QUERY_CAPABILITY_DEFINITIONS,
        WorldModelResourceLimits().canonical_value(),
    ]
)


class WorldModelAnsweringService:
    """Application owner for Requirement, Plan, Result, and Assessment."""

    def __init__(
        self,
        store: InMemoryWorldModelAuthorityStore,
        view: StructureViewService,
        *,
        model_route: str | None = None,
    ) -> None:
        self._store = store
        self._view = view
        self._read_authority = WorldModelReadAuthority.from_view(view)
        self._model_route = (
            _text(model_route, "model route")
            if model_route is not None
            else None
        )

    def open_question(
        self,
        *,
        request_ref: str,
        original_question: str,
        response_language: str,
        classification: str,
        permission_digest: Digest,
        resource_limits: WorldModelResourceLimits | None = None,
        explicit_entity_refs: Sequence[WorldModelExplicitEntityRef] = (),
    ) -> WorldModelQuestion:
        return self._store.save(
            WorldModelQuestion.create(
                request_ref=request_ref,
                original_question=original_question,
                response_language=response_language,
                classification=classification,
                permission_digest=permission_digest,
                view=self._view,
                resource_limits=resource_limits,
                explicit_entity_refs=explicit_entity_refs,
                model_route=self._model_route,
            )
        )

    def seal_requirement(
        self,
        *,
        question_id: StableId,
        planner: WorldModelRequirementPlanner,
        fidelity_reviewer: WorldModelRequirementFidelityReviewer,
    ) -> WorldModelRequirementRevision:
        question = self._question(question_id)
        planning = _issue_strategy_invocation(
            stage=OfflineStage.REQUIREMENT_PLANNING,
            question=question,
            input_digest=question.digest,
            strategy=planner,
        )
        proposal = planner.plan(question=question, invocation=planning)
        if not isinstance(proposal, WorldModelRequirementProposal):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_PROPOSAL_INVALID",
                "requirement planner returned an invalid typed proposal",
            )
        _require_invocation(proposal, planning, "requirement planning")
        self._validate_requirement_proposal(
            question, proposal, self._read_authority
        )
        proposal_digest = digest_of(
            [
                "WORLD_MODEL_REQUIREMENT_PROPOSAL@1",
                {
                    "original_question": proposal.original_question,
                    "response_language": proposal.response_language,
                    "needs": tuple(item.canonical_value() for item in proposal.needs),
                    "joint_constraints": tuple(
                        item.canonical_value() for item in proposal.joint_constraints
                    ),
                    "invocation_id": proposal.invocation_id.value,
                    "invocation_digest": proposal.invocation_digest.value,
                },
            ]
        )
        review_invocation = _issue_strategy_invocation(
            stage=OfflineStage.REQUIREMENT_FIDELITY_REVIEW,
            question=question,
            input_digest=proposal_digest,
            strategy=fidelity_reviewer,
        )
        fidelity = fidelity_reviewer.review(
            question=question,
            proposal=proposal,
            invocation=review_invocation,
        )
        if not isinstance(fidelity, WorldModelRequirementFidelityProposal):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_REVIEW_INVALID",
                "requirement fidelity reviewer returned an invalid proposal",
            )
        _require_invocation(fidelity, review_invocation, "requirement fidelity review")
        need_ids = tuple(item.need_id for item in proposal.needs)
        constraint_ids = tuple(
            item.constraint_id for item in proposal.joint_constraints
        )
        if (
            fidelity.decision is not WorldModelReviewDecision.APPROVE
            or fidelity.original_question_preserved is not True
            or fidelity.all_material_questions_covered is not True
            or fidelity.accepted_need_ids != need_ids
            or fidelity.accepted_constraint_ids != constraint_ids
            or fidelity.findings
        ):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_FIDELITY_REJECTED",
                "independent Requirement fidelity review did not accept every Need and constraint",
            )
        core = {
            "revision": 1,
            "question_id": question.question_id.value,
            "question_digest": question.digest.value,
            "original_question": proposal.original_question,
            "response_language": proposal.response_language,
            "needs": tuple(item.canonical_value() for item in proposal.needs),
            "joint_constraints": tuple(
                item.canonical_value() for item in proposal.joint_constraints
            ),
            "planning_invocation": planning.canonical_value(),
            "fidelity_review_invocation": review_invocation.canonical_value(),
            "fidelity_decision": fidelity.decision.value,
            "fidelity_accepted_need_ids": fidelity.accepted_need_ids,
            "fidelity_accepted_constraint_ids": (
                fidelity.accepted_constraint_ids
            ),
            "fidelity_original_question_preserved": (
                fidelity.original_question_preserved
            ),
            "fidelity_all_material_questions_covered": (
                fidelity.all_material_questions_covered
            ),
            "fidelity_findings": fidelity.findings,
            "read_authority": self._read_authority.canonical_value(),
        }
        identity = digest_of(["WORLD_MODEL_REQUIREMENT_ID@1", core])
        requirement_id = _stable("world_model_requirement", identity)
        return self._store.save(
            WorldModelRequirementRevision(
                requirement_id=requirement_id,
                revision=1,
                question_id=question.question_id,
                question_digest=question.digest,
                original_question=proposal.original_question,
                response_language=proposal.response_language,
                needs=proposal.needs,
                joint_constraints=proposal.joint_constraints,
                planning_invocation=planning,
                fidelity_review_invocation=review_invocation,
                fidelity_decision=fidelity.decision,
                fidelity_accepted_need_ids=fidelity.accepted_need_ids,
                fidelity_accepted_constraint_ids=(
                    fidelity.accepted_constraint_ids
                ),
                fidelity_original_question_preserved=(
                    fidelity.original_question_preserved
                ),
                fidelity_all_material_questions_covered=(
                    fidelity.all_material_questions_covered
                ),
                fidelity_findings=fidelity.findings,
                read_authority=self._read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_REQUIREMENT@1",
                        {"requirement_id": requirement_id.value, **core},
                    ]
                ),
            )
        )

    def seal_query_plan(
        self,
        *,
        requirement_id: StableId,
        planner: WorldModelQueryPlanner,
    ) -> WorldModelQueryPlan:
        requirement = self._store.get(
            WorldModelRequirementRevision, requirement_id
        )
        question = self._question(requirement.question_id)
        self._verify_requirement(requirement, question)
        invocation = _issue_strategy_invocation(
            stage=OfflineStage.QUERY_PLANNING,
            question=question,
            input_digest=requirement.digest,
            strategy=planner,
        )
        proposal = planner.plan(
            question=question,
            requirement=requirement,
            invocation=invocation,
        )
        if not isinstance(proposal, WorldModelQueryPlanProposal):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_PROPOSAL_INVALID",
                "query planner returned an invalid typed proposal",
            )
        _require_invocation(proposal, invocation, "query planning")
        if (
            proposal.requirement_id != requirement.requirement_id
            or proposal.requirement_digest != requirement.digest
            or proposal.read_set_digest != self._read_authority.read_set_digest
            or proposal.ordered_bundle_digest
            != self._read_authority.ordered_bundle_digest
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_BINDING_MISMATCH",
                "query proposal binds another Requirement or Read Set",
            )
        if any(
            step.operation not in _ALLOWED_QUERY_OPERATIONS
            for step in proposal.steps
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_OPERATION_UNREGISTERED",
                "query proposal contains an unregistered operation",
            )
        if proposal.investigation_trace is not None:
            validate_bounded_investigation_trace(
                proposal.investigation_trace,
                view=self._view,
                question_digest=question.digest,
            )
            if (
                proposal.investigation_trace.need_ids
                != tuple(item.need_id for item in requirement.needs)
                or question.read_authority.profile_refs
                != (JAVA_SOURCE_SEMANTICS_PROFILE_REF,)
            ):
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_TRACE_BINDING_INVALID",
                    "bounded investigation trace binds another Requirement or Profile",
                )
        proposal = self._normalize_plan_proposal(proposal)
        self._validate_plan_proposal(
            question, requirement, proposal, self._read_authority
        )
        proposal_digest = _query_plan_proposal_digest(proposal)
        resolutions = tuple(
            self._resolve_selector(
                question,
                selector,
                investigation_trace=proposal.investigation_trace,
            )
            for selector in proposal.selectors
        )
        resolution_core = {
            "question_id": question.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "requirement_digest": requirement.digest.value,
            "proposal_digest": proposal_digest.value,
            "planning_invocation": invocation.canonical_value(),
            "resolutions": tuple(item.canonical_value() for item in resolutions),
            "read_authority": self._read_authority.canonical_value(),
        }
        resolution_identity = digest_of(
            ["WORLD_MODEL_RESOLUTION_SET_ID@1", resolution_core]
        )
        resolution_set_id = _stable(
            "world_model_resolution_set", resolution_identity
        )
        resolution_set = self._store.save(
            WorldModelCandidateResolutionSet(
                resolution_set_id=resolution_set_id,
                question_id=question.question_id,
                requirement_id=requirement.requirement_id,
                requirement_digest=requirement.digest,
                proposal_digest=proposal_digest,
                planning_invocation=invocation,
                resolutions=resolutions,
                read_authority=self._read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_RESOLUTION_SET@1",
                        {
                            "resolution_set_id": resolution_set_id.value,
                            **resolution_core,
                        },
                    ]
                ),
            )
        )
        by_selector = {
            item.selector.selector_id: item for item in resolution_set.resolutions
        }
        steps = tuple(
            self._seal_query_step(item, by_selector)
            for item in proposal.steps
        )
        core = {
            "question_id": question.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "requirement_digest": requirement.digest.value,
            "resolution_set_id": resolution_set.resolution_set_id.value,
            "resolution_set_digest": resolution_set.digest.value,
            "planning_invocation": invocation.canonical_value(),
            "capability_registry_digest": (
                WORLD_MODEL_QUERY_CAPABILITY_REGISTRY_DIGEST.value
            ),
            "steps": tuple(item.canonical_value() for item in steps),
            "explicit_gaps": tuple(
                item.canonical_value() for item in proposal.explicit_gaps
            ),
            "read_authority": self._read_authority.canonical_value(),
        }
        if proposal.investigation_trace is not None:
            core["investigation_trace"] = (
                proposal.investigation_trace.canonical_value()
            )
        identity = digest_of(["WORLD_MODEL_QUERY_PLAN_ID@1", core])
        plan_id = _stable("world_model_query_plan", identity)
        return self._store.save(
            WorldModelQueryPlan(
                plan_id=plan_id,
                question_id=question.question_id,
                requirement_id=requirement.requirement_id,
                requirement_digest=requirement.digest,
                resolution_set_id=resolution_set.resolution_set_id,
                resolution_set_digest=resolution_set.digest,
                planning_invocation=invocation,
                capability_registry_digest=(
                    WORLD_MODEL_QUERY_CAPABILITY_REGISTRY_DIGEST
                ),
                steps=steps,
                explicit_gaps=proposal.explicit_gaps,
                investigation_trace=proposal.investigation_trace,
                read_authority=self._read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_QUERY_PLAN@1",
                        {"plan_id": plan_id.value, **core},
                    ]
                ),
            )
        )

    def execute_query_plan(
        self, *, plan_id: StableId
    ) -> WorldModelQueryResultSet:
        plan = self._store.get(WorldModelQueryPlan, plan_id)
        resolution_set = self._store.get(
            WorldModelCandidateResolutionSet, plan.resolution_set_id
        )
        self._verify_plan_authority(plan, resolution_set)
        by_selector = {
            item.selector.selector_id: item for item in resolution_set.resolutions
        }
        results = tuple(
            self._execute_step(step, by_selector)
            for step in plan.steps
            if step.state is QueryStepState.READY
        )
        support_map_digest = digest_of(
            [
                "WORLD_MODEL_QUERY_SUPPORT_MAP@1",
                tuple(
                    support.canonical_value()
                    for result in results
                    for support in result.view_result.support_map
                ),
            ]
        )
        evidence_allowlist_digest = digest_of(
            [
                "WORLD_MODEL_QUERY_EVIDENCE_ALLOWLIST@1",
                tuple(
                    sorted(
                        {
                            evidence.value
                            for result in results
                            for evidence in result.view_result.evidence_allowlist
                        }
                    )
                ),
            ]
        )
        core = {
            "question_id": plan.question_id.value,
            "requirement_id": plan.requirement_id.value,
            "plan_id": plan.plan_id.value,
            "plan_digest": plan.digest.value,
            "step_results": tuple(item.canonical_value() for item in results),
            "read_authority": self._read_authority.canonical_value(),
            "support_map_digest": support_map_digest.value,
            "evidence_allowlist_digest": evidence_allowlist_digest.value,
        }
        identity = digest_of(["WORLD_MODEL_QUERY_RESULT_SET_ID@1", core])
        result_set_id = _stable("world_model_result_set", identity)
        return self._store.save(
            WorldModelQueryResultSet(
                result_set_id=result_set_id,
                question_id=plan.question_id,
                requirement_id=plan.requirement_id,
                plan_id=plan.plan_id,
                plan_digest=plan.digest,
                step_results=results,
                read_authority=self._read_authority,
                support_map_digest=support_map_digest,
                evidence_allowlist_digest=evidence_allowlist_digest,
                digest=digest_of(
                    [
                        "WORLD_MODEL_QUERY_RESULT_SET@1",
                        {"result_set_id": result_set_id.value, **core},
                    ]
                ),
            )
        )

    def assess(
        self, *, result_set_id: StableId
    ) -> WorldModelAssessment:
        result_set = self._store.get(
            WorldModelQueryResultSet, result_set_id
        )
        plan = self._store.get(WorldModelQueryPlan, result_set.plan_id)
        requirement = self._store.get(
            WorldModelRequirementRevision, result_set.requirement_id
        )
        resolution_set = self._store.get(
            WorldModelCandidateResolutionSet, plan.resolution_set_id
        )
        self.verify_query_result_set(result_set.result_set_id)
        results_by_step = {
            item.step_id: item for item in result_set.step_results
        }
        gaps = {item.need_id: item for item in plan.explicit_gaps}
        needs = tuple(
            self._assess_need(
                need,
                plan=plan,
                results_by_step=results_by_step,
                explicit_gap=gaps.get(need.need_id),
            )
            for need in requirement.needs
        )
        by_need = {item.need_id: item for item in needs}
        joints = tuple(
            self._assess_joint(
                item,
                needs=by_need,
                plan=plan,
                results_by_step=results_by_step,
            )
            for item in requirement.joint_constraints
        )
        sufficient = all(
            item.outcome
            in {
                WorldModelNeedOutcome.SATISFIED,
                WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE,
            }
            for item in needs
        ) and all(item.satisfied for item in joints)
        core = {
            "question_id": requirement.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "requirement_digest": requirement.digest.value,
            "plan_id": plan.plan_id.value,
            "plan_digest": plan.digest.value,
            "result_set_id": result_set.result_set_id.value,
            "result_set_digest": result_set.digest.value,
            "needs": tuple(item.canonical_value() for item in needs),
            "joint_constraints": tuple(item.canonical_value() for item in joints),
            "sufficient": sufficient,
            "read_authority": self._read_authority.canonical_value(),
        }
        identity = digest_of(["WORLD_MODEL_ASSESSMENT_ID@1", core])
        assessment_id = _stable("world_model_assessment", identity)
        return self._store.save(
            WorldModelAssessment(
                assessment_id=assessment_id,
                question_id=requirement.question_id,
                requirement_id=requirement.requirement_id,
                requirement_digest=requirement.digest,
                plan_id=plan.plan_id,
                plan_digest=plan.digest,
                result_set_id=result_set.result_set_id,
                result_set_digest=result_set.digest,
                needs=needs,
                joint_constraints=joints,
                sufficient=sufficient,
                read_authority=self._read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_ASSESSMENT@1",
                        {"assessment_id": assessment_id.value, **core},
                    ]
                ),
            )
        )

    def verify_query_result_set(self, result_set_id: StableId) -> None:
        """Re-execute every issued Result against the exact mounted Bundles."""

        result_set = self._store.get(
            WorldModelQueryResultSet, result_set_id
        )
        plan = self._store.get(WorldModelQueryPlan, result_set.plan_id)
        if (
            result_set.question_id != plan.question_id
            or result_set.requirement_id != plan.requirement_id
            or result_set.plan_digest != plan.digest
            or result_set.read_authority != self._read_authority
            or plan.read_authority != self._read_authority
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_RESULT_READ_SET_MISMATCH",
                "Query Result authority binds another Plan or Read Set",
            )
        resolution_set = self._store.get(
            WorldModelCandidateResolutionSet, plan.resolution_set_id
        )
        self._verify_plan_authority(plan, resolution_set)
        by_selector = {
            item.selector.selector_id: item for item in resolution_set.resolutions
        }
        expected = tuple(
            self._execute_step(step, by_selector)
            for step in plan.steps
            if step.state is QueryStepState.READY
        )
        if expected != result_set.step_results:
            raise _invalid(
                "WORLD_MODEL_QUERY_RESULT_REPLAY_MISMATCH",
                "stored Query Result differs from exact Plan replay",
            )
        expected_support_digest = digest_of(
            [
                "WORLD_MODEL_QUERY_SUPPORT_MAP@1",
                tuple(
                    support.canonical_value()
                    for result in expected
                    for support in result.view_result.support_map
                ),
            ]
        )
        expected_allowlist_digest = digest_of(
            [
                "WORLD_MODEL_QUERY_EVIDENCE_ALLOWLIST@1",
                tuple(
                    sorted(
                        {
                            evidence.value
                            for result in expected
                            for evidence in result.view_result.evidence_allowlist
                        }
                    )
                ),
            ]
        )
        if (
            result_set.support_map_digest != expected_support_digest
            or result_set.evidence_allowlist_digest
            != expected_allowlist_digest
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_SUPPORT_CLOSURE_MISMATCH",
                "Query Result Support or Evidence allowlist closure is invalid",
            )
        core = {
            key: value
            for key, value in result_set.canonical_value().items()
            if key not in {"result_set_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_QUERY_RESULT_SET_ID@1", core])
        expected_id = _stable("world_model_result_set", identity)
        expected_digest = digest_of(
            [
                "WORLD_MODEL_QUERY_RESULT_SET@1",
                {"result_set_id": expected_id.value, **core},
            ]
        )
        if (
            result_set.result_set_id != expected_id
            or result_set.digest != expected_digest
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_RESULT_DIGEST_MISMATCH",
                "Query Result authority is not canonical",
            )

    def _question(self, question_id: StableId) -> WorldModelQuestion:
        question = self._store.get(WorldModelQuestion, question_id)
        question.require_valid()
        if (
            question.read_authority != self._read_authority
            or question.model_route != self._model_route
            or question.external_dispatch_allowed is not (
                self._model_route is not None
            )
        ):
            raise _invalid(
                "WORLD_MODEL_QUESTION_READ_SET_MISMATCH",
                "Question belongs to another mounted Read Set or execution route",
            )
        return question

    def _verify_requirement(
        self,
        requirement: WorldModelRequirementRevision,
        question: WorldModelQuestion,
    ) -> None:
        requirement.planning_invocation.require_valid()
        requirement.fidelity_review_invocation.require_valid()
        if (
            requirement.question_id != question.question_id
            or requirement.question_digest != question.digest
            or requirement.original_question != question.original_question
            or requirement.response_language != question.response_language
            or requirement.read_authority != self._read_authority
            or type(requirement.revision) is not int
            or requirement.revision != 1
            or requirement.planning_invocation.stage
            is not OfflineStage.REQUIREMENT_PLANNING
            or requirement.planning_invocation.question_id != question.question_id
            or requirement.planning_invocation.question_digest != question.digest
            or requirement.planning_invocation.input_digest != question.digest
            or requirement.fidelity_review_invocation.stage
            is not OfflineStage.REQUIREMENT_FIDELITY_REVIEW
            or requirement.fidelity_review_invocation.question_id
            != question.question_id
            or requirement.fidelity_review_invocation.question_digest
            != question.digest
            or requirement.fidelity_decision
            is not WorldModelReviewDecision.APPROVE
            or requirement.fidelity_accepted_need_ids
            != tuple(item.need_id for item in requirement.needs)
            or requirement.fidelity_accepted_constraint_ids
            != tuple(
                item.constraint_id for item in requirement.joint_constraints
            )
            or requirement.fidelity_original_question_preserved is not True
            or requirement.fidelity_all_material_questions_covered is not True
            or requirement.fidelity_findings
        ):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_AUTHORITY_MISMATCH",
                "Requirement Revision does not bind its exact Question and fidelity review",
            )
        reconstructed_proposal = WorldModelRequirementProposal(
            original_question=requirement.original_question,
            response_language=requirement.response_language,
            needs=requirement.needs,
            joint_constraints=requirement.joint_constraints,
            invocation_id=requirement.planning_invocation.invocation_id,
            invocation_digest=requirement.planning_invocation.digest,
        )
        self._validate_requirement_proposal(
            question, reconstructed_proposal, self._read_authority
        )
        proposal_digest = digest_of(
            [
                "WORLD_MODEL_REQUIREMENT_PROPOSAL@1",
                {
                    "original_question": reconstructed_proposal.original_question,
                    "response_language": reconstructed_proposal.response_language,
                    "needs": tuple(
                        item.canonical_value()
                        for item in reconstructed_proposal.needs
                    ),
                    "joint_constraints": tuple(
                        item.canonical_value()
                        for item in reconstructed_proposal.joint_constraints
                    ),
                    "invocation_id": (
                        reconstructed_proposal.invocation_id.value
                    ),
                    "invocation_digest": (
                        reconstructed_proposal.invocation_digest.value
                    ),
                },
            ]
        )
        if requirement.fidelity_review_invocation.input_digest != proposal_digest:
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_REVIEW_INPUT_MISMATCH",
                "Requirement reviewer did not receive the exact proposal",
            )
        core = {
            key: value
            for key, value in requirement.canonical_value().items()
            if key not in {"requirement_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_REQUIREMENT_ID@1", core])
        expected_id = _stable("world_model_requirement", identity)
        expected_digest = digest_of(
            [
                "WORLD_MODEL_REQUIREMENT@1",
                {"requirement_id": expected_id.value, **core},
            ]
        )
        if (
            requirement.requirement_id != expected_id
            or requirement.digest != expected_digest
        ):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_DIGEST_MISMATCH",
                "Requirement Revision is not canonical",
            )

    @staticmethod
    def _validate_requirement_proposal(
        question: WorldModelQuestion,
        proposal: WorldModelRequirementProposal,
        read_authority: WorldModelReadAuthority,
    ) -> None:
        if (
            proposal.original_question != question.original_question
            or proposal.response_language != question.response_language
            or not proposal.needs
            or len(proposal.needs) > question.resource_limits.max_needs
            or len(proposal.joint_constraints)
            > question.resource_limits.max_joint_constraints
        ):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_FIDELITY_INVALID",
                "Requirement proposal changed the question, language, or omitted all Needs",
            )
        need_ids = tuple(item.need_id for item in proposal.needs)
        if len(set(need_ids)) != len(need_ids):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_NEED_DUPLICATE",
                "Requirement Need IDs must be unique",
            )
        constraint_ids = tuple(
            item.constraint_id for item in proposal.joint_constraints
        )
        if len(set(constraint_ids)) != len(constraint_ids):
            raise _invalid(
                "WORLD_MODEL_REQUIREMENT_CONSTRAINT_DUPLICATE",
                "Requirement constraint IDs must be unique",
            )
        known = set(need_ids)
        for constraint in proposal.joint_constraints:
            _text(constraint.constraint_id, "constraint ID")
            _text(constraint.description, "constraint description")
            if (
                not isinstance(constraint.kind, WorldModelJointConstraintKind)
                or not constraint.need_ids
                or len(set(constraint.need_ids)) != len(constraint.need_ids)
                or any(item not in known for item in constraint.need_ids)
            ):
                raise _invalid(
                    "WORLD_MODEL_REQUIREMENT_CONSTRAINT_INVALID",
                    "Requirement constraint references unknown or duplicate Needs",
                )
            if constraint.kind is WorldModelJointConstraintKind.ORDERED_READ_SET:
                if (
                    constraint.base_snapshot_id is None
                    or constraint.target_snapshot_id is None
                    or not _adjacent_order(
                        read_authority.snapshot_ids,
                        constraint.base_snapshot_id,
                        constraint.target_snapshot_id,
                    )
                ):
                    raise _invalid(
                        "WORLD_MODEL_REQUIREMENT_ORDER_INVALID",
                        "ordered constraint must preserve caller-declared adjacent Snapshot order",
                    )
            elif (
                constraint.base_snapshot_id is not None
                or constraint.target_snapshot_id is not None
            ):
                raise _invalid(
                    "WORLD_MODEL_REQUIREMENT_CONSTRAINT_SHAPE_INVALID",
                    "non-ordered Joint Constraint cannot carry Snapshot order",
                )

    @staticmethod
    def _validate_plan_proposal(
        question: WorldModelQuestion,
        requirement: WorldModelRequirementRevision,
        proposal: WorldModelQueryPlanProposal,
        read_authority: WorldModelReadAuthority,
    ) -> None:
        need_ids = {item.need_id for item in requirement.needs}
        constraints_by_id = {
            item.constraint_id: item for item in requirement.joint_constraints
        }
        selector_ids = tuple(item.selector_id for item in proposal.selectors)
        step_ids = tuple(item.step_id for item in proposal.steps)
        gap_ids = tuple(item.need_id for item in proposal.explicit_gaps)
        if (
            len(proposal.selectors)
            > question.resource_limits.max_query_selectors
            or len(proposal.steps) > question.resource_limits.max_query_steps
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_RESOURCE_LIMIT",
                "Query Plan exceeds the Question's fixed resource limits",
            )
        if len(set(selector_ids)) != len(selector_ids):
            raise _invalid(
                "WORLD_MODEL_QUERY_SELECTOR_DUPLICATE",
                "query selector IDs must be unique",
            )
        if len(set(step_ids)) != len(step_ids):
            raise _invalid(
                "WORLD_MODEL_QUERY_STEP_DUPLICATE",
                "query step IDs must be unique",
            )
        if len(set(gap_ids)) != len(gap_ids):
            raise _invalid(
                "WORLD_MODEL_QUERY_GAP_DUPLICATE",
                "query plan may declare one explicit Gap per Need",
            )
        covered: set[str] = set(gap_ids)
        step_needs: set[str] = set()
        used_selector_ids: set[str] = set()
        for selector in proposal.selectors:
            WorldModelAnsweringService._validate_selector(
                question,
                selector,
                need_ids,
                read_authority,
                proposal.investigation_trace,
            )
        for step in proposal.steps:
            if (
                not step.need_ids
                or len(set(step.need_ids)) != len(step.need_ids)
                or any(item not in need_ids for item in step.need_ids)
                or len(set(step.constraint_ids)) != len(step.constraint_ids)
                or any(
                    item not in constraints_by_id
                    for item in step.constraint_ids
                )
                or step.operation not in _ALLOWED_QUERY_OPERATIONS
            ):
                raise _invalid(
                    "WORLD_MODEL_QUERY_STEP_INVALID",
                    "query step is unregistered or references unknown Needs",
                )
            for constraint_id in step.constraint_ids:
                constraint = constraints_by_id[constraint_id]
                if not set(step.need_ids).issubset(
                    set(constraint.need_ids)
                ):
                    raise _invalid(
                        "WORLD_MODEL_QUERY_CONSTRAINT_NEED_MISMATCH",
                        "query step maps a Joint Constraint to unrelated Needs",
                    )
            WorldModelAnsweringService._validate_step_shape(
                step, set(selector_ids)
            )
            WorldModelAnsweringService._validate_step_parameters(
                question, step, read_authority
            )
            referenced_selectors = set(step.arguments.values())
            used_selector_ids.update(referenced_selectors)
            selector_by_id = {
                item.selector_id: item for item in proposal.selectors
            }
            if any(
                not set(step.need_ids).issubset(
                    set(selector_by_id[selector_id].need_ids)
                )
                for selector_id in referenced_selectors
            ):
                raise _invalid(
                    "WORLD_MODEL_QUERY_SELECTOR_NEED_MISMATCH",
                    "query step uses an Entity selector outside the selector's declared Needs",
                )
            step_needs.update(step.need_ids)
        if set(gap_ids) & step_needs:
            raise _invalid(
                "WORLD_MODEL_QUERY_GAP_CONFLICT",
                "a Need cannot have both an explicit Gap and a query step",
            )
        covered.update(step_needs)
        if covered != need_ids:
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_NEED_OMITTED",
                "validated Query Plan must cover every Requirement Need",
            )
        if used_selector_ids != set(selector_ids):
            raise _invalid(
                "WORLD_MODEL_QUERY_SELECTOR_UNUSED",
                "every resolved Entity selector must be consumed by a query step",
            )
        if proposal.investigation_trace is not None:
            WorldModelAnsweringService._validate_investigation_plan_binding(
                proposal
            )
        for selector in proposal.selectors:
            if selector.origin is not EntitySelectorOrigin.IMPLEMENTATION_FEATURES:
                continue
            matching_search_steps = tuple(
                step
                for step in proposal.steps
                if step.operation
                is StructureViewOperation.IMPLEMENTATION_CANDIDATES
                and step.need_ids == selector.need_ids
                and step.parameters["snapshot_id"]
                == selector.snapshot_id.value
                and step.parameters["search_terms"] == selector.search_terms
                and step.parameters["limit"] == selector.max_candidates
            )
            consuming_method_steps = tuple(
                step
                for step in proposal.steps
                if step.operation is StructureViewOperation.METHOD_IMPLEMENTATION
                and selector.selector_id in step.arguments.values()
            )
            if len(matching_search_steps) != 1 or len(consuming_method_steps) != 1:
                raise _invalid(
                    "WORLD_MODEL_IMPLEMENTATION_CHAIN_INVALID",
                    "implementation method selection must bind one exact candidate Result and one method query",
                )
        total_entity_candidates = sum(
            selector.max_candidates for selector in proposal.selectors
        ) + sum(
            int(step.parameters["limit"])
            for step in proposal.steps
            if step.operation
            is StructureViewOperation.IMPLEMENTATION_CANDIDATES
        )
        total_paths = sum(
            int(step.parameters["max_paths"])
            for step in proposal.steps
            if step.operation is StructureViewOperation.ALL_SIMPLE_PATHS
        )
        total_path_expansions = sum(
            int(step.parameters["max_expansions"])
            for step in proposal.steps
            if step.operation
            in {
                StructureViewOperation.PATH_EXISTS,
                StructureViewOperation.ALL_SIMPLE_PATHS,
            }
        )
        if (
            total_entity_candidates
            > question.resource_limits.max_total_entity_candidates
            or total_paths > question.resource_limits.max_total_paths
            or total_path_expansions
            > question.resource_limits.max_total_path_expansions
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_AGGREGATE_BUDGET_INVALID",
                "Query Plan exceeds the Question's aggregate execution budget",
            )
        for constraint in requirement.joint_constraints:
            mapped_steps = tuple(
                step
                for step in proposal.steps
                if constraint.constraint_id in step.constraint_ids
            )
            mapped_needs = {
                need_id for step in mapped_steps for need_id in step.need_ids
            }
            if not mapped_steps or mapped_needs != set(constraint.need_ids):
                raise _invalid(
                    "WORLD_MODEL_QUERY_CONSTRAINT_OMITTED",
                    "validated Query Plan must map every Joint Constraint and constrained Need",
                )
            if constraint.kind is WorldModelJointConstraintKind.ORDERED_READ_SET:
                ordered_steps = tuple(
                    step
                    for step in mapped_steps
                    if step.operation
                    is StructureViewOperation.ORDERED_SNAPSHOT_DIFF
                    and _stable_parameter(step.parameters, "base_snapshot_id")
                    == constraint.base_snapshot_id
                    and _stable_parameter(step.parameters, "target_snapshot_id")
                    == constraint.target_snapshot_id
                )
                if len(ordered_steps) != 1:
                    raise _invalid(
                        "WORLD_MODEL_QUERY_ORDER_CONSTRAINT_UNPROVEN",
                        "ordered Read Set constraint requires one exact ordered diff step",
                    )
        for gap in proposal.explicit_gaps:
            if not isinstance(gap.reason_code, WorldModelGapReason):
                raise _invalid(
                    "WORLD_MODEL_QUERY_GAP_REASON_INVALID",
                    "Knowledge Gap reason must use the closed G3a reason catalog",
                )
            _text(gap.detail, "Knowledge Gap detail")

    @staticmethod
    def _normalize_plan_proposal(
        proposal: WorldModelQueryPlanProposal,
    ) -> WorldModelQueryPlanProposal:
        normalized_steps = tuple(
            WorldModelQueryStepProposal(
                step_id=step.step_id,
                need_ids=step.need_ids,
                operation=step.operation,
                arguments=step.arguments,
                parameters=CanonicalFields(
                    {
                        **dict(_QUERY_STEP_DEFAULTS[step.operation]),
                        **dict(step.parameters),
                    }
                ),
                constraint_ids=step.constraint_ids,
            )
            for step in proposal.steps
        )
        return WorldModelQueryPlanProposal(
            requirement_id=proposal.requirement_id,
            requirement_digest=proposal.requirement_digest,
            read_set_digest=proposal.read_set_digest,
            ordered_bundle_digest=proposal.ordered_bundle_digest,
            selectors=proposal.selectors,
            steps=normalized_steps,
            explicit_gaps=proposal.explicit_gaps,
            invocation_id=proposal.invocation_id,
            invocation_digest=proposal.invocation_digest,
            investigation_trace=proposal.investigation_trace,
        )

    @staticmethod
    def _validate_investigation_plan_binding(
        proposal: WorldModelQueryPlanProposal,
    ) -> None:
        trace = proposal.investigation_trace
        assert trace is not None
        if proposal.explicit_gaps:
            raise _invalid(
                "WORLD_MODEL_INVESTIGATION_PLAN_GAP_INVALID",
                "bounded investigation Plan cannot replace its trace with an explicit Gap",
            )
        selectors = {item.selector_id: item for item in proposal.selectors}

        def ref_value(value: InvestigationEntityRef) -> tuple[str, ...]:
            return (
                value.source_result_id.value,
                value.source_result_digest.value,
                value.entity_root_id.value,
                value.entity_state_id.value,
            )

        def selector_value(selector_id: object) -> tuple[str, ...]:
            if not isinstance(selector_id, str) or selector_id not in selectors:
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_PLAN_SELECTOR_INVALID",
                    "investigation Plan uses an unknown selector",
                )
            selector = selectors[selector_id]
            if (
                selector.origin
                is not EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT
                or selector.source_result_id is None
                or selector.source_result_digest is None
                or selector.entity_root_id is None
                or selector.entity_state_id is None
            ):
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_PLAN_SELECTOR_INVALID",
                    "investigation Plan selector lacks sealed Result provenance",
                )
            return (
                selector.source_result_id.value,
                selector.source_result_digest.value,
                selector.entity_root_id.value,
                selector.entity_state_id.value,
            )

        expected: list[
            tuple[
                StructureViewOperation,
                tuple[tuple[str, tuple[str, ...]], ...],
                CanonicalFields,
            ]
        ] = []
        for trace_step in trace.steps:
            item = trace_step.proposal
            if item.operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
                assert item.snapshot_id is not None
                assert item.limit is not None
                expected.append(
                    (
                        StructureViewOperation.IMPLEMENTATION_CANDIDATES,
                        (),
                        CanonicalFields(
                            {
                                "snapshot_id": item.snapshot_id.value,
                                "search_terms": item.search_terms,
                                "limit": item.limit,
                            }
                        ),
                    )
                )
            elif item.operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
                expected.extend(
                    (
                        StructureViewOperation.METHOD_IMPLEMENTATION,
                        (("method", ref_value(value)),),
                        CanonicalFields({}),
                    )
                    for value in item.method_refs
                )
            elif item.operation is InvestigationOperation.DECLARED_METHOD_INVENTORY:
                expected.append(
                    (
                        StructureViewOperation.DECLARED_METHOD_INVENTORY,
                        (("java_type", ref_value(item.entity_refs[0])),),
                        CanonicalFields({}),
                    )
                )
            elif item.operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
                expected.append(
                    (
                        StructureViewOperation.DIRECT_NEIGHBORHOOD,
                        (("entity", ref_value(item.entity_refs[0])),),
                        CanonicalFields(
                            {
                                "direction": item.direction.value,
                                "predicate": (
                                    item.predicate.value
                                    if item.predicate is not None
                                    else None
                                ),
                            }
                        ),
                    )
                )
            elif item.operation in {
                InvestigationOperation.PATH_EXISTS,
                InvestigationOperation.ALL_SIMPLE_PATHS,
            }:
                parameters: dict[str, object] = {
                    "predicate": item.predicate.value,
                    "max_depth": item.max_depth,
                    "max_expansions": item.max_expansions,
                }
                if item.operation is InvestigationOperation.ALL_SIMPLE_PATHS:
                    parameters["max_paths"] = item.max_paths
                expected.append(
                    (
                        (
                            StructureViewOperation.PATH_EXISTS
                            if item.operation is InvestigationOperation.PATH_EXISTS
                            else StructureViewOperation.ALL_SIMPLE_PATHS
                        ),
                        (
                            ("source", ref_value(item.entity_refs[0])),
                            ("target", ref_value(item.entity_refs[1])),
                        ),
                        CanonicalFields(parameters),
                    )
                )
            else:  # pragma: no cover - trace steps cannot contain FINISH
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_PLAN_OPERATION_INVALID",
                    "investigation trace contains a terminal operation as a step",
                )
        actual = tuple(
            (
                step.operation,
                tuple(
                    (name, selector_value(selector_id))
                    for name, selector_id in step.arguments.items()
                ),
                step.parameters,
            )
            for step in proposal.steps
        )
        if (
            actual != tuple(expected)
            or any(step.need_ids != trace.need_ids for step in proposal.steps)
            or any(step.constraint_ids for step in proposal.steps)
        ):
            raise _invalid(
                "WORLD_MODEL_INVESTIGATION_PLAN_TRACE_MISMATCH",
                "Query Plan does not exactly replay the sealed investigation trace",
            )

    @staticmethod
    def _validate_selector(
        question: WorldModelQuestion,
        selector: WorldModelEntitySelectorProposal,
        need_ids: set[str],
        read_authority: WorldModelReadAuthority,
        investigation_trace: BoundedInvestigationTrace | None,
    ) -> None:
        _text(selector.selector_id, "entity selector ID")
        if (
            not selector.need_ids
            or len(set(selector.need_ids)) != len(selector.need_ids)
            or any(item not in need_ids for item in selector.need_ids)
            or selector.snapshot_id not in read_authority.snapshot_ids
            or type(selector.max_candidates) is not int
            or selector.max_candidates < 1
            or selector.max_candidates
            > question.resource_limits.max_entity_candidates
        ):
            raise _invalid(
                "WORLD_MODEL_ENTITY_SELECTOR_INVALID",
                "entity selector has an invalid Need, Snapshot, or budget",
            )
        if selector.origin is EntitySelectorOrigin.MENTION:
            if (
                selector.mention is None
                or selector.entity_root_id is not None
                or selector.entity_state_id is not None
                or selector.search_terms
                or selector.source_result_id is not None
                or selector.source_result_digest is not None
            ):
                raise _invalid(
                    "WORLD_MODEL_ENTITY_SELECTOR_SHAPE_INVALID",
                    "mention selector cannot carry a model-generated EntityRef",
                )
            _text(selector.mention, "entity mention")
            for qualifier in (selector.canonical_ga, selector.canonical_gav):
                if qualifier is not None and qualifier not in question.original_question:
                    raise _invalid(
                        "WORLD_MODEL_UNAUTHORIZED_ENTITY_QUALIFIER",
                        "an exact entity qualifier must be present in the original caller question",
                    )
            return
        if selector.origin is EntitySelectorOrigin.IMPLEMENTATION_FEATURES:
            if (
                selector.mention is not None
                or selector.entity_type is not None
                or selector.canonical_ga is not None
                or selector.canonical_gav is not None
                or selector.entity_root_id is not None
                or selector.entity_state_id is not None
                or selector.source_result_id is not None
                or selector.source_result_digest is not None
                or not 1 <= len(selector.search_terms) <= 12
                or any(
                    not isinstance(item, str)
                    or not item
                    or item != item.strip()
                    for item in selector.search_terms
                )
                or selector.max_candidates > 20
            ):
                raise _invalid(
                    "WORLD_MODEL_IMPLEMENTATION_SELECTOR_INVALID",
                    "implementation feature selector has an invalid closed shape",
                )
            return
        if selector.origin is EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT:
            if (
                investigation_trace is None
                or selector.mention is not None
                or selector.entity_type is not None
                or selector.canonical_ga is not None
                or selector.canonical_gav is not None
                or selector.entity_root_id is None
                or selector.entity_state_id is None
                or selector.search_terms
                or selector.source_result_id is None
                or selector.source_result_digest is None
                or selector.max_candidates != 1
            ):
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_SELECTOR_INVALID",
                    "investigation selector has an invalid closed provenance shape",
                )
            source_result = investigation_trace.result(
                selector.source_result_id,
                selector.source_result_digest,
            )
            argument = StructureEntityArgument.from_result_member(
                source_result,
                entity_root_id=selector.entity_root_id,
                entity_state_id=selector.entity_state_id,
            )
            if argument.snapshot_id != selector.snapshot_id:
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_SELECTOR_SNAPSHOT_MISMATCH",
                    "investigation selector binds an Entity from another Snapshot",
                )
            return
        if selector.origin is not EntitySelectorOrigin.CALLER_EXACT_REF:
            raise _invalid(
                "WORLD_MODEL_ENTITY_SELECTOR_ORIGIN_INVALID",
                "entity selector origin is unsupported",
            )
        if (
            selector.mention is not None
            or selector.entity_type is not None
            or selector.canonical_ga is not None
            or selector.canonical_gav is not None
            or selector.entity_root_id is None
            or selector.entity_state_id is None
            or selector.search_terms
            or selector.source_result_id is not None
            or selector.source_result_digest is not None
        ):
            raise _invalid(
                "WORLD_MODEL_CALLER_ENTITY_REF_SHAPE_INVALID",
                "caller exact selector must contain only an exact Root/State pair",
            )
        if not any(
            item.snapshot_id == selector.snapshot_id
            and item.entity_root_id == selector.entity_root_id
            and item.entity_state_id == selector.entity_state_id
            for item in question.explicit_entity_refs
        ):
            raise _invalid(
                "WORLD_MODEL_FORGED_ENTITY_REF",
                "planner supplied an EntityRef absent from the original caller request",
            )

    @staticmethod
    def _validate_step_shape(
        step: WorldModelQueryStepProposal,
        selector_ids: set[str],
    ) -> None:
        required_arguments, required_parameters, optional_parameters = (
            _QUERY_STEP_SCHEMAS[step.operation]
        )
        if set(step.arguments) != required_arguments:
            raise _invalid(
                "WORLD_MODEL_QUERY_ARGUMENT_SCHEMA_INVALID",
                "query step arguments do not match the registered operation",
            )
        if (
            not required_parameters.issubset(step.parameters)
            or set(step.parameters) - required_parameters - optional_parameters
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PARAMETER_SCHEMA_INVALID",
                "query step parameters do not match the registered operation",
            )
        if any(
            not isinstance(value, str) or value not in selector_ids
            for value in step.arguments.values()
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_TYPED_ARGUMENT_FORGED",
                "query step must reference a validated selector, never a direct EntityRef",
            )

    @staticmethod
    def _validate_step_parameters(
        question: WorldModelQuestion,
        step: WorldModelQueryStepProposal,
        read_authority: WorldModelReadAuthority,
    ) -> None:
        parameters = step.parameters
        predicate = parameters.get("predicate")
        if predicate is not None:
            try:
                RelationPredicate(predicate)
            except (TypeError, ValueError) as exc:
                raise _invalid(
                    "WORLD_MODEL_QUERY_PREDICATE_INVALID",
                    "query step contains an unsupported relation predicate",
                ) from exc
        if step.operation is StructureViewOperation.DIRECT_NEIGHBORHOOD:
            direction = parameters.get(
                "direction", NeighborhoodDirection.BOTH.value
            )
            try:
                NeighborhoodDirection(direction)
            except (TypeError, ValueError) as exc:
                raise _invalid(
                    "WORLD_MODEL_QUERY_DIRECTION_INVALID",
                    "query step contains an unsupported neighborhood direction",
                ) from exc
        limits = (
            ("max_depth", question.resource_limits.max_path_depth),
            ("max_paths", question.resource_limits.max_paths),
            (
                "max_expansions",
                question.resource_limits.max_path_expansions,
            ),
        )
        for name, maximum in limits:
            if name not in parameters:
                continue
            value = parameters[name]
            if type(value) is not int or not 1 <= value <= maximum:
                raise _invalid(
                    "WORLD_MODEL_QUERY_BUDGET_INVALID",
                    f"query {name} must be an integer from 1 through {maximum}",
                )
        if step.operation is StructureViewOperation.ORDERED_SNAPSHOT_DIFF:
            base = _stable_parameter(parameters, "base_snapshot_id")
            target = _stable_parameter(parameters, "target_snapshot_id")
            if not _adjacent_order(read_authority.snapshot_ids, base, target):
                raise _invalid(
                    "WORLD_MODEL_QUERY_DIFF_ORDER_INVALID",
                    "Snapshot diff must preserve adjacent caller-declared Read Set order",
                )
        if step.operation is StructureViewOperation.IMPLEMENTATION_CANDIDATES:
            snapshot_id = _stable_parameter(parameters, "snapshot_id")
            search_terms = parameters.get("search_terms")
            limit = parameters.get("limit")
            if snapshot_id not in read_authority.snapshot_ids:
                raise _invalid(
                    "WORLD_MODEL_QUERY_SNAPSHOT_OUTSIDE_READ_SET",
                    "implementation search Snapshot is outside the exact Read Set",
                )
            if (
                not isinstance(search_terms, tuple)
                or not 1 <= len(search_terms) <= 12
                or any(
                    not isinstance(item, str)
                    or not item
                    or item != item.strip()
                    for item in search_terms
                )
                or type(limit) is not int
                or not 1 <= limit <= 20
            ):
                raise _invalid(
                    "WORLD_MODEL_IMPLEMENTATION_SEARCH_INVALID",
                    "implementation search terms or limit are outside the closed contract",
                )

    def _resolve_selector(
        self,
        question: WorldModelQuestion,
        selector: WorldModelEntitySelectorProposal,
        *,
        investigation_trace: BoundedInvestigationTrace | None = None,
    ) -> WorldModelEntityResolution:
        if selector.origin is EntitySelectorOrigin.MENTION:
            result = self._view.entity_candidates(
                snapshot_id=selector.snapshot_id,
                mention=selector.mention,
                entity_type=selector.entity_type,
                canonical_ga=selector.canonical_ga,
                canonical_gav=selector.canonical_gav,
                max_candidates=selector.max_candidates,
            )
            status = EntityResolutionStatus(result.payload["resolution_status"])
            argument = (
                StructureEntityArgument.from_unique_candidate(result)
                if status is EntityResolutionStatus.UNIQUE
                else None
            )
            limitations = result.limitations
            candidate_result = result
        elif selector.origin is EntitySelectorOrigin.IMPLEMENTATION_FEATURES:
            result = self._view.implementation_candidates(
                snapshot_id=selector.snapshot_id,
                search_terms=selector.search_terms,
                limit=selector.max_candidates,
            )
            status = _implementation_resolution_status(result)
            argument = (
                StructureEntityArgument.from_unique_candidate(result)
                if status is EntityResolutionStatus.UNIQUE
                else None
            )
            limitations = _implementation_resolution_limitations(result, status)
            candidate_result = result
        elif selector.origin is EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT:
            if (
                investigation_trace is None
                or selector.source_result_id is None
                or selector.source_result_digest is None
                or selector.entity_root_id is None
                or selector.entity_state_id is None
            ):
                raise _invalid(
                    "WORLD_MODEL_INVESTIGATION_SELECTOR_INVALID",
                    "investigation selector lacks its sealed trace provenance",
                )
            candidate_result = investigation_trace.result(
                selector.source_result_id,
                selector.source_result_digest,
            )
            argument = StructureEntityArgument.from_result_member(
                candidate_result,
                entity_root_id=selector.entity_root_id,
                entity_state_id=selector.entity_state_id,
            )
            status = EntityResolutionStatus.UNIQUE
            limitations = ()
        else:
            assert selector.entity_root_id is not None
            assert selector.entity_state_id is not None
            argument = StructureEntityArgument.caller_exact_ref(
                service=self._view,
                snapshot_id=selector.snapshot_id,
                entity_root_id=selector.entity_root_id,
                entity_state_id=selector.entity_state_id,
            )
            # Force exact membership/provenance validation at resolution time.
            self._view.direct_neighborhood(
                entity=argument,
                direction=NeighborhoodDirection.BOTH,
            )
            status = EntityResolutionStatus.UNIQUE
            limitations = ()
            candidate_result = None
        core = {
            "selector": selector.canonical_value(),
            "status": status.value,
            "candidate_result": (
                candidate_result.canonical_value()
                if candidate_result is not None
                else None
            ),
            "argument": _entity_argument_value(argument),
            "limitations": limitations,
            "read_authority_digest": self._read_authority.digest.value,
        }
        identity = digest_of(["WORLD_MODEL_ENTITY_RESOLUTION_ID@1", core])
        resolution_id = _stable("world_model_resolution", identity)
        return WorldModelEntityResolution(
            resolution_id=resolution_id,
            selector=selector,
            status=status,
            candidate_result=candidate_result,
            argument=argument,
            limitations=limitations,
            read_authority_digest=self._read_authority.digest,
            digest=digest_of(
                [
                    "WORLD_MODEL_ENTITY_RESOLUTION@1",
                    {"resolution_id": resolution_id.value, **core},
                ]
            ),
        )

    def _verify_resolution_for_question(
        self,
        question: WorldModelQuestion,
        resolution: WorldModelEntityResolution,
        investigation_trace: BoundedInvestigationTrace | None = None,
    ) -> None:
        replay = self._resolve_selector(
            question,
            resolution.selector,
            investigation_trace=investigation_trace,
        )
        if replay != resolution:
            raise _invalid(
                "WORLD_MODEL_ENTITY_RESOLUTION_REPLAY_MISMATCH",
                "stored Entity resolution differs from exact Bundle replay",
            )

    @staticmethod
    def _seal_query_step(
        proposal: WorldModelQueryStepProposal,
        resolutions: Mapping[str, WorldModelEntityResolution],
    ) -> WorldModelQueryStep:
        blockers = tuple(
            resolutions[item]
            for item in proposal.arguments.values()
            if resolutions[item].status is not EntityResolutionStatus.UNIQUE
        )
        state = QueryStepState.BLOCKED if blockers else QueryStepState.READY
        limitation = (
            "ENTITY_RESOLUTION_NOT_UNIQUE" if blockers else None
        )
        core = {
            **proposal.canonical_value(),
            "state": state.value,
            "limitation_code": limitation,
        }
        return WorldModelQueryStep(
            step_id=proposal.step_id,
            need_ids=proposal.need_ids,
            operation=proposal.operation,
            arguments=proposal.arguments,
            parameters=proposal.parameters,
            constraint_ids=proposal.constraint_ids,
            state=state,
            limitation_code=limitation,
            digest=digest_of(["WORLD_MODEL_QUERY_STEP@1", core]),
        )

    def _verify_plan_authority(
        self,
        plan: WorldModelQueryPlan,
        resolution_set: WorldModelCandidateResolutionSet,
    ) -> None:
        plan.planning_invocation.require_valid()
        resolution_set.planning_invocation.require_valid()
        question = self._question(plan.question_id)
        requirement = self._store.get(
            WorldModelRequirementRevision, plan.requirement_id
        )
        self._verify_requirement(requirement, question)
        if (
            plan.requirement_digest != requirement.digest
            or plan.resolution_set_digest != resolution_set.digest
            or resolution_set.question_id != question.question_id
            or resolution_set.requirement_id != requirement.requirement_id
            or resolution_set.requirement_digest != requirement.digest
            or plan.read_authority != self._read_authority
            or resolution_set.read_authority != self._read_authority
            or plan.capability_registry_digest
            != WORLD_MODEL_QUERY_CAPABILITY_REGISTRY_DIGEST
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_AUTHORITY_MISMATCH",
                "Query Plan authority chain is inconsistent",
            )
        for resolution in resolution_set.resolutions:
            self._verify_resolution_for_question(
                question,
                resolution,
                plan.investigation_trace,
            )
        resolution_core = {
            "question_id": question.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "requirement_digest": requirement.digest.value,
            "proposal_digest": resolution_set.proposal_digest.value,
            "planning_invocation": (
                resolution_set.planning_invocation.canonical_value()
            ),
            "resolutions": tuple(
                item.canonical_value() for item in resolution_set.resolutions
            ),
            "read_authority": self._read_authority.canonical_value(),
        }
        expected_resolution_id = _stable(
            "world_model_resolution_set",
            digest_of(["WORLD_MODEL_RESOLUTION_SET_ID@1", resolution_core]),
        )
        expected_resolution_digest = digest_of(
            [
                "WORLD_MODEL_RESOLUTION_SET@1",
                {
                    "resolution_set_id": expected_resolution_id.value,
                    **resolution_core,
                },
            ]
        )
        if (
            resolution_set.resolution_set_id != expected_resolution_id
            or resolution_set.digest != expected_resolution_digest
            or resolution_set.planning_invocation != plan.planning_invocation
        ):
            raise _invalid(
                "WORLD_MODEL_RESOLUTION_SET_DIGEST_MISMATCH",
                "Entity resolution authority set is not canonical",
            )
        by_selector = {
            item.selector.selector_id: item for item in resolution_set.resolutions
        }
        expected_steps = tuple(
            self._seal_query_step(
                WorldModelQueryStepProposal(
                    step_id=item.step_id,
                    need_ids=item.need_ids,
                    operation=item.operation,
                    arguments=item.arguments,
                    parameters=item.parameters,
                    constraint_ids=item.constraint_ids,
                ),
                by_selector,
            )
            for item in plan.steps
        )
        if expected_steps != plan.steps:
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_STEP_MISMATCH",
                "Query Plan steps do not match exact candidate authority",
            )
        if plan.investigation_trace is not None:
            validate_bounded_investigation_trace(
                plan.investigation_trace,
                view=self._view,
                question_digest=question.digest,
            )
        reconstructed_proposal = WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=self._read_authority.read_set_digest,
            ordered_bundle_digest=self._read_authority.ordered_bundle_digest,
            selectors=tuple(
                item.selector for item in resolution_set.resolutions
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
                for item in plan.steps
            ),
            explicit_gaps=plan.explicit_gaps,
            invocation_id=plan.planning_invocation.invocation_id,
            invocation_digest=plan.planning_invocation.digest,
            investigation_trace=plan.investigation_trace,
        )
        if self._normalize_plan_proposal(reconstructed_proposal) != (
            reconstructed_proposal
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_DEFAULTS_UNSEALED",
                "Query Plan does not seal all effective operation defaults",
            )
        self._validate_plan_proposal(
            question,
            requirement,
            reconstructed_proposal,
            self._read_authority,
        )
        if (
            resolution_set.proposal_digest
            != _query_plan_proposal_digest(reconstructed_proposal)
            or plan.planning_invocation.stage is not OfflineStage.QUERY_PLANNING
            or plan.planning_invocation.question_id != question.question_id
            or plan.planning_invocation.question_digest != question.digest
            or plan.planning_invocation.input_digest != requirement.digest
        ):
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_PROPOSAL_MISMATCH",
                "validated Plan differs from its exact planner proposal",
            )
        core = {
            key: value
            for key, value in plan.canonical_value().items()
            if key not in {"plan_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_QUERY_PLAN_ID@1", core])
        expected_id = _stable("world_model_query_plan", identity)
        expected_digest = digest_of(
            ["WORLD_MODEL_QUERY_PLAN@1", {"plan_id": expected_id.value, **core}]
        )
        if plan.plan_id != expected_id or plan.digest != expected_digest:
            raise _invalid(
                "WORLD_MODEL_QUERY_PLAN_DIGEST_MISMATCH",
                "Query Plan is not canonical",
            )

    def _execute_step(
        self,
        step: WorldModelQueryStep,
        resolutions: Mapping[str, WorldModelEntityResolution],
    ) -> WorldModelQueryStepResult:
        if step.state is not QueryStepState.READY:
            raise _invalid(
                "WORLD_MODEL_QUERY_STEP_BLOCKED",
                "blocked Query step cannot be executed",
            )
        arguments = {
            key: resolutions[value].argument
            for key, value in step.arguments.items()
        }
        if any(value is None for value in arguments.values()):
            raise _invalid(
                "WORLD_MODEL_QUERY_ARGUMENT_UNRESOLVED",
                "Query step has no unique typed Entity argument",
            )
        parameters = dict(step.parameters)
        if step.operation is StructureViewOperation.CHILD_MODULE_INVENTORY:
            result = self._view.child_module_inventory(system=arguments["system"])
        elif step.operation is StructureViewOperation.DECLARED_METHOD_INVENTORY:
            result = self._view.declared_method_inventory(
                java_type=arguments["java_type"]
            )
        elif step.operation is StructureViewOperation.IMPLEMENTATION_CANDIDATES:
            result = self._view.implementation_candidates(
                snapshot_id=_stable_parameter(parameters, "snapshot_id"),
                search_terms=parameters["search_terms"],
                limit=parameters["limit"],
            )
        elif step.operation is StructureViewOperation.METHOD_IMPLEMENTATION:
            result = self._view.method_implementation(method=arguments["method"])
        elif step.operation is StructureViewOperation.DIRECT_NEIGHBORHOOD:
            result = self._view.direct_neighborhood(
                entity=arguments["entity"],
                direction=parameters.get("direction", NeighborhoodDirection.BOTH.value),
                predicate=parameters.get("predicate"),
            )
        elif step.operation is StructureViewOperation.PATH_EXISTS:
            result = self._view.path_exists(
                source=arguments["source"],
                target=arguments["target"],
                predicate=parameters.get(
                    "predicate", RelationPredicate.DEPENDS_ON.value
                ),
                max_depth=_positive_int(parameters.get("max_depth", 64), "max depth"),
                max_expansions=_positive_int(
                    parameters.get("max_expansions", 100_000),
                    "max expansions",
                ),
            )
        elif step.operation is StructureViewOperation.ALL_SIMPLE_PATHS:
            result = self._view.all_simple_paths(
                source=arguments["source"],
                target=arguments["target"],
                predicate=parameters.get(
                    "predicate", RelationPredicate.DEPENDS_ON.value
                ),
                max_depth=_positive_int(parameters.get("max_depth", 64), "max depth"),
                max_paths=_positive_int(parameters.get("max_paths", 1000), "max paths"),
                max_expansions=_positive_int(
                    parameters.get("max_expansions", 100_000),
                    "max expansions",
                ),
            )
        elif step.operation is StructureViewOperation.ORDERED_SNAPSHOT_DIFF:
            base = _stable_parameter(parameters, "base_snapshot_id")
            target = _stable_parameter(parameters, "target_snapshot_id")
            if not _adjacent_order(self._read_authority.snapshot_ids, base, target):
                raise _invalid(
                    "WORLD_MODEL_QUERY_DIFF_ORDER_INVALID",
                    "Snapshot diff reverses or leaves caller-declared order",
                )
            result = self._view.ordered_snapshot_diff(
                base_snapshot_id=base,
                target_snapshot_id=target,
            )
        else:  # pragma: no cover - sealed registry prevents this branch
            raise _invalid(
                "WORLD_MODEL_QUERY_OPERATION_UNREGISTERED",
                "Query operation is not registered",
            )
        result.require_valid()
        core = {
            "step_id": step.step_id,
            "step_digest": step.digest.value,
            "view_result": result.canonical_value(),
        }
        identity = digest_of(["WORLD_MODEL_QUERY_STEP_RESULT_ID@1", core])
        step_result_id = _stable("world_model_step_result", identity)
        return WorldModelQueryStepResult(
            step_result_id=step_result_id,
            step_id=step.step_id,
            step_digest=step.digest,
            view_result=result,
            digest=digest_of(
                [
                    "WORLD_MODEL_QUERY_STEP_RESULT@1",
                    {"step_result_id": step_result_id.value, **core},
                ]
            ),
        )

    @staticmethod
    def _assess_need(
        need: WorldModelNeed,
        *,
        plan: WorldModelQueryPlan,
        results_by_step: Mapping[str, WorldModelQueryStepResult],
        explicit_gap: WorldModelGapProposal | None,
    ) -> WorldModelNeedAssessment:
        relevant_steps = tuple(
            item for item in plan.steps if need.need_id in item.need_ids
        )
        implementation_gap_results = tuple(
            results_by_step[item.step_id]
            for item in relevant_steps
            if item.state is QueryStepState.READY
            and item.step_id in results_by_step
            and item.operation is StructureViewOperation.IMPLEMENTATION_CANDIDATES
            and results_by_step[item.step_id].view_result.payload.get(
                "query_status"
            )
            == "KNOWLEDGE_GAP"
        )
        implementation_candidate_results = tuple(
            results_by_step[item.step_id]
            for item in relevant_steps
            if item.state is QueryStepState.READY
            and item.step_id in results_by_step
            and item.operation
            is StructureViewOperation.IMPLEMENTATION_CANDIDATES
        )
        implementation_method_results = tuple(
            results_by_step[item.step_id]
            for item in relevant_steps
            if item.state is QueryStepState.READY
            and item.step_id in results_by_step
            and item.operation is StructureViewOperation.METHOD_IMPLEMENTATION
        )
        trace = plan.investigation_trace
        if explicit_gap is not None:
            outcome = WorldModelNeedOutcome.KNOWLEDGE_GAP
            step_results: tuple[WorldModelQueryStepResult, ...] = ()
            gap_code = explicit_gap.reason_code.value
            gap_detail = explicit_gap.detail
            limitations: tuple[str, ...] = ()
        elif (
            trace is not None
            and trace.terminal_status is InvestigationTerminalStatus.LIMITATION
        ):
            outcome = WorldModelNeedOutcome.LIMITATION
            step_results = ()
            gap_code = None
            gap_detail = None
            limitations = (trace.terminal_reason,)
        elif (
            implementation_gap_results
            and len(implementation_gap_results)
            == len(implementation_candidate_results)
            and not implementation_method_results
        ):
            step_results = ()
            if trace is not None and trace.completeness.bounded_absence_allowed:
                outcome = WorldModelNeedOutcome.KNOWLEDGE_GAP
                gap_code = "BOUNDED_ABSENCE"
                gap_detail = (
                    "The exact query closure, representation Coverage, and "
                    "pre-question business-discovery Oracle jointly prove no "
                    "matching implementation in the bounded Snapshot."
                )
                limitations = ()
            elif trace is not None:
                outcome = WorldModelNeedOutcome.LIMITATION
                gap_code = None
                gap_detail = None
                limitations = trace.completeness.missing_limitation_codes
            else:
                outcome = WorldModelNeedOutcome.KNOWLEDGE_GAP
                gap_code = "IMPLEMENTATION_CANDIDATES_ZERO"
                gap_detail = (
                    "The exact formal feature index contains no implementation "
                    "candidate for the validated search terms."
                )
                limitations = ()
        elif any(item.state is QueryStepState.BLOCKED for item in relevant_steps):
            outcome = WorldModelNeedOutcome.LIMITATION
            step_results = tuple(
                results_by_step[item.step_id]
                for item in relevant_steps
                if item.state is QueryStepState.READY
            )
            gap_code = None
            gap_detail = None
            limitations = tuple(
                sorted(
                    {
                        item.limitation_code
                        for item in relevant_steps
                        if item.limitation_code is not None
                    }
                )
            )
        else:
            step_results = tuple(
                results_by_step[item.step_id] for item in relevant_steps
            )
            incomplete = tuple(
                item
                for item in step_results
                if item.view_result.completeness
                is not StructureViewCompleteness.COMPLETE
                or item.view_result.truncated
            )
            if incomplete:
                outcome = WorldModelNeedOutcome.LIMITATION
                gap_code = None
                gap_detail = None
                limitations = tuple(
                    sorted(
                        {
                            limitation
                            for item in incomplete
                            for limitation in item.view_result.limitations
                        }
                    )
                )
                if not limitations:
                    limitations = ("QUERY_RESULT_INCOMPLETE",)
            else:
                negative_results = tuple(
                    item
                    for item in step_results
                    if _is_negative_result(item.view_result)
                )
                if any(
                    not _negative_supported(item.view_result)
                    for item in negative_results
                ):
                    outcome = WorldModelNeedOutcome.LIMITATION
                    gap_code = None
                    gap_detail = None
                    limitations = tuple(
                        sorted(
                            {
                                limitation
                                for item in negative_results
                                for limitation in item.view_result.limitations
                            }
                        )
                    )
                    if not limitations:
                        limitations = ("NEGATIVE_RESULT_NOT_SUPPORTED",)
                else:
                    outcome = (
                        WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE
                        if negative_results
                        else WorldModelNeedOutcome.SATISFIED
                    )
                    gap_code = None
                    gap_detail = None
                    limitations = ()
        support_digests = tuple(
            sorted(
                {
                    support.digest
                    for item in step_results
                    for support in item.view_result.support_map
                },
                key=lambda item: item.value,
            )
        )
        core = {
            "need_id": need.need_id,
            "outcome": outcome.value,
            "step_result_ids": tuple(
                item.step_result_id.value for item in step_results
            ),
            "view_result_ids": tuple(
                item.view_result.result_id.value for item in step_results
            ),
            "support_digests": tuple(item.value for item in support_digests),
            "gap_code": gap_code,
            "gap_detail": gap_detail,
            "limitations": limitations,
        }
        return WorldModelNeedAssessment(
            need_id=need.need_id,
            outcome=outcome,
            step_result_ids=tuple(item.step_result_id for item in step_results),
            view_result_ids=tuple(
                item.view_result.result_id for item in step_results
            ),
            support_digests=support_digests,
            gap_code=gap_code,
            gap_detail=gap_detail,
            limitations=limitations,
            digest=digest_of(["WORLD_MODEL_NEED_ASSESSMENT@1", core]),
        )

    @staticmethod
    def _assess_joint(
        constraint: WorldModelJointConstraint,
        *,
        needs: Mapping[str, WorldModelNeedAssessment],
        plan: WorldModelQueryPlan,
        results_by_step: Mapping[str, WorldModelQueryStepResult],
    ) -> WorldModelJointAssessment:
        relevant_steps = tuple(
            item
            for item in plan.steps
            if constraint.constraint_id in item.constraint_ids
        )
        step_results = tuple(
            results_by_step[item.step_id]
            for item in relevant_steps
            if item.state is QueryStepState.READY
            and item.step_id in results_by_step
        )
        needs_satisfied = all(
            needs[item].outcome
            in {
                WorldModelNeedOutcome.SATISFIED,
                WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE,
            }
            for item in constraint.need_ids
        )
        results_complete = (
            len(step_results) == len(relevant_steps)
            and all(
                item.view_result.completeness
                is StructureViewCompleteness.COMPLETE
                and not item.view_result.truncated
                for item in step_results
            )
        )
        satisfied = needs_satisfied and results_complete
        finding = (
            None
            if satisfied
            else "one or more constrained Needs or proof Results are incomplete"
        )
        support_digests = tuple(
            sorted(
                {
                    support.digest
                    for result in step_results
                    for support in result.view_result.support_map
                },
                key=lambda item: item.value,
            )
        )
        core = {
            "constraint_id": constraint.constraint_id,
            "satisfied": satisfied,
            "need_ids": constraint.need_ids,
            "step_result_ids": tuple(
                item.step_result_id.value for item in step_results
            ),
            "view_result_ids": tuple(
                item.view_result.result_id.value for item in step_results
            ),
            "support_digests": tuple(
                item.value for item in support_digests
            ),
            "finding": finding,
        }
        return WorldModelJointAssessment(
            constraint_id=constraint.constraint_id,
            satisfied=satisfied,
            need_ids=constraint.need_ids,
            step_result_ids=tuple(
                item.step_result_id for item in step_results
            ),
            view_result_ids=tuple(
                item.view_result.result_id for item in step_results
            ),
            support_digests=support_digests,
            finding=finding,
            digest=digest_of(["WORLD_MODEL_JOINT_ASSESSMENT@1", core]),
        )


class WorldModelResponseControlService:
    """Response owner for sealed Draft, independent Review, Auth, and Delivery."""

    def __init__(
        self,
        store: InMemoryWorldModelAuthorityStore,
        answering: WorldModelAnsweringService,
    ) -> None:
        self._store = store
        self._answering = answering

    def seal_draft(
        self,
        *,
        assessment_id: StableId,
        generator: WorldModelDraftGenerator,
    ) -> WorldModelAnswerDraft:
        assessment = self._store.get(WorldModelAssessment, assessment_id)
        (
            question,
            requirement,
            plan,
            result_set,
            _,
        ) = self._query_chain(assessment)
        self._answering.verify_query_result_set(result_set.result_set_id)
        input_digest = digest_of(
            [
                "WORLD_MODEL_DRAFT_INPUT@1",
                question.digest.value,
                requirement.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
            ]
        )
        invocation = _issue_strategy_invocation(
            stage=OfflineStage.ANSWER_DRAFTING,
            question=question,
            input_digest=input_digest,
            strategy=generator,
        )
        proposal = generator.draft(
            question=question,
            requirement=requirement,
            plan=plan,
            result_set=result_set,
            assessment=assessment,
            invocation=invocation,
        )
        if not isinstance(proposal, WorldModelDraftProposal):
            raise _invalid(
                "WORLD_MODEL_DRAFT_PROPOSAL_INVALID",
                "draft generator returned an invalid typed proposal",
            )
        _require_invocation(proposal, invocation, "answer drafting")
        if (
            proposal.assessment_id != assessment.assessment_id
            or proposal.assessment_digest != assessment.digest
        ):
            raise _invalid(
                "WORLD_MODEL_DRAFT_ASSESSMENT_MISMATCH",
                "Draft proposal binds another Need Assessment",
            )
        claims = self._seal_claims(
            proposal.claims,
            requirement=requirement,
            result_set=result_set,
            assessment=assessment,
        )
        body = "\n".join(item.text for item in claims)
        if len(body) > question.resource_limits.max_answer_body_chars:
            raise _invalid(
                "WORLD_MODEL_ANSWER_BODY_SIZE_LIMIT",
                "Answer Draft exceeds the Question's fixed body limit",
            )
        body_digest = digest_of(body)
        core = {
            "question_id": question.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "plan_id": plan.plan_id.value,
            "result_set_id": result_set.result_set_id.value,
            "assessment_id": assessment.assessment_id.value,
            "claims": tuple(item.canonical_value() for item in claims),
            "body": body,
            "body_digest": body_digest.value,
            "generation_invocation": invocation.canonical_value(),
            "read_authority": question.read_authority.canonical_value(),
        }
        identity = digest_of(["WORLD_MODEL_ANSWER_DRAFT_ID@1", core])
        draft_id = _stable("world_model_draft", identity)
        return self._store.save(
            WorldModelAnswerDraft(
                draft_id=draft_id,
                question_id=question.question_id,
                requirement_id=requirement.requirement_id,
                plan_id=plan.plan_id,
                result_set_id=result_set.result_set_id,
                assessment_id=assessment.assessment_id,
                claims=claims,
                body=body,
                body_digest=body_digest,
                generation_invocation=invocation,
                read_authority=question.read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_ANSWER_DRAFT@1",
                        {"draft_id": draft_id.value, **core},
                    ]
                ),
            )
        )

    def review(
        self,
        *,
        draft_id: StableId,
        reviewer: WorldModelAnswerReviewer,
    ) -> WorldModelAnswerReview:
        draft = self._store.get(WorldModelAnswerDraft, draft_id)
        assessment = self._store.get(
            WorldModelAssessment, draft.assessment_id
        )
        (
            question,
            requirement,
            plan,
            result_set,
            _,
        ) = self._query_chain(assessment)
        self._validate_draft(draft, assessment, requirement, result_set)
        self._answering.verify_query_result_set(result_set.result_set_id)
        input_digest = digest_of(
            [
                "WORLD_MODEL_REVIEW_INPUT@1",
                question.digest.value,
                requirement.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
                draft.digest.value,
            ]
        )
        invocation = _issue_strategy_invocation(
            stage=OfflineStage.ANSWER_REVIEW,
            question=question,
            input_digest=input_digest,
            strategy=reviewer,
        )
        if invocation.invocation_id == draft.generation_invocation.invocation_id:
            raise _invalid(
                "WORLD_MODEL_SELF_REVIEW",
                "generation and review must use different invocations",
            )
        proposal = reviewer.review(
            question=question,
            requirement=requirement,
            plan=plan,
            result_set=result_set,
            assessment=assessment,
            draft=draft,
            invocation=invocation,
        )
        if not isinstance(proposal, WorldModelReviewProposal):
            raise _invalid(
                "WORLD_MODEL_REVIEW_PROPOSAL_INVALID",
                "answer reviewer returned an invalid typed proposal",
            )
        if proposal.invocation_id == draft.generation_invocation.invocation_id:
            raise _invalid(
                "WORLD_MODEL_SELF_REVIEW",
                "review proposal reused the generation invocation",
            )
        _require_invocation(proposal, invocation, "answer review")
        _validate_review_dimensions(proposal.dimensions, proposal.decision)
        expected_needs = tuple(item.need_id for item in requirement.needs)
        expected_constraints = tuple(
            item.constraint_id for item in requirement.joint_constraints
        )
        expected_results = tuple(
            item.step_result_id for item in result_set.step_results
        )
        if (
            proposal.original_question_digest
            != digest_of(question.original_question)
            or proposal.draft_digest != draft.digest
            or proposal.read_set_digest != question.read_authority.read_set_digest
            or proposal.checked_need_ids != expected_needs
            or proposal.checked_constraint_ids != expected_constraints
            or proposal.checked_step_result_ids != expected_results
        ):
            raise _invalid(
                "WORLD_MODEL_REVIEW_CHECKLIST_INCOMPLETE",
                "independent Review omitted or changed required authority inputs",
            )
        if (
            proposal.decision is WorldModelReviewDecision.APPROVE
            and (proposal.finding_codes or proposal.findings)
        ):
            raise _invalid(
                "WORLD_MODEL_REVIEW_APPROVED_WITH_FINDING",
                "Review cannot approve a Draft while reporting findings",
            )
        core = {
            "question_id": question.question_id.value,
            "draft_id": draft.draft_id.value,
            "draft_digest": draft.digest.value,
            "decision": proposal.decision.value,
            "dimensions": tuple(
                item.canonical_value() for item in proposal.dimensions
            ),
            "checked_need_ids": proposal.checked_need_ids,
            "checked_constraint_ids": proposal.checked_constraint_ids,
            "checked_step_result_ids": tuple(
                item.value for item in proposal.checked_step_result_ids
            ),
            "finding_codes": proposal.finding_codes,
            "findings": proposal.findings,
            "review_invocation": invocation.canonical_value(),
            "generation_invocation_id": (
                draft.generation_invocation.invocation_id.value
            ),
            "read_authority": question.read_authority.canonical_value(),
        }
        identity = digest_of(["WORLD_MODEL_ANSWER_REVIEW_ID@1", core])
        review_id = _stable("world_model_review", identity)
        return self._store.save(
            WorldModelAnswerReview(
                review_id=review_id,
                question_id=question.question_id,
                draft_id=draft.draft_id,
                draft_digest=draft.digest,
                decision=proposal.decision,
                dimensions=proposal.dimensions,
                checked_need_ids=proposal.checked_need_ids,
                checked_constraint_ids=proposal.checked_constraint_ids,
                checked_step_result_ids=proposal.checked_step_result_ids,
                finding_codes=proposal.finding_codes,
                findings=proposal.findings,
                review_invocation=invocation,
                generation_invocation_id=(
                    draft.generation_invocation.invocation_id
                ),
                read_authority=question.read_authority,
                digest=digest_of(
                    [
                        "WORLD_MODEL_ANSWER_REVIEW@1",
                        {"review_id": review_id.value, **core},
                    ]
                ),
            )
        )

    def authorize(
        self,
        *,
        review_id: StableId,
        sink_id: str = EVALUATION_ONLY_SINK,
    ) -> WorldModelResponseAuthorization:
        review = self._store.get(WorldModelAnswerReview, review_id)
        if review.decision is not WorldModelReviewDecision.APPROVE:
            raise _invalid(
                "WORLD_MODEL_REVIEW_NOT_APPROVED",
                "only an independently approved Draft can be authorized",
            )
        (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
        ) = self._response_chain(review)
        self._validate_review(review, draft, requirement, result_set)
        self._answering.verify_query_result_set(result_set.result_set_id)
        normalized_sink = _text(sink_id, "evaluation sink ID")
        if normalized_sink != EVALUATION_ONLY_SINK:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_SINK_FORBIDDEN",
                "G3a authorization permits only the evaluation-only sink",
            )
        chain_digest = digest_of(
            [
                "WORLD_MODEL_PREAUTHORITY_CHAIN@1",
                question.digest.value,
                requirement.digest.value,
                resolutions.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
                draft.digest.value,
                review.digest.value,
            ]
        )
        core = {
            "question_id": question.question_id.value,
            "requirement_id": requirement.requirement_id.value,
            "plan_id": plan.plan_id.value,
            "result_set_id": result_set.result_set_id.value,
            "assessment_id": assessment.assessment_id.value,
            "draft_id": draft.draft_id.value,
            "draft_digest": draft.digest.value,
            "review_id": review.review_id.value,
            "review_digest": review.digest.value,
            "permission_digest": question.permission_digest.value,
            "read_authority": question.read_authority.canonical_value(),
            "chain_digest": chain_digest.value,
            "sink_id": normalized_sink,
        }
        identity = digest_of(["WORLD_MODEL_AUTHORIZATION_ID@1", core])
        authorization_id = _stable("world_model_authorization", identity)
        return self._store.save(
            WorldModelResponseAuthorization(
                authorization_id=authorization_id,
                question_id=question.question_id,
                requirement_id=requirement.requirement_id,
                plan_id=plan.plan_id,
                result_set_id=result_set.result_set_id,
                assessment_id=assessment.assessment_id,
                draft_id=draft.draft_id,
                draft_digest=draft.digest,
                review_id=review.review_id,
                review_digest=review.digest,
                permission_digest=question.permission_digest,
                read_authority=question.read_authority,
                chain_digest=chain_digest,
                sink_id=normalized_sink,
                digest=digest_of(
                    [
                        "WORLD_MODEL_AUTHORIZATION@1",
                        {"authorization_id": authorization_id.value, **core},
                    ]
                ),
            )
        )

    def deliver(
        self,
        *,
        authorization_id: StableId,
        sink: InMemoryWorldModelEvaluationSink,
    ) -> WorldModelDelivery:
        authorization = self._store.get(
            WorldModelResponseAuthorization, authorization_id
        )
        (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
            review,
        ) = self._authorized_chain(authorization)
        if type(sink) is not InMemoryWorldModelEvaluationSink:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_SINK_FORBIDDEN",
                "G3a delivery requires the closed in-memory evaluation sink",
            )
        if sink.sink_id != authorization.sink_id:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_SINK_MISMATCH",
                "delivery sink does not match exact Authorization",
            )
        projection = _evaluation_delivery_projection(
            question=question,
            requirement=requirement,
            draft=draft,
            authorization=authorization,
        )
        projection_digest = digest_of(
            ["WORLD_MODEL_EVALUATION_DELIVERY_PROJECTION@1", projection]
        )
        delivery = self._store.prepare_delivery(
            question=question,
            authorization=authorization,
            draft=draft,
            projection_digest=projection_digest,
        )
        if delivery.state is WorldModelDeliveryState.DELIVERED:
            return delivery
        if delivery.state is not WorldModelDeliveryState.PREPARED:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "world-model delivery is not dispatchable",
            )
        delivery = self._store.transition_delivery(
            delivery_id=delivery.delivery_id,
            expected_revision=delivery.revision,
            state=WorldModelDeliveryState.SENDING,
            receipt=None,
            failure_code=None,
        )
        try:
            receipt = sink.deliver(
                delivery_key=delivery.delivery_key,
                body=draft.body,
                body_digest=draft.body_digest,
                projection=projection,
                projection_digest=projection_digest,
            )
        except Exception:
            self._store.transition_delivery(
                delivery_id=delivery.delivery_id,
                expected_revision=delivery.revision,
                state=WorldModelDeliveryState.FAILED,
                receipt=None,
                failure_code="EVALUATION_SINK_FAILED",
            )
            raise
        expected_receipt = WorldModelDeliveryReceipt.create(
            receipt_id=receipt.receipt_id,
            sink_id=receipt.sink_id,
            delivery_key=receipt.delivery_key,
            body_digest=receipt.body_digest,
            projection_digest=receipt.projection_digest,
            accepted=receipt.accepted,
        )
        if (
            receipt != expected_receipt
            or receipt.sink_id != authorization.sink_id
            or receipt.delivery_key != delivery.delivery_key
            or receipt.body_digest != draft.body_digest
            or receipt.projection_digest != projection_digest
            or not receipt.accepted
        ):
            return self._store.transition_delivery(
                delivery_id=delivery.delivery_id,
                expected_revision=delivery.revision,
                state=WorldModelDeliveryState.FAILED,
                receipt=None,
                failure_code="EVALUATION_SINK_RECEIPT_INVALID",
            )
        return self._store.transition_delivery(
            delivery_id=delivery.delivery_id,
            expected_revision=delivery.revision,
            state=WorldModelDeliveryState.DELIVERED,
            receipt=receipt,
            failure_code=None,
        )

    def authority_chain(
        self,
        *,
        delivery_id: StableId,
        provider_call_count: int = 0,
        network_operation_count: int = 0,
    ) -> WorldModelAuthorityChain:
        if (
            type(provider_call_count) is not int
            or type(network_operation_count) is not int
        ):
            raise _invalid(
                "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
                "world-model execution counters must be exact integers",
            )
        delivery = self._store.get(WorldModelDelivery, delivery_id)
        if delivery.state is not WorldModelDeliveryState.DELIVERED:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_NOT_COMPLETE",
                "only a delivered evaluation result has a complete authority chain",
            )
        authorization = self._store.get(
            WorldModelResponseAuthorization, delivery.authorization_id
        )
        (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
            review,
        ) = self._authorized_chain(authorization)
        if (
            delivery.authorization_digest != authorization.digest
            or delivery.body_digest != draft.body_digest
            or delivery.sink_id != authorization.sink_id
            or delivery.receipt is None
            or delivery.projection_digest
            != digest_of(
                [
                    "WORLD_MODEL_EVALUATION_DELIVERY_PROJECTION@1",
                    _evaluation_delivery_projection(
                        question=question,
                        requirement=requirement,
                        draft=draft,
                        authorization=authorization,
                    ),
                ]
            )
        ):
            raise _invalid(
                "WORLD_MODEL_DELIVERY_AUTHORITY_MISMATCH",
                "delivered result does not match its exact Authorization",
            )
        self._validate_delivery(delivery)
        core = {
            "question": question.canonical_value(),
            "requirement": requirement.canonical_value(),
            "resolutions": resolutions.canonical_value(),
            "plan": plan.canonical_value(),
            "result_set": result_set.canonical_value(),
            "assessment": assessment.canonical_value(),
            "draft": draft.canonical_value(),
            "review": review.canonical_value(),
            "authorization": authorization.canonical_value(),
            "delivery": delivery.canonical_value(),
            "provider_call_count": provider_call_count,
            "network_operation_count": network_operation_count,
        }
        chain = WorldModelAuthorityChain(
            question=question,
            requirement=requirement,
            resolutions=resolutions,
            plan=plan,
            result_set=result_set,
            assessment=assessment,
            draft=draft,
            review=review,
            authorization=authorization,
            delivery=delivery,
            provider_call_count=provider_call_count,
            network_operation_count=network_operation_count,
            digest=digest_of(["WORLD_MODEL_AUTHORITY_CHAIN@1", core]),
        )
        chain.require_valid()
        return chain

    @staticmethod
    def _validate_delivery(delivery: WorldModelDelivery) -> None:
        prepared_core = {
            "question_id": delivery.question_id.value,
            "authorization_id": delivery.authorization_id.value,
            "authorization_digest": delivery.authorization_digest.value,
            "delivery_key": delivery.delivery_key,
            "sink_id": delivery.sink_id,
            "body_digest": delivery.body_digest.value,
            "projection_digest": delivery.projection_digest.value,
            "state": WorldModelDeliveryState.PREPARED.value,
            "receipt": None,
            "failure_code": None,
            "revision": 1,
        }
        expected_id = _stable(
            "world_model_delivery",
            digest_of(["WORLD_MODEL_DELIVERY_ID@1", prepared_core]),
        )
        current_core = {
            key: value
            for key, value in delivery.canonical_value().items()
            if key not in {"delivery_id", "digest"}
        }
        expected_digest = digest_of(["WORLD_MODEL_DELIVERY@1", current_core])
        if (
            delivery.delivery_id != expected_id
            or delivery.digest != expected_digest
            or delivery.state is not WorldModelDeliveryState.DELIVERED
            or type(delivery.revision) is not int
            or delivery.revision != 3
            or delivery.sink_id != EVALUATION_ONLY_SINK
        ):
            raise _invalid(
                "WORLD_MODEL_DELIVERY_DIGEST_MISMATCH",
                "world-model Delivery is not canonical",
            )
        if delivery.receipt is not None:
            expected_receipt = WorldModelDeliveryReceipt.create(
                receipt_id=_evaluation_receipt_id(delivery.delivery_key),
                sink_id=delivery.receipt.sink_id,
                delivery_key=delivery.receipt.delivery_key,
                body_digest=delivery.receipt.body_digest,
                projection_digest=delivery.receipt.projection_digest,
                accepted=delivery.receipt.accepted,
            )
            if (
                expected_receipt != delivery.receipt
                or delivery.state is not WorldModelDeliveryState.DELIVERED
                or not delivery.receipt.accepted
                or delivery.receipt.sink_id != delivery.sink_id
                or delivery.receipt.delivery_key != delivery.delivery_key
                or delivery.receipt.body_digest != delivery.body_digest
                or delivery.receipt.projection_digest
                != delivery.projection_digest
                or delivery.failure_code is not None
            ):
                raise _invalid(
                    "WORLD_MODEL_DELIVERY_RECEIPT_DIGEST_MISMATCH",
                    "world-model Delivery receipt does not bind the exact dispatch",
                )
        elif delivery.state is WorldModelDeliveryState.DELIVERED:
            raise _invalid(
                "WORLD_MODEL_DELIVERY_RECEIPT_MISSING",
                "delivered world-model authority requires an accepted receipt",
            )

    @staticmethod
    def _seal_claims(
        proposals: tuple[WorldModelAnswerClaimProposal, ...],
        *,
        requirement: WorldModelRequirementRevision,
        result_set: WorldModelQueryResultSet,
        assessment: WorldModelAssessment,
    ) -> tuple[WorldModelAnswerClaim, ...]:
        if not proposals or any(
            not isinstance(item, WorldModelAnswerClaimProposal)
            for item in proposals
        ) or len(proposals) > _MAX_ANSWER_CLAIMS:
            raise _invalid(
                "WORLD_MODEL_DRAFT_CLAIMS_INVALID",
                "Draft requires typed Claim proposals",
            )
        claim_ids = tuple(item.claim_id for item in proposals)
        if len(set(claim_ids)) != len(claim_ids):
            raise _invalid(
                "WORLD_MODEL_DRAFT_CLAIM_DUPLICATE",
                "Draft Claim IDs must be unique",
            )
        expected_needs = tuple(item.need_id for item in requirement.needs)
        claimed_needs = tuple(dict.fromkeys(item.need_id for item in proposals))
        if claimed_needs != expected_needs:
            raise _invalid(
                "WORLD_MODEL_DRAFT_NEED_OMITTED",
                "Draft must cover every Need exactly in Requirement order",
            )
        assessment_by_need = {item.need_id: item for item in assessment.needs}
        result_by_id = {
            item.step_result_id: item for item in result_set.step_results
        }
        sealed: list[WorldModelAnswerClaim] = []
        for proposal in proposals:
            _text(proposal.claim_id, "Claim ID")
            text = _text(proposal.text, "Claim text")
            if len(text) > _MAX_CLAIM_TEXT_CHARS:
                raise _invalid(
                    "WORLD_MODEL_CLAIM_SIZE_LIMIT",
                    "Answer Claim exceeds the fixed G3a text limit",
                )
            item = assessment_by_need.get(proposal.need_id)
            if item is None:
                raise _invalid(
                    "WORLD_MODEL_DRAFT_UNKNOWN_NEED",
                    "Draft Claim references an unknown Need",
                )
            expected_result_ids = item.step_result_ids
            if item.outcome in {
                WorldModelNeedOutcome.SATISFIED,
                WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE,
            }:
                if (
                    proposal.kind is not WorldModelClaimKind.QUERY_RESULT
                    or proposal.step_result_ids != expected_result_ids
                    or not proposal.step_result_ids
                ):
                    raise _invalid(
                        "WORLD_MODEL_DRAFT_SUPPORT_MISMATCH",
                        "satisfied Need Claim must bind all and only its issued Query Results",
                    )
                gap_code = None
                limitation_codes: tuple[str, ...] = ()
            elif item.outcome is WorldModelNeedOutcome.KNOWLEDGE_GAP:
                if (
                    proposal.kind is not WorldModelClaimKind.KNOWLEDGE_GAP
                    or proposal.step_result_ids
                ):
                    raise _invalid(
                        "WORLD_MODEL_DRAFT_GAP_MISMATCH",
                        "Knowledge Gap Claim cannot assert Query Result support",
                    )
                gap_code = item.gap_code
                limitation_codes = ()
            else:
                if (
                    proposal.kind
                    is not WorldModelClaimKind.APPLICATION_LIMITATION
                    or proposal.step_result_ids
                    or not item.limitations
                ):
                    raise _invalid(
                        "WORLD_MODEL_DRAFT_LIMITATION_MISMATCH",
                        "Application Limitation Claim must disclose the exact failed operation boundary",
                    )
                gap_code = None
                limitation_codes = item.limitations
            try:
                bound_results = tuple(
                    result_by_id[result_id]
                    for result_id in proposal.step_result_ids
                )
            except KeyError as exc:
                raise _invalid(
                    "WORLD_MODEL_DRAFT_RESULT_OUTSIDE_AUTHORITY",
                    "Draft Claim references a Result outside the issued Result Set",
                ) from exc
            view_result_ids = tuple(
                result.view_result.result_id for result in bound_results
            )
            support_digests = tuple(
                sorted(
                    {
                        support.digest
                        for result in bound_results
                        for support in result.view_result.support_map
                    },
                    key=lambda value: value.value,
                )
            )
            evidence_references = tuple(
                sorted(
                    {
                        evidence
                        for result in bound_results
                        for evidence in result.view_result.evidence_allowlist
                    },
                    key=lambda value: value.value,
                )
            )
            core = {
                "claim_id": proposal.claim_id,
                "need_id": proposal.need_id,
                "kind": proposal.kind.value,
                "text": text,
                "step_result_ids": tuple(
                    value.value for value in proposal.step_result_ids
                ),
                "view_result_ids": tuple(
                    value.value for value in view_result_ids
                ),
                "support_digests": tuple(
                    value.value for value in support_digests
                ),
                "evidence_references": tuple(
                    value.value for value in evidence_references
                ),
                "gap_code": gap_code,
                "limitation_codes": limitation_codes,
            }
            sealed.append(
                WorldModelAnswerClaim(
                    claim_id=proposal.claim_id,
                    need_id=proposal.need_id,
                    kind=proposal.kind,
                    text=text,
                    step_result_ids=proposal.step_result_ids,
                    view_result_ids=view_result_ids,
                    support_digests=support_digests,
                    evidence_references=evidence_references,
                    gap_code=gap_code,
                    limitation_codes=limitation_codes,
                    digest=digest_of(["WORLD_MODEL_ANSWER_CLAIM@1", core]),
                )
            )
        return tuple(sealed)

    def _validate_draft(
        self,
        draft: WorldModelAnswerDraft,
        assessment: WorldModelAssessment,
        requirement: WorldModelRequirementRevision,
        result_set: WorldModelQueryResultSet,
    ) -> None:
        proposals = tuple(
            WorldModelAnswerClaimProposal(
                claim_id=item.claim_id,
                need_id=item.need_id,
                kind=item.kind,
                text=item.text,
                step_result_ids=item.step_result_ids,
            )
            for item in draft.claims
        )
        expected_claims = self._seal_claims(
            proposals,
            requirement=requirement,
            result_set=result_set,
            assessment=assessment,
        )
        body = "\n".join(item.text for item in expected_claims)
        if expected_claims != draft.claims or digest_of(body) != draft.body_digest:
            raise _invalid(
                "WORLD_MODEL_DRAFT_REPLAY_MISMATCH",
                "sealed Draft differs from exact Result-bound reconstruction",
            )
        core = {
            key: value
            for key, value in draft.canonical_value().items()
            if key not in {"draft_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_ANSWER_DRAFT_ID@1", core])
        expected_id = _stable("world_model_draft", identity)
        expected_digest = digest_of(
            ["WORLD_MODEL_ANSWER_DRAFT@1", {"draft_id": expected_id.value, **core}]
        )
        if (
            draft.draft_id != expected_id
            or draft.digest != expected_digest
            or draft.body != body
        ):
            raise _invalid(
                "WORLD_MODEL_DRAFT_DIGEST_MISMATCH",
                "sealed Draft is not canonical",
            )

    @staticmethod
    def _validate_review(
        review: WorldModelAnswerReview,
        draft: WorldModelAnswerDraft,
        requirement: WorldModelRequirementRevision,
        result_set: WorldModelQueryResultSet,
    ) -> None:
        draft.generation_invocation.require_valid()
        review.review_invocation.require_valid()
        _validate_review_dimensions(review.dimensions, review.decision)
        if (
            review.draft_id != draft.draft_id
            or review.draft_digest != draft.digest
            or review.generation_invocation_id
            != draft.generation_invocation.invocation_id
            or review.review_invocation.invocation_id
            == draft.generation_invocation.invocation_id
            or draft.generation_invocation.stage
            is not OfflineStage.ANSWER_DRAFTING
            or review.review_invocation.stage is not OfflineStage.ANSWER_REVIEW
            or draft.generation_invocation.question_id != draft.question_id
            or review.review_invocation.question_id != review.question_id
            or draft.generation_invocation.question_digest
            != review.review_invocation.question_digest
            or review.checked_need_ids
            != tuple(item.need_id for item in requirement.needs)
            or review.checked_constraint_ids
            != tuple(
                item.constraint_id for item in requirement.joint_constraints
            )
            or review.checked_step_result_ids
            != tuple(item.step_result_id for item in result_set.step_results)
            or (
                review.decision is WorldModelReviewDecision.APPROVE
                and (review.finding_codes or review.findings)
            )
        ):
            raise _invalid(
                "WORLD_MODEL_REVIEW_AUTHORITY_MISMATCH",
                "Answer Review does not cover the exact sealed chain",
            )
        core = {
            key: value
            for key, value in review.canonical_value().items()
            if key not in {"review_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_ANSWER_REVIEW_ID@1", core])
        expected_id = _stable("world_model_review", identity)
        expected_digest = digest_of(
            [
                "WORLD_MODEL_ANSWER_REVIEW@1",
                {"review_id": expected_id.value, **core},
            ]
        )
        if review.review_id != expected_id or review.digest != expected_digest:
            raise _invalid(
                "WORLD_MODEL_REVIEW_DIGEST_MISMATCH",
                "Answer Review is not canonical",
            )

    def _query_chain(
        self,
        assessment: WorldModelAssessment,
    ) -> tuple[
        WorldModelQuestion,
        WorldModelRequirementRevision,
        WorldModelQueryPlan,
        WorldModelQueryResultSet,
        WorldModelCandidateResolutionSet,
    ]:
        question = self._answering._question(assessment.question_id)
        requirement = self._store.get(
            WorldModelRequirementRevision, assessment.requirement_id
        )
        self._answering._verify_requirement(requirement, question)
        plan = self._store.get(WorldModelQueryPlan, assessment.plan_id)
        result_set = self._store.get(
            WorldModelQueryResultSet, assessment.result_set_id
        )
        resolutions = self._store.get(
            WorldModelCandidateResolutionSet, plan.resolution_set_id
        )
        self._answering.verify_query_result_set(result_set.result_set_id)
        verified_assessment = self._answering.assess(
            result_set_id=result_set.result_set_id
        )
        if verified_assessment != assessment:
            raise _invalid(
                "WORLD_MODEL_ASSESSMENT_REPLAY_MISMATCH",
                "Need Assessment differs from exact Query Result replay",
            )
        if (
            assessment.requirement_digest != requirement.digest
            or assessment.plan_digest != plan.digest
            or assessment.result_set_digest != result_set.digest
            or result_set.plan_digest != plan.digest
            or plan.requirement_digest != requirement.digest
            or plan.resolution_set_digest != resolutions.digest
            or any(
                value.read_authority != question.read_authority
                for value in (
                    requirement,
                    plan,
                    result_set,
                    assessment,
                    resolutions,
                )
            )
        ):
            raise _invalid(
                "WORLD_MODEL_ASSESSMENT_AUTHORITY_MISMATCH",
                "Need Assessment chain is inconsistent",
            )
        expected_need_ids = tuple(item.need_id for item in requirement.needs)
        expected_constraint_ids = tuple(
            item.constraint_id for item in requirement.joint_constraints
        )
        if (
            tuple(item.need_id for item in assessment.needs)
            != expected_need_ids
            or tuple(
                item.constraint_id for item in assessment.joint_constraints
            )
            != expected_constraint_ids
        ):
            raise _invalid(
                "WORLD_MODEL_ASSESSMENT_NEED_OMITTED",
                "Need Assessment omits or reorders a Requirement item",
            )
        core = {
            key: value
            for key, value in assessment.canonical_value().items()
            if key not in {"assessment_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_ASSESSMENT_ID@1", core])
        expected_id = _stable("world_model_assessment", identity)
        expected_digest = digest_of(
            [
                "WORLD_MODEL_ASSESSMENT@1",
                {"assessment_id": expected_id.value, **core},
            ]
        )
        if (
            assessment.assessment_id != expected_id
            or assessment.digest != expected_digest
        ):
            raise _invalid(
                "WORLD_MODEL_ASSESSMENT_DIGEST_MISMATCH",
                "Need Assessment is not canonical",
            )
        return question, requirement, plan, result_set, resolutions

    def _response_chain(
        self,
        review: WorldModelAnswerReview,
    ) -> tuple[
        WorldModelQuestion,
        WorldModelRequirementRevision,
        WorldModelCandidateResolutionSet,
        WorldModelQueryPlan,
        WorldModelQueryResultSet,
        WorldModelAssessment,
        WorldModelAnswerDraft,
    ]:
        draft = self._store.get(WorldModelAnswerDraft, review.draft_id)
        assessment = self._store.get(
            WorldModelAssessment, draft.assessment_id
        )
        question, requirement, plan, result_set, resolutions = self._query_chain(
            assessment
        )
        if (
            draft.question_id != question.question_id
            or draft.requirement_id != requirement.requirement_id
            or draft.plan_id != plan.plan_id
            or draft.result_set_id != result_set.result_set_id
            or draft.assessment_id != assessment.assessment_id
            or draft.read_authority != question.read_authority
            or review.question_id != question.question_id
            or review.read_authority != question.read_authority
        ):
            raise _invalid(
                "WORLD_MODEL_RESPONSE_CHAIN_MISMATCH",
                "Draft or Review binds another query authority chain",
            )
        expected_draft_input = digest_of(
            [
                "WORLD_MODEL_DRAFT_INPUT@1",
                question.digest.value,
                requirement.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
            ]
        )
        draft.generation_invocation.require_valid()
        if (
            draft.generation_invocation.stage
            is not OfflineStage.ANSWER_DRAFTING
            or draft.generation_invocation.question_id != question.question_id
            or draft.generation_invocation.question_digest != question.digest
            or draft.generation_invocation.input_digest != expected_draft_input
        ):
            raise _invalid(
                "WORLD_MODEL_DRAFT_INPUT_MISMATCH",
                "Draft invocation did not receive the exact sealed query chain",
            )
        self._validate_draft(draft, assessment, requirement, result_set)
        return (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
        )

    def _authorized_chain(
        self,
        authorization: WorldModelResponseAuthorization,
    ) -> tuple[
        WorldModelQuestion,
        WorldModelRequirementRevision,
        WorldModelCandidateResolutionSet,
        WorldModelQueryPlan,
        WorldModelQueryResultSet,
        WorldModelAssessment,
        WorldModelAnswerDraft,
        WorldModelAnswerReview,
    ]:
        review = self._store.get(
            WorldModelAnswerReview, authorization.review_id
        )
        (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
        ) = self._response_chain(review)
        self._validate_review(review, draft, requirement, result_set)
        if review.decision is not WorldModelReviewDecision.APPROVE:
            raise _invalid(
                "WORLD_MODEL_REVIEW_NOT_APPROVED",
                "Authorization chain contains a non-approved Review",
            )
        expected_review_input = digest_of(
            [
                "WORLD_MODEL_REVIEW_INPUT@1",
                question.digest.value,
                requirement.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
                draft.digest.value,
            ]
        )
        if (
            review.review_invocation.stage is not OfflineStage.ANSWER_REVIEW
            or review.review_invocation.question_id != question.question_id
            or review.review_invocation.question_digest != question.digest
            or review.review_invocation.input_digest != expected_review_input
        ):
            raise _invalid(
                "WORLD_MODEL_REVIEW_INPUT_MISMATCH",
                "Review invocation did not receive the exact sealed authority chain",
            )
        expected_chain_digest = digest_of(
            [
                "WORLD_MODEL_PREAUTHORITY_CHAIN@1",
                question.digest.value,
                requirement.digest.value,
                resolutions.digest.value,
                plan.digest.value,
                result_set.digest.value,
                assessment.digest.value,
                draft.digest.value,
                review.digest.value,
            ]
        )
        if (
            authorization.question_id != question.question_id
            or authorization.requirement_id != requirement.requirement_id
            or authorization.plan_id != plan.plan_id
            or authorization.result_set_id != result_set.result_set_id
            or authorization.assessment_id != assessment.assessment_id
            or authorization.draft_id != draft.draft_id
            or authorization.draft_digest != draft.digest
            or authorization.review_digest != review.digest
            or authorization.permission_digest != question.permission_digest
            or authorization.read_authority != question.read_authority
            or authorization.chain_digest != expected_chain_digest
            or authorization.sink_id != EVALUATION_ONLY_SINK
        ):
            raise _invalid(
                "WORLD_MODEL_AUTHORIZATION_CHAIN_MISMATCH",
                "Response Authorization does not bind the current exact chain",
            )
        core = {
            key: value
            for key, value in authorization.canonical_value().items()
            if key not in {"authorization_id", "digest"}
        }
        identity = digest_of(["WORLD_MODEL_AUTHORIZATION_ID@1", core])
        expected_id = _stable("world_model_authorization", identity)
        expected_digest = digest_of(
            [
                "WORLD_MODEL_AUTHORIZATION@1",
                {"authorization_id": expected_id.value, **core},
            ]
        )
        if (
            authorization.authorization_id != expected_id
            or authorization.digest != expected_digest
        ):
            raise _invalid(
                "WORLD_MODEL_AUTHORIZATION_DIGEST_MISMATCH",
                "Response Authorization is not canonical",
            )
        self._answering.verify_query_result_set(result_set.result_set_id)
        return (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
            review,
        )


class OfflineWorldModelAnswerService:
    """Convenience orchestrator for one complete G3a evaluation-only chain."""

    def __init__(
        self,
        *,
        answering: WorldModelAnsweringService,
        responses: WorldModelResponseControlService,
    ) -> None:
        self._answering = answering
        self._responses = responses

    def execute(
        self,
        *,
        request_ref: str,
        original_question: str,
        response_language: str,
        classification: str,
        permission_digest: Digest,
        resource_limits: WorldModelResourceLimits | None = None,
        requirement_planner: WorldModelRequirementPlanner,
        requirement_reviewer: WorldModelRequirementFidelityReviewer,
        query_planner: WorldModelQueryPlanner,
        draft_generator: WorldModelDraftGenerator,
        answer_reviewer: WorldModelAnswerReviewer,
        sink: InMemoryWorldModelEvaluationSink,
        explicit_entity_refs: Sequence[WorldModelExplicitEntityRef] = (),
    ) -> WorldModelAuthorityChain:
        question = self._answering.open_question(
            request_ref=request_ref,
            original_question=original_question,
            response_language=response_language,
            classification=classification,
            permission_digest=permission_digest,
            resource_limits=resource_limits,
            explicit_entity_refs=explicit_entity_refs,
        )
        requirement = self._answering.seal_requirement(
            question_id=question.question_id,
            planner=requirement_planner,
            fidelity_reviewer=requirement_reviewer,
        )
        plan = self._answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=query_planner,
        )
        result_set = self._answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = self._answering.assess(
            result_set_id=result_set.result_set_id
        )
        draft = self._responses.seal_draft(
            assessment_id=assessment.assessment_id,
            generator=draft_generator,
        )
        review = self._responses.review(
            draft_id=draft.draft_id,
            reviewer=answer_reviewer,
        )
        authorization = self._responses.authorize(
            review_id=review.review_id,
        )
        delivery = self._responses.deliver(
            authorization_id=authorization.authorization_id,
            sink=sink,
        )
        return self._responses.authority_chain(delivery_id=delivery.delivery_id)


def _validate_exported_authority_chain(
    chain: WorldModelAuthorityChain,
) -> None:
    """Mechanically verify every exported record without connected stores.

    Bundle replay remains the live owner's responsibility.  This verifier owns
    artifact integrity after Delivery: child IDs/digests, cross-links, review,
    authorization, receipt, and projection must all remain exact.
    """

    question = chain.question
    requirement = chain.requirement
    resolutions = chain.resolutions
    plan = chain.plan
    result_set = chain.result_set
    assessment = chain.assessment
    draft = chain.draft
    review = chain.review
    authorization = chain.authorization
    delivery = chain.delivery

    for invocation in (
        requirement.planning_invocation,
        requirement.fidelity_review_invocation,
        resolutions.planning_invocation,
        plan.planning_invocation,
        draft.generation_invocation,
        review.review_invocation,
    ):
        invocation.require_valid()
        if (
            invocation.question_id != question.question_id
            or invocation.question_digest != question.digest
        ):
            raise _invalid(
                "WORLD_MODEL_EXPORTED_INVOCATION_MISMATCH",
                "exported strategy invocation binds another Question",
            )

    _require_stable_record(
        requirement,
        id_field="requirement_id",
        stable_kind="world_model_requirement",
        id_domain="WORLD_MODEL_REQUIREMENT_ID@1",
        digest_domain="WORLD_MODEL_REQUIREMENT@1",
    )
    expected_need_ids = tuple(item.need_id for item in requirement.needs)
    expected_constraint_ids = tuple(
        item.constraint_id for item in requirement.joint_constraints
    )
    if (
        requirement.question_id != question.question_id
        or requirement.question_digest != question.digest
        or requirement.original_question != question.original_question
        or requirement.response_language != question.response_language
        or type(requirement.revision) is not int
        or requirement.revision != 1
        or requirement.planning_invocation.stage
        is not OfflineStage.REQUIREMENT_PLANNING
        or requirement.planning_invocation.input_digest != question.digest
        or requirement.fidelity_review_invocation.stage
        is not OfflineStage.REQUIREMENT_FIDELITY_REVIEW
        or requirement.fidelity_decision
        is not WorldModelReviewDecision.APPROVE
        or requirement.fidelity_accepted_need_ids != expected_need_ids
        or requirement.fidelity_accepted_constraint_ids
        != expected_constraint_ids
        or requirement.fidelity_original_question_preserved is not True
        or requirement.fidelity_all_material_questions_covered is not True
        or requirement.fidelity_findings
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_REQUIREMENT_MISMATCH",
            "exported Requirement fidelity authority is invalid",
        )
    reconstructed_requirement_proposal = WorldModelRequirementProposal(
        original_question=requirement.original_question,
        response_language=requirement.response_language,
        needs=requirement.needs,
        joint_constraints=requirement.joint_constraints,
        invocation_id=requirement.planning_invocation.invocation_id,
        invocation_digest=requirement.planning_invocation.digest,
    )
    WorldModelAnsweringService._validate_requirement_proposal(
        question,
        reconstructed_requirement_proposal,
        question.read_authority,
    )
    expected_requirement_proposal_digest = digest_of(
        [
            "WORLD_MODEL_REQUIREMENT_PROPOSAL@1",
            {
                "original_question": reconstructed_requirement_proposal.original_question,
                "response_language": reconstructed_requirement_proposal.response_language,
                "needs": tuple(
                    item.canonical_value()
                    for item in reconstructed_requirement_proposal.needs
                ),
                "joint_constraints": tuple(
                    item.canonical_value()
                    for item in reconstructed_requirement_proposal.joint_constraints
                ),
                "invocation_id": (
                    reconstructed_requirement_proposal.invocation_id.value
                ),
                "invocation_digest": (
                    reconstructed_requirement_proposal.invocation_digest.value
                ),
            },
        ]
    )
    if (
        requirement.fidelity_review_invocation.input_digest
        != expected_requirement_proposal_digest
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_REQUIREMENT_REVIEW_INPUT_MISMATCH",
            "exported Requirement review did not bind the exact proposal",
        )

    _require_stable_record(
        resolutions,
        id_field="resolution_set_id",
        stable_kind="world_model_resolution_set",
        id_domain="WORLD_MODEL_RESOLUTION_SET_ID@1",
        digest_domain="WORLD_MODEL_RESOLUTION_SET@1",
    )
    if (
        resolutions.question_id != question.question_id
        or resolutions.requirement_id != requirement.requirement_id
        or resolutions.requirement_digest != requirement.digest
        or resolutions.planning_invocation != plan.planning_invocation
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RESOLUTION_SET_MISMATCH",
            "exported candidate resolutions bind another authority",
        )
    selector_ids: list[str] = []
    snapshot_bundles = dict(
        zip(
            question.read_authority.snapshot_ids,
            question.read_authority.snapshot_bundle_digests,
            strict=True,
        )
    )
    for resolution in resolutions.resolutions:
        _require_stable_record(
            resolution,
            id_field="resolution_id",
            stable_kind="world_model_resolution",
            id_domain="WORLD_MODEL_ENTITY_RESOLUTION_ID@1",
            digest_domain="WORLD_MODEL_ENTITY_RESOLUTION@1",
        )
        selector_ids.append(resolution.selector.selector_id)
        if resolution.read_authority_digest != question.read_authority.digest:
            raise _invalid(
                "WORLD_MODEL_EXPORTED_RESOLUTION_READ_SET_MISMATCH",
                "exported Entity resolution binds another Read Set",
            )
        candidate = resolution.candidate_result
        argument = resolution.argument
        if candidate is not None:
            candidate.require_valid()
            expected_candidate_operation = (
                StructureViewOperation.ENTITY_CANDIDATES
                if resolution.selector.origin is EntitySelectorOrigin.MENTION
                else StructureViewOperation.IMPLEMENTATION_CANDIDATES
                if resolution.selector.origin
                is EntitySelectorOrigin.IMPLEMENTATION_FEATURES
                else candidate.operation
                if resolution.selector.origin
                is EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT
                else None
            )
            if (
                expected_candidate_operation is None
                or candidate.operation is not expected_candidate_operation
                or candidate.session_id
                != question.read_authority.session_id
                or candidate.session_digest
                != question.read_authority.session_digest
                or candidate.read_set_digest
                != question.read_authority.read_set_digest
                or candidate.ordered_bundle_digest
                != question.read_authority.ordered_bundle_digest
                or resolution.selector.snapshot_id not in snapshot_bundles
                or candidate.snapshot_ids
                != (resolution.selector.snapshot_id,)
                or candidate.snapshot_bundle_digests
                != (snapshot_bundles.get(resolution.selector.snapshot_id),)
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_CANDIDATE_READ_SET_MISMATCH",
                    "exported candidate Result binds another Read Set",
                )
        if argument is not None:
            argument.require_valid()
            argument_value = _entity_argument_value(argument)
            assert argument_value is not None
            argument_core = {
                key: value
                for key, value in argument_value.items()
                if key != "digest"
            }
            if argument.digest != digest_of(
                ["STRUCTURE_ENTITY_ARGUMENT@1", argument_core]
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_ENTITY_ARGUMENT_INVALID",
                    "exported typed Entity argument is not canonical",
                )
            if (
                argument.session_id != question.read_authority.session_id
                or argument.read_set_digest
                != question.read_authority.read_set_digest
                or argument.ordered_bundle_digest
                != question.read_authority.ordered_bundle_digest
                or snapshot_bundles.get(argument.snapshot_id)
                != argument.snapshot_bundle_digest
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_ENTITY_ARGUMENT_READ_SET_MISMATCH",
                    "exported typed Entity argument binds another Read Set",
                )
        if resolution.selector.origin is EntitySelectorOrigin.MENTION:
            if candidate is None:
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_CANDIDATE_PROOF_MISSING",
                    "exported mention resolution lacks its candidate Result",
                )
            try:
                candidate_status = EntityResolutionStatus(
                    candidate.payload["resolution_status"]
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_CANDIDATE_STATUS_INVALID",
                    "exported candidate Result has no valid resolution status",
                ) from exc
            expected_argument = (
                StructureEntityArgument.from_unique_candidate(candidate)
                if candidate_status is EntityResolutionStatus.UNIQUE
                else None
            )
            if (
                resolution.status is not candidate_status
                or resolution.limitations != candidate.limitations
                or argument != expected_argument
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_CANDIDATE_PROOF_MISMATCH",
                    "exported mention resolution differs from its exact candidate Result",
                )
        elif (
            resolution.selector.origin
            is EntitySelectorOrigin.IMPLEMENTATION_FEATURES
        ):
            if candidate is None:
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_CANDIDATE_PROOF_MISSING",
                    "exported implementation resolution lacks its candidate Result",
                )
            candidate_status = _implementation_resolution_status(candidate)
            expected_argument = (
                StructureEntityArgument.from_unique_candidate(candidate)
                if candidate_status is EntityResolutionStatus.UNIQUE
                else None
            )
            if (
                resolution.status is not candidate_status
                or resolution.limitations
                != _implementation_resolution_limitations(
                    candidate, candidate_status
                )
                or argument != expected_argument
                or candidate.payload.get("search_terms_original")
                != resolution.selector.search_terms
                or candidate.payload.get("limit")
                != resolution.selector.max_candidates
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_IMPLEMENTATION_CANDIDATE_MISMATCH",
                    "exported implementation resolution differs from its exact candidate Result",
                )
        elif (
            resolution.selector.origin
            is EntitySelectorOrigin.SEALED_INVESTIGATION_RESULT
        ):
            trace = plan.investigation_trace
            selector = resolution.selector
            if (
                trace is None
                or candidate is None
                or argument is None
                or selector.source_result_id is None
                or selector.source_result_digest is None
                or selector.entity_root_id is None
                or selector.entity_state_id is None
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_INVESTIGATION_PROOF_MISSING",
                    "exported investigation resolution lacks exact trace provenance",
                )
            source_result = trace.result(
                selector.source_result_id,
                selector.source_result_digest,
            )
            expected_argument = StructureEntityArgument.from_result_member(
                source_result,
                entity_root_id=selector.entity_root_id,
                entity_state_id=selector.entity_state_id,
            )
            if (
                candidate != source_result
                or argument != expected_argument
                or argument.origin
                is not StructureViewArgumentOrigin.SEALED_RESULT_MEMBER
                or resolution.status is not EntityResolutionStatus.UNIQUE
                or resolution.limitations
            ):
                raise _invalid(
                    "WORLD_MODEL_EXPORTED_INVESTIGATION_PROOF_MISMATCH",
                    "exported investigation resolution differs from its sealed Result member",
                )
        elif (
            resolution.selector.origin
            is not EntitySelectorOrigin.CALLER_EXACT_REF
            or candidate is not None
            or resolution.status is not EntityResolutionStatus.UNIQUE
            or argument is None
            or argument.origin is not StructureViewArgumentOrigin.CALLER_EXACT_REF
            or argument.snapshot_id != resolution.selector.snapshot_id
            or argument.entity_root_id != resolution.selector.entity_root_id
            or argument.entity_state_id != resolution.selector.entity_state_id
            or resolution.limitations
        ):
            raise _invalid(
                "WORLD_MODEL_EXPORTED_RESOLUTION_STATUS_MISMATCH",
                "exported exact-Ref resolution has an inconsistent shape",
            )
    if len(set(selector_ids)) != len(selector_ids):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_SELECTOR_DUPLICATE",
            "exported resolution set contains duplicate selectors",
        )

    _validate_exported_plan(chain)
    _validate_exported_result_and_assessment(chain)
    _validate_exported_response(chain)


def _validate_exported_plan(chain: WorldModelAuthorityChain) -> None:
    requirement = chain.requirement
    resolutions = chain.resolutions
    plan = chain.plan
    if plan.investigation_trace is not None:
        trace = plan.investigation_trace
        trace.require_valid()
        if (
            trace.question_digest != chain.question.digest
            or trace.need_ids != tuple(item.need_id for item in requirement.needs)
            or trace.session_id != chain.question.read_authority.session_id
            or trace.session_digest != chain.question.read_authority.session_digest
            or trace.read_set_digest
            != chain.question.read_authority.read_set_digest
            or trace.ordered_bundle_digest
            != chain.question.read_authority.ordered_bundle_digest
            or trace.snapshot_ids != chain.question.read_authority.snapshot_ids
            or trace.snapshot_bundle_digests
            != chain.question.read_authority.snapshot_bundle_digests
        ):
            raise _invalid(
                "WORLD_MODEL_EXPORTED_INVESTIGATION_TRACE_MISMATCH",
                "exported investigation trace binds another authority chain",
            )
    _require_stable_record(
        plan,
        id_field="plan_id",
        stable_kind="world_model_query_plan",
        id_domain="WORLD_MODEL_QUERY_PLAN_ID@1",
        digest_domain="WORLD_MODEL_QUERY_PLAN@1",
    )
    if (
        plan.question_id != chain.question.question_id
        or plan.requirement_id != requirement.requirement_id
        or plan.requirement_digest != requirement.digest
        or plan.resolution_set_id != resolutions.resolution_set_id
        or plan.resolution_set_digest != resolutions.digest
        or plan.planning_invocation != resolutions.planning_invocation
        or plan.planning_invocation.stage is not OfflineStage.QUERY_PLANNING
        or plan.planning_invocation.input_digest != requirement.digest
        or plan.capability_registry_digest
        != WORLD_MODEL_QUERY_CAPABILITY_REGISTRY_DIGEST
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_PLAN_MISMATCH",
            "exported Query Plan authority is inconsistent",
        )
    selector_ids = {
        item.selector.selector_id for item in resolutions.resolutions
    }
    for step in plan.steps:
        step_core = {
            key: value
            for key, value in step.canonical_value().items()
            if key != "digest"
        }
        if (
            step.digest != digest_of(["WORLD_MODEL_QUERY_STEP@1", step_core])
            or any(value not in selector_ids for value in step.arguments.values())
        ):
            raise _invalid(
                "WORLD_MODEL_EXPORTED_QUERY_STEP_INVALID",
                "exported Query step is not canonical or uses an unknown selector",
            )
    reconstructed = WorldModelQueryPlanProposal(
        requirement_id=requirement.requirement_id,
        requirement_digest=requirement.digest,
        read_set_digest=chain.question.read_authority.read_set_digest,
        ordered_bundle_digest=chain.question.read_authority.ordered_bundle_digest,
        selectors=tuple(item.selector for item in resolutions.resolutions),
        steps=tuple(
            WorldModelQueryStepProposal(
                step_id=item.step_id,
                need_ids=item.need_ids,
                operation=item.operation,
                arguments=item.arguments,
                parameters=item.parameters,
                constraint_ids=item.constraint_ids,
            )
            for item in plan.steps
        ),
        explicit_gaps=plan.explicit_gaps,
        invocation_id=plan.planning_invocation.invocation_id,
        invocation_digest=plan.planning_invocation.digest,
        investigation_trace=plan.investigation_trace,
    )
    if WorldModelAnsweringService._normalize_plan_proposal(
        reconstructed
    ) != reconstructed:
        raise _invalid(
            "WORLD_MODEL_EXPORTED_PLAN_DEFAULTS_UNSEALED",
            "exported Query Plan does not seal all effective defaults",
        )
    WorldModelAnsweringService._validate_plan_proposal(
        chain.question,
        requirement,
        reconstructed,
        chain.question.read_authority,
    )
    resolutions_by_selector = {
        item.selector.selector_id: item for item in resolutions.resolutions
    }
    expected_steps = tuple(
        WorldModelAnsweringService._seal_query_step(item, resolutions_by_selector)
        for item in reconstructed.steps
    )
    if expected_steps != plan.steps:
        raise _invalid(
            "WORLD_MODEL_EXPORTED_PLAN_STEP_MISMATCH",
            "exported Query Plan step state differs from candidate authority",
        )
    if resolutions.proposal_digest != _query_plan_proposal_digest(reconstructed):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_PLAN_PROPOSAL_MISMATCH",
            "exported Query Plan differs from its sealed proposal",
        )


def _validate_exported_result_and_assessment(
    chain: WorldModelAuthorityChain,
) -> None:
    result_set = chain.result_set
    plan = chain.plan
    assessment = chain.assessment
    _require_stable_record(
        result_set,
        id_field="result_set_id",
        stable_kind="world_model_result_set",
        id_domain="WORLD_MODEL_QUERY_RESULT_SET_ID@1",
        digest_domain="WORLD_MODEL_QUERY_RESULT_SET@1",
    )
    ready_steps = tuple(
        item for item in plan.steps if item.state is QueryStepState.READY
    )
    steps_by_id = {item.step_id: item for item in ready_steps}
    if (
        result_set.question_id != chain.question.question_id
        or result_set.requirement_id != chain.requirement.requirement_id
        or result_set.plan_id != plan.plan_id
        or result_set.plan_digest != plan.digest
        or len(result_set.step_results) != len(ready_steps)
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RESULT_SET_MISMATCH",
            "exported Query Result Set authority is inconsistent",
        )
    resolution_by_selector = {
        item.selector.selector_id: item
        for item in chain.resolutions.resolutions
    }
    bundle_by_snapshot = dict(
        zip(
            chain.question.read_authority.snapshot_ids,
            chain.question.read_authority.snapshot_bundle_digests,
            strict=True,
        )
    )
    for result in result_set.step_results:
        result.view_result.require_valid()
        _require_stable_record(
            result,
            id_field="step_result_id",
            stable_kind="world_model_step_result",
            id_domain="WORLD_MODEL_QUERY_STEP_RESULT_ID@1",
            digest_domain="WORLD_MODEL_QUERY_STEP_RESULT@1",
        )
        step = steps_by_id.get(result.step_id)
        if step is not None and step.operation is StructureViewOperation.ORDERED_SNAPSHOT_DIFF:
            expected_snapshot_ids = (
                _stable_parameter(step.parameters, "base_snapshot_id"),
                _stable_parameter(step.parameters, "target_snapshot_id"),
            )
        elif (
            step is not None
            and step.operation
            is StructureViewOperation.IMPLEMENTATION_CANDIDATES
        ):
            expected_snapshot_ids = (
                _stable_parameter(step.parameters, "snapshot_id"),
            )
        elif step is not None:
            expected_snapshot_ids = tuple(
                dict.fromkeys(
                    resolution_by_selector[selector_id].argument.snapshot_id
                    for selector_id in step.arguments.values()
                    if resolution_by_selector[selector_id].argument is not None
                )
            )
        else:
            expected_snapshot_ids = ()
        if (
            step is None
            or result.step_digest != step.digest
            or result.view_result.operation is not step.operation
            or result.view_result.session_id
            != chain.question.read_authority.session_id
            or result.view_result.session_digest
            != chain.question.read_authority.session_digest
            or result.view_result.read_set_digest
            != chain.question.read_authority.read_set_digest
            or result.view_result.ordered_bundle_digest
            != chain.question.read_authority.ordered_bundle_digest
            or result.view_result.snapshot_ids != expected_snapshot_ids
            or result.view_result.snapshot_bundle_digests
            != tuple(bundle_by_snapshot[item] for item in expected_snapshot_ids)
        ):
            raise _invalid(
                "WORLD_MODEL_EXPORTED_STEP_RESULT_MISMATCH",
                "exported Query step Result binds another Plan or Read Set",
            )
    if tuple(
        (item.step_id, item.step_digest) for item in result_set.step_results
    ) != tuple((item.step_id, item.digest) for item in ready_steps):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RESULT_SET_MISMATCH",
            "exported Query Result Set is not the exact ordered READY-step set",
        )
    expected_support_digest = digest_of(
        [
            "WORLD_MODEL_QUERY_SUPPORT_MAP@1",
            tuple(
                support.canonical_value()
                for result in result_set.step_results
                for support in result.view_result.support_map
            ),
        ]
    )
    expected_allowlist_digest = digest_of(
        [
            "WORLD_MODEL_QUERY_EVIDENCE_ALLOWLIST@1",
            tuple(
                sorted(
                    {
                        evidence.value
                        for result in result_set.step_results
                        for evidence in result.view_result.evidence_allowlist
                    }
                )
            ),
        ]
    )
    if (
        result_set.support_map_digest != expected_support_digest
        or result_set.evidence_allowlist_digest != expected_allowlist_digest
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RESULT_SUPPORT_MISMATCH",
            "exported Query Result support closure is inconsistent",
        )

    _require_stable_record(
        assessment,
        id_field="assessment_id",
        stable_kind="world_model_assessment",
        id_domain="WORLD_MODEL_ASSESSMENT_ID@1",
        digest_domain="WORLD_MODEL_ASSESSMENT@1",
    )
    for item in assessment.needs:
        _require_digest_record(item, "WORLD_MODEL_NEED_ASSESSMENT@1")
    for item in assessment.joint_constraints:
        _require_digest_record(item, "WORLD_MODEL_JOINT_ASSESSMENT@1")
    valid_result_ids = {
        item.step_result_id for item in result_set.step_results
    }
    if (
        assessment.question_id != chain.question.question_id
        or assessment.requirement_id != chain.requirement.requirement_id
        or assessment.requirement_digest != chain.requirement.digest
        or assessment.plan_id != plan.plan_id
        or assessment.plan_digest != plan.digest
        or assessment.result_set_id != result_set.result_set_id
        or assessment.result_set_digest != result_set.digest
        or tuple(item.need_id for item in assessment.needs)
        != tuple(item.need_id for item in chain.requirement.needs)
        or tuple(item.constraint_id for item in assessment.joint_constraints)
        != tuple(
            item.constraint_id
            for item in chain.requirement.joint_constraints
        )
        or any(
            result_id not in valid_result_ids
            for item in assessment.needs
            for result_id in item.step_result_ids
        )
        or any(
            result_id not in valid_result_ids
            for item in assessment.joint_constraints
            for result_id in item.step_result_ids
        )
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_ASSESSMENT_MISMATCH",
            "exported Need or Joint Assessment authority is inconsistent",
        )
    results_by_step = {
        item.step_id: item for item in result_set.step_results
    }
    gaps_by_need = {item.need_id: item for item in plan.explicit_gaps}
    expected_needs = tuple(
        WorldModelAnsweringService._assess_need(
            need,
            plan=plan,
            results_by_step=results_by_step,
            explicit_gap=gaps_by_need.get(need.need_id),
        )
        for need in chain.requirement.needs
    )
    expected_needs_by_id = {item.need_id: item for item in expected_needs}
    expected_joints = tuple(
        WorldModelAnsweringService._assess_joint(
            constraint,
            needs=expected_needs_by_id,
            plan=plan,
            results_by_step=results_by_step,
        )
        for constraint in chain.requirement.joint_constraints
    )
    expected_sufficient = all(
        item.outcome
        in {
            WorldModelNeedOutcome.SATISFIED,
            WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE,
        }
        for item in expected_needs
    ) and all(item.satisfied for item in expected_joints)
    if (
        any(
            type(item.satisfied) is not bool
            for item in assessment.joint_constraints
        )
        or type(assessment.sufficient) is not bool
        or assessment.needs != expected_needs
        or assessment.joint_constraints != expected_joints
        or assessment.sufficient != expected_sufficient
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_ASSESSMENT_REPLAY_MISMATCH",
            "exported Need Assessment differs from deterministic Result replay",
        )


def _validate_exported_response(chain: WorldModelAuthorityChain) -> None:
    draft = chain.draft
    review = chain.review
    authorization = chain.authorization
    delivery = chain.delivery
    _require_stable_record(
        draft,
        id_field="draft_id",
        stable_kind="world_model_draft",
        id_domain="WORLD_MODEL_ANSWER_DRAFT_ID@1",
        digest_domain="WORLD_MODEL_ANSWER_DRAFT@1",
    )
    for claim in draft.claims:
        _require_digest_record(claim, "WORLD_MODEL_ANSWER_CLAIM@1")
    claim_proposals = tuple(
        WorldModelAnswerClaimProposal(
            claim_id=item.claim_id,
            need_id=item.need_id,
            kind=item.kind,
            text=item.text,
            step_result_ids=item.step_result_ids,
        )
        for item in draft.claims
    )
    try:
        expected_claims = WorldModelResponseControlService._seal_claims(
            claim_proposals,
            requirement=chain.requirement,
            result_set=chain.result_set,
            assessment=chain.assessment,
        )
    except DomainError as exc:
        raise _invalid(
            "WORLD_MODEL_EXPORTED_CLAIM_REPLAY_MISMATCH",
            "exported Answer Claims fail deterministic grounding replay",
        ) from exc
    expected_body = "\n".join(item.text for item in draft.claims)
    expected_draft_input_digest = digest_of(
        [
            "WORLD_MODEL_DRAFT_INPUT@1",
            chain.question.digest.value,
            chain.requirement.digest.value,
            chain.plan.digest.value,
            chain.result_set.digest.value,
            chain.assessment.digest.value,
        ]
    )
    valid_results = {
        item.step_result_id for item in chain.result_set.step_results
    }
    if (
        draft.question_id != chain.question.question_id
        or draft.requirement_id != chain.requirement.requirement_id
        or draft.plan_id != chain.plan.plan_id
        or draft.result_set_id != chain.result_set.result_set_id
        or draft.assessment_id != chain.assessment.assessment_id
        or draft.generation_invocation.stage
        is not OfflineStage.ANSWER_DRAFTING
        or draft.generation_invocation.input_digest
        != expected_draft_input_digest
        or draft.claims != expected_claims
        or draft.body != expected_body
        or draft.body_digest != digest_of(expected_body)
        or len(draft.body)
        > chain.question.resource_limits.max_answer_body_chars
        or any(
            result_id not in valid_results
            for claim in draft.claims
            for result_id in claim.step_result_ids
        )
    ):
        raise _invalid(
            (
                "WORLD_MODEL_EXPORTED_CLAIM_REPLAY_MISMATCH"
                if draft.claims != expected_claims
                else "WORLD_MODEL_EXPORTED_DRAFT_MISMATCH"
            ),
            "exported Answer Draft is inconsistent with its sealed chain",
        )

    _require_stable_record(
        review,
        id_field="review_id",
        stable_kind="world_model_review",
        id_domain="WORLD_MODEL_ANSWER_REVIEW_ID@1",
        digest_domain="WORLD_MODEL_ANSWER_REVIEW@1",
    )
    _validate_review_dimensions(review.dimensions, review.decision)
    expected_review_input_digest = digest_of(
        [
            "WORLD_MODEL_REVIEW_INPUT@1",
            chain.question.digest.value,
            chain.requirement.digest.value,
            chain.plan.digest.value,
            chain.result_set.digest.value,
            chain.assessment.digest.value,
            draft.digest.value,
        ]
    )
    if (
        review.question_id != chain.question.question_id
        or review.draft_id != draft.draft_id
        or review.draft_digest != draft.digest
        or review.decision is not WorldModelReviewDecision.APPROVE
        or review.checked_need_ids
        != tuple(item.need_id for item in chain.requirement.needs)
        or review.checked_constraint_ids
        != tuple(
            item.constraint_id for item in chain.requirement.joint_constraints
        )
        or review.checked_step_result_ids
        != tuple(
            item.step_result_id for item in chain.result_set.step_results
        )
        or review.finding_codes
        or review.findings
        or review.review_invocation.stage is not OfflineStage.ANSWER_REVIEW
        or review.review_invocation.input_digest
        != expected_review_input_digest
        or review.review_invocation.invocation_id
        == draft.generation_invocation.invocation_id
        or review.generation_invocation_id
        != draft.generation_invocation.invocation_id
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_REVIEW_MISMATCH",
            "exported Answer Review is inconsistent with its exact Draft",
        )

    expected_chain_digest = digest_of(
        [
            "WORLD_MODEL_PREAUTHORITY_CHAIN@1",
            chain.question.digest.value,
            chain.requirement.digest.value,
            chain.resolutions.digest.value,
            chain.plan.digest.value,
            chain.result_set.digest.value,
            chain.assessment.digest.value,
            chain.draft.digest.value,
            chain.review.digest.value,
        ]
    )
    _require_stable_record(
        authorization,
        id_field="authorization_id",
        stable_kind="world_model_authorization",
        id_domain="WORLD_MODEL_AUTHORIZATION_ID@1",
        digest_domain="WORLD_MODEL_AUTHORIZATION@1",
    )
    if (
        authorization.question_id != chain.question.question_id
        or authorization.requirement_id != chain.requirement.requirement_id
        or authorization.plan_id != chain.plan.plan_id
        or authorization.result_set_id != chain.result_set.result_set_id
        or authorization.assessment_id != chain.assessment.assessment_id
        or authorization.draft_id != draft.draft_id
        or authorization.draft_digest != draft.digest
        or authorization.review_id != review.review_id
        or authorization.review_digest != review.digest
        or authorization.permission_digest != chain.question.permission_digest
        or authorization.chain_digest != expected_chain_digest
        or authorization.sink_id != EVALUATION_ONLY_SINK
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_AUTHORIZATION_MISMATCH",
            "exported Response Authorization is inconsistent",
        )

    WorldModelResponseControlService._validate_delivery(delivery)
    expected_projection_digest = digest_of(
        [
            "WORLD_MODEL_EVALUATION_DELIVERY_PROJECTION@1",
            _evaluation_delivery_projection(
                question=chain.question,
                requirement=chain.requirement,
                draft=draft,
                authorization=authorization,
            ),
        ]
    )
    if (
        delivery.question_id != chain.question.question_id
        or delivery.authorization_id != authorization.authorization_id
        or delivery.authorization_digest != authorization.digest
        or delivery.body_digest != draft.body_digest
        or delivery.projection_digest != expected_projection_digest
        or delivery.delivery_key
        != f"world-model:{digest_of(chain.question.request_ref).value[-32:]}"
        or delivery.sink_id != EVALUATION_ONLY_SINK
        or delivery.state is not WorldModelDeliveryState.DELIVERED
        or type(delivery.revision) is not int
        or delivery.revision != 3
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_DELIVERY_MISMATCH",
            "exported Delivery is inconsistent with its Authorization",
        )


def _require_stable_record(
    record: object,
    *,
    id_field: str,
    stable_kind: str,
    id_domain: str,
    digest_domain: str,
) -> None:
    canonical = record.canonical_value()
    core = {
        key: value
        for key, value in canonical.items()
        if key not in {id_field, "digest"}
    }
    expected_id = _stable(stable_kind, digest_of([id_domain, core]))
    expected_digest = digest_of(
        [digest_domain, {id_field: expected_id.value, **core}]
    )
    if (
        getattr(record, id_field) != expected_id
        or getattr(record, "digest") != expected_digest
    ):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RECORD_DIGEST_MISMATCH",
            f"exported {type(record).__name__} is not canonical",
        )


def _require_digest_record(record: object, digest_domain: str) -> None:
    canonical = record.canonical_value()
    core = {key: value for key, value in canonical.items() if key != "digest"}
    if record.digest != digest_of([digest_domain, core]):
        raise _invalid(
            "WORLD_MODEL_EXPORTED_RECORD_DIGEST_MISMATCH",
            f"exported {type(record).__name__} is not canonical",
        )


def _record_id(record: object) -> StableId:
    for name in (
        "question_id",
        "requirement_id",
        "resolution_set_id",
        "plan_id",
        "result_set_id",
        "assessment_id",
        "draft_id",
        "review_id",
        "authorization_id",
        "delivery_id",
    ):
        value = getattr(record, name, None)
        if isinstance(value, StableId) and value.kind == name.removesuffix("_id"):
            return value
    # Stable kinds intentionally include the world_model prefix, so field order
    # rather than kind equality owns selection for those records.
    mapping = {
        WorldModelQuestion: "question_id",
        WorldModelRequirementRevision: "requirement_id",
        WorldModelCandidateResolutionSet: "resolution_set_id",
        WorldModelQueryPlan: "plan_id",
        WorldModelQueryResultSet: "result_set_id",
        WorldModelAssessment: "assessment_id",
        WorldModelAnswerDraft: "draft_id",
        WorldModelAnswerReview: "review_id",
        WorldModelResponseAuthorization: "authorization_id",
        WorldModelDelivery: "delivery_id",
    }
    try:
        return getattr(record, mapping[type(record)])
    except (KeyError, AttributeError) as exc:
        raise TypeError("world-model record has no stable identity") from exc


def _evaluation_delivery_projection(
    *,
    question: WorldModelQuestion,
    requirement: WorldModelRequirementRevision,
    draft: WorldModelAnswerDraft,
    authorization: WorldModelResponseAuthorization,
) -> dict[str, object]:
    return {
        "evaluation_only": True,
        "mode": WORLD_MODEL_MODE,
        "question_id": question.question_id.value,
        "requirement_id": requirement.requirement_id.value,
        "read_set_digest": question.read_authority.read_set_digest.value,
        "ordered_bundle_digest": (
            question.read_authority.ordered_bundle_digest.value
        ),
        "draft_id": draft.draft_id.value,
        "draft_digest": draft.digest.value,
        "authorization_id": authorization.authorization_id.value,
        "authorization_digest": authorization.digest.value,
    }


def _evaluation_receipt_id(delivery_key: str) -> str:
    receipt_digest = digest_of(
        ["WORLD_MODEL_LOCAL_EVALUATION_RECEIPT_ID@1", delivery_key]
    )
    return f"evaluation-receipt:{receipt_digest.value[-32:]}"


def _validate_review_dimensions(
    dimensions: tuple[WorldModelReviewDimensionAssessment, ...],
    overall_decision: WorldModelReviewDecision,
) -> None:
    if (
        any(
            not isinstance(item, WorldModelReviewDimensionAssessment)
            for item in dimensions
        )
        or tuple(item.dimension for item in dimensions)
        != _REQUIRED_REVIEW_DIMENSIONS
    ):
        raise _invalid(
            "WORLD_MODEL_REVIEW_DIMENSIONS_INCOMPLETE",
            "Answer Review must contain every required dimension exactly once and in canonical order",
        )
    if overall_decision is WorldModelReviewDecision.APPROVE and any(
        item.decision is not WorldModelReviewDecision.APPROVE
        or item.finding_codes
        for item in dimensions
    ):
        raise _invalid(
            "WORLD_MODEL_REVIEW_DIMENSION_REJECTED",
            "Answer Review cannot approve unless every review dimension passes without findings",
        )


def _require_invocation(
    proposal: object,
    expected: WorldModelStrategyInvocation,
    label: str,
) -> None:
    expected.require_valid()
    if (
        getattr(proposal, "invocation_id", None) != expected.invocation_id
        or getattr(proposal, "invocation_digest", None) != expected.digest
    ):
        raise _invalid(
            "WORLD_MODEL_STRATEGY_INVOCATION_MISMATCH",
            f"{label} proposal does not bind its authority-issued invocation",
        )


def _issue_strategy_invocation(
    *,
    stage: OfflineStage,
    question: WorldModelQuestion,
    input_digest: Digest,
    strategy: object,
) -> WorldModelStrategyInvocation:
    strategy_ref = getattr(strategy, "strategy_ref", None)
    if not isinstance(strategy_ref, str):
        raise _invalid(
            "WORLD_MODEL_STRATEGY_IDENTITY_INVALID",
            "world-model proposal role has no exact strategy reference",
        )
    execution_mode = getattr(strategy, "execution_mode", OFFLINE_STRATEGY_MODE)
    if execution_mode == OFFLINE_STRATEGY_MODE:
        return OfflineStrategyInvocation.issue(
            stage=stage,
            question=question,
            input_digest=input_digest,
            strategy_ref=strategy_ref,
        )
    if execution_mode != QUALIFIED_MODEL_STRATEGY_MODE:
        raise _invalid(
            "WORLD_MODEL_STRATEGY_EXECUTION_MODE_INVALID",
            "world-model proposal role requested an unknown execution mode",
        )
    provider_route = getattr(strategy, "provider_route", None)
    if not isinstance(provider_route, str):
        raise _invalid(
            "MODEL_INVOCATION_ROUTE_DENIED",
            "model-backed proposal role has no exact provider route",
        )
    return QualifiedModelStrategyInvocation.issue(
        stage=stage,
        question=question,
        input_digest=input_digest,
        strategy_ref=strategy_ref,
        provider_route=provider_route,
    )


def _execution_boundary_is_valid(
    *,
    question: WorldModelQuestion,
    invocations: Sequence[WorldModelStrategyInvocation],
    provider_call_count: object,
    network_operation_count: object,
) -> bool:
    if (
        type(provider_call_count) is not int
        or type(network_operation_count) is not int
        or any(
            not isinstance(
                invocation,
                (OfflineStrategyInvocation, QualifiedModelStrategyInvocation),
            )
            for invocation in invocations
        )
    ):
        return False
    model_invocations = tuple(
        {
            invocation.invocation_id: invocation
            for invocation in invocations
            if isinstance(invocation, QualifiedModelStrategyInvocation)
        }.values()
    )
    if question.external_dispatch_allowed is False:
        return (
            question.model_route is None
            and not model_invocations
            and provider_call_count == 0
            and network_operation_count == 0
        )
    if (
        question.external_dispatch_allowed is not True
        or not isinstance(question.model_route, str)
        or not model_invocations
        or any(
            invocation.provider_route != question.model_route
            for invocation in model_invocations
        )
    ):
        return False
    if question.read_authority.profile_refs == (
        JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    ):
        if (
            len(model_invocations) != 3
            or tuple(item.stage for item in model_invocations)
            != (
                OfflineStage.QUERY_PLANNING,
                OfflineStage.ANSWER_DRAFTING,
                OfflineStage.ANSWER_REVIEW,
            )
        ):
            return False
        strategy_refs = {item.strategy_ref for item in model_invocations}
        if strategy_refs == {_LEGACY_FIXED_SEMANTICS_STRATEGY_REF}:
            return provider_call_count == network_operation_count == 3
        if strategy_refs == {_BOUNDED_SEMANTICS_STRATEGY_REF}:
            return (
                4 <= provider_call_count <= 6
                and network_operation_count == provider_call_count
            )
        return False
    return (
        len(model_invocations) <= provider_call_count <= _MAX_PROVIDER_CALLS
        and network_operation_count == provider_call_count
    )


def _query_plan_proposal_digest(
    proposal: WorldModelQueryPlanProposal,
) -> Digest:
    core: dict[str, object] = {
        "requirement_id": proposal.requirement_id.value,
        "requirement_digest": proposal.requirement_digest.value,
        "read_set_digest": proposal.read_set_digest.value,
        "ordered_bundle_digest": proposal.ordered_bundle_digest.value,
        "selectors": tuple(
            item.canonical_value() for item in proposal.selectors
        ),
        "steps": tuple(item.canonical_value() for item in proposal.steps),
        "explicit_gaps": tuple(
            item.canonical_value() for item in proposal.explicit_gaps
        ),
        "invocation_id": proposal.invocation_id.value,
        "invocation_digest": proposal.invocation_digest.value,
    }
    if proposal.investigation_trace is not None:
        core["investigation_trace"] = (
            proposal.investigation_trace.canonical_value()
        )
    return digest_of(
        [
            "WORLD_MODEL_QUERY_PLAN_PROPOSAL@1",
            core,
        ]
    )


def _entity_argument_value(
    value: StructureEntityArgument | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "origin": value.origin.value,
        "session_id": value.session_id.value,
        "read_set_digest": value.read_set_digest.value,
        "ordered_bundle_digest": value.ordered_bundle_digest.value,
        "snapshot_id": value.snapshot_id.value,
        "snapshot_bundle_digest": value.snapshot_bundle_digest.value,
        "entity_root_id": value.entity_root_id.value,
        "entity_state_id": value.entity_state_id.value,
        "candidate_result_id": (
            value.candidate_result_id.value if value.candidate_result_id else None
        ),
        "candidate_result_digest": (
            value.candidate_result_digest.value
            if value.candidate_result_digest
            else None
        ),
        "digest": value.digest.value,
    }


def _is_negative_result(result: StructureViewResult) -> bool:
    if result.operation is StructureViewOperation.PATH_EXISTS:
        return result.payload.get("exists") is False
    if result.operation is StructureViewOperation.ALL_SIMPLE_PATHS:
        return result.payload.get("path_count") == 0
    return False


def _implementation_resolution_status(
    result: StructureViewResult,
) -> EntityResolutionStatus:
    if result.operation is not StructureViewOperation.IMPLEMENTATION_CANDIDATES:
        raise _invalid(
            "WORLD_MODEL_IMPLEMENTATION_CANDIDATE_RESULT_REQUIRED",
            "implementation resolution requires an implementation candidate Result",
        )
    candidate_count = result.payload.get("candidate_count")
    query_status = result.payload.get("query_status")
    if type(candidate_count) is not int or candidate_count < 0:
        raise _invalid(
            "WORLD_MODEL_IMPLEMENTATION_CANDIDATE_RESULT_INVALID",
            "implementation candidate Result has an invalid candidate count",
        )
    if query_status == "EXECUTION_FAILURE":
        return EntityResolutionStatus.INCOMPLETE_COVERAGE
    if query_status not in {"SUPPORTED", "KNOWLEDGE_GAP"}:
        raise _invalid(
            "WORLD_MODEL_IMPLEMENTATION_CANDIDATE_RESULT_INVALID",
            "implementation candidate Result has an invalid query status",
        )
    if result.truncated:
        return EntityResolutionStatus.TRUNCATED
    if candidate_count == 0:
        return EntityResolutionStatus.ZERO
    if candidate_count == 1:
        return EntityResolutionStatus.UNIQUE
    return EntityResolutionStatus.AMBIGUOUS


def _implementation_resolution_limitations(
    result: StructureViewResult,
    status: EntityResolutionStatus,
) -> tuple[str, ...]:
    if status in {
        EntityResolutionStatus.ZERO,
        EntityResolutionStatus.TRUNCATED,
        EntityResolutionStatus.INCOMPLETE_COVERAGE,
    }:
        return result.limitations
    if status is EntityResolutionStatus.AMBIGUOUS:
        return ("IMPLEMENTATION_ENTITY_RESOLUTION_AMBIGUOUS",)
    return ()


def _negative_supported(result: StructureViewResult) -> bool:
    return (
        result.completeness is StructureViewCompleteness.COMPLETE
        and not result.truncated
        and result.payload.get("negative_conclusion_supported") is True
    )


def _adjacent_order(
    snapshot_ids: tuple[StableId, ...],
    base: StableId,
    target: StableId,
) -> bool:
    try:
        base_index = snapshot_ids.index(base)
        target_index = snapshot_ids.index(target)
    except ValueError:
        return False
    return target_index == base_index + 1


def _mapping_text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise _invalid(
            "WORLD_MODEL_QUERY_PARAMETER_INVALID",
            f"query parameter {key!r} must be text",
        )
    return item


def _stable_parameter(
    value: Mapping[str, object], key: str
) -> StableId:
    try:
        return StableId(_mapping_text(value, key))
    except ValueError as exc:
        raise _invalid(
            "WORLD_MODEL_QUERY_SNAPSHOT_ID_INVALID",
            f"query parameter {key} is not a valid stable ID",
        ) from exc


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise _invalid(
            "WORLD_MODEL_QUERY_BUDGET_INVALID",
            f"{label} must be a positive integer",
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise _invalid(
            "WORLD_MODEL_TEXT_INVALID",
            f"{label} must be non-empty text without surrounding whitespace",
        )
    return value


def _stable(kind: str, digest: Digest) -> StableId:
    return StableId(f"{kind}_{digest.value[-32:]}")


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.CONTROL_STATE_DENIED,
        message,
        {"reason_code": reason_code},
    )
