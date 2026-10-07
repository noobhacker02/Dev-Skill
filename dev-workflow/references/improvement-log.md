# Improvement log: why each change to this skill was made, and how

The changelog says what changed. This says **why it was worth doing and how**, with the evidence before and the number after, so the
reasoning is readable later. Newest last. `tests/improvement_log_test.py` fails if an entry is missing a field, an id repeats, a suite it
names does not exist in `tests/bench_skill.py`, or "Measured" has neither a number nor "not measurable because ...".

The project-side log is `agent-loop/docs/IMPROVEMENTS.md` (ids `IMP-`). When one teaches the other, it is logged in both and each entry names
the other.

Template:

```
## SKILL-NNN · YYYY-MM-DD (or "backfilled") · Short title
- **Problem:** what was wrong, with evidence.
- **Why it matters:** the harm.
- **Change (how):** the mechanism and where.
- **Measured:** before -> after, or "not measurable because ...".
- **Cost / trade-off:** what it costs.
- **Suites:** benchmark suite ids it moves, or `none`.
- **Skill impact:** what changed in SKILL.md or a reference, or `none`.
- **Follow-ups:** what could still be improved, or `none`.
```

## SKILL-001 · backfilled · The staged-file scanner stopped missing the obvious spellings
- **Problem:** the first stress test (`docs/STRESS-TEST-REPORT.md`) staged 68 files with secrets, destructive commands and encodings; the
  scanner did the right thing on 22, and on 1 of 8 hook, push and CI cases. `git mv settings .env`, `.envrc`, a non-ASCII path, base64 and
  split forms all went through.
- **Why it matters:** the skill's promise is that secrets and destructive commands do not get committed; a scanner that only catches
  the textbook spelling gives false comfort.
- **Change (how):** rewrote the patterns and the file selection in `scripts/check_staged.py` (renames, quoted paths, `.envrc` and
  `*.env`), added a Gitleaks layer and a TruffleHog layer when installed, and made the pre-push hook scan the whole commit range.
- **Measured:** 22 of 68 -> 67 of 68 staged-file cases and 1 of 8 -> 6 of 8 hook/push/CI cases (the later figures are the harness's own
  output on 2026-10-02 at 4f96ec9; the one remaining staged-file miss is a secret split across a concatenation).
- **Cost / trade-off:** heuristics, not a parser, so new spellings slip; a 200,000-line staged file takes about 7.5 s to scan.
- **Suites:** scanner-stress, scanner-stress2
- **Skill impact:** Step 8 rules 1, 6 and 7 (construct the bypass; look for siblings; control run plus mutation).
- **Follow-ups:** three cases still fail in the harness: a secret split across a string concatenation, a pull request that replaces the scanner
  script with `exit(0)` and adds a key, and `git commit --no-verify` of an `.env` file (it leaves no record). The 200,000-line file also takes about 7.5 s.

## SKILL-002 · backfilled · SKILL.md shortened from 398 lines to 279 without dropping anything
- **Problem:** Step 8 had grown a long paragraph for every lesson; the file was about 4,800 words, which the stress report had named as
  the bloat that makes a skill get skimmed, on a skill whose own A/B showed no quality gain.
- **Why it matters:** a rule nobody reads does nothing; a long skill costs tokens on every use.
- **Change (how):** moved each lesson's long form word for word into `references/verification-lessons.md` and left a one-line rule in Step 8
  that points to it.
- **Measured:** 398 -> 279 lines (285 after three more rules were added later).
- **Cost / trade-off:** one more hop to read the reasoning behind a rule.
- **Suites:** skill-lines
- **Skill impact:** the Step 8 checklist format used by every later rule.
- **Follow-ups:** SKILL-005 and SKILL-006 added lines back; see their costs.

## SKILL-003 · 2026-10-02 · A benchmark scorer needs its own control
- **Problem:** the first agent-loop observability scorer reported 2 of 8; one pass was the word "blank" matching the probe's own URL path
  (`/blank`). Found only by reading the tool output behind the number. The real first baseline was 1 of 8.
- **Why it matters:** a baseline from a lenient scorer makes every later improvement look smaller, and a scorer that cannot fail cannot be
  trusted to pass.
- **Change (how):** probes use opaque paths; each check is exported and a control test feeds it silence (including the URL) and requires a
  miss, feeds it a real report and requires a hit, and proves the control itself catches a lenient scorer and a URL-matching one.
  Written up in `references/improvement-loop.md` (section 5) and Step 8 rule 8's reasoning.
