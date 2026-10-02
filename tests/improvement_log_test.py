#!/usr/bin/env python3
"""dev-workflow/references/improvement-log.md: every entry complete, ids unique and increasing, suites exist, Measured has a number or a reason.
Controls: each defect, injected into a copy, must be reported."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_skill as b  # noqa: E402

FIELDS = ["Problem", "Why it matters", "Change (how)", "Measured", "Cost / trade-off", "Suites", "Skill impact", "Follow-ups"]
PATH = os.path.join(b.ROOT, "dev-workflow", "references", "improvement-log.md")
KNOWN = [s[0] for s in b.SUITES]


def parse(md):
    out = []
    heads = list(re.finditer(r"^## (SKILL-\d+) · ([^·\n]+?) · (.+)$", md, re.M))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        body = md[h.end():end]
        fields = {}
        for f in FIELDS:
            m = re.search(r"^- \*\*" + re.escape(f) + r":\*\*\s*([\s\S]*?)(?=^- \*\*|\n## |\Z)", body, re.M)
            fields[f] = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
        out.append((h.group(1), h.group(2).strip(), fields))
    return out


def validate(md):
    problems, seen, last = [], set(), 0
    entries = parse(md)
    if not entries:
        problems.append("no entries")
    for eid, date, fields in entries:
        n = int(eid.split("-")[1])
        if eid in seen:
            problems.append(f"{eid}: duplicate id")
        seen.add(eid)
        if n <= last:
            problems.append(f"{eid}: ids must increase")
        last = n
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) and date != "backfilled":
            problems.append(f"{eid}: date must be YYYY-MM-DD or backfilled, got {date!r}")
        for f in FIELDS:
            if not fields[f]:
                problems.append(f'{eid}: missing or empty field "{f}"')
        m = fields["Measured"]
        if m and not re.search(r"\d", m) and "not measurable because" not in m.lower():
            problems.append(f'{eid}: "Measured" has no number and no "not measurable because"')
        s = fields["Suites"]
        if s and s.lower() != "none":
            for suite in re.split(r"[,\s]+", s):
                if suite and suite not in KNOWN:
                    problems.append(f'{eid}: unknown benchmark suite "{suite}"')
    return problems


md = open(PATH, encoding="utf-8").read()
problems = validate(md)
for p in problems:
    print("FAIL:", p)
if problems:
    sys.exit(1)
entries = parse(md)
controls = [
    (re.sub(r"(## SKILL-001[\s\S]*?)- \*\*Why it matters:\*\*", r"\1- **Why:**", md, count=1), "Why it matters"),
    (md.replace("- **Suites:** scanner-stress, scanner-stress2", "- **Suites:** nope", 1), "unknown benchmark suite"),
    (md.replace("- **Measured:** 398 -> 279 lines (285 after three more rules were added later).", "- **Measured:** shorter.", 1), "Measured"),
    (md.replace("## SKILL-002", "## SKILL-001", 1), "duplicate"),
    (md.replace("· backfilled · The staged", "· someday · The staged", 1), "date must be"),
]
for mutated, needle in controls:
    got = validate(mutated)
    if not any(needle in p for p in got):
        print(f"FAIL: control not caught: {needle}")
        sys.exit(1)
print(f"ok: skill improvement log: {len(entries)} complete entries; {len(controls)} controls caught")
