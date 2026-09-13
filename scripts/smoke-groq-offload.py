"""Manual generated-fixture Groq smoke. Prints no key, prompt, or response text."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-api"))

from app.groq_advisory import TASKS
from app.providers.groq_offload import GroqOffloadProvider

FIXTURES = {
    "recipe_titles": "green chile rice skillet",
    "ingredient_parse": "2 cups rice",
    "instruction_cleanup": "Stir rice into simmering water.",
    "substitution_ideas": "butter",
    "shopping_group": "carrots",
    "pantry_ideas": "canned chickpeas",
    "meal_ideas": "tomato pasta",
    "plain_language": "Fold chopped herbs into the cooked rice.",
    "query_expansion": "courgette",
}


def main() -> int:
    active = GroqOffloadProvider()
    totals = {"input_tokens": 0, "output_tokens": 0}
    for task, source in FIXTURES.items():
        try:
            items, usage = active.generate(
                task=TASKS[task], task_key=task, lines=[{"source_id": "s0", "text": source}],
            )
        except Exception as exc:
            print(f"Groq generated-fixture smoke: {task}=failed ({exc.__class__.__name__})")
            return 1
        if len(items) != 1 or items[0]["source_id"] != "s0":
            print(f"Groq generated-fixture smoke: {task}=invalid contract")
            return 1
        totals["input_tokens"] += usage["input_tokens"]
        totals["output_tokens"] += usage["output_tokens"]
        print(f"Groq generated-fixture smoke: {task}=passed")
    print(f"Groq generated-fixture smoke: 9/9 passed; input_tokens={totals['input_tokens']}; "
          f"output_tokens={totals['output_tokens']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