- **Measured:** observability baseline 2 of 8 reported -> 1 of 8 true; 2 deliberately broken scorers caught by the control (agent-loop IMP-006).
- **Cost / trade-off:** every suite needs a small control test.
- **Suites:** none
- **Skill impact:** `references/improvement-loop.md` section 5; `references/benchmark.md` rule 2.
- **Follow-ups:** none

## SKILL-004 · 2026-10-02 · A handoff template, and an optional hook that keeps it from being lost to compaction
- **Problem:** a conversation was compacted once and the summary alone carried the requirements and decisions (agent-loop IMP-007).
- **Why it matters:** the user asked that nothing be forgotten across compaction.
- **Change (how):** `references/handoff-template.md` (ten sections, the user's requests verbatim); `scripts/handoff_hook.py` with three events
  (PreCompact warns when the handoff is stale, PostCompact saves the summary with secrets redacted, SessionStart re-injects the handoff),
  opt-in per project, never blocking, writing only inside the project; Step 9 gained a paragraph. Input and output shapes were read from the
  Agent SDK's type definitions; PreCompact has no documented way to block or inject.
- **Measured:** 3 events handled; `tests/handoff_hook_test.py` checks each with the documented payload shape and catches 2 mutants (redaction
  removed, project-boundary guard removed); 1 live firing observed (SessionStart on resume injected the handoff) and 0 for PreCompact/PostCompact, which stay unproven until a real compaction happens.
- **Cost / trade-off:** a committed hook config runs a script when a contributor trusts the repo's settings; SKILL.md +4 lines.
- **Suites:** hook-tests
- **Skill impact:** Step 9 paragraph; `references/handoff-template.md`; `scripts/handoff_hook.py`.
- **Follow-ups:** after the first compaction, confirm a file landed in the configured save directory.

## SKILL-005 · 2026-10-02 · The team of agents is sized to the task, not fixed at five
- **Problem:** the loop and agent-loop both assumed a fixed team of five. In agent-loop the code can only shrink it (skip one phase) and
  never add; a typo fix pays for five agents and a migration gets the same five; the job flow needs a pair per item.
- **Why it matters:** the fixed team cost about 17.6 times a plain session for a 2-point difference on one task (agent-loop IMP-003), and it
  gives risky changes no more scrutiny than trivial ones.
- **Change (how):** `references/team-composition.md`: principles (every agent pays for itself; a floor that is never cut; mandatory
  reviewers by signal; caps; serial by default; agents never hire agents; the checker never inherits the builder's reasoning; disjoint write
  scopes; role files not writable by agents), a role table mapped to Claude Code subagents, a sizing table from 1 to 12 agents, how to record
  the team in `SPEC.md`, how to change it mid-run, failure modes. SKILL.md gained a "Team size follows the task" section and a Step 3 line.
- **Measured:** not measurable because the sizing and cost comparisons are built in agent-loop S3a and S7 (suites `team-sizing`,
  `team-vs-fixed`); the only measured input is the 17.6 times figure. Cost on the skill side: SKILL.md 285 -> 319 lines across this and the
  next two entries.
- **Cost / trade-off:** longer SKILL.md (the benchmark row shows it as worse, on purpose); the floor of three agents may still be too many for
  a true one-liner.
- **Suites:** skill-lines
- **Skill impact:** SKILL.md section and Step 3 line; `references/team-composition.md`; spec-template Team section.
- **Follow-ups:** re-measure when `team-vs-fixed` has run; trim SKILL.md if the section is not used.

## SKILL-006 · 2026-10-02 · The adversary loop, the learning loop and "run the test twice" become part of the skill
- **Problem:** adversarial testing happened when someone remembered, in the same context that built the thing; and a new test written on
  2026-10-02 passed once, then failed on the next run because a deliberately broken mutant had left a file at a fixed path.
- **Why it matters:** an adversary that shares the builder's context shares its blind spots; a test that depends on what ran before it is
  worse than no test because it fails for the wrong reason later.
- **Change (how):** `references/improvement-loop.md` (a new agent every round, given spec and interfaces but not reasoning; reproduction
  required; fix test-first; stop rule; findings per round as a metric; the learning loop with proposals as data, a threshold, and learning
  only from what people and agents did, never from page text). Step 8 gained rule 21 (run a new test twice, and its mutant once) and rule 22
  (an adversary round with a new agent).
- **Measured:** the polluted test: 1 of 2 consecutive runs failed before unique paths, 0 of 2 after. Adversary findings per round: round 1
  pending at the time of writing (agent-loop spec and threat model), recorded in agent-loop `docs/adversary/round-01.md`.
- **Cost / trade-off:** a round costs one fresh agent session; two more rules in Step 8.
- **Suites:** none
- **Skill impact:** Step 8 rules 21 and 22; `references/improvement-loop.md`; `references/verification-lessons.md`.
- **Follow-ups:** fill in the round 1 count; decide whether rule 22 should be a hard step rather than a rule.

## SKILL-007 · 2026-10-02 · Lessons from adversary round 1: chains, links, baselines and buffers
- **Problem:** the first adversary round on agent-loop (a fresh-context agent) found a critical hole in a boundary the project's docs called tested (a
  server-side redirect reached a forbidden host), a symlink walk out of the project directory, a benchmark whose baseline could be lowered or whose one point
  was earned by accident, and, in my own S1 work, a bounded buffer that threw away its most informative entry. None of these was in the skill's rules.
