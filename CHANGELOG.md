# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- **A lesson from a reviewer's round on the upload hold: a test that passes against its own mutant has not tested the rule, and "cannot matter" is a claim** (`dev-workflow/references/verification-lessons.md` lesson 35, SKILL-022; found in agent-loop IMP-031). Build the counterexample before calling a mutant equivalent, print what the interception point sees before designing a fix for a channel, run every new rule's test against the old code and a mutant and read which assertion failed, and count only what your own process made in a shared directory.
- **A lesson from a file-upload tool: when the thing being checked can lie, check it twice, and the second time where it cannot reach** (SKILL-021, verification lesson 34). Asking a page where its form sends a file is advisory; repeat the check in a layer the page does not control (here, the network) and write the test from the liar's side, one hostile page per lie with a counter on the far side and an allowed control.
- **A lesson from a mutation check whose most useful survivor was a redundant clause** (SKILL-020, verification lesson 33). Give every survivor a verdict (a missing test, equivalent, unreachable here, or a defect); read the equivalent ones twice, because rewriting a redundant clause is where a path-containment bug showed (a directory named `..x` counted as outside its parent); make a cross-process race testable with a test-only hook; probe a library call before asserting what you believe it does.
- **A lesson from a repeated Windows-only failure: scan for it instead of remembering it** (SKILL-019, verification lesson 32). A path handed to a child process as `--import` fails on Windows and had been found four times after a push; the lesson is to write the scanning test the second time, check the scanner against snippets it must refuse and accept, and make a harness name a failed load instead of reporting "undefined".
- **A lesson from a mutation check that was green for the wrong reason** (SKILL-018, verification lesson 31). A run said 0 survivors of 30 while its test was failing on the unmutated code, so every mutant died of the same failure; an older kill had been vacuous because the copy lacked a directory the test reads. The lesson: run the unmutated copy first and stop if it fails, give the copy every directory the tests read, and treat a perfect first pass as something to check. Documentation only; the scripts in agent-loop now carry the control (IMP-021).
- **A lesson from a flaky test that was really load** (SKILL-017, verification lesson 30). A test that waited a fixed 2 s for a popup storm passed alone and failed in the full suite; the lesson is to wait on a signal from the thing waited for, and to run any timing-dependent test under four busy loops for six runs before calling it stable. Documentation only; the product fix is agent-loop IMP-019.
- **This repository's own scanner hook was four findings behind the skill's** (SKILL-016). `.githooks/check_staged.py` still cut each finding at 200 characters before looking for `devskill:allow`; the fix of SKILL-012 had reached the skill and
  agent-loop but not the hook that guards this repository. It is synced, and `tests/scanner_copies_test.py` fails when the copies differ (it failed on the stale one).
- **The compaction-summary redactor now catches `GITHUB_TOKEN`, `DB_PASSWORD`, `client_secret`, `access_token`, Cookie and Authorization lines, Bearer values and JWTs** (SKILL-015; agent-loop adversary round 2, A34). The pattern
  had a word boundary in front of the key name and `_` is a word character, so 8 of 10 ordinary spellings were saved as they were into a file the checkpoint command commits. Thirteen spellings now tested (11 survived on the old
  script, 0 on the new), four ordinary sentences stay, a speed check, and a third mutant. The three saved summaries are unchanged by it.
- **The scanner's `devskill:allow` marker now counts anywhere on the line.** `check_staged.py` checked the marker against the first 200 characters of the finding, so a long line with the marker at its end stayed
  blocked, and the only ways through were rewriting the code around the scanner or `--no-verify`. Findings keep the whole line; only the printed snippet is cut. Three new cases in `tests/stress/scan_stress2.py`
  (long line without the marker still blocked, with it allowed, short line allowed); the old scanner failed the second (SKILL-012). agent-loop's copy in `.githooks/` is updated to match.

### Added
- **Two more verification lessons from adversary round 2 of agent-loop** (`references/verification-lessons.md` 28 and 29; `references/improvement-log.md` SKILL-013 and SKILL-014). 28: a gate on what a tool is given must judge what the
  tool will open or run (resolve as the tool does, allow-list safe forms instead of names, treat words the shell rewrites as unjudgeable, keep a table of every form beside the ordinary commands that must still pass). 29: a test for a
  failure that kills or hangs a process is measured on the old code five or six times and made harsher until it fails every time, runs in a child process, counts a timeout as a failure and removes any detector listener
  before asserting; an old-build score is taken with a copy of the test inside the scratch worktree.
