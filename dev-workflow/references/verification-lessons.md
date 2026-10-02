# Verification lessons: the why and the real example behind each Step 8 rule

SKILL.md carries the one-line version of each rule. This file keeps the long form: what went wrong, in which real project, and how it was
found. Read the paragraph that matches what you are verifying; there is no need to read the whole file for a one-line change.

For anything security- or trust-relevant (an approval/permission gate, an auth check, a sandbox
boundary, a scanner or validator, "don't ask again" style rules), verification means more than
confirming the happy path: construct the specific bypass you're worried about and actually run it,
the way an attacker or a careless caller would, rather than reasoning about whether it should hold.
"The test suite passes" and "I traced the code and it looks safe" are not the same claim as "I ran
the bypass and it failed" — only the last one is verification (this is how a real multi-agent
orchestrator's supply-chain-approval bypass, terminal-escape-injection hole, and a leaked local
filesystem path were actually found — reasoning about the code alone had already missed all three).
If the task produces artifacts a person will look at later — a screenshot, an exported log, a saved
report, a recorded video — check what's actually visible in them before committing, not just that
they were generated: a local path, a token, or other output can leak through a rendered artifact in
a way no text-based scan (including this skill's own Step 6 gate, which only ever sees staged *text*
diffs — a binary file's diff is just "Binary files differ") will ever catch.

A CI failure that doesn't reproduce locally is not evidence it's safe to ignore. Before calling
anything a flake, check whether the commit CI blamed could plausibly have caused it at all (read its
actual diff) — if it touched none of the failing code's dependencies, the test itself is the
suspect, not the commit. Trace the failure to a real mechanism (a fixed `sleep`-then-check-once
racing a genuine multi-hop round-trip is a common one) and fix that mechanism, even when dozens of
local re-runs — including under deliberately added CPU load — won't reproduce it; "couldn't
reproduce it" and "it's fine" are different claims, and only a fix to the actual race closes the gap.
Confirm the fix against the real CI environment once pushed, not just locally — a race that depends
on machine load won't necessarily show up the same way on your own machine.

Your own test fixtures and harnesses are part of what Step 8 verifies, not exempt from it. A stub or
fake that never exercises a whole class of real behavior (a scripted fake API client that never sends
the message type carrying cost data, say) means every test built on it has a blind spot nobody
notices until something downstream breaks — audit what a fake actually simulates against what the
real thing does, the same way you'd audit application code for a missed case.

When the fake stands in for the thing that *decides* (a model, a person, a network), run the real one through
your real hooks at least once, on the cheapest tier. A scripted caller can't surprise you. agent-loop's scripted
SDK never emitted a tool call, so nothing had shown what a model does with the gates: the first real run
showed one refused click being asked for eight more times, each a fresh prompt for a person to read. Assert
only what the gates guarantee whatever the model chooses, and print what it chose.

Tests that pass are not the same as a feature that works for the person using it. Before calling a feature
that people experience (commentary, notifications, a dashboard, any pacing or ordering) done, run it against
data shaped like the real thing and read what comes out. agent-loop's persona passed 24 safety checks and had
never been seen on a run longer than a second; replaying realistic runs showed its own gap rule swallowed every
agent's voice and every veto, the feature's whole point. Build the simulator from numbers you recorded, make
it deterministic, and assert the shape of what a person would see (nothing silent, nothing a flood, nothing
repeated, the key moments present), not the wording.

When you build a view derived from data another part of the product already shows, put the two side by side and
treat every disagreement as a bug in one of them. agent-loop's lineage tree credits a file only after the write
succeeded; its older "Files changed" panel recorded the attempt, so it listed a write the human had refused, even to
a `.env`. And cross-check every total the new view reports against an independent count of the raw data (never
only against its own arithmetic): that comparison caught a lying test simulator (10 attempts against 11 in the
events) the same way.

When a dangerous capability is found in one syntactic form, check for the others before calling it
fixed. A shell command that redirects behavior via `VAR=value cmd` and one that does the identical
thing via a bare `export VAR=value` are the same underlying risk in two different grammars — finding
and fixing only the first form because it's the one you happened to test leaves the second wide open.

When a boundary rests on a library mechanism, read what that mechanism is documented *not* to cover
and probe each gap. A browser sandbox enforced by request interception had held against links,
redirects and background fetches. It still let a page open a WebSocket and send WebRTC packets to a
forbidden host, because the interception API never sees either one; its own docs said so. Test the
fix the same way. A browser flag named for exactly this problem (Chromium's WebRTC IP-handling
policy) sent the same packets through; only removing the API in every page realm stopped them.

A "nothing got through" result needs two companions before it counts:

- **A control run.** Point the same probe at an undefended setup and confirm the detector sees the
  leak. Otherwise zero might only mean the environment can't observe it (a loopback alias the OS
  doesn't route, say). When the control can't observe it either, report the check as skipped, not
  passed.
- **A mutation check.** Break each defence in the built output, one at a time, and confirm the test
  fails. A test that still passes with the defence removed was never testing it.

When a mutation survives, say which of two things it is, and don't move on until you have: the test wasn't
testing what it claimed (strengthen it), or the defence is redundant and nothing can observe it (say so).
One test claimed "typing always names the target window" and passed with the window name removed, because the
target happened to still have focus; making an adversary steal focus *between* the two steps is what made it
mean something.

A test that asserts something *didn't* happen ("silent while replaying", "never reads outside the folder", "no network
request") passes trivially if the setup never made it possible. First assert the precondition happened, then assert the
silence. agent-loop's "replayed history makes no sound" test emitted approval events that the server never replays (it
replays only an approval that is really waiting), so it passed with the guard deleted; the mutation check surfaced it.
The fix was to create a real pending approval, assert that the page got it back on reconnect, and only then assert it
made no sound.

