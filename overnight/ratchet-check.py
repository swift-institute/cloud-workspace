#!/usr/bin/env python3
"""Pre-push gate: no repository may end with any rule's count above its limit in institute's ratchet table
(the published CI gate goes red otherwise). Reads lint-all.sh output for the packages to push.

    overnight/ratchet-check.py <lint-dir> [package ...]

Prints each package|rule|count>limit over its limit and exits 1 if any."""
import collections, glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
table = os.path.join(root, "repos/swift-institute/institute/Sources/Institute Command/Institute.CI.Command.Source.Ratchet+limits.swift")
limits = {}
for line in open(table):
    m = re.fullmatch(r"\s*([^|\s]+)\|([^|]+)\|(\d+)\n?", line)
    if m:
        limits[(m[1], m[2])] = int(m[3])
lint, only = sys.argv[1], set(sys.argv[2:])
over = []
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    counts = collections.Counter(x["rule"] for x in json.load(open(f))["findings"])
    for r, n in sorted(counts.items()):
        if n > limits.get((p, r), 0):
            over.append(f"{p}|{r}|{n}>{limits.get((p, r), 0)}")
print("\n".join(over))
print(f"{len(over)} over the limit", file=sys.stderr)
sys.exit(1 if over else 0)
