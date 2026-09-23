---
name: dev-workflow
description: >
  Drives a disciplined, spec-first loop for building or changing software: restate the ask in
  plain terms, pin down the tech stack (recommend one with rationale if the project is new or
  unspecified), write an in-depth spec plus a changelog entry, research prior art before writing
  any code, implement, run a pre-commit quality gate on staged changes only (logic review, lint,
  secret scan, destructive-command scan), commit locally, verify locally against the spec
  (Playwright for anything with a browser surface, stack-appropriate tests otherwise), write a
  short status report of what's good/bad, checkpoint with the user on whether to iterate or push,
  and loop. Also installs tracked git hooks (pre-commit + pre-push, Gitleaks- and TruffleHog-backed
  with a pattern-based fallback) that block secrets, .env files, and destructive SQL/shell commands
  from ever being committed or pushed. Use this whenever the user asks to build, implement, fix, ship,
  or "properly" do a non-trivial piece of code — phrases like "spec this out", "set up the
  workflow", "add the safety hooks", "what stack should I use", or any multi-step feature/bugfix
  request — even when they never say the words "spec" or "workflow" out loud.
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

Add an entry under `Unreleased` in the repo's root `CHANGELOG.md` (create it from
`references/changelog-template.md` if it doesn't exist yet — Keep a Changelog format). Update both
files again at the end of the loop if scope shifted during implementation; the spec and changelog
should describe what actually got built, not just what was planned.

## Step 4 — Research before implementing

Before writing code, spend a short, bounded pass checking that the planned approach actually holds
up: search the codebase for existing patterns/utilities that already solve part of this (don't
duplicate), and, for anything non-trivial or unfamiliar, look at how it's commonly solved
elsewhere (library docs, GitHub search for similar implementations, known gotchas) — via
WebSearch/WebFetch or an Explore subagent for in-repo search. The goal is narrow: confirm the
spec's approach will actually produce the spec's output, and surface anything that would make you
redo work later (a deprecated API, a simpler built-in, a footgun). This is not a literature review
— stop once you're confident, not once you've read everything.

## Step 5 — Execute

Implement to the spec. Keep the diff scoped to what the spec describes; if you discover mid-build
that the spec needs to change, update `SPEC.md` rather than silently drifting from it.

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

## Step 9 — Status report + checkpoint

Write `specs/<task-slug>/STATUS.md` from `references/status-report-template.md`: what's working
and verified, what's broken or risky, and exactly what was tested (Step 8's actual results, not
its intentions). Give the user a short summary of the same, then ask directly: iterate further, or
push? Loop back to Step 3 for another pass on the same feedback, or run `git push` (the installed
pre-push hook is the last line of defense) once they say go.

## Reference files

| File | When to read it |
|---|---|
| `references/spec-template.md` | Writing `SPEC.md` in Step 3 |
| `references/changelog-template.md` | Writing/updating `CHANGELOG.md` in Step 3 |
| `references/status-report-template.md` | Writing `STATUS.md` in Step 9 |
| `references/tech-stack-guide.md` | Recommending a stack for a new/unspecified project in Step 2 |
| `references/constitution-template.md` | Creating or checking a target project's `CONSTITUTION.md` in Step 2 |
| `references/hooks.md` | Explaining what the git hooks block, tuning false positives, or troubleshooting a blocked commit/push |
| `references/model-effort-tiers.md` | Deciding which model/effort tier to use for a given phase, especially when orchestrating the loop as separate subagent calls |
| `references/roadmap.md` | Known limitations, deferred ideas, and notes from using this skill across other projects |

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/install-hooks.sh` | One-time per-repo: installs the tracked git hooks (Step 0) |
| `scripts/check_staged.py` | The actual secret/`.env`/destructive-command scanner; called both by the hooks and directly in Step 6 |
| `scripts/hooks/pre-commit`, `scripts/hooks/pre-push` | Thin wrappers `install-hooks.sh` copies into `.githooks/`; not meant to be run directly |
