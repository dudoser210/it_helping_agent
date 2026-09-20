import argparse
import asyncio
import json

from src.config import get_settings
from src.models import TicketRequest
from src.observability.logging import configure_logging
from src.orchestrator import HelpingOrchestrator


async def run() -> None:
    parser = argparse.ArgumentParser(description="IT Helping Agent CLI")
    parser.add_argument("text", help="Текст заявки")
    parser.add_argument("--employee", default="demo-user")
    parser.add_argument("--device")
    parser.add_argument("--os")
    parser.add_argument("--location")
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    orchestrator = HelpingOrchestrator(settings)
    result = await orchestrator.process(
        TicketRequest(employee_id=args.employee, text=args.text, device=args.device, os=args.os, location=args.location)
    )
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
