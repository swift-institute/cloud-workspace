#!/usr/bin/env python3
"""Counts the current compiler warnings from every .dia file under a scratch path, for source files in repos/.
Unique by file, line, column and message. Prints JSON like count-warnings.py.

    overnight/count-dia.py [/home/user/scratch-warn] > counts.json

A kind is the diagnostic group (from the documentation URL the compiler attaches), else the message with quoted
names blanked. HTML @deprecated warnings are their own kind, "html-deprecated": they stay by decision."""
import collections, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dia

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repos = os.path.join(root, "repos")
scratch = sys.argv[1] if len(sys.argv) > 1 else "/home/user/scratch-warn"


def tier(p):
    o = p.split("/")[0]
    return {"swift-atoms": "atoms", "swift-molecules": "molecules", "swift-compositions": "compositions",
            "swift-institute": "compositions", "coenttb": "coenttb"}.get(o, "standards")


def html_deprecation(file, message):
    return "is deprecated" in message and ("html" in file.lower()) and "/Sources/" in file


def kind(file, message, flag):
    if html_deprecation(file, message):
        return "html-deprecated"
    if flag:
        return flag.rstrip("/").split("/")[-1]
    k = re.sub(r"'[^']*'", "'_'", message)
    return re.sub(r"\d+", "N", k)[:120]


items = {}
for path in glob.glob(os.path.join(scratch, "**", "*.dia"), recursive=True):
    try:
        diags = dia.read(path)
    except Exception as error:
        print("unreadable", path, error, file=sys.stderr)
        continue
    for sev, file, line, col, message, flag in diags:
        if sev != "warning" or not file:
            continue
        real = os.path.realpath(file)
        rel = os.path.relpath(real, repos)
        if rel.startswith("..") or not os.path.exists(real):
            continue
        items[(rel, line, col, message)] = ("/".join(rel.split("/")[:2]), kind(rel, message, flag))

by_package = collections.Counter(p for p, _ in items.values())
by_kind = collections.Counter(k for _, k in items.values())
by_tier = collections.Counter(tier(p) for p, _ in items.values())
by_tier_kind = collections.defaultdict(collections.Counter)
for p, k in items.values():
    by_tier_kind[tier(p)][k] += 1
json.dump({
    "total": len(items),
    "html_deprecated": by_kind.get("html-deprecated", 0),
    "by_tier": dict(by_tier.most_common()),
    "by_kind": dict(by_kind.most_common()),
    "by_package": dict(by_package.most_common()),
    "by_tier_kind": {t: dict(c.most_common()) for t, c in by_tier_kind.items()},
    "items": [{"file": k[0], "line": k[1], "column": k[2], "message": k[3], "kind": v[1]} for k, v in sorted(items.items())],
}, sys.stdout, indent=1)
