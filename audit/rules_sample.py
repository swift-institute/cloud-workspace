#!/usr/bin/env python3
"""Part 2: per-rule counts and a seeded random sample of 20 findings per rule, with source context, from the runner's
location-level output ($LINT_OUT) and the runner's inventory ($AUDIT_WORK/inventory.json).
Writes audit/data/rules-counts.json (public) and $AUDIT_WORK/rule-samples/<rule>.md for judging (private packages'
findings are sampled too, since judging needs them, but their text never reaches audit/)."""
import collections, glob, json, os, random, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINT = os.environ["LINT_OUT"]; WORK = os.environ["AUDIT_WORK"]
inv = json.load(open(os.path.join(WORK, "inventory.json")))
bundles = {b["bundle"]: set(b["rules"]) for b in inv["bundles"]}
rules = sorted(set().union(*bundles.values()))
private = set(l.strip() for l in open(os.path.join(ROOT, "private-repos.txt")) if l.strip())

findings = collections.defaultdict(list); supp = collections.Counter(); pk = collections.defaultdict(set)
repair = collections.defaultdict(collections.Counter); sev = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(os.path.join(LINT, "*.json"))):
    repo = os.path.basename(f)[:-5].replace("__", "/", 1)
    d = json.load(open(f))
    for x in d.get("findings", []):
        x["repo"] = repo; findings[x["rule"]].append(x); pk[x["rule"]].add(repo); sev[x["rule"]][x["severity"]] += 1
    for s in d.get("suppressions", []):
        supp[s["rule"]] += 1
    for p in d.get("repairProposals", []):
        repair[p["rule"]][p["proposal"]["status"]] += 1

counts = []
for r in rules:
    counts.append({"rule": r, "bundles": sorted(b for b, rs in bundles.items() if r in rs), "findings": len(findings[r]),
                   "packages": len(pk[r]), "suppressions": supp[r], "severity": dict(sev[r]), "repairs": dict(repair[r])})
json.dump(counts, open(os.path.join(ROOT, "audit", "data", "rules-counts.json"), "w"), indent=1)

out = os.path.join(WORK, "rule-samples"); os.makedirs(out, exist_ok=True)


def context(repo, path, line):
    path = path.removeprefix("./")
    try:
        if path == "Package.swift":
            text = subprocess.run(["git", "-C", os.path.join(ROOT, "repos", repo), "show", ":Package.swift"], capture_output=True, text=True).stdout
        else:
            text = open(os.path.join(ROOT, "repos", repo, path)).read()
    except Exception:
        return "(unreadable)"
    L = text.split("\n"); a = max(0, line - 5); b = min(len(L), line + 4)
    return "\n".join("%s%5d  %s" % (">" if i + 1 == line else " ", i + 1, L[i]) for i in range(a, b))


for r in rules:
    fs = findings[r]
    rnd = random.Random("coenttb/work#242:" + r)
    sample = fs if len(fs) <= 20 else rnd.sample(fs, 20)
    with open(os.path.join(out, r.replace(" ", "_") + ".md"), "w") as f:
        f.write("# %s: %d findings in %d packages, %d suppressions\n\n" % (r, len(fs), len(pk[r]), supp[r]))
        for i, x in enumerate(sample, 1):
            f.write("## %d. %s %s:%s (%s)%s\n%s\n```swift\n%s\n```\n\n" % (i, x["repo"], x.get("filePath"), x.get("line"), x["severity"],
                    "  [PRIVATE: do not quote]" if x["repo"] in private else "", x["message"], context(x["repo"], x.get("filePath", ""), x.get("line", 0))))
print(len(rules), "rules;", sum(1 for c in counts if c["findings"]), "with findings;", sum(c["findings"] for c in counts), "findings")
