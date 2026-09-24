# Dev-Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security gate](https://github.com/noobhacker02/Dev-Skill/actions/workflows/security-gate.yml/badge.svg)](https://github.com/noobhacker02/Dev-Skill/actions/workflows/security-gate.yml)

A Claude Code skill (`dev-workflow/`) that drives a spec-first development loop: restate the ask,
pin the tech stack, write a spec + changelog, research prior art, implement, run a pre-commit
safety gate, commit locally, verify locally, report status, and checkpoint with the user before
anything reaches the remote. It also ships tracked git hooks (pre-commit + pre-push, Gitleaks- and
TruffleHog-backed with a pattern-based fallback) that block secrets, `.env` files, and destructive
SQL/shell commands, plus a GitHub Actions gate that re-runs the same check server-side on every PR.

## The loop

```
 Step 0 (once)        Steps 1–2                    Steps 3–9 repeat
 ┌───────────┐    ┌──────────────┐   ┌──────────────────────────────────────────────────┐
 │  install  │───▶│ Intake ──────┤   │ Spec + changelog → Research → Execute → Quality   │
 │   hooks   │    │ Tech stack   │──▶│ gate → Local commit → Local verification →         │
 └───────────┘    └──────┬───────┘   │ Status report + checkpoint ──┐                    │
                         │           └───────────────────────────────┼────────────────────┘
                         ▼                                           │
              reads CONSTITUTION.md,                     iterate? ◀──┘   push? ──▶ git push
              checks DECISIONS.md before                 (loop to Step 3)   (pre-push hook
              asking anything (see below)                                   is the last gate)
```

See `dev-workflow/SKILL.md` for the full description of each step and why it exists.

## Avoiding guesses: questions, decisions, and plan drift

Three things work together so the loop never has to silently guess what you meant, and never gets
to re-ask something you already told it:

1. **A question only gets asked if it clears three bars** (Step 1, and the same bar again in Step
   5 if a fork shows up mid-build): the answer would actually change what gets built, it isn't
   inferable from the repo or `CONSTITUTION.md`, and it isn't already answered in `DECISIONS.md`.
   If several things are genuinely unclear, they get asked together in one round — not a drip-feed
   of one question at a time. If nothing clears the bar, the skill states its interpretation and
   moves on rather than asking out of caution.
2. **`DECISIONS.md`** (optional, project-wide, same pattern as `CONSTITUTION.md` — see
   `dev-workflow/references/decisions-log-template.md`) is the append-only record of every real
   fork: what was unclear, what was decided, who decided it, and why. It's checked *before* any
   question is asked, so the same fork never gets asked about twice across different tasks. It's
   also what keeps a low-memory orchestrator (like the companion `agent-loop` project's Overseer)
   informed without needing the full conversation history — the log is the interface, not
   somebody's memory of a chat three tasks ago.
3. **A required "Plan vs Actual" section in every `STATUS.md`** (Step 9) means a deviation from the
   spec gets named explicitly — "matched exactly" is a required sentence when true, not something
   left out because there was nothing to report. If execution took a different path than `SPEC.md`
   described, the status report says exactly where and why, pointing at the `DECISIONS.md` entry if
   the fork was resolved by asking.

The net effect: the same question doesn't get asked twice, a silent guess doesn't get built without
being named as one, and there's a durable, cross-task record of which way the project actually went
and why — not just what any single task happened to do.

## Layout

```
dev-workflow/
├── SKILL.md                        the skill itself — start here
├── scripts/
│   ├── check_staged.py             secret / .env / destructive-command scanner (Gitleaks + TruffleHog + patterns)
│   ├── install-hooks.sh            one-time per-repo hook installer
│   └── hooks/                      pre-commit / pre-push wrappers install-hooks.sh copies in
└── references/
    ├── spec-template.md
    ├── changelog-template.md
    ├── status-report-template.md
    ├── tech-stack-guide.md
    ├── constitution-template.md    optional project-wide conventions file for target repos
    ├── decisions-log-template.md   optional project-wide decision log (DECISIONS.md) for target repos
    ├── model-effort-tiers.md       which model/effort tier to use for which phase
    ├── roadmap.md                  known limitations, deferred ideas, notes from real usage
    └── hooks.md                    what the hooks block, false-positive handling, troubleshooting
.github/workflows/security-gate.yml  CI re-run of check_staged.py against every PR's diff
specs/                              this repo's own specs, written using the skill on itself
evals/evals.json                     test prompts used to validate the skill in skill-creator
CHANGELOG.md                         this project's changelog (Keep a Changelog format)
```

## Quickstart: install the skill in another project

Copy `dev-workflow/` into that project's (or your personal) skills directory so Claude Code
auto-discovers it:

```bash
# Project-level — this project only, committed and shared with a team
git clone https://github.com/noobhacker02/Dev-Skill.git /tmp/dev-skill-src
mkdir -p .claude/skills
cp -r /tmp/dev-skill-src/dev-workflow .claude/skills/dev-workflow

# Personal — every project on your machine
cp -r /tmp/dev-skill-src/dev-workflow ~/.claude/skills/dev-workflow
```

Requires **git**, **bash**, and **python3** (standard library only — no `pip install`); Gitleaks,
TruffleHog, and Playwright are used automatically when present and otherwise skipped gracefully
(see `dev-workflow/SKILL.md`'s `compatibility` frontmatter). No API key or separate auth needed
beyond whatever Claude Code session you're already running it in.

Once installed, Claude invokes it on its own for coding requests (measured: 8 of 8 held-out coding asks,
0 of 2 plain questions; see CHANGELOG) — you don't
need to name it explicitly. The first time it runs in a given target repo, it also runs:

```bash
bash dev-workflow/scripts/install-hooks.sh
```

from inside that repo, which installs the safety hooks there (see
`dev-workflow/references/hooks.md` for exactly what they block and how to handle a false
positive).

## Safety hooks, standalone

The hooks don't require the rest of the workflow — `scripts/check_staged.py` and
`scripts/install-hooks.sh` are usable on their own in any git repo if all you want is the
secret/`.env`/destructive-command scanning on commit and push.

## Related projects

[**agent-loop**](https://github.com/noobhacker02/Agentic-dev-alpha) is a separate multi-agent orchestrator
(Claude Agent SDK, TypeScript) built specifically to test whether this skill's dev lifecycle actually
works: an Overseer plus five worker phases (planner, test-designer, builder, verifier, gatekeeper)
run a task end-to-end with a live browser UI for approving/rejecting every tool call, so the process
can be watched and judged rather than trusted on faith. It's meant to both evaluate `dev-workflow`
and, self-referentially, be built and improved using `dev-workflow`'s own method. Its Overseer also
reads a project's `DECISIONS.md` directly (indexed, not held in any one phase's session memory) when
one exists — the same log this skill's own loop writes to.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
