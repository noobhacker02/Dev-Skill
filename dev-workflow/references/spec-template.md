# Spec: <task name>

> Written in Step 3 of the dev-workflow loop, before implementation starts. The bar for "done"
> is: someone with none of this conversation's context could implement from this file and know
> when they're finished.

## Request

The user's ask, close to verbatim.

## Restated scope

What we heard, in plain language — this is the Step 1 intake restatement, kept for the record.
Include what's explicitly **out of scope** if the request could plausibly be read more broadly
than intended.

## Tech stack

The stack in use (or chosen, if this is a new project) and why, if it wasn't already fixed by the
existing codebase.

## Requirements

The concrete, checkable things the implementation must do. Prefer a numbered list over prose —
each item should be small enough that it's obvious in review whether it was met.

1. ...
2. ...

## Expected output / deliverable

Exactly what exists when this is done: files changed, endpoints added, commands available, UI
states, etc. Be concrete — "a working login form" is not this; "a `/login` route rendering an
email+password form that POSTs to `/api/login` and redirects to `/dashboard` on success, or shows
an inline error on 401" is.

## Test plan

What will actually be checked in Step 8, and how. This is the most load-bearing section — it's
what turns local verification from a vibe check into a real gate. For each requirement above, name
the check that proves it:

| Requirement | How it will be verified |
|---|---|
| ... | e.g. Playwright: fill form with valid creds → redirected to /dashboard |
| ... | e.g. unit test: `parseCsv` rejects malformed rows |

## Open questions / risks

Anything genuinely uncertain going in — a dependency that might not support something needed, an
ambiguous edge case, a performance concern. Not a place to restate the obvious.
