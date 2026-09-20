from prometheus_client import Counter, Histogram

REQUESTS = Counter("helping_requests_total", "Tickets processed", ["status", "priority"])
AGENT_RUNS = Counter("helping_agent_runs_total", "Agent invocations", ["agent", "status"])
LLM_ERRORS = Counter("helping_llm_errors_total", "LLM call errors", ["agent"])
TOKENS = Counter("helping_tokens_total", "Ollama token counts", ["agent", "kind"])
REQUEST_LATENCY = Histogram("helping_request_duration_seconds", "End-to-end ticket latency")
LLM_LATENCY = Histogram("helping_llm_duration_seconds", "LLM latency", ["agent"])
RETRIEVAL_LATENCY = Histogram("helping_retrieval_duration_seconds", "RAG retrieval latency")
