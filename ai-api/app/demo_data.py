import argparse
import csv
import json
import sqlite3
from pathlib import Path


DEMO_DATASET_MARKER = ".ai-demo-fixture.json"

DEMO_RECIPES = [
    {
        "id": 1,
        "title": "Lemon Herb White Beans",
        "description": "A bright pantry dinner with beans, lemon, olive oil, and herbs.",
        "ingredients": ["white beans", "lemon juice", "olive oil", "parsley", "garlic"],
        "instructions": ["Warm beans with olive oil and garlic.", "Finish with lemon juice and parsley."],
        "tags": ["dinner", "vegetarian", "quick"],
        "source_url": "demo://saved-recipes/lemon-herb-white-beans",
    },
    {
        "id": 2,
        "title": "Weeknight Tomato Pasta",
        "description": "A simple pasta dinner with tomato sauce and parmesan.",
        "ingredients": ["pasta", "tomato sauce", "parmesan", "basil"],
        "instructions": ["Boil pasta.", "Toss with warm tomato sauce.", "Top with parmesan and basil."],
        "tags": ["dinner", "vegetarian"],
        "source_url": "demo://saved-recipes/weeknight-tomato-pasta",
    },
    {
        "id": 3,
        "title": "Chickpea Cucumber Bowls",
        "description": "A cool lunch bowl with chickpeas, cucumber, yogurt, and herbs.",
        "ingredients": ["chickpeas", "cucumber", "yogurt", "dill", "lemon zest"],
        "instructions": ["Mix chickpeas and cucumber.", "Spoon over yogurt.", "Finish with dill and lemon zest."],
        "tags": ["lunch", "vegetarian", "quick"],
        "source_url": "demo://saved-recipes/chickpea-cucumber-bowls",
    },
]

DEMO_DATASET_ROWS = [
    {
        "recipe_id": "demo-dataset-1",
        "title": "Tomato Pasta Skillet",
        "ingredients": "pasta; tomato sauce; basil",
        "instructions": "Simmer tomato sauce, add cooked pasta, and finish with basil.",
        "cuisine": "weeknight dinner",
    },
    {
        "recipe_id": "demo-dataset-2",
        "title": "Lemon White Bean Toasts",
        "ingredients": "white beans; lemon; olive oil; toast",
        "instructions": "Mash beans with lemon and olive oil, then spoon onto toast.",
        "cuisine": "lunch",
    },
    {
        "recipe_id": "demo-dataset-3",
        "title": "Cucumber Chickpea Salad",
        "ingredients": "chickpeas; cucumber; parsley; lemon",
        "instructions": "Toss chickpeas, cucumber, parsley, and lemon dressing.",
        "cuisine": "salad",
    },
]


def seed_demo_data(output_dir: str | Path) -> dict[str, Path]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    db_path = base_dir / "recipes.sqlite"
    dataset_dir = base_dir / "dataset"
    dataset_dir.mkdir(exist_ok=True)

    _write_recipe_db(db_path)
    _write_dataset_csv(dataset_dir / "13k-recipes.csv")
    _write_dataset_marker(dataset_dir / DEMO_DATASET_MARKER)

    return {"db_path": db_path, "dataset_dir": dataset_dir}


def _write_recipe_db(path: Path) -> None:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE recipes (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                ingredients TEXT,
                instructions TEXT,
                tags TEXT,
                source_url TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO recipes
              (id, title, description, ingredients, instructions, tags, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    recipe["id"],
                    recipe["title"],
                    recipe["description"],
                    json.dumps(recipe["ingredients"]),
                    "\n".join(recipe["instructions"]),
                    "\n".join(recipe["tags"]),
                    recipe["source_url"],
                )
                for recipe in DEMO_RECIPES
            ],
        )
        connection.commit()
    finally:
        connection.close()


def _write_dataset_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["recipe_id", "title", "ingredients", "instructions", "cuisine"])
        writer.writeheader()
        writer.writerows(DEMO_DATASET_ROWS)


def _write_dataset_marker(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "kind": "cookbook-ai-demo-fixture",
                "version": 1,
                "purpose": "generated local demo data",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed generated local AI demo data.")
    parser.add_argument("--output-dir", default=".tmp-ai-demo/local", help="Directory for generated demo fixtures.")
    args = parser.parse_args()

    paths = seed_demo_data(args.output_dir)
    print(f"COOKBOOK_DB_PATH={paths['db_path']}")
    print(f"RECIPE_DATASET_DIR={paths['dataset_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
