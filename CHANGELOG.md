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
