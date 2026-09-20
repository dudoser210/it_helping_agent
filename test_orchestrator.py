from pathlib import Path

from src.agents.resolver import ResolutionDraft
from src.config import Settings
from src.models import (
    Category,
    DiagnosticStep,
    IntakeResult,
    PolicyResult,
    Priority,
    SpecialistResult,
    TicketRequest,
)
from src.orchestrator import HelpingOrchestrator


async def test_end_to_end_graph_without_llm(tmp_path: Path):
    settings = Settings(
        data_dir=tmp_path,
        prompt_dir=Path("prompts"),
        knowledge_dir=Path("knowledge"),
        otel_enabled=False,
    )
    system = HelpingOrchestrator(settings)

    async def classify(request, history):
        return IntakeResult(categories=[Category.wifi], priority=Priority.medium, summary="Проблема DNS")

    async def diagnose(request, intake, context):
        return SpecialistResult(
            agent="wifi_specialist", diagnosis="DNS недоступен", confidence=0.8,
            steps=[DiagnosticStep(order=1, action="Переподключиться к Wi-Fi", expected_result="Сайты открываются")],
        )

    async def review(request, results, allow_high_risk):
        return PolicyResult(approved=True, sanitized_text=request.text)

    async def resolve(request, intake, specialist_results, policy):
        return ResolutionDraft(
            status="resolved", response="Вероятна проблема DNS.",
            steps=specialist_results[0].steps, questions=[],
        )

    system.intake.classify = classify
    system.specialists["wifi"].diagnose = diagnose
    system.policy.review = review
    system.resolver.resolve = resolve

    response = await system.process(TicketRequest(employee_id="u-1", text="Wi-Fi есть, сайты не открываются"))
    assert response.status == "resolved"
    assert response.agents_used == ["intake", "wifi_specialist", "policy", "resolver"]
    assert system.memory.recent_for_employee("u-1")[0]["ticket_id"] == response.ticket_id
