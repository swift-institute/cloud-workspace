#!/usr/bin/env python3
"""Counts runner findings from lint-all.sh output: by tier, package, rule and severity; also suppressions and
unmeasured observations as the runner reports them. Prints JSON."""
import collections, glob, json, os, sys

def tier(p):
    o = p.split("/")[0]
    return {"swift-atoms": "atoms", "swift-molecules": "molecules", "swift-compositions": "compositions",
            "swift-institute": "compositions", "coenttb": "coenttb"}.get(o, "standards")

by_pkg, by_rule, by_tier, by_sev = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
by_tier_rule = collections.defaultdict(collections.Counter)
supp, unmeasured, failed, broken, items = collections.Counter(), collections.Counter(), [], [], []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    try:
        d = json.load(open(f))
    except Exception:
        broken.append(p); continue
    for x in d["findings"]:
        by_pkg[p] += 1; by_rule[x["rule"]] += 1; by_tier[tier(p)] += 1; by_sev[x.get("severity", "?")] += 1
        by_tier_rule[tier(p)][x["rule"]] += 1
        items.append({"package": p, "rule": x["rule"], "severity": x.get("severity"), "file": x.get("fileID"),
                      "line": x.get("line"), "message": x.get("message", "")[:300]})
    supp[p] = d["summary"].get("suppressions", 0)
    unmeasured[p] = d["summary"].get("unmeasuredObservations", 0)
    if d["summary"].get("failedControls"): failed.append(p)
json.dump({"total": sum(by_pkg.values()), "suppressions": sum(supp.values()),
           "unmeasured_observations": sum(unmeasured.values()), "failed_controls": failed, "unreadable": broken,
           "by_tier": dict(by_tier.most_common()), "by_severity": dict(by_sev), "by_rule": dict(by_rule.most_common()),
           "by_package": dict(by_pkg.most_common()),
           "by_tier_rule": {t: dict(c.most_common()) for t, c in by_tier_rule.items()},
           "items": items}, sys.stdout, indent=1)
