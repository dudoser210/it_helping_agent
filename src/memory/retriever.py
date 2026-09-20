import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.observability.metrics import RETRIEVAL_LATENCY

TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9_-]{2,}")


@dataclass
class Document:
    source: str
    title: str
    text: str


class KnowledgeRetriever:
    """Small deterministic BM25 retriever over semantic Markdown runbooks."""

    def __init__(self, directory: Path):
        self.documents = self._load(directory)
        self.doc_tokens = [self._tokens(d.text) for d in self.documents]
        self.avg_len = sum(map(len, self.doc_tokens)) / max(len(self.doc_tokens), 1)
        self.df = Counter(token for tokens in self.doc_tokens for token in set(tokens))

    @staticmethod
    def _load(directory: Path) -> list[Document]:
        docs = []
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            chunks = re.split(r"(?=^## )", text, flags=re.MULTILINE)
            for index, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if len(chunk) < 40:
                    continue
                first = chunk.splitlines()[0].lstrip("# ")
                docs.append(Document(f"{path.name}#{index}", first, chunk))
        return docs

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token.lower() for token in TOKEN_RE.findall(text)]

    def search(self, query: str, top_k: int = 4, category: str | None = None) -> list[Document]:
        started = time.perf_counter()
        try:
            query_tokens = self._tokens(query)
            scores = []
            n = max(len(self.documents), 1)
            for idx, tokens in enumerate(self.doc_tokens):
                tf = Counter(tokens)
                score = 0.0
                for term in query_tokens:
                    freq = tf[term]
                    if not freq:
                        continue
                    idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                    denom = freq + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / max(self.avg_len, 1))
                    score += idf * freq * 2.5 / denom
                if category and self.documents[idx].source.startswith(category):
                    score += 2.0
                if score > 0:
                    scores.append((score, idx))
            return [self.documents[idx] for _, idx in sorted(scores, reverse=True)[:top_k]]
        finally:
            RETRIEVAL_LATENCY.observe(time.perf_counter() - started)

    @staticmethod
    def context(documents: list[Document]) -> str:
        return "\n\n---\n\n".join(f"SOURCE: {d.source}\n{d.text}" for d in documents)
