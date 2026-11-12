"""Loading game content (questions, themes, UI strings) from the JSON files in data/."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from functools import cache
from importlib import resources
from typing import Any

from terminal_challenge.engine import Question

LANGUAGES = ("ru", "en")
MODES = ("good", "bad", "verybad")
LEVELS = ("easy", "medium", "hard")

DATA = resources.files("terminal_challenge") / "data"


def _read_json(*parts: str) -> Any:
    return json.loads(DATA.joinpath(*parts).read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Verdict:
    max_score: int
    status: str
    comments: tuple[str, ...]


@dataclass(frozen=True)
class Theme:
    id: str
    title: str
    phrases: dict[str, dict[str, dict[str, list[str]]]]  # language -> mode -> correct/wrong -> phrases
    verdicts: dict[str, list[Verdict]]  # language -> verdicts sorted by max_score

    @property
    def languages(self) -> tuple[str, ...]:
        return tuple(lang for lang in LANGUAGES if lang in self.phrases and lang in self.verdicts)

    def reaction(self, lang: str, mode: str, correct: bool, rng: random.Random) -> str:
        return rng.choice(self.phrases[lang][mode]["correct" if correct else "wrong"])

    def verdict(self, lang: str, percent: float) -> Verdict:
        """The first rank whose upper bound covers the score."""
        for verdict in self.verdicts[lang]:
            if percent <= verdict.max_score:
                return verdict
        return self.verdicts[lang][-1]


@cache
def load_themes() -> tuple[Theme, ...]:
    order = _read_json("themes", "order.json")
    themes = []
    for theme_id in order:
        raw = _read_json("themes", f"{theme_id}.json")
        verdicts = {
            lang: sorted(
                (Verdict(v["max_score"], v["status"], tuple(v["comments"])) for v in items), key=lambda v: v.max_score
            )
            for lang, items in raw["verdicts"].items()
        }
        themes.append(Theme(raw["id"], raw["title"], raw["phrases"], verdicts))
    return tuple(themes)


def themes_for(lang: str) -> list[Theme]:
    return [theme for theme in load_themes() if lang in theme.languages]


@cache
def load_questions(level: str) -> tuple[Question, ...]:
    raw = _read_json("questions.json")[level]
    return tuple(Question(id=q["id"], prompt=q["prompt"], answers=tuple(q["answers"])) for q in raw)


@cache
def load_strings(lang: str) -> dict[str, str]:
    return _read_json("i18n", f"{lang}.json")
