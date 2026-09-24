# Status: dev-workflow skill

## Summary

Built and dogfooded the full `dev-workflow` skill (loop + safety hooks) on this repo. All
functional tests pass, including secrets caught by TruffleHog's own detector set beyond our
pattern checks. The skill-creator eval loop shows a clear, real effect: 100% pass rate on our
process assertions with the skill vs. 43% without, at roughly 7x the time and 2.3x the tokens —
the expected cost of the extra rigor, not a red flag. One tooling limitation was found and is
called out below rather than worked around. Ready to push.

## What's good

- Hooks block every category tested: AWS keys, private key blocks, a Stripe key (TruffleHog-only,
  not covered by our own patterns), `.env` files, `DROP TABLE`, `rm -rf /`, `git push --force`,
  `git reset --hard` — on both `pre-commit` (staged diff) and `pre-push` (commit range, including
  a secret smuggled past `--no-verify` and a first-push-of-a-new-branch scan against the empty
  tree). `--force-with-lease`, `.env.example`, clean commits, and `devskill:allow`-marked lines
  all correctly pass through. Verified with TruffleHog absent (pattern fallback) and present (real
  binary, installed and tested in this session).
- Dogfooding on this repo surfaced and fixed a real bug: the scanner flagged its own documentation
  for *naming* the destructive patterns it detects. Fixed at the root (destructive-pattern check
  now skips `.md`/`.mdx`/`.rst`/`.txt`; secret scanning still applies to docs) rather than
  allowlisted around.
- The eval loop (2 test cases, with-skill vs. baseline subagents, graded against 7 assertions
  each) shows the skill's actual value isn't code quality — baseline agents wrote solid code in
  both cases — it's the process artifacts baseline consistently skips: a spec written before
  coding, a changelog entry, a run quality gate, and a status-report checkpoint. Both with-skill
  runs also independently hit and correctly worked around the doc-file false positive using the
  documented `devskill:allow` escape hatch (not `--no-verify`), before I'd even fixed it upstream
  in one case — real evidence the documented escape hatch is discoverable and usable under
  pressure, not just in theory.
- The db-reset eval (existing Node/Knex/Postgres stack, inherently destructive task) is the
  strongest single result: the with-skill run built a four-layer guard plus an explicit
  confirmation flag, avoided raw destructive SQL entirely by using Knex's own migration rollback,
  and verified it against a real, self-started local Postgres instance — end to end, not just
  read-through. The baseline run used one guard condition and no spec/changelog/quality gate.

## What's bad / risks / open issues

- **skill-creator's automated description-trigger optimization pass doesn't work in this
  environment and I didn't route around it.** It registers the candidate skill as a
  `.claude/commands/*.md` file and then waits for a `Skill`-tool invocation to detect triggering —
  but a manual replication showed the model just uses `Bash` directly; `.claude/commands/` entries
  are user-typed slash commands, not something a model spontaneously invokes from natural-language
  intent the way an actual `.claude/skills/` entry is. Recall was 0% across three completely
  different description rewordings, which is what exposed this as a harness bug rather than a
  wording problem — a real signal would have varied. I stopped the loop rather than let it "tune"
  the description against a broken signal, and cleaned up ten stray leftover command files it left
  in `/root/.claude/commands/` from the killed run. The description in `SKILL.md` is un-tuned by
  this pass; it's the deliberately "pushy," explicit-trigger-phrase version from the initial draft.
  Real usage feedback is the right way to tune it, not this broken harness.
- Destructive-SQL/shell patterns are heuristics (e.g. "no `WHERE` on the same line" misses a
  multi-line statement) — deliberate scope limit, not a gap I missed.

## Stage 1 follow-up (Gitleaks, constitution, CI gate, roadmap)

- **Gitleaks** installed and functionally tested the same way TruffleHog was: catches a real
  (non-example) AWS-shaped key and a Slack webhook URL, correctly ignores AWS's own well-known
  documented example key, and a clean commit still passes with it active. Added as an additional
  layer, not a replacement for the pattern baseline — see `references/roadmap.md` for why.
- **`.github/workflows/security-gate.yml`** — the local-hooks-are-per-clone gap noted above is now
  closed for GitHub-hosted projects: CI re-runs `.githooks/check_staged.py` against every PR's
  diff. Before trusting it to a live run, simulated the exact same invocation locally with this
  PR's real base/head SHAs and confirmed it passes; genuinely verified once pushed by checking the
  Actions run on the live PR (not just "the YAML looks right").
- **Found and fixed a real gap while building the above**: `.githooks/` had been generated locally
  by `install-hooks.sh` during earlier dogfooding but never actually `git add`ed — this repo's own
  local hooks were silently unenforced for anyone who cloned it since. Caught because the CI
  simulation failed with "file not found" before it was staged; now tracked.
- **Constitution template** added as an optional file for target projects, not a required step —
  intentionally didn't adopt GitHub Spec Kit's full command set (see `references/roadmap.md` for
  the reasoning).

## Iteration 2: mock-project eval round on previously-untested paths

Three new with-skill scenarios, deliberately chosen to stress paths iteration 1 never touched:

