from src.agents.base import Agent
from src.models import IntakeResult, TicketRequest


class IntakeAgent(Agent):
    async def classify(self, request: TicketRequest, history: list[dict]) -> IntakeResult:
        return await self.run(
            "ЗАЯВКА:\n"
            f"{request.model_dump_json(indent=2)}\n\n"
            f"ПОСЛЕДНИЕ ЗАЯВКИ ЭТОГО СОТРУДНИКА:\n{history or 'нет'}",
            IntakeResult,
        )
