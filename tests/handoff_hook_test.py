#!/usr/bin/env python3
"""
Tests for dev-workflow/scripts/handoff_hook.py using the payload shapes from the Claude Agent SDK's hook types
(PreCompact: trigger/custom_instructions; PostCompact: trigger/compact_summary; SessionStart: source).
Also runs three mutants of the script (redaction removed, project-boundary guard removed, a word boundary back in front of the key name) and requires the checks to catch them,
so a green run means the safeguards are actually exercised.
Live firing by Claude Code is NOT tested here; that can only be observed when a real compaction happens.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "dev-workflow", "scripts", "handoff_hook.py")
FAKE_KEY = "sk-" + "ant-" + "A1b2C3d4E5f6G7h8I9j0"  # built at runtime so this file holds no key-shaped literal


def run(script, payload, raw=None):
    p = subprocess.run([sys.executable, script], input=raw if raw is not None else json.dumps(payload), capture_output=True, text=True, timeout=20)
    return p.returncode, p.stdout, p.stderr


def project(updated_minutes_ago=5, config=None):
    d = tempfile.mkdtemp(prefix="handoff-hook-")
    os.makedirs(os.path.join(d, "docs"))
    ts = (datetime.now(timezone.utc) - timedelta(minutes=updated_minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(d, "docs", "HANDOFF.md"), "w") as f:
        f.write(f"# Handoff\n\nUpdated: {ts}\n\n## Next step\nDo the thing UNIQUE-HANDOFF-MARKER.\n")
    if config is not None:
        os.makedirs(os.path.join(d, ".claude"))
        with open(os.path.join(d, ".claude", "handoff.json"), "w") as f:
            json.dump(config, f)
    return d


def checks(script):
    """Returns a list of failure strings (empty = all good)."""
    bad = []

    def expect(cond, msg):
        if not cond:
            bad.append(msg)

    # PreCompact: stale warns, fresh is silent, missing warns, never blocks
    d = project(updated_minutes_ago=300)
    rc, out, _ = run(script, {"hook_event_name": "PreCompact", "trigger": "auto", "custom_instructions": None, "cwd": d})
    expect(rc == 0 and "stale" in json.loads(out or "{}").get("systemMessage", ""), "PreCompact did not warn on a stale handoff")
    d = project(updated_minutes_ago=2)
    rc, out, _ = run(script, {"hook_event_name": "PreCompact", "trigger": "manual", "custom_instructions": None, "cwd": d})
    expect(rc == 0 and out.strip() == "", "PreCompact was not silent on a fresh handoff")
    d = project()
    os.remove(os.path.join(d, "docs", "HANDOFF.md"))
    rc, out, _ = run(script, {"hook_event_name": "PreCompact", "trigger": "auto", "cwd": d})
    expect(out.strip() == "", "PreCompact spoke in a project that has no handoff at all (should be opt-in)")
    d = project()
    cfg = os.path.join(d, ".claude"); os.makedirs(cfg)
    json.dump({"handoff": "docs/NOPE.md"}, open(os.path.join(cfg, "handoff.json"), "w"))
    rc, out, _ = run(script, {"hook_event_name": "PreCompact", "trigger": "auto", "cwd": d})
    expect(rc == 0 and "no handoff document" in json.loads(out or "{}").get("systemMessage", ""), "PreCompact did not warn when the configured handoff is missing")

    # PostCompact: saved, redacted, named by trigger
    d = project()
    summary = f"Summary of the work. The key is {FAKE_KEY} and password: hunter2hunter2 were pasted. Decision: use the queue."  # devskill:allow (fake value on purpose: this test checks it is redacted)
    rc, out, _ = run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": summary, "session_id": "s1", "cwd": d})
    save_dir = os.path.join(d, "docs", "handoff", "compactions")
    files = os.listdir(save_dir) if os.path.isdir(save_dir) else []
    expect(rc == 0 and len(files) == 1 and files[0].endswith("-auto.md"), f"PostCompact did not save one -auto.md file (got {files})")
    if files:
        saved = open(os.path.join(save_dir, files[0])).read()
        expect("Decision: use the queue." in saved, "saved summary lost its content")
        expect(FAKE_KEY not in saved, "secret-shaped key was saved unredacted")
        expect("hunter2hunter2" not in saved, "password assignment was saved unredacted")
    rc, out, _ = run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "   ", "cwd": d})
    expect(rc == 0 and len(os.listdir(save_dir)) == 1, "an empty summary created a file")

    # PostCompact: the ordinary spellings of a secret (adversary round 2, A34: 8 of 10 survived into a file that is committed). The values are invented and built at run time.
    d = project()
    v = "notarealvalue" + "12345"
    spellings = [
        "export GITHUB_" + "TOKEN=" + v,
        "DB_" + "PASSWORD=" + v,
        "client_" + 'secret = "' + v + '"',
        "access_" + "token=" + v,
        "refresh_" + "token: " + v,
        "Cookie: li_" + "at=" + v + "; JSESSIONID=\"" + v + "\"",
        "Authorization: Bear" + "er " + v + "." + v + "." + v,
        "AWS_SECRET_" + "ACCESS_KEY=" + v,
        "api_" + "key=" + v,
        '{"pass' + 'word": "' + v + '"}',
        "Set-Cookie: sid=" + v + "; Path=/",
        "curl -H 'Authorization: Bear" + "er " + v + "' https://example.test",
        "the jwt was eyJ" + "hbGciOiJIUzI1NiJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0." + "abcdEFGH",
    ]
    controls = ["The token budget for the run is large.", "Passwords are never logged and the secret store is outside this repo.", "Decision: the api key rotation is planned for Friday.", "Authorization is checked by the hook, not the page."]
    rc, out, _ = run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "\n".join(["Summary."] + spellings + controls), "session_id": "s2", "cwd": d})
    save_dir2 = os.path.join(d, "docs", "handoff", "compactions")
    files2 = os.listdir(save_dir2) if os.path.isdir(save_dir2) else []
    if files2:
        saved2 = open(os.path.join(save_dir2, files2[0])).read()
        expect(v not in saved2, f"a secret spelling was saved unredacted: still contains the value after redaction ({len([l for l in saved2.splitlines() if v in l])} line(s): {[l[:50] for l in saved2.splitlines() if v in l][:3]})")
        for c in controls:
            expect(c in saved2, f"redaction ate ordinary prose: {c!r}")
    else:
        expect(False, "PostCompact saved nothing for the spellings summary")
    # a long word and a long run of key names must not make the redactor slow
    import time
    d = project()
    t0 = time.time()
    run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": ("A" * 150_000) + "\n" + ("token" * 8_000), "session_id": "s3", "cwd": d})
    expect(time.time() - t0 < 10, f"redacting a long word took {time.time() - t0:.1f} s")

    # PostCompact: never writes outside the project, whatever the config says
    outside = tempfile.mkdtemp(prefix="handoff-outside-")
    d = project(config={"save_dir": os.path.relpath(outside, start=None) if False else outside})
    rc, out, _ = run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "should not land outside", "cwd": d})
    expect(rc == 0 and os.listdir(outside) == [], "summary was written outside the project directory")
    d = project()
    escape_name = "escape-" + os.path.basename(d)  # unique per check, so a mutant run cannot poison the next run
    json.dump({"save_dir": "../" + escape_name}, open(os.path.join(d, ".claude", "handoff.json"), "w")) if os.path.isdir(os.path.join(d, ".claude")) else (os.makedirs(os.path.join(d, ".claude")), json.dump({"save_dir": "../" + escape_name}, open(os.path.join(d, ".claude", "handoff.json"), "w")))
    escape_dir = os.path.join(os.path.dirname(d), escape_name)
    rc, out, _ = run(script, {"hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "no escape", "cwd": d})
    escaped = os.path.isdir(escape_dir) and os.listdir(escape_dir) != []
    expect(not escaped, "a ../ save_dir escaped the project")
    shutil.rmtree(escape_dir, ignore_errors=True)

    # SessionStart: injects the handoff for each source; includes the newest saved summary path; silent without a handoff
    for source in ("compact", "resume", "startup", "clear"):
        d = project()
        run(script, {"hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "older", "cwd": d})
        rc, out, _ = run(script, {"hook_event_name": "SessionStart", "source": source, "cwd": d})
        o = json.loads(out or "{}").get("hookSpecificOutput", {})
        expect(o.get("hookEventName") == "SessionStart" and "UNIQUE-HANDOFF-MARKER" in o.get("additionalContext", ""), f"SessionStart({source}) did not inject the handoff")
        expect("Newest saved compaction summary" in o.get("additionalContext", ""), f"SessionStart({source}) did not point at the saved summary")
    d = tempfile.mkdtemp(prefix="handoff-empty-")
    rc, out, _ = run(script, {"hook_event_name": "SessionStart", "source": "startup", "cwd": d})
    expect(rc == 0 and out.strip() == "", "SessionStart spoke in a project with no handoff")

    # A hook must never wedge a session: garbage in, exit 0, nothing out
    for raw in ("", "not json", "[]", "null", '{"hook_event_name": 5}'):
        rc, out, _ = run(script, None, raw=raw)
        expect(rc == 0 and out.strip() == "", f"garbage input {raw!r} did not exit quietly")
    return bad


def mutant(name, old, new):
    src = open(SCRIPT).read()
    assert old in src, f"mutation target for {name} not found in the script"
    path = os.path.join(tempfile.mkdtemp(prefix="handoff-mutant-"), "handoff_hook.py")
    open(path, "w").write(src.replace(old, new))
    return path


def main():
    failures = checks(SCRIPT)
    for f in failures:
        print("FAIL:", f)
    if failures:
        return 1
    m1 = mutant("no-redaction", "body = redact(summary)", "body = (summary)")
    m2 = mutant("no-boundary-guard", "if not inside(cfg[\"save_dir\"], cwd):", "if False:")
    m3 = mutant("word-boundary-before-key", "(?i)(token|secret|", "(?i)\\b(token|secret|")
    for name, path in (("redaction removed", m1), ("project-boundary guard removed", m2), ("word boundary before the key name (the old A34 pattern)", m3)):
        caught = checks(path)
        if not caught:
            print(f"FAIL: mutant '{name}' survived: the tests cannot tell it from the real script")
            return 1
    print("ok: handoff_hook: PreCompact/PostCompact/SessionStart behave as documented; 3 mutants caught; live firing by Claude Code not tested")
    return 0


if __name__ == "__main__":
    sys.exit(main())
