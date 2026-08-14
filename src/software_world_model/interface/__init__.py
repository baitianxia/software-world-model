"""User-facing adapters that call application services only.

The package root intentionally exposes its public names lazily.  Isolated
product roles import narrow interface modules and must not acquire unrelated
Update/parser dependencies merely because Python initializes this package.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any


_EXPORT_MODULES = {
    "ActivatedApplicationAssembly": ".agentic_runtime",
    "AgenticTaskServiceAssembly": ".agentic_runtime",
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
        WORLD_MODEL_EVALUATION_PAGE_FORMAT,
        read_world_model_evaluation_page,
        world_model_evaluation_page_envelope,
        world_model_evaluation_page_payload,
        write_world_model_evaluation_page,
    )

__all__ = [
    "ActivatedApplicationAssembly",
    "AgenticTaskServiceAssembly",
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
