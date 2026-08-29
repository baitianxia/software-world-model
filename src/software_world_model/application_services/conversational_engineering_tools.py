"""Trusted World Model and Source tools for the conversational Agent.

This adapter reuses the existing Engineering QA cognition projector, Source
Broker, and Retrieval Worker.  The Agent supplies semantic intent only.  It
never receives a repository handle or path authority, and reads can only use
opaque locator references issued by a prior Broker-authorized search.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import PurePosixPath
from threading import Lock
from typing import Mapping, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)

from .conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLedgerEntryReceipt,
    EngineeringAgentToolAuthorityKind,
    EngineeringAgentToolAuthorityReceipt,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolEvidence,
    EngineeringAgentToolOperation,
    EngineeringAgentToolRequest,
    EngineeringAgentToolResult,
)
from .engineering_conversation import (
    EngineeringTurnExecutionRequest,
    RuntimeCapabilityStatus,
)
from .engineering_question_answering import (
    BrokerDecisionStatus,
    CompiledSourceOperation,
    EngineeringEvidenceClass,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    EngineeringQuestionResourceUsage,
    EvidenceLedger,
    InvestigationKind,
    InvestigationOperation,
    InvestigationStepProposal,
    LedgerEntryKind,
    RetrievalItem,
    RetrievalResult,
    RetrievalStatus,
    RetrievalWorker,
    SourceBroker,
    SourceReadOperation,
    WorldModelCognitionContext,
    WorldModelCognitionProjector,
)


_OBSERVATION_PAYLOAD_LIMIT = 240_000


@dataclass(frozen=True, slots=True)
class EngineeringAgentEvidenceToolConfiguration:
    project_name: str
    response_language: str
    repository_id: StableId
    binding_id: StableId
    repository_revision: str
    source_profile_ref: str
    source_profile_digest: Digest
    world_model_read_authority_digest: Digest
    source_allowlist: tuple[str, ...]
    excluded_source_paths: tuple[str, ...]
    provider_disclosure_policy: str
    limits: EngineeringQuestionResourceLimits
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        project_name: str,
        response_language: str,
        repository_id: StableId,
        binding_id: StableId,
        repository_revision: str,
        source_profile_ref: str,
        source_profile_digest: Digest,
        world_model_read_authority_digest: Digest,
        source_allowlist: Sequence[str],
        excluded_source_paths: Sequence[str] = ("src/main/resources",),
        provider_disclosure_policy: str = "NO_EXTERNAL_DISCLOSURE",
        limits: EngineeringQuestionResourceLimits | None = None,
    ) -> "EngineeringAgentEvidenceToolConfiguration":
        validated = EngineeringQuestionRequest.create(
            request_ref="engineering-agent-tool-configuration-validation",
            original_question="engineering Agent tool configuration validation",
            response_language=response_language,
            repository_id=repository_id,
            binding_id=binding_id,
            repository_revision=repository_revision,
            source_profile_ref=source_profile_ref,
            source_profile_digest=source_profile_digest,
            world_model_read_authority_digest=world_model_read_authority_digest,
            source_allowlist=source_allowlist,
            registered_operations=(SourceReadOperation.SEARCH, SourceReadOperation.READ),
            provider_disclosure_policy=provider_disclosure_policy,
            limits=limits,
        )
        normalized_exclusions = tuple(
            sorted({_relative_path(item) for item in excluded_source_paths})
        )
        if "src/main/resources" not in normalized_exclusions:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering Agent tools must keep src/main/resources excluded",
            )
        if any(
            _contains_path(allowed, excluded)
            for allowed in validated.source_allowlist
            for excluded in normalized_exclusions
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering Agent Source allowlist contains an excluded path",
            )
        project_name = _reference(project_name, "Engineering Agent project name")
        core = {
            "schema": "ENGINEERING_AGENT_EVIDENCE_TOOL_CONFIGURATION@1",
            "project_name": project_name,
            "response_language": validated.response_language,
            "repository_id": validated.repository_id.value,
            "binding_id": validated.binding_id.value,
            "repository_revision": validated.repository_revision,
            "source_profile_ref": validated.source_profile_ref,
            "source_profile_digest": validated.source_profile_digest.value,
            "world_model_read_authority_digest": (
                validated.world_model_read_authority_digest.value
            ),
            "source_allowlist": validated.source_allowlist,
            "excluded_source_paths": normalized_exclusions,
            "provider_disclosure_policy": validated.provider_disclosure_policy,
            "limits_digest": validated.limits.digest.value,
        }
        return cls(
            project_name=project_name,
            response_language=validated.response_language,
            repository_id=validated.repository_id,
            binding_id=validated.binding_id,
            repository_revision=validated.repository_revision,
            source_profile_ref=validated.source_profile_ref,
            source_profile_digest=validated.source_profile_digest,
            world_model_read_authority_digest=(
                validated.world_model_read_authority_digest
            ),
            source_allowlist=validated.source_allowlist,
            excluded_source_paths=normalized_exclusions,
            provider_disclosure_policy=validated.provider_disclosure_policy,
            limits=validated.limits,
            digest=digest_of(core),
        )

    def request_for(self, tool_request: EngineeringAgentToolRequest) -> EngineeringQuestionRequest:
        return EngineeringQuestionRequest.create(
            request_ref=tool_request.turn_request.turn_id.value,
            original_question=tool_request.turn_request.user_message.content,
            response_language=self.response_language,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.repository_revision,
            source_profile_ref=self.source_profile_ref,
            source_profile_digest=self.source_profile_digest,
            world_model_read_authority_digest=self.world_model_read_authority_digest,
            source_allowlist=self.source_allowlist,
            registered_operations=(SourceReadOperation.SEARCH, SourceReadOperation.READ),
            provider_disclosure_policy=self.provider_disclosure_policy,
            limits=self.limits,
        )


@dataclass(slots=True)
class _TurnToolState:
    turn_request: EngineeringTurnExecutionRequest
    evidence_request: EngineeringQuestionRequest
    cognition: WorldModelCognitionContext
    ledger: EvidenceLedger
    attempt_id: StableId
    role_context_id: StableId
    locator_catalog: dict[StableId, RetrievalItem] = field(default_factory=dict)
    usage: EngineeringQuestionResourceUsage = field(
        default_factory=EngineeringQuestionResourceUsage
    )
    next_step_index: int = 1
    progress_digests: set[Digest] = field(default_factory=set)
    world_model_item_digests: set[Digest] = field(default_factory=set)
    world_model_receipt_recorded: bool = False
    lock: Lock = field(default_factory=Lock)


class EngineeringAgentEvidenceToolAdapter:
    """Execute bounded Agent tool requests through existing trusted assets."""

    def __init__(
        self,
        *,
        configuration: EngineeringAgentEvidenceToolConfiguration,
        cognition_projector: WorldModelCognitionProjector,
        source_broker: SourceBroker,
        retrieval_worker: RetrievalWorker,
        maximum_retained_turns: int = 1_024,
    ) -> None:
        if type(maximum_retained_turns) is not int or maximum_retained_turns < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "retained tool Turn limit must be a positive integer",
            )
        self._configuration = configuration
        self._cognition_projector = cognition_projector
        self._source_broker = source_broker
        self._retrieval_worker = retrieval_worker
        self._maximum_retained_turns = maximum_retained_turns
        self._states: dict[StableId, _TurnToolState] = {}
        self._states_lock = Lock()

    def execute(self, request: EngineeringAgentToolRequest) -> EngineeringAgentToolResult:
        self._validate_tool_request(request)
        state = self._state_for(request)
        with state.lock:
            if request.action.operation is EngineeringAgentToolOperation.WORLD_MODEL_QUERY:
                return self._world_model(request=request, state=state)
            if request.action.operation in {
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            }:
                return self._source(request=request, state=state)
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Agent requested an operation outside the evidence tool adapter catalog",
        )

    def _validate_tool_request(self, request: EngineeringAgentToolRequest) -> None:
        action = request.action
        expected_action = EngineeringAgentToolActionProposal.create(
            operation=action.operation,
            arguments=action.arguments,
            evidence_need=action.evidence_need,
        )
        turn = request.turn_request
        expected_digest = digest_of(
            {
                "schema": "ENGINEERING_AGENT_TOOL_REQUEST@1",
                "tool_request_id": request.tool_request_id.value,
                "turn_request_digest": request.turn_request_digest.value,
                "binding_digest": request.binding_digest.value,
                "work_state_digest": request.work_state_digest.value,
                "action_digest": action.digest.value,
            }
        )
        if (
            action != expected_action
            or request.digest != expected_digest
            or turn.request_digest != request.turn_request_digest
            or turn.binding.digest != request.binding_digest
            or turn.snapshot_before.conversation.binding_digest
            != request.binding_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent evidence tool request identity is invalid",
            )
        binding = turn.binding
        configuration = self._configuration
        if (
            binding.project_name != configuration.project_name
            or binding.repository_revision != configuration.repository_revision
            or binding.world_model_status is not RuntimeCapabilityStatus.READY
            or binding.world_model_authority_digest
            != configuration.world_model_read_authority_digest
            or binding.source_access_status is not RuntimeCapabilityStatus.READY
            or binding.source_profile_ref != configuration.source_profile_ref
            or not set(configuration.excluded_source_paths).issubset(
                binding.excluded_source_paths
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent evidence tools do not bind the current Chat configuration",
            )

    def _state_for(self, request: EngineeringAgentToolRequest) -> _TurnToolState:
        turn_id = request.turn_request.turn_id
        with self._states_lock:
            current = self._states.get(turn_id)
            if current is not None:
                if current.turn_request != request.turn_request:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "retained tool state binds a different Turn request",
                    )
                return current
            if len(self._states) >= self._maximum_retained_turns:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "retained Engineering Agent tool Turn fuse is exhausted",
                )
            evidence_request = self._configuration.request_for(request)
            self._source_broker.registered_evidence_classes(
                request=evidence_request
            )
            cognition = self._cognition_projector.project(
                request=evidence_request
            )
            if (
                cognition.request_digest != evidence_request.digest
                or cognition.read_authority_digest
                != evidence_request.world_model_read_authority_digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "World Model cognition does not bind the derived Turn request",
                )
            ledger = EvidenceLedger.start(
                request=evidence_request,
                cognition=cognition,
            )
            state = _TurnToolState(
                turn_request=request.turn_request,
                evidence_request=evidence_request,
                cognition=cognition,
                ledger=ledger,
                attempt_id=_derived_id(
                    "agent_investigation", evidence_request.digest.value
                ),
                role_context_id=_derived_id(
                    "agent_tool_context", evidence_request.digest.value
                ),
                usage=EngineeringQuestionResourceUsage(
                    world_model_bytes=len(
                        canonical_json_bytes(cognition.model_view())
                    )
                ),
            )
            self._states[turn_id] = state
            return state

    def _world_model(
        self,
        *,
        request: EngineeringAgentToolRequest,
        state: _TurnToolState,
    ) -> EngineeringAgentToolResult:
        arguments = dict(request.action.arguments)
        if set(arguments) == {"query"} and len(arguments) == 1:
            query = arguments["query"]
        elif not arguments:
            query = _compile_world_model_semantic_query(request)
        else:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "World Model query accepts either one semantic query or Application compilation",
            )
        project_for_query = getattr(
            self._cognition_projector, "project_for_query", None
        )
        if callable(project_for_query):
            cognition = project_for_query(
                request=state.evidence_request,
                query=query,
            )
            if (
                cognition.request_digest != state.evidence_request.digest
                or cognition.read_authority_digest
                != state.evidence_request.world_model_read_authority_digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "query-relevant cognition does not bind the current Turn authority",
                )
            if cognition.digest != state.cognition.digest:
                state.ledger = state.ledger.append(
                    kind=LedgerEntryKind.COGNITION_CONTEXT,
                    subject_id=cognition.cognition_context_id.value,
                    subject_digest=cognition.digest,
                    references=(state.ledger.entries[-1].entry_id.value,),
                    details={
                        "alignment": cognition.alignment.value,
                        "relevance_query_digest": digest_of(
                            ["ENGINEERING_COGNITION_RELEVANCE_QUERY@1", query]
                        ).value,
                    },
                    maximum_bytes=state.evidence_request.limits.maximum_ledger_bytes,
                )
                state.cognition = cognition
                state.usage = replace(
                    state.usage,
                    world_model_bytes=len(
                        canonical_json_bytes(cognition.model_view())
                    ),
                )
        else:
            cognition = state.cognition
        if not state.world_model_receipt_recorded:
            state.ledger = _append_resource_receipt(
                request=state.evidence_request,
                ledger=state.ledger,
                usage=state.usage,
            )
            state.world_model_receipt_recorded = True
        current_items = tuple(cognition.items)
        novel_items = tuple(
            item
            for item in current_items
            if item.digest not in state.world_model_item_digests
        )
        repeated_item_count = len(current_items) - len(novel_items)
        citations = tuple(
            EngineeringAgentCitation.create(
                citation_ref=item.item_id.value,
                evidence_class=EngineeringEvidenceClass.WORLD_MODEL.value,
                source_revision=item.source_revision,
                locator=item.locator,
                modality=item.modality,
                content_digest=digest_of(item.statement),
            )
            for item in current_items
        )
        novel_citation_refs = tuple(item.item_id.value for item in novel_items)
        receipt = self._receipt(
            request=request,
            state=state,
            authority_kind=EngineeringAgentToolAuthorityKind.WORLD_MODEL,
            evidence_digest=cognition.digest,
            citations=citations,
        )
        fresh_context = cognition.digest not in state.progress_digests
        state.progress_digests.add(cognition.digest)
        evidence: list[EngineeringAgentToolEvidence] = []
        if novel_items and cognition.alignment.value == "ALIGNED":
            payload = {
                "schema": "ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@2",
                "query": query,
                "cognition_context_id": cognition.cognition_context_id.value,
                "cognition_context_digest": cognition.digest.value,
                "source_revision": cognition.source_revision,
                "projection": {
                    "kind": "CURRENT_TURN_NOVEL_COGNITION_ITEMS",
                    "current_context_item_count": len(current_items),
                    "novel_item_count": len(novel_items),
                    "previously_observed_item_count": repeated_item_count,
                },
                "dimensions": [
                    item.model_view(alignment=cognition.alignment)
                    for item in novel_items
                ],
                "coverage": list(cognition.coverage),
            }
            content = _payload(payload)
            if content is not None:
                evidence.append(
                    EngineeringAgentToolEvidence.create(
                        tool_request_digest=request.digest,
                        result_ref=f"{cognition.cognition_context_id.value}-support",
                        content=content,
                        disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
                        progress=fresh_context,
                        citation_refs=novel_citation_refs,
                        authority_receipt=receipt,
                    )
                )
                state.world_model_item_digests.update(
                    item.digest for item in novel_items
                )
        boundary_reasons = []
        if cognition.alignment.value != "ALIGNED":
            boundary_reasons.append("WORLD_MODEL_REVISION_UNALIGNED")
        if not current_items:
            boundary_reasons.append("WORLD_MODEL_HAS_NO_SUPPORTED_ITEMS")
        if cognition.conflicts:
            boundary_reasons.append("WORLD_MODEL_CONFLICT_REPORTED")
        if cognition.unknowns:
            boundary_reasons.append("WORLD_MODEL_UNKNOWN_REPORTED")
        if (
            not evidence
            and current_items
            and cognition.alignment.value == "ALIGNED"
        ):
            boundary_reasons.append(
                "WORLD_MODEL_HAS_NO_NEW_SUPPORTED_ITEMS"
                if not novel_items
                else "WORLD_MODEL_OBSERVATION_BYTE_LIMIT"
            )
        if boundary_reasons:
            boundary_progress = fresh_context and boundary_reasons != [
                "WORLD_MODEL_HAS_NO_NEW_SUPPORTED_ITEMS"
            ]
            evidence.append(
                EngineeringAgentToolEvidence.create(
                    tool_request_digest=request.digest,
                    result_ref=f"{cognition.cognition_context_id.value}-boundary",
                    content=_required_payload(
                        {
                            "schema": "ENGINEERING_AGENT_WORLD_MODEL_BOUNDARY@1",
                            "query": query,
                            "cognition_context_id": (
                                cognition.cognition_context_id.value
                            ),
                            "cognition_context_digest": cognition.digest.value,
                            "source_revision": cognition.source_revision,
                            "alignment": cognition.alignment.value,
                            "reasons": boundary_reasons,
                            "coverage": list(cognition.coverage),
                            "conflicts": list(cognition.conflicts),
                            "unknowns": list(cognition.unknowns),
                        }
                    ),
                    disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
                    progress=boundary_progress,
                    authority_receipt=receipt,
                )
            )
        return EngineeringAgentToolResult.create_many(
            tool_request_digest=request.digest,
            evidence=evidence,
        )

    def _source(
        self,
        *,
        request: EngineeringAgentToolRequest,
        state: _TurnToolState,
    ) -> EngineeringAgentToolResult:
        operation = request.action.operation
        if operation is EngineeringAgentToolOperation.SOURCE_SEARCH:
            arguments = _arguments(request, expected=("evidence_class", "query"))
            try:
                evidence_class = EngineeringEvidenceClass(
                    arguments["evidence_class"]
                )
            except ValueError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "Source search evidence class is not registered",
                ) from exc
            proposal_operation = InvestigationOperation.SEARCH
            query: str | None = arguments["query"]
            locator_reference: StableId | None = None
        else:
            arguments = _arguments(request, expected=("locator_reference",))
            try:
                locator_reference = StableId(arguments["locator_reference"])
            except ValueError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "Source read locator reference is malformed",
                ) from exc
            locator = state.locator_catalog.get(locator_reference)
            if locator is None:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Source read requires a locator issued by this Turn Ledger",
                )
            evidence_class = locator.evidence_class
            proposal_operation = InvestigationOperation.READ
            query = None

        pre_proposal_ledger = state.ledger
        proposal = InvestigationStepProposal.create(
            investigation_kind=InvestigationKind.INITIAL,
            attempt_id=state.attempt_id,
            role_context_id=state.role_context_id,
            request_digest=state.evidence_request.digest,
            step_index=state.next_step_index,
            ledger_id=pre_proposal_ledger.ledger_id,
            ledger_generation=pre_proposal_ledger.generation,
            ledger_revision=len(pre_proposal_ledger.entries),
            ledger_prefix_digest=pre_proposal_ledger.prefix_digest,
            operation=proposal_operation,
            checklist_item_ids=("agent-evidence-need",),
            evidence_class=evidence_class,
            query=query,
            locator_reference=locator_reference,
            basis_entry_ids=(pre_proposal_ledger.entries[-1].entry_id,),
            unknown_to_reduce=request.action.evidence_need,
        )
        compilation = self._source_broker.compile(
            request=state.evidence_request,
            proposal=proposal,
            ledger=pre_proposal_ledger,
            locator_catalog=state.locator_catalog,
            usage=state.usage,
        )
        state.next_step_index += 1
        proposal_details = {
            "investigation_kind": proposal.investigation_kind.value,
            "attempt_id": proposal.attempt_id.value,
            "operation": proposal.operation.value,
            "step_index": str(proposal.step_index),
            "evidence_class": evidence_class.value,
        }
        if query is not None:
            proposal_details["query"] = query
        if locator_reference is not None:
            proposal_details["locator_reference"] = locator_reference.value
        state.ledger = state.ledger.append(
            kind=LedgerEntryKind.INVESTIGATION_PROPOSAL,
            subject_id=proposal.proposal_id.value,
            subject_digest=proposal.digest,
            references=tuple(item.value for item in proposal.basis_entry_ids),
            details=proposal_details,
            maximum_bytes=state.evidence_request.limits.maximum_ledger_bytes,
        )
        decision = compilation.decision
        state.ledger = state.ledger.append(
            kind=LedgerEntryKind.BROKER_DECISION,
            subject_id=decision.decision_id.value,
            subject_digest=decision.digest,
            references=(proposal.proposal_id.value,),
            details={
                "status": decision.status.value,
                "reason": decision.reason_code,
            },
            maximum_bytes=state.evidence_request.limits.maximum_ledger_bytes,
        )
        if decision.status is BrokerDecisionStatus.REJECTED:
            receipt = self._receipt(
                request=request,
                state=state,
                authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
                evidence_digest=decision.digest,
                citations=(),
            )
            return EngineeringAgentToolResult.create(
                tool_request_digest=request.digest,
                result_ref=decision.decision_id.value,
                content=_required_payload(
                    {
                        "schema": "ENGINEERING_AGENT_SOURCE_BOUNDARY@1",
                        "broker_decision_id": decision.decision_id.value,
                        "status": decision.status.value,
                        "reason": decision.reason_code,
                    }
                ),
                disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
                progress=False,
                authority_receipt=receipt,
            )

        compiled = compilation.operation
        if compiled is None or decision.operation_id != compiled.operation_id:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "authorized Source Broker decision has no exact operation",
            )
        state.ledger = _append_operation(
            ledger=state.ledger,
            operation=compiled,
            decision_ref=decision.decision_id.value,
            maximum_bytes=state.evidence_request.limits.maximum_ledger_bytes,
        )
        try:
            result = self._retrieval_worker.execute(compiled)
        except DomainError as exc:
            if exc.code is not ErrorCode.SOURCE_OPERATION_FAILED:
                raise
            result = RetrievalResult.create(
                operation=compiled,
                status=RetrievalStatus.OUTCOME_UNKNOWN,
                items=(),
                bytes_read=0,
                files_read=0,
                truncated=False,
                coverage={
                    "worker_outcome": "unknown",
                    "error_code": exc.code.value,
                },
                failure_code="SOURCE_WORKER_OUTCOME_UNKNOWN",
            )
        _validate_retrieval_result(
            request=state.evidence_request,
            operation=compiled,
            result=result,
        )
        for item in result.items:
            state.locator_catalog[item.locator_reference] = item
        state.ledger = _append_result(
            ledger=state.ledger,
            operation=compiled,
            result=result,
            maximum_bytes=state.evidence_request.limits.maximum_ledger_bytes,
        )
        state.usage = state.usage.with_retrieval(result, compiled)
        state.ledger = _append_resource_receipt(
            request=state.evidence_request,
            ledger=state.ledger,
            usage=state.usage,
        )
        citations = tuple(
            EngineeringAgentCitation.create(
                citation_ref=item.locator_reference.value,
                evidence_class=item.evidence_class.value,
                source_revision=result.repository_revision,
                locator=item.display_locator,
                modality=item.modality,
                content_digest=item.content_digest,
            )
            for item in result.items
        )
        receipt = self._receipt(
            request=request,
            state=state,
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            evidence_digest=result.digest,
            citations=citations,
        )
        fresh = result.progress_digest not in state.progress_digests
        state.progress_digests.add(result.progress_digest)
        evidence: list[EngineeringAgentToolEvidence] = []
        if result.items and result.status in {
            RetrievalStatus.COMPLETE,
            RetrievalStatus.PARTIAL,
        }:
            content = _payload(
                {
                    "schema": "ENGINEERING_AGENT_SOURCE_SUPPORT@1",
                    "retrieval_result": result.model_view(),
                }
            )
            if content is not None:
                evidence.append(
                    EngineeringAgentToolEvidence.create(
                        tool_request_digest=request.digest,
                        result_ref=f"{result.result_id.value}-support",
                        content=content,
                        disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
                        progress=fresh,
                        citation_refs=tuple(
                            item.citation_ref for item in citations
                        ),
                        authority_receipt=receipt,
                    )
                )
        boundary_reasons = []
        if result.status is not RetrievalStatus.COMPLETE:
            boundary_reasons.append(f"SOURCE_{result.status.value}")
        if result.truncated:
            boundary_reasons.append("SOURCE_RESULT_TRUNCATED")
        if result.failure_code:
            boundary_reasons.append(result.failure_code)
        if not result.items:
            boundary_reasons.append("SOURCE_RESULT_HAS_NO_ITEMS")
        if result.items and not evidence:
            boundary_reasons.append("SOURCE_OBSERVATION_BYTE_LIMIT")
        if boundary_reasons:
            evidence.append(
                EngineeringAgentToolEvidence.create(
                    tool_request_digest=request.digest,
                    result_ref=f"{result.result_id.value}-boundary",
                    content=_required_payload(
                        {
                            "schema": "ENGINEERING_AGENT_SOURCE_BOUNDARY@1",
                            "retrieval_result_id": result.result_id.value,
                            "retrieval_result_digest": result.digest.value,
                            "status": result.status.value,
                            "coverage": dict(result.coverage),
                            "failure_code": result.failure_code,
                            "truncated": result.truncated,
                            "reasons": boundary_reasons,
                        }
                    ),
                    disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
                    progress=fresh,
                    authority_receipt=receipt,
                )
            )
        return EngineeringAgentToolResult.create_many(
            tool_request_digest=request.digest,
            evidence=evidence,
        )

    @staticmethod
    def _receipt(
        *,
        request: EngineeringAgentToolRequest,
        state: _TurnToolState,
        authority_kind: EngineeringAgentToolAuthorityKind,
        evidence_digest: Digest,
        citations: Sequence[EngineeringAgentCitation],
    ) -> EngineeringAgentToolAuthorityReceipt:
        state.ledger.validate_integrity()
        entries = tuple(
            EngineeringAgentLedgerEntryReceipt.create(
                sequence=item.sequence,
                kind=item.kind.value,
                subject_ref=item.subject_id,
                subject_digest=item.subject_digest,
                references=item.references,
                details=item.details,
                previous_entry_digest=item.previous_entry_digest,
                source_entry_digest=item.digest,
            )
            for item in state.ledger.entries
        )
        return EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=authority_kind,
            turn_request_digest=request.turn_request_digest,
            tool_request_digest=request.digest,
            evidence_request_digest=state.evidence_request.digest,
            repository_revision=state.evidence_request.repository_revision,
            evidence_digest=evidence_digest,
            ledger_ref=state.ledger.ledger_id.value,
            ledger_generation=state.ledger.generation,
            ledger_parent_seal_digest=state.ledger.parent_seal_digest,
            ledger_prefix_digest=state.ledger.prefix_digest,
            ledger_entries=entries,
            citations=citations,
        )


def _append_operation(
    *,
    ledger: EvidenceLedger,
    operation: CompiledSourceOperation,
    decision_ref: str,
    maximum_bytes: int,
) -> EvidenceLedger:
    return ledger.append(
        kind=LedgerEntryKind.SOURCE_OPERATION,
        subject_id=operation.operation_id.value,
        subject_digest=operation.digest,
        references=(decision_ref,),
        details={
            "operation": operation.operation.value,
            "repository_revision": operation.repository_revision,
            "source_profile_ref": operation.source_profile_ref,
            "source_profile_digest": operation.source_profile_digest.value,
            "evidence_class_allowlist_digest": digest_of(
                [
                    "ENGINEERING_QA_EVIDENCE_CLASS_ALLOWLIST@1",
                    operation.evidence_class.value,
                    operation.evidence_class_allowlist,
                ]
            ).value,
            "evidence_class": operation.evidence_class.value,
            "result_modality": operation.result_modality,
        },
        maximum_bytes=maximum_bytes,
    )


def _append_result(
    *,
    ledger: EvidenceLedger,
    operation: CompiledSourceOperation,
    result: RetrievalResult,
    maximum_bytes: int,
) -> EvidenceLedger:
    return ledger.append(
        kind=LedgerEntryKind.SOURCE_RESULT,
        subject_id=result.result_id.value,
        subject_digest=result.digest,
        references=(
            operation.operation_id.value,
            *(item.item_id.value for item in result.items),
        ),
        details={
            "status": result.status.value,
            "bytes": str(result.bytes_read),
            "files": str(result.files_read),
            "truncated": str(result.truncated).lower(),
            "progress_digest": result.progress_digest.value,
            "evidence_class": operation.evidence_class.value,
            "result_modality": operation.result_modality,
        },
        maximum_bytes=maximum_bytes,
    )


def _append_resource_receipt(
    *,
    request: EngineeringQuestionRequest,
    ledger: EvidenceLedger,
    usage: EngineeringQuestionResourceUsage,
) -> EvidenceLedger:
    details = {
        field_name: str(getattr(usage, field_name))
        for field_name in usage.__dataclass_fields__
    }
    details["maximum_source_files"] = str(request.limits.maximum_source_files)
    receipt_digest = digest_of(
        [
            "ENGINEERING_QA_RESOURCE_RECEIPT@1",
            request.limits.digest.value,
            details,
        ]
    )
    return ledger.append(
        kind=LedgerEntryKind.RESOURCE_RECEIPT,
        subject_id=_derived_id("resource_receipt", receipt_digest.value).value,
        subject_digest=receipt_digest,
        references=(ledger.entries[-1].entry_id.value,),
        details=details,
        maximum_bytes=request.limits.maximum_ledger_bytes,
    )


def _validate_retrieval_result(
    *,
    request: EngineeringQuestionRequest,
    operation: CompiledSourceOperation,
    result: RetrievalResult,
) -> None:
    operation.validate_identity()
    expected = RetrievalResult.create(
        operation=operation,
        status=result.status,
        items=result.items,
        bytes_read=result.bytes_read,
        files_read=result.files_read,
        truncated=result.truncated,
        coverage=dict(result.coverage),
        failure_code=result.failure_code,
    )
    if (
        result != expected
        or result.operation_id != operation.operation_id
        or result.operation_digest != operation.digest
        or result.repository_revision != request.repository_revision
        or result.bytes_read > operation.maximum_source_bytes
        or result.files_read > operation.maximum_files
        or len(result.items) > operation.maximum_result_items
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Retrieval Worker result violates its compiled Source authority",
        )
    if any(
        not _path_allowed(item.path, operation.source_allowlist)
        or not _path_allowed(item.path, operation.evidence_class_allowlist)
        or item.evidence_class is not operation.evidence_class
        or item.modality != operation.result_modality
        or (
            operation.operation is SourceReadOperation.READ
            and item.path != operation.path
        )
        for item in result.items
    ):
        raise DomainError(
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
            "Retrieval Worker returned evidence outside the compiled authority",
        )
    if len({item.locator_reference for item in result.items}) != len(result.items):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Retrieval Worker returned duplicate locator references",
        )


def _arguments(
    request: EngineeringAgentToolRequest,
    *,
    expected: Sequence[str],
) -> dict[str, str]:
    arguments = dict(request.action.arguments)
    if set(arguments) != set(expected) or len(arguments) != len(tuple(expected)):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Agent tool arguments do not match the closed operation schema",
        )
    return arguments


def _compile_world_model_semantic_query(
    request: EngineeringAgentToolRequest,
) -> str:
    """Compile a bounded semantic query from the material Need and exact Turn.

    ``evidence_need`` remains an untrusted Agent proposal.  Binding the current
    immutable User Message keeps the compiled query inside the Turn's material
    scope while still allowing repository-native symbols or cross-language
    terminology proposed by the Agent to drive formal cognition projection.
    """

    action = request.action
    current_message = request.turn_request.user_message.content
    components = tuple(
        dict.fromkeys((action.evidence_need, current_message))
    )
    query = "\n".join(components)
    if not query or len(query.encode("utf-8")) > 17_000:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Application-compiled World Model semantic query exceeds its bound",
        )
    return query


def _payload(value: Mapping[str, object]) -> str | None:
    encoded = canonical_json_bytes(value)
    if len(encoded) > _OBSERVATION_PAYLOAD_LIMIT:
        return None
    return encoded.decode("utf-8")


def _required_payload(value: Mapping[str, object]) -> str:
    content = _payload(value)
    if content is None:
        raise DomainError(
            ErrorCode.BUDGET_EXHAUSTED,
            "tool boundary metadata exceeds the Observation byte limit",
        )
    return content


def _derived_id(kind: str, value: str) -> StableId:
    suffix = digest_of(["ENGINEERING_AGENT_DERIVED_ID@1", kind, value])
    return StableId(f"{kind}_{suffix.value.removeprefix('sha256:')[:32]}")


def _reference(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be non-empty without surrounding whitespace",
        )
    if len(value.encode("utf-8")) > 512:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} exceeds its boundary")
    return value


def _relative_path(value: str) -> str:
    value = _reference(value, "excluded Source path").replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or value in {"", "."} or ".." in path.parts:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "excluded Source path must be a repository-relative path",
        )
    normalized = path.as_posix().rstrip("/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _contains_path(parent: str, child: str) -> bool:
    return parent == "." or child == parent or child.startswith(parent + "/")


def _path_allowed(path: str, allowlist: Sequence[str]) -> bool:
    return any(_contains_path(root, path) for root in allowlist)


__all__ = [
    "EngineeringAgentEvidenceToolAdapter",
    "EngineeringAgentEvidenceToolConfiguration",
]