Measure what you would otherwise eyeball. A screenshot of a mascot standing on a permission prompt looked right and was
12 px low, because it had measured the prompt mid-slide-in; a test comparing `getBoundingClientRect` against the prompt's
edge, with a 2 px tolerance, found it, and the same assertion later killed a mutation that a pose-only check could not.
Layout, position and "does not cover the button" are numbers: assert them. Then still look at the picture, because
numbers will not tell you the icon is the wrong drawing.

Labels inside assets and data you did not make are claims to check, not facts. A sprite sheet's layer names paired each
12 px icon with the 17 px icon of the same name; side by side, a map was paired with a telescope and a hammer with a gear.
Pair by something the labels cannot get wrong (position in the grid), check the pairing by content in the build step (here,
mean colour), and look at a sheet that shows both. Likewise, `String.replace(str, replacementString)` expands `$'`, `$&`
and `` $` `` inside the replacement: embedding a run's text into an HTML file that way corrupted any shell command
containing a dollar sign. Use a function replacer whenever the replacement is data.

For a control that stops something reaching something else, give the test an adversary that records
everything it receives, and assert on the adversary's record as well as on the refusal. A refusal that
still delivers the input passes the first check alone.

A timeout on a call with side effects is not a failure, it's an unknown: the call can complete later, after
every check you made has stopped meaning anything. Treat a timed-out action as "may have happened" and stop
sending, rather than reporting an error and carrying on. A timeout on a read is just an error. A timeout in a *probe* is an unknown, never "absent": a doctor command ran `which`/`where` with a 3-second limit and read a timeout as "not
installed", so a loaded Windows runner made it say node was missing (7 of 20 lookups with a 1 ms limit gave the same false answer here). Search
PATH directly, or report "could not tell"; and test it with a PATH that holds only the thing you are looking for, where a subprocess-based probe
cannot even start.

Fail-closed behaviour of something you depend on is a claim like any other. Check it in an environment built to
trigger it (no window manager, so the driver can't focus anything), and make the normal tests wait for the
dependency to be ready rather than racing it: a correct refusal during startup looks exactly like a flaky test.

Ask of any long-running tool: how does it stop? Then send the signal and look. agent-loop had no stop path at all: Ctrl-C
killed the process, the audit database kept saying the run was "running" for good, no report was written, and a model call
aborted while an approval waited left that approval open for the next tab. Nobody had tried it, because a test run always
ends by itself. Reproduce the bug on the previous commit (a throwaway worktree is enough) before fixing it, so the claim in
the changelog is measured; test the fix with a real signal against a real process, and, if the model was stood in for,
once with the real one (the stand-in only proves what you wrote it to prove).

A guard nothing exercises is a guard you do not have. When a feature has a layer underneath the one a person sees (the
script refuses what the button already hides), a mutation check will show that deleting the lower layer fails no test,
because every test goes through the upper one. Call the lower layer directly. Likewise a check that samples something
(a spinner holding still, a label not appearing) must first prove there is something to sample, with a control that shows
it changing when the feature is on; otherwise it samples an empty page and passes. And when a test injects a stand-in into
a browser, assert that the stand-in answered: a function passed to an init script loses its closure, the stub silently
never loaded, and the real browser's own answer made the test pass for the wrong reason.

Compare a timestamp from one machine with the clock of another only after you have simulated them disagreeing. A page that
measured "how long has this been running" by subtracting a server's event time from its own clock would show false alarms to
anyone viewing through a forwarded port or from a phone. Estimate the difference from live events (the smallest
"now minus stamp" seen) and test it with the page's clock seven minutes ahead and seven behind.

Passing tests do not tell you what the thing costs, so measure the cost. A page with a 36-suite test run behind it burned 4.2%
of a core for as long as a permission prompt waited, which can be hours, because a glow animated `box-shadow` and repainted every
frame. No test could have noticed; a CPU reading with animations switched off one at a time found it in minutes, and a test of the
*cause* (no repaint-bound infinite animation while idle, with a control proving the detector fires) now guards it. Do the same for
size, memory and time on whatever sits open or runs long.

Run N copies at once against whatever they share. Five simultaneous runs against one SQLite file all crashed with "database is locked"
in the middle of finishing, leaving a run "running" with no report; nothing had ever started two. Then break the shared thing on purpose
(a database that throws from the first phase on) and check the run survives, says so once, and does not claim success it cannot back up.

A bounded buffer must say when it has dropped something. A replay history capped at 5,000 events made a reloaded page and the saved
report quietly show only the tail of a long run while the README said "full transcript"; the note ("N earlier events dropped"), with an
exact count that a test adds up against what is on screen, is the fix. Keep related items together when you trim (a result without its
call is a headerless card) and never trim what someone is still being asked about.

Ask the question the owner will ask: is it useful, or decoration? Answer with the baseline, not a feeling. Here the simplest
alternative (one plain session) scored 4,037 of 4,040 for $0.08 against the pipeline's 4,039 for $1.41; the honest page says so, sorts every
feature into "earns its place / small / delight / unproven" with the measured price of the delight, and names the experiment that would
settle it. While writing it, check every number against the code: two docs disagreed with themselves (13 and 16 prompts; 26 and 37 suites)
and one true claim was incomplete (50 KB of images travel as 71 KB in every report).

"The suite passes" is a claim about one commit. After adding a server timestamp to an existing message, the full suite was reported green;
it had not been re-run since that change, and a test that stamped events with a clock 7 minutes off while the test server truthfully
reported its own went red on Linux, macOS and Windows at once. The test was inconsistent, not the product (a real server stamps events and
reports its time from one clock); the fix gave the test server the same skewed clock, and the check that the page's skew handling really
is what makes it pass was re-run with that handling broken. Run everything after the last edit, then read CI, and read each failing job's
own output: the cross-platform job was allowed to fail so that it could report a table, which meant the run showed "success" while two or
three suites in it were red.

Porting is testing. The first run on macOS and Windows (listed in the docs as "untested") found a server that answered 404 to its own page's
scripts on Windows (`normalize("/persona.js")` is `\persona.js` there), a command line that printed `file://` plus a Windows path (not a
URL, not a link), and tests that passed a bare `D:\...` path to `node --import` (read as the scheme `d:`). Two more failures were about
the newer browser CI installs, not the operating system: the same notification-permission assertion that passed on the sandbox's older
Chromium said `denied` on Linux CI too. When one failure shows up on every system, suspect the version before the OS.

A test that samples once after a fixed sleep is a race with the machine's load. A dinosaur game's "the picture changes as it runs" compared
two frames 250 ms apart and failed once on a loaded runner; it could not be reproduced locally (36 intervals, every one different). When
you cannot reproduce, say so in the commit, make the assertion wait for the condition with a bound, and do not claim a cause you did not
see.

A scripted recording must script every timestamp. The desktop walkthrough's header read "1309m 48s" because one event (an approval
request) was stamped by the server's real clock while everything else came from the scripted one, and the page estimates the server's
clock from the live events it sees. The recorder now scripts that event too, and the server takes a clock option for exactly this. It was
found by looking at a contact sheet of the finished video, not by any test: look at the thing a person will look at.

