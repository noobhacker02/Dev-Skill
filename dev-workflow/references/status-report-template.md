# Status: <task name>

> Written in Step 9, after local verification actually ran. This is the file (and the short
> summary drawn from it) that the user sees at the loop's checkpoint before deciding whether to
> iterate again or push.

## Summary

Two or three sentences: what was built, and the one-line verdict (ready to push / needs another
pass / blocked on X).

## Plan vs Actual

Did execution match `SPEC.md`? If yes, say so plainly ("matched exactly, no deviations") — this is
a required line, not something to skip because there's nothing to report. If not, state exactly
where and why, pointing at the relevant `DECISIONS.md` entry if the fork was resolved by asking or
by a documented judgment call during Step 5. The point of this section is that a deviation gets
named here, not left for the reader to discover by diffing the spec against the code.

## What's good

What was verified working, and how (point at the specific test-plan row from `SPEC.md` it
satisfies). Only list something here if it was actually run/observed this loop — not "should
work."

- ...

## What's bad / risks / open issues

Anything broken, untested, uncertain, or deliberately deferred. Be specific about severity —
"blocks push" vs. "worth knowing about but not blocking."

- ...

## Test evidence

What was actually executed in Step 8 and its result — command run, test suite output, Playwright
scenario and outcome, or "not run: <reason>" if something in the test plan couldn't be exercised
(no display, no access to a dependency, etc.). Don't claim something was tested if it wasn't.

| Test plan item | Result |
|---|---|
| ... | pass / fail / not run — why |

## Decision needed

State the two options plainly: iterate on the issues above, or push as-is. If there's a specific
reason to lean one way (e.g. an open issue is cosmetic and low-risk), say so — but the call is the
user's.
