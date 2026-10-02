#!/usr/bin/env python3
"""
Benchmark for the dev-workflow skill. Same shape as agent-loop's bench/: a results file, a baseline that is recorded the first time a
suite appears and never overwritten silently, and a table in dev-workflow/references/benchmark.md generated from them.

  python3 tests/bench_skill.py            quick suites (a few seconds)
  python3 tests/bench_skill.py --full     also run the scanner stress harnesses (about 3 minutes)
  python3 tests/bench_skill.py --write-doc   regenerate the table in references/benchmark.md

The skill's real-model arms (does the skill change what an agent produces?) are not run here; they live in agent-loop's
test/stress/ab_skill.mjs and are gated behind AGENT_LOOP_REAL_MODEL_TESTS=1.
"""
import json
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(ROOT, "tests", "bench-results.json")
BASELINE = os.path.join(ROOT, "tests", "bench-baseline.json")
DOC = os.path.join(ROOT, "dev-workflow", "references", "benchmark.md")
START, END = "<!-- bench:table:start -->", "<!-- bench:table:end -->"

# id, title, unit, direction ("up" more is better, "down" less is better, "info" no direction), needs --full
SUITES = [
    ("skill-lines", "Length of SKILL.md (lines); shorter is better because long skills get skimmed", "lines", "down", False),
    ("skill-words", "Length of SKILL.md (words)", "words", "down", False),
    ("step8-rules", "One-line verification rules in Step 8", "rules", "info", False),
    ("references", "Reference files shipped with the skill", "files", "info", False),
    ("hook-tests", "Compaction-hook behaviours verified, including 2 mutants caught", "of 1", "up", False),
    ("scanner-stress", "Staged-file scanner: cases behaving correctly (secrets, destructive commands, encodings, allowlist abuse)", "of 68", "up", True),
    ("scanner-stress2", "Scanner: hook, push, CI and performance cases behaving correctly", "of 8", "up", True),
]


def git_short():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def measure(sid, full):
    skill = read(os.path.join(ROOT, "dev-workflow", "SKILL.md"))
    if sid == "skill-lines":
        return len(skill.splitlines()), None
    if sid == "skill-words":
        return len(skill.split()), None
    if sid == "step8-rules":
        step8 = skill.split("## Step 8", 1)[1].split("\n## ", 1)[0]
        return len(re.findall(r"^\d+\. \*\*", step8, re.M)), None
    if sid == "references":
        return len([f for f in os.listdir(os.path.join(ROOT, "dev-workflow", "references")) if f.endswith(".md")]), None
    if sid == "hook-tests":
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "handoff_hook_test.py")], capture_output=True, text=True)
        return (1 if p.returncode == 0 else 0), 1
    if sid in ("scanner-stress", "scanner-stress2"):
        script = "scan_stress.py" if sid == "scanner-stress" else "scan_stress2.py"
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "stress", script)], capture_output=True, text=True)
        m = re.search(r"(\d+)/(\d+) cases behaved correctly", p.stdout)
        if not m:
            raise SystemExit(f"{script}: could not read the score from its output")
        return int(m.group(1)), int(m.group(2))
    raise KeyError(sid)


def cell(v):
    if v is None:
        return "-"
    return f"{v['value']}/{v['max']}" if v.get("max") is not None else str(v["value"])


def change(direction, base, now):
    if not base or not now:
        return "-"
    d = now["value"] - base["value"]
    if d == 0:
        return "no change"
    if direction == "info":
        return f"{'+' if d > 0 else ''}{d}"
    better = d > 0 if direction == "up" else d < 0
    return f"{'+' if d > 0 else ''}{d} ({'better' if better else 'worse'})"


def log_ids(sid):
    path = os.path.join(ROOT, "dev-workflow", "references", "improvement-log.md")
    if not os.path.exists(path):
        return "-"
    ids = []
    for block in read(path).split("\n## ")[1:]:
        m = re.match(r"(SKILL-\d+)", block)
        s = re.search(r"^- \*\*Suites:\*\*\s*(.*)$", block, re.M)
        if m and s and sid in re.split(r"[,\s]+", s.group(1)):
            ids.append(m.group(1))
    return ", ".join(ids) or "-"


def render(results, baseline):
    rows = []
    for sid, title, unit, direction, _full in SUITES:
        b, n = baseline["suites"].get(sid), results["suites"].get(sid)
        rows.append(f"| `{sid}` | {title} | {cell(b)}{' @ ' + b['commit'] if b else ''} | {cell(n)} | {change(direction, b, n)} | {log_ids(sid)} |")
    return "\n".join([START, "| Suite | What it measures | First recorded | Now | Change | Why / how |", "|---|---|---|---|---|---|", *rows,
                      f"Latest run: commit `{results['commit']}`, {results['date']}. Baselines are the first value recorded for a suite and are not overwritten without a log entry.", END])


def main():
    args = sys.argv[1:]
    full = "--full" in args
    results = json.load(open(RESULTS)) if os.path.exists(RESULTS) else {"suites": {}}
    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {"suites": {}}
    commit = git_short()
    for sid, _t, _u, _d, needs_full in SUITES:
        if needs_full and not full:
            continue
        value, mx = measure(sid, full)
        results["suites"][sid] = {"value": value, "max": mx}
        print(f"{sid:16} {value}{'/' + str(mx) if mx is not None else ''}")
        if sid not in baseline["suites"]:
            baseline["suites"][sid] = {"value": value, "max": mx, "commit": commit, "date": str(date.today())}
            print(f"  baseline recorded for {sid} @ {commit}")
    results["commit"], results["date"] = commit, str(date.today())
    json.dump(results, open(RESULTS, "w"), indent=2); open(RESULTS, "a").write("\n")
    json.dump(baseline, open(BASELINE, "w"), indent=2); open(BASELINE, "a").write("\n")
    if "--write-doc" in args:
        doc = read(DOC)
        a, b = doc.index(START), doc.index(END)
        open(DOC, "w", encoding="utf-8").write(doc[:a] + render(results, baseline) + doc[b + len(END):])
        print("benchmark.md table regenerated")


if __name__ == "__main__":
    main()
