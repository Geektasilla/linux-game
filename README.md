# 🐧 Linux Game — SUDOMAZO

[![Tests](https://github.com/Geektasilla/linux-game/actions/workflows/tests.yml/badge.svg)](https://github.com/Geektasilla/linux-game/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Languages](https://img.shields.io/badge/UI-RU%20%7C%20EN-blue)

A Linux command quiz that runs in your terminal. You get a task — *"Find files in /tmp older than 7 days"* —
and type the command. Characters from your favourite TV universe comment on every answer.

```text
███████╗██╗   ██╗██████╗  ██████╗ ███╗   ███╗ █████╗ ███████╗ ██████╗
██╔════╝██║   ██║██╔══██╗██╔═══██╗████╗ ████║██╔══██╗╚══███╔╝██╔═══██╗
███████╗██║   ██║██║  ██║██║   ██║██╔████╔██║███████║  ███╔╝ ██║   ██║
╚════██║██║   ██║██║  ██║██║   ██║██║╚██╔╝██║██╔══██║ ███╔╝  ██║   ██║
███████║╚██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║███████╗╚██████╔╝
╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
                [ SYSTEM: ESCAPE NOT POSSIBLE ]
            >>>>>>> SHOW THEM WHO THE REAL ROOT IS! <<<<<<<<

► ► You have 2 attempts per question. Don't mess it up.
2.Find files in the current directory larger than 100 megabytes.
Your answer: find . -size 100M
✘ Wrong. Your answer has the stability of a Friday evening deploy.
Attempts left: 1
Your answer: find . -size +100M
✔ Right. Merge approved. Reluctantly.

3.Terminate the process named 'firefox' (with the default signal).
Your answer: skip
Question skipped. Skips left: 1
...
Correct answers: 9 of 10 (90%)
Rank: True root
Linus would merge this without comments. That never happens.
```

## Features

- **176 tasks** on three levels — from `ls` and `pwd` to cron schedules, `find -exec`, `awk`, `sed` and `tar`
- **9 universes** for the commentary: Star Wars, The Big Bang Theory, Silicon Valley, Breaking Bad, Linux,
  The Sopranos, Rick and Morty, Shrek, Game of Thrones — almost 3,000 reaction phrases
- **Three tones**: `good`, `bad` and `verybad` — from friendly to merciless sarcasm, always without swearing;
  `bad` and `verybad` ask for confirmation first
- **Difficulty** defines attempts per question and skips per game (1 / 2 / 3); sessions of 10, 30 or 60 questions
- **Russian and English** interface and tasks (theme commentary: Russian for all themes, English for *Linux*)
- Answers are compared tolerantly: extra spaces, `"` vs `'` and a trailing `;` do not matter
- Commands during the game: `skip`, `help`, `end`
- No dependencies — just Python 3.10+

## Run it

```bash
git clone https://github.com/Geektasilla/linux-game.git
cd linux-game
python -m terminal_challenge            # asks for the language
python -m terminal_challenge --lang en
```

Or install it as a command:

```bash
pip install .
linux-game --lang en
```

## How it is built

```
terminal_challenge/
├── engine.py      # game rules: answer checking, attempts, skips, score — no input/output
├── content.py     # loads themes, questions and UI texts from JSON
├── cli.py         # console interface; all I/O goes through one Console class
└── data/
    ├── questions.json        # 176 tasks, prompts in RU and EN, accepted answers
    ├── themes/<theme>.json   # reactions per language / tone / correct-wrong + result ranks
    └── i18n/{ru,en}.json     # interface texts
```

- **Rules are separated from I/O.** `QuizSession` knows nothing about the terminal, so the rules are tested directly.
- **The whole game is testable.** `Console` takes the input and output functions as parameters; tests play complete
  games with a scripted console and check what the player sees.
- **Content is data, not code.** Adding a theme or a translation means adding JSON — no Python changes.
  The theme list in each language is built from the content that exists for that language.

## Tests

```bash
pip install -e ".[dev]"
pytest --cov=terminal_challenge
```

**84 tests, 96 % coverage**, run in GitHub Actions on Linux, Windows and macOS with Python 3.10 and 3.13:

- **Rules** — answer normalisation, attempts, skip limit, score calculation
- **Content validation** — every theme has enough phrases for every tone, all five ranks, every task is bilingual and
  its main answer is accepted, both UI languages have the same keys, **and no text contains swear words**
- **End-to-end games** — the intro screens and original menus, a perfect game, wrong answers, skips, invalid input,
  replay, quitting, every theme in every mode played to the result screen, the English version

## Background

The first version (*SUDOMAZO*) was a team practice project at IT Career Hub (December 2025), which I coordinated and later
continued on my own. This repository is my rewrite of it: the same look and menus, but a new architecture, tests,
two languages, fixes for several crashes, and content without swearing. Details: [docs/development.md](docs/development.md).

## Contributing a translation

English commentary currently exists for the *Linux* theme. To add another one, put an `"en"` section next to `"ru"`
in `terminal_challenge/data/themes/<theme>.json` (same structure) — the theme then appears in the English menu
automatically, and the content tests check that it is complete.
