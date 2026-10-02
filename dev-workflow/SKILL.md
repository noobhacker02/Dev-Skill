---
name: dev-workflow
description: >
  Use this for ANY request to write or change code in a repository: adding a feature, route,
  endpoint, script, CLI, function or test; fixing a bug; refactoring; or starting a new project —
  including small, one-sentence asks like "add a /health endpoint", "fix the slugify bug" or
  "write a function that parses dates", and even when the user never mentions specs, tests or a
  workflow. Skip it only for questions that change no code, and one-line typo fixes. It runs a
  spec-first loop — restate the ask, pick the stack, write a short spec and changelog entry,
  implement, run a pre-commit safety gate (secrets, .env files, destructive commands), commit
  locally, verify for real (Playwright when there's a browser surface), report what's good and
  bad, and ask before pushing — and installs git hooks that block secrets and destructive
  commands from ever being committed or pushed.
compatibility: >
  Requires git and bash. The safety-check scripts require python3 (standard library only, no
  pip installs). Gitleaks (https://github.com/gitleaks/gitleaks) and TruffleHog
  (https://github.com/trufflesecurity/trufflehog) are used automatically when installed and the
  hooks fall back to pattern-based scanning when neither is. Playwright is used for local
  verification only when the project has a browser-facing surface.
---

# Dev Workflow

## Why this loop exists

Jumping straight to code is fast right up until the ask was misread, the wrong stack was picked,
a secret ends up in a commit, or "done" turns out to mean something different to the user than it
did to you. Each phase below exists to catch one specific failure mode, as cheaply as possible —
misunderstanding the ask (Intake), picking the wrong foundation (Tech stack), building the wrong
thing (Spec), reinventing a solved problem or missing a known gotcha (Research), shipping broken
or dangerous code (Quality gate), and shipping something nobody actually verified (Local
verification). The loop is not bureaucracy for its own sake — skip a phase only when its failure
mode genuinely cannot occur for the task at hand (e.g. a one-line typo fix doesn't need a spec).

The phases run once per unit of work (a feature, a fix, a task). Steps 3–9 repeat: after a status
report, the user decides whether to iterate again or push, and either answer feeds back into the
loop.

## Step 0 — One-time setup: install the safety hooks

Do this once per repository, the first time this skill is used in it (skip if `.githooks/` and
`core.hooksPath` are already configured):

```bash
bash <path-to-this-skill>/scripts/install-hooks.sh
```

This copies `check_staged.py` and the `pre-commit` / `pre-push` hooks into a tracked
`.githooks/` directory in the target repo and points `git config core.hooksPath` at it. Commit
`.githooks/` so it ships with the repo — but note `core.hooksPath` itself is a local git config,
not something version control carries, so each teammate's clone needs one run of
`install-hooks.sh` (mention this in the repo's README/CONTRIBUTING if you set it up for someone
else). From then on, every `git commit` and `git push` in that repo runs the checks in
`scripts/check_staged.py` automatically — see **Step 6** and **references/hooks.md** for exactly
what they block.

## Step 1 — Intake: restate the ask

Before touching anything, say back — in plain, non-jargon language — what you understood the user
to be asking for and what you're going to deliver. This is a one- or two-paragraph gut check, not
a document. If a detail that changes scope is genuinely unclear (not guessable from the repo or
convention), ask; otherwise state your interpretation and move on — restating and moving is itself
the checkpoint, it doesn't require waiting for a reply unless something is truly ambiguous.

**Before asking anything, check `DECISIONS.md` at the repo root (if it exists).** A question this
project already answered doesn't get asked again — that's what makes the log worth keeping. Only
ask a question that clears all three bars:

1. The answer would actually change what gets built or how — not just its phrasing or naming.
2. It isn't inferable from the repo, `CONSTITUTION.md`, or an existing `DECISIONS.md` entry.
3. It isn't already answered in `DECISIONS.md` from an earlier task in this project.

If more than one thing is genuinely unclear, ask all of it in one round, not one question at a
time — repeated back-and-forth for things that could've been asked together is what makes
questions feel like busywork rather than a real checkpoint. If nothing clears the bar, don't ask —
state your interpretation (per the paragraph above) and move on.

When a question does get asked and answered, or when you make a genuinely close call yourself
without asking (e.g. a tech-stack pick in Step 2), log it: create `DECISIONS.md` from
`references/decisions-log-template.md` if it doesn't exist yet, and append an entry (fork,
decision, who decided, why). Skip this for routine implementation choices a spec would normally
just make on its own — this log tracks real forks in the project's direction, not every detail.

## Step 2 — Tech stack

Look at the repo first. Lockfiles, config files, and existing source tell you the stack — use it,
don't relitigate it. If the repo is new or empty:

- If the user named a stack, use it.
- If they didn't, recommend one. Give a specific pick (framework/language/tooling), not a menu,
  with the one or two reasons it fits *this* task — then note the main alternative and why you
  didn't pick it. `references/tech-stack-guide.md` has starting recommendations by project shape
  (web frontend, backend API, CLI tool, data/ML, mobile). Ask via a real question only if the
  choice is genuinely close or the user is likely to care (e.g. it locks them into an ecosystem);
  otherwise recommend and proceed.

Check for a `CONSTITUTION.md` at the repo root — a project-wide set of conventions/non-negotiables
that this and every future spec should respect (see `references/constitution-template.md`). If one
exists, read it now so Step 3 doesn't re-derive decisions it already answers. If the project is new
and this is shaping up to be more than a one-off task, it's worth creating one from the template;
for a small existing repo or a single quick task, skip it — it's a tool for recurring drift across
many specs, not a mandatory file every project needs on day one.

## Step 3 — Spec + changelog

Write the spec to `specs/<task-slug>/SPEC.md` using `references/spec-template.md`. If a
`CONSTITUTION.md` exists, reference it for anything it already covers instead of restating those
decisions in the spec. It should be detailed enough that someone with zero conversation context
could implement from it and know when
they're done — that's the actual bar, not "is it long." At minimum it captures: the restated
request, in-scope vs out-of-scope, the chosen stack, requirements, exactly what the output/
deliverable is, and — critically — the test plan (what will be checked in Step 8 and how). Writing
the test plan now, before code exists, is what makes Step 8 more than a vibe check.

When the spec lists facts about the existing code, check that every file it cites actually exists,
not just the code it describes. Source comments can point at a design doc nobody ever wrote, and a
spec that says "update docs/X.md" inherits that gap.

Add an entry under `Unreleased` in the repo's root `CHANGELOG.md` (create it from
`references/changelog-template.md` if it doesn't exist yet — Keep a Changelog format). Update both
files again at the end of the loop if scope shifted during implementation; the spec and changelog
should describe what actually got built, not just what was planned.

If you will run this as several agents, add the **Team** section now (who, why, which slice; `references/team-composition.md`).

## Step 4 — Research before implementing

Before writing code, spend a short, bounded pass checking that the planned approach actually holds
up: search the codebase for existing patterns/utilities that already solve part of this (don't
duplicate), and, for anything non-trivial or unfamiliar, look at how it's commonly solved
elsewhere (library docs, GitHub search for similar implementations, known gotchas) — via
WebSearch/WebFetch or an Explore subagent for in-repo search. The goal is narrow: confirm the
spec's approach will actually produce the spec's output, and surface anything that would make you
redo work later (a deprecated API, a simpler built-in, a footgun). This is not a literature review
— stop once you're confident, not once you've read everything.

When the plan leans on a third-party package or service, read and run its real surface before designing
around it, not just its README or your memory of it. One plan assumed a driver was an MCP server to spawn; it
was an in-process native library with about sixty tools, most of which (clipboard, full-screen capture,
launch and kill app) must never be reachable. That changed the design: a narrow interface of your own
with only the methods you'll allow, so the rest isn't "forbidden" but absent, plus a test that puts a trap on
every other method of the real thing.

## Step 5 — Execute

Implement to the spec. Keep the diff scoped to what the spec describes; if you discover mid-build
that the spec needs to change, update `SPEC.md` rather than silently drifting from it.

If what you hit is a genuine fork the spec doesn't resolve — not "which variable name," but
something that changes behavior or scope — don't silently pick one and hope: stop and ask, the same
bar as Step 1 (would the answer change what gets built; is it not inferable from the repo,
`CONSTITUTION.md`, or `DECISIONS.md`). Log the resolution in `DECISIONS.md` either way — asked and
answered, or a close call you made yourself and are flagging so it's visible, not buried in a diff.
This is what Step 9's "Plan vs Actual" section then reports on.

## Step 6 — Quality gate (staged changes only)

Stage your changes, then run the bundled check against exactly what's staged — not the whole
working tree, so unrelated pre-existing issues don't block you:

```bash
python3 <path-to-this-skill>/scripts/check_staged.py --mode=commit
```

This scans staged diffs and filenames for secrets (API keys, private key material, AWS/GitHub/
Slack tokens, generic hardcoded credentials), `.env` files, and destructive SQL/shell patterns
(`DROP TABLE`, unguarded `DELETE`/`UPDATE`, `rm -rf /`, `git push --force`, `git reset --hard`,
etc.), and shells out to Gitleaks (fast, maintained ruleset) and TruffleHog (deeper, including
live-credential verification) for additional secret scanning when either is installed (if neither
is, the script says so and continues with the pattern checks — see **references/hooks.md** for the
false-positive escape hatches: inline `# devskill:allow` or a `.devskill-allowlist` file). Also
run the project's own linter/typechecker/test suite, and actually re-read your diff once for logic
bugs the tools won't catch — a clean lint run is not the same thing as correct.

Fix everything the gate finds before moving on. This step exists specifically so Step 7 never
commits something dangerous, whatever else happens later in the loop.

## Step 7 — Local commit

Commit locally with a message that references the spec/changelog entry. **Do not run `git push`
here** — nothing goes to the remote until the user signs off at Step 9. The installed pre-commit
hook re-runs the same checks as Step 6 as a backstop.

## Step 8 — Local verification

Stand the project up locally and actually exercise what you built, using `SPEC.md`'s test plan so
you're checking the things that matter for *this* task rather than guessing. Use Playwright for
anything with a browser-facing surface (the golden path plus the edge cases named in the spec);
use the stack's normal test tooling otherwise (unit/integration tests, CLI invocation, API
requests). If you can't actually run/observe something (no display, no way to hit a live
dependency), say so explicitly in the status report rather than claiming it was tested.

Rules for verifying, one line each. The reason and the real example behind every rule is in `references/verification-lessons.md`; read the
matching paragraph when your work touches that area.

1. **Security or trust (a gate, auth, a sandbox, a scanner):** construct the bypass and run it. "The suite passes" and "I traced the code" are
   not "I ran the attack and it failed". Look inside any artifact a person will see (screenshot, log, report, video) for a leaked path or token.
2. **A CI failure you cannot reproduce is a mechanism you have not found.** Read what the blamed commit touched, fix the race, confirm on CI.
3. **Your own fixtures and stubs are verified too.** When a fake stands in for the thing that decides (a model, a person, a network), run the
   real one once.
4. **Passing tests are not a working feature.** Use it as the person would, on data shaped like real data, and read what comes out.
5. **A view built from data shown elsewhere:** put the two side by side, treat every disagreement as a bug, and check totals against the raw data.
6. **A dangerous capability found in one form:** look for its siblings before calling it fixed. **A boundary resting on a library:** read what
   the library says it does not cover and probe that.
7. **"Nothing got through" needs a control run** (the same probe against an undefended setup must see the leak) **and a mutation check**; when a
   mutant survives, say whether the test was too loose or its precondition never happened.
8. **A test that asserts something did not happen must first prove it could have.** Assert the precondition, then the silence; give every
   "holds still" or "never appears" check a control that shows the thing happening when the feature is on.
9. **Measure what you would eyeball** (layout, position), **treat labels in data you did not make as claims**, and use a function replacer
   whenever `String.replace` embeds data.
10. **A control that stops X reaching Y:** give the test an adversary that records what it receives. **A timeout on a call with side effects is
    an unknown**, not a failure. **A fail-closed claim** is tested in an environment built to trigger it.
11. **Ask of any long-running tool how it stops, then send the signal and look.** Reproduce the bug on the previous commit before fixing it.
12. **A guard nothing exercises is a guard you do not have:** after a mutation run, call the layer beneath the UI directly, and assert that an
    injected stand-in actually answered.
13. **Timestamps across machines:** simulate the clocks disagreeing before trusting a "how long" figure.
14. **Measure what it costs** (CPU while idle, size, memory, time); passing tests will not show it.
15. **Run N copies at once against whatever they share, then break the shared thing on purpose.**
16. **A bounded buffer must say when it dropped something**, with an exact count; keep related items together and never trim what someone is
    still being asked about, and decide what goes by how informative it is, not how old (an oldest-first buffer threw away a message repeated 100
    times to keep 200 one-offs).
17. **"Is it useful?" is answered against the simplest baseline**, with the measured price of every delight feature, and every number in the docs
    checked against the code.
18. **"The suite passes" is a claim about the commit you ran it on.** After the last edit, including a "small" one that adds a field to an
    existing message, run the whole suite again before saying so, then read CI. **A green badge can lie**: a job allowed to fail reports
    success while suites inside it fail, so read the job's own list.
19. **"Portable" means it ran on the other systems**, and on a newer browser than yours. A first run on Windows and macOS found real bugs in
    code that "only uses cross-platform APIs": a route 404, a printed link that was not a URL, a flag that wants a URL and got a path.
20. **A scripted recording scripts every timestamp**, including the ones the system stamps itself; one real-clock event made a video's header
    read "1309m 48s". Watch the whole recording, or a frame every few seconds, before it goes in the README.
21. **Run a new test twice in a row, and its mutant once.** A test that writes to a fixed global path passed on the first run, and a
    deliberately broken mutant left a file there that made the next run of the *real* code fail. Use unique paths, clean up, and run it twice.
22. **For anything sizeable, run an adversary round with a new agent** in a fresh context that gets the spec and interfaces but not your
    reasoning, must give a reproduction for every finding, and is replaced by another new agent next round until a round finds nothing above
    low. Fix each finding test-first, log why and how, record findings per round (`references/improvement-loop.md`).
23. **A boundary enforced on the first request is not a boundary on a chain.** A route handler saw only the first URL, so a server-side redirect
    from an allowed page reached a forbidden host, and the docs called that boundary "already tested". Test with a decoy that records what reaches
    it, through redirects, popups, tunnels and the tool's own background traffic, and judge paths as the operating system resolves them (a symlink,
    `link/..`), never as text.
