from src.agents.base import Agent
from src.models import IntakeResult, SpecialistResult, TicketRequest


class SpecialistAgent(Agent):
    def __init__(self, category: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

    async def diagnose(self, request: TicketRequest, intake: IntakeResult, context: str) -> SpecialistResult:
        return await self.run(
            f"КАТЕГОРИЯ: {self.category}\n"
            f"ЗАЯВКА: {request.text}\n"
            f"УСТРОЙСТВО: {request.device or 'не указано'}; ОС: {request.os or 'не указана'}; "
            f"ЛОКАЦИЯ: {request.location or 'не указана'}\n"
            f"РЕЗЮМЕ ДИСПЕТЧЕРА: {intake.summary}\n\n"
            f"ФРАГМЕНТЫ БАЗЫ ЗНАНИЙ:\n{context or 'релевантных фрагментов нет'}",
            SpecialistResult,
        )
