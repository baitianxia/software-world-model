from __future__ import annotations

from typing import Protocol


class KnowledgeUpdateServices(Protocol):
    def update_knowledge(
        self, scope_id: str, build_profile: str = "structure-core"
    ) -> dict[str, object]: ...


class SchedulerAdapter:
    """Turns a time trigger into the same fixed Knowledge Update use case as CLI."""

    def __init__(self, application: KnowledgeUpdateServices):
        self.application = application

    def trigger_update(
        self, scope_id: str, build_profile: str = "structure-core"
    ) -> dict[str, object]:
        return self.application.update_knowledge(scope_id, build_profile)
