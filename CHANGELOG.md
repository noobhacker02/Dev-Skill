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
- Gitleaks as a second, fast maintained-ruleset secret-scan layer in `check_staged.py`, alongside
  TruffleHog's deeper/verified scan and the always-on pattern baseline — matches the industry
  pre-commit-fast/CI-deep pairing (see `dev-workflow/references/hooks.md`).
- `dev-workflow/references/constitution-template.md`: an optional, project-wide `CONSTITUTION.md`
  a target repo can keep so specs stop re-deriving the same conventions every task (the one piece
  worth taking from GitHub Spec Kit / OpenSpec without adopting their whole framework).
- `.github/workflows/security-gate.yml`: server-side CI re-run of `check_staged.py` against every
  PR's diff — closes the gap where a clone that never ran `install-hooks.sh` gets no local
  protection. Runs against `.githooks/check_staged.py`, the same tracked copy the local hooks use.
- `dev-workflow/references/roadmap.md`: living doc for known limitations, ideas considered and
  rejected, and notes from using this skill in other projects.
- **Fixed a real gap found while adding the CI workflow**: `.githooks/` had been generated locally
  by `install-hooks.sh` during earlier dogfooding but was never actually committed — this repo's
  own local hooks were silently not enforced for anyone re-cloning it. Now tracked.

### Fixed
- `check_staged.py` no longer flags documentation (`.md`/`.mdx`/`.rst`/`.txt`) for *naming* the
  destructive patterns it detects — found by running the quality gate on this repo's own diff,
  which itself documents those patterns. Secret scanning still applies to docs.
- SKILL.md Step 9 now explicitly says to commit `STATUS.md` — found because two iteration-2 eval
  runs interpreted the previous silence differently (one committed it as a follow-up commit, one
  left it uncommitted as a "handback note"). Wording fix, verified by inspection rather than a full
  re-run (low-risk, doesn't change any logic the skill executes).

### Verified
- Functional hook tests re-run with a real TruffleHog binary installed (previously only the
  pattern-based fallback had been exercised): confirmed it independently catches a secret shape
  (a Stripe key) our own patterns don't cover, and correctly ignores TruffleHog's own well-known
  public example key rather than flagging it as noise.
- skill-creator eval loop (2 test prompts, with-skill vs. no-skill baseline, 7 assertions each):
  100% pass rate with the skill vs. 43% without — see `specs/dev-workflow-skill/STATUS.md` for the
  full breakdown and the benchmark/review viewer.
- Iteration 2: 3 new mock scenarios targeting previously-untested paths — an existing repo with a
  `CONSTITUTION.md` (respected, verified live), a browser-facing form-validation task (verified
  with real Playwright/Chromium, 23/23 assertions, real screenshots), and a genuinely ambiguous
  two-word request with zero context (correctly recognized as unanswerable without more input and
  stopped rather than fabricating a system). 19/19 assertions passed across all three — see
  `specs/dev-workflow-skill/STATUS.md`.

### Known issues
- skill-creator's automated description-trigger optimization pass (`run_loop.py`) doesn't work
  against this Claude Code CLI version — it registers the candidate skill as a slash command and
  waits for a `Skill`-tool call to detect triggering, but the model never invokes commands that
  way. Confirmed by manual replication (the model used `Bash` directly) and by 0% recall staying
  identical across three unrelated description rewordings. Stopped rather than tune against a
  broken signal; see `specs/dev-workflow-skill/STATUS.md`.
