from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from prometheus_client import make_asgi_app

from src.config import get_settings
from src.models import HealthResponse, TicketRequest, TicketResponse
from src.observability.logging import configure_logging
from src.observability.tracing import configure_tracing
from src.orchestrator import HelpingOrchestrator

settings = get_settings()
configure_logging(settings.log_level)
tracer = configure_tracing(settings.app_name, settings.otel_exporter_otlp_endpoint, settings.otel_enabled)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = HelpingOrchestrator(settings, tracer)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Локальная мультиагентная система обработки IT-заявок.",
    lifespan=lifespan,
)
app.mount("/metrics", make_asgi_app())


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health():
    orchestrator: HelpingOrchestrator = app.state.orchestrator
    ok = await orchestrator.llm.health()
    return HealthResponse(status="ok" if ok else "degraded", ollama="available" if ok else "unavailable", model=settings.ollama_model)


@app.post("/api/v1/tickets", response_model=TicketResponse)
async def create_ticket(request: TicketRequest):
    orchestrator: HelpingOrchestrator = app.state.orchestrator
    try:
        return await orchestrator.process(request)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Не удалось обработать заявку: {type(exc).__name__}") from exc
