# Contributing

This repo holds a single Claude Code skill (`dev-workflow/`) plus its own dogfooded specs. Changes
to it should go through the workflow it describes:

1. Write or update a spec under `specs/<slug>/SPEC.md` (use `dev-workflow/references/spec-template.md`)
   describing what's changing and how it'll be verified.
2. Add a `CHANGELOG.md` entry under `[Unreleased]`.
3. Before committing, run the safety/quality gate:
   ```bash
   python3 dev-workflow/scripts/check_staged.py --mode=commit
   ```
4. If you're touching `scripts/check_staged.py` or the hooks, test them functionally in a scratch
   repo (stage a fake secret, a `.env` file, a destructive SQL/shell snippet — confirm each is
   blocked, and that a clean commit still succeeds) rather than only reading the diff.
5. Open a PR with the spec and changelog entry linked.

The git hooks in this repo (installed via `dev-workflow/scripts/install-hooks.sh`) will also catch
secrets and destructive commands automatically on `git commit` / `git push` — run the installer
once after cloning if `git config core.hooksPath` doesn't already point at `.githooks`.
