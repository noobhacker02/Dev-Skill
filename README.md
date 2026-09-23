# Dev-Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Claude Code skill (`dev-workflow/`) that drives a spec-first development loop: restate the ask,
pin the tech stack, write a spec + changelog, research prior art, implement, run a pre-commit
safety gate, commit locally, verify locally, report status, and checkpoint with the user before
anything reaches the remote. It also ships tracked git hooks (pre-commit + pre-push, Gitleaks- and
TruffleHog-backed with a pattern-based fallback) that block secrets, `.env` files, and destructive
SQL/shell commands, plus a GitHub Actions gate that re-runs the same check server-side on every PR.

## The loop

```
Intake → Tech stack → Spec + changelog → Research → Execute → Quality gate
   ↑         (once)                                                  │
   └──────────────────── Status report + checkpoint ←── Local verification ← Local commit
```

Steps 3–9 repeat: after the status report, the user decides whether to iterate again or push, and
either answer feeds back into the loop. See `dev-workflow/SKILL.md` for the full description of
each step and why it exists.

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
    ├── model-effort-tiers.md       which model/effort tier to use for which phase
    ├── roadmap.md                  known limitations, deferred ideas, notes from real usage
    └── hooks.md                    what the hooks block, false-positive handling, troubleshooting
.github/workflows/security-gate.yml  CI re-run of check_staged.py against every PR's diff
specs/                              this repo's own specs, written using the skill on itself
evals/evals.json                     test prompts used to validate the skill in skill-creator
CHANGELOG.md                         this project's changelog (Keep a Changelog format)
```

## Using the skill

Point a Claude Code session at `dev-workflow/SKILL.md` (or install it as a project/personal
skill) and it will drive the loop described there for any non-trivial build/fix/ship request. The
first time it's used in a given target repo, it runs:

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

[**agent-loop**](https://github.com/noobhacker02/test-dev-1) is a separate multi-agent orchestrator
(Claude Agent SDK, TypeScript) built specifically to test whether this skill's dev lifecycle actually
works: an Overseer plus five worker phases (planner, test-designer, builder, verifier, gatekeeper)
run a task end-to-end with a live browser UI for approving/rejecting every tool call, so the process
can be watched and judged rather than trusted on faith. It's meant to both evaluate `dev-workflow`
and, self-referentially, be built and improved using `dev-workflow`'s own method.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
