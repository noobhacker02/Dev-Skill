# The skill's benchmark

A standing table with a recorded baseline, generated from `tests/bench-results.json` and `tests/bench-baseline.json`, and checked by
`tests/bench_skill_test.py` so a hand-typed number cannot drift. Why and how each movement happened is in `improvement-log.md` (last column).

```bash
python3 tests/bench_skill.py              # quick suites, a few seconds
python3 tests/bench_skill.py --full       # also the scanner stress harnesses (about 3 minutes)
python3 tests/bench_skill.py --write-doc  # regenerate the table below
```

## Rules

1. A baseline is the first value recorded for a suite and is not overwritten silently. A baseline taken from a broken scorer is removed and
   the removal is recorded under "Definition changes".
2. A scorer must be able to fail: feed it silence and require a miss (see `improvement-loop.md`, section 5).
3. State what the numbers do not show.
4. Lower is better for length rows. A length row going up is shown as worse even when the addition was worth it; the log entry says so.

## Results

<!-- bench:table:start -->
| Suite | What it measures | First recorded | Now | Change | Why / how |
|---|---|---|---|---|---|
| `skill-lines` | Length of SKILL.md (lines); shorter is better because long skills get skimmed | 285 @ 4f96ec9 | 319 | +34 (worse) | SKILL-002, SKILL-005, SKILL-007, SKILL-008 |
| `skill-words` | Length of SKILL.md (words) | 3318 @ 4f96ec9 | 3946 | +628 (worse) | - |
| `step8-rules` | One-line verification rules in Step 8 | 20 @ 4f96ec9 | 24 | +4 | - |
| `references` | Reference files shipped with the skill | 10 @ 4f96ec9 | 15 | +5 | - |
| `hook-tests` | Compaction-hook behaviours verified, including 2 mutants caught | 1/1 @ 4f96ec9 | 1/1 | no change | SKILL-004 |
| `scanner-stress` | Staged-file scanner: cases behaving correctly (secrets, destructive commands, encodings, allowlist abuse) | 67/68 @ 4f96ec9 | 67/68 | no change | SKILL-001 |
| `scanner-stress2` | Scanner: hook, push, CI and performance cases behaving correctly | 6/8 @ 4f96ec9 | 6/8 | no change | SKILL-001 |
Latest run: commit `4855163`, 2026-10-02. Baselines are the first value recorded for a suite and are not overwritten without a log entry.
<!-- bench:table:end -->

## Definition changes

| Date | Suite | Change | Why |
|---|---|---|---|
| 2026-10-02 | `references` | Baseline corrected from 13 to 10. | The first run happened after three new reference files had already been written; `git ls-tree 4f96ec9` shows 10 at the commit the other baselines describe. |
| 2026-10-02 | `hook-tests` | First recorded value (0 of 1) discarded and re-recorded as 1 of 1. | The test wrote to a fixed `/tmp` path and a mutant run polluted it, so the first benchmark run failed for the wrong reason. Fixed with unique paths (SKILL-006). |

## What these numbers do not show

- Whether the skill makes an agent produce better work. That needs real-model runs (agent-loop's `test/stress/ab_skill.mjs`, gated); an
  earlier A/B showed no quality gain, which is what motivated SKILL-002.
- Line and word counts say nothing about whether a rule is a good rule.
- The scanner suites are fixed cases; a new spelling is a new case.
