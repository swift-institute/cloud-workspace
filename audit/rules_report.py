#!/usr/bin/env python3
"""Renders audit/data/rules-judged.json (counts from rules_sample.py plus each rule's judged sample) as the table in rules-table.md."""
import json, os
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit", "data")
rs = json.load(open(os.path.join(D, "rules-judged.json")))
order = {"remove": 0, "fix": 1, "merge": 2, "split": 3, "keep": 4}
with open(os.path.join(D, "..", "rules-table.md"), "w") as f:
    f.write("| Rule | Bundles | Findings | Pkgs | Supp. | Sample real/false | FP rate | Repair | Verdict | Reason / defect |\n|---|---|---|---|---|---|---|---|---|---|\n")
    for r in sorted(rs, key=lambda r: (order.get(r.get("verdict"), 9), -r["findings"])):
        n = r.get("sampled", 0)
        fp = "%d%%" % round(100 * r.get("false", 0) / n) if n else "-"
        why = (r.get("defect") or r.get("reason") or "").replace("|", "/").replace("\n", " ")
        f.write("| %s | %s | %d | %d | %d | %s | %s | %s | **%s** | %s |\n" % (
            r["rule"], ", ".join(b[0] for b in r["bundles"]), r["findings"], r["packages"], r["suppressions"],
            "%d/%d" % (r.get("real", 0), r.get("false", 0)) if n else "-", fp,
            (r.get("repair") or "none").replace("|", "/")[:90], r.get("verdict", "?"), why[:260]))
