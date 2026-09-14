"""Manual bounded public-fixture comparison; writes aggregate evidence, never keys/text."""
import argparse
from hashlib import sha256
import json
import logging
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-api"))
from dotenv import load_dotenv
from app import importer, rag_offload
from app.ai_budget_guard import default_provider_budget_tracker
from app.providers.openai_provider import OpenAIProvider
from app.schemas import RecipeImportRequest

FIXTURES = ["Carrot salad with carrots, lettuce and onions for 4 servings.",
            "Omelet with eggs and cheese for 4 servings.",
            "Carbonara pasta with eggs and parmesan for 4 servings.",
            "Chicken and rice casserole for 4 servings."]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    load_dotenv(args.env_file, override=False)
    os.environ.update(RECIPE_DATASET_DIR=args.dataset, RECIPE_DATASET_INDEX_LIMIT="5000",
        AI_PROVIDER="openai", AI_MAX_OUTPUT_TOKENS="1800", AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL="2000",
        AI_PROVIDER_CALLS_ENABLED="true", AI_PROVIDER_GLOBAL_DISABLE="false",
        AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION="30", AI_RAG_DEDUP_ENABLED="false", AI_OFFLOAD_ENABLED="true")
    fingerprint = sha256()
    for name in ("13k-recipes.csv", "13k-recipes.db", "5k-recipes.db"):
        path = Path(args.dataset) / name
        fingerprint.update(name.encode())
        fingerprint.update(sha256(path.read_bytes()).digest() if path.exists() else b"missing")
    os.environ["AI_RAG_PUBLIC_DATASET_SHA256"] = fingerprint.hexdigest()
    logging.getLogger("app.observability").setLevel(logging.CRITICAL)
    events = []
    rag_offload.log_event = lambda event, **kwargs: events.append(kwargs)
    results = []
    default_provider_budget_tracker.reset()
    for index, text in enumerate(FIXTURES):
        # Exclude cold index creation from both arms of the paired comparison.
        importer._retrieve_importer_examples(text)
        for mode in ("baseline", "groq"):
            os.environ["AI_RAG_GROQ_DEDUP_ENABLED"] = str(mode == "groq").lower()
            events.clear()
            started = time.perf_counter()
            row = {"fixture": index, "mode": mode}
            try:
                provider = OpenAIProvider(max_output_tokens=1800)
                # No hidden OpenAI SDK retries in this comparison.
                provider._client_instance().max_retries = 0
                response = importer.import_recipe_text(RecipeImportRequest(text=text), provider=provider)
                row.update(valid=response.draft is not None, nano_usage=response.usage,
                           citation_ids=[item.id for item in response.citations],
                           context_chars=response.retrieval.packed_context_chars if response.retrieval else 0,
                           ingredient_names=[item.name for item in response.draft.ingredients] if response.draft else [],
                           instruction_count=len(response.draft.instructions) if response.draft else 0,
                           servings=response.draft.servings if response.draft else None)
            except Exception as exc:
                row.update(valid=False, error_type=type(exc).__name__)
            row.update(duration_ms=round((time.perf_counter() - started) * 1000, 2), groq_events=list(events))
            results.append(row)
            print(f"fixture={index} mode={mode} valid={row['valid']}", flush=True)
    summary = {}
    for mode in ("baseline", "groq"):
        rows = [row for row in results if row["mode"] == mode]
        nano_in = sum((row.get("nano_usage") or {}).get("input_tokens", 0) for row in rows)
        nano_out = sum((row.get("nano_usage") or {}).get("output_tokens", 0) for row in rows)
        groq_in = sum(event["input_tokens"] for row in rows for event in row["groq_events"])
        groq_out = sum(event["output_tokens"] for row in rows for event in row["groq_events"])
        durations = sorted(row["duration_ms"] for row in rows)
        summary[mode] = {"nano_input": nano_in, "nano_output": nano_out, "groq_input": groq_in,
            "groq_output": groq_out, "groq_attempts": sum(event["attempts"] for row in rows for event in row["groq_events"]),
            "valid": sum(row["valid"] for row in rows), "p50_ms": durations[len(durations)//2],
            "p95_ms": durations[math.ceil(.95 * len(durations))-1],
            "estimated_usd": (nano_in*.20+nano_out*1.25+groq_in*.075+groq_out*.30)/1_000_000}
    Path(args.output).write_text(json.dumps({"pricing_date": "2026-09-13", "sample_count": len(FIXTURES),
        "summary": summary, "rows": results}, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if all(row["valid"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
