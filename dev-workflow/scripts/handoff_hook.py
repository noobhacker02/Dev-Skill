#!/usr/bin/env python3
"""
Claude Code hook that keeps a project's handoff document from being lost to context compaction.

One script, three events (the event name comes from the hook's JSON on stdin):

  PreCompact   warn (systemMessage) if the handoff doc is missing or its "Updated:" stamp is old.
               PreCompact has no documented way to block or to inject context, so this can only warn.
  PostCompact  save the compaction summary (compact_summary) to <save_dir>/<UTC time>-<trigger>.md,
               with obvious secrets redacted, so the summary survives outside the transcript.
  SessionStart re-inject the handoff doc as additionalContext (source: startup/resume/clear/compact),
               plus the path of the newest saved summary.

Opt-in per project: nothing happens unless a handoff doc is found. Looked up, in order:
  $HANDOFF_FILE, then .claude/handoff.json {"handoff": "path", "save_dir": "path", "max_age_minutes": 45},
  then docs/HANDOFF.md, HANDOFF.md under the session's cwd.

It never blocks: it always exits 0, ignores malformed input, and only writes inside the project directory.
Standard library only.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

MAX_INJECT_CHARS = 24000
MAX_SUMMARY_BYTES = 200_000
DEFAULT_MAX_AGE_MIN = 45

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----|$)"),
    # A key name with anything word-like before or after it (GITHUB_TOKEN, access_token, DB_PASSWORD, client_secret, AWS_SECRET_ACCESS_KEY, "password": "x") and its value. A \b in front would not fire
    # inside GITHUB_TOKEN, because _ is a word character (adversary round 2, A34). The trailing run is bounded so a long word cannot make the match slow.
    re.compile(r"(?i)(token|secret|passw(or)?d|pwd|api[_-]?key|private[_-]?key|credential|session[_-]?id|jsessionid|li_at)[\w.-]{0,40}[\"']?\s*[:=]\s*[\"']?[^\s\"';,]{6,}"),
    # A header that carries a credential, the whole value (a Cookie line holds several)
    re.compile(r"(?im)^[ \t>*-]*((set-)?cookie|(proxy-)?authorization|x-api-key)[ \t]*:[ \t]*\S.*$"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"),
]


def redact(text):
    for pat in SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text


def load_config(cwd):
    cfg = {}
    try:
        with open(os.path.join(cwd, ".claude", "handoff.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        pass
    env_file = os.environ.get("HANDOFF_FILE")
    handoff = env_file or cfg.get("handoff")
    if not handoff:
        for cand in ("docs/HANDOFF.md", "HANDOFF.md"):
            if os.path.isfile(os.path.join(cwd, cand)):
                handoff = cand
                break
    if not handoff:
        return None
    handoff = handoff if os.path.isabs(handoff) else os.path.join(cwd, handoff)
    save_dir = cfg.get("save_dir") or os.path.join(os.path.dirname(handoff), "handoff", "compactions")
    save_dir = save_dir if os.path.isabs(save_dir) else os.path.join(cwd, save_dir)
    return {
        "handoff": os.path.realpath(handoff),
        "save_dir": os.path.realpath(save_dir),
        "max_age_minutes": int(cfg.get("max_age_minutes", DEFAULT_MAX_AGE_MIN)),
    }


def inside(path, root):
    root = os.path.realpath(root)
    path = os.path.realpath(path)
    return path == root or path.startswith(root + os.sep)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return None


def pre_compact(data, cfg, now):
    text = read_text(cfg["handoff"])
    trigger = data.get("trigger", "?")
    if text is None:
        msg = f"Context is about to be compacted ({trigger}) and there is no handoff document at {cfg['handoff']}. Write one first if you still can."
        return {"systemMessage": msg}
    m = re.search(r"^Updated:\s*(\S+)\s*$", text, re.M)
    try:
        stamp = datetime.fromisoformat(m.group(1).replace("Z", "+00:00")) if m else None
    except Exception:
        stamp = None
    if stamp is None:
        return {"systemMessage": f"Context is about to be compacted ({trigger}); the handoff document has no readable 'Updated:' stamp."}
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    age_min = (now - stamp).total_seconds() / 60
    if age_min > cfg["max_age_minutes"]:
        return {"systemMessage": f"Context is about to be compacted ({trigger}) and the handoff document was last updated {int(age_min)} minutes ago (stale after {cfg['max_age_minutes']}). The compaction summary will be saved next to it."}
    return None


def post_compact(data, cfg, cwd, now):
    summary = data.get("compact_summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    # Only ever write inside the project directory, whatever the config says.
    if not inside(cfg["save_dir"], cwd):
        sys.stderr.write(f"handoff_hook: save_dir {cfg['save_dir']} is outside the project; not writing\n")
        return None
    os.makedirs(cfg["save_dir"], exist_ok=True)
    trigger = re.sub(r"[^a-z]", "", str(data.get("trigger", "x")).lower()) or "x"
    name = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{trigger}.md"
    body = redact(summary).encode("utf-8")[:MAX_SUMMARY_BYTES].decode("utf-8", errors="ignore")
    header = f"# Compaction summary ({trigger}) saved {now.isoformat()}\n\nSession: {data.get('session_id', '?')}\n\nSecrets are redacted on a best-effort basis. Compare this with the handoff document and add anything missing there.\n\n---\n\n"
    path = os.path.join(cfg["save_dir"], name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(header + body + "\n")
    os.replace(tmp, path)
    return None


def session_start(data, cfg):
    text = read_text(cfg["handoff"])
    if text is None:
        return None
    note = ""
    if len(text) > MAX_INJECT_CHARS:
        text = text[:MAX_INJECT_CHARS]
        note = f"\n\n[handoff truncated at {MAX_INJECT_CHARS} characters; read the whole file at {cfg['handoff']}]"
    newest = None
    try:
        files = sorted(f for f in os.listdir(cfg["save_dir"]) if f.endswith(".md"))
        newest = os.path.join(cfg["save_dir"], files[-1]) if files else None
    except Exception:
        pass
    pointer = f"\n\nNewest saved compaction summary: {newest}" if newest else ""
    ctx = (f"Session source: {data.get('source', '?')}. The project keeps a handoff document so context is not lost. "
           f"Treat it as the current state of the work, and update it before the next compaction.\n\n--- {cfg['handoff']} ---\n{text}{note}{pointer}")
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        if not isinstance(data, dict):
            return 0
        cwd = data.get("cwd") or os.getcwd()
        cfg = load_config(cwd)
        if not cfg:
            return 0
        event = data.get("hook_event_name")
        now = datetime.now(timezone.utc)
        if event == "PreCompact":
            out = pre_compact(data, cfg, now)
        elif event == "PostCompact":
            out = post_compact(data, cfg, cwd, now)
        elif event == "SessionStart":
            out = session_start(data, cfg)
        else:
            out = None
        if out:
            sys.stdout.write(json.dumps(out))
    except Exception as e:  # a hook must never wedge a session
        sys.stderr.write(f"handoff_hook: ignored error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
