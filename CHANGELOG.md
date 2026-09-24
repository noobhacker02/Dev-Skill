# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Security
- **`check_staged.py` scanner hardened after an adversarial stress test found it catching only 3 of
  19 real secret formats and 7 of 26 destructive commands, plus three structural bypasses.** Full
  before/after and the exact test commands are in
  [`docs/STRESS-TEST-REPORT.md`](docs/STRESS-TEST-REPORT.md); headline numbers:
  `tests/stress/scan_stress.py` 32/68 → 67/68 (the one remaining failure — a secret split across
  string concatenation, e.g. `"sk-ant-" + "api03-..."` — is a documented, deliberately out-of-scope
  limitation: catching it would require parsing string-concatenation semantics, not pattern
  matching), `tests/stress/scan_stress2.py` 4/8 → 6/8 (see the two accepted exceptions below).

  **Secrets** — `SECRET_PATTERNS` only covered AWS keys, private-key headers, and Slack tokens.
  Added GitHub (classic + fine-grained), Anthropic, OpenAI (incl. project keys), Stripe, and Google
  API key formats, JWTs, and inline-password connection strings (`user:pass@host`). Generic
  key/token/password patterns now capture the secret into a named group and check *only that value*
  against the placeholder list (`changeme`, `example`, `<...>`, etc.) — previously the whole line was
  checked, so a line assigning a real-looking secret to a `password` variable was waved through
  simply because the line also contained the literal word "password".

  **Destructive commands** — the old check was ~6 fixed regexes for exact flag spellings. Ported
  `hasDangerousRm()` from `agent-loop/src/hooks.ts`'s safety net: tokenizes an `rm` invocation and
  checks for recursive+force *independent of flag order or spelling* (`-rf`, `-fr`, `-r -f`,
  `--recursive --force`) against a dangerous-target pattern (`/`, `~`, `$HOME` in its quoted/braced
  forms, `..`, bare `*`) — catching both the raw and quote-stripped form of each token so
  `rm -rf "$DIR"/` matches without the trailing slash mangling the closing quote. Added DROP INDEX,
  TRUNCATE-without-TABLE, `WHERE 1=1`, knex `.dropTable(`, and Django
  `.objects.all().delete()`. Fixed a DELETE/UPDATE guard-clause bug: `UPDATE ... SET a=1` (the first
  line of a legitimately multi-line, WHERE-guarded statement) was a false positive, while a genuinely
  unguarded single-line `DELETE FROM users` was a false *negative* — fixed by requiring UPDATE's
  match to have its terminating `;` on the same line, and adding one-line lookahead so a `WHERE` on
  the very next added line suppresses the DELETE finding.

  **Doc-exemption abuse** — Markdown files were fully exempt from destructive-command scanning, so
  `rm -rf /` inside a fenced ` ```bash ` block in a `SETUP.md` that CI or a copy-pasting developer
  actually executes went completely unscanned. The scanner now fetches the full file content and
  tracks fence state so only prose is exempt — code blocks are still scanned regardless of file
  extension.

  **Structural bypasses found by `scan_stress2.py`**:
  - `git mv secret .env` didn't trip the `.env` check because `--diff-filter=ACM` has no `R` —
    renamed files were invisible to `git diff --name-only`. Added `R` and `-M`.
  - Non-ASCII filenames (e.g. `café/.env`) were octal-escaped by git's default `core.quotePath`,
    breaking the filename regex. Now passes `-c core.quotePath=false` and uses NUL-separated
    (`-z`) output throughout.
  - `subprocess.run(..., text=True)` with no `errors=` raised `UnicodeDecodeError` on non-UTF-8
    staged content; the resulting traceback happened to exit non-zero, which the test suite counted
    as "correctly blocked" — a crash masquerading as a working control. Added
    `encoding="utf-8", errors="replace"`.
  - Push-mode's git helper discarded non-zero exit codes, so an unresolvable ref silently produced
    an empty diff and passed clean. Now fails closed with an explicit `SCAN_ERROR` finding.
  - A brand-new branch's first push diffed against the empty tree, rescanning the *entire* history
    it forked from and false-positiving on old, already-reviewed files. `resolve_push_base()` now
    substitutes the merge-base against a discoverable `main`/`master`/`origin/main`/`origin/master`
    ref, falling back to the empty tree (safe, just noisier) only when none exists.

  **CI-gate tampering** (`.github/workflows/security-gate.yml`) — the gate ran
  `.githooks/check_staged.py` from the PR's own checked-out working tree, so a PR could replace the
  scanner with `exit(0)` and pass its own gate. Not fixable in the script itself — a replaced copy of
  a self-check has no way to defend against its own replacement. Fixed at the workflow level:
  extracts the scanner from the immutable base-commit git object (`git show <base-sha>:...`) and
  runs *that* copy against the PR's diff instead.

  **Accepted, not fixed**: (1) the string-concatenation secret case above; (2) `scan_stress2.py`'s
  CI-bypass test necessarily runs the *replaced* copy of the scanner directly, by design — it can
  only be exercised for real by the workflow-level fix, not this local test; (3) `git commit
  --no-verify` bypassing the local hook entirely — a git-native feature, not something any
  pre-commit hook can prevent from inside itself.

  Verified with `python3 tests/stress/scan_stress.py` and `python3 tests/stress/scan_stress2.py`;
  `.githooks/check_staged.py` re-synced from the fixed source via `install-hooks.sh` so this repo's
  own local hook enforces the current scanner.

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
- Iteration 3: real skill-triggering test via the companion `agent-loop` project (installs
  `dev-workflow` as a real project skill in a throwaway repo, runs one real Agent SDK session with
  an ordinary feature request that never says "spec" or "workflow"). The `Skill` tool fired
  unprompted, and all 9 independently-checked artifacts the loop requires — `SPEC.md`, a
  `CHANGELOG.md` entry, installed hooks, local-only commits, a committed `STATUS.md`, and a working
  feature — were present and correct. Resolves the trigger-testing gap left open by skill-creator's
  broken harness with a real, working alternative signal. No defects found; nothing changed in the
  skill as a result. See `specs/dev-workflow-skill/STATUS.md`.

### Known issues
- skill-creator's automated description-trigger optimization pass (`run_loop.py`) doesn't work
  against this Claude Code CLI version — it registers the candidate skill as a slash command and
  waits for a `Skill`-tool call to detect triggering, but the model never invokes commands that
  way. Confirmed by manual replication (the model used `Bash` directly) and by 0% recall staying
  identical across three unrelated description rewordings. Stopped rather than tune against a
  broken signal; see `specs/dev-workflow-skill/STATUS.md`.
