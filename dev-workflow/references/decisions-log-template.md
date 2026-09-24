# Decisions: <project name>

> Lives once per **target project** at `DECISIONS.md` (repo root) — not per task, and not inside
> this skill. Append-only: never edit or delete a past entry, even if a later decision supersedes
> it — add a new entry that says so instead, so the log stays an honest record of how the project's
> direction actually moved, not a rewritten history.

## Why this file exists

Two problems, one file:

1. **Without it, the same question gets asked twice.** A choice the user made three tasks ago has
   nowhere to live except that old task's `STATUS.md`, which nobody re-reads before Step 1's intake
   — so the same fork in the road gets asked about again. Before asking anything in Step 1 or
   mid-execution in Step 5, check this file first; only ask if the question genuinely isn't
   answered here, isn't inferable from `CONSTITUTION.md` or the repo, and would actually change
   what gets built.
2. **Without it, nobody can see the project's direction at a glance.** Individual `STATUS.md` files
   are per-task; this file is the cross-task thread — the handful of real forks where the project
   could have gone a different way, and which way it went, in one place.

Only log decisions that meet the bar in `SKILL.md`'s Step 1/Step 5 guidance: the answer changed
what got built, and it wasn't inferable from the repo or an existing entry here. Don't log routine
implementation choices a spec would normally just make — this file tracks forks, not every detail.

## Entries

Newest first. Each entry: the fork (what was genuinely ambiguous or had real alternatives), the
decision, who made the call, and why — in enough detail that a future task can rely on it instead
of re-asking.

<!-- Example entry shape:
### <date> — <short title> (task: <specs/task-slug>)
- **Fork:** what was actually unclear or had more than one reasonable path
- **Decision:** what was chosen
- **Decided by:** user (asked directly) / Claude (stated as a default, unchallenged)
- **Why:** the reasoning, briefly
-->
