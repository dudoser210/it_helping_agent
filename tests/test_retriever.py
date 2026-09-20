from pathlib import Path

from src.memory.retriever import KnowledgeRetriever


def test_wifi_query_prefers_wifi_runbook():
    retriever = KnowledgeRetriever(Path("knowledge"))
    docs = retriever.search("Wi-Fi подключен, но сайты не открываются DNS", top_k=3, category="wifi")
    assert docs
    assert docs[0].source.startswith("wifi.md")


def test_context_preserves_source():
    retriever = KnowledgeRetriever(Path("knowledge"))
    docs = retriever.search("принтер очередь печати", top_k=2, category="printer")
    assert "SOURCE:" in retriever.context(docs)
