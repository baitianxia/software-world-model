"""Non-dispatching preflight for the ITER-010 Engineering Chat candidate.

The fixed public launcher remains Access-only.  This module validates already
sealed product, Chat, evidence-tool, Provider, and session-disclosure records
without opening a listener, resolving a credential, reading Source, or crossing
the Model Gateway.  Its receipt is deliberately not a live-readiness receipt:
the required Ark-to-DeepSeek fallback and fixed launcher composition remain
explicit blocking gaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Sequence

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentLoopLimits,
    EngineeringAgentToolOperation,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .engineering_chat_browser import ENGINEERING_CHAT_LOOPBACK_ORIGIN


ENGINEERING_CHAT_CANDIDATE_PREFLIGHT_SCHEMA = (
    "SWM-ENGINEERING-CHAT-CANDIDATE-PREFLIGHT@1"
)
ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS = (
    "MODEL_BOUNDARY_LOCAL_CANDIDATE"
)
ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS = (
    "ARK_DEEPSEEK_FALLBACK_NOT_INTEGRATED",
    "FIXED_PROVIDER_LAUNCHER_NOT_WIRED",
    "LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",
)
ENGINEERING_CHAT_CANDIDATE_OPERATIONS = (
    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
    EngineeringAgentToolOperation.SOURCE_SEARCH,
    EngineeringAgentToolOperation.SOURCE_READ,
)

_GIT_IDENTITY = re.compile(r"^[0-9a-f]{40}$")


def engineering_chat_product_candidate_digest(
    *, product_revision: str, product_tree: str
) -> Digest:
    """Bind already-resolved exact Git identities without reading a worktree."""

    if not _GIT_IDENTITY.fullmatch(product_revision) or not _GIT_IDENTITY.fullmatch(
        product_tree
    ):
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            "Engineering Chat candidate requires exact product commit and tree identities",
        )
    return digest_of(
        [
            "ENGINEERING_CHAT_PRODUCT_CANDIDATE@1",
            {"product_revision": product_revision, "product_tree": product_tree},
        ]
    )


def engineering_chat_single_provider_route_ref(
    configuration: EngineeringAgentModelConfiguration,
) -> str:
    """Return the exact temporary single-route identity used by this preflight."""

    return f"engineering-agent-single-route:{configuration.digest.value}"


@dataclass(frozen=True, slots=True)
class EngineeringChatCandidatePreflightReceipt:
    schema: str
    status: str
    product_revision: str
    product_tree: str
    product_candidate_digest: Digest
    chat_binding_digest: Digest
    world_model_authority_digest: Digest
    source_profile_ref: str
    evidence_tool_configuration_digest: Digest
    provider_route_ref: str
    provider_type: str
    model_ref: str
    provider_configuration_digest: Digest
    session_disclosure_authority_digest: Digest
    available_operations: tuple[EngineeringAgentToolOperation, ...]
    maximum_turns: int
    maximum_dispatches_per_turn: int
    maximum_total_dispatches: int
    blocking_gaps: tuple[str, ...]
    ready_for_live: bool
    listener_started: bool
    credential_resolved: bool
    source_read_performed: bool
    provider_dispatch_count: int
    request_retry_allowed: bool
    production_activation: str
    checked_at: datetime
    digest: Digest

    def public_status(self) -> dict[str, object]:
        """Project a credential-reference-free, non-live status view."""

        return {
            "schema": self.schema,
            "status": self.status,
            "ready_for_live": self.ready_for_live,
            "product_revision": self.product_revision,
            "product_tree": self.product_tree,
            "product_candidate_digest": self.product_candidate_digest.value,
            "chat_binding_digest": self.chat_binding_digest.value,
            "world_model_authority_digest": self.world_model_authority_digest.value,
            "source_profile_ref": self.source_profile_ref,
            "evidence_tool_configuration_digest": (
                self.evidence_tool_configuration_digest.value
            ),
            "provider_route_ref": self.provider_route_ref,
            "provider_type": self.provider_type,
            "model_ref": self.model_ref,
            "provider_configuration_digest": (
                self.provider_configuration_digest.value
            ),
            "session_disclosure_authority_digest": (
                self.session_disclosure_authority_digest.value
            ),
            "available_operations": tuple(
                item.value for item in self.available_operations
            ),
            "maximum_turns": self.maximum_turns,
            "maximum_dispatches_per_turn": self.maximum_dispatches_per_turn,
            "maximum_total_dispatches": self.maximum_total_dispatches,
            "blocking_gaps": self.blocking_gaps,
            "listener_started": self.listener_started,
            "credential_resolved": self.credential_resolved,
            "source_read_performed": self.source_read_performed,
            "provider_dispatch_count": self.provider_dispatch_count,
            "request_retry_allowed": self.request_retry_allowed,
            "production_activation": self.production_activation,
            "checked_at": self.checked_at.isoformat().replace("+00:00", "Z"),
            "preflight_receipt_digest": self.digest.value,
        }


def prepare_engineering_chat_candidate_preflight(
    *,
    binding: EngineeringChatBinding,
    product_tree: str,
    evidence_tools: EngineeringAgentEvidenceToolConfiguration,
    provider_configuration: EngineeringAgentModelConfiguration,
    session_authority: EngineeringAgentSessionDisclosureAuthority,
    checked_at: datetime,
    loop_limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
    available_operations: Sequence[EngineeringAgentToolOperation] = (
        ENGINEERING_CHAT_CANDIDATE_OPERATIONS
    ),
    required_conversation_turns: int = 5,
) -> EngineeringChatCandidatePreflightReceipt:
    """Validate the sealed single-route candidate without performing I/O."""

    current = _aware_utc(checked_at)
    operations = tuple(available_operations)
    if operations != ENGINEERING_CHAT_CANDIDATE_OPERATIONS:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Chat candidate tool catalog is not the exact current catalog",
        )
    if type(required_conversation_turns) is not int or required_conversation_turns < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat candidate Turn requirement must be a positive integer",
        )
    if (
        binding.world_model_status is not RuntimeCapabilityStatus.READY
        or binding.source_access_status is not RuntimeCapabilityStatus.READY
        or binding.provider_status is not RuntimeCapabilityStatus.READY
        or binding.world_model_authority_digest is None
        or binding.source_profile_ref is None
        or binding.provider_route_ref is None
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Chat candidate requires ready exact World Model, Source, and Provider bindings",
        )
    product_candidate_digest = engineering_chat_product_candidate_digest(
        product_revision=binding.product_revision,
        product_tree=product_tree,
    )
    expected_route = engineering_chat_single_provider_route_ref(
        provider_configuration
    )
    if binding.provider_route_ref != expected_route:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat Provider route does not bind the exact model configuration",
        )
    if (
        evidence_tools.project_name != binding.project_name
        or evidence_tools.repository_revision != binding.repository_revision
        or evidence_tools.world_model_read_authority_digest
        != binding.world_model_authority_digest
        or evidence_tools.source_profile_ref != binding.source_profile_ref
        or evidence_tools.provider_disclosure_policy
        != provider_configuration.provider_disclosure_policy_ref
        or "src/main/resources" not in binding.excluded_source_paths
        or "src/main/resources" not in evidence_tools.excluded_source_paths
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat evidence tools do not bind the exact Chat and Provider scope",
        )
    provider_configuration.require_current(current)
    session_authority.require_current(
        configuration=provider_configuration,
        chat_binding_digest=binding.digest,
        at=current,
    )
    if session_authority.product_candidate_digest != product_candidate_digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat session disclosure does not bind the exact product candidate",
        )
    required_dispatches_per_turn = (
        loop_limits.maximum_agent_steps + loop_limits.maximum_reviews
    )
    required_total_dispatches = (
        required_conversation_turns * required_dispatches_per_turn
    )
    if (
        session_authority.maximum_turns < required_conversation_turns
        or session_authority.maximum_dispatches_per_turn
        < required_dispatches_per_turn
        or session_authority.maximum_total_dispatches < required_total_dispatches
    ):
        raise DomainError(
            ErrorCode.BUDGET_EXHAUSTED,
            "Engineering Chat session fuses cannot complete the bounded five-Turn candidate",
        )
    core = {
        "schema": ENGINEERING_CHAT_CANDIDATE_PREFLIGHT_SCHEMA,
        "status": ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS,
        "product_revision": binding.product_revision,
        "product_tree": product_tree,
        "product_candidate_digest": product_candidate_digest.value,
        "chat_binding_digest": binding.digest.value,
        "world_model_authority_digest": binding.world_model_authority_digest.value,
        "source_profile_ref": binding.source_profile_ref,
        "evidence_tool_configuration_digest": evidence_tools.digest.value,
        "provider_route_ref": expected_route,
        "provider_type": provider_configuration.provider_type,
        "model_ref": provider_configuration.model_ref,
        "provider_configuration_digest": provider_configuration.digest.value,
        "session_disclosure_authority_digest": session_authority.digest.value,
        "available_operations": tuple(item.value for item in operations),
        "maximum_turns": session_authority.maximum_turns,
        "maximum_dispatches_per_turn": (
            session_authority.maximum_dispatches_per_turn
        ),
        "maximum_total_dispatches": session_authority.maximum_total_dispatches,
        "blocking_gaps": ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS,
        "ready_for_live": False,
        "listener_started": False,
        "credential_resolved": False,
        "source_read_performed": False,
        "provider_dispatch_count": 0,
        "request_retry_allowed": False,
        "production_activation": "NOT_EXECUTED",
        "checked_at": current.isoformat().replace("+00:00", "Z"),
    }
    return EngineeringChatCandidatePreflightReceipt(
        schema=ENGINEERING_CHAT_CANDIDATE_PREFLIGHT_SCHEMA,
        status=ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS,
        product_revision=binding.product_revision,
        product_tree=product_tree,
        product_candidate_digest=product_candidate_digest,
        chat_binding_digest=binding.digest,
        world_model_authority_digest=binding.world_model_authority_digest,
        source_profile_ref=binding.source_profile_ref,
        evidence_tool_configuration_digest=evidence_tools.digest,
        provider_route_ref=expected_route,
        provider_type=provider_configuration.provider_type,
        model_ref=provider_configuration.model_ref,
        provider_configuration_digest=provider_configuration.digest,
        session_disclosure_authority_digest=session_authority.digest,
        available_operations=operations,
        maximum_turns=session_authority.maximum_turns,
        maximum_dispatches_per_turn=(
            session_authority.maximum_dispatches_per_turn
        ),
        maximum_total_dispatches=session_authority.maximum_total_dispatches,
        blocking_gaps=ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS,
        ready_for_live=False,
        listener_started=False,
        credential_resolved=False,
        source_read_performed=False,
        provider_dispatch_count=0,
        request_retry_allowed=False,
        production_activation="NOT_EXECUTED",
        checked_at=current,
        digest=digest_of(core),
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat candidate preflight time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


__all__ = [
    "ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS",
    "ENGINEERING_CHAT_CANDIDATE_OPERATIONS",
    "ENGINEERING_CHAT_CANDIDATE_PREFLIGHT_SCHEMA",
    "ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS",
    "EngineeringChatCandidatePreflightReceipt",
    "engineering_chat_product_candidate_digest",
    "engineering_chat_single_provider_route_ref",
    "prepare_engineering_chat_candidate_preflight",
]
