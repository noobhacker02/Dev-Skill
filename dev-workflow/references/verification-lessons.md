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

## 21. Run a new test twice in a row, and its mutant once

**What happened (agent-loop's companion work, 2026-10-02).** A test for a compaction hook checked that a configured save directory outside the
project was refused, using a fixed path under `/tmp`. It passed. Then the test harness ran a deliberately broken copy of the hook (the
project-boundary guard removed) to prove the test could notice, and that copy did exactly what the guard exists to stop: it wrote into the fixed
path. The next run of the real hook failed its own check because the directory was no longer empty. A benchmark that wraps the test recorded a
first baseline of 0 of 1 for the wrong reason.

**How it was found.** The test passed when run by hand and failed when run by the benchmark a minute later; running it twice in a row
reproduced it.

**The rule.** Give every path a test touches a unique name, clean up after it, and run a new test twice in a row before trusting it. A mutant
that is supposed to misbehave must not be able to leave state that a later honest run can see.

## 22. For anything sizeable, run an adversary round with a new agent

**Why.** An adversary that is the same session as the builder shares its blind spots; one that is given the builder's summary inherits its
assumptions. The point of a round is a mind that has not seen your reasoning, given only the spec, the threat model and the interfaces, who must
**prove** each finding with a reproduction.

**How to run it.** See `improvement-loop.md`: a new agent every round, titles of earlier findings from round two, findings with a command or a
step-by-step scenario or marked unconfirmed, each confirmed finding fixed test-first with a log entry, stop when a round finds nothing above
low or the round budget is spent, findings per round recorded.

## 23. A boundary enforced on the first request is not a boundary on a chain

**What happened (agent-loop, adversary round 1, finding A2, critical).** The browser's "localhost only" boundary was a Playwright route handler, which is
called once, for the first URL of a request. A server-side redirect is followed inside the browser, so the handler never saw the next hop. A fresh-context
agent reproduced it: a decoy server on an off-list address received `/exfil?data=secret` through one 301, while a direct request to the same host was refused.
The project's own docs said the boundary was "already built and tested". The fix was a layer underneath: a local proxy the browser must use, so every hop is a new
request that arrives at a place that can refuse it; it also exposed that this Chromium contacts google.com by itself at start-up.

The same round found the file tools judging paths as text: a symlink inside the project directory pointing at the login profile was read straight through, and
`link/..` was judged by its text while the operating system resolves it through the link. (An early version of the new test used `path.join` to build that input,
which collapses the `..` as text and so tested nothing. A dangling symlink was a second hole: writing through it creates the file at its target.)

**The rule.** For any boundary, test with a decoy that records what reaches it, and try the chain: redirects (all five status codes, a chain, a meta refresh, a
`Refresh` header), subresources, frames, popups, tunnels, sockets, and the tool's own background requests. For paths, build the attack on a real disk with real links
and judge the path as the operating system resolves it. Do not trust "the layer I added covers it": make the test fail on the old code first.

## 24. A baseline is measured, not remembered

**What happened.** The first observability baseline was 2 of 8 (one point was the word "blank" matching the page's own URL), corrected to 1 of 8, and an adversary round
then showed the last point was the redirect probe matching the landing URL that every `inspect` prints. The true baseline was 0 of 8, found by building the old commit in
a scratch worktree and scoring it with the corrected scorer. Separately, a hand-edited baseline made the table show a gain that never happened, one corrupt file made the
runner silently re-record every baseline, and the freshness checks passed when the commit they named was missing from the clone.

**The rule.** Score the old code with the corrected scorer, in a worktree. Make a baseline change need a logged reason checked against git history, make a corrupt
baseline stop the runner, compare pass rates when the number of checks changes, and make a freshness check fail closed where it matters (CI) when it cannot measure.


## 25. Before pushing a test, say what it assumes about the machine

**What happened.** Three systems went red for different reasons, none of which showed on the machine the code was written on: a proxy connected to only the first address a name
resolved to (CI runners resolve `localhost` to `::1` first, the test server listened on `127.0.0.1`), a path scope treated `/` as a directory (on Windows it is the current drive),
a generated table was compared with a checkout that had CRLF endings, and two tests paused for a fixed time before an action that needed a particular state. A load experiment
was then run without the flags the npm script adds, so it measured the real SDK and proved nothing.

**The rule.** Write down, in the commit or the test header, what the test assumes about loopback order, path roots and separators, line endings, case sensitivity and timers. Replace a
fixed pause with a wait for the state itself, and measure from the action, not from the start. Run a suite the way its script does (`npm run test:x`). After a push read CI for **every**
system, and say which fixes were reproduced locally and which are confirmed only by CI.

## 26. A reader that cannot see part of the thing must say so, or its "nothing wrong" means nothing

**What happened.** A page reader listed one field of four on a form whose other questions sat in an iframe and a shadow root. It reported no error: it simply did not know the rest existed. Every check planned on top of it
(a diff of the filled form against the facts, a job-id check, a hidden-text check) would have said "no mismatch" for questions it never read. A fresh-context adversary found this by running the reader on a page built to
break it, not by reviewing the plan. The fix had a second half: a text field with opacity 0 (a bot trap) was offered as an ordinary field, because "visible" had been defined by the DOM, not by a person.

**The rule.** For any reader, scanner or checker, define the states "could not read this" and "this is hidden from a person" and make them loud (a named block in the result, a refusal to act), so a pass means "read it all and it
was fine". Test it on a page with every kind of container (frame, shadow root, a frame still loading, one that fails, over the limit) and score the old code first. When page-side code is shared as text, build real functions
from it: Playwright runs a string as an expression and ignores the argument.

## 27. A filter test names the byte classes and the channels it covers

**What happened.** The first test that no control byte reaches the terminal fed one escape sequence (C0) into the text output and passed. A stricter version found C1 characters (U+0080 to U+009F) inside a plan field and a
repository file name inside `--json`: two channels and one byte class the first test never touched. A mutation that removed the JSON filter had survived for the same reason.

**The rule.** Write the matrix before the test: byte classes (C0, C1, bidi overrides, NUL) by channels (text output, JSON output, file names, role and config files, error text). NUL cannot be put on a command line, so
call the function directly for that class. Feed every class through every channel, include a control that the same input without the bad bytes still works, filter at the source and again at the edge, and mutate each
filter to see the test fail.

## 28. Judge what the tool will open or run, not what the text looks like

**What happened.** An approval hook and a set of path hooks decided from the text of a command or a path, and the tool that acted on the text read it differently. Round 1 of the adversary found a read through a symlink
inside the allowed directory. Round 2 found `~/x` judged as a directory called `~` while the file tools expand it to the home directory, a relative link judged from the wrong directory, `sed '1e CMD'` and `sed w`
(run a program, write a file) approved as "read-only because it is sed", `rg --pre`, `git remote set-url`, `sort -o`, `cat {/etc/hostname,notes.txt}` (the shell expands the brace before the command sees it), and a credential
list that knew only exact file names. Three proof files were created outside the directory by commands the hook approved with no prompt. It was the fourth time in the project that a check on text lost to a tool that reads
the same text another way.

**The rule.** For any gate on what a tool is given: (1) resolve the way the tool does, links, `~`, `..`, drive forms and the base directory it will use; (2) allow-list safe FORMS instead of listing dangerous names, because one
name (`sed`, `git`, `find`) hides many forms and a list of names is a list of the ones you thought of; (3) a word the shell rewrites before the command sees it (a glob, a brace, a tilde, a variable) is a word you cannot judge, so
it asks; (4) write the table of every form of input beside the ordinary commands that must still run without asking, because a rule that asks about everything is turned off by the people it was meant to protect; (5) score the
old gate with that table first.

## 29. A test for a failure that kills or hangs a process: measure it on the old code many times, run it in a child, and count a timeout as a failure

**What happened.** Four things went wrong with tests of this kind in one round. A popup storm that killed the old build about one run in three was called "fails on the old code" after one lucky run, so the first benchmark
score said the check passed; five or six runs and a harsher scenario (ten popups with eight requests each, then thirty) made it fail every time. A test for a bad status line installed an `uncaughtException` listener to
detect the crash, and the listener caught the test's own failed assertion: the old build "passed" with exit 0. A child process that outlived its time limit came back from `spawnSync` with `status: 0` and `error: ETIMEDOUT`,
which a harness that read `status` alone scored as a clean exit. And a new test file run from the main tree to "score the old build" imported `../dist` from its own location, so it scored the new one.

**The rule.** Run the scenario against the old build five or six times and keep making it harsher until it fails every time, or a mutant survives it by luck. Run it in a child process with a time limit, and treat a timeout, a
signal and an error as failures in their own right, never `status` alone. Remove any detector listener before asserting. When scoring an old build, copy the test into the scratch worktree and print which `dist` it loaded.

## 30. A wait in a test is on a signal, and a test that touches timing is run under load before it is called stable

**What happened.** A browser test opened a page that opens and closes thirty popups, waited a fixed 2 s, and asked the browser tools what the page says. Alone it passed every time. In the full suite, with other suites using the CPU, the page's storm was still running at 2 s; the
browser dropped the call ("Resulting promise was garbage collected") and the test failed, and so did the benchmark check that measures the same thing. The test was not wrong about what should happen; it was wrong about how long it takes. Re-running it would have turned green and hidden that the
product handed the agent an error it could not act on.

**The rule.** Wait for a signal from the thing you are waiting for (the page makes a request when its work is over; an event; a file appears), never for a number of seconds. If a test depends on timing at all, run it with four busy loops (`node -e 'while(true){}'` four times) and count
failures over six runs before calling it stable, and read "passes alone, fails in the full suite" as "load" first. When the failure is one an agent would meet in real use, fix the product as well as the test: ask a read again, say plainly what happened for an action, and do not repeat an action
that may have happened.

## 31. A mutation check starts with a control, and "0 survivors" on the first pass is a reason to look

**What happened.** A mutation run over a new module said 0 survivors of 30. The test it ran was failing on the unmutated code (a wording assertion that was wrong), so every mutant died of that one failure. Earlier, a copy of the tree that did not contain a directory the test reads had made a test fail in the copy only, and one mutant was counted as killed by it; with the directory in place it survived and exposed a missing assertion.

**The rule.** Before the first mutant, run the unmutated copy through the same tests and stop if it fails. Give the copy every directory the tests read. Read the survivor count together with the control line, and treat a perfect score on the first pass as something to check, not to report. Then, as before, every survivor is a missing assertion, a redundant line (delete it), a redundant layer (a combined mutant shows it), an equivalent mutant (say why), or an unexercised guard (say so).

## 32. A mistake made twice becomes a scan; a path handed to a child process is checked on Windows by a test, not by memory

**What happened.** A test started a child node process with `--import` and an absolute path. Windows reads `D:\a\...` as a URL with the scheme `d:` and refuses it. The suite on Linux passed on the exact commit; the Windows CI job failed after the push. It was the fourth time, and a catalog row telling people to use a file URL had not prevented it. In the same run a UI test failed with "undefined" because a page script had not loaded and the harness hid failed loads as noise, so the cause could not be read.

**The rule.** The second time anything fails for the same reason, write the test that looks for the cause (a scan of the repository for the pattern), not another sentence. Check the scanner against snippets it must refuse and snippets it must accept, run it on the tree before the fix to see it fail there, and mutation-check it. For anything a person cannot see when it goes wrong (a page that survives a missing script), make the harness say what failed instead of letting the test report only the symptom.

## 33. Every mutation survivor gets a verdict; the one that is neither redundant nor unreachable is a bug

**What happened.** A mutation run over a new profile-and-lock module left 51 survivors of 121. Most were missing assertions (a directory readable by the group alone was never tried; the field of a process's start time was never compared across two processes; the recovery mutex was never contended). A few were genuinely equivalent. One was a redundant clause in a path-containment helper; rewriting it without the redundant clause showed that `startsWith("..")` also matches a directory *named* `..x`, so a profile could be placed inside a forbidden directory. In the same pass a test failed on correct code because I had assumed a blocked service worker rejects `register()`; it resolves, and the worker just never runs.

**The rule.** Give every survivor a verdict and write it next to the mutant: *a missing test* (write one that fails on the mutant), *equivalent* (say why the behaviour is identical), *unreachable here* (say which platform or fault reaches it) or *a defect* (fix it test-first, and confirm the new test fails on the old code). Read the equivalent ones twice, because a redundant clause is a clause nobody tested. For a race between two processes, give the code a test-only hook at the point where the other one can step in and drive both sides from the test; a stress test only sometimes lands there. Before asserting what a library call does, run it on the odd inputs and read the result, and assert the effect that matters rather than the shape of the call. Finish with one consolidated pass over the final code and quote its numbers, not the sum of earlier passes. Treat an *equivalent* verdict as a claim to test: before writing "the platform handles it", build the counterexample (a link, a missing directory, a slow start) in the test itself and see whether the mutant survives it. One verdict of that kind ("`path.relative` resolves a relative path itself") was wrong, and a macOS CI run found the bug on the day it was written, because Linux's temporary directory is not a link.

## 34. When the thing being checked can lie, check it twice, and the second time where it cannot reach

**What happened.** A tool that attaches a file to a web form had to be sure the form sends it to the right site. The first check asks the page (what is the form's action, where do the buttons post) and it is only as honest as the page: an input named `action` hides the real attribute, a script can replace the accessors or `URL`, a script can rewrite the form after the look, and a script can send the file with `fetch` and no form at all. A look at the address resolver also showed that asking the page to parse addresses lets the page parse them its own way. The version that held was layered: ask through the browser's own accessors on the real prototypes, take the raw strings out and resolve them in the trusted process, look again after the file is attached, and, last, put the rule where the page cannot reach: while a file is attached, the network layer holds that tab's non-read requests to the page's own site, whatever the page says it is doing. The tests give the page every lie in turn and count what arrives at the far side.

**The rule.** A check made by asking the subject is advisory. Name who controls the answer, and for anything that matters repeat the check in a layer that party does not control (the network, the trusted process, the operating system), then write the test from the liar's side: one hostile page per lie, with a counter on the far side and a control that is allowed. Do the cheap honest check too, for the message it gives the person.
