# Development history

## Version 1 — prototype (December 2025 – January 2026)

The game started as a team practice project at IT Career Hub. The goal was to learn to build a project together
and to give students a fun way to find gaps in their Linux knowledge.

I coordinated the work in short sprints with a written plan for each meeting:

| Sprint | Focus |
|---|---|
| 22.12.2025 | Goals and value of the project, repository structure (`main` + `devops` branches), file formats, deadline |
| 24.12.2025 | Themes split between three participants; question sets trimmed to ~60 per difficulty level |
| 26.12.2025 | Game logic description, result ranks by score, one naming convention for all content files |
| 27.12.2025 | Beta version for a plain terminal on any OS: intro, content warning, short instructions, backlog |
| 02.01.2026 | Exception-handling tests, wrap-up, ideas for a Telegram version |

The reaction phrases were generated with AI assistants (ChatGPT, Gemini, Blackbox AI) from prompts we wrote,
then reviewed and edited by hand.

Afterwards I continued the game on my own: the game engine, a start sound, and showing the correct answer
when all attempts are used.

The prototype worked, but every theme was stored as 7 Python modules (63 files in total) that were imported by name,
the game loop was a single 260-line function, and there were no tests.

## Version 2 — rewrite (November 2026)

| Problem in v1 | Solution in v2 |
|---|---|
| 63 near-identical `.py` content modules imported dynamically | One JSON file per theme, validated by tests |
| One 260-line `main()` mixing rules, input and output | `engine.py` (pure rules), `content.py` (data), `cli.py` (console I/O) |
| No tests | 84 tests: rules, content validation, full games through a scripted console |
| Game of Thrones crashed on the result screen (wrong key in the data) | Data schema is the same for every theme and checked in CI |
| The Big Bang Theory crashed at 41–60 % (missing rank) | Test requires all five ranks in every theme |
| 100 % was impossible in a 60-question session (only 58 questions exist) | Score is calculated from the questions actually played; only available lengths are offered |
| `help` and other commands used up an answer attempt | Commands are handled before the answer is checked |
| `ls  -l` (two spaces) was a wrong answer | Answers are normalised (spaces, quote style) |
| Any answer other than y/n in the mode warning silently returned to the menu | The question is asked again |
| Result was shown as a rounded bucket ("80% правильных ответов" for 70 %) | Exact result: correct of total and percent |
| Sound path hard-coded to one user's computer, Windows only | Sound removed — the game is the same on every OS |
| Russian only | Interface and all 176 questions in Russian and English (same logo, colours and menus) |
| Explicit language in the `bad` / `verybad` modes | Same three modes; swear words replaced or removed, and a test fails on any swear word |
