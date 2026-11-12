"""Validates the JSON content, so a broken or incomplete theme is caught before anyone plays it."""

import re
from collections.abc import Iterator

import pytest

from terminal_challenge.content import LANGUAGES, LEVELS, MODES, load_questions, load_strings, load_themes, themes_for
from terminal_challenge.engine import SESSION_LENGTHS

THEMES = load_themes()
MIN_PHRASES = 15

# Russian obscene roots, including masked spellings like "х..ня" or "бл*ть".
PROFANITY = re.compile(
    r"(?<![а-яё])(?:ху[йеёяию]|пизд|бля|[её]б[аеиуыолн]|заеб|уеб|муда[кч]|залуп|пидо?р|шлюх)"
    r"|\w[*…]+\w|[а-яё]\.{2,}[а-яё]",
    re.IGNORECASE,
)


def all_texts() -> Iterator[str]:
    for theme in THEMES:
        for modes in theme.phrases.values():
            for results in modes.values():
                yield from (p for phrases in results.values() for p in phrases)
        for verdicts in theme.verdicts.values():
            for verdict in verdicts:
                yield verdict.status
                yield from verdict.comments
    for level in LEVELS:
        for question in load_questions(level):
            yield from question.prompt.values()
    for lang in LANGUAGES:
        yield from load_strings(lang).values()


def test_there_are_nine_themes_with_unique_ids():
    ids = [theme.id for theme in THEMES]
    assert len(ids) == 9
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("theme", THEMES, ids=lambda t: t.id)
def test_every_theme_is_complete_in_russian(theme):
    for mode in MODES:
        for result in ("correct", "wrong"):
            assert len(theme.phrases["ru"][mode][result]) >= MIN_PHRASES, (mode, result)


@pytest.mark.parametrize("theme", THEMES, ids=lambda t: t.id)
def test_verdicts_cover_every_score(theme):
    for lang in theme.languages:
        verdicts = theme.verdicts[lang]
        assert [v.max_score for v in verdicts] == [20, 40, 60, 80, 100]
        assert all(v.status and v.comments for v in verdicts)
        for percent in (0, 20, 21, 59, 60, 61, 100):
            assert theme.verdict(lang, percent).max_score >= percent


def test_english_is_available_for_at_least_one_theme():
    assert [theme.id for theme in themes_for("en")] == ["linux"]
    assert len(themes_for("ru")) == 9


@pytest.mark.parametrize("level", LEVELS)
def test_questions_are_bilingual_and_answerable(level):
    questions = load_questions(level)
    # The longest session (60) is capped by the available questions; it must still be clearly longer than 30.
    assert len(questions) > sorted(SESSION_LENGTHS)[-2] + 20
    for question in questions:
        assert question.prompt["ru"].strip() and question.prompt["en"].strip(), question.id
        assert question.answers and all(a.strip() for a in question.answers), question.id
        assert question.is_correct(question.main_answer), question.id


def test_question_ids_are_unique():
    ids = [q.id for level in LEVELS for q in load_questions(level)]
    assert len(ids) == len(set(ids))


def test_ui_strings_exist_in_both_languages():
    assert load_strings("ru").keys() == load_strings("en").keys()


def test_no_profanity_anywhere():
    offending = [text for text in all_texts() if PROFANITY.search(text)]
    assert offending == []
