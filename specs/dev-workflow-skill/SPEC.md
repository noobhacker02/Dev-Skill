# Spec: dev-workflow skill

## Request

Build a Claude Code skill encoding a spec-first development loop: restate the ask → detect/pick
the tech stack → write a spec + changelog → research prior art → implement → run a pre-commit
quality gate on staged changes → commit locally → verify locally (Playwright + stack-appropriate
tests) → write a status report → checkpoint with the user on iterate-vs-push → loop. Also install
git hooks (pre-commit + pre-push) backed by TruffleHog that block secrets, `.env` files, and
destructive SQL/shell commands from being committed or pushed.

## Restated scope

A reusable skill (not a one-off script) that a future Claude Code session can follow for any
non-trivial build/fix/ship task, in any target repo. In scope: the workflow's instructions
(SKILL.md), the templates it points to, the safety-check engine and the git hooks that wrap it,
and an install path for wiring the hooks into a target repo. Out of scope: this skill does not
itself decide *what* to build — it structures how any given build happens. It does not manage
CI/CD, deployment, or remote branch protection rules (a git hook is a local, per-clone control, not
a substitute for server-side branch protection — noted as a known limitation, not solved here).

## Tech stack

The skill's own instructions are Markdown (`SKILL.md` + `references/*.md`). Its enforcement logic
is Python 3 standard-library only (no dependencies to install) for the actual pattern matching,
wrapped in thin Bash for the git-hook plumbing (`pre-commit`/`pre-push` are what git actually
invokes, and bash is what's universally available there). This split was chosen over an
all-bash implementation because Python's `re` module supports lookahead assertions and multiline
diff parsing far more reliably than portable POSIX/BSD-compatible bash+grep would, without adding
a real dependency (python3 is assumed present in any dev environment this skill targets).

## Requirements

1. `SKILL.md` documents all nine per-task phases plus the one-time hook install step, each with
   enough "why" that a future session can use judgement on when a phase can be shortened, not just
   follow it by rote.
2. A spec template, changelog template, status-report template, and tech-stack recommendation
   guide exist under `references/` and are referenced from `SKILL.md`.
3. `scripts/check_staged.py` detects, in both a "staged changes" mode and a "commit range" mode:
   `.env` files (excluding `.example`/`.sample`/`.template`/`.dist`), common hardcoded-secret
   shapes (AWS keys, private key blocks, GitHub/Slack/OpenAI-style tokens, generic
   password/API-key assignments), and destructive SQL/shell patterns (`DROP`/`TRUNCATE`, unguarded
   `DELETE`/`UPDATE`, `rm -rf` on root/home/wildcard, `git push --force`, `git reset --hard`, etc.),
   and shells out to TruffleHog when present.
4. False positives can be suppressed per-line (`devskill:allow` inline) or repo-wide
   (`.devskill-allowlist` regex file), so the checks don't become something people route around.
5. `scripts/install-hooks.sh` wires `check_staged.py` into a target repo's `pre-commit` and
   `pre-push` hooks via a tracked `.githooks/` directory + `core.hooksPath`, idempotently.
6. Missing TruffleHog degrades to a warning, not a block — the pattern checks above already
   provide a real baseline, and requiring a third-party tool before a contributor's first commit
   would cost more in adoption than it buys in safety (explicit product decision, confirmed with
   the requester rather than assumed).

## Expected output / deliverable

`dev-workflow/` containing `SKILL.md`, `scripts/{check_staged.py,install-hooks.sh,hooks/{pre-commit,pre-push}}`,
`references/{spec-template,changelog-template,status-report-template,tech-stack-guide,hooks}.md`,
and `.devskill-allowlist.example`; a root `README.md` and `CHANGELOG.md` for this project;
`evals/evals.json` with realistic test prompts; this spec and its companion `STATUS.md`, written
by applying the skill to itself.

## Test plan

| Requirement | How it will be verified |
|---|---|
| Hooks block secrets/.env/destructive commands on commit and push | Functional test in a scratch repo: stage/commit an AWS key, a private key, a `.env` file, `DROP TABLE`, `rm -rf /`, `git push --force` — each must be rejected; a clean commit, `.env.example`, `--force-with-lease`, and an inline `devskill:allow`-marked line must all be accepted. Pre-push tested against a bare remote, including a first-push-of-a-new-branch and a commit smuggled past `--no-verify`. |
| TruffleHog absence degrades gracefully | Run the above in an environment without TruffleHog installed (this container) and confirm a warning is printed but pattern-based blocking still occurs. |
| The skill actually produces the intended behavior end-to-end, not just its individual scripts | Two skill-creator evals run with-skill vs. baseline subagents: (0) a brand-new, stack-unspecified CLI task, to check the tech-stack-recommendation and from-scratch spec/changelog/checkpoint flow; (1) a feature request against an existing Node/Express/Knex/Postgres fixture repo that inherently involves a destructive operation (a dev-database reset), to check stack detection and whether the workflow's caution around destructive actions actually shows up in what gets built, not just in the git hooks. |
| Skill triggers appropriately | Deferred — description-trigger optimization (skill-creator's eval-set + `run_loop.py`) is a separate, optional pass; not required to consider this build done. |

## Open questions / risks

- Git hooks are a local, per-clone control (`core.hooksPath` isn't versioned) — a contributor who
  never runs `install-hooks.sh` gets no protection. Documented in `references/hooks.md`, not
  solved (would need a server-side check, e.g. a GitHub Actions secret-scan job, to fully close —
  out of scope for this skill, which is about the local dev loop).
- The destructive-SQL/shell patterns are heuristics (e.g. "no `WHERE` on the same line" misses a
  multi-line statement) — deliberate scope limit; TruffleHog and human review in Step 6 are the
  deeper layers, not the regexes.
