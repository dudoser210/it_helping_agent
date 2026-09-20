from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Category(str, Enum):
    wifi = "wifi"
    printer = "printer"
    access = "access"
    software = "software"
    unknown = "unknown"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=5, max_length=6000)
    device: str | None = Field(default=None, max_length=200)
    os: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=150)
    session_id: str | None = Field(default=None, max_length=80)


class IntakeResult(BaseModel):
    categories: list[Category]
    priority: Priority
    summary: str
    clarifying_questions: list[str] = []
    pii_detected: bool = False


class DiagnosticStep(BaseModel):
    order: int
    action: str
    expected_result: str
    risk: Literal["safe", "caution", "admin"] = "safe"


class SpecialistResult(BaseModel):
    agent: str
    diagnosis: str
    confidence: float = Field(ge=0, le=1)
    steps: list[DiagnosticStep]
    escalation_needed: bool = False
    escalation_reason: str | None = None
    sources: list[str] = []


class PolicyResult(BaseModel):
    approved: bool
    blocked_actions: list[str] = []
    warnings: list[str] = []
    sanitized_text: str


class TicketResponse(BaseModel):
    ticket_id: str
    status: Literal["resolved", "needs_info", "escalated"]
    category: list[Category]
    priority: Priority
    summary: str
    response: str
    steps: list[DiagnosticStep]
    questions: list[str]
    escalation_reason: str | None = None
    agents_used: list[str]
    retrieved_documents: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    model: str
