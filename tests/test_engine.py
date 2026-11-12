import pytest

from terminal_challenge.engine import DIFFICULTIES, Difficulty, Outcome, Question, QuizSession, normalize_command


def make_question(qid: str = "q1", *answers: str) -> Question:
    return Question(id=qid, prompt={"ru": "вопрос", "en": "question"}, answers=answers or ("ls -la",))


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("  ls   -la  ", "ls -la"),
        ('grep "error" app.log', "grep 'error' app.log"),
        ("pwd;", "pwd"),
        ("\tcd\t..\n", "cd .."),
    ],
)
def test_normalize_command(given, expected):
    assert normalize_command(given) == expected


def test_answer_matching_ignores_spacing_and_quote_style():
    question = make_question("q", "grep -i 'error' app.log")

    assert question.is_correct('grep  -i "error"   app.log')
    assert not question.is_correct("grep error app.log")
    assert not question.is_correct("   ")


def test_question_text_falls_back_to_russian():
    question = Question(id="q", prompt={"ru": "только по-русски"}, answers=("ls",))

    assert question.text("en") == "только по-русски"


def test_correct_answer_moves_to_next_question():
    session = QuizSession([make_question("a"), make_question("b")], Difficulty(attempts=1, skips=0))

    assert session.answer("ls -la") is Outcome.CORRECT
    assert session.index == 1
    assert session.correct == 1


def test_wrong_answers_use_attempts_then_fail():
    session = QuizSession([make_question()], Difficulty(attempts=3, skips=0))

    assert session.answer("nope") is Outcome.WRONG
    assert session.attempts_left == 2
    assert session.answer("nope") is Outcome.WRONG
    assert session.answer("nope") is Outcome.FAILED
    assert session.finished
    assert session.correct == 0


def test_attempts_reset_for_each_question():
    session = QuizSession([make_question("a"), make_question("b")], Difficulty(attempts=2, skips=0))

    session.answer("nope")
    session.answer("ls -la")

    assert session.attempts_left == 2


def test_skips_are_limited_per_game():
    session = QuizSession([make_question(str(i)) for i in range(3)], Difficulty(attempts=1, skips=1))

    assert session.skip() is True
    assert session.skip() is False
    assert session.skipped == 1
    assert session.index == 1


def test_percent_is_based_on_questions_played():
    """Regression: the old version divided by the chosen session length, so 100 % was unreachable."""
    session = QuizSession([make_question(str(i)) for i in range(4)], DIFFICULTIES["easy"])

    for _ in range(4):
        session.answer("ls -la")

    assert session.percent == 100


def test_skipped_questions_count_as_not_correct():
    session = QuizSession([make_question("a"), make_question("b")], Difficulty(attempts=1, skips=1))

    session.skip()
    session.answer("ls -la")

    assert session.percent == 50


def test_answering_after_the_end_is_an_error():
    session = QuizSession([make_question()], DIFFICULTIES["easy"])
    session.answer("ls -la")

    with pytest.raises(RuntimeError):
        session.answer("ls -la")


def test_empty_session_is_rejected():
    with pytest.raises(ValueError):
        QuizSession([], DIFFICULTIES["easy"])


@pytest.mark.parametrize(("level", "attempts"), [("easy", 1), ("medium", 2), ("hard", 3)])
def test_difficulty_levels(level, attempts):
    assert DIFFICULTIES[level].attempts == attempts
    assert DIFFICULTIES[level].skips == attempts
