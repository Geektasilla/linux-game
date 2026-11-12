"""Plays the game end-to-end through a scripted console."""

import random
import re

import pytest

from terminal_challenge.cli import Console, Game, QuitGame, main
from terminal_challenge.content import LEVELS, load_questions

ANSWERS = {q.text(lang): q.main_answer for level in LEVELS for q in load_questions(level) for lang in ("ru", "en")}
QUESTION_LINE = re.compile(r"^\d+\.(.+)$")


class ScriptedConsole(Console):
    """Feeds prepared inputs. The token '<answer>' is replaced with the correct answer to the last question."""

    def __init__(self, inputs: list[str]) -> None:
        self.inputs = list(inputs)
        self.lines: list[str] = []
        super().__init__(input_fn=self._read, output_fn=self.lines.append, color=False, pause=lambda _: None)

    def _read(self, prompt: str) -> str:
        self.lines.append(prompt)
        if not self.inputs:
            raise EOFError
        value = self.inputs.pop(0)
        if value == "<answer>":
            for line in reversed(self.lines):
                match = QUESTION_LINE.match(line)
                if match and match.group(1) in ANSWERS:
                    return ANSWERS[match.group(1)]
        return value

    @property
    def output(self) -> str:
        return "\n".join(self.lines)


def make_game(inputs: list[str], lang: str = "ru") -> tuple[Game, ScriptedConsole]:
    console = ScriptedConsole(inputs)
    return Game(console, lang, rng=random.Random(42)), console


# theme 5 (Linux), mode 1 (good), difficulty 1 (easy), length 1 (10 questions)
SETUP = ["5", "1", "1", "1"]


def test_intro_shows_logo_warning_and_commands():
    game, console = make_game(["end"])

    with pytest.raises(QuitGame):
        game.run()

    assert "███████╗██╗   ██╗██████╗" in console.output
    assert "ПОКАЖИ, КТО ТУТ НАСТОЯЩИЙ ROOT!" in console.output
    assert "ВОЗРАСТНОЕ ОГРАНИЧЕНИЕ И ПРЕДУПРЕЖДЕНИЕ" in console.output
    assert "`skip` — пропустить вопрос" in console.output


def test_menus_keep_the_original_items():
    game, console = make_game([*SETUP, "end"])

    with pytest.raises(QuitGame):
        game.run()

    for item in ("1. Star Wars", "9. Game of Thrones", "1. good", "2. bad", "3. verybad", "3. hard", "3. 60 вопросов"):
        assert item in console.lines


def test_perfect_game_gives_100_percent():
    game, console = make_game([*SETUP, *["<answer>"] * 10, "n"])

    game.run()

    assert "Правильных ответов: 10 из 10 (100%)" in console.output
    assert "Правильно, беги. Не всем дано быть root." in console.output


def test_help_does_not_cost_an_attempt():
    """Regression: commands used to consume one of the attempts."""
    game, console = make_game([*SETUP, "help", "<answer>", *["<answer>"] * 9, "n"])

    game.run()

    assert "Правильных ответов: 10 из 10 (100%)" in console.output


def test_skip_is_limited_on_easy():
    game, console = make_game([*SETUP, "skip", "skip", "<answer>", *["<answer>"] * 8, "n"])

    game.run()

    assert "Пропуски закончились" in console.output
    assert "Правильных ответов: 9 из 10 (90%)" in console.output


def test_wrong_answer_reveals_the_correct_one_on_easy():
    game, console = make_game([*SETUP, "definitely-wrong", *["<answer>"] * 9, "n"])

    game.run()

    assert "Попытки исчерпаны. Правильный ответ:" in console.output
    assert "Правильных ответов: 9 из 10 (90%)" in console.output


def test_invalid_menu_input_shows_original_errors():
    game, console = make_game(["abc", "99", *SETUP, *["<answer>"] * 10, "n"])

    game.run()

    assert "Ошибка ввода! Нужно ввести ЦИФРУ или 'end'." in console.output
    assert "Темы под номером 99 не существует!" in console.output


def test_declining_bad_mode_returns_to_mode_choice():
    game, console = make_game(["5", "2", "n", "1", "1", "1", *["<answer>"] * 10, "n"])

    game.run()

    assert "Возврат к выбору режима..." in console.output
    assert console.output.count("Выберите режим контента:") == 2


def test_unclear_confirmation_is_asked_again():
    """Regression: any answer other than y/n silently returned to the mode menu."""
    game, console = make_game(["5", "3", "maybe", "y", "1", "1", *["<answer>"] * 10, "n"])

    game.run()

    assert "Я спросил 'y' или 'n'. Ты читать умеешь?" in console.output
    assert "◈ Выбран режим: verybad" in console.output


def test_play_again_starts_a_new_round():
    game, console = make_game([*SETUP, *["<answer>"] * 10, "y", *SETUP, *["<answer>"] * 10, "n"])

    game.run()

    assert "Мазохист, значит? Ну давай, попробуй еще раз." in console.output
    assert console.output.count("Правильных ответов: 10 из 10") == 2


def test_longest_session_is_capped_by_available_questions():
    """Regression: '60 questions' on easy has only 58 tasks, so 100 % used to be impossible."""
    game, console = make_game(["5", "1", "1", "3", *["<answer>"] * 58, "n"])

    game.run()

    assert "Правильных ответов: 58 из 58 (100%)" in console.output


def test_end_quits_from_any_question():
    game, _ = make_game([*SETUP, "end"])

    with pytest.raises(QuitGame):
        game.run()


@pytest.mark.parametrize("theme_number", [str(n) for n in range(1, 10)])
@pytest.mark.parametrize("mode_inputs", [["1"], ["2", "y"], ["3", "y"]], ids=["good", "bad", "verybad"])
def test_every_theme_and_mode_can_be_played_to_the_end(theme_number, mode_inputs):
    """Regression: two themes crashed on the result screen (wrong key / missing rank)."""
    game, console = make_game([theme_number, *mode_inputs, "3", "1", *["wrong"] * 5, *["<answer>"] * 10, "n"])

    game.run()

    assert "Правильных ответов:" in console.output


def test_english_game():
    game, console = make_game(["1", "1", "1", "1", *["<answer>"] * 10, "n"], lang="en")

    game.run()

    assert "Correct answers: 10 of 10 (100%)" in console.output
    assert "Right, run. Not everyone is meant to be root." in console.output


def test_main_exits_cleanly_on_end_of_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError))
    monkeypatch.setattr("terminal_challenge.cli.INTRO_PAUSE", 0)

    assert main(["--lang", "en", "--no-color"]) == 0
    assert "Come back when you are ready" in capsys.readouterr().out
