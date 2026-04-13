from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent / "taxonomy.yaml"


@dataclass(frozen=True)
class TaxonomyRule:
    pattern: str
    merchant: str | None
    category: str


@dataclass(frozen=True)
class TaxonomyHit:
    merchant: str | None
    category: str


class Taxonomy:
    def __init__(self, rules: list[TaxonomyRule]) -> None:
        self.rules = rules

    def match(self, description_normalized: str) -> TaxonomyHit | None:
        hay = description_normalized.lower()
        for rule in self.rules:
            if rule.pattern in hay:
                return TaxonomyHit(merchant=rule.merchant, category=rule.category)
        return None


def load_taxonomy(path: Path) -> Taxonomy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = [
        TaxonomyRule(
            pattern=r["pattern"].lower(),
            merchant=r.get("merchant"),
            category=r["category"],
        )
        for r in raw["rules"]
    ]
    return Taxonomy(rules)


def load_default_taxonomy() -> Taxonomy:
    return load_taxonomy(DEFAULT_PATH)