- **Why it matters:** these are the failures a person following the skill would repeat: testing a boundary with a direct request, judging paths as text, trusting
  a baseline recorded from a lenient scorer, evicting oldest-first.
- **Change (how):** Step 8 rule 16 gained the eviction clause; new rules 23 (test boundaries with a decoy through redirects, popups, tunnels and the tool's own
  traffic; judge paths as the operating system resolves them) and 24 (a baseline is measured by scoring the old code with the corrected scorer, and a
  changed baseline needs a logged reason); long forms in `verification-lessons.md` sections 23 and 24.
- **Measured:** 1 critical, 6 high, 12 medium and 1 low confirmed finding in round 1 (agent-loop IMP-009 to IMP-011 fixed five in code); SKILL.md grew by
  7 lines for the three additions (312 to 319). The benchmark's skill-lines row shows this as worse, on purpose.
- **Cost / trade-off:** SKILL.md is longer again; two more rules to read.
- **Suites:** skill-lines
- **Skill impact:** Step 8 rules 16, 23, 24; `references/verification-lessons.md` sections 23 and 24.
- **Follow-ups:** trim Step 8 by merging rules that overlap (7, 8 and 12 all concern controls); consider a "boundaries" checklist reference if a third boundary bug appears.

## SKILL-008 · 2026-10-02 · Save before usage runs out, and keep a catalog of recoveries (user request)
- **Problem:** limits were hit or neared several times; a sub-agent died of one with nothing written, a background run was lost to a restart, and saving two repos by hand costs
  steps at the wrong moment. The skill said nothing about any of this.
- **Why it matters:** unsaved work is redone work, and the user asked twice that it not be.
- **Change (how):** Step 9 gained one sentence (save everything first, then continue); `references/improvement-loop.md` section 6 now covers usage and the catalog of recoveries and
  repeated mistakes; the project carries a one-command checkpoint script and `CLAUDE.md` rules (agent-loop IMP-012).
- **Measured:** SKILL.md +1 line (319 to 320); the checkpoint script has 6 checks with controls (agent-loop `test/checkpoint.mjs`). Not measurable: whether the rule is followed under pressure.
- **Cost / trade-off:** one more sentence to read in Step 9; a checkpoint commit may hold unfinished work (its message says so).
- **Suites:** skill-lines
- **Skill impact:** Step 9; `references/improvement-loop.md` section 6.
- **Follow-ups:** none until a limit event shows the rule failing.


## SKILL-009 · 2026-10-03 · A new test names what it assumes about the operating system, and a fixed pause becomes a wait (agent-loop IMP-013)
- **Problem:** after a long stretch of work on one machine, CI on all three systems was red. Each cause was something a test or a fix had silently assumed: `localhost` resolves to
  `127.0.0.1` first, `/` is a directory, files have LF endings, a call has started within 500 ms, a transition advances between two reads 120 ms apart.
- **Why it matters:** the failures were found by the user, not by the suite, and each red run costs a full cycle on three runners.
- **Change (how):** `references/verification-lessons.md` lesson 25; the project catalog (agent-loop `docs/SELF-HEALING.md`, part C) has the matching rows.
- **Measured:** not measurable as a number for the skill; the product-side evidence is agent-loop IMP-013 (which fixes were reproduced and which were only confirmed by CI).
- **Cost / trade-off:** one more lesson to read; a short list to write before a test is pushed.
- **Suites:** none
- **Skill impact:** lesson 25.
- **Follow-ups:** none until the lesson is shown to be ignored.

