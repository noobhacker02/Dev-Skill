#!/usr/bin/env python3
"""Stress test for dev-workflow/scripts/check_staged.py (commit mode).

Each case stages one file in a throwaway git repo and checks whether the scanner blocks or allows it.
Payloads (fake keys, destructive commands) live in cases.json XOR-ed with 0x5A then base64-encoded, so
this repo's own hooks and CI gate (including TruffleHog, which decodes plain base64) don't flag the test data. FAIL = the scanner did the wrong thing (a hole or a false positive).
See docs/STRESS-TEST-REPORT.md.
"""
import base64, json, os, subprocess, sys, tempfile

XOR_KEY = 0x5A

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.join(HERE, "..", "..", "dev-workflow", "scripts", "check_staged.py")


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)


def new_repo():
    d = tempfile.mkdtemp(prefix="devskill-stress-")
    sh("git init -q && git config user.email t@example.com && git config user.name t && git commit -q --allow-empty -m init", d)
    return d


def decode(field):
    return bytes(c ^ XOR_KEY for c in base64.b64decode(field))


def run_case(case):
    name = decode(case["name"]).decode()
    fname = decode(case["file"]).decode()
    content = decode(case["content"])
    d = new_repo()
    path = os.path.join(d, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    sh("git add -A", d)
    r = subprocess.run([sys.executable, SCAN, "--mode=commit"], cwd=d, capture_output=True, text=True)
    blocked = r.returncode != 0
    ok = blocked == case["expect_block"]
    crash = " | CRASH" if "Traceback" in r.stdout + r.stderr else ""
    print(f"{'PASS' if ok else 'FAIL'} | {'block' if blocked else 'allow'} | want {'block' if case['expect_block'] else 'allow'} | {name}{crash}")
    return ok


if __name__ == "__main__":
    cases = json.load(open(os.path.join(HERE, "cases.json")))
    results = [run_case(c) for c in cases]
    print(f"\n{sum(results)}/{len(results)} cases behaved correctly")
    sys.exit(0 if all(results) else 1)
