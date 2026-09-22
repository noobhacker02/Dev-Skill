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
- Git hooks are a local, per-clone control — `core.hooksPath` isn't versioned, so a clone that
  never runs `install-hooks.sh` gets no protection. Documented, not solved (would need a
  server-side check to fully close, out of scope for a local dev-loop skill).
- Destructive-SQL/shell patterns are heuristics (e.g. "no `WHERE` on the same line" misses a
  multi-line statement) — deliberate scope limit, not a gap I missed.

## Test evidence

| Test plan item | Result |
|---|---|
| Hooks block secrets/.env/destructive commands, commit + push, TruffleHog present and absent | pass — see functional test log in this session; Stripe-only-detected secret confirmed the TruffleHog path specifically, not just the pattern fallback |
| Skill produces the intended end-to-end behavior (2 eval prompts, with-skill vs. baseline, 7 assertions each) | pass — 100% (7/7, 7/7) with skill vs. 43% (3/7, 3/7) baseline; benchmark.json/md and a static review viewer generated and sent to the user |
| Skill triggers appropriately (description-trigger optimization) | not run to a valid result — harness bug in skill-creator's run_eval.py for this Claude Code CLI version (see above); not blocking |

## Decision needed

Ready to push as-is. The one open item (trigger-tuning) is explicitly deferred, not silently
dropped — it needs either a fixed/updated skill-creator harness or real usage data, neither of
which is available right now.