## SKILL-010 · 2026-10-03 · A reader that cannot see part of the thing must say so (agent-loop IMP-014)
- **Problem:** the page reader listed one field of four on a form with an iframe and a shadow root, and every check planned on top of it (a diff of the form against the facts, a job-id check, a hidden-text check)
  would have printed "no mismatch": a pass because nothing was inspected. A fresh-context adversary found it by running the reader, not by reading the design. Measuring the fix then showed a second blind spot (a field no
  person can see was offered as an ordinary one).
- **Why it matters:** a green check that never looked is worse than no check, and the person reading "no mismatch" cannot tell which kind they have.
- **Change (how):** `references/verification-lessons.md` lesson 26; the project catalog (agent-loop `docs/SELF-HEALING.md`) lists "form the reader cannot fully read" as a runtime recovery.
- **Measured:** not measurable as a number for the skill; the product-side evidence is agent-loop IMP-014 (`form-coverage` 1 of 8 to 8 of 8, 17 mutants killed).
- **Cost / trade-off:** one more lesson; an "unreadable" state to design for in every reader.
- **Suites:** none
- **Skill impact:** lesson 26.
- **Follow-ups:** none until a reader built under this lesson is shown to hide something again.

## SKILL-011 · 2026-10-03 · A filter test names the byte classes and the channels it covers (agent-loop IMP-015)
- **Problem:** the first "no control bytes reach the terminal" test for the new `team` command fed one class (C0, an escape sequence) into one channel (the text output) and passed. Run against a stricter version it
  failed twice: C1 control characters (U+0080 to U+009F, which some terminals act on) survived into the plan's `brief`, and a repository file NAME with control bytes reached `--json` through the signals' paths.
  A mutation of the JSON filter had survived the first test for the same reason.
- **Why it matters:** "no control byte reaches the terminal" is a claim about every path text can take, and a test that covers the easy path reads as proof for all of them.
- **Change (how):** `references/verification-lessons.md` lesson 27: list the byte classes (C0, C1, bidi, NUL) and the channels (text, JSON, file names, role or config files, error text) a filter test covers, feed each
  class through each channel, and filter both at the source and at the edge.
