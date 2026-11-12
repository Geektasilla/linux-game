"""Console interface. The look and the menus follow the original game (v1); all I/O goes through Console."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from collections.abc import Callable, Sequence

from terminal_challenge import __version__
from terminal_challenge.content import LANGUAGES, LEVELS, MODES, Theme, load_questions, load_strings, themes_for
from terminal_challenge.engine import DIFFICULTIES, SESSION_LENGTHS, Outcome, QuizSession

# Terminal colours of the original game
SOFT_ORANGE = "\033[38;5;214m"
CRAFT_ORANGE = "\033[38;5;166m"
ORANGE = "\033[38;5;208m"
BRIGHT_ORANGE = "\033[38;5;208m"
RED_BRIGHT = "\033[38;5;196m"
MUTED_GREEN = "\033[38;5;28m"
MEDIUM_GREEN = "\033[38;5;34m"
END = "\033[0m"

LOGO_LEFT = [
    "███████╗██╗   ██╗██████╗  ██████╗ ",
    "██╔════╝██║   ██║██╔══██╗██╔═══██╗",
    "███████╗██║   ██║██║  ██║██║   ██║",
    "╚════██║██║   ██║██║  ██║██║   ██║",
    "███████║╚██████╔╝██████╔╝╚██████╔╝",
    "╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ",
]
LOGO_RIGHT = [
    "███╗   ███╗ █████╗ ███████╗ ██████╗",
    "████╗ ████║██╔══██╗╚══███╔╝██╔═══██╗",
    "██╔████╔██║███████║  ███╔╝ ██║   ██║",
    "██║╚██╔╝██║██╔══██║ ███╔╝  ██║   ██║",
    "██║ ╚═╝ ██║██║  ██║███████╗╚██████╔╝",
    "╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝",
]
BAR = "▀" * 69
INTRO_PAUSE = 3.5  # seconds between the intro screens, as in the original


class QuitGame(Exception):
    """Raised when the player types 'end'."""


class Console:
    def __init__(
        self,
        input_fn: Callable[[str], str] | None = None,
        output_fn: Callable[[str], None] | None = None,
        color: bool = True,
        pause: Callable[[float], None] = time.sleep,
    ) -> None:
        self._input = input_fn or (lambda prompt: input(prompt))
        self._output = output_fn or (lambda text: print(text))
        self.color = color
        self.pause = pause

    def paint(self, text: str, color: str | None) -> str:
        return f"{color}{text}{END}" if color and self.color else text

    def say(self, text: str = "", color: str | None = None) -> None:
        self._output(self.paint(text, color))

    def ask(self, prompt: str) -> str:
        return self._input(self.paint(prompt, MUTED_GREEN) + " ").strip()


class Game:
    def __init__(self, console: Console, lang: str, rng: random.Random | None = None) -> None:
        self.console = console
        self.lang = lang
        self.text = load_strings(lang)
        self.rng = rng or random.Random()

    def t(self, key: str, **values: object) -> str:
        return self.text[key].format(**values)

    def read(self, prompt: str) -> str:
        """Read a line; 'end' quits the game from anywhere."""
        value = self.console.ask(prompt)
        if value.lower() == "end":
            raise QuitGame
        return value

    # ---- screens -------------------------------------------------------------------------------------------------

    def intro(self) -> None:
        say, c = self.console.say, self.console
        say()
        for left, right in zip(LOGO_LEFT, LOGO_RIGHT, strict=True):
            say(c.paint(left, RED_BRIGHT) + c.paint(right, ORANGE))
        say()
        say(BAR, RED_BRIGHT)
        say(" " * 16 + self.t("tagline_1"), ORANGE)
        say(" " * 20 + self.t("tagline_2"), ORANGE)
        say(" " * 12 + self.t("tagline_3"), ORANGE)
        say(BAR, RED_BRIGHT)
        c.pause(INTRO_PAUSE)

        say()
        say(self.t("warning_title"), RED_BRIGHT)
        say()
        say(self.t("warning_attention"), ORANGE)
        say(self.t("warning_body"))
        say()
        say(self.t("warning_consent"), ORANGE)
        say(self.t("warning_consent_body"))
        say()
        say(self.t("warning_limits_title"), ORANGE)
        say(self.t("warning_limits"))
        c.pause(INTRO_PAUSE)

        self.show_commands()
        c.pause(INTRO_PAUSE)

    def show_commands(self) -> None:
        self.console.say()
        self.console.say(self.t("commands_title"), MUTED_GREEN)
        self.console.say(self.t("commands"))

    def choose(self, title: str, options: Sequence[str], prompt: str, missing: str) -> int:
        """Numbered menu with the original error messages. Returns the index of the chosen option."""
        self.console.say(" ")
        self.console.say(title, MUTED_GREEN)
        for number, option in enumerate(options, start=1):
            self.console.say(f"{number}. {option}")
        while True:
            value = self.read(prompt)
            if not value.isdigit():
                self.console.say(self.t("input_error_digit"), RED_BRIGHT)
                continue
            if 1 <= int(value) <= len(options):
                return int(value) - 1
            self.console.say(self.t(missing, number=value), RED_BRIGHT)
            self.console.say(self.t("choose_range", max=len(options)), CRAFT_ORANGE)

    def choose_theme(self) -> Theme:
        themes = themes_for(self.lang)
        index = self.choose(self.t("choose_theme"), [t.title for t in themes], self.t("theme_prompt"), "theme_missing")
        self.console.say("\n" + self.t("theme_selected", value=themes[index].title), CRAFT_ORANGE)
        return themes[index]

    def choose_mode(self) -> str:
        while True:
            mode = MODES[self.choose(self.t("choose_mode"), list(MODES), self.t("mode_prompt"), "mode_missing")]
            if mode == "good" or self.confirm_mode(mode):
                break
            self.console.say(self.t("mode_back"), CRAFT_ORANGE)
        self.console.say("\n" + self.t("mode_selected", value=mode), CRAFT_ORANGE)
        return mode

    def confirm_mode(self, mode: str) -> bool:
        self.console.say()
        self.console.say(self.t("mode_warning_title", mode=mode.upper()), RED_BRIGHT)
        self.console.say(self.t("mode_warning_body"))
        if self.yes_no(""):
            self.console.say(self.t("mode_confirmed"), RED_BRIGHT)
            return True
        return False

    def choose_level(self) -> str:
        level = LEVELS[
            self.choose(self.t("choose_difficulty"), list(LEVELS), self.t("difficulty_prompt"), "difficulty_missing")
        ]
        self.console.say(" ")
        self.console.say(self.t(f"difficulty_{level}"), CRAFT_ORANGE)
        self.console.say(self.t("skips_allowed", count=DIFFICULTIES[level].skips))
        return level

    def choose_length(self) -> int:
        options = [self.t("length_option", count=n) for n in SESSION_LENGTHS]
        index = self.choose(self.t("choose_length"), options, self.t("length_prompt"), "length_missing")
        return SESSION_LENGTHS[index]

    def yes_no(self, prompt: str) -> bool:
        while True:
            value = self.read(prompt).lower()
            if value in {"y", "yes", "д", "да"}:
                return True
            if value in {"n", "no", "b", "н", "нет"}:
                return False
            self.console.say(self.t("yes_no"), RED_BRIGHT)

    # ---- game ----------------------------------------------------------------------------------------------------

    def play_round(self, theme: Theme, mode: str, level: str, length: int) -> QuizSession:
        pool = load_questions(level)
        session = QuizSession(self.rng.sample(pool, min(length, len(pool))), DIFFICULTIES[level])
        self.console.say(" ")
        self.console.say(self.t(f"attempts_{level}"), CRAFT_ORANGE)

        while not session.finished:
            self.console.say(f"{session.index + 1}.{session.current.text(self.lang)}")
            self.handle_answer(session, theme, mode)

        self.show_result(session, theme)
        return session

    def handle_answer(self, session: QuizSession, theme: Theme, mode: str) -> None:
        """Read input until the question is closed. Commands never cost an attempt."""
        question = session.current
        while True:
            raw = self.read(self.t("answer_prompt"))
            command = raw.lower()
            if command == "help":
                self.show_commands()
                continue
            if command == "skip":
                if session.skip():
                    self.console.say(self.t("skipped", count=session.skips_left) + "\n", CRAFT_ORANGE)
                    return
                self.console.say(self.t("no_skips"), RED_BRIGHT)
                continue

            outcome = session.answer(raw)
            correct = outcome is Outcome.CORRECT
            mark = self.console.paint("✔", MUTED_GREEN) if correct else self.console.paint("✘", RED_BRIGHT)
            self.console.say(f"{mark} {theme.reaction(self.lang, mode, correct, self.rng)}\n")
            if correct:
                return
            if outcome is Outcome.FAILED:
                self.console.say(self.t("out_of_attempts", answer=question.main_answer) + "\n", CRAFT_ORANGE)
                return
            self.console.say(self.t("attempts_left", count=session.attempts_left))

    def show_result(self, session: QuizSession, theme: Theme) -> None:
        percent = session.percent
        color = RED_BRIGHT if percent <= 40 else BRIGHT_ORANGE if percent <= 80 else MEDIUM_GREEN
        verdict = theme.verdict(self.lang, percent)
        self.console.say(self.t("result", correct=session.correct, total=session.total, percent=percent), color)
        self.console.say(verdict.status)
        self.console.say(self.rng.choice(verdict.comments))

    def run(self) -> None:
        self.intro()
        while True:
            theme = self.choose_theme()
            mode = self.choose_mode()
            level = self.choose_level()
            length = self.choose_length()
            self.play_round(theme, mode, level, length)
            if not self.yes_no(self.t("play_again")):
                self.console.say(self.t("play_again_no"), CRAFT_ORANGE)
                return
            self.console.say(self.t("play_again_yes") + "\n", CRAFT_ORANGE)


def choose_language(console: Console) -> str:
    console.say("1. Русский   2. English", MUTED_GREEN)
    while True:
        value = console.ask("Язык / Language:").lower()
        if value in {"1", "ru"}:
            return "ru"
        if value in {"2", "en"}:
            return "en"
        if value == "end":
            raise QuitGame


def enable_windows_colors() -> bool:
    """Turn on ANSI escape codes in the Windows console. Returns False if the console refuses."""
    import ctypes

    enable_virtual_terminal_processing = 0x0004
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    return bool(kernel32.SetConsoleMode(handle, mode.value | enable_virtual_terminal_processing))


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="linux-game", description="Linux command quiz for the terminal.")
    parser.add_argument("--lang", choices=LANGUAGES, help="interface language (asked at start if omitted)")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    interactive = sys.stdout.isatty()
    if sys.platform == "win32" and interactive:
        sys.stdout.reconfigure(encoding="utf-8")
        interactive = enable_windows_colors()
    use_color = not args.no_color and "NO_COLOR" not in os.environ and interactive
    console = Console(color=use_color)
    lang = args.lang or "ru"
    try:
        lang = args.lang or choose_language(console)
        Game(console, lang).run()
    except QuitGame:
        console.say(load_strings(lang)["goodbye"], CRAFT_ORANGE)
    except (KeyboardInterrupt, EOFError):
        console.say()
        console.say(load_strings(lang)["goodbye"], CRAFT_ORANGE)
    return 0
