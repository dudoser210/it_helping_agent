import re

from src.models import DiagnosticStep

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|пароль|token|токен|api[_ -]?key|secret)\s*[:=]\s*\S+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
]
PROHIBITED = re.compile(
    r"(?i)(rm\s+-rf|format\s+[a-z]:|disable.{0,20}(antivirus|firewall|mfa|edr)|"
    r"отключ.{0,20}(антивирус|фаервол|mfa|2fa)|reg\s+delete|bypass|обойти.{0,20}(доступ|защит))"
)


def redact_secrets(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[УДАЛЕНО]", text)
    return text


def filter_steps(steps: list[DiagnosticStep], allow_high_risk: bool) -> tuple[list[DiagnosticStep], list[str]]:
    safe, blocked = [], []
    for step in steps:
        if (
            PROHIBITED.search(step.action)
            or PROHIBITED.search(step.expected_result)
            or (step.risk == "admin" and not allow_high_risk)
        ):
            blocked.append(step.action)
        else:
            safe.append(step)
    for index, step in enumerate(safe, start=1):
        step.order = index
    return safe, blocked


def output_is_safe(text: str) -> bool:
    return not PROHIBITED.search(text) and all(not p.search(text) for p in SECRET_PATTERNS)
