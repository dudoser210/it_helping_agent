import asyncio
import logging
import time
import uuid

from src.agents.intake import IntakeAgent
from src.agents.policy import PolicyAgent
from src.agents.resolver import ResolverAgent
from src.agents.specialist import SpecialistAgent
from src.config import Settings
from src.llm import OllamaClient
from src.memory.retriever import KnowledgeRetriever
from src.memory.store import TicketMemory
from src.models import Category, SpecialistResult, TicketRequest, TicketResponse
from src.observability.metrics import REQUEST_LATENCY, REQUESTS
from src.observability.tracing import span
from src.safety import filter_steps, output_is_safe, redact_secrets

logger = logging.getLogger(__name__)


class HelpingOrchestrator:
    """Deterministic DAG: intake -> selected specialists -> policy -> resolver."""

    def __init__(self, settings: Settings, tracer=None):
        self.settings = settings
        self.tracer = tracer
        self.llm = OllamaClient(settings)
        p = settings.prompt_dir
        self.intake = IntakeAgent("intake", p / "intake_agent.md", self.llm)
        self.policy = PolicyAgent("policy", p / "policy_agent.md", self.llm)
        self.resolver = ResolverAgent("resolver", p / "resolver_agent.md", self.llm)
        self.specialists = {
            category: SpecialistAgent(
                category=category,
                name=f"{category}_specialist",
                prompt_file=p / f"{category}_agent.md",
                llm=self.llm,
            )
            for category in ("wifi", "printer", "access", "software")
        }
        self.retriever = KnowledgeRetriever(settings.knowledge_dir)
        self.memory = TicketMemory(settings.database_path)
        self.semaphore = asyncio.Semaphore(settings.agent_max_parallel)

    async def _specialist(self, category: str, request: TicketRequest, intake) -> tuple[SpecialistResult, list[str]]:
        docs = self.retriever.search(request.text, self.settings.rag_top_k, category)
        async with self.semaphore:
            with span(self.tracer, f"agent.{category}", {"helping.category": category}):
                result = await self.specialists[category].diagnose(
                    request, intake, self.retriever.context(docs)
                )
        return result, [doc.source for doc in docs]

    async def process(self, request: TicketRequest) -> TicketResponse:
        started = time.perf_counter()
        ticket_id = f"HD-{uuid.uuid4().hex[:8].upper()}"
        with span(self.tracer, "ticket.process", {"helping.ticket_id": ticket_id}):
            history = self.memory.recent_for_employee(request.employee_id, self.settings.max_history_items)
            with span(self.tracer, "agent.intake"):
                intake = await self.intake.classify(request, history)

            categories = [c.value for c in intake.categories if c != Category.unknown]
            if not categories:
                categories = ["wifi", "printer", "access", "software"]
            categories = list(dict.fromkeys(categories))[:4]

            pairs = await asyncio.gather(
                *(self._specialist(category, request, intake) for category in categories)
            )
            specialist_results = [pair[0] for pair in pairs]
            sources = list(dict.fromkeys(source for pair in pairs for source in pair[1]))

            with span(self.tracer, "agent.policy"):
                policy = await self.policy.review(
                    request, specialist_results, self.settings.allow_high_risk_actions
                )
            for result in specialist_results:
                result.steps, blocked = filter_steps(result.steps, self.settings.allow_high_risk_actions)
                policy.blocked_actions.extend(blocked)
            policy.sanitized_text = redact_secrets(policy.sanitized_text)
            if policy.blocked_actions:
                policy.approved = False
            with span(self.tracer, "agent.resolver"):
                draft = await self.resolver.resolve(request, intake, specialist_results, policy)
            draft.steps, post_blocked = filter_steps(draft.steps, self.settings.allow_high_risk_actions)
            if post_blocked or not output_is_safe(draft.response):
                draft.status = "escalated"
                draft.response = "Рекомендации требуют проверки специалистом Helping. Не выполняйте непроверенные команды и не передавайте секреты."
                draft.steps = []
                draft.escalation_reason = "Детерминированный safety-gate заблокировал потенциально опасное действие."

            latency_ms = round((time.perf_counter() - started) * 1000)
            response = TicketResponse(
                ticket_id=ticket_id,
                status=draft.status,
                category=intake.categories,
                priority=intake.priority,
                summary=intake.summary,
                response=draft.response,
                steps=draft.steps,
                questions=draft.questions,
                escalation_reason=draft.escalation_reason,
                agents_used=["intake", *[f"{c}_specialist" for c in categories], "policy", "resolver"],
                retrieved_documents=sources,
                latency_ms=latency_ms,
            )
            self.memory.save(request, response)
            REQUESTS.labels(status=response.status, priority=response.priority.value).inc()
            REQUEST_LATENCY.observe(time.perf_counter() - started)
            logger.info(
                "ticket_completed",
                extra={"ticket_id": ticket_id, "status": response.status, "duration_ms": latency_ms,
                       "category": ",".join(c.value for c in response.category)},
            )
            return response