24. **A baseline is measured, not remembered.** One baseline point was earned by accident (the scorer matched the URL the tool always prints).
    Score the *old* code with the corrected scorer, record that, and make a changed baseline need a logged reason.

## Model & effort: don't spend the same tier everywhere

Steps 1–4 (Plan) are where a wrong call is most expensive and cheapest to prevent — use the
strongest model/highest effort available there. Step 5 (Execute) is usually the highest-token-
volume phase and, once the spec from Steps 1–4 is genuinely unambiguous, close to mechanical —
this is where a faster/cheaper model or lower effort pays off most. Steps 6, 8, and 9 (Recheck)
want medium effort in a *fresh* context rather than a continuation of Step 5's — a check that
shares the executor's context inherits its blind spots along with its reasoning. See
`references/model-effort-tiers.md` for the full reasoning, the circuit-breaker for when execution
hits an ambiguity the spec didn't resolve, and how to apply this whether the loop runs as separate
subagent calls per phase or as one continuous session.

## Team size follows the task

The loop names roles, not a headcount. If you orchestrate subagents, size the team to the task and write it in `SPEC.md` (a short **Team**
section: each member, why it is there, the slice it owns). Floor that is never cut for anything that writes or acts: a builder, then a verifier
that is a *different* agent in a *fresh* context, then a final gate. Add a role only for a named risk; add a security or migration reviewer when
the signals say so (auth, secrets, input parsing, shell/SQL, dependencies, schema); run steps one at a time; give parallel writers disjoint
paths or do not run them in parallel; agents never hire agents; more than four mid-run additions means re-plan. A one-file fix is three
agents, a typical feature five, several independent modules up to twelve; the numbers are guides, not targets. Details, the role table and the
failure list are in `references/team-composition.md`.

