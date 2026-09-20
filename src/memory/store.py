import json
import sqlite3
from pathlib import Path

from src.models import TicketRequest, TicketResponse


class TicketMemory:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._init()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    request_text TEXT NOT NULL,
                    categories TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_employee ON tickets(employee_id, created_at DESC)")

    def recent_for_employee(self, employee_id: str, limit: int = 3) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT ticket_id, categories, status, summary, response, created_at FROM tickets "
                "WHERE employee_id = ? ORDER BY created_at DESC LIMIT ?",
                (employee_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def save(self, request: TicketRequest, response: TicketResponse) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    response.ticket_id,
                    request.employee_id,
                    request.text,
                    json.dumps([c.value for c in response.category], ensure_ascii=False),
                    response.priority.value,
                    response.status,
                    response.summary,
                    response.response,
                    response.created_at.isoformat(),
                ),
            )