- **Measured:** not a number for the skill; product side agent-loop IMP-015: both gaps found by strengthening the test before any adversary saw the code, and the mutation of the JSON filter now dies.
- **Cost / trade-off:** a longer test; a second filter at the edge that is redundant while the source filter holds.
- **Suites:** none
- **Skill impact:** lesson 27.
- **Follow-ups:** the same matrix for the other places agent-loop prints untrusted text (the lineage and report renderers were checked in round 1; the browser's page-text channel is adversary finding A37).

## SKILL-012 · 2026-10-03 · The scanner's allow marker counts anywhere on the line (found committing agent-loop IMP-015)
- **Problem:** `check_staged.py` stored each finding's text as `content.strip()[:200]` and checked `devskill:allow` against that cut-down text, so a marker after column 200 was never seen. A long, legitimate regex
  line that names the destructive words it detects (`drop table`) stayed blocked with the marker on it; the only way through was to rewrite the code around the scanner or use `--no-verify`, which is not allowed.
- **Why it matters:** a block that cannot be answered by the documented escape hatch trains people to use the undocumented one.
- **Change (how):** findings keep the whole line; only the printed snippet is cut (with " ..."). `tests/stress/scan_stress2.py` cases: a long destructive line with no marker (still blocked), the same line with the marker after column 200 (allowed), a short line with the marker (allowed). agent-loop's `.githooks/check_staged.py` copy updated to match.
- **Measured:** `tests/stress/scan_stress2.py` 8 of 11 cases correct on the old scanner (the long-line case blocked) and 9 of 11 on the new one; its other cases are unchanged (it still reports its two documented holes, the `.githooks` self-replacement and `--no-verify`, which this change does not touch).
- **Cost / trade-off:** a finding now carries a whole line in memory (a 5 MB single-line file measured 5.7 s before and after); the printed snippet is unchanged.
- **Suites:** none
- **Skill impact:** the scanner only.
- **Follow-ups:** the two documented holes; agent-loop keeps a copy of the scanner in `.githooks/`, so every fix here has to be copied there (a drift check would catch a stale copy).


## SKILL-013 · 2026-10-07 · Judge what the tool will open or run, not what the text looks like (agent-loop IMP-016)
- **Problem:** the approval and path hooks of agent-loop judged text. Round 2 of the adversary ran the real hook chain and got commands that run programs or write files approved as read-only (`sed '1e CMD'`, `rg --pre`, `git remote set-url`,
  `sort -o`), a `~` read as a directory name, a relative link judged from the wrong directory, and brace expansion past the path check; it was the fourth time the same class had been found (symlinks in round 1).
- **Why it matters:** every gate that decides from the text of its input is bypassed by whatever the tool does with that text before it acts; for an unattended agent one approved line is enough.
- **Change (how):** `references/verification-lessons.md` lesson 28: resolve as the tool does, allow-list safe forms instead of names, treat shell-rewritten words as unjudgeable (ask), keep a table of every form beside the ordinary
  commands that must still pass, score the old gate first. The project catalog (agent-loop `docs/SELF-HEALING.md`, part C) counts the class at four.
- **Measured:** not measurable as a number for the skill; product side agent-loop IMP-016: `shell-readonly` 106 of 216 to 216 of 216 and `file-hooks` 65 of 242 to 242 of 242, baselines on the unmodified build.
- **Cost / trade-off:** one more lesson; a gate built this way asks more often (globs, braces, variables ask), which is the price of not guessing.
- **Suites:** none
- **Skill impact:** lesson 28.
- **Follow-ups:** the same table for any new gate (the LIVE-mode allowances list in S2 is the next one); expansion is judged, not performed, so a glob still asks.

## SKILL-014 · 2026-10-07 · A test for a failure that kills or hangs a process is measured on the old code many times and counts a timeout as a failure (agent-loop IMP-017)
- **Problem:** four slips in one round (lesson 29): a one-run "fails on the old code" for a race that fails one run in three, a crash detector that swallowed its own assertion and let the old build exit 0, a timed-out child scored as
  exit 0, and a "score the old build" run that imported the new `dist`.
- **Why it matters:** a regression test that fails on the old code only sometimes protects nothing and lets mutants survive by luck; a harness that reads a hang as a pass inflates a benchmark.
- **Change (how):** `references/verification-lessons.md` lesson 29; the project catalog has a row for each slip.
- **Measured:** product side agent-loop IMP-017: the popup scenario went from 1 failure in 3 old-build runs (three popups, one request each) to 5 in 6 (ten popups, eight requests each) and 6 in 6 (thirty), and the benchmark
  check `popup-storm-survives` scores 0 on the old build in every run since.
- **Cost / trade-off:** a harsher scenario costs a few seconds per run; a child process per scenario is slower than an in-process call.
- **Suites:** none
- **Skill impact:** lesson 29.
- **Follow-ups:** none until a test of this kind is shown to pass on the old code again.

## SKILL-015 · 2026-10-07 · The compaction-summary redactor matches key names with word characters around them, and credential headers (agent-loop adversary round 2, A34)
- **Problem:** `handoff_hook.py` redacted `(password|secret|api_key|token)` only with a `\b` in front, and `_` is a word character, so `GITHUB_TOKEN=...`, `DB_PASSWORD=...`, `client_secret`, `access_token`, `refresh_token`,
  `AWS_SECRET_ACCESS_KEY` were saved as they were; `Cookie:`, `Set-Cookie:`, `Authorization: Bearer ...` and JWTs had no pattern at all. 8 of the 10 spellings the adversary tried survived into a file that the checkpoint command commits
  to the agent-loop repository, which is public. Nothing real had leaked (the saved summaries were searched).
- **Why it matters:** a compaction summary is a model-written digest of a whole session, including anything pasted or printed; a leaked session token in a public git history cannot be unpublished.
- **Change (how):** `scripts/handoff_hook.py`: one pattern for a key name with anything word-like around it and its value (the trailing run is bounded to 40 characters so a long word cannot make the match slow), one for a credential
  header taken whole (a Cookie line holds several), one for `Bearer` values and one for JWTs. `tests/handoff_hook_test.py`: thirteen spellings built at run time (the adversary's ten plus a JSON key, `Set-Cookie`, a curl header and a JWT),
  four ordinary sentences that must stay (the token budget, passwords never logged, the api key rotation, authorization checked by the hook), a speed check on a 150,000-character word and 8,000 repetitions of `token`, and a third
  mutant (the word boundary put back in front of the key name).
- **Measured:** on the old script 11 of 13 spellings are saved unredacted; on the new one 0 of 13, with the four ordinary sentences intact; the third mutant is caught (3 of 3 mutants); the new redactor changes none of the three
  summaries already saved (no false positive on 75 KB of real summaries, and nothing found in them).
- **Cost / trade-off:** a few more words are redacted than strictly needed (`token: abcdef` in prose); a pattern set can always be missed by a spelling nobody tried.
- **Suites:** none
- **Skill impact:** `scripts/handoff_hook.py` only.
- **Follow-ups:** whether to keep committing the summaries at all (they live under `docs/handoff/compactions/` and `checkpoint` stages them) is the user's decision, recorded in agent-loop's HANDOFF; until then the newest summary stays out of commits.

## SKILL-016 · 2026-10-07 · The scanner's copies are checked against each other (found while fixing agent-loop adversary A32)
- **Problem:** this repository's own hook (`.githooks/check_staged.py`, which `core.hooksPath` runs here and the CI gate extracts from the base commit) was still the version from before SKILL-012: four findings cut at 200 characters before the
  allow-marker check and a printed snippet that was not cut. The fix reached the skill's copy and agent-loop's copy and not the one that guards this repository, and nothing noticed for four days; SKILL-012's own follow-up had named
  the risk ("a drift check would catch a stale copy").
- **Why it matters:** a safety fix that did not reach the copy that guards the place it was made for is a fix that does not protect it, and a stale scanner looks exactly like a working one.
- **Change (how):** `.githooks/check_staged.py` copied from `dev-workflow/scripts/check_staged.py`; `tests/scanner_copies_test.py` fails when the skill's, the repository hook's or (when checked out) agent-loop's copy differ, and shows it can by
  catching a one-byte change.
- **Measured:** 1 of 3 copies was stale before (the repository hook differed in 4 lines); the new test fails on it and passes on the synced copy; 3 of 3 identical now.
- **Cost / trade-off:** every scanner fix is now made in one place and copied twice; the test needs to be run (it is not wired into CI, which only runs the PR gate).
- **Suites:** none
- **Skill impact:** `.githooks/check_staged.py`; `tests/scanner_copies_test.py`.
- **Follow-ups:** wiring the test into the PR gate workflow; an install script that copies instead of a human.

## SKILL-017 · 2026-10-07 · A wait in a test is on a signal from the thing waited for, and a test that touches timing is run under load before it is called stable (found when the full suite failed on a test that passed alone)
- **Problem:** a browser test waited a fixed 2 s for a popup storm to finish, then asked the tools a question. Alone on an idle machine it passed every time; in the full suite, where other suites share the CPU, the storm was still running when the question came, the browser dropped
  the call, and the test failed (twice in one full run, once directly and once through the benchmark that re-measures it). The cause was found only because the full suite was run on the exact commit before pushing; the lesson that "it passed when I ran it" was about the wrong machine state.
- **Why it matters:** a flaky test teaches people to re-run until green, and a re-run is exactly the habit that hides a real defect (here the product passed the browser's own wording to the agent). Load is a normal condition for the thing under test, not an error in the test.
- **Change (how):** `dev-workflow/references/verification-lessons.md` lesson 30: wait on a signal from the thing waited for (a request the page makes when its work is over, an event, a file); when a test depends on timing at all, run it with four busy loops competing for the CPU
  and count failures in six runs before calling it stable; treat "passes alone, fails in the full suite" as load until shown otherwise; make the failure the product's problem too when an agent would meet it (retry a read, say plainly what happened for an action).
- **Measured:** one failing test and one failing benchmark check in one full run, both reproduced under load (4 of 6 runs failed on the old code, 0 of 8 idle), both gone with the signal-based wait (3 of 3 runs passed under the same load); see agent-loop IMP-019.
- **Cost / trade-off:** a signal-based wait takes as long as the work takes, so a slow machine makes the test slow instead of flaky.
- **Suites:** none
- **Skill impact:** `dev-workflow/references/verification-lessons.md` (lesson 30).
- **Follow-ups:** a "run under load" mode for the dev-workflow's own stress tests (none of them waits on a clock today, checked by search).
