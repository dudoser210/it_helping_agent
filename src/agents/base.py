from pathlib import Path

from pydantic import BaseModel

from src.llm import OllamaClient
from src.observability.metrics import AGENT_RUNS


class Agent:
    def __init__(self, name: str, prompt_file: Path, llm: OllamaClient):
        self.name = name
        self.system_prompt = prompt_file.read_text(encoding="utf-8")
        self.llm = llm

    async def run(self, user: str, schema: type[BaseModel]):
        try:
            result = await self.llm.structured(agent=self.name, system=self.system_prompt, user=user, schema=schema)
            AGENT_RUNS.labels(agent=self.name, status="ok").inc()
            return result
        except Exception:
            AGENT_RUNS.labels(agent=self.name, status="error").inc()
            raise
