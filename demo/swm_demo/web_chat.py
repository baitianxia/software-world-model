from __future__ import annotations

from dataclasses import asdict

from swm_demo.agent_orchestrator import AgentOrchestrator


class WebChatAdapter:
    """Protocol adapter: it delegates every natural-language request to orchestration."""

    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    def send(self, request: str, scope_id: str) -> dict[str, object]:
        return asdict(self.orchestrator.handle(request, scope_id))
