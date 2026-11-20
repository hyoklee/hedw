#!/usr/bin/env python3
"""Check every number in <run>/interpretation.md against the run's own files.

A number counts as supported if it appears (as written, or rounded from a value
in summary.json / cities.csv / anomalous_days.csv / city_years.csv to the same
number of decimals) in those files. Years, list markers and section numbers are
ignored. Writes <run>/interpretation_check.json and prints the unsupported ones.
usage: check_numbers.py <run_dir>"""
import json, os, re, sys

run = sys.argv[1]
text = open(os.path.join(run, "interpretation.md")).read()
src = ""
for f in ["summary.json", "cities.csv", "anomalous_days.csv", "city_years.csv"]:
    p = os.path.join(run, f)
    if os.path.exists(p):
        src += open(p).read() + "\n"
vals = set()
for tok in re.findall(r"-?\d+(?:\.\d+)?", src):
    vals.add(tok.lstrip("-"))
    if "." in tok:
        x = abs(float(tok))
        for d in range(0, 5):
            vals.add(f"{x:.{d}f}")
nums = re.findall(r"(?<![\w.-])-?\d[\d,]*(?:\.\d+)?", text)
checked, bad = [], []
for n in nums:
    v = n.replace(",", "").lstrip("-")
    if re.fullmatch(r"(19|20)\d\d", v) or (re.fullmatch(r"\d", v)):
        continue  # years, small integers (section numbers, list items, lags)
    ok = v in vals or (v.endswith(".0") and v[:-2] in vals)
    checked.append(n)
    if not ok:
        bad.append(n)
res = {"numbers_checked": len(checked), "unsupported": bad, "supported_frac": round(1 - len(bad) / max(1, len(checked)), 3)}
json.dump(res, open(os.path.join(run, "interpretation_check.json"), "w"), indent=1)
print(f"numbers checked {len(checked)}, unsupported {len(bad)}: {bad[:30]}")
