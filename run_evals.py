import argparse
import asyncio
import json
from pathlib import Path

from src.config import get_settings
from src.models import TicketRequest
from src.orchestrator import HelpingOrchestrator


def contains_any(text: str, needles: list[str]) -> bool:
    low = text.lower()
    return any(needle.lower() in low for needle in needles)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="evals/cases/golden.jsonl")
    parser.add_argument("--output", default="output/eval-results.json")
    args = parser.parse_args()
    cases = [json.loads(line) for line in Path(args.cases).read_text(encoding="utf-8").splitlines() if line.strip()]
    system = HelpingOrchestrator(get_settings())
    results = []
    for case in cases:
        response = await system.process(TicketRequest(**case["request"]))
        text = response.response + " " + " ".join(s.action for s in response.steps)
        checks = {
            "category": bool(set(case["expected_categories"]) & {x.value for x in response.category}),
            "priority": response.priority.value in case["expected_priority"],
            "content": contains_any(text, case["must_contain_any"]),
            "safety": not contains_any(text, case["must_not_contain"]),
            "latency": response.latency_ms < 600_000,
        }
        results.append({"id": case["id"], "passed": all(checks.values()), "checks": checks,
                        "latency_ms": response.latency_ms, "response": response.model_dump(mode="json")})
        print(f"{case['id']}: {'PASS' if all(checks.values()) else 'FAIL'} {checks}")
    summary = {"total": len(results), "passed": sum(x["passed"] for x in results),
               "pass_rate": sum(x["passed"] for x in results) / len(results), "results": results}
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if summary["pass_rate"] >= 0.75 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
