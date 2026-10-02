#!/usr/bin/env python3
"""The generated table in references/benchmark.md must equal what tests/bench-results.json and bench-baseline.json produce,
the cheap measurements must equal an independent count, and the checks need controls (a changed number must change the table)."""
import copy
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_skill as b  # noqa: E402

results = json.load(open(b.RESULTS))
baseline = json.load(open(b.BASELINE))
doc = b.read(b.DOC)
fail = []


def expect(cond, msg):
    if not cond:
        fail.append(msg)


a, z = doc.index(b.START), doc.index(b.END)
expect(doc[a:z + len(b.END)] == b.render(results, baseline), "references/benchmark.md table is out of date: run `python3 tests/bench_skill.py --write-doc`")
for sid, _t, _u, _d, needs_full in b.SUITES:
    expect(sid in baseline["suites"], f"no baseline for {sid}")
    expect(sid in results["suites"], f"no result for {sid}")

# Independent counts: the benchmark's own measurements agree with a different way of counting.
skill = b.read(os.path.join(b.ROOT, "dev-workflow", "SKILL.md"))
expect(results["suites"]["skill-lines"]["value"] == len(skill.split("\n")) - (0 if skill.endswith("\n") else 0) - (1 if skill.endswith("\n") else 0) or
       results["suites"]["skill-lines"]["value"] == len(skill.splitlines()),
       "skill-lines in results does not match SKILL.md (results are stale: run the benchmark)")
step8 = skill.split("## Step 8", 1)[1].split("\n## ", 1)[0]
numbered = [l for l in step8.splitlines() if re.match(r"\d+\. \*\*", l)]
expect(results["suites"]["step8-rules"]["value"] == len(numbered), f"step8-rules {results['suites']['step8-rules']['value']} != {len(numbered)} numbered rules found")
nums = [int(re.match(r"(\d+)\.", l).group(1)) for l in numbered]
expect(nums == list(range(1, len(nums) + 1)), f"Step 8 rule numbers are not 1..N in order: {nums}")

# Every file named in SKILL.md's reference and script tables exists.
for rel in re.findall(r"`((?:references|scripts)/[A-Za-z0-9_./-]+)`", skill):
    expect(os.path.exists(os.path.join(b.ROOT, "dev-workflow", rel)), f"SKILL.md mentions {rel}, which does not exist")

# Controls
bumped = copy.deepcopy(results)
bumped["suites"]["skill-lines"]["value"] += 1
expect(b.render(bumped, baseline) != b.render(results, baseline), "control: the table ignores a changed number")
worse = copy.deepcopy(results); worse["suites"]["skill-lines"]["value"] = baseline["suites"]["skill-lines"]["value"] + 5
expect("(worse)" in b.render(worse, baseline), "control: a longer SKILL.md is not shown as worse")

# Freshness: results produced no more than 25 commits ago (skipped when the commit is not in this clone)
try:
    subprocess.run(["git", "cat-file", "-e", results["commit"] + "^{commit}"], cwd=b.ROOT, check=True, capture_output=True)
    n = int(subprocess.run(["git", "rev-list", "--count", f"{results['commit']}..HEAD"], cwd=b.ROOT, capture_output=True, text=True).stdout.strip())
    expect(n <= 25, f"tests/bench-results.json is {n} commits old: re-run the benchmark")
except subprocess.CalledProcessError:
    print("note: results freshness not checked (commit not in this clone)")

for f in fail:
    print("FAIL:", f)
if fail:
    sys.exit(1)
print("ok: skill benchmark table matches its results; counts cross-checked; controls hold")
