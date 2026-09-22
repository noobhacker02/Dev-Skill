# Tech stack recommendations

Starting points for Step 2 when a project is new or the user hasn't named a stack. These are
defaults, not mandates — deviate when the task has a specific reason to (an existing team
convention, a hard platform constraint, a library that only exists in one ecosystem). Always give
the pick plus the one main alternative and why it lost, rather than a bare menu.

## Web frontend

- **Recommend:** React + TypeScript + Vite. Vast ecosystem, fast dev loop, hiring/familiarity odds
  are good, TypeScript catches a real class of bugs before they ship.
- **Alternative:** Plain HTML/CSS/vanilla JS for something genuinely tiny (a single static page,
  a widget) where a build step is pure overhead.

## Backend API

- **Recommend:** Node.js + TypeScript + Express (or Fastify for higher throughput needs) if the
  team/task is JS-leaning; Python + FastAPI if it's data/ML-adjacent or the team is Python-leaning.
  Both have mature ecosystems and good async support.
- **Alternative:** Go (net/http or Chi) when raw performance or a single static binary for
  deployment matters more than ecosystem breadth.

## CLI tool

- **Recommend:** Match the surrounding ecosystem if there is one (a Node project gets a Node CLI,
  a Python project gets a Python CLI via `argparse`/`click`). For a genuinely standalone tool with
  no existing ecosystem, Python is the lowest-friction default — no build step, good stdlib.
- **Alternative:** Go when the deliverable needs to be a single dependency-free binary handed to
  users who may not have a runtime installed.

## Data / ML

- **Recommend:** Python + pandas/numpy, with FastAPI if it needs to be served.
- **Alternative:** rarely worth deviating — the ecosystem gravity here is real.

## Mobile

- **Recommend:** React Native if the team already knows React and the target is "one codebase,
  both platforms, not squeezing out every last bit of platform-native feel."
- **Alternative:** Native (Swift/Kotlin) when the task specifically needs deep platform
  integration or top-tier performance/UX that cross-platform frameworks compromise on.

## Database

- **Recommend:** PostgreSQL as the default relational choice — mature, capable of both simple and
  fairly heavy workloads without an early migration.
- **Alternative:** SQLite for a local-only tool or prototype with no concurrent-write requirement.
