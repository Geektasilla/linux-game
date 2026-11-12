"""Game rules without any input/output, so they can be unit-tested directly."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass(frozen=True)
class Difficulty:
    attempts: int  # attempts per question
    skips: int  # skips per game


DIFFICULTIES: dict[str, Difficulty] = {
    "easy": Difficulty(attempts=1, skips=1),
    "medium": Difficulty(attempts=2, skips=2),
    "hard": Difficulty(attempts=3, skips=3),
}

SESSION_LENGTHS = (10, 30, 60)

_SPACES = re.compile(r"\s+")


def normalize_command(text: str) -> str:
    """Make answers comparable: ignore extra spaces, quote style and a trailing semicolon."""
    text = _SPACES.sub(" ", text.strip()).replace('"', "'")
    return text.rstrip(";").strip()


@dataclass(frozen=True)
class Question:
    id: str
    prompt: dict[str, str]  # language -> text
    answers: tuple[str, ...]

    def text(self, lang: str) -> str:
        return self.prompt.get(lang) or self.prompt["ru"]

    @property
    def main_answer(self) -> str:
        return self.answers[0]

    def is_correct(self, answer: str) -> bool:
        given = normalize_command(answer)
        return bool(given) and any(given == normalize_command(a) for a in self.answers)


class Outcome(Enum):
    CORRECT = auto()
    WRONG = auto()  # wrong, but attempts are left
    FAILED = auto()  # wrong and no attempts left
    SKIPPED = auto()


@dataclass
class QuizSession:
    """One game: a fixed list of questions, attempts per question and skips per game."""

    questions: list[Question]
    difficulty: Difficulty
    index: int = 0
    correct: int = 0
    skipped: int = 0
    attempts_used: int = 0
    skips_left: int = field(init=False)

    def __post_init__(self) -> None:
        if not self.questions:
            raise ValueError("A session needs at least one question")
        self.skips_left = self.difficulty.skips

    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def finished(self) -> bool:
        return self.index >= self.total

    @property
    def current(self) -> Question:
        return self.questions[self.index]

    @property
    def attempts_left(self) -> int:
        return self.difficulty.attempts - self.attempts_used

    def answer(self, text: str) -> Outcome:
        if self.finished:
            raise RuntimeError("The session is already finished")
        if self.current.is_correct(text):
            self.correct += 1
            self._next()
            return Outcome.CORRECT
        self.attempts_used += 1
        if self.attempts_left > 0:
            return Outcome.WRONG
        self._next()
        return Outcome.FAILED

    def skip(self) -> bool:
        """Skip the current question. Returns False if no skips are left."""
        if self.finished or self.skips_left == 0:
            return False
        self.skips_left -= 1
        self.skipped += 1
        self._next()
        return True

    @property
    def percent(self) -> int:
        """Share of correct answers among the questions actually played."""
        return round(self.correct * 100 / self.total)

    def _next(self) -> None:
        self.index += 1
        self.attempts_used = 0
