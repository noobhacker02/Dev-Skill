# Git hooks: what they block and how to work with them

Installed once per repo by `scripts/install-hooks.sh` (see SKILL.md Step 0). Both hooks run the
same engine, `scripts/check_staged.py`:

- **pre-commit** — scans exactly what's staged (`git diff --cached`).
- **pre-push** — scans every commit range about to be pushed (computed from the ref updates git
  passes the hook on stdin; a brand-new branch's first push is scanned in full, against the empty
  tree).

## What gets blocked

1. **`.env` files** — any `.env` or `.env.<suffix>` filename being added or modified, except
   `.env.example` / `.env.sample` / `.env.template` / `.env.dist`.
2. **Secrets** — AWS access key IDs, private key material (`-----BEGIN ... PRIVATE KEY-----`),
   Slack tokens, GitHub tokens, OpenAI/Anthropic-style `sk-...` keys, and generic
   `password/api_key/secret = "..."`-shaped assignments (the generic patterns skip anything that
   looks like a placeholder — `changeme`, `your_api_key`, `<...>`, `${...}` interpolation, etc., to
   cut down on noise).
3. **Destructive SQL** — `DROP TABLE/DATABASE/SCHEMA`, `TRUNCATE TABLE`, `ALTER TABLE ... DROP
   COLUMN`, and `DELETE`/`UPDATE` statements with no `WHERE` on the same line.
4. **Destructive shell** — `rm -rf /`, `~`, `*`, or `$HOME`; `git push --force` (but not
   `--force-with-lease`); `git reset --hard`; `chmod -R 777 /`; raw `dd ... of=/dev/...` disk
   writes; shell fork bombs.
5. **TruffleHog**, when installed, additionally scans every touched file for verified/likely
   secrets using its full detector set — a strictly deeper check than the patterns above. If it
   isn't installed, the hook prints an install link and continues; it does not block the commit or
   push on TruffleHog's absence, because the pattern checks above already provide a baseline and
   requiring every contributor to install a third-party tool before their first commit is worse
   for adoption than it's worth.

The destructive-command/SQL check (but not the secret check) skips `.md`/`.mdx`/`.rst`/`.txt`
files: documentation about this tool necessarily names the exact patterns it blocks (this file
does, right above), and that's prose, not code that will ever execute. A real secret pasted into a
README by mistake is still a real secret, so the secret patterns and TruffleHog still run on
docs.

## Handling a false positive

Two escape hatches, both meant for genuine false positives — not for actually committing a real
secret or destructive command:

- **Inline**, on the exact offending line: add a comment containing the literal text
  `devskill:allow` (in whatever comment syntax the file uses, e.g. `# devskill:allow` or
  `// devskill:allow`).
- **Repo-wide**, in a `.devskill-allowlist` file at the repo root: one regex per line (lines
  starting with `#` are comments). Any finding whose line content matches one of these regexes is
  suppressed everywhere, not just on one line — use this for a recurring pattern (e.g. a test
  fixture directory full of intentionally fake keys) rather than one-off inline markers.

## Troubleshooting

- **"python3 not found"** — the hooks need python3 on PATH (standard library only, nothing to
  `pip install`). Set `PYTHON=/path/to/python3` in the environment if it's installed somewhere
  non-standard.
- **Hook didn't run at all** — check `git config core.hooksPath` points at `.githooks` in this
  repo; `install-hooks.sh` sets this, but it's local to each clone and isn't carried by version
  control, so a fresh clone needs one run of the install script.
- **Need to bypass in a genuine emergency** — `git commit --no-verify` / `git push --no-verify`
  skip hooks entirely. This is a real bypass, not a workflow step; don't reach for it to get past a
  finding you haven't actually looked at.
