import json
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel

from src.config import Settings
from src.observability.metrics import LLM_ERRORS, LLM_LATENCY, TOKENS

T = TypeVar("T", bound=BaseModel)


class OllamaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.settings.ollama_base_url}/api/tags")
                response.raise_for_status()
                names = {m.get("name") for m in response.json().get("models", [])}
                model = self.settings.ollama_model
                return model in names or model.split(":")[0] in {str(n).split(":")[0] for n in names}
        except (httpx.HTTPError, ValueError):
            return False

    async def structured(self, *, agent: str, system: str, user: str, schema: type[T]) -> T:
        started = time.perf_counter()
        payload = {
            "model": self.settings.ollama_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema.model_json_schema(),
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1, "num_ctx": 8192},
            "keep_alive": "10m",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.ollama_timeout_seconds) as client:
                response = await client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            TOKENS.labels(agent=agent, kind="prompt").inc(data.get("prompt_eval_count", 0))
            TOKENS.labels(agent=agent, kind="completion").inc(data.get("eval_count", 0))
            content = data["message"]["content"]
            return schema.model_validate(json.loads(content))
        except Exception:
            LLM_ERRORS.labels(agent=agent).inc()
            raise
        finally:
            LLM_LATENCY.labels(agent=agent).observe(time.perf_counter() - started)
