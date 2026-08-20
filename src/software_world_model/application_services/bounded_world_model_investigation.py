"""Bounded, result-driven investigation over an exact Structure View.

The model-facing layer may propose operations, but this module owns their
closed shape, provenance, execution, progress, budgets, and sealed trace.  It
has no Source, Repository, Evidence-payload, Update, Direct, model, or network
port.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from time import monotonic_ns
from typing import Callable

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    RelationPredicate,
)

from .structure_read_bundle import (
    JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF,
)
from .structure_view import (
    NeighborhoodDirection,
    StructureEntityArgument,
    StructureViewCompleteness,
    StructureViewOperation,
    StructureViewResult,
    StructureViewService,
)


class InvestigationOperation(str, Enum):
    IMPLEMENTATION_CANDIDATES = "implementation_candidates"
    METHOD_IMPLEMENTATIONS = "method_implementations"
    DECLARED_METHOD_INVENTORY = "declared_method_inventory"
    DIRECT_NEIGHBORHOOD = "direct_neighborhood"
    PATH_EXISTS = "path_exists"
    ALL_SIMPLE_PATHS = "all_simple_paths"
    FINISH = "FINISH"


class InvestigationTerminalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    LIMITATION = "LIMITATION"


class InvestigationCompletenessVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class InvestigationEvidenceRequest:
    """One model-owned semantic evidence obligation, never query authority."""

    operation: InvestigationOperation
    relation_intent: str | None

    def canonical_value(self) -> dict[str, str | None]:
        return {
            "operation": self.operation.value,
            "relation_intent": self.relation_intent,
        }


_PROPOSAL_FIELDS = frozenset(
    {
        "step_index",
        "trace_digest",
        "operation",
        "snapshot_id",
        "search_terms",
        "limit",
        "candidate_result_id",
        "candidate_result_digest",
        "method_refs",
        "entity_refs",
        "direction",
        "predicate",
        "max_depth",
        "max_paths",
        "max_expansions",
        "finish_reason",
        "evidence_requests",
    }
)

_INTENT_FIELDS = frozenset(
    {
        "operation",
        "search_terms",
        "relation_intent",
        "finish_reason",
        "evidence_requests",
    }
)

_SEALED_INPUT_FIELDS = frozenset(
    {
        "original_question",
        "response_language",
        "need_key",
        "read_authority",
        "profile_ref",
        "step_index",
        "trace_digest",
        "previous_result",
        "progress_receipt",
        "remaining_budget",
    }
)

_RELATION_INTENT_ARGUMENTS = {
    "OUTGOING_CALLS": (
        NeighborhoodDirection.OUTGOING,
        RelationPredicate.CALLS,
    ),
    "INCOMING_CALLS": (
        NeighborhoodDirection.INCOMING,
        RelationPredicate.CALLS,
    ),
    "BOTH_CALLS": (
        NeighborhoodDirection.BOTH,
        RelationPredicate.CALLS,
    ),
    "DECLARING_TYPE": (
        NeighborhoodDirection.INCOMING,
        RelationPredicate.DECLARES_METHOD,
    ),
}

_EVIDENCE_OPERATION_ORDER = {
    operation: index
    for index, operation in enumerate(
        (
            InvestigationOperation.IMPLEMENTATION_CANDIDATES,
            InvestigationOperation.METHOD_IMPLEMENTATIONS,
            InvestigationOperation.DECLARED_METHOD_INVENTORY,
            InvestigationOperation.DIRECT_NEIGHBORHOOD,
            InvestigationOperation.PATH_EXISTS,
            InvestigationOperation.ALL_SIMPLE_PATHS,
        )
    )
}

_DIRECT_EVIDENCE_RELATIONS = frozenset(
    {"OUTGOING_CALLS", "INCOMING_CALLS", "BOTH_CALLS"}
)


@dataclass(frozen=True, slots=True)
class InvestigationBudget:
    minimum_model_calls: int = 2
    maximum_model_calls: int = 4
    maximum_steps: int = 4
    maximum_method_refs_per_batch: int = 3
    maximum_query_bytes_per_step: int = 8_192
    maximum_result_bytes_per_step: int = 262_144
    maximum_total_query_bytes: int = 32_768
    maximum_total_result_bytes: int = 786_432
    maximum_support_items: int = 512
    maximum_trace_bytes: int = 1_048_576
    maximum_wall_time_milliseconds: int = 900_000
    retries_allowed: bool = False

    def __post_init__(self) -> None:
        expected = InvestigationBudget.canonical_defaults()
        if self.canonical_value() != expected:
            raise _invalid(
                "INVESTIGATION_BUDGET_NOT_FROZEN",
                "investigation budget differs from ITER-008-BOUNDED-INVESTIGATION@1.0.0",
            )

    @staticmethod
    def canonical_defaults() -> dict[str, object]:
        return {
            "minimum_model_calls": 2,
            "maximum_model_calls": 4,
            "maximum_steps": 4,
            "maximum_method_refs_per_batch": 3,
            "maximum_query_bytes_per_step": 8_192,
            "maximum_result_bytes_per_step": 262_144,
            "maximum_total_query_bytes": 32_768,
            "maximum_total_result_bytes": 786_432,
            "maximum_support_items": 512,
            "maximum_trace_bytes": 1_048_576,
            "maximum_wall_time_milliseconds": 900_000,
            "retries_allowed": False,
        }

    def canonical_value(self) -> dict[str, object]:
        return {
            "minimum_model_calls": self.minimum_model_calls,
            "maximum_model_calls": self.maximum_model_calls,
            "maximum_steps": self.maximum_steps,
            "maximum_method_refs_per_batch": (
                self.maximum_method_refs_per_batch
            ),
            "maximum_query_bytes_per_step": self.maximum_query_bytes_per_step,
            "maximum_result_bytes_per_step": self.maximum_result_bytes_per_step,
            "maximum_total_query_bytes": self.maximum_total_query_bytes,
            "maximum_total_result_bytes": self.maximum_total_result_bytes,
            "maximum_support_items": self.maximum_support_items,
            "maximum_trace_bytes": self.maximum_trace_bytes,
            "maximum_wall_time_milliseconds": (
                self.maximum_wall_time_milliseconds
            ),
            "retries_allowed": self.retries_allowed,
        }


@dataclass(frozen=True, slots=True)
class InvestigationEntityRef:
    source_result_id: StableId
    source_result_digest: Digest
    entity_root_id: StableId
    entity_state_id: StableId

    @classmethod
    def from_mapping(cls, value: object) -> "InvestigationEntityRef":
        if not isinstance(value, Mapping) or set(value) != {
            "source_result_id",
            "source_result_digest",
            "entity_root_id",
            "entity_state_id",
        }:
            raise _invalid(
                "INVESTIGATION_ENTITY_REF_SHAPE_INVALID",
                "investigation Entity Ref has an open or incomplete shape",
            )
        return cls(
            source_result_id=_stable_id(
                value["source_result_id"], "source Result ID"
            ),
            source_result_digest=_digest(
                value["source_result_digest"], "source Result digest"
            ),
            entity_root_id=_stable_id(value["entity_root_id"], "Entity Root ID"),
            entity_state_id=_stable_id(
                value["entity_state_id"], "Entity State ID"
            ),
        )

    def canonical_value(self) -> dict[str, str]:
        return {
            "source_result_id": self.source_result_id.value,
            "source_result_digest": self.source_result_digest.value,
            "entity_root_id": self.entity_root_id.value,
            "entity_state_id": self.entity_state_id.value,
        }


def _normalized_evidence_requests(
    value: object,
) -> tuple[InvestigationEvidenceRequest, ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or not 1 <= len(value) <= 3
    ):
        raise _invalid(
            "INVESTIGATION_EVIDENCE_REQUESTS_INVALID",
            "evidence requests must contain one through three bounded semantic requests",
        )
    operations: set[InvestigationOperation] = set()
    direct_relations: set[str] = set()
    for raw in value:
        if not isinstance(raw, Mapping) or set(raw) != {
            "operation",
            "relation_intent",
        }:
            raise _invalid(
                "INVESTIGATION_EVIDENCE_REQUEST_SHAPE_INVALID",
                "evidence request has an open or incomplete shape",
            )
        try:
            operation = InvestigationOperation(raw.get("operation"))
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "INVESTIGATION_EVIDENCE_OPERATION_INVALID",
                "evidence request uses an unregistered operation",
            ) from exc
        if operation not in _EVIDENCE_OPERATION_ORDER:
            raise _invalid(
                "INVESTIGATION_EVIDENCE_OPERATION_INVALID",
                "FINISH cannot be an evidence obligation",
            )
        operations.add(operation)
        if operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
            relation = raw.get("relation_intent")
            if not isinstance(relation, str) or relation not in _DIRECT_EVIDENCE_RELATIONS:
                raise _invalid(
                    "INVESTIGATION_EVIDENCE_RELATION_INVALID",
                    "direct-neighborhood evidence requires a registered CALLS relation intent",
                )
            direct_relations.add(relation)

    if len(operations) > 1:
        operations.discard(InvestigationOperation.IMPLEMENTATION_CANDIDATES)
    graph_operations = {
        InvestigationOperation.DIRECT_NEIGHBORHOOD,
        InvestigationOperation.PATH_EXISTS,
        InvestigationOperation.ALL_SIMPLE_PATHS,
    }
    if operations & graph_operations:
        operations.discard(InvestigationOperation.METHOD_IMPLEMENTATIONS)
    if InvestigationOperation.ALL_SIMPLE_PATHS in operations:
        operations.discard(InvestigationOperation.PATH_EXISTS)
    if InvestigationOperation.DECLARED_METHOD_INVENTORY in operations and len(
        operations
    ) != 1:
        raise _invalid(
            "INVESTIGATION_EVIDENCE_BUDGET_UNREACHABLE",
            "declared inventory cannot be combined with another evidence obligation in the frozen budget",
        )
    if not operations or len(operations) > 2:
        raise _invalid(
            "INVESTIGATION_EVIDENCE_BUDGET_UNREACHABLE",
            "normalized evidence obligations exceed the frozen transition budget",
        )

    normalized: list[InvestigationEvidenceRequest] = []
    for operation in sorted(operations, key=_EVIDENCE_OPERATION_ORDER.__getitem__):
        relation: str | None = None
        if operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
            if not direct_relations:
                raise _invalid(
                    "INVESTIGATION_EVIDENCE_RELATION_INVALID",
                    "direct-neighborhood evidence lacks a CALLS relation intent",
                )
            relation = (
                next(iter(direct_relations))
                if len(direct_relations) == 1
                else "BOTH_CALLS"
            )
        normalized.append(
            InvestigationEvidenceRequest(
                operation=operation,
                relation_intent=relation,
            )
        )
    return tuple(normalized)


def normalize_investigation_evidence_requests(
    value: object,
) -> tuple[dict[str, str | None], ...]:
    """Return the canonical, dependency-reduced evidence obligation value."""

    return tuple(
        item.canonical_value() for item in _normalized_evidence_requests(value)
    )


def _evidence_requests_from_previous_result(
    previous_result: Mapping[object, object],
) -> tuple[InvestigationEvidenceRequest, ...]:
    requests = _normalized_evidence_requests(
        previous_result.get("evidence_requests")
    )
    if [item.canonical_value() for item in requests] != previous_result.get(
        "evidence_requests"
    ):
        raise _invalid(
            "INVESTIGATION_EVIDENCE_LEDGER_NON_CANONICAL",
            "sealed evidence ledger is not in canonical dependency order",
        )
    return requests


def _candidate_result_allows_method_batch(
    previous_result: Mapping[object, object],
) -> bool:
    results = previous_result.get("results")
    if (
        isinstance(results, (str, bytes))
        or not isinstance(results, Sequence)
        or len(results) != 1
        or not isinstance(results[0], Mapping)
    ):
        return False
    result = results[0]
    if result.get("truncated") is not False:
        return False
    payload = result.get("payload")
    if not isinstance(payload, Mapping):
        return False
    if {"total", "returned", "candidate_count", "next_cursor"}.issubset(
        payload
    ):
        return (
            payload.get("total") == payload.get("returned")
            and payload.get("returned") == payload.get("candidate_count")
            and payload.get("next_cursor") is None
        )
    return (
        result.get("completeness")
        == InvestigationCompletenessVerdict.COMPLETE.value
        and type(payload.get("candidate_count")) is int
    )


def _scheduled_investigation_transition(
    *,
    step_index: int,
    previous_result: object,
) -> tuple[InvestigationOperation, str | None, tuple[InvestigationEvidenceRequest, ...]]:
    if step_index == 1:
        return InvestigationOperation.IMPLEMENTATION_CANDIDATES, None, ()
    if not isinstance(previous_result, Mapping):
        raise _invalid(
            "INVESTIGATION_INTENT_PREFIX_INVALID",
            "later investigation transition requires one sealed previous Result",
        )
    requests = _evidence_requests_from_previous_result(previous_result)
    try:
        previous_operation = InvestigationOperation(previous_result.get("operation"))
    except (TypeError, ValueError) as exc:
        raise _invalid(
            "INVESTIGATION_INTENT_RESULT_INVALID",
            "previous Result uses an unregistered operation",
        ) from exc
    refs = _compiled_previous_result_refs(previous_result)
    method_ref_count = sum(1 for _, kind in refs if kind == "JAVA_METHOD")
    type_ref_count = sum(1 for _, kind in refs if kind == "JAVA_TYPE")
    requested = {item.operation: item for item in requests}

    operation = InvestigationOperation.FINISH
    relation: str | None = None
    if previous_operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
        if (
            not refs
            or not _candidate_result_allows_method_batch(previous_result)
            or set(requested)
            == {InvestigationOperation.IMPLEMENTATION_CANDIDATES}
        ):
            operation = InvestigationOperation.FINISH
        elif InvestigationOperation.DECLARED_METHOD_INVENTORY in requested:
            operation = InvestigationOperation.DIRECT_NEIGHBORHOOD
            relation = "DECLARING_TYPE"
        elif method_ref_count:
            operation = InvestigationOperation.METHOD_IMPLEMENTATIONS
    elif previous_operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
        direct = requested.get(InvestigationOperation.DIRECT_NEIGHBORHOOD)
        if direct is not None and method_ref_count:
            operation = InvestigationOperation.DIRECT_NEIGHBORHOOD
            relation = direct.relation_intent
        elif InvestigationOperation.PATH_EXISTS in requested and method_ref_count >= 2:
            operation = InvestigationOperation.PATH_EXISTS
        elif (
            InvestigationOperation.ALL_SIMPLE_PATHS in requested
            and method_ref_count >= 2
        ):
            operation = InvestigationOperation.ALL_SIMPLE_PATHS
    elif previous_operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
        if InvestigationOperation.DECLARED_METHOD_INVENTORY in requested and type_ref_count:
            operation = InvestigationOperation.DECLARED_METHOD_INVENTORY
        elif InvestigationOperation.PATH_EXISTS in requested and method_ref_count >= 2:
            operation = InvestigationOperation.PATH_EXISTS
        elif (
            InvestigationOperation.ALL_SIMPLE_PATHS in requested
            and method_ref_count >= 2
        ):
            operation = InvestigationOperation.ALL_SIMPLE_PATHS
    return operation, relation, requests


def constrained_investigation_operations(
    *,
    sealed_input: object,
) -> tuple[str, ...]:
    """Return the one platform-authorized transition for a sealed prefix."""

    if not isinstance(sealed_input, Mapping):
        raise _invalid(
            "INVESTIGATION_INTENT_AUTHORITY_INVALID",
            "investigation transition lacks a sealed input",
        )
    step_index = sealed_input.get("step_index")
    if type(step_index) is not int or not 1 <= step_index <= 4:
        raise _invalid(
            "INVESTIGATION_STEP_INDEX_INVALID",
            "investigation step index must be from 1 through 4",
        )
    operation, _, _ = _scheduled_investigation_transition(
        step_index=step_index,
        previous_result=sealed_input.get("previous_result"),
    )
    return (operation.value,)


def _platform_finish_reason(
    *,
    previous_result: Mapping[object, object],
    progress_receipt: Mapping[object, object],
) -> str:
    completeness = progress_receipt.get("completeness")
    if isinstance(completeness, Mapping):
        query = completeness.get("query_result")
        representation = completeness.get("knowledge_representation")
        discovery = completeness.get("business_discovery_recall")
        if query != InvestigationCompletenessVerdict.COMPLETE.value:
            return "Limitation: query completeness is unknown or incomplete."
        if representation != InvestigationCompletenessVerdict.COMPLETE.value:
            return "Limitation: representation coverage is unknown or incomplete."
        if (
            previous_result.get("operation")
            != InvestigationOperation.IMPLEMENTATION_CANDIDATES.value
            or _compiled_previous_result_refs(previous_result)
        ):
            return "Platform evidence obligations are complete and typed support is sufficient."
        if discovery != InvestigationCompletenessVerdict.COMPLETE.value:
            return "Limitation: absence cannot be established because discovery recall is unknown or incomplete."
        return "Bounded authorized absence is complete for the sealed authority."
    return "Limitation: the sealed completeness receipt is unavailable."


def compile_investigation_intent(
    value: object,
    *,
    sealed_input: object,
    available_operations: Sequence[str] | None = None,
) -> dict[str, object]:
    """Compile model-owned semantic intent into one exact platform proposal.

    The model chooses the operation and the semantic argument owned by that
    operation.  The fixed model-output envelope carries every possible
    semantic slot, but slots that do not belong to the selected operation have
    no meaning and are deterministically discarded.  Platform authority
    fields, opaque Result/Entity references, and frozen query bounds are copied
    or derived here instead of being regenerated by the model.
    """

    if not isinstance(value, Mapping) or set(value) != _INTENT_FIELDS:
        raise _invalid(
            "INVESTIGATION_INTENT_SHAPE_INVALID",
            "investigation intent has an open or incomplete shape",
        )
    if (
        not isinstance(sealed_input, Mapping)
        or set(sealed_input) != _SEALED_INPUT_FIELDS
        or sealed_input.get("profile_ref") != JAVA_SOURCE_SEMANTICS_PROFILE_REF
    ):
        raise _invalid(
            "INVESTIGATION_INTENT_AUTHORITY_INVALID",
            "investigation intent does not bind the closed source-semantics input",
        )
    step_index = sealed_input.get("step_index")
    if type(step_index) is not int or not 1 <= step_index <= 4:
        raise _invalid(
            "INVESTIGATION_STEP_INDEX_INVALID",
            "investigation step index must be from 1 through 4",
        )
    trace_digest = _digest(sealed_input.get("trace_digest"), "trace digest")
    try:
        InvestigationOperation(value.get("operation"))
    except (TypeError, ValueError) as exc:
        raise _invalid(
            "INVESTIGATION_OPERATION_INVALID",
            "investigation intent uses an unregistered operation",
        ) from exc
    previous_result = sealed_input.get("previous_result")
    progress_receipt = sealed_input.get("progress_receipt")
    if step_index == 1:
        evidence_requests = _normalized_evidence_requests(
            value.get("evidence_requests")
        )
    elif isinstance(previous_result, Mapping):
        evidence_requests = _evidence_requests_from_previous_result(
            previous_result
        )
    else:
        evidence_requests = ()
    operation, scheduled_relation_intent, scheduled_requests = (
        _scheduled_investigation_transition(
            step_index=step_index,
            previous_result=previous_result,
        )
    )
    if step_index > 1 and evidence_requests != scheduled_requests:
        raise _invalid(
            "INVESTIGATION_EVIDENCE_LEDGER_MISMATCH",
            "scheduled transition does not bind the sealed evidence ledger",
        )
    expected_available_operations = (operation.value,)
    if (
        available_operations is not None
        and tuple(available_operations) != expected_available_operations
    ):
        raise _invalid(
            "INVESTIGATION_TRANSITION_ALLOWLIST_INVALID",
            "investigation available operations do not match the platform transition",
        )

    search_terms: tuple[str, ...] = ()
    if operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
        search_terms = _deduplicated_text_sequence(
            value.get("search_terms"),
            "investigation search terms",
            maximum=12,
        )
    if step_index == 1:
        if previous_result is not None or progress_receipt is not None:
            raise _invalid(
                "INVESTIGATION_INTENT_PREFIX_INVALID",
                "first investigation intent cannot carry prior progress",
            )
    elif not isinstance(previous_result, Mapping) or not isinstance(
        progress_receipt, Mapping
    ):
        raise _invalid(
            "INVESTIGATION_INTENT_PREFIX_INVALID",
            "later investigation intent requires one sealed previous Result and progress receipt",
        )

    proposal: dict[str, object] = {
        "step_index": step_index,
        "trace_digest": trace_digest.value,
        "operation": operation.value,
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
        "finish_reason": None,
        "evidence_requests": [
            item.canonical_value() for item in evidence_requests
        ],
    }
    if operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
        read_authority = sealed_input.get("read_authority")
        snapshot_ids = (
            read_authority.get("snapshot_ids")
            if isinstance(read_authority, Mapping)
            else None
        )
        if (
            step_index != 1
            or not search_terms
            or isinstance(snapshot_ids, (str, bytes))
            or not isinstance(snapshot_ids, Sequence)
            or len(snapshot_ids) != 1
        ):
            raise _invalid(
                "INVESTIGATION_INTENT_OPERATION_INVALID",
                "candidate intent requires first-step terms and one exact authorized Snapshot",
            )
        proposal.update(
            {
                "snapshot_id": _stable_id(
                    snapshot_ids[0], "authorized Snapshot ID"
                ).value,
                "search_terms": list(search_terms),
                "limit": 5,
            }
        )
        return proposal

    if step_index == 1:
        raise _invalid(
            "INVESTIGATION_INTENT_OPERATION_INVALID",
            "later investigation intent cannot restart candidate discovery",
        )
    assert isinstance(previous_result, Mapping)
    if operation is InvestigationOperation.FINISH:
        assert isinstance(progress_receipt, Mapping)
        proposal["finish_reason"] = _platform_finish_reason(
            previous_result=previous_result,
            progress_receipt=progress_receipt,
        )
        return proposal

    refs = _compiled_previous_result_refs(previous_result)
    if operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
        if (
            previous_result.get("operation")
            != InvestigationOperation.IMPLEMENTATION_CANDIDATES.value
        ):
            raise _invalid(
                "INVESTIGATION_INTENT_TRANSITION_INVALID",
                "method batch intent requires one candidate Result",
            )
        results = previous_result.get("results")
        method_refs = tuple(item for item in refs if item[1] == "JAVA_METHOD")
        if (
            isinstance(results, (str, bytes))
            or not isinstance(results, Sequence)
            or len(results) != 1
            or not isinstance(results[0], Mapping)
            or not method_refs
        ):
            raise _invalid(
                "INVESTIGATION_INTENT_RESULT_INVALID",
                "method batch intent lacks one non-empty candidate Result",
            )
        result_id = _stable_id(results[0].get("result_id"), "candidate Result ID")
        result_digest = _digest(
            results[0].get("digest"), "candidate Result digest"
        )
        proposal.update(
            {
                "candidate_result_id": result_id.value,
                "candidate_result_digest": result_digest.value,
                "method_refs": [item[0] for item in method_refs[:3]],
            }
        )
        return proposal
    if operation is InvestigationOperation.DECLARED_METHOD_INVENTORY:
        type_refs = tuple(item for item in refs if item[1] == "JAVA_TYPE")
        if not type_refs:
            raise _invalid(
                "INVESTIGATION_INTENT_RESULT_INVALID",
                "declared inventory intent lacks an exact JAVA_TYPE Ref",
            )
        proposal["entity_refs"] = [type_refs[0][0]]
        return proposal
    if operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
        method_refs = tuple(item for item in refs if item[1] == "JAVA_METHOD")
        if (
            scheduled_relation_intent not in _RELATION_INTENT_ARGUMENTS
            or not method_refs
        ):
            raise _invalid(
                "INVESTIGATION_INTENT_RESULT_INVALID",
                "direct-neighborhood intent lacks a relation purpose or exact Ref",
            )
        direction, predicate = _RELATION_INTENT_ARGUMENTS[
            scheduled_relation_intent
        ]
        proposal.update(
            {
                "entity_refs": [method_refs[0][0]],
                "direction": direction.value,
                "predicate": predicate.value,
            }
        )
        return proposal
    if operation in {
        InvestigationOperation.PATH_EXISTS,
        InvestigationOperation.ALL_SIMPLE_PATHS,
    }:
        method_refs = tuple(item for item in refs if item[1] == "JAVA_METHOD")
        if len(method_refs) < 2:
            raise _invalid(
                "INVESTIGATION_INTENT_RESULT_INVALID",
                "path intent requires two exact prior Result refs",
            )
        proposal.update(
            {
                "entity_refs": [item[0] for item in method_refs[:2]],
                "predicate": RelationPredicate.CALLS.value,
                "max_depth": 8,
                "max_expansions": 256,
            }
        )
        if operation is InvestigationOperation.ALL_SIMPLE_PATHS:
            proposal["max_paths"] = 16
        return proposal
    raise _invalid(
        "INVESTIGATION_INTENT_OPERATION_INVALID",
        "investigation intent cannot be compiled",
    )


def _compiled_previous_result_refs(
    previous_result: Mapping[object, object],
) -> tuple[tuple[dict[str, str], str | None], ...]:
    results = previous_result.get("results")
    if (
        isinstance(results, (str, bytes))
        or not isinstance(results, Sequence)
        or not results
    ):
        return ()
    compiled: list[tuple[dict[str, str], str | None]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for raw_result in results:
        if not isinstance(raw_result, Mapping):
            raise _invalid(
                "INVESTIGATION_INTENT_RESULT_INVALID",
                "previous Result collection contains a non-object",
            )
        result_id = _stable_id(raw_result.get("result_id"), "source Result ID")
        result_digest = _digest(raw_result.get("digest"), "source Result digest")

        def add(raw_entity: object) -> None:
            if not isinstance(raw_entity, Mapping):
                return
            root_value = raw_entity.get("root_id", raw_entity.get("entity_root_id"))
            state_value = raw_entity.get(
                "state_id", raw_entity.get("entity_state_id")
            )
            if not isinstance(root_value, str) or not isinstance(state_value, str):
                return
            source_id = raw_entity.get("source_result_id")
            source_digest = raw_entity.get("source_result_digest")
            if (
                (source_id is not None and source_id != result_id.value)
                or (
                    source_digest is not None
                    and source_digest != result_digest.value
                )
            ):
                raise _invalid(
                    "INVESTIGATION_INTENT_RESULT_INVALID",
                    "previous Result exposes a Ref with mismatched provenance",
                )
            root_id = _stable_id(root_value, "Entity Root ID")
            state_id = _stable_id(state_value, "Entity State ID")
            key = (
                result_id.value,
                result_digest.value,
                root_id.value,
                state_id.value,
            )
            if key in seen:
                return
            seen.add(key)
            entity_type = raw_entity.get("entity_type")
            compiled.append(
                (
                    {
                        "source_result_id": result_id.value,
                        "source_result_digest": result_digest.value,
                        "entity_root_id": root_id.value,
                        "entity_state_id": state_id.value,
                    },
                    entity_type if isinstance(entity_type, str) else None,
                )
            )

        exposed = raw_result.get("entity_refs")
        if isinstance(exposed, Sequence) and not isinstance(exposed, (str, bytes)):
            for item in exposed:
                add(item)
        add(raw_result.get("scope_entity_ref"))

        def visit(raw: object) -> None:
            if isinstance(raw, Mapping):
                add(raw)
                for nested in raw.values():
                    visit(nested)
            elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
                for nested in raw:
                    visit(nested)

        visit(raw_result.get("payload"))
    return tuple(compiled)


@dataclass(frozen=True, slots=True)
class BusinessDiscoveryRecallOracle:
    oracle_ref: str
    oracle_result_digest: Digest
    authority_binding_digest: Digest
    discovery_contract_ref: str
    snapshot_id: StableId
    bundle_digest: Digest
    counterexample_classes: tuple[str, ...]
    verdict: InvestigationCompletenessVerdict
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        oracle_ref: str,
        oracle_result_digest: Digest,
        authority_binding_digest: Digest,
        discovery_contract_ref: str,
        snapshot_id: StableId,
        bundle_digest: Digest,
        counterexample_classes: Sequence[str],
        verdict: InvestigationCompletenessVerdict,
    ) -> "BusinessDiscoveryRecallOracle":
        normalized_ref = _text(oracle_ref, "business discovery Oracle ref")
        normalized_contract = _text(
            discovery_contract_ref,
            "business discovery Contract ref",
        )
        if (
            not isinstance(oracle_result_digest, Digest)
            or not isinstance(authority_binding_digest, Digest)
            or normalized_contract
            != JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
            or not isinstance(snapshot_id, StableId)
            or snapshot_id.kind != "structure_snapshot"
            or not isinstance(bundle_digest, Digest)
            or not isinstance(verdict, InvestigationCompletenessVerdict)
            or isinstance(counterexample_classes, (str, bytes))
        ):
            raise _invalid(
                "BUSINESS_DISCOVERY_ORACLE_AUTHORITY_INVALID",
                "business discovery Oracle does not bind the active discovery Contract and exact Bundle",
            )
        normalized_classes = tuple(
            sorted(
                {
                    _text(item, "counterexample class")
                    for item in counterexample_classes
                }
            )
        )
        if verdict is InvestigationCompletenessVerdict.COMPLETE and normalized_classes != (
            "alternate-entry",
            "naming",
            "synonym",
        ):
            raise _invalid(
                "BUSINESS_DISCOVERY_ORACLE_INCOMPLETE",
                "a COMPLETE discovery Oracle must seal naming, synonym, and alternate-entry counterexamples",
            )
        core = {
            "oracle_ref": normalized_ref,
            "oracle_result_digest": oracle_result_digest.value,
            "authority_binding_digest": authority_binding_digest.value,
            "discovery_contract_ref": normalized_contract,
            "snapshot_id": snapshot_id.value,
            "bundle_digest": bundle_digest.value,
            "counterexample_classes": normalized_classes,
            "verdict": verdict.value,
        }
        return cls(
            oracle_ref=normalized_ref,
            oracle_result_digest=oracle_result_digest,
            authority_binding_digest=authority_binding_digest,
            discovery_contract_ref=normalized_contract,
            snapshot_id=snapshot_id,
            bundle_digest=bundle_digest,
            counterexample_classes=normalized_classes,
            verdict=verdict,
            digest=digest_of(["BUSINESS_DISCOVERY_RECALL_ORACLE@1", core]),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "oracle_ref": self.oracle_ref,
            "oracle_result_digest": self.oracle_result_digest.value,
            "authority_binding_digest": self.authority_binding_digest.value,
            "discovery_contract_ref": self.discovery_contract_ref,
            "snapshot_id": self.snapshot_id.value,
            "bundle_digest": self.bundle_digest.value,
            "counterexample_classes": self.counterexample_classes,
            "verdict": self.verdict.value,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        expected = type(self).create(
            oracle_ref=self.oracle_ref,
            oracle_result_digest=self.oracle_result_digest,
            authority_binding_digest=self.authority_binding_digest,
            discovery_contract_ref=self.discovery_contract_ref,
            snapshot_id=self.snapshot_id,
            bundle_digest=self.bundle_digest,
            counterexample_classes=self.counterexample_classes,
            verdict=self.verdict,
        )
        if self != expected:
            raise _invalid(
                "BUSINESS_DISCOVERY_ORACLE_INVALID",
                "business discovery Oracle is not canonical",
            )


@dataclass(frozen=True, slots=True)
class InvestigationProposal:
    step_index: int
    trace_digest: Digest
    operation: InvestigationOperation
    snapshot_id: StableId | None
    search_terms: tuple[str, ...]
    limit: int | None
    candidate_result_id: StableId | None
    candidate_result_digest: Digest | None
    method_refs: tuple[InvestigationEntityRef, ...]
    entity_refs: tuple[InvestigationEntityRef, ...]
    direction: NeighborhoodDirection | None
    predicate: RelationPredicate | None
    max_depth: int | None
    max_paths: int | None
    max_expansions: int | None
    finish_reason: str | None
    evidence_requests: tuple[InvestigationEvidenceRequest, ...]
    model_proposal_digest: Digest
    digest: Digest

    @classmethod
    def from_mapping(
        cls,
        value: object,
        *,
        model_proposal_digest: Digest,
    ) -> "InvestigationProposal":
        if not isinstance(value, Mapping) or set(value) != _PROPOSAL_FIELDS:
            raise _invalid(
                "INVESTIGATION_PROPOSAL_SHAPE_INVALID",
                "investigation proposal has an open or incomplete shape",
            )
        step_index = value["step_index"]
        if type(step_index) is not int or not 1 <= step_index <= 4:
            raise _invalid(
                "INVESTIGATION_STEP_INDEX_INVALID",
                "investigation step index must be from 1 through 4",
            )
        try:
            operation = InvestigationOperation(value["operation"])
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "INVESTIGATION_OPERATION_INVALID",
                "investigation proposal uses an unregistered operation",
            ) from exc
        proposal = cls(
            step_index=step_index,
            trace_digest=_digest(value["trace_digest"], "trace digest"),
            operation=operation,
            snapshot_id=_optional_stable_id(value["snapshot_id"], "Snapshot ID"),
            search_terms=_text_sequence(
                value["search_terms"], "investigation search terms", maximum=12
            ),
            limit=_optional_positive_int(value["limit"], "candidate limit"),
            candidate_result_id=_optional_stable_id(
                value["candidate_result_id"], "candidate Result ID"
            ),
            candidate_result_digest=_optional_digest(
                value["candidate_result_digest"], "candidate Result digest"
            ),
            method_refs=_entity_refs(value["method_refs"], "method refs"),
            entity_refs=_entity_refs(value["entity_refs"], "Entity refs"),
            direction=_optional_enum(
                NeighborhoodDirection, value["direction"], "neighborhood direction"
            ),
            predicate=_optional_enum(
                RelationPredicate, value["predicate"], "relation predicate"
            ),
            max_depth=_optional_positive_int(value["max_depth"], "max depth"),
            max_paths=_optional_positive_int(value["max_paths"], "max paths"),
            max_expansions=_optional_positive_int(
                value["max_expansions"], "max expansions"
            ),
            finish_reason=(
                _text(value["finish_reason"], "finish reason")
                if value["finish_reason"] is not None
                else None
            ),
            evidence_requests=_normalized_evidence_requests(
                value["evidence_requests"]
            ),
            model_proposal_digest=model_proposal_digest,
            digest=Digest("sha256:" + "0" * 64),
        )
        proposal._require_closed_operation_shape()
        core = proposal._canonical_core()
        return cls(
            **{
                name: getattr(proposal, name)
                for name in proposal.__dataclass_fields__
                if name != "digest"
            },
            digest=digest_of(["BOUNDED_INVESTIGATION_PROPOSAL@1", core]),
        )

    def _canonical_core(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "trace_digest": self.trace_digest.value,
            "operation": self.operation.value,
            "snapshot_id": self.snapshot_id.value if self.snapshot_id else None,
            "search_terms": self.search_terms,
            "limit": self.limit,
            "candidate_result_id": (
                self.candidate_result_id.value
                if self.candidate_result_id is not None
                else None
            ),
            "candidate_result_digest": (
                self.candidate_result_digest.value
                if self.candidate_result_digest is not None
                else None
            ),
            "method_refs": tuple(item.canonical_value() for item in self.method_refs),
            "entity_refs": tuple(item.canonical_value() for item in self.entity_refs),
            "direction": self.direction.value if self.direction else None,
            "predicate": self.predicate.value if self.predicate else None,
            "max_depth": self.max_depth,
            "max_paths": self.max_paths,
            "max_expansions": self.max_expansions,
            "finish_reason": self.finish_reason,
            "evidence_requests": tuple(
                item.canonical_value() for item in self.evidence_requests
            ),
            "model_proposal_digest": self.model_proposal_digest.value,
        }

    def canonical_value(self) -> dict[str, object]:
        return {**self._canonical_core(), "digest": self.digest.value}

    def require_valid(self) -> None:
        self._require_closed_operation_shape()
        if self.digest != digest_of(
            ["BOUNDED_INVESTIGATION_PROPOSAL@1", self._canonical_core()]
        ):
            raise _invalid(
                "INVESTIGATION_PROPOSAL_DIGEST_MISMATCH",
                "investigation proposal is not canonical",
            )

    def _require_closed_operation_shape(self) -> None:
        if not self.evidence_requests:
            raise _invalid(
                "INVESTIGATION_EVIDENCE_REQUESTS_INVALID",
                "investigation proposal must bind a non-empty evidence ledger",
            )
        empty_refs = not self.method_refs and not self.entity_refs
        no_graph = (
            self.direction is None
            and self.predicate is None
            and self.max_depth is None
            and self.max_paths is None
            and self.max_expansions is None
        )
        no_candidate = (
            self.snapshot_id is None
            and not self.search_terms
            and self.limit is None
            and self.candidate_result_id is None
            and self.candidate_result_digest is None
        )
        no_search = (
            self.snapshot_id is None
            and not self.search_terms
            and self.limit is None
        )
        if self.operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
            valid = (
                self.snapshot_id is not None
                and 1 <= len(self.search_terms) <= 12
                and self.limit is not None
                and 1 <= self.limit <= 20
                and self.candidate_result_id is None
                and self.candidate_result_digest is None
                and empty_refs
                and no_graph
                and self.finish_reason is None
            )
        elif self.operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
            valid = (
                no_search
                and self.candidate_result_id is not None
                and self.candidate_result_digest is not None
                and 1 <= len(self.method_refs) <= 3
                and not self.entity_refs
                and no_graph
                and self.finish_reason is None
            )
        elif self.operation is InvestigationOperation.DECLARED_METHOD_INVENTORY:
            valid = (
                no_candidate
                and not self.method_refs
                and len(self.entity_refs) == 1
                and no_graph
                and self.finish_reason is None
            )
        elif self.operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
            valid = (
                no_candidate
                and not self.method_refs
                and len(self.entity_refs) == 1
                and self.direction is not None
                and self.max_depth is None
                and self.max_paths is None
                and self.max_expansions is None
                and self.finish_reason is None
            )
        elif self.operation is InvestigationOperation.PATH_EXISTS:
            valid = (
                no_candidate
                and not self.method_refs
                and len(self.entity_refs) == 2
                and self.direction is None
                and self.predicate is not None
                and self.max_depth is not None
                and self.max_paths is None
                and self.max_expansions is not None
                and self.finish_reason is None
            )
        elif self.operation is InvestigationOperation.ALL_SIMPLE_PATHS:
            valid = (
                no_candidate
                and not self.method_refs
                and len(self.entity_refs) == 2
                and self.direction is None
                and self.predicate is not None
                and self.max_depth is not None
                and self.max_paths is not None
                and self.max_expansions is not None
                and self.finish_reason is None
            )
        else:
            valid = no_candidate and empty_refs and no_graph and self.finish_reason is not None
        if not valid:
            raise _invalid(
                "INVESTIGATION_OPERATION_SHAPE_INVALID",
                "investigation proposal fields do not match its exact operation schema",
            )
        refs = (*self.method_refs, *self.entity_refs)
        if len(set(refs)) != len(refs):
            raise _invalid(
                "INVESTIGATION_ENTITY_REF_DUPLICATE",
                "investigation proposal repeats an exact Entity Ref",
            )


@dataclass(frozen=True, slots=True)
class InvestigationStep:
    proposal: InvestigationProposal
    results: tuple[StructureViewResult, ...]
    query_bytes: int
    result_bytes: int
    support_item_count: int
    progress_token: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        proposal: InvestigationProposal,
        results: Sequence[StructureViewResult],
    ) -> "InvestigationStep":
        normalized_results = tuple(results)
        query_bytes = len(canonical_json_bytes(proposal.canonical_value()))
        result_bytes = len(
            canonical_json_bytes(
                tuple(item.canonical_value() for item in normalized_results)
            )
        )
        support_count = len(
            {
                item.digest
                for result in normalized_results
                for item in result.support_map
            }
        )
        progress_token = digest_of(
            [
                "BOUNDED_INVESTIGATION_PROGRESS@1",
                proposal.operation.value,
                tuple(
                    (item.result_id.value, item.digest.value)
                    for item in normalized_results
                ),
            ]
        )
        core = {
            "proposal": proposal.canonical_value(),
            "results": tuple(item.canonical_value() for item in normalized_results),
            "query_bytes": query_bytes,
            "result_bytes": result_bytes,
            "support_item_count": support_count,
            "progress_token": progress_token.value,
        }
        return cls(
            proposal=proposal,
            results=normalized_results,
            query_bytes=query_bytes,
            result_bytes=result_bytes,
            support_item_count=support_count,
            progress_token=progress_token,
            digest=digest_of(["BOUNDED_INVESTIGATION_STEP@1", core]),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "proposal": self.proposal.canonical_value(),
            "results": tuple(item.canonical_value() for item in self.results),
            "query_bytes": self.query_bytes,
            "result_bytes": self.result_bytes,
            "support_item_count": self.support_item_count,
            "progress_token": self.progress_token.value,
            "digest": self.digest.value,
        }

    def require_valid(self) -> None:
        self.proposal.require_valid()
        for result in self.results:
            result.require_valid()
        if self != type(self).create(proposal=self.proposal, results=self.results):
            raise _invalid(
                "INVESTIGATION_STEP_INVALID",
                "investigation step is not canonical",
            )


@dataclass(frozen=True, slots=True)
class InvestigationCompleteness:
    query_result: InvestigationCompletenessVerdict
    knowledge_representation: InvestigationCompletenessVerdict
    business_discovery_recall: InvestigationCompletenessVerdict
    missing_limitation_codes: tuple[str, ...]

    @property
    def bounded_absence_allowed(self) -> bool:
        return (
            self.query_result is InvestigationCompletenessVerdict.COMPLETE
            and self.knowledge_representation
            is InvestigationCompletenessVerdict.COMPLETE
            and self.business_discovery_recall
            is InvestigationCompletenessVerdict.COMPLETE
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "query_result": self.query_result.value,
            "knowledge_representation": self.knowledge_representation.value,
            "business_discovery_recall": self.business_discovery_recall.value,
            "bounded_absence_allowed": self.bounded_absence_allowed,
            "missing_limitation_codes": self.missing_limitation_codes,
        }


@dataclass(frozen=True, slots=True)
class BoundedInvestigationTrace:
    question_digest: Digest
    need_ids: tuple[str, ...]
    session_id: StableId
    session_digest: Digest
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    snapshot_ids: tuple[StableId, ...]
    snapshot_bundle_digests: tuple[Digest, ...]
    budget: InvestigationBudget
    discovery_oracle: BusinessDiscoveryRecallOracle | None
    steps: tuple[InvestigationStep, ...]
    terminal_proposal: InvestigationProposal | None
    model_call_count: int
    terminal_status: InvestigationTerminalStatus
    terminal_reason: str
    completeness: InvestigationCompleteness
    total_query_bytes: int
    total_result_bytes: int
    support_item_count: int
    elapsed_milliseconds: int
    digest: Digest

    def _canonical_core(self) -> dict[str, object]:
        return {
            "question_digest": self.question_digest.value,
            "need_ids": self.need_ids,
            "session_id": self.session_id.value,
            "session_digest": self.session_digest.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "snapshot_ids": tuple(item.value for item in self.snapshot_ids),
            "snapshot_bundle_digests": tuple(
                item.value for item in self.snapshot_bundle_digests
            ),
            "budget": self.budget.canonical_value(),
            "discovery_oracle": (
                self.discovery_oracle.canonical_value()
                if self.discovery_oracle is not None
                else None
            ),
            "steps": tuple(item.canonical_value() for item in self.steps),
            "terminal_proposal": (
                self.terminal_proposal.canonical_value()
                if self.terminal_proposal is not None
                else None
            ),
            "model_call_count": self.model_call_count,
            "terminal_status": self.terminal_status.value,
            "terminal_reason": self.terminal_reason,
            "completeness": self.completeness.canonical_value(),
            "total_query_bytes": self.total_query_bytes,
            "total_result_bytes": self.total_result_bytes,
            "support_item_count": self.support_item_count,
            "elapsed_milliseconds": self.elapsed_milliseconds,
        }

    def canonical_value(self) -> dict[str, object]:
        return {**self._canonical_core(), "digest": self.digest.value}

    def result(self, result_id: StableId, result_digest: Digest) -> StructureViewResult:
        matches = tuple(
            result
            for step in self.steps
            for result in step.results
            if result.result_id == result_id and result.digest == result_digest
        )
        if len(matches) != 1:
            raise _invalid(
                "INVESTIGATION_RESULT_PROVENANCE_INVALID",
                "Entity Ref does not bind one earlier sealed investigation Result",
            )
        return matches[0]

    def require_valid(self) -> None:
        if self.discovery_oracle is not None:
            self.discovery_oracle.require_valid()
        if (
            not self.need_ids
            or len(set(self.need_ids)) != len(self.need_ids)
            or any(not isinstance(item, str) or not item for item in self.need_ids)
            or len(self.snapshot_ids) != len(self.snapshot_bundle_digests)
            or not self.snapshot_ids
            or len(self.steps) > self.budget.maximum_steps
            or not 0 <= self.elapsed_milliseconds
            <= self.budget.maximum_wall_time_milliseconds
        ):
            raise _invalid(
                "INVESTIGATION_TRACE_SHAPE_INVALID",
                "investigation trace has an invalid authority or budget shape",
            )
        for index, step in enumerate(self.steps, start=1):
            step.require_valid()
            if (
                step.proposal.step_index != index
                or step.proposal.trace_digest
                != _trace_prefix_digest(
                    question_digest=self.question_digest,
                    need_ids=self.need_ids,
                    session_id=self.session_id,
                    read_set_digest=self.read_set_digest,
                    ordered_bundle_digest=self.ordered_bundle_digest,
                    steps=self.steps[: index - 1],
                    model_call_count=index - 1,
                )
            ):
                raise _invalid(
                    "INVESTIGATION_TRACE_PREFIX_INVALID",
                    "investigation proposal does not bind its exact preceding trace prefix",
                )
            previous_result: object = None
            if index > 1:
                prior = self.steps[index - 2]
                previous_result = {
                    "operation": prior.proposal.operation.value,
                    "results": tuple(
                        item.canonical_value() for item in prior.results
                    ),
                    "evidence_requests": [
                        item.canonical_value()
                        for item in prior.proposal.evidence_requests
                    ],
                }
            scheduled_operation, scheduled_relation, scheduled_requests = (
                _scheduled_investigation_transition(
                    step_index=index,
                    previous_result=previous_result,
                )
            )
            if index == 1:
                scheduled_requests = step.proposal.evidence_requests
            if (
                step.proposal.operation is not scheduled_operation
                or step.proposal.evidence_requests != scheduled_requests
            ):
                raise _invalid(
                    "INVESTIGATION_TRACE_TRANSITION_INVALID",
                    "investigation trace violates its frozen evidence transition",
                )
            if scheduled_operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
                expected_direction, expected_predicate = _RELATION_INTENT_ARGUMENTS[
                    scheduled_relation
                ]
                if (
                    step.proposal.direction is not expected_direction
                    or step.proposal.predicate is not expected_predicate
                ):
                    raise _invalid(
                        "INVESTIGATION_TRACE_TRANSITION_INVALID",
                        "investigation trace relation does not match its evidence ledger",
                    )
        if self.terminal_proposal is not None:
            self.terminal_proposal.require_valid()
        if self.terminal_status is InvestigationTerminalStatus.FINISHED:
            scheduled_terminal: InvestigationOperation | None = None
            scheduled_requests: tuple[InvestigationEvidenceRequest, ...] = ()
            if self.steps:
                prior = self.steps[-1]
                terminal_previous_result = {
                    "operation": prior.proposal.operation.value,
                    "results": tuple(
                        item.canonical_value() for item in prior.results
                    ),
                    "evidence_requests": [
                        item.canonical_value()
                        for item in prior.proposal.evidence_requests
                    ],
                }
                scheduled_terminal, _, scheduled_requests = (
                    _scheduled_investigation_transition(
                        step_index=self.model_call_count,
                        previous_result=terminal_previous_result,
                    )
                )
            if (
                self.terminal_proposal is None
                or self.terminal_proposal.operation is not InvestigationOperation.FINISH
                or scheduled_terminal is not InvestigationOperation.FINISH
                or self.terminal_proposal.evidence_requests != scheduled_requests
                or len(self.steps) < 1
                or self.model_call_count != len(self.steps) + 1
                or self.terminal_proposal.step_index != self.model_call_count
                or self.terminal_proposal.trace_digest
                != _trace_prefix_digest(
                    question_digest=self.question_digest,
                    need_ids=self.need_ids,
                    session_id=self.session_id,
                    read_set_digest=self.read_set_digest,
                    ordered_bundle_digest=self.ordered_bundle_digest,
                    steps=self.steps,
                    model_call_count=len(self.steps),
                )
            ):
                raise _invalid(
                    "INVESTIGATION_FINISH_INVALID",
                    "finished investigation does not bind an executed step and one exact FINISH proposal",
                )
        elif self.terminal_status is InvestigationTerminalStatus.LIMITATION:
            if (
                self.terminal_proposal is not None
                or self.model_call_count != len(self.steps)
                or self.model_call_count != self.budget.maximum_model_calls
                or self.terminal_reason != "INVESTIGATION_BUDGET_EXHAUSTED"
            ):
                raise _invalid(
                    "INVESTIGATION_LIMITATION_INVALID",
                    "terminal investigation Limitation has an invalid shape",
                )
        else:
            raise _invalid(
                "INVESTIGATION_TRACE_NOT_TERMINAL",
                "only a terminal investigation trace may enter Draft and Review",
            )
        if (
            self.model_call_count < self.budget.minimum_model_calls
            or self.model_call_count > self.budget.maximum_model_calls
            or self.total_query_bytes != sum(item.query_bytes for item in self.steps)
            or self.total_result_bytes != sum(item.result_bytes for item in self.steps)
            or self.total_query_bytes > self.budget.maximum_total_query_bytes
            or self.total_result_bytes > self.budget.maximum_total_result_bytes
            or any(
                item.query_bytes > self.budget.maximum_query_bytes_per_step
                or item.result_bytes > self.budget.maximum_result_bytes_per_step
                for item in self.steps
            )
        ):
            raise _invalid(
                "INVESTIGATION_TRACE_BUDGET_INVALID",
                "investigation trace exceeds its frozen byte or call budget",
            )
        progress = tuple(item.progress_token for item in self.steps)
        support = {
            item.digest
            for step in self.steps
            for result in step.results
            for item in result.support_map
        }
        if (
            len(set(progress)) != len(progress)
            or self.support_item_count != len(support)
            or self.support_item_count > self.budget.maximum_support_items
            or self.completeness != _completeness(self.steps, self.discovery_oracle)
            or self.digest
            != digest_of(["BOUNDED_INVESTIGATION_TRACE@1", self._canonical_core()])
            or len(canonical_json_bytes(self.canonical_value()))
            > self.budget.maximum_trace_bytes
        ):
            raise _invalid(
                "INVESTIGATION_TRACE_INVALID",
                "investigation trace progress, support, completeness, or digest is invalid",
            )


class BoundedWorldModelInvestigationSession:
    """Platform-owned executor for one exact Question and Read Session."""

    def __init__(
        self,
        *,
        view: StructureViewService,
        question_digest: Digest,
        need_ids: Sequence[str],
        budget: InvestigationBudget | None = None,
        clock_ns: Callable[[], int] = monotonic_ns,
    ) -> None:
        normalized_need_ids = tuple(_text(item, "Need ID") for item in need_ids)
        if not normalized_need_ids or len(set(normalized_need_ids)) != len(
            normalized_need_ids
        ):
            raise _invalid(
                "INVESTIGATION_NEED_SET_INVALID",
                "investigation requires unique immutable Need IDs",
            )
        self._view = view
        self._question_digest = question_digest
        self._need_ids = normalized_need_ids
        self._budget = budget or InvestigationBudget()
        authority_oracles = _business_discovery_oracles(view)
        self._oracle = authority_oracles[0] if authority_oracles else None
        if self._oracle is not None:
            self._oracle.require_valid()
            bindings = dict(
                zip(view.snapshot_ids, view.snapshot_bundle_digests, strict=True)
            )
            if bindings.get(self._oracle.snapshot_id) != self._oracle.bundle_digest:
                raise _invalid(
                    "BUSINESS_DISCOVERY_ORACLE_READ_SET_MISMATCH",
                    "business discovery Oracle binds another Snapshot Bundle",
                )
        self._clock_ns = clock_ns
        self._started_ns = clock_ns()
        self._steps: list[InvestigationStep] = []
        self._model_call_count = 0
        self._failed = False
        self._terminal_proposal: InvestigationProposal | None = None
        self._terminal_status = InvestigationTerminalStatus.ACTIVE
        self._terminal_reason = "ACTIVE"

    @property
    def trace_digest(self) -> Digest:
        return _trace_prefix_digest(
            question_digest=self._question_digest,
            need_ids=self._need_ids,
            session_id=self._view.session_id,
            read_set_digest=self._view.read_set_digest,
            ordered_bundle_digest=self._view.ordered_bundle_digest,
            steps=tuple(self._steps),
            model_call_count=self._model_call_count,
        )

    @property
    def model_call_count(self) -> int:
        return self._model_call_count

    @property
    def steps(self) -> tuple[InvestigationStep, ...]:
        return tuple(self._steps)

    @property
    def current_completeness(self) -> InvestigationCompleteness:
        """Return the platform verdict for the currently sealed trace prefix."""

        return _completeness(tuple(self._steps), self._oracle)

    @property
    def terminal(self) -> bool:
        return (
            self._failed
            or self._terminal_status is not InvestigationTerminalStatus.ACTIVE
        )

    def submit(self, proposal: InvestigationProposal) -> InvestigationStep | None:
        if self.terminal:
            raise _invalid(
                "INVESTIGATION_ALREADY_TERMINAL",
                "terminal investigation cannot accept another proposal",
            )
        try:
            proposal.require_valid()
            expected_index = self._model_call_count + 1
            if (
                proposal.step_index != expected_index
                or proposal.trace_digest != self.trace_digest
            ):
                raise _invalid(
                    "INVESTIGATION_PROPOSAL_PREFIX_MISMATCH",
                    "investigation proposal does not bind the current exact trace prefix",
                )
            previous_result: object = None
            if self._steps:
                prior = self._steps[-1]
                previous_result = {
                    "operation": prior.proposal.operation.value,
                    "results": tuple(
                        item.canonical_value() for item in prior.results
                    ),
                    "evidence_requests": [
                        item.canonical_value()
                        for item in prior.proposal.evidence_requests
                    ],
                }
            scheduled_operation, scheduled_relation, scheduled_requests = (
                _scheduled_investigation_transition(
                    step_index=expected_index,
                    previous_result=previous_result,
                )
            )
            if expected_index == 1:
                scheduled_requests = proposal.evidence_requests
            if (
                proposal.operation is not scheduled_operation
                or proposal.evidence_requests != scheduled_requests
            ):
                raise _invalid(
                    "INVESTIGATION_TRANSITION_NOT_AUTHORIZED",
                    "investigation proposal is outside the frozen evidence transition",
                )
            if scheduled_operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
                expected_direction, expected_predicate = _RELATION_INTENT_ARGUMENTS[
                    scheduled_relation
                ]
                if (
                    proposal.direction is not expected_direction
                    or proposal.predicate is not expected_predicate
                ):
                    raise _invalid(
                        "INVESTIGATION_TRANSITION_NOT_AUTHORIZED",
                        "direct-neighborhood proposal does not match the frozen relation obligation",
                    )
            if expected_index > self._budget.maximum_model_calls:
                raise _invalid(
                    "INVESTIGATION_CALL_BUDGET_EXHAUSTED",
                    "investigation model-call budget is exhausted",
                )
            self._model_call_count = expected_index
            if proposal.operation is InvestigationOperation.FINISH:
                if not self._steps:
                    raise _invalid(
                        "INVESTIGATION_FINISH_TOO_EARLY",
                        "FINISH requires at least one executed investigation step",
                    )
                self._terminal_proposal = proposal
                self._terminal_status = InvestigationTerminalStatus.FINISHED
                self._terminal_reason = proposal.finish_reason or "FINISHED"
                return None
            if len(self._steps) >= self._budget.maximum_steps:
                raise _invalid(
                    "INVESTIGATION_STEP_BUDGET_EXHAUSTED",
                    "investigation execution-step budget is exhausted",
                )
            results = self._execute(proposal)
            step = InvestigationStep.create(proposal=proposal, results=results)
            if (
                step.query_bytes > self._budget.maximum_query_bytes_per_step
                or step.result_bytes > self._budget.maximum_result_bytes_per_step
                or sum(item.query_bytes for item in self._steps) + step.query_bytes
                > self._budget.maximum_total_query_bytes
                or sum(item.result_bytes for item in self._steps) + step.result_bytes
                > self._budget.maximum_total_result_bytes
            ):
                raise _invalid(
                    "INVESTIGATION_RESULT_BUDGET_EXHAUSTED",
                    "investigation query or result exceeds its frozen byte budget",
                )
            step.require_valid()
            if step.progress_token in {
                item.progress_token for item in self._steps
            }:
                raise _invalid(
                    "INVESTIGATION_CYCLE_DETECTED",
                    "investigation repeated an exact no-progress operation Result",
                )
            prospective_support = {
                item.digest
                for prior in (*self._steps, step)
                for result in prior.results
                for item in result.support_map
            }
            if len(prospective_support) > self._budget.maximum_support_items:
                raise _invalid(
                    "INVESTIGATION_SUPPORT_BUDGET_EXHAUSTED",
                    "investigation Support exceeds its frozen item budget",
                )
            prospective_steps = (*self._steps, step)
            if (
                len(canonical_json_bytes(self._active_value(prospective_steps)))
                > self._budget.maximum_trace_bytes
            ):
                raise _invalid(
                    "INVESTIGATION_TRACE_BUDGET_EXHAUSTED",
                    "investigation trace exceeds its frozen byte budget",
                )
            if (
                self._elapsed_milliseconds()
                > self._budget.maximum_wall_time_milliseconds
            ):
                raise _invalid(
                    "INVESTIGATION_WALL_TIME_EXHAUSTED",
                    "investigation exceeds its frozen wall-time budget",
                )
            self._steps.append(step)
            if self._model_call_count == self._budget.maximum_model_calls:
                self._terminal_status = InvestigationTerminalStatus.LIMITATION
                self._terminal_reason = "INVESTIGATION_BUDGET_EXHAUSTED"
            return step
        except Exception:
            self._failed = True
            raise

    def seal(self) -> BoundedInvestigationTrace:
        if self._failed:
            raise _invalid(
                "INVESTIGATION_FAILED",
                "failed investigation cannot be resumed or sealed for Draft",
            )
        if not self.terminal:
            raise _invalid(
                "INVESTIGATION_NOT_TERMINAL",
                "investigation trace cannot be sealed before FINISH or a terminal Limitation",
            )
        elapsed = self._elapsed_milliseconds()
        support = {
            item.digest
            for step in self._steps
            for result in step.results
            for item in result.support_map
        }
        completeness = _completeness(tuple(self._steps), self._oracle)
        provisional = BoundedInvestigationTrace(
            question_digest=self._question_digest,
            need_ids=self._need_ids,
            session_id=self._view.session_id,
            session_digest=self._view.read_session.digest,
            read_set_digest=self._view.read_set_digest,
            ordered_bundle_digest=self._view.ordered_bundle_digest,
            snapshot_ids=self._view.snapshot_ids,
            snapshot_bundle_digests=self._view.snapshot_bundle_digests,
            budget=self._budget,
            discovery_oracle=self._oracle,
            steps=tuple(self._steps),
            terminal_proposal=self._terminal_proposal,
            model_call_count=self._model_call_count,
            terminal_status=self._terminal_status,
            terminal_reason=self._terminal_reason,
            completeness=completeness,
            total_query_bytes=sum(item.query_bytes for item in self._steps),
            total_result_bytes=sum(item.result_bytes for item in self._steps),
            support_item_count=len(support),
            elapsed_milliseconds=elapsed,
            digest=Digest("sha256:" + "0" * 64),
        )
        trace = BoundedInvestigationTrace(
            **{
                name: getattr(provisional, name)
                for name in provisional.__dataclass_fields__
                if name != "digest"
            },
            digest=digest_of(
                ["BOUNDED_INVESTIGATION_TRACE@1", provisional._canonical_core()]
            ),
        )
        trace.require_valid()
        return trace

    def _execute(
        self, proposal: InvestigationProposal
    ) -> tuple[StructureViewResult, ...]:
        operation = proposal.operation
        if operation is InvestigationOperation.IMPLEMENTATION_CANDIDATES:
            assert proposal.snapshot_id is not None
            assert proposal.limit is not None
            return (
                self._view.implementation_candidates(
                    snapshot_id=proposal.snapshot_id,
                    search_terms=proposal.search_terms,
                    limit=proposal.limit,
                ),
            )
        if operation is InvestigationOperation.METHOD_IMPLEMENTATIONS:
            assert proposal.candidate_result_id is not None
            assert proposal.candidate_result_digest is not None
            candidate = self._prior_result(
                proposal.candidate_result_id,
                proposal.candidate_result_digest,
            )
            if (
                candidate.operation
                is not StructureViewOperation.IMPLEMENTATION_CANDIDATES
                or candidate.truncated
                or candidate.payload.get("total")
                != candidate.payload.get("returned")
            ):
                raise _invalid(
                    "INVESTIGATION_METHOD_BATCH_CANDIDATE_INVALID",
                    "method batch requires one complete sealed candidate Result",
                )
            candidate_order = tuple(
                (
                    StableId(item["method"]["root_id"]),
                    StableId(item["method"]["state_id"]),
                )
                for item in candidate.payload["candidates"]
            )
            requested = tuple(
                (item.entity_root_id, item.entity_state_id)
                for item in proposal.method_refs
            )
            if (
                any(
                    item.source_result_id != candidate.result_id
                    or item.source_result_digest != candidate.digest
                    for item in proposal.method_refs
                )
                or any(item not in candidate_order for item in requested)
                or tuple(item for item in candidate_order if item in requested)
                != requested
            ):
                raise _invalid(
                    "INVESTIGATION_METHOD_REF_PROVENANCE_INVALID",
                    "method batch Ref is forged, reordered, or absent from the candidate Result",
                )
            return tuple(
                self._view.method_implementation(
                    method=StructureEntityArgument.from_result_member(
                        candidate,
                        entity_root_id=item.entity_root_id,
                        entity_state_id=item.entity_state_id,
                    )
                )
                for item in proposal.method_refs
            )
        arguments = tuple(self._argument(item) for item in proposal.entity_refs)
        if operation is InvestigationOperation.DECLARED_METHOD_INVENTORY:
            return (self._view.declared_method_inventory(java_type=arguments[0]),)
        if operation is InvestigationOperation.DIRECT_NEIGHBORHOOD:
            assert proposal.direction is not None
            return (
                self._view.direct_neighborhood(
                    entity=arguments[0],
                    direction=proposal.direction,
                    predicate=proposal.predicate,
                ),
            )
        if operation is InvestigationOperation.PATH_EXISTS:
            assert proposal.predicate is not None
            assert proposal.max_depth is not None
            assert proposal.max_expansions is not None
            return (
                self._view.path_exists(
                    source=arguments[0],
                    target=arguments[1],
                    predicate=proposal.predicate,
                    max_depth=proposal.max_depth,
                    max_expansions=proposal.max_expansions,
                ),
            )
        if operation is InvestigationOperation.ALL_SIMPLE_PATHS:
            assert proposal.predicate is not None
            assert proposal.max_depth is not None
            assert proposal.max_paths is not None
            assert proposal.max_expansions is not None
            return (
                self._view.all_simple_paths(
                    source=arguments[0],
                    target=arguments[1],
                    predicate=proposal.predicate,
                    max_depth=proposal.max_depth,
                    max_paths=proposal.max_paths,
                    max_expansions=proposal.max_expansions,
                ),
            )
        raise _invalid(
            "INVESTIGATION_OPERATION_INVALID",
            "investigation operation is not executable",
        )

    def _prior_result(
        self, result_id: StableId, result_digest: Digest
    ) -> StructureViewResult:
        matches = tuple(
            result
            for step in self._steps
            for result in step.results
            if result.result_id == result_id and result.digest == result_digest
        )
        if len(matches) != 1:
            raise _invalid(
                "INVESTIGATION_RESULT_PROVENANCE_INVALID",
                "operation does not bind one earlier sealed Result",
            )
        return matches[0]

    def _argument(self, value: InvestigationEntityRef) -> StructureEntityArgument:
        result = self._prior_result(
            value.source_result_id, value.source_result_digest
        )
        return StructureEntityArgument.from_result_member(
            result,
            entity_root_id=value.entity_root_id,
            entity_state_id=value.entity_state_id,
        )

    def _active_value(
        self,
        steps: Sequence[InvestigationStep] | None = None,
    ) -> dict[str, object]:
        normalized_steps = tuple(self._steps if steps is None else steps)
        return {
            "trace_digest": _trace_prefix_digest(
                question_digest=self._question_digest,
                need_ids=self._need_ids,
                session_id=self._view.session_id,
                read_set_digest=self._view.read_set_digest,
                ordered_bundle_digest=self._view.ordered_bundle_digest,
                steps=normalized_steps,
                model_call_count=self._model_call_count,
            ).value,
            "model_call_count": self._model_call_count,
            "steps": tuple(item.canonical_value() for item in normalized_steps),
        }

    def _elapsed_milliseconds(self) -> int:
        return max(0, (self._clock_ns() - self._started_ns) // 1_000_000)


def validate_bounded_investigation_trace(
    trace: BoundedInvestigationTrace,
    *,
    view: StructureViewService,
    question_digest: Digest,
) -> None:
    """Verify trace authority and replay every typed Result against the Bundle."""

    trace.require_valid()
    authority_oracles = _business_discovery_oracles(view)
    expected_oracle = authority_oracles[0] if authority_oracles else None
    if (
        trace.question_digest != question_digest
        or trace.session_id != view.session_id
        or trace.session_digest != view.read_session.digest
        or trace.read_set_digest != view.read_set_digest
        or trace.ordered_bundle_digest != view.ordered_bundle_digest
        or trace.snapshot_ids != view.snapshot_ids
        or trace.snapshot_bundle_digests != view.snapshot_bundle_digests
        or trace.discovery_oracle != expected_oracle
    ):
        raise _invalid(
            "INVESTIGATION_TRACE_AUTHORITY_MISMATCH",
            "investigation trace binds another Question or Read Authority",
        )
    prior: list[StructureViewResult] = []
    for step in trace.steps:
        replay = _execute_against_prior(view, step.proposal, tuple(prior))
        if replay != step.results:
            raise _invalid(
                "INVESTIGATION_RESULT_REPLAY_MISMATCH",
                "investigation Result differs from exact Bundle replay",
            )
        prior.extend(replay)


def _business_discovery_oracles(
    view: StructureViewService,
) -> tuple[BusinessDiscoveryRecallOracle, ...]:
    authority_bindings = tuple(
        item
        for item in view.business_discovery_recall_bindings
        if item.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF
        and item.discovery_contract_ref
        == JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
    )
    authority_oracles = tuple(
        BusinessDiscoveryRecallOracle.create(
            oracle_ref=item.oracle_ref,
            oracle_result_digest=item.oracle_result_digest,
            authority_binding_digest=item.digest,
            discovery_contract_ref=item.discovery_contract_ref,
            snapshot_id=item.snapshot_id,
            bundle_digest=item.snapshot_bundle_digest,
            counterexample_classes=item.counterexample_classes,
            verdict=InvestigationCompletenessVerdict(item.verdict.value),
        )
        for item in authority_bindings
    )
    if len(authority_oracles) > 1:
        raise _invalid(
            "BUSINESS_DISCOVERY_ORACLE_AMBIGUOUS",
            "bounded source-semantics investigation requires at most one recall authority",
        )
    return authority_oracles


def _execute_against_prior(
    view: StructureViewService,
    proposal: InvestigationProposal,
    prior: tuple[StructureViewResult, ...],
) -> tuple[StructureViewResult, ...]:
    """Replay helper using a minimal session-shaped prior-result authority."""

    class _ReplaySession:
        _view = view
        _steps = ()

        def _prior_result(self, result_id, result_digest):
            matches = tuple(
                item
                for item in prior
                if item.result_id == result_id and item.digest == result_digest
            )
            if len(matches) != 1:
                raise _invalid(
                    "INVESTIGATION_RESULT_PROVENANCE_INVALID",
                    "replay operation does not bind one earlier Result",
                )
            return matches[0]

        def _argument(self, value):
            result = self._prior_result(
                value.source_result_id, value.source_result_digest
            )
            return StructureEntityArgument.from_result_member(
                result,
                entity_root_id=value.entity_root_id,
                entity_state_id=value.entity_state_id,
            )

    return BoundedWorldModelInvestigationSession._execute(  # type: ignore[arg-type]
        _ReplaySession(), proposal
    )


def _trace_prefix_digest(
    *,
    question_digest: Digest,
    need_ids: tuple[str, ...],
    session_id: StableId,
    read_set_digest: Digest,
    ordered_bundle_digest: Digest,
    steps: Sequence[InvestigationStep],
    model_call_count: int,
) -> Digest:
    return digest_of(
        [
            "BOUNDED_INVESTIGATION_TRACE_PREFIX@1",
            {
                "question_digest": question_digest.value,
                "need_ids": need_ids,
                "session_id": session_id.value,
                "read_set_digest": read_set_digest.value,
                "ordered_bundle_digest": ordered_bundle_digest.value,
                "steps": tuple(item.canonical_value() for item in steps),
                "model_call_count": model_call_count,
            },
        ]
    )


def _completeness(
    steps: Sequence[InvestigationStep],
    oracle: BusinessDiscoveryRecallOracle | None,
) -> InvestigationCompleteness:
    results = tuple(result for step in steps for result in step.results)
    query_complete = bool(results) and all(
        not result.truncated
        and (
            result.operation is not StructureViewOperation.IMPLEMENTATION_CANDIDATES
            or (
                result.payload.get("total") == result.payload.get("returned")
                and result.payload.get("returned")
                == result.payload.get("candidate_count")
                and result.payload.get("next_cursor") is None
            )
        )
        for result in results
    )
    representation_complete = bool(results) and all(
        all(item.get("completeness") == "COMPLETE" for item in result.coverage)
        and not any("COVERAGE_INSUFFICIENT" in item for item in result.limitations)
        and (
            result.operation is not StructureViewOperation.METHOD_IMPLEMENTATION
            or (
                result.payload.get("method_disposition") == "SEMANTICS_COMPLETE"
                and result.payload.get("implementation_semantics_completeness")
                == "COMPLETE"
            )
        )
        for result in results
    )
    discovery_complete = (
        oracle is not None
        and oracle.verdict is InvestigationCompletenessVerdict.COMPLETE
    )
    missing: list[str] = []
    if not query_complete:
        missing.append("QUERY_RESULT_COMPLETENESS_UNPROVEN")
    if not representation_complete:
        missing.append("KNOWLEDGE_REPRESENTATION_COVERAGE_UNPROVEN")
    if not discovery_complete:
        missing.append("BUSINESS_DISCOVERY_RECALL_UNPROVEN")
    return InvestigationCompleteness(
        query_result=(
            InvestigationCompletenessVerdict.COMPLETE
            if query_complete
            else InvestigationCompletenessVerdict.UNKNOWN
        ),
        knowledge_representation=(
            InvestigationCompletenessVerdict.COMPLETE
            if representation_complete
            else InvestigationCompletenessVerdict.UNKNOWN
        ),
        business_discovery_recall=(
            InvestigationCompletenessVerdict.COMPLETE
            if discovery_complete
            else InvestigationCompletenessVerdict.UNKNOWN
        ),
        missing_limitation_codes=tuple(missing),
    )


def _entity_refs(value: object, label: str) -> tuple[InvestigationEntityRef, ...]:
    if not isinstance(value, (tuple, list)):
        raise _invalid(
            "INVESTIGATION_ENTITY_REF_LIST_INVALID",
            f"{label} must be an array",
        )
    return tuple(InvestigationEntityRef.from_mapping(item) for item in value)


def _text_sequence(value: object, label: str, *, maximum: int) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or len(value) > maximum:
        raise _invalid(
            "INVESTIGATION_TEXT_LIST_INVALID",
            f"{label} is outside its closed bound",
        )
    normalized = tuple(_text(item, label) for item in value)
    if len(set(item.casefold() for item in normalized)) != len(normalized):
        raise _invalid(
            "INVESTIGATION_TEXT_LIST_DUPLICATE",
            f"{label} contains duplicate normalized values",
        )
    return normalized


def _deduplicated_text_sequence(
    value: object, label: str, *, maximum: int
) -> tuple[str, ...]:
    """Canonicalize harmless model repetition before typed validation.

    The raw list remains bounded, and the first spelling/order wins.  This is
    appropriate only for model-owned search vocabulary; authority references
    and typed proposal collections continue to reject duplicates.
    """

    if not isinstance(value, (tuple, list)) or len(value) > maximum:
        raise _invalid(
            "INVESTIGATION_TEXT_LIST_INVALID",
            f"{label} is outside its closed bound",
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in value:
        item = _text(raw, label)
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return tuple(normalized)


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 32_768
        or "\x00" in value
    ):
        raise _invalid(
            "INVESTIGATION_TEXT_INVALID",
            f"{label} must be canonical non-empty text",
        )
    return value


def _stable_id(value: object, label: str) -> StableId:
    if not isinstance(value, str):
        raise _invalid(
            "INVESTIGATION_STABLE_ID_INVALID",
            f"{label} must be a stable ID string",
        )
    try:
        return StableId(value)
    except (TypeError, ValueError) as exc:
        raise _invalid(
            "INVESTIGATION_STABLE_ID_INVALID",
            f"{label} is invalid",
        ) from exc


def _optional_stable_id(value: object, label: str) -> StableId | None:
    return None if value is None else _stable_id(value, label)


def _digest(value: object, label: str) -> Digest:
    if not isinstance(value, str):
        raise _invalid(
            "INVESTIGATION_DIGEST_INVALID",
            f"{label} must be a digest string",
        )
    try:
        return Digest(value)
    except (TypeError, ValueError) as exc:
        raise _invalid(
            "INVESTIGATION_DIGEST_INVALID",
            f"{label} is invalid",
        ) from exc


def _optional_digest(value: object, label: str) -> Digest | None:
    return None if value is None else _digest(value, label)


def _optional_positive_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 1 <= value <= 100_000:
        raise _invalid(
            "INVESTIGATION_INTEGER_INVALID",
            f"{label} must be an integer from 1 through 100000",
        )
    return value


def _optional_enum(enum_type, value: object, label: str):
    if value is None:
        return None
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise _invalid(
            "INVESTIGATION_ENUM_INVALID",
            f"{label} is invalid",
        ) from exc


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )
