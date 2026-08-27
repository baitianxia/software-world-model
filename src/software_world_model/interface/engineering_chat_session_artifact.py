"""Load and compose one sealed Engineering Chat artifact Session.

The owner-private configuration fixes product and Source Git identities,
published World Model bundles, the Source Profile, the ordered Ark-to-DeepSeek
route, both current Conformance results, private Gateway repository references,
and the bounded Session disclosure authority.  Preparation reads only those
artifacts and Git metadata.  It does not resolve credentials, create a Turn or
Provider attempt, dispatch a model call, read repository content, or start the
loopback listener.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import stat
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure.ark_chat_conformance import (
    load_ark_chat_conformance_qualification,
)
from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
    deepseek_transport_session_audit,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    load_deepseek_chat_conformance_qualification,
)
from software_world_model.ai_infrastructure.model_gateway import (
    ModelGatewayRepository,
)
from software_world_model.ai_infrastructure.volcengine_ark_chat_adapter import (
    VolcengineArkModelConfiguration,
    ark_transport_session_audit,
)
from software_world_model.application_services.conversational_engineering_routing import (
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    engineering_agent_dual_provider_route_ref,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN,
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
    SourceBroker,
)
from software_world_model.application_services.engineering_question_cognition import (
    CognitionProfileCapability,
    MultiProfileWorldModelCognitionProjector,
    StructureBundleWorldModelCognitionProjector,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)

from .engineering_chat_candidate import (
    engineering_chat_product_candidate_digest,
)
from .engineering_chat_provider_runtime import (
    create_ark_engineering_chat_provider_model_runtime,
    create_deepseek_engineering_chat_provider_model_runtime,
    engineering_chat_ark_model_configuration,
    engineering_chat_deepseek_model_configuration,
)
from .engineering_chat_session_runtime import (
    ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS,
    PreparedEngineeringChatSessionRuntime,
    prepare_engineering_chat_session_runtime,
)
from .engineering_qa_preview_cli import (
    _canonical_directory,
    _exact_source_revision,
    _select_cognition_snapshot,
    _stable_id,
    _verify_product_candidate,
)
from .engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1 = (
    "SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1"
)
ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA = (
    "SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@2"
)
ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_SCHEMA = (
    "SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-PREPARATION@2"
)
ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS = (
    "ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE"
)
_MAXIMUM_SESSION_CONFIG_BYTES = 1_048_576
_SESSION_CONFIG_COMMON_FIELDS = frozenset(
    {
        "schema",
        "product_repository",
        "product_commit",
        "product_tree",
        "project_name",
        "repository",
        "repository_id",
        "binding_id",
        "repository_revision",
        "source_profile_ref",
        "source_paths",
        "document_paths",
        "build_paths",
        "test_paths",
        "excluded_source_paths",
        "response_language",
        "session_ref",
        "authorization_message_digest",
        "authorized_at",
        "expires_at",
        "provider_routes",
        "launch_receipt",
        "terminal_receipt",
        "required_conversation_turns",
        "maximum_dispatches_per_turn",
        "maximum_total_dispatches_per_provider",
        "known_limitations",
    }
)
_SESSION_CONFIG_V1_FIELDS = _SESSION_CONFIG_COMMON_FIELDS | {
    "ordered_envelope",
    "snapshot_bundles",
    "cognition_snapshot_id",
}
_SESSION_CONFIG_V2_FIELDS = _SESSION_CONFIG_COMMON_FIELDS | {
    "cognition_profiles",
}
_COGNITION_PROFILE_FIELDS = frozenset(
    {
        "ordinal",
        "profile_ref",
        "schema_ref",
        "source_binding_id",
        "ordered_envelope",
        "ordered_bundle_digest",
        "ordered_file_digest",
        "snapshot_bundles",
        "snapshot_bundle_digests",
        "snapshot_file_digests",
        "cognition_snapshot_id",
    }
)
_PROVIDER_ROUTE_FIELDS = frozenset(
    {
        "ordinal",
        "provider_type",
        "conformance_result",
        "gateway_database",
    }
)
_PROVIDER_ROUTE_ORDER = ("VOLCENGINE_ARK", "DEEPSEEK")
_CURRENT_REQUIRED_CONVERSATION_TURNS = 5
_CURRENT_MAXIMUM_DISPATCHES_PER_TURN = 15
_CURRENT_MAXIMUM_TOTAL_DISPATCHES_PER_PROVIDER = 75


@dataclass(frozen=True, slots=True)
class EngineeringChatArtifactProviderRouteConfig:
    ordinal: int
    provider_type: str
    conformance_result: str
    gateway_database: str


@dataclass(frozen=True, slots=True)
class EngineeringChatArtifactCognitionProfileConfig:
    ordinal: int
    profile_ref: str | None
    schema_ref: str | None
    source_binding_id: StableId | None
    ordered_envelope: str
    ordered_bundle_digest: Digest | None
    ordered_file_digest: Digest | None
    snapshot_bundles: tuple[str, ...]
    snapshot_bundle_digests: tuple[Digest, ...] | None
    snapshot_file_digests: tuple[Digest, ...] | None
    cognition_snapshot_id: str | None


@dataclass(frozen=True, slots=True)
class EngineeringChatArtifactSessionConfig:
    schema: str
    path: Path
    file_digest: Digest
    product_repository: str
    product_commit: str
    product_tree: str
    project_name: str
    repository: str
    repository_id: str
    binding_id: str
    repository_revision: str
    source_profile_ref: str
    source_paths: tuple[str, ...]
    document_paths: tuple[str, ...]
    build_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    excluded_source_paths: tuple[str, ...]
    cognition_profiles: tuple[EngineeringChatArtifactCognitionProfileConfig, ...]
    response_language: str
    session_ref: str
    authorization_message_digest: Digest
    authorized_at: datetime
    expires_at: datetime
    provider_routes: tuple[EngineeringChatArtifactProviderRouteConfig, ...]
    launch_receipt: str
    terminal_receipt: str
    required_conversation_turns: int
    maximum_dispatches_per_turn: int
    maximum_total_dispatches_per_provider: int
    known_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedEngineeringChatCognitionProfileArtifact:
    ordinal: int
    profile_ref: str
    schema_ref: str
    source_binding_id: StableId
    snapshot_id: StableId
    read_authority_digest: Digest
    ordered_bundle_digest: Digest
    ordered_file_digest: Digest
    snapshot_bundle_digests: tuple[Digest, ...]
    snapshot_file_digests: tuple[Digest, ...]

    def public_status(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "profile_ref": self.profile_ref,
            "schema_ref": self.schema_ref,
            "source_binding_id": self.source_binding_id.value,
            "snapshot_id": self.snapshot_id.value,
            "read_authority_digest": self.read_authority_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "ordered_file_digest": self.ordered_file_digest.value,
            "snapshot_bundle_digests": tuple(
                item.value for item in self.snapshot_bundle_digests
            ),
            "snapshot_file_digests": tuple(
                item.value for item in self.snapshot_file_digests
            ),
        }


@dataclass(frozen=True, slots=True)
class _LoadedEngineeringChatCognitionProfile:
    config: EngineeringChatArtifactCognitionProfileConfig
    view: StructureViewService
    projector: StructureBundleWorldModelCognitionProjector
    ordered_file_digest: Digest
    snapshot_file_digests: tuple[Digest, ...]


@dataclass(frozen=True, slots=True)
class PreparedEngineeringChatArtifactSession:
    runtime: PreparedEngineeringChatSessionRuntime
    session_config: EngineeringChatArtifactSessionConfig
    product_candidate_commit: str
    product_candidate_tree: str
    cognition_profiles: tuple[PreparedEngineeringChatCognitionProfileArtifact, ...]
    world_model_read_authority_digest: Digest
    ark_conformance_result_digest: Digest
    deepseek_conformance_result_digest: Digest
    preparation_digest: Digest

    def public_status(self) -> dict[str, object]:
        health = self.runtime.launcher.application.health()
        return {
            **health,
            "schema": ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_SCHEMA,
            "status": ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS,
            "url": "http://127.0.0.1:8765/",
            "product": {
                **health["product"],
                "tree": self.product_candidate_tree,
            },
            "session_config_file_digest": self.session_config.file_digest.value,
            "session_runtime": self.runtime.receipt.public_status(),
            "provider_routes": (
                self.runtime.primary_provider_runtime.public_status(),
                self.runtime.fallback_provider_runtime.public_status(),
            ),
            "world_model_artifacts": {
                "read_authority_digest": (
                    self.world_model_read_authority_digest.value
                ),
                "profiles": tuple(
                    item.public_status() for item in self.cognition_profiles
                ),
            },
            "listener_started": False,
            "browser_live_verification": "NOT_EXECUTED",
            "production_activation": "NOT_EXECUTED",
            "preparation_digest": self.preparation_digest.value,
        }

    def launch_receipt(self) -> dict[str, object]:
        """Seal the zero-dispatch state before a future listener starts."""

        service = self.runtime.launcher.service
        primary = self.runtime.primary_provider_runtime
        fallback = self.runtime.fallback_provider_runtime
        if (
            service.statistics() != (0, 0)
            or service.provider_dispatch_count() != 0
            or self.runtime.evidence_tool_factory.created_tool_count != 0
            or primary.model_boundary.audits
            or fallback.model_boundary.audits
            or primary.authorizer.disclosure_requests
            or fallback.authorizer.disclosure_requests
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat artifact launch receipt requires zero runtime activity",
            )
        core = {
            "schema": "SWM-ENGINEERING-CHAT-ARTIFACT-LAUNCH-RECEIPT@1",
            "status": "ARTIFACT_SESSION_PREPARED_NOT_STARTED",
            "preparation_digest": self.preparation_digest.value,
            "session_config_file_digest": self.session_config.file_digest.value,
            "session_runtime_receipt_digest": self.runtime.receipt.digest.value,
            "chat_binding_digest": (
                self.runtime.launcher.service.binding.digest.value
            ),
            "route_plan_digest": self.runtime.launcher.route_plan.digest.value,
            "ark_conformance_result_digest": (
                self.ark_conformance_result_digest.value
            ),
            "deepseek_conformance_result_digest": (
                self.deepseek_conformance_result_digest.value
            ),
            "conversation_count_at_seal": 0,
            "turn_count_at_seal": 0,
            "provider_dispatch_count_at_seal": 0,
            "credential_resolved_at_seal": False,
            "source_read_performed_at_seal": False,
            "listener_started_at_seal": False,
            "request_retry_count": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return {**core, "digest": digest_of(core).value}

    def terminal_receipt(self) -> dict[str, object]:
        """Seal bounded Provider/disclosure audit identities after shutdown."""

        service = self.runtime.launcher.service
        conversation_count, turn_count = service.statistics()
        provider_audits = (
            _provider_terminal_audit(self.runtime.primary_provider_runtime),
            _provider_terminal_audit(self.runtime.fallback_provider_runtime),
        )
        provider_dispatch_count = sum(
            item["provider_dispatch_count"] for item in provider_audits
        )
        if provider_dispatch_count != service.provider_dispatch_count():
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat terminal Provider dispatch totals drifted",
            )
        core = {
            "schema": "SWM-ENGINEERING-CHAT-ARTIFACT-TERMINAL-RECEIPT@1",
            "status": (
                "STOPPED_AFTER_DISPATCH"
                if provider_dispatch_count
                else "STOPPED_WITHOUT_DISPATCH"
            ),
            "preparation_digest": self.preparation_digest.value,
            "session_config_file_digest": self.session_config.file_digest.value,
            "session_runtime_receipt_digest": self.runtime.receipt.digest.value,
            "conversation_count": conversation_count,
            "turn_count": turn_count,
            "provider_dispatch_count": provider_dispatch_count,
            "provider_audits": provider_audits,
            "request_retry_count": 0,
            "production_activation": "NOT_EXECUTED",
        }
        return {**core, "digest": digest_of(core).value}


def load_engineering_chat_artifact_session_config(
    value: str | Path,
) -> EngineeringChatArtifactSessionConfig:
    """Load one owner-private, closed, unique-key Session document."""

    path = _canonical_private_file(value, "Engineering Chat artifact session config")
    raw = path.read_bytes()
    if not raw or len(raw) > _MAXIMUM_SESSION_CONFIG_BYTES:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session config has an invalid size",
        )
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session config is not unique-key UTF-8 JSON",
        ) from exc
    if not isinstance(decoded, Mapping):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session config must be an object",
        )
    schema = decoded.get("schema")
    expected_fields = {
        ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1: (
            _SESSION_CONFIG_V1_FIELDS
        ),
        ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA: (
            _SESSION_CONFIG_V2_FIELDS
        ),
    }.get(schema)
    if expected_fields is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session config schema is unsupported",
        )
    if set(decoded) != expected_fields:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session config contains missing or unknown fields",
        )
    routes = _provider_routes(decoded)
    try:
        authorization_message_digest = Digest(
            _required_text(decoded, "authorization_message_digest")
        )
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat authorization message digest is invalid",
        ) from exc
    cognition_profiles = _cognition_profiles(decoded, schema=schema)
    config = EngineeringChatArtifactSessionConfig(
        schema=schema,
        path=path,
        file_digest=Digest("sha256:" + sha256(raw).hexdigest()),
        product_repository=_required_absolute_path_text(
            decoded, "product_repository"
        ),
        product_commit=_required_text(decoded, "product_commit"),
        product_tree=_required_text(decoded, "product_tree"),
        project_name=_required_text(decoded, "project_name"),
        repository=_required_absolute_path_text(decoded, "repository"),
        repository_id=_required_text(decoded, "repository_id"),
        binding_id=_required_text(decoded, "binding_id"),
        repository_revision=_required_text(decoded, "repository_revision"),
        source_profile_ref=_required_text(decoded, "source_profile_ref"),
        source_paths=_required_text_list(decoded, "source_paths"),
        document_paths=_required_text_list(decoded, "document_paths"),
        build_paths=_required_text_list(decoded, "build_paths"),
        test_paths=_required_text_list(decoded, "test_paths"),
        excluded_source_paths=_required_text_list(
            decoded, "excluded_source_paths"
        ),
        cognition_profiles=cognition_profiles,
        response_language=_required_text(decoded, "response_language"),
        session_ref=_required_text(decoded, "session_ref"),
        authorization_message_digest=authorization_message_digest,
        authorized_at=_required_time(decoded, "authorized_at"),
        expires_at=_required_time(decoded, "expires_at"),
        provider_routes=routes,
        launch_receipt=_required_absolute_path_text(decoded, "launch_receipt"),
        terminal_receipt=_required_absolute_path_text(
            decoded, "terminal_receipt"
        ),
        required_conversation_turns=_required_positive_int(
            decoded, "required_conversation_turns"
        ),
        maximum_dispatches_per_turn=_required_positive_int(
            decoded, "maximum_dispatches_per_turn"
        ),
        maximum_total_dispatches_per_provider=_required_positive_int(
            decoded, "maximum_total_dispatches_per_provider"
        ),
        known_limitations=_required_text_list(decoded, "known_limitations"),
    )
    if (
        config.required_conversation_turns
        != _CURRENT_REQUIRED_CONVERSATION_TURNS
        or config.maximum_dispatches_per_turn
        != _CURRENT_MAXIMUM_DISPATCHES_PER_TURN
        or config.maximum_total_dispatches_per_provider
        != _CURRENT_MAXIMUM_TOTAL_DISPATCHES_PER_PROVIDER
        or config.maximum_total_dispatches_per_provider
        != config.required_conversation_turns
        * config.maximum_dispatches_per_turn
        or "src/main/resources" not in config.excluded_source_paths
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Chat artifact session bounds or exclusions drifted",
        )
    conformance_paths = tuple(item.conformance_result for item in routes)
    database_paths = tuple(item.gateway_database for item in routes)
    if (
        len(set(conformance_paths)) != len(conformance_paths)
        or len(set(database_paths)) != len(database_paths)
        or config.launch_receipt == config.terminal_receipt
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat Provider artifacts and receipts require distinct paths",
        )
    return config


def prepare_engineering_chat_artifact_session(
    session_config: EngineeringChatArtifactSessionConfig,
    *,
    ark_gateway_repository: ModelGatewayRepository,
    deepseek_gateway_repository: ModelGatewayRepository,
    at: datetime,
) -> PreparedEngineeringChatArtifactSession:
    """Compose all configured assets without listener, credential, or dispatch."""

    current = _aware_utc(at)
    if session_config.response_language != "zh-CN":
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "current Engineering Chat artifact requires the registered zh-CN input policy",
        )
    if ark_gateway_repository is deepseek_gateway_repository:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Ark and DeepSeek require distinct Gateway repositories",
        )
    product_repository = _canonical_directory(
        session_config.product_repository,
        "product repository",
    )
    product_commit, product_tree = _verify_product_candidate(
        repository=product_repository,
        expected_commit=session_config.product_commit,
        expected_tree=session_config.product_tree,
        implementation_path=Path(__file__),
    )
    source_repository = _canonical_directory(
        session_config.repository,
        "source repository",
    )
    if product_repository == source_repository:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "product and Chat Source require distinct repositories",
        )
    repository_revision = _exact_source_revision(
        source_repository,
        session_config.repository_revision,
    )
    repository_id = _stable_id(session_config.repository_id, "repository ID")
    binding_id = _stable_id(session_config.binding_id, "binding ID")
    profile = LocalGitEvidenceClassProfile.create(
        profile_ref=session_config.source_profile_ref,
        binding_id=binding_id,
        evidence_class_paths={
            EngineeringEvidenceClass.SOURCE: session_config.source_paths,
            EngineeringEvidenceClass.REPOSITORY_DOCUMENT: (
                session_config.document_paths
            ),
            EngineeringEvidenceClass.BUILD_CONFIGURATION: (
                session_config.build_paths
            ),
            EngineeringEvidenceClass.TEST: session_config.test_paths,
        },
    )
    source_allowlist = tuple(
        path for _, paths in profile.evidence_class_paths for path in paths
    )
    if any(
        _source_paths_overlap(allowed, excluded)
        for allowed in source_allowlist
        for excluded in session_config.excluded_source_paths
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Chat excluded Source path overlaps its Source Profile",
        )

    store = FileStructureReadBundleStore()
    loaded_cognition_profiles = tuple(
        _load_cognition_profile_artifacts(config=item, store=store)
        for item in session_config.cognition_profiles
    )
    projectors = tuple(
        item.projector for item in loaded_cognition_profiles
    )
    if session_config.schema == ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1:
        cognition = projectors[0]
        if cognition.binding_id != binding_id:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "legacy World Model cognition does not bind the Chat Source Binding",
            )
        capabilities = (
            CognitionProfileCapability.from_projector(
                ordinal=0,
                projector=cognition,
            ),
        )
    else:
        cognition = MultiProfileWorldModelCognitionProjector(
            repository_id=repository_id,
            binding_id=binding_id,
            projectors=projectors,
        )
        capabilities = cognition.manifest.profiles
    if cognition.source_revision != repository_revision:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "published World Model cognition does not bind the Chat Source revision",
        )
    _require_configured_cognition_profiles(
        configs=session_config.cognition_profiles,
        loaded=loaded_cognition_profiles,
        capabilities=capabilities,
    )
    prepared_cognition_profiles = tuple(
        PreparedEngineeringChatCognitionProfileArtifact(
            ordinal=capability.ordinal,
            profile_ref=capability.profile_ref,
            schema_ref=capability.schema_ref,
            source_binding_id=capability.source_binding_id,
            snapshot_id=capability.snapshot_id,
            read_authority_digest=capability.read_authority_digest,
            ordered_bundle_digest=capability.ordered_bundle_digest,
            ordered_file_digest=loaded_profile.ordered_file_digest,
            snapshot_bundle_digests=(
                loaded_profile.view.snapshot_bundle_digests
            ),
            snapshot_file_digests=loaded_profile.snapshot_file_digests,
        )
        for capability, loaded_profile in zip(
            capabilities,
            loaded_cognition_profiles,
            strict=True,
        )
    )

    ark_route_config, deepseek_route_config = session_config.provider_routes
    ark_provider = VolcengineArkModelConfiguration()
    deepseek_provider = DeepSeekModelConfiguration()
    ark_conformance_path = _canonical_regular_file(
        ark_route_config.conformance_result,
        "Ark Conformance result",
    )
    deepseek_conformance_path = _canonical_regular_file(
        deepseek_route_config.conformance_result,
        "DeepSeek Conformance result",
    )
    ark_qualification = load_ark_chat_conformance_qualification(
        ark_conformance_path,
        ark_provider,
        now=current,
    )
    deepseek_qualification = load_deepseek_chat_conformance_qualification(
        deepseek_conformance_path,
        deepseek_provider,
        now=current,
    )
    ark_configuration = engineering_chat_ark_model_configuration(
        provider_configuration=ark_provider,
        qualification=ark_qualification,
        maximum_calls=(
            session_config.maximum_total_dispatches_per_provider
        ),
        at=current,
    )
    deepseek_configuration = engineering_chat_deepseek_model_configuration(
        provider_configuration=deepseek_provider,
        qualification=deepseek_qualification,
        maximum_calls=(
            session_config.maximum_total_dispatches_per_provider
        ),
        at=current,
    )
    route_ref = engineering_agent_dual_provider_route_ref(
        primary_configuration_digest=ark_configuration.digest,
        fallback_configuration_digest=deepseek_configuration.digest,
    )
    binding = EngineeringChatBinding.create(
        product_version="CONVERSATIONAL_ENGINEERING_AGENT@1",
        product_revision=product_commit,
        project_name=session_config.project_name,
        repository_revision=repository_revision,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=cognition.read_authority_digest,
        source_profile_ref=profile.profile_ref,
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref=route_ref,
        conversation_input_policy_ref=(
            ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN
        ),
        excluded_source_paths=session_config.excluded_source_paths,
        known_limitations=session_config.known_limitations,
    )
    product_candidate_digest = engineering_chat_product_candidate_digest(
        product_revision=product_commit,
        product_tree=product_tree,
    )
    authorization_ref = (
        "codex-user-message:"
        + session_config.authorization_message_digest.value
    )
    ark_authority = EngineeringAgentSessionDisclosureAuthority.create(
        session_ref=session_config.session_ref + ":ark",
        product_candidate_digest=product_candidate_digest,
        chat_binding_digest=binding.digest,
        configuration=ark_configuration,
        maximum_turns=session_config.required_conversation_turns,
        maximum_dispatches_per_turn=(
            session_config.maximum_dispatches_per_turn
        ),
        maximum_total_dispatches=(
            session_config.maximum_total_dispatches_per_provider
        ),
        authorized_at=session_config.authorized_at,
        expires_at=session_config.expires_at,
        authorization_ref=authorization_ref,
        authorization_message_digest=(
            session_config.authorization_message_digest
        ),
    )
    deepseek_authority = EngineeringAgentSessionDisclosureAuthority.create(
        session_ref=session_config.session_ref + ":deepseek",
        product_candidate_digest=product_candidate_digest,
        chat_binding_digest=binding.digest,
        configuration=deepseek_configuration,
        maximum_turns=session_config.required_conversation_turns,
        maximum_dispatches_per_turn=(
            session_config.maximum_dispatches_per_turn
        ),
        maximum_total_dispatches=(
            session_config.maximum_total_dispatches_per_provider
        ),
        authorized_at=session_config.authorized_at,
        expires_at=session_config.expires_at,
        authorization_ref=authorization_ref,
        authorization_message_digest=(
            session_config.authorization_message_digest
        ),
    )
    primary_route = _route_spec(
        ordinal=1,
        role=EngineeringProviderRouteRole.PRIMARY,
        configuration=ark_configuration,
        authority=ark_authority,
    )
    fallback_route = _route_spec(
        ordinal=2,
        role=EngineeringProviderRouteRole.FALLBACK,
        configuration=deepseek_configuration,
        authority=deepseek_authority,
    )
    route_plan = EngineeringProviderRoutePlan.create(
        binding=binding,
        primary=primary_route,
        fallback=fallback_route,
    )
    evidence_tools = EngineeringAgentEvidenceToolConfiguration.create(
        project_name=session_config.project_name,
        response_language=session_config.response_language,
        repository_id=repository_id,
        binding_id=binding_id,
        repository_revision=repository_revision,
        source_profile_ref=profile.profile_ref,
        source_profile_digest=profile.profile_digest,
        world_model_read_authority_digest=cognition.read_authority_digest,
        source_allowlist=source_allowlist,
        excluded_source_paths=session_config.excluded_source_paths,
        provider_disclosure_policy=ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
    )
    ark_repository_ref = _gateway_repository_ref(
        session_config=session_config,
        route=ark_route_config,
    )
    deepseek_repository_ref = _gateway_repository_ref(
        session_config=session_config,
        route=deepseek_route_config,
    )
    ark_runtime = create_ark_engineering_chat_provider_model_runtime(
        repository=ark_gateway_repository,
        gateway_repository_ref=ark_repository_ref,
        binding=binding,
        provider_configuration=ark_provider,
        qualification=ark_qualification,
        configuration=ark_configuration,
        session_authority=ark_authority,
        at=current,
        clock=lambda: current,
    )
    deepseek_runtime = create_deepseek_engineering_chat_provider_model_runtime(
        repository=deepseek_gateway_repository,
        gateway_repository_ref=deepseek_repository_ref,
        binding=binding,
        provider_configuration=deepseek_provider,
        qualification=deepseek_qualification,
        configuration=deepseek_configuration,
        session_authority=deepseek_authority,
        at=current,
        clock=lambda: current,
    )
    worker = LocalGitRetrievalWorker(
        source_repository,
        repository_id=repository_id,
        binding_id=binding_id,
        source_profile=profile,
    )
    runtime = prepare_engineering_chat_session_runtime(
        binding=binding,
        product_tree=product_tree,
        evidence_tools=evidence_tools,
        cognition_projector=cognition,
        source_broker=SourceBroker(source_profile=profile),
        retrieval_worker=worker,
        primary_provider_runtime=ark_runtime,
        fallback_provider_runtime=deepseek_runtime,
        route_plan=route_plan,
        checked_at=current,
        required_conversation_turns=(
            session_config.required_conversation_turns
        ),
        artifact_session_config_digest=session_config.file_digest,
        fixed_command_wired=True,
    )
    if (
        runtime.receipt.status
        != ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "artifact Session did not produce the loaded runtime status",
        )
    core = {
        "schema": ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_SCHEMA,
        "status": ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS,
        "session_config_file_digest": session_config.file_digest.value,
        "product_candidate_commit": product_commit,
        "product_candidate_tree": product_tree,
        "chat_binding_digest": binding.digest.value,
        "evidence_tool_configuration_digest": evidence_tools.digest.value,
        "world_model_read_authority_digest": (
            cognition.read_authority_digest.value
        ),
        "cognition_profiles": tuple(
            item.public_status() for item in prepared_cognition_profiles
        ),
        "ark_conformance_result_digest": ark_qualification.result_digest.value,
        "deepseek_conformance_result_digest": (
            deepseek_qualification.result_digest.value
        ),
        "session_runtime_receipt_digest": runtime.receipt.digest.value,
        "source_read_performed_at_preparation": False,
        "credential_resolved_at_preparation": False,
        "provider_dispatch_count_at_preparation": 0,
        "listener_started_at_preparation": False,
        "request_retry_allowed": False,
        "production_activation": "NOT_EXECUTED",
        "checked_at": _time(current),
    }
    return PreparedEngineeringChatArtifactSession(
        runtime=runtime,
        session_config=session_config,
        product_candidate_commit=product_commit,
        product_candidate_tree=product_tree,
        cognition_profiles=prepared_cognition_profiles,
        world_model_read_authority_digest=cognition.read_authority_digest,
        ark_conformance_result_digest=ark_qualification.result_digest,
        deepseek_conformance_result_digest=deepseek_qualification.result_digest,
        preparation_digest=digest_of(core),
    )


def _cognition_profiles(
    document: Mapping[str, object],
    *,
    schema: object,
) -> tuple[EngineeringChatArtifactCognitionProfileConfig, ...]:
    if schema == ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1:
        snapshot_id = document["cognition_snapshot_id"]
        if snapshot_id is not None:
            snapshot_id = _required_text(document, "cognition_snapshot_id")
        return (
            EngineeringChatArtifactCognitionProfileConfig(
                ordinal=0,
                profile_ref=None,
                schema_ref=None,
                source_binding_id=None,
                ordered_envelope=_required_absolute_path_text(
                    document, "ordered_envelope"
                ),
                ordered_bundle_digest=None,
                ordered_file_digest=None,
                snapshot_bundles=_required_absolute_path_text_list(
                    document, "snapshot_bundles"
                ),
                snapshot_bundle_digests=None,
                snapshot_file_digests=None,
                cognition_snapshot_id=snapshot_id,
            ),
        )

    value = document.get("cognition_profiles")
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session requires one to 16 cognition Profiles",
        )
    profiles: list[EngineeringChatArtifactCognitionProfileConfig] = []
    artifact_paths: list[str] = []
    for ordinal, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != _COGNITION_PROFILE_FIELDS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering Chat cognition Profile contains missing or unknown fields",
            )
        if type(item.get("ordinal")) is not int or item.get("ordinal") != ordinal:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat cognition Profiles are not in exact zero-based order",
            )
        source_binding_id = _stable_id(
            _required_text(item, "source_binding_id"),
            "cognition Profile Source Binding ID",
        )
        if source_binding_id.kind != "binding":
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering Chat cognition Profile Source Binding ID is not typed",
            )
        snapshot_bundles = _required_absolute_path_text_list(
            item, "snapshot_bundles"
        )
        snapshot_bundle_digests = _required_digest_list(
            item, "snapshot_bundle_digests"
        )
        snapshot_file_digests = _required_digest_list(
            item, "snapshot_file_digests"
        )
        if not (
            len(snapshot_bundles)
            == len(snapshot_bundle_digests)
            == len(snapshot_file_digests)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat cognition Profile Snapshot manifests differ in length",
            )
        ordered_envelope = _required_absolute_path_text(
            item, "ordered_envelope"
        )
        artifact_paths.extend((ordered_envelope, *snapshot_bundles))
        profiles.append(
            EngineeringChatArtifactCognitionProfileConfig(
                ordinal=ordinal,
                profile_ref=_required_text(item, "profile_ref"),
                schema_ref=_required_text(item, "schema_ref"),
                source_binding_id=source_binding_id,
                ordered_envelope=ordered_envelope,
                ordered_bundle_digest=_required_digest(
                    item, "ordered_bundle_digest"
                ),
                ordered_file_digest=_required_digest(
                    item, "ordered_file_digest"
                ),
                snapshot_bundles=snapshot_bundles,
                snapshot_bundle_digests=snapshot_bundle_digests,
                snapshot_file_digests=snapshot_file_digests,
                cognition_snapshot_id=_required_text(
                    item, "cognition_snapshot_id"
                ),
            )
        )
    if (
        len({item.profile_ref for item in profiles}) != len(profiles)
        or len(artifact_paths) != len(set(artifact_paths))
        or len({item.cognition_snapshot_id for item in profiles})
        != len(profiles)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat cognition Profile identities or artifacts are duplicated",
        )
    return tuple(profiles)


def _load_cognition_profile_artifacts(
    *,
    config: EngineeringChatArtifactCognitionProfileConfig,
    store: FileStructureReadBundleStore,
) -> _LoadedEngineeringChatCognitionProfile:
    ordered_path = _canonical_regular_file(
        config.ordered_envelope,
        "ordered Structure Read Bundle",
    )
    snapshot_paths = tuple(
        _canonical_regular_file(path, "Snapshot Structure Read Bundle")
        for path in config.snapshot_bundles
    )
    ordered, ordered_file_digest = store.read_ordered(str(ordered_path))
    loaded = tuple(store.read_snapshot(str(path)) for path in snapshot_paths)
    view = StructureViewService(ordered, loaded)
    snapshot_bundle = _select_cognition_snapshot(
        loaded=loaded,
        requested_snapshot_id=config.cognition_snapshot_id,
    )
    projector = StructureBundleWorldModelCognitionProjector(
        view=view,
        snapshot_bundle=snapshot_bundle,
    )
    snapshot_file_digests = tuple(item[1] for item in loaded)
    if (
        config.ordered_bundle_digest is not None
        and (
            view.ordered_bundle_digest != config.ordered_bundle_digest
            or ordered_file_digest != config.ordered_file_digest
            or view.snapshot_bundle_digests
            != config.snapshot_bundle_digests
            or snapshot_file_digests != config.snapshot_file_digests
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat cognition Profile artifact digests drifted",
        )
    return _LoadedEngineeringChatCognitionProfile(
        config=config,
        view=view,
        projector=projector,
        ordered_file_digest=ordered_file_digest,
        snapshot_file_digests=snapshot_file_digests,
    )


def _require_configured_cognition_profiles(
    *,
    configs: Sequence[EngineeringChatArtifactCognitionProfileConfig],
    loaded: Sequence[_LoadedEngineeringChatCognitionProfile],
    capabilities: Sequence[CognitionProfileCapability],
) -> None:
    if not (len(configs) == len(loaded) == len(capabilities)):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat cognition Profile counts drifted",
        )
    for config, loaded_profile, capability in zip(
        configs, loaded, capabilities, strict=True
    ):
        if (
            capability.ordinal != config.ordinal
            or capability.snapshot_id
            != loaded_profile.projector.snapshot_bundle.snapshot_id
            or capability.snapshot_bundle_digest
            != loaded_profile.projector.snapshot_bundle.digest
            or capability.read_authority_digest
            != loaded_profile.projector.read_authority_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat cognition Profile authority drifted while composing",
            )
        if config.profile_ref is not None and (
            capability.profile_ref != config.profile_ref
            or capability.schema_ref != config.schema_ref
            or capability.source_binding_id != config.source_binding_id
            or capability.snapshot_id.value != config.cognition_snapshot_id
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat cognition Profile identity differs from Session authority",
            )


def _provider_routes(
    document: Mapping[str, object],
) -> tuple[EngineeringChatArtifactProviderRouteConfig, ...]:
    value = document.get("provider_routes")
    if not isinstance(value, list) or len(value) != len(_PROVIDER_ROUTE_ORDER):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session requires exactly two Provider routes",
        )
    routes: list[EngineeringChatArtifactProviderRouteConfig] = []
    for ordinal, (item, provider_type) in enumerate(
        zip(value, _PROVIDER_ROUTE_ORDER, strict=True),
        start=1,
    ):
        if not isinstance(item, Mapping) or set(item) != _PROVIDER_ROUTE_FIELDS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering Chat Provider route contains missing or unknown fields",
            )
        if (
            type(item.get("ordinal")) is not int
            or item.get("ordinal") != ordinal
            or item.get("provider_type") != provider_type
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat Provider routes are not exact Ark-to-DeepSeek order",
            )
        routes.append(
            EngineeringChatArtifactProviderRouteConfig(
                ordinal=ordinal,
                provider_type=provider_type,
                conformance_result=_required_absolute_path_text(
                    item, "conformance_result"
                ),
                gateway_database=_required_absolute_path_text(
                    item, "gateway_database"
                ),
            )
        )
    return tuple(routes)


def _route_spec(*, ordinal, role, configuration, authority):
    return EngineeringProviderRouteSpec.create(
        ordinal=ordinal,
        role=role,
        provider_type=configuration.provider_type,
        endpoint=configuration.endpoint,
        model_ref=configuration.model_ref,
        provider_configuration_digest=configuration.digest,
        session_disclosure_authority_digest=authority.digest,
        qualification_ref=configuration.qualification_ref,
        maximum_dispatches_per_turn=authority.maximum_dispatches_per_turn,
    )


def _gateway_repository_ref(
    *,
    session_config: EngineeringChatArtifactSessionConfig,
    route: EngineeringChatArtifactProviderRouteConfig,
) -> str:
    identity = digest_of(
        [
            "ENGINEERING_CHAT_PRIVATE_GATEWAY_REPOSITORY@1",
            session_config.file_digest.value,
            route.ordinal,
            route.provider_type,
        ]
    )
    return f"sqlite-model-gateway:{route.provider_type}:{identity.value}"


def _provider_terminal_audit(runtime) -> dict[str, object]:
    audits = runtime.model_boundary.audits
    requests = runtime.authorizer.disclosure_requests
    authorizations = runtime.authorizer.issued_authorizations
    if len(requests) != len(authorizations):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat Provider disclosure audit is incomplete",
        )
    provider_dispatch_count = sum(
        item.receipt.provider_dispatch_count for item in audits
    )
    if runtime.provider_type == "DEEPSEEK":
        transport_session_audit = deepseek_transport_session_audit(
            runtime.transport
        )
    elif runtime.provider_type == "VOLCENGINE_ARK":
        transport_session_audit = ark_transport_session_audit(runtime.transport)
    else:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat Provider transport audit type is unsupported",
        )
    return {
        "provider_type": runtime.provider_type,
        "runtime_digest": runtime.digest.value,
        "session_disclosure_authority_digest": (
            runtime.session_authority.digest.value
        ),
        "disclosure_request_digests": tuple(item.digest.value for item in requests),
        "disclosure_authorization_digests": tuple(
            item.digest.value for item in authorizations
        ),
        "model_dispatch_audit_digests": tuple(
            item.digest.value for item in audits
        ),
        "model_call_receipt_digests": tuple(
            item.receipt.digest.value for item in audits
        ),
        "provider_dispatch_count": provider_dispatch_count,
        "transport_session_audit": transport_session_audit,
        "request_retry_count": 0,
        "production_activation": "NOT_EXECUTED",
    }


def _canonical_private_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
        metadata = path.stat()
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            f"{label} does not exist",
        ) from exc
    if (
        resolved != path
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o600
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            f"{label} must be a canonical owner-private regular file",
        )
    return path


def _canonical_regular_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            f"{label} does not exist",
        ) from exc
    if resolved != path or not resolved.is_file():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be a canonical non-symlink regular file",
        )
    return path


def _unique_json_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 65_536
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} is invalid",
        )
    return value


def _required_text_list(
    document: Mapping[str, object],
    field: str,
) -> tuple[str, ...]:
    value = document.get(field)
    if not isinstance(value, list) or not value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} must be a non-empty list",
        )
    values = tuple(value)
    if any(
        not isinstance(item, str)
        or not item
        or item != item.strip()
        or len(item.encode("utf-8")) > 65_536
        for item in values
    ) or len(values) != len(set(values)):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} contains invalid or duplicate text",
        )
    return values


def _required_absolute_path_text(
    document: Mapping[str, object],
    field: str,
) -> str:
    value = _required_text(document, field)
    path = Path(value)
    if not path.is_absolute():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} must be an absolute path",
        )
    return value


def _required_absolute_path_text_list(
    document: Mapping[str, object],
    field: str,
) -> tuple[str, ...]:
    values = _required_text_list(document, field)
    if any(not Path(item).is_absolute() for item in values):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} must contain absolute paths",
        )
    return values


def _required_digest(
    document: Mapping[str, object], field: str
) -> Digest:
    try:
        return Digest(_required_text(document, field))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} is not a digest",
        ) from exc


def _required_digest_list(
    document: Mapping[str, object], field: str
) -> tuple[Digest, ...]:
    values = _required_text_list(document, field)
    try:
        return tuple(Digest(item) for item in values)
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} contains an invalid digest",
        ) from exc


def _required_positive_int(document: Mapping[str, object], field: str) -> int:
    value = document.get(field)
    if type(value) is not int or value < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} must be positive",
        )
    return value


def _required_time(document: Mapping[str, object], field: str) -> datetime:
    value = _required_text(document, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} is not a time",
        ) from exc
    current = _aware_utc(parsed)
    if _time(current) != value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"Engineering Chat artifact session field {field} is not canonical UTC",
        )
    return current


def _source_paths_overlap(left: str, right: str) -> bool:
    return (
        left == "."
        or right == "."
        or left == right
        or left.startswith(right + "/")
        or right.startswith(left + "/")
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat artifact session time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA",
    "ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1",
    "ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_SCHEMA",
    "ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS",
    "EngineeringChatArtifactCognitionProfileConfig",
    "EngineeringChatArtifactProviderRouteConfig",
    "EngineeringChatArtifactSessionConfig",
    "PreparedEngineeringChatArtifactSession",
    "PreparedEngineeringChatCognitionProfileArtifact",
    "load_engineering_chat_artifact_session_config",
    "prepare_engineering_chat_artifact_session",
]
