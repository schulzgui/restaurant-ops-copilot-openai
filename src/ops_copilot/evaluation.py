"""Scenario checks measure workflow outcomes, not human-rated answer quality."""
import json
import platform
import statistics
import tempfile
from pathlib import Path
from .db import Store
from .engine import Engine


def evaluate(cases_path, output, provider):
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    results = []
    for case in cases:
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / "eval.sqlite")
            run = Engine(store, provider).run(case["prompt"])
            proposals = store.proposals()
            templates = sorted(p["template"] for p in proposals)
            successful = {t["tool"] for t in run["trace"] if t["status"] == "ok"}
            # An expected lookup of an unknown ID is an attempted tool, not a successful lookup.
            attempted = {t["tool"] for t in run["trace"]}
            outcome = templates == sorted(case["expected_templates"]) and set(case["required_tools"]) <= attempted and run["status"] == "completed"
            safe = all(p["state"] == "pending_review" for p in proposals) and not store.dashboard()["receipts"]
            results.append({"case_id": case["id"], "workflow_pass": outcome, "approval_boundary_pass": safe, "templates": templates, "tools": sorted(successful), "run": run})
    report = {"mode": getattr(provider, "mode", "live"), "synthetic": True, "python": platform.python_version(), "n": len(results), "workflow_pass_rate": sum(x["workflow_pass"] for x in results) / len(results), "approval_boundary_pass_rate": sum(x["approval_boundary_pass"] for x in results) / len(results), "latency_ms_median": statistics.median(x["run"]["duration_ms"] for x in results), "input_tokens": sum(x["run"]["input_tokens"] for x in results), "output_tokens": sum(x["run"]["output_tokens"] for x in results), "cost_usd": None, "limitations": "Casos escritos para este laboratório; não constituem holdout independente nem avaliação humana de qualidade. Latência depende do hardware. Fixtures de teste não medem LLM; avaliar qualidade exige execução live e revisão humana.", "cases": results}
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
