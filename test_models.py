import pytest
from pydantic import ValidationError

from src.models import TicketRequest


def test_rejects_too_short_ticket():
    with pytest.raises(ValidationError):
        TicketRequest(employee_id="u", text="wifi")
