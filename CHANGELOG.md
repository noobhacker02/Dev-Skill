# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `dev-workflow` skill: the full spec-first development loop (intake, tech stack, spec +
  changelog, research, execute, quality gate, local commit, local verification, status report +
  checkpoint) — see `dev-workflow/SKILL.md` and `specs/dev-workflow-skill/SPEC.md`.
- `scripts/check_staged.py`: secret, `.env`, and destructive SQL/shell scanner, used directly by
  the workflow's quality gate and by the installed git hooks.
- `scripts/install-hooks.sh` and tracked `pre-commit` / `pre-push` hooks (TruffleHog-backed with a
  pattern-based fallback) that block secrets and destructive commands from being committed or
  pushed.
- Reference templates for specs, changelogs, status reports, and tech-stack recommendations.
- `references/model-effort-tiers.md`: guidance on matching model/effort to phase — highest at Plan
  (Steps 1–4), lowest at Execute (Step 5), medium-in-a-fresh-context at Recheck (Steps 6/8/9).
- Repo housekeeping: `LICENSE` (MIT), `.gitignore`, `CONTRIBUTING.md`.

### Fixed
- `check_staged.py` no longer flags documentation (`.md`/`.mdx`/`.rst`/`.txt`) for *naming* the
  destructive patterns it detects — found by running the quality gate on this repo's own diff,
  which itself documents those patterns. Secret scanning still applies to docs.

### Verified
- Functional hook tests re-run with a real TruffleHog binary installed (previously only the
  pattern-based fallback had been exercised): confirmed it independently catches a secret shape
  (a Stripe key) our own patterns don't cover, and correctly ignores TruffleHog's own well-known
  public example key rather than flagging it as noise.
- skill-creator eval loop (2 test prompts, with-skill vs. no-skill baseline, 7 assertions each):
  100% pass rate with the skill vs. 43% without — see `specs/dev-workflow-skill/STATUS.md` for the
  full breakdown and the benchmark/review viewer.

### Known issues
- skill-creator's automated description-trigger optimization pass (`run_loop.py`) doesn't work
  against this Claude Code CLI version — it registers the candidate skill as a slash command and
  waits for a `Skill`-tool call to detect triggering, but the model never invokes commands that
  way. Confirmed by manual replication (the model used `Bash` directly) and by 0% recall staying
  identical across three unrelated description rewordings. Stopped rather than tune against a
  broken signal; see `specs/dev-workflow-skill/STATUS.md`.
