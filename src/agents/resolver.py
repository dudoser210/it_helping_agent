from typing import Literal

from pydantic import BaseModel

from src.agents.base import Agent
from src.models import DiagnosticStep, IntakeResult, PolicyResult, SpecialistResult, TicketRequest


class ResolutionDraft(BaseModel):
    status: Literal["resolved", "needs_info", "escalated"]
    response: str
    steps: list[DiagnosticStep]
    questions: list[str]
    escalation_reason: str | None = None


class ResolverAgent(Agent):
    async def resolve(
        self,
        request: TicketRequest,
        intake: IntakeResult,
        specialist_results: list[SpecialistResult],
        policy: PolicyResult,
    ) -> ResolutionDraft:
        return await self.run(
            f"ЗАЯВКА: {request.text}\n"
            f"КЛАССИФИКАЦИЯ: {intake.model_dump()}\n"
            f"ЗАКЛЮЧЕНИЯ СПЕЦИАЛИСТОВ: {[r.model_dump() for r in specialist_results]}\n"
            f"ПРОВЕРКА ПОЛИТИКИ: {policy.model_dump()}",
            ResolutionDraft,
        )
