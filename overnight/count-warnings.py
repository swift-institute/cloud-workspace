#!/usr/bin/env python3
"""Counts compiler warnings in build logs: unique by file, line, column and message, attributed to the checkout
the file belongs to. Prints JSON {"total", "by_tier", "by_package", "by_kind", "by_tier_kind", "items"}.

    overnight/count-warnings.py <log-dir> [> counts.json]

A kind is the diagnostic group when the compiler names one ([#Group]), else the message with quoted names blanked.
HTML @deprecated warnings are counted under their own kind, "html-deprecated", and stay by decision."""
import collections, glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
line = re.compile(r"^(/[^:\n]+?):(\d+):(\d+): warning: (.*)$")
group = re.compile(r"\s*\[#(\w+)\](?:\s*\(.*\))?$")


def tier(package):
    owner = package.split("/")[0]
    return {"swift-atoms": "atoms", "swift-molecules": "molecules", "swift-compositions": "compositions",
            "swift-institute": "compositions", "coenttb": "coenttb"}.get(owner, "standards")


def kind(message):
    g = group.search(message)
    base = group.sub("", message)
    if "deprecated" in base and re.search(r"HTML|html|element|attribute", base):
        if re.search(r"is deprecated: .*(HTML|element|attribute)", base, re.I):
            return "html-deprecated"
    if g:
        return g.group(1)
    k = re.sub(r"'[^']*'", "'_'", base)
    k = re.sub(r"\d+", "N", k)
    return k[:120]


items = {}
for log in sorted(glob.glob(os.path.join(sys.argv[1], "*.log"))):
    for text in open(log, encoding="utf8", errors="replace"):
        m = line.match(text.rstrip("\n"))
        if not m:
            continue
        path = os.path.realpath(m[1])
        rel = os.path.relpath(path, os.path.join(root, "repos"))
        if rel.startswith(".."):
            continue
        package = "/".join(rel.split("/")[:2])
        key = (rel, int(m[2]), int(m[3]), m[4])
        items[key] = package

by_package = collections.Counter(items.values())
by_kind = collections.Counter(kind(k[3]) for k in items)
by_tier = collections.Counter(tier(p) for p in items.values())
by_tier_kind = collections.defaultdict(collections.Counter)
for k, p in items.items():
    by_tier_kind[tier(p)][kind(k[3])] += 1
json.dump({
    "total": len(items),
    "by_tier": dict(by_tier.most_common()),
    "by_kind": dict(by_kind.most_common()),
    "by_package": dict(by_package.most_common()),
    "by_tier_kind": {t: dict(c.most_common()) for t, c in by_tier_kind.items()},
    "items": [{"file": k[0], "line": k[1], "column": k[2], "message": k[3], "kind": kind(k[3])} for k in sorted(items)],
}, sys.stdout, indent=1)
