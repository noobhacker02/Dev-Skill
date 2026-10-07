#!/usr/bin/env python3
"""
The scanner exists as copies: the skill's own (dev-workflow/scripts/check_staged.py, the one a project installs from), this repository's hook (.githooks/check_staged.py, which the CI gate extracts
from the base commit) and agent-loop's (agent-loop/.githooks/check_staged.py, a separate repository nested here and ignored, so it is compared only when it is checked out). A fix made in one and
not the others is a fix that does not protect the place it was made for: SKILL-012's marker fix reached agent-loop and the skill but not this repository's own hook for four days.
This test fails when the copies differ, and shows that it can: a one-byte change in a copy is caught.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
COPIES = [
    ("skill", os.path.join(ROOT, "dev-workflow", "scripts", "check_staged.py"), True),
    ("repo hook", os.path.join(ROOT, ".githooks", "check_staged.py"), True),
    ("agent-loop", os.path.join(ROOT, "agent-loop", ".githooks", "check_staged.py"), False),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def differing(copies):
    """copies: list of (name, bytes). Returns the names that differ from the first one."""
    first = digest(copies[0][1])
    return [n for n, b in copies[1:] if digest(b) != first]


def main():
    present = []
    for name, path, required in COPIES:
        if not os.path.isfile(path):
            if required:
                print(f"FAIL: the {name} copy of the scanner is missing: {path}")
                return 1
            continue
        present.append((name, open(path, "rb").read()))
    drift = differing(present)
    if drift:
        print(f"FAIL: these copies of the scanner differ from the skill's: {', '.join(drift)}. Copy dev-workflow/scripts/check_staged.py over them.")
        return 1
    # the check has teeth: one changed byte is caught, and an identical copy is not
    base = present[0][1]
    if differing([("a", base), ("b", base + b"\n")]) != ["b"]:
        print("FAIL: the control cannot tell a changed copy from the original")
        return 1
    if differing([("a", base), ("b", base)]):
        print("FAIL: the control flags an identical copy")
        return 1
    print(f"ok: scanner copies identical ({', '.join(n for n, _ in present)}); a one-byte change is caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
