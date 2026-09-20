from src.agents.base import Agent
from src.models import PolicyResult, SpecialistResult, TicketRequest


class PolicyAgent(Agent):
    async def review(self, request: TicketRequest, results: list[SpecialistResult], allow_high_risk: bool) -> PolicyResult:
        return await self.run(
            f"ИСХОДНАЯ ЗАЯВКА:\n{request.text}\n\n"
            f"ПРЕДЛОЖЕННАЯ ДИАГНОСТИКА:\n{[r.model_dump() for r in results]}\n\n"
            f"РАЗРЕШИТЬ ВЫСОКОРИСКОВЫЕ ДЕЙСТВИЯ: {allow_high_risk}",
            PolicyResult,
        )
