# Model & effort tiers across the loop

Quality doesn't cost the same at every phase, and neither should the model/effort spent on it. A
wrong call in Step 3 (Spec) is expensive to discover later and cheap to prevent by thinking harder
up front, while Step 5 (Execute) is usually the highest-token-volume phase in the whole loop and,
*if the spec is actually solid*, close to mechanical. Spending frontier-level effort uniformly
across every phase is the same mistake as spending none of it anywhere — this is about matching
effort to where it actually changes the outcome.

This is a documented, validated pattern in agentic coding systems generally, not something
specific to this skill: three-tier model routing (frontier model for planning/coordination,
mid-tier for high-volume implementation, fast/cheap for bulk mechanical operations) has been
measured at roughly half the cost of uniform frontier-model use with comparable outcomes, and
weak models given a strong model's detailed plan measurably outperform weak models planning for
themselves — the planning effort transfers through the plan, not through the executor having to
be smart on its own. See Sources below.

## The three tiers

**PLAN — Steps 1–4 (Intake, Tech stack, Spec, Research) → highest capability, highest effort.**
This is low-volume (a spec is a page or two, not a codebase) and high-leverage — every downstream
step inherits whatever this phase got wrong, with no upstream correction mechanism once execution
has started. Use the strongest model available at its highest reasoning effort here. The bar
already stated in `spec-template.md` — a spec detailed enough that someone with zero context could
implement from it — is exactly what makes the next tier's cost savings *safe* rather than reckless;
skimping here to save cost is a false economy, since it just relocates the cost into rework later.

**EXECUTE — Step 5 → lowest effort that still works, fastest model.** This phase burns the most
tokens (all the actual code), so it's where a cheaper/faster model has the largest absolute impact.
This is only safe because PLAN already resolved the ambiguity — a low-effort executor isn't being
asked to make judgment calls, just to follow an unambiguous plan closely. **Circuit breaker:** if
execution hits a real ambiguity the spec didn't resolve, that's a signal the *spec* needs another
PLAN-tier pass, not that the executor should improvise around the gap at low effort. Escalate back
to Step 3 rather than guess forward.

**RECHECK — Steps 6, 8, 9 (Quality gate, Local verification, Status report) → medium capability,
medium effort, and — this is the part that actually matters, more than the model tier — a fresh
context, not a continuation of Step 5's.** A verifier sharing the executor's context window
inherits the executor's assumptions and blind spots along with its reasoning; it's self-confirmation,
not independent review. RECHECK's job is narrower than PLAN's (it's checking specific, mostly
enumerated things — does the diff satisfy the spec's requirements table, does it pass the safety
scan, do the test-plan's rows actually pass) but it needs enough independent judgment to catch what
a low-effort executor rushed past, which a same-context glance at "does this look right" usually
won't. Medium effort here is the actual middle ground the tiering is trying to find: not
"trust the executor" (cheap, no safety net) and not "rerun everything at PLAN-tier effort"
(correct but erases the savings from tier two).

## Applying this

**Orchestrated as separate subagent calls per phase** (e.g. via an `Agent`-style tool that takes a
`model` parameter): request PLAN phases on the strongest model, EXECUTE on a faster/cheaper one,
and run RECHECK as a *new* subagent call — new context — even if it's cheap to keep the executor's
context around. The fresh context is doing more work than the model choice; a same-tier model in a
clean context beats a stronger model continuing the executor's own reasoning chain.

**Running as a single continuous session** (the common case for this skill): true mid-session
model/effort switching usually isn't available, but the qualitative shape still holds. Spend real
deliberation on Steps 1–4 before writing any code — resist the pull to rush the spec to get to
implementation. Move efficiently and directly through Step 5 once the spec is solid — re-deriving
the plan while executing is wasted effort the plan already paid for. For Steps 6/8/9, deliberately
re-read the spec's requirements and test-plan tables from scratch rather than reasoning from memory
of having just written the code — that's the same fresh-look discipline a context switch would have
forced, done by choice instead.

**Don't over-split.** Three tiers, not nine — one per loop step. Spinning up a fresh subagent for
every individual step adds handoff latency and context-transfer overhead that isn't worth it for
low-stakes steps (Step 7's commit doesn't need its own tier). Group by the three tiers above and no
finer.

## Sources

- [Best AI Model for Coding Agents in 2026: A Routing Guide](https://www.augmentcode.com/guides/ai-model-routing-guide) — three-tier Claude routing (frontier for coordination, mid-tier for implementation, fast model for bulk file operations) measured at roughly half the cost of uniform frontier-model deployment.
- [An Empirical Study on Strong-Weak Model Collaboration for Repo-level Code Generation](https://arxiv.org/pdf/2505.20182) — strong-to-weak plan injection consistently improves weak-model execution success; the gain comes from the plan's structured content, not from extra compute at execution time.
- [What Is the Verifier Pattern in Multi-Agent Systems?](https://www.mindstudio.ai/blog/verifier-pattern-multi-agent-systems-independent-review) — a verifier sharing the generator's context produces self-confirmation, not independent review; effective verification needs the requirements and the output, not the generator's reasoning chain.
