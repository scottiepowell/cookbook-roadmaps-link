# Local Recipe Dataset Adapter

Task 0024A starts the indexing layer with local-only inspection for the Kaggle recipe dataset. It does not build an index, import recipes, ingest images, call providers, or write to Vanilla Cookbook.

## Dataset

Expected local source:

- Dataset: Food Ingredients and Recipes Dataset with Images
- Author: Kaggle user `pes12017000148`
- URL: https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
- License: Creative Commons Attribution-ShareAlike 3.0 Unported, CC BY-SA 3.0
- License URL: https://creativecommons.org/licenses/by-sa/3.0/

Place downloaded files under the ignored local directory:

```text
recipe-dataset/
  13k-recipes.csv
  13k-recipes.db
  5k-recipes.db
  metadata.json
  README.md
  tutorial.md
```

`recipe-dataset/` is ignored by Git. Do not commit raw dataset files, generated indexes, downloaded images, or derived private data.

## Configuration

The adapter defaults to `recipe-dataset` relative to the repository root. Override it with:

```text
RECIPE_DATASET_DIR=recipe-dataset
```

This setting is local-only. It is not a deployment requirement and does not change Cloudflare routing or Compose behavior.

## Adapter Behavior

`ai-api/app/dataset_adapter.py` exposes `inspect_recipe_dataset()`.

It returns structured objects for:

- expected file presence, readability, size, and warnings;
- CSV columns and up to three sample rows from `13k-recipes.csv`;
- SQLite table/column previews from `13k-recipes.db` and `5k-recipes.db`;
- `metadata.json` keys and parsed values;
- a small normalized preview with likely title, ingredients, and instructions fields when the CSV contains a sample row.

SQLite inspection reuses the existing read-only schema inspector. Missing or unreadable files produce warnings instead of failing the whole inspection.

Task 0024B adds a bounded record reader:

```text
iter_recipe_dataset_records(dataset_dir=None, limit=100)
```

The reader uses the 0024A adapter conventions and reads at most `limit` normalized records from local CSV and SQLite files. It maps likely source ID, title/name, ingredients, instructions/directions, tags/category/cuisine, source file, and source table fields into `ExternalRecipeRecord` objects. SQLite reads use the existing read-only connection helper.

## Deterministic Local Index

`ai-api/app/dataset_index.py` builds an in-memory keyword index from `ExternalRecipeRecord` objects. The index lowercases and tokenizes consistently, records document counts, source counts, indexed fields, token totals, warnings, and deterministic build metadata, and supports deterministic search with stable tie ordering.

Ranking is field weighted:

- title/name matches rank highest;
- tags/category/cuisine rank below title;
- ingredients rank above instruction/body matches;
- source file/table matches rank lowest.

Search results include recipe ID, source ID, title, score, matched fields, snippets, and source file/table metadata.

The optional local helper script prints a compact summary only:

```powershell
python scripts/inspect-recipe-index.py --dataset-dir recipe-dataset --limit 25 --query beans
```

The script does not write index artifacts and must not be used to commit raw dataset output.

## Testing

Tests generate tiny temporary CSV, SQLite, and metadata fixtures. They do not require local Kaggle files, provider keys, a real cookbook DB, or network access.

## Deferred Work

Later tasks can expose or expand this index after review. The following remain intentionally out of scope:

- embeddings;
- vector databases;
- hybrid search endpoints;
- RAG over the 13K dataset;
- imports into Vanilla Cookbook;
- image ingestion;
- generated index artifacts;
- provider calls.
