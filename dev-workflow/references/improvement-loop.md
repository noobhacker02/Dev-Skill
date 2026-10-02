# The improvement loop: adversary, learning, benchmark, log, handoff

One loop, five parts. Use it on any piece of work big enough that a mistake would be expensive. agent-loop implements it as commands
(`agent-loop adversary`, `agent-loop learn`) and as its own development process; this file is the version a person or a single session can follow.

```
 build test-first ─► write down what was done and what could be better ─► FRESH adversary agent ─► findings with repros
      ▲                                                                                              │
      │            benchmark updated, improvement logged (why + how) ◄── fix each one test-first ◄───┘
      └──────────── repeat with a NEW agent until a round finds nothing above "low" ─────────────────┘
```

## 1. The adversary: a new agent every round

- **Fresh context, every time.** A new subagent or session. Never the agent that built it, never the same one as last round.
- **Give it** the spec, the threat model, the public interfaces, read access to the repo, permission to run the tests and to write one report
  file. **Do not give it** your reasoning, your summary or the handoff document; it would inherit your blind spots. From round two, give it the
  *titles* of earlier findings so it hunts for new classes instead of re-finding old ones.
- **Make it prove things.** Every finding has an id, a severity, the exact place, and a **reproduction** (a command, a file and line, or a
  step-by-step scenario that ends in harm). No reproduction means *unconfirmed*, and it is not fixed on faith.
- **Ask for what is solid too:** "three things I tried and failed to break" tells you where the strength is.
- **Triage:** each confirmed finding becomes a failing test first, then a fix, then a log entry (why and how). Close it only when the test is
  green and has a control showing it can fail.
- **Stop rule:** a stage is closed when the latest round has no confirmed finding above *low*, or the round budget (default five) is spent, in
  which case the open findings go into the handoff by name.
- **Measure it:** confirmed findings per round. It should fall. If round four finds as much as round one, the fixes are not addressing
  causes, or the adversary is finding a different class each time (also useful, but say which).

## 2. Real-life and bad-case testing

After the unit-level work: run it the way it will be used, and run the bad cases on purpose. For agent-loop that is the fake job board with
its chaos switches (429, challenge page, session expiry, hostile text, a crash at every step). Record what happened, not what you expect.

## 3. The learning loop: what we do often becomes a process

Look at what repeats and turn it into something reusable, **with a person's yes**:

| Repeats | Becomes |
|---|---|
| The same question asked of the user | An answer saved with the question text |
| The same command approved again and again | A proposed rule (a loosening, so never activated automatically) |
| The same kind of task | A template, checklist or flow |
| The same failure text | A check or a warning |
| The same adversary finding class | A permanent test case |

Rules: a threshold (three times across two pieces of work), the evidence stored with the proposal, proposals are **data and never code**,
nothing activates without acceptance, and it learns from **what people and agents did**, never from the text of web pages or files read
along the way (that is how a hostile page would write itself into your playbook).

## 4. The improvement log (why and how)

Every improvement gets an entry in `references/improvement-log.md` (skill) or `docs/IMPROVEMENTS.md` (project): **Problem** with evidence,
**Why it matters**, **Change (how)**, **Measured** before and after (or "not measurable because ..."), **Cost / trade-off**, which benchmark
suites it moves, what the other project should learn, follow-ups. A test checks the fields. The point is that months later someone can read
"oh, we did this because of that, in this way, and it moved this number" instead of guessing from a diff.

## 5. The benchmark

A standing table of numbers with a **recorded baseline** that is never silently overwritten, generated from a results file and checked by a
test so a hand-typed claim cannot drift. The scorer must have its own control (feed it silence; it must say "not reported"), and a change to
what a suite counts is logged with the reason. State what the numbers do not show. See `references/benchmark.md`.

## 6. The handoff, before context is lost, and saving before usage runs out

If the work will outlive one context window (it almost always does), keep `docs/HANDOFF.md` current from `references/handoff-template.md`:
the standing instructions, the requests *in the user's words*, decisions, where everything is, status, the next step, what is verified and what
is not, the improvement backlog, gotchas, how to resume. Update it at the end of every stage and whenever the user adds a requirement. Optional
hooks (`scripts/handoff_hook.py`) save each compaction summary to disk and re-inject the handoff when a session starts; they are opt-in per
project and they can warn but not block.

**Usage nearly out is the same problem as compaction, faster.** When a limit is close, save before you move ahead: commit and push every repo involved (a one-command script is
worth having; agent-loop has `npm run checkpoint`), bring the handoff's "Next step" and "verified / not verified" up to date, and make sure anything in the background (a
test run, a sub-agent) writes to disk as it goes, because a sub-agent that dies of the limit leaves nothing otherwise. Say in the commit message what was not re-run; a
checkpoint is not a claim of green. Keep a catalog of recoveries and of mistakes made more than once (`agent-loop/docs/SELF-HEALING.md` is an example) and add a row the second
time anything fails.