- **Constitution respect** (existing repo with `CONSTITUTION.md`): read the file, quoted its exact
  rules, and followed every one — correct route file location/naming, correct `{ok, data}`
  response envelope (verified live via curl), zero new npm dependencies (confirmed by diffing
  `package.json`), no request-body logging. SPEC.md referenced the constitution instead of
  re-deriving its conventions. 7/7 assertions.
- **Playwright verification** (browser-facing form-validation task): correctly picked plain
  HTML/CSS/JS over a framework, citing `tech-stack-guide.md`'s own carve-out for genuinely tiny
  pages. Verified with real Playwright/Chromium — 23 real assertions covering both the
  invalid-email-blocks-submit path and the valid-submit-shows-success path, plus real screenshots
  taken and visually confirmed, not just read from source. 7/7 assertions.
- **Ambiguous intake** ("make the checkout thing better", zero context, empty workspace): correctly
  distinguished "one ambiguous detail in an otherwise clear ask" (proceed with a labeled default,
  the skill's normal path) from "the entire ask has no anchor" (this case) — built nothing, staged
  nothing, and explained exactly why proceeding would mean stacking three independent fabrications
  (domain, current state, success criteria). 5/5 assertions.

19/19 assertions passed across all three — no functional gaps found. One real but minor
inconsistency surfaced: two different runs (this round's constitution eval vs. iteration 1's runs)
disagreed on whether `STATUS.md` gets committed, because SKILL.md's Step 9 never said either way.
Fixed with a one-line wording addition to Step 9. Verified by inspection, not a full re-run — it's
a documentation clarity fix with no logic behind it to regress, and re-running a 10+ minute,
100k+-token subagent to confirm a sentence is unambiguous would cost far more than the fix's risk
warrants.

## Iteration 3: real trigger test via agent-loop, resolving the skill-creator harness gap

The trigger-optimization question left open above (skill-creator's `run_eval.py` is broken for this
CLI version) is now answered a different, better way: `agent-loop/test/validate-dev-workflow.mjs`
(a script in the companion agent-loop project) installs this skill as a real
`.claude/skills/dev-workflow/` in a fresh throwaway repo — the actual mechanism a user's install
would use, not a simulated one — and runs one real Agent SDK session with an ordinary feature
request that never says "spec" or "workflow": *"This app currently only has a /ping route. Add a
/health route that returns JSON with the server's status and how many seconds the process has been
running."*

Result: the `Skill` tool fired unprompted with `{"skill":"dev-workflow", ...}` — a real trigger,
not a simulated one — and every artifact the loop's steps require actually appeared and was
independently checked by the script (not just claimed by the session): `specs/health-route/SPEC.md`
with a proper restated-scope/requirements/deliverable, `.githooks/` installed with
`core.hooksPath` configured, a `CHANGELOG.md` entry, two local commits and zero push attempts, and
`specs/health-route/STATUS.md` committed rather than left as a handback note. The built `/health`
route was then run for real (not trusted from the transcript) and returned the correct JSON.

9/9 independent checks passed. This is a full, clean pass — no defects found in the skill this
run, so nothing was changed in `SKILL.md` or its scripts as a result. Recorded as-is rather than
inventing an improvement to justify the exercise: a validation pass with nothing to fix is itself
useful signal, especially given how thin the skill's real usage evidence was.

## Test evidence

| Test plan item | Result |
|---|---|
| Hooks block secrets/.env/destructive commands, commit + push, TruffleHog present and absent | pass — see functional test log in this session; Stripe-only-detected secret confirmed the TruffleHog path specifically, not just the pattern fallback |
| Skill produces the intended end-to-end behavior (2 eval prompts, with-skill vs. baseline, 7 assertions each) | pass — 100% (7/7, 7/7) with skill vs. 43% (3/7, 3/7) baseline; benchmark.json/md and a static review viewer generated and sent to the user |
| Skill triggers appropriately on a natural request (real signal, not skill-creator's broken harness) | pass — see "Iteration 3" below: real `.claude/skills/dev-workflow/` install + a genuine Agent SDK session, Skill tool invoked unprompted |
| Gitleaks catches secrets our patterns don't, ignores known examples, clean commit unaffected | pass — random AWS-shaped key and a Slack webhook both caught, AWS's documented example key correctly ignored, clean commit passed with gitleaks active |
| CI security gate runs the same check server-side as the local hooks | pass — simulated locally with this PR's real base/head SHAs before pushing; confirmed against the live PR's Actions run after |
| Skill respects an existing project CONSTITUTION.md rather than ignoring it | pass — 7/7 assertions, verified live |
| Skill uses Playwright for real browser verification on a UI-facing task | pass — 7/7 assertions, 23 real Playwright assertions, real screenshots |
| Skill handles a genuinely ambiguous, zero-context request responsibly | pass — 5/5 assertions, correctly stopped rather than fabricating a system |

## Decision needed

Ready to push as-is. The trigger-tuning question is now resolved with a real pass (Iteration 3) —
the description doesn't need tuning against this one data point alone, but is no longer flying
blind on triggering the way it was before. skill-creator's own harness bug (broken for this CLI
version) remains unfixed and undocumented-as-worked-around, which is fine: it's no longer blocking
anything now that a real, working alternative signal exists.