## Step 9 — Status report + checkpoint

Write `specs/<task-slug>/STATUS.md` from `references/status-report-template.md`: what's working
and verified, what's broken or risky, and exactly what was tested (Step 8's actual results, not
its intentions). It must include a **Plan vs Actual** section stating plainly whether execution
matched `SPEC.md` — "matched exactly" is a required sentence when true, not something you skip
because there's nothing to report; if it didn't match, say exactly where and why, pointing at the
`DECISIONS.md` entry if one was logged in Step 5.

It must also say **what was asked and what was delivered, line by line**, in a short table: each thing
the user actually said, and whether it exists, exists in part, or doesn't. Anything scaled back, deferred or
reinterpreted is named as such, with why. Never describe a smaller version as a deliberate design choice in a
changelog or README unless the user agreed to it: agent-loop's "jokes with life in them, dark but not too
dark, about how the tool is used" shipped as ten dry idle lines, recorded as "deliberately not dark", and was
only found when the user asked whether it had been done properly. The point is that a deviation gets surfaced by
name, not left for the user to notice by diffing the spec against the code themselves. Commit it —
a second small local commit is fine, run the quality gate on it same as any other (Step 6 is cheap
on a docs-only diff); STATUS.md is part of the task's record, not a disposable handback note, so
don't leave it sitting uncommitted. Give the user a short summary of the same, then ask directly:
iterate further, or push? Loop back to Step 3 for another pass on the same feedback, or run
`git push` (the installed pre-push hook is the last line of defense) once they say go — either way,
log which one they picked in `DECISIONS.md` if this project is tracking one.

