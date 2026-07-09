from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


QUOTE_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
    }
)

NORMALIZATION_VERSION = "2026-07-09"

IMPORTANT_PHRASES = (
    "graham cracker crust",
    "cream of chicken",
    "cream of chicken soup",
    "cream of mushroom",
    "cream of mushroom soup",
    "chicken and rice",
    "baked cheesecake",
    "cream cheese",
    "graham cracker",
    "black pepper",
    "pasta water",
    "heavy cream",
    "egg yolk",
    "parmesan cheese",
    "cheddar cheese",
    "olive oil",
    "brown sugar",
    "no bake",
)

ALIAS_PATTERNS = {
    "omelette": "omelet",
    "omelettes": "omelet",
    "parmigiano reggiano": "parmesan",
    "parmigiano-reggiano": "parmesan",
    "graham crackers": "graham cracker",
    "no-bake": "no bake",
    "no bake": "no bake",
}

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

PLURAL_SUFFIX_EXCEPTIONS = ("ss", "us", "is")


@dataclass(frozen=True)
class NormalizedText:
    original: str
    normalized: str
    tokens: list[str]
    phrases: list[str] = field(default_factory=list)
    aliases_applied: list[str] = field(default_factory=list)


def normalize_text(value: str, *, fold_accents: bool = True) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text).translate(QUOTE_TRANSLATION)
    if fold_accents:
        text = "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))
    text = text.lower()
    for alias, canonical in sorted(ALIAS_PATTERNS.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(alias)}(?!\w)", canonical, text)
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def safe_tokenize(value: str, *, fold_accents: bool = True) -> list[str]:
    normalized = normalize_text(value, fold_accents=fold_accents)
    return [normalize_token(token) for token in TOKEN_PATTERN.findall(normalized) if token]


def extract_phrases(value: str, *, fold_accents: bool = True) -> list[str]:
    normalized = normalize_text(value, fold_accents=fold_accents)
    phrases: list[str] = []
    for phrase in IMPORTANT_PHRASES:
        if _contains_phrase(normalized, phrase):
            phrases.append(phrase)
    return _dedupe_preserve_order(phrases)


def normalize_index_text(value: str, *, fold_accents: bool = True) -> NormalizedText:
    normalized = normalize_text(value, fold_accents=fold_accents)
    tokens = [normalize_token(token) for token in TOKEN_PATTERN.findall(normalized)]
    phrases = extract_phrases(value, fold_accents=fold_accents)
    aliases_applied = [alias for alias in ALIAS_PATTERNS if _contains_phrase(normalized, ALIAS_PATTERNS[alias])]
    return NormalizedText(
        original=value,
        normalized=normalized,
        tokens=_dedupe_preserve_order([token for token in tokens if token]),
        phrases=phrases,
        aliases_applied=_dedupe_preserve_order(aliases_applied),
    )


def normalize_token(token: str) -> str:
    text = normalize_text(token)
    if not text:
        return ""
    for alias, canonical in ALIAS_PATTERNS.items():
        if text == alias:
            text = canonical
            break
    return _singularize_token(text)


def _contains_phrase(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.search(pattern, text) is not None


def _singularize_token(token: str) -> str:
    if len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("oes") and len(token) > 4:
        return token[:-2]
    if token.endswith(("xes", "zes", "ches", "shes")) and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith(PLURAL_SUFFIX_EXCEPTIONS):
        return token[:-1]
    return token


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
