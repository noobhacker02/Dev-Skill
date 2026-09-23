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
- **skill-creator's automated description-trigger optimization pass doesn't work** against the
  Claude Code CLI version this was built against — it registers the candidate skill as a slash
  command but detects triggering via a `Skill`-tool call, which a model never spontaneously invokes
  for a command. Confirmed by manual replication (see `specs/dev-workflow-skill/STATUS.md`). Retry
  once a fixed version of that harness exists, or tune the description from real usage instead.

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