- **Save before usage runs out**: Step 9 now says to save everything first (commit and push every repo, handoff current, background work writing to disk), `references/improvement-loop.md` section 6 covers it with a catalog of recoveries and repeated mistakes, and `CLAUDE.md` carries the rule (SKILL-008).
- **Four new references, a team-size section, a handoff template and hook, an improvement log and a benchmark, from a long session of building and adversarially testing agent-loop.**
  `references/team-composition.md` (the number of agents depends on the task: principles, role table mapped to Claude Code subagents, a sizing table from 1 to 12, a
  floor that is never cut, mandatory reviewers by signal, caps, mid-run changes, failure modes), `references/improvement-loop.md` (a new adversary agent every round, the
  learning loop, the log, the benchmark, the handoff), `references/handoff-template.md` plus `scripts/handoff_hook.py` (PreCompact warns, PostCompact saves the summary
  with secrets redacted, SessionStart re-injects the handoff; SessionStart was seen firing live, the other two are tested only with the SDK's documented payloads),
  `references/improvement-log.md` (seven entries, each with why, how, the number it moved and the cost) and `references/benchmark.md` with `tests/bench_skill.py`.
  SKILL.md gained a "Team size follows the task" section, a Step 3 line, a Step 9 paragraph and Step 8 rules 21 to 24; it went from 285 to 319 lines, which the
  benchmark shows as worse and the log explains. Tests: `tests/handoff_hook_test.py` (2 mutants caught), `tests/improvement_log_test.py` (5 controls),
  `tests/bench_skill_test.py`.
- **Step 8 rules 23 and 24 and a decision about eviction** come from adversary round 1 on agent-loop: a boundary enforced on the first request is not a boundary on a
  chain (a server-side redirect reached a forbidden host while the docs said the boundary was tested); a baseline is measured by scoring the old code with the corrected
  scorer; and a bounded buffer decides what to drop by how informative it is, not how old.

### Changed
- **Step 8 carries three more lessons, from running agent-loop on macOS and Windows for the first time and remaking its README media.**
  "The suite passes" is a claim about the commit you ran it on (a server field was added, the full suite was not re-run, and a test
  that depended on the old behaviour went red on all three systems), and a green badge can lie when the job is allowed to fail;
  "portable" means it ran on the other systems and on a newer browser than yours (a route 404, a printed link that was not a URL, a flag
  that wants a URL and got a path); and a scripted recording scripts every timestamp, including the ones the system stamps itself (a
  video's header read "1309m 48s"). Long form in `references/verification-lessons.md`; `SKILL.md` is 285 lines.
- **`SKILL.md` is shorter: 398 lines to 279.** Step 8 had grown a long paragraph for every lesson learned (about 4,800 words in the file),
  which is the bloat an earlier stress report warned about, on a skill whose own A/B showed no quality gain. The long form of each lesson
  (what went wrong, in which real project, how it was found) moved word for word into `references/verification-lessons.md`; Step 8 now
  has a 17-rule, one-line-each checklist that points there. Nothing was dropped.
- **Step 8 carries four more lessons, from stress-testing agent-loop and asking whether it was useful.** Measure what a thing costs
  (a CPU reading found a paint-bound animation costing 4.2% of a core while a prompt waited, which 36 passing suites could not); run N
  copies at once against whatever they share, then break the shared thing on purpose; a bounded buffer must say when it has dropped
  something; and answer "is it useful?" against the simplest baseline, with the measured price of every delight feature, while checking
  each number in the docs against the code. Details in `references/roadmap.md`.
- **Step 8 carries three more lessons, from auditing agent-loop against three reference projects.** Ask how any long-running tool
  stops, then send the signal and look (agent-loop's Ctrl-C left the run "running" forever; reproduce on the previous commit before
  fixing). A guard nothing exercises is a guard you do not have: mutation survivors point at the layer beneath the UI, so call it
  directly, give every "it holds still" check a control proving there was something to sample, and assert that an injected stand-in
  actually answered. And compare timestamps across machines only after simulating the clocks disagreeing. Details in
  `references/roadmap.md`.
- **Step 8 carries four more lessons, from agent-loop\'s redesigned UI.** A test that asserts something did *not*
  happen passes trivially if the setup never made it possible, so assert the precondition first (a "replayed events are
  silent" test whose events were never replayed passed with the guard deleted). Measure layout and position instead of
  eyeballing them (a mascot 12 px off its prompt looked right). Treat labels in assets and data you did not make as claims
  to check by content (icons paired by name were different drawings). And use a function replacer, not a replacement
  string, whenever `String.replace` embeds data (`$'` corrupted a saved report). Details in `references/roadmap.md`.
- **Step 8 carries one more lesson, from agent-loop's lineage view.** When you build a view derived from data
  another part of the product already shows, put the two side by side and treat every disagreement as a bug in
  one of them (that is how a "Files changed" panel listing a refused `.env` write was found), and cross-check
  every total against an independent count of the raw data, not against the view's own arithmetic. Details in
  `references/roadmap.md`.
- **Step 8 carries one more lesson from agent-loop's persona.** A feature people experience (commentary,
  notifications, pacing, ordering) is not done when its safety tests pass: run it against deterministic data
  shaped like real runs and read what comes out. That found the persona's own gap rule swallowing every agent's
  voice and every veto, which no test had asserted. Details in `references/roadmap.md`.
- **Steps 8 and 9 carry two lessons from agent-loop's real-model tests and its persona.**
  - Step 8: when a fake stands in for the thing that decides (a model, a person, a network), run the real one
    through your real hooks once, on the cheapest tier, and assert only what the gates guarantee. That found a
    model asking for one refused action eight more times, which no scripted caller could.
  - Step 9: the status report must say what was asked and what was delivered, line by line, and must never call a
    scaled-back version a deliberate design choice unless the user agreed. Jokes that were asked for as dark,
    context-aware and everywhere shipped as ten dry idle lines, described as deliberate.

  Details in `references/roadmap.md`.
- **Steps 4 and 8 carry lessons from agent-loop's desktop computer use (Stages 3-6).**
  - Step 4: read and run a third-party dependency's real surface before designing around it. A plan that
    assumed an MCP server was really an in-process library with ~60 tools, which changed the design to a
    narrow interface of the project's own.
  - Step 8: when a mutation survives, say whether the test was weak or the defence redundant; give a
    containment test an adversary that records what it receives, and assert on that too; treat a timeout on a
    call with side effects as "may have happened", not as a failure; and test a dependency's fail-closed
    behaviour in an environment built to trigger it.

  Details in `references/roadmap.md`.
- **Step 3 and Step 8 carry lessons from agent-loop's computer-use Stage 1.**
  - Step 3: check that every file a spec cites actually exists. agent-loop's code cited a design doc
    that was never written, and the spec inherited the gap.
  - Step 8: probe what a boundary's underlying mechanism is documented not to cover. That turned up
    real WebSocket and WebRTC escapes past a request-interception sandbox.
  - Step 8: test the mitigation itself. A browser flag named for the WebRTC problem didn't stop it.
  - Step 8: a "nothing got through" result needs a control run that proves the detector sees the
    leak, plus a mutation check that removing each defence fails the test.

  Details in `references/roadmap.md`.

### Fixed
- **`pre-commit`/`pre-push` only ever looked for a `python3` command.** Many Windows Python installs
  only add `python`, not `python3`, to `PATH`. Confirmed empirically: stripping `python3` from `PATH`
  and leaving only `python` made the old hook fail outright (`python3 not found`, exit 1); the fixed
  hook tries `python3` then `python`, verifying whichever it finds is actually Python 3 (not a stray
  Python 2) before trusting it, and succeeds in the same scenario. Found while auditing agent-loop
  (which installs these same hooks) for Linux/macOS/Windows portability.
- **The skill now triggers on ordinary coding requests.** Its description led with process detail
  and only mentioned when to use it at the end. On 8 everyday requests the real model invoked it only
  3–4 times ("add pagination to /users", "fix the January date bug", "write unit tests for the cart
  total" were all missed). The description now opens with when to use it. On a held-out set of 8
  coding requests plus 2 plain questions, run against the real model, it triggered 8/8 (was 3/8)
  with 0/2 false triggers. Rerun with `node test/stress/skill-trigger.mjs` in agent-loop.

### Changed
- **Step 8 (Local verification) now says explicitly what "verified" means for security- or
  trust-relevant work**: construct the specific bypass you're worried about and actually run it,
  rather than reasoning about whether it should hold — and, for anything that produces artifacts a
  person looks at later (a screenshot, an exported log, a recording), check what's actually visible
  in them before committing, since this skill's own Step 6 gate only ever sees staged *text* diffs
  and can't catch a leak baked into binary content. Backed by a real second cross-project round of
  using this skill's hooks (`references/roadmap.md`'s new "extended adversarial-review round" entry):
  the exact methodology now named in Step 8 is what found a supply-chain approval bypass, a terminal
  escape-injection hole, a browser-session cleanup bug, a `--port 0` auth break, a local-path leak
  through a committed screenshot, and a Windows-specific bug in this skill's own git hooks (see
  "Fixed" above) — none of them found by reading the code alone.
- **`references/roadmap.md`** gained a "known limitations" entry for the binary-artifact gap above,
  and the new dated notes entry with the full round's findings.
- **Step 8 gained three more lessons from a further round of using this skill's own hooks on
  agent-loop**, each pulled straight into the step's wording, not just recorded in the roadmap: (1)
  a CI failure that doesn't reproduce locally is not evidence it's safe to ignore — check whether the
  blamed commit's own diff could plausibly have caused it before treating the test as the suspect,
  then fix the real mechanism (a fixed-sleep-then-check-once race, in the case that prompted this)
  and confirm against real CI, not just local re-runs; (2) your own test fixtures and harnesses are
  part of what Step 8 verifies — a fake that never exercises a whole class of real behavior (a
  scripted stand-in for a real API that never sent the message type carrying cost data, in this
  case) leaves a blind spot nobody notices until something downstream breaks; (3) when one syntactic
  form of a dangerous capability is found and fixed, check for the other grammars of the identical
  underlying risk before calling it closed (an approval analyzer that correctly refused to
  rule-ify `VAR=value cmd` but missed the standalone `export`/`set`/`declare` forms of the same
  persistent-state mutation). Full detail and the two follow-on bugs the fix for (1) caught in
  itself before it could be trusted: `references/roadmap.md`'s new dated entry.

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
