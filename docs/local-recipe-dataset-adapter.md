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

## Testing

Tests generate tiny temporary CSV, SQLite, and metadata fixtures. They do not require local Kaggle files, provider keys, a real cookbook DB, or network access.

## Deferred Work

Later indexing tasks can use this adapter to decide how to map the local Kaggle files into a deterministic index. The following remain intentionally out of scope for 0024A:

- embeddings;
- vector databases;
- hybrid search endpoints;
- RAG over the 13K dataset;
- imports into Vanilla Cookbook;
- image ingestion;
- provider calls.
