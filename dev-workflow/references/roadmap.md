# Roadmap: known limitations, deferred ideas, cross-project notes

Living document. Update it whenever something is found not to work, considered and rejected, or
learned from using this skill in a different project — this is the one place that history lives,
instead of scattered across old STATUS.md files nobody re-reads. Keep entries short; this file
tracks decisions and status, not the reasoning essay behind each one (link to the relevant
`specs/<slug>/STATUS.md` for that if it's worth keeping).

## Known limitations (current)

- **Git hooks are local, per-clone.** `core.hooksPath` isn't versioned, so a clone that never runs
  `install-hooks.sh` gets no protection. The CI workflow (`.github/workflows/security-gate.yml`)
  closes this for GitHub-hosted projects by re-running the same check server-side on every PR; a
  project on another CI system needs an equivalent job added by hand (the check itself,
  `check_staged.py --mode=push`, is CI-agnostic — only the workflow file is GitHub-specific).
- **Destructive-SQL/shell detection is heuristic**, not a parser — e.g. "no `WHERE` on the same
  line" misses a multi-line statement. Deliberate scope limit: Gitleaks/TruffleHog and human review
  in Step 6 are the deeper layers, not the regexes. Not planned to change; a real SQL parser here
  would be a lot of complexity for a backstop check that already has two better-resourced layers
  behind it.
- **The security gate only ever sees staged text diffs, never binary content.** A leak baked into a
  committed image or video (a real absolute filesystem path visible in a UI screenshot, say) is
  invisible to `check_staged.py`'s secret/destructive-pattern scanning, which runs on `git diff`
  text output — a binary file's diff is just "Binary files differ," nothing to pattern-match. Found
  for real in agent-loop: a committed UI screenshot and its matching demo video both showed the
  sandbox's own internal directory structure through an app-level leak the scanner had no way to
  see (that project's `docs/LEAK-REVIEW-ui-video.md` has the full writeup). Not a `check_staged.py`
  defect to fix — a scanner reading text diffs can't reasonably decode arbitrary binary formats —
  but a real gap: a project that regularly commits screenshots or recordings of its own UI needs a
  human actually looking at what's rendered in them, since this gate won't. Reflected in Step 8's
  wording (verify what artifacts actually show, not just that they were generated) rather than a new
  script, since a format-specific scanner is a lot of machinery for a gap hit exactly once so far —
  revisit if it recurs.
- **skill-creator's automated description-trigger optimization pass doesn't work** against the
  Claude Code CLI version this was built against — it registers the candidate skill as a slash
  command but detects triggering via a `Skill`-tool call, which a model never spontaneously invokes
  for a command. Confirmed by manual replication (see `specs/dev-workflow-skill/STATUS.md`). Still
  unfixed, but no longer blocking anything: `agent-loop/test/validate-dev-workflow.mjs` gets the
  same signal a real, working way — install as a real `.claude/skills/dev-workflow/`, run one real
  Agent SDK session with a natural request, check whether the `Skill` tool actually fires. First
  real data point: it fired correctly, unprompted. One data point isn't enough to call triggering
  "solved," but it's the first genuine evidence either way, and the mechanism is cheap to re-run
  with different phrasing.

## Considered, not built

- **Full GitHub Spec Kit / OpenSpec adoption** (separate `constitution`/`specify`/`plan`/`tasks`/
  `clarify`/`analyze`/`checklist` commands) — rejected. Our 9-step loop covers the same ground
  without the extra multi-command machinery; adopting a whole second framework on top would be
  duplication, not improvement. Took the one piece worth it on its own: `CONSTITUTION.md`
  (`references/constitution-template.md`), as a lightweight, optional file rather than a new
  required step.
- **Gitleaks replacing our own hand-rolled secret patterns entirely** — rejected. Kept both: our
  small pattern list is the zero-dependency baseline (still blocks with nothing installed),
  Gitleaks and TruffleHog are additive deeper layers. Dropping our own patterns would mean zero
  protection in a repo where neither external tool is installed.

## Ideas not yet worth building

Things that came up but didn't clear the bar of "actually needed right now" — revisit if a real
task exposes the gap rather than building ahead of it:

- A task-decomposition step between Spec and Execute for genuinely large tasks (Spec Kit's
  `tasks` phase) — the current spec-template's requirements list has covered every task exercised
  so far; add this only once a spec is unwieldy enough that "implement the whole thing" stops being
  a reasonable unit of work.
- Non-GitHub CI templates (GitLab CI, CircleCI) for the security gate — add the first one when a
  project actually using this skill needs it, not speculatively.

## Notes from using this in other projects

Add an entry each time this skill (or its hooks standalone) gets used in a different repo —
what worked, what needed adjusting for that project's stack/CI, anything that should feed back
into the skill itself rather than staying a one-off local tweak.

<!-- Example entry shape:
### <project name/type> — <date>
- Stack: ...
- What needed adjusting: ...
- Worth pulling back into the skill? y/n — why
-->

### agent-loop (TypeScript/Node, Claude Agent SDK orchestrator) — first cross-project stack test

- Stack: TypeScript/Node, `node:sqlite`, `ws`, `playwright-core` — the hooks' first real exposure to
  a non-Python project.
- What needed adjusting: nothing in the hooks themselves. `install-hooks.sh` and `check_staged.py`
  worked unmodified. Ran a full simulated security-gate pass against the project's entire initial
  commit before trusting it live (same discipline as the CI-gate check on this repo) — clean pass,
  including on `src/hooks.ts`'s own `HARD_DENY_PATTERNS` array, which contains regex *source* like
  `rm\s+-rf\s+\/` as string literals. That text does not false-trigger the destructive-command
  scanner, because the scanner's own regexes require literal whitespace (`rm -rf /`), and `\s+` in
  source code is backslash-s-plus characters, not a space — different from the doc-file false
  positive found on this repo (Iteration: dogfooding, see `specs/dev-workflow-skill/STATUS.md`),
  where *prose* naming these same patterns in plain English did trigger it. Net finding: writing
  security-pattern *source* into a file is safe by construction in a way writing about it in docs
  is not; no change needed here, but worth knowing this isn't luck if it comes up again.
- Honest gap, not a hooks problem: the hooks were installed on agent-loop *after* several commits
  already existed, not from the first commit (Step 0 of the skill's own loop), because agent-loop
  was built quickly under an autonomous `/loop` session focused on getting a working pipeline
  verified end-to-end first. This is a real instance of the loop's own Step 0 being skipped in
  practice under time/task pressure, not a hooks defect — worth remembering that "install hooks
  first" needs to survive fast, exploratory starts, not just careful ones. No spec/changelog were
  written for agent-loop via `spec-template.md`/`changelog-template.md` either, for the same reason;
  its `STATUS.md` was written in the project's own voice instead. Not proposing a process change
  from this alone — one data point — but flagging it since "did we actually follow our own loop"
  is exactly what this section exists to catch honestly rather than paper over.
- Worth pulling back into the skill? Not yet — one clean cross-stack pass isn't enough signal to
  change anything, and the Step-0-skipped gap is about this session's pacing under `/loop`, not a
  defect in Step 0 itself. Revisit if a second, less rushed cross-project use shows the same gap.
- **A concrete example of Step 8's own point, from the same project**: agent-loop's Step-8-equivalent
  verification first used a WebSocket-only test (`test/plumbing.mjs`) that opened and immediately
  closed its own client socket. It passed clean. A *second*, real-browser test that left a
  connection open for the run's actual duration (`test/browser-approval.mjs`) then caught a genuine
  process-exit deadlock — `server.close()` never returning while a browser stayed connected — that
  the first test structurally could not have found, because it never left anything open long enough
  to expose it. This is the same failure shape Step 8 exists to catch in this skill's own loop:
  a check that matches the shape of what will actually happen in use finds bugs a narrower one
  passes right over. Reinforces Step 8 as written; no wording change needed, but a good concrete
  example worth keeping if Step 8 is ever revised, since "test the real usage shape, not just the
  wiring" is otherwise easy to nod at without a case that shows the cost of skipping it.

### agent-loop — extended adversarial-review round (cross-platform + git-hooks bug)

- What needed adjusting, and pulled straight back into the skill (not just noted here): the
  installed `pre-commit`/`pre-push` hooks only ever looked for a `python3` command on `PATH`. Many
  Windows Python installs (the standard python.org installer, in particular) only add `python`.
  Confirmed empirically: stripping `python3` from `PATH` and leaving only `python` made the old hook
  fail outright (`python3 not found`, exit 1). Fixed in `scripts/hooks/pre-commit`/`pre-push`
  themselves, not just agent-loop's installed copy: try `python3` then `python`, verifying whichever
  is found is actually Python 3 (not a stray Python 2) via a real version check before trusting it.
  A real fix to the skill's own bundled hooks, found by using them on a second project and actually
  auditing for a platform this skill had only ever been run on Linux/macOS for — exactly the loop
  this file exists to close.
- A leak class the quality gate structurally can't catch, found the same way Step 8's wording now
  calls out directly: doing an adversarial pass on agent-loop's UI/video artifacts (not prompted by
  `check_staged.py`, which never flagged it — the leak was in binary PNG/webm content, not a staged
  text diff) turned up a real absolute filesystem path baked into a committed screenshot and its
  matching demo video. See the new "known limitations" entry above.
- Worth pulling back further than the two changes above (the Python-detection fix, the Step 8
  wording)? Not yet on the binary-artifact gap specifically — a format-specific scanner is a lot of
  machinery for something hit once so far; revisit if it recurs on a project that commits screenshots
  routinely enough for that cost to make sense.
- The methodology that actually found all of the above, worth naming plainly since it's now backed
  by more than one project's worth of results: hypothesize a concrete, specific way something could
  fail (not "is this secure?" but "what happens if I strip python3 from PATH" or "what does this
  screenshot actually show pixel-for-pixel"), go verify it for real against the running code, fix
  what's confirmed, add a permanent regression test for it, then move to the next surface. Across
  this round alone that process found and closed: a supply-chain approval bypass (a "don't ask
  again" rule that didn't actually narrow to the approved package), a terminal escape-sequence
  injection hole (untrusted text reaching a real terminal unsanitized), a browser-session cleanup
  bug that could leak a Chromium process *and* leave a run stuck "running" forever in its own audit
  database, an auth check broken by `--port 0`, the local-path leak above, and the Windows
  git-hooks bug. None of these were found by reasoning about the code in the abstract; all of them
  required actually constructing the failing case and running it.

### agent-loop — a real CI failure, and two things pulled straight back into the skill

- **A CI run actually failed once**, on a commit whose own diff touched only UI markup/CSS/docs —
  nothing that could plausibly cause a server/WebSocket-timing failure. Confirmed that first (`git
  show --stat` on the blamed commit) before treating the test as the suspect. Root cause: a fixed
  `setTimeout(_, 200)` sleep followed by a single check of an asynchronously-populated buffer, racing
  a real WebSocket → server → event-bus → synchronous-SQLite-write → broadcast → client-receive
  round-trip. Tried to reproduce it 35 times locally (15 idle, 20 under artificial CPU saturation)
  and never could — this is exactly the "couldn't reproduce it locally ≠ safe to ignore" case now in
  Step 8: fixed the actual race (a poll-until-true helper, one case improved further to poll a
  server-emitted completion sentinel instead of guessing a duration) rather than either bumping the
  timeout number or shrugging at a run that "must have been a fluke," and confirmed the fix against a
  real subsequent CI run, not just local re-runs, before considering it closed.
- **The project's own stress-test harness had a real coverage hole**: its scripted fake SDK never
  emitted the message type that carries cost/usage data, so the entire stress suite — despite
  covering 10+ adversarial pipeline scenarios — had zero coverage of the actual cost-tracking
  emission code the whole time; only the UI's separate summing logic was ever exercised. Found by
  asking "does this fake actually simulate the real thing's full behavior," not by a test failing.
  Fixing it then immediately surfaced a second-order bug in the fix's own check (comparing against
  *attempted* calls instead of *completed* ones, misfiring on a call that throws before completing)
  and a third in that fix's shell idiom (`grep -c ... || echo 0` double-prints on a genuine
  zero-match file, because `grep -c` already writes "0" to stdout before its exit-1 status makes
  `||` fire) — each caught by testing the fix itself against a real input before trusting it, the
  same discipline applied one layer deeper than usual.
- **One dangerous capability, found in one syntactic form, was missing its sibling forms**: the
  Bash-approval analyzer already correctly refused to turn a `VAR=value cmd` prefix into a reusable
  "don't ask again" rule (an approved `NODE_OPTIONS=... npm test` shouldn't bless a differently-poisoned
  `npm test` later) — but the *standalone* forms of the identical risk (`export`, `set`, `declare`,
  `unset`, `alias`, `readonly` — which mutate the same persistent-shell state, just more durably
  across separate calls, not just for one line) weren't in the same exclusion list. Found by asking
  "what are all the ways to achieve this same effect," not by a new bug report.
- Pulled straight into `SKILL.md`'s Step 8 (not just recorded here): treat a non-reproducing CI
  failure as real until the blamed commit is cleared by its own diff; audit your own test
  fixtures/harnesses for behavior they never actually simulate; and when one form of a risk is
  handled, check for the other grammars of the same capability before calling it closed.

### agent-loop — computer-use Stage 1 (browser refs, coordinates, tabs) — 2026-09-30

- **The spec's own "verified facts" table missed a missing file.** The code cited
  `docs/BROWSER-AGENT.md` in several places and the spec said to update it, but the file had never
  existed. The table checked the code it described, not the files it cited.
- **A boundary everyone trusted leaked through the channels its mechanism doesn't see.**
  Request-level interception had been tested against links, redirects and fetches. Probing the
  channels the interception API is documented not to cover turned up two leaks: a page could open a
  WebSocket, and send WebRTC packets, to a forbidden host.
- **A mitigation named for exactly the problem didn't work.** Chromium's WebRTC IP-handling policy
  flag let the same packets through, even to a non-loopback address. Only removing the API in every
  page realm (checked across iframes, `data:`/`blob:` frames and popups) stopped them.
- **Zero is only evidence with a control.** The leak test first runs the same page in an undefended
  browser and requires the counters to see traffic, then requires zero with the defences on. Five
  mutations of the built code (one per defence) each fail it.
- Pulled into `SKILL.md`: Step 3 now says to check that cited files exist. Step 8 now says to probe a
  mechanism's documented blind spots, test the fix itself, and give every "nothing got through"
  result a control run and a mutation check.

### agent-loop: desktop computer use, Stages 3-6 (2026-09-30)

- **The plan was wrong about what the dependency was.** The spec said to spawn a driver and talk MCP over stdio.
  Reading and running the package showed an in-process native SDK with ~60 tools (clipboard, full-desktop
  capture, launch/kill app, hotkeys, config...). The fix was a design change, not a patch: a narrow interface of
  the project's own with only the methods it allows, an adapter over it, and a stand-in SDK with a trap on every
  other method. The controls live in code the model can't argue with; the driver only executes.
- **Two real defects came out of asking what a mechanism means when it fails.** A driver call that timed out
  was reported as an error but could still act later, past the approval and every fence; and nothing bounded
  what the native driver returned (about a gigabyte of disk over a session). Neither was found by reading the
  happy path.
- **A surviving mutation found a test that didn't test what it claimed.** The "a decoy holding focus gets no
  keystrokes" scenario passed with typing that named no window at all. The adversary had to steal focus between
  the click and the typing for the test to mean anything. A second survivor was redundant defence in depth,
  which is worth saying out loud rather than leaving as an unexplained gap.
- **Correct fail-closed behaviour looked like a flaky test.** The driver refuses to send input until the window
  manager is ready, which it is not for the first second of a run. Fixed by waiting for readiness, and by giving
  the fail-closed claim its own test in an environment built to trigger it.
- **Every threat got an exploit built from real processes**, with two apps logging everything they receive (the
  chosen target and an adversary that must end with nothing), so a refusal only counted if the adversary's log
  was empty too.
- Pulled into `SKILL.md`: Step 4 now says to read and run a dependency's real surface before designing around
  it. Step 8 now covers what to do with a surviving mutation, adversary-side assertions, timeouts on calls with
  side effects, and testing a dependency's fail-closed behaviour.

### agent-loop: real model in the loop, and a persona built properly (2026-09-30)

- **A fake that stands in for the decider can't surprise you.** The scripted SDK never emitted a tool call, so
  the assembled flow (real SDK, real hooks, real window) had never run. Two opt-in tests (a few cents on the
  cheapest model) did it once each and found one thing no scripted test could: told "no" to a click, the model
  asked for it eight more times. Fixed with a limit of three refused requests in a row, verified with the real
  model and by mutation. The same tests also showed a wrong assumption of mine (capture asks too), which
  was the test's bug, not the product's.
- **A request shipped at a fraction and described as done.** The ask was jokes with life in them, dark but not
  too dark, about how the tool is used, with bite that isn't toxic. What shipped was ten dry lines and a changelog
  entry calling "not genuinely dark" deliberate. Found only when the user asked whether it was done properly.
  The rebuild is a voice with rules that can be tested: it never reaches a model (import graph), carries no
  untrusted text (hostile input in every field, every note still exactly a catalog line), is never inside an
  approval (a real prompt checked), can be turned off, and can't break a run.
- **Taste needs guardrails you can assert.** "Is it funny" is for a person; "can it hurt anything" is a set of
  properties, each checked by trying to break it. Eighteen mutations, three survivors: a test that could never
  produce what it asserted was absent, one that looked for `[object` where the bug prints `Object`, and a
  defensive guard nothing exercised. Each survivor became a stronger test.
- Pulled into `SKILL.md`: Step 8 says to run the real decider once behind your fake. Step 9 requires an
  asked-vs-delivered table and forbids calling a scaled-back version deliberate without the user's agreement.

### agent-loop: judging the persona on realistic runs (2026-10-01)

- **Passing safety tests is not a working feature.** The persona had 24 checks and 18 caught mutations and had
  still never been seen on a run longer than a second. A deterministic simulator shaped from recorded numbers
  (6-minute typical run, 36-minute run with three vetoes, a speed-approver, a failure, a 2:40 a.m. start)
  showed the minimum-gap rule swallowed every agent's opening line and every Overseer veto, while the generic
  filler took the slots. No test could have found that; reading the replay did.
- **Fix the model, not the number.** Raising or lowering the gap would not have helped. The notes needed a
  priority (key vs seasoning), a template memory (no repeats in a run), and context (a line that says "everyone
  before me said yes" must not speak after three vetoes).
- **Mutation survivors came in three kinds again:** guards another check already makes redundant (deleted),
  a boundary no test pinned exactly (100th call versus 101st), and hostile numbers that never reached the code
  under test. Saying which kind each is was the useful part.
- Pulled into `SKILL.md`: Step 8 now says to run a human-experienced feature against realistic simulated data
  and assert the shape of what a person would see.

### agent-loop: the lineage view (2026-10-01)

- **A derived view is a second opinion on the data.** The lineage tree attributes a file only after the write
  succeeded. Next to it, the older "Files changed" panel listed a refused write to a `.env`, because it recorded
  the attempt. Nobody had noticed in months. Building the new view and comparing it with the old one found a bug
  in the old one.
- **Cross-check totals against the raw events, not against the view's own sums.** Node count, prompts, tool
  calls, repairs and cost are each compared with an independent count over the event stream on realistic runs. That
  flagged 10 against 11 attempts and led to the test simulator numbering a second attempt twice, which had also
  put "attempt 2" twice into the persona's screenshots.
- **Make the read-only choice on purpose and write it down.** The research said shared mutable logs between
  agents are where multi-agent systems get races, so the view is derived from events and nothing can write to it.
  It also does not commit to the user's repository on its own; that would be a decision for them.
- **Mutation survivors again named the untested paths** (an answer arriving during a retry, a reconnect clearing
  an old tree, the clock of an unfinished run): 46 breaks, all caught, three missing cases added.
- Pulled into `SKILL.md`: Step 8 now says to put a derived view beside the data it derives from, treat every
  disagreement as a bug, and cross-check totals against independent counts of the raw data.

### agent-loop: a redesigned UI with a cat, a dinosaur and sound (2026-10-01)

- **A negative test passes if the thing never happens.** "Replayed history makes no sound" emitted approval events the
  server never replays (it replays only an approval that is really waiting), and passed with the guard deleted. The
  mutation matrix surfaced it: 14 of 17 deliberate breaks were caught at first, and the three survivors were exactly the
  places where a precondition was missing or an assertion was too loose (a position checked only by which anchor was
  chosen, a nap checked by one of two code paths, the replay above). All 17 are caught now.
- **Measure what you would otherwise eyeball.** A mascot standing on a permission prompt looked right in a screenshot and
  was 12 px low: it had measured the prompt while it was still sliding in. An assertion on `getBoundingClientRect` with a
  2 px tolerance found it. A game's first jump was silently cancelled on the takeoff frame (height exactly 0 read as
  "landed"); a test that pressed Space and read the height found it. Look at the picture too: numbers cannot tell you an
  icon is the wrong drawing.
- **Labels in assets you did not make are claims.** Icon pairs matched by layer name paired a map with a telescope and a
  hammer with a gear. Pair by position, assert the pairing by content (mean colour) in the build step, and look at a sheet
  showing both.
- **Reading code for one feature found a bug in another.** `String.replace(str, replacementString)` expands `$'`, `$&`
  and `` $` ``; the saved-report writer embedded a run's text that way, so any shell command containing a dollar sign
  corrupted the whole report. Reproduced, fixed with a function replacer, regression test with all four patterns.
- **Say what is not known.** The cat and cursor sheets carry no artist or licence; the dinosaur and icon terms were not
  checked. The docs say so before they say anything about the art, and everything depending on it is optional and tested
  to fail soft.
