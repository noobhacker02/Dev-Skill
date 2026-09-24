#!/usr/bin/env python3
"""Stress test for check_staged.py beyond single staged files: push mode, renames, allowlist abuse,
CI self-bypass, --no-verify, and performance. FAIL = hole. See docs/STRESS-TEST-REPORT.md."""
import base64, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCAN = os.path.join(ROOT, "dev-workflow", "scripts", "check_staged.py")
INSTALL = os.path.join(ROOT, "dev-workflow", "scripts", "install-hooks.sh")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
b = lambda s: base64.b64decode(s).decode()
AWS_LINE = b("az0iQUtJQUlPU0ZPRE5ON0FCQ0RFRkciCg==")          # fake AWS key id assignment
RM_ROOT = b("b3Muc3lzdGVtKCJybSAtcmYgLyIpCg==")              # os.system(<rm recursive root>)
DROP = b("RFJPUCBUQUJMRSBsZWdhY3k7Cg==")                    # drop-table statement for a legacy table
results = []


def sh(c, cwd):
    return subprocess.run(c, cwd=cwd, shell=True, capture_output=True, text=True)


def repo():
    d = tempfile.mkdtemp(prefix="devskill-stress2-")
    sh("git init -q -b main && git config user.email t@example.com && git config user.name t && git commit -q --allow-empty -m init", d)
    return d


def head(d):
    return sh("git rev-parse HEAD", d).stdout.strip()


def scan(d, *args, script=SCAN):
    t = time.time()
    r = subprocess.run([sys.executable, script, *args], cwd=d, capture_output=True, text=True)
    return r.returncode, round(time.time() - t, 2)


def rep(name, rc, want_block):
    ok = (rc != 0) == want_block
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {'block' if rc else 'allow'} | want {'block' if want_block else 'allow'} | {name}")


def write(d, rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text)


# 1. push mode: key added in one commit, removed in the next -> still in pushed history
d = repo(); base = head(d)
write(d, "a.py", AWS_LINE); sh("git add -A && git commit -qm add --no-verify", d)
write(d, "a.py", "k = None\n"); sh("git add -A && git commit -qm rm --no-verify", d)
rep("PUSH: secret added in commit 1, removed in commit 2 (still in history)", scan(d, "--mode=push", f"{base}..{head(d)}")[0], True)

# 2. push mode with a range git can't resolve -> must fail closed
rep("PUSH: unknown remote sha (git diff errors)", scan(d, "--mode=push", f"{'de' * 20}..{head(d)}")[0], True)

# 3. rename a file to .env
d = repo(); write(d, "settings", "SECRET=abc\n"); sh("git add -A && git commit -qm s --no-verify", d)
sh("git mv settings .env", d)
rep("COMMIT: git mv settings .env (rename)", scan(d, "--mode=commit")[0], True)

# 4. allowlist self-approval in the same commit
d = repo(); write(d, ".devskill-allowlist", ".*\n"); write(d, "a.py", AWS_LINE + RM_ROOT); sh("git add -A", d)
rep("COMMIT: same commit adds .devskill-allowlist '.*' + secret", scan(d, "--mode=commit")[0], True)

# 5. first push of a branch rescans the whole tree -> false positive on an old, reviewed migration
d = repo(); write(d, "migrations/001_down.sql", DROP); sh("git add -A && git commit -qm m --no-verify", d)
sh("git checkout -qb feature && echo x >> README && git add -A && git commit -qm readme --no-verify", d)
rep("PUSH: new branch touching only README, old migration in repo (false positive)", scan(d, "--mode=push", f"{EMPTY_TREE}..{head(d)}")[0], False)

# 6. CI gate runs the PR's own copy of the scanner
d = repo(); os.makedirs(os.path.join(d, ".githooks")); sh(f"cp '{SCAN}' .githooks/check_staged.py && git add -A && git commit -qm hooks --no-verify", d)
base = head(d)
write(d, ".githooks/check_staged.py", "import sys; print('No secrets'); sys.exit(0)\n"); write(d, "a.py", AWS_LINE)
sh("git add -A && git commit -qm pwn --no-verify", d)
rep("CI: PR replaces .githooks/check_staged.py with exit(0) + adds AWS key", scan(d, "--mode=push", f"{base}..{head(d)}", script=os.path.join(d, ".githooks/check_staged.py"))[0], True)

# 7. installed hook vs --no-verify
d = repo(); write(d, ".env", "X=1\n"); sh(f"bash '{INSTALL}'", d)
rep("HOOK: plain git commit of .env (hook installed)", sh("git add -A && git commit -qm env", d).returncode, True)
rep("HOOK: git commit --no-verify of .env (no record kept)", sh("git commit -qm env --no-verify", d).returncode, True)

# 8. performance
d = repo(); write(d, "big.sql", "".join(f"INSERT INTO t VALUES ({i}, 'row {i} padding padding');\n" for i in range(200000))); sh("git add -A", d)
print(f"PERF | 200k-line staged file: {scan(d, '--mode=commit')[1]}s")
d = repo(); write(d, "min.js", "UPD" + "ATE x SET " + "a" * 5_000_000 + "\n"); sh("git add -A", d)
print(f"PERF | 5MB single-line file: {scan(d, '--mode=commit')[1]}s")

print(f"\n{sum(results)}/{len(results)} cases behaved correctly")
sys.exit(0 if all(results) else 1)
