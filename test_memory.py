from pathlib import Path

from src.memory.store import TicketMemory
from src.models import Category, Priority, TicketRequest, TicketResponse


def test_ticket_round_trip(tmp_path: Path):
    store = TicketMemory(tmp_path / "test.db")
    request = TicketRequest(employee_id="u-1", text="Не работает Wi-Fi")
    response = TicketResponse(
        ticket_id="HD-TEST", status="resolved", category=[Category.wifi], priority=Priority.medium,
        summary="Wi-Fi", response="Проверить подключение", steps=[], questions=[], agents_used=["intake"],
        retrieved_documents=[], latency_ms=1,
    )
    store.save(request, response)
    history = store.recent_for_employee("u-1")
    assert history[0]["ticket_id"] == "HD-TEST"
