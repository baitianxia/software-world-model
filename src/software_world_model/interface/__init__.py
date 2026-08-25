"""User-facing adapters that call application services only.

The package root intentionally exposes its public names lazily.  Isolated
product roles import narrow interface modules and must not acquire unrelated
Update/parser dependencies merely because Python initializes this package.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any


_EXPORT_MODULES = {
    "EngineeringChatCandidatePreflightReceipt": ".engineering_chat_candidate",
    "engineering_chat_product_candidate_digest": ".engineering_chat_candidate",
    "engineering_chat_single_provider_route_ref": ".engineering_chat_candidate",
    "prepare_engineering_chat_candidate_preflight": ".engineering_chat_candidate",
    "EngineeringChatProviderAttemptDependencies": ".engineering_chat_provider_launcher",
    "EngineeringChatProviderAttemptFactory": ".engineering_chat_provider_launcher",
    "EngineeringChatProviderLauncherReceipt": ".engineering_chat_provider_launcher",
    "PreparedEngineeringChatProviderLauncher": ".engineering_chat_provider_launcher",
    "prepare_engineering_chat_provider_launcher": ".engineering_chat_provider_launcher",
    "EngineeringChatProviderModelRuntime": ".engineering_chat_provider_runtime",
    "create_ark_engineering_chat_provider_model_runtime": ".engineering_chat_provider_runtime",
    "create_deepseek_engineering_chat_provider_model_runtime": ".engineering_chat_provider_runtime",
    "engineering_chat_ark_model_configuration": ".engineering_chat_provider_runtime",
    "engineering_chat_deepseek_model_configuration": ".engineering_chat_provider_runtime",
    "EngineeringChatEvidenceToolFactory": ".engineering_chat_session_runtime",
    "EngineeringChatSessionRuntimeReceipt": ".engineering_chat_session_runtime",
    "PreparedEngineeringChatSessionRuntime": ".engineering_chat_session_runtime",
    "prepare_engineering_chat_session_runtime": ".engineering_chat_session_runtime",
    "EngineeringChatArtifactProviderRouteConfig": ".engineering_chat_session_artifact",
    "EngineeringChatArtifactSessionConfig": ".engineering_chat_session_artifact",
    "PreparedEngineeringChatArtifactSession": ".engineering_chat_session_artifact",
    "load_engineering_chat_artifact_session_config": ".engineering_chat_session_artifact",
    "prepare_engineering_chat_artifact_session": ".engineering_chat_session_artifact",
    "EngineeringChatBrowserApplication": ".engineering_chat_browser",
    "PreparedEngineeringChatAccess": ".engineering_chat_alpha_cli",
    "prepare_engineering_chat_access": ".engineering_chat_alpha_cli",
    "EngineeringQuestionBrowserApplication": ".engineering_qa_browser",
    "EngineeringQuestionRequestFactory": ".engineering_qa_browser",
    "EngineeringQuestionWebRuntimeStatus": ".engineering_qa_browser",
    "EngineeringQuestionWebProduct": ".engineering_qa_browser",
    "ExactAuthorizedEngineeringQuestionRequestFactory": ".engineering_qa_browser",
    "FixedEngineeringQuestionRequestFactory": ".engineering_qa_browser",
    "InMemoryEngineeringQuestionWebProduct": ".engineering_qa_browser",
    "DeepSeekEngineeringQuestionRoleRuntime": ".engineering_qa_live",
    "DeepSeekEngineeringQuestionBrowserAssembly": ".engineering_qa_live",
    "create_deepseek_engineering_question_browser_assembly": ".engineering_qa_live",
    "create_deepseek_engineering_question_role_runtime": ".engineering_qa_live",
    "engineering_question_deepseek_configuration": ".engineering_qa_live",
    "ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA": ".engineering_qa_preview_cli",
    "PreparedEngineeringQuestionPreview": ".engineering_qa_preview_cli",
    "engineering_question_preview_subject_digest": ".engineering_qa_preview_cli",
    "prepare_engineering_question_preview": ".engineering_qa_preview_cli",
    "LocalGitEvidenceClassProfile": ".engineering_qa_source",
    "LocalGitRetrievalWorker": ".engineering_qa_source",
    "ActivatedApplicationAssembly": ".agentic_runtime",
    "AgenticTaskServiceAssembly": ".agentic_runtime",
    "BOUNDED_WORLD_MODEL_EVALUATION_PAGE_FORMAT": ".world_model_evaluation",
    "EvidenceTaskServiceAssembly": ".agentic_runtime",
    "ApplicationRuntime": ".runtime",
    "WORLD_MODEL_EVALUATION_PAGE_FORMAT": ".world_model_evaluation",
    "activate_browser_experience": ".agentic_runtime",
    "agentic_task_capability_registry": ".agentic_runtime",
    "agentic_task_strategy_definition": ".agentic_runtime",
    "assemble_activated_task_services": ".agentic_runtime",
    "assemble_activated_evidence_services": ".agentic_runtime",
    "build_activated_application_runtime": ".agentic_runtime",
    "load_capability_qualification_proof": ".agentic_runtime",
    "evidence_task_capability_registry": ".agentic_runtime",
    "evidence_task_strategy_definition": ".agentic_runtime",
    "read_world_model_evaluation_page": ".world_model_evaluation",
    "world_model_evaluation_page_envelope": ".world_model_evaluation",
    "world_model_evaluation_page_payload": ".world_model_evaluation",
    "write_world_model_evaluation_page": ".world_model_evaluation",
}


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *_EXPORT_MODULES})


if TYPE_CHECKING:
    from .engineering_chat_candidate import (
        EngineeringChatCandidatePreflightReceipt,
        engineering_chat_product_candidate_digest,
        engineering_chat_single_provider_route_ref,
        prepare_engineering_chat_candidate_preflight,
    )
    from .engineering_chat_browser import EngineeringChatBrowserApplication
    from .engineering_chat_provider_launcher import (
        EngineeringChatProviderAttemptDependencies,
        EngineeringChatProviderAttemptFactory,
        EngineeringChatProviderLauncherReceipt,
        PreparedEngineeringChatProviderLauncher,
        prepare_engineering_chat_provider_launcher,
    )
    from .engineering_chat_provider_runtime import (
        EngineeringChatProviderModelRuntime,
        create_ark_engineering_chat_provider_model_runtime,
        create_deepseek_engineering_chat_provider_model_runtime,
        engineering_chat_ark_model_configuration,
        engineering_chat_deepseek_model_configuration,
    )
    from .engineering_chat_session_runtime import (
        EngineeringChatEvidenceToolFactory,
        EngineeringChatSessionRuntimeReceipt,
        PreparedEngineeringChatSessionRuntime,
        prepare_engineering_chat_session_runtime,
    )
    from .engineering_chat_session_artifact import (
        EngineeringChatArtifactProviderRouteConfig,
        EngineeringChatArtifactSessionConfig,
        PreparedEngineeringChatArtifactSession,
        load_engineering_chat_artifact_session_config,
        prepare_engineering_chat_artifact_session,
    )
    from .engineering_chat_alpha_cli import (
        PreparedEngineeringChatAccess,
        prepare_engineering_chat_access,
    )
    from .engineering_qa_browser import (
        EngineeringQuestionBrowserApplication,
        EngineeringQuestionRequestFactory,
        EngineeringQuestionWebRuntimeStatus,
        EngineeringQuestionWebProduct,
        ExactAuthorizedEngineeringQuestionRequestFactory,
        FixedEngineeringQuestionRequestFactory,
        InMemoryEngineeringQuestionWebProduct,
    )
    from .engineering_qa_source import (
        LocalGitEvidenceClassProfile,
        LocalGitRetrievalWorker,
    )
    from .engineering_qa_live import (
        DeepSeekEngineeringQuestionRoleRuntime,
        DeepSeekEngineeringQuestionBrowserAssembly,
        create_deepseek_engineering_question_browser_assembly,
        create_deepseek_engineering_question_role_runtime,
        engineering_question_deepseek_configuration,
    )
    from .engineering_qa_preview_cli import (
        ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA,
        PreparedEngineeringQuestionPreview,
        engineering_question_preview_subject_digest,
        prepare_engineering_question_preview,
    )
    from .agentic_runtime import (
        ActivatedApplicationAssembly,
        AgenticTaskServiceAssembly,
        EvidenceTaskServiceAssembly,
        activate_browser_experience,
        agentic_task_capability_registry,
        agentic_task_strategy_definition,
        assemble_activated_task_services,
        assemble_activated_evidence_services,
        build_activated_application_runtime,
        evidence_task_capability_registry,
        evidence_task_strategy_definition,
        load_capability_qualification_proof,
    )
    from .runtime import ApplicationRuntime
    from .world_model_evaluation import (
        BOUNDED_WORLD_MODEL_EVALUATION_PAGE_FORMAT,
        WORLD_MODEL_EVALUATION_PAGE_FORMAT,
        read_world_model_evaluation_page,
        world_model_evaluation_page_envelope,
        world_model_evaluation_page_payload,
        write_world_model_evaluation_page,
    )

__all__ = [
    "EngineeringChatBrowserApplication",
    "EngineeringChatCandidatePreflightReceipt",
    "engineering_chat_product_candidate_digest",
    "engineering_chat_single_provider_route_ref",
    "prepare_engineering_chat_candidate_preflight",
    "EngineeringChatProviderAttemptDependencies",
    "EngineeringChatProviderAttemptFactory",
    "EngineeringChatProviderLauncherReceipt",
    "PreparedEngineeringChatProviderLauncher",
    "prepare_engineering_chat_provider_launcher",
    "EngineeringChatProviderModelRuntime",
    "create_ark_engineering_chat_provider_model_runtime",
    "create_deepseek_engineering_chat_provider_model_runtime",
    "engineering_chat_ark_model_configuration",
    "engineering_chat_deepseek_model_configuration",
    "EngineeringChatEvidenceToolFactory",
    "EngineeringChatSessionRuntimeReceipt",
    "PreparedEngineeringChatSessionRuntime",
    "prepare_engineering_chat_session_runtime",
    "EngineeringChatArtifactProviderRouteConfig",
    "EngineeringChatArtifactSessionConfig",
    "PreparedEngineeringChatArtifactSession",
    "load_engineering_chat_artifact_session_config",
    "prepare_engineering_chat_artifact_session",
    "PreparedEngineeringChatAccess",
    "prepare_engineering_chat_access",
    "EngineeringQuestionBrowserApplication",
    "EngineeringQuestionRequestFactory",
    "EngineeringQuestionWebRuntimeStatus",
    "EngineeringQuestionWebProduct",
    "ExactAuthorizedEngineeringQuestionRequestFactory",
    "FixedEngineeringQuestionRequestFactory",
    "InMemoryEngineeringQuestionWebProduct",
    "DeepSeekEngineeringQuestionRoleRuntime",
    "DeepSeekEngineeringQuestionBrowserAssembly",
    "create_deepseek_engineering_question_browser_assembly",
    "create_deepseek_engineering_question_role_runtime",
    "engineering_question_deepseek_configuration",
    "ENGINEERING_QA_PREVIEW_SUBJECT_SCHEMA",
    "PreparedEngineeringQuestionPreview",
    "engineering_question_preview_subject_digest",
    "prepare_engineering_question_preview",
    "LocalGitEvidenceClassProfile",
    "LocalGitRetrievalWorker",
    "ActivatedApplicationAssembly",
    "AgenticTaskServiceAssembly",
    "BOUNDED_WORLD_MODEL_EVALUATION_PAGE_FORMAT",
    "EvidenceTaskServiceAssembly",
    "ApplicationRuntime",
    "WORLD_MODEL_EVALUATION_PAGE_FORMAT",
    "activate_browser_experience",
    "agentic_task_capability_registry",
    "agentic_task_strategy_definition",
    "assemble_activated_task_services",
    "assemble_activated_evidence_services",
    "build_activated_application_runtime",
    "load_capability_qualification_proof",
    "evidence_task_capability_registry",
    "evidence_task_strategy_definition",
    "read_world_model_evaluation_page",
    "world_model_evaluation_page_envelope",
    "world_model_evaluation_page_payload",
    "write_world_model_evaluation_page",
]