If the work will outlive one context window, keep `docs/HANDOFF.md` current (`references/handoff-template.md`): requests in the user's own
words, decisions, where things are, next step, what is verified and what is not. Update it at every stage end and whenever a requirement is
added. **When usage is nearly out, save everything first** (commit and push every repo involved, handoff current, background work writing to disk) and only then continue. Log each improvement with its **why and how** and the number it moved (`references/improvement-log.md`, `references/benchmark.md`).

## Reference files

| File | When to read it |
|---|---|
| `references/spec-template.md` | Writing `SPEC.md` in Step 3 |
| `references/changelog-template.md` | Writing/updating `CHANGELOG.md` in Step 3 |
| `references/status-report-template.md` | Writing `STATUS.md` in Step 9 |
| `references/tech-stack-guide.md` | Recommending a stack for a new/unspecified project in Step 2 |
| `references/constitution-template.md` | Creating or checking a target project's `CONSTITUTION.md` in Step 2 |
| `references/decisions-log-template.md` | Creating or checking a target project's `DECISIONS.md` in Step 1/5/9 |
| `references/hooks.md` | Explaining what the git hooks block, tuning false positives, or troubleshooting a blocked commit/push |
| `references/model-effort-tiers.md` | Deciding which model/effort tier to use for a given phase, especially when orchestrating the loop as separate subagent calls |
| `references/verification-lessons.md` | The long form of each Step 8 rule: what went wrong, in which real project, how it was found |
| `references/roadmap.md` | Known limitations, deferred ideas, and notes from using this skill across other projects |
| `references/team-composition.md` | Sizing the team of agents to the task: roles, floor, mandatory reviewers, caps, how to change it mid-run |
| `references/improvement-loop.md` | The adversary (fresh agent each round), learning loop, benchmark, improvement log and handoff as one loop |
| `references/handoff-template.md` | Creating `docs/HANDOFF.md` so no context is lost to compaction |
| `references/improvement-log.md` | This skill's own log of each improvement: why, how, what it moved |
| `references/benchmark.md` | The skill's standing benchmark table and how to run it |

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/install-hooks.sh` | One-time per-repo: installs the tracked git hooks (Step 0) |
| `scripts/check_staged.py` | The actual secret/`.env`/destructive-command scanner; called both by the hooks and directly in Step 6 |
| `scripts/hooks/pre-commit`, `scripts/hooks/pre-push` | Thin wrappers `install-hooks.sh` copies into `.githooks/`; not meant to be run directly |
| `scripts/handoff_hook.py` | Optional Claude Code hook (PreCompact warns, PostCompact saves the summary, SessionStart re-injects the handoff); opt-in per project |
