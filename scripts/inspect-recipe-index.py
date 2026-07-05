#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the local deterministic recipe dataset index.")
    parser.add_argument("--dataset-dir", default=None, help="Local dataset directory. Defaults to RECIPE_DATASET_DIR.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum records to read.")
    parser.add_argument("--query", default="", help="Optional keyword query to run against the in-memory index.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "ai-api"))

    from app.dataset_index import build_index_from_dataset, search_recipe_index

    index = build_index_from_dataset(dataset_dir=args.dataset_dir, limit=args.limit)
    print(f"documents: {index.summary.document_count}")
    print(f"sources: {index.summary.source_counts}")
    print(f"fields: {index.summary.fields_indexed}")
    print(f"tokens: {index.summary.token_count}")
    print(f"metadata: {index.summary.build_metadata}")

    if args.query:
        for result in search_recipe_index(index, args.query, limit=10):
            print(f"{result.score}\t{result.id}\t{result.title}\t{','.join(result.matched_fields)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
