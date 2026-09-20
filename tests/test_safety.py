from src.models import DiagnosticStep
from src.safety import filter_steps, output_is_safe, redact_secrets


def test_redacts_secret():
    assert "supersecret" not in redact_secrets("password=supersecret")


def test_blocks_destructive_command():
    steps = [DiagnosticStep(order=1, action="Выполнить rm -rf /", expected_result="Очистка")]
    safe, blocked = filter_steps(steps, False)
    assert not safe and blocked


def test_blocks_admin_step_by_default():
    steps = [DiagnosticStep(order=1, action="Установить драйвер", expected_result="Готово", risk="admin")]
    safe, blocked = filter_steps(steps, False)
    assert not safe and blocked


def test_safe_output():
    assert output_is_safe("Перезапустите приложение и повторите вход.")
