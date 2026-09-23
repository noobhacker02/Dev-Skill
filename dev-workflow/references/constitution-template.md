# Constitution: <project name>

> Lives once per **target project** at `CONSTITUTION.md` (repo root) — not per task, and not
> inside this skill. A spec (Step 3) should reference this file for anything it covers rather than
> re-deriving the same conventions from scratch on every task; only put a decision here if it's
> meant to hold across most or all future work in this repo, not just the current one.

## Why this file exists

Without it, every spec re-litigates the same questions — which test framework, how errors surface
to users, what "done" means for a migration — and answers drift slightly each time. This file is
the place those answers live once. Keep it short: a handful of real, load-bearing decisions beats
a long list of restated defaults nobody would have gotten wrong anyway.

## Tech stack

The stack this project actually uses, and anything a spec shouldn't re-decide (e.g. "Postgres via
Knex, not raw SQL" or "React function components only, no classes").

## Conventions

Naming, file layout, error-handling style, logging — whatever this project does consistently that
a new contributor (or a fresh Claude Code session) would otherwise have to infer from reading
around.

## Non-negotiables

Hard constraints a spec must respect no matter what it's building — a compliance requirement, a
performance budget, a platform this must keep running on, data that must never leave a region.

## Out of scope for this file

Anything specific to one task belongs in that task's `SPEC.md`, not here. If you're not sure
whether something is project-wide or task-specific, default to the spec — this file should change
rarely; a spec changes every task.
