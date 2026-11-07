#!/usr/bin/env python3
"""Renames files that `extension file naming` names exactly ("must be named 'X' for the conformance it adds"),
with git mv, in Sources/ only (test files can locate snapshots by their own path). Skips when the new name exists
anywhere in the same target (Swift requires unique file names per module).

    overnight/rename-extension-files.py <lint-dir> [--tier T ...] [--dry-run]"""
import argparse, glob, json, os, re, subprocess

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern = re.compile(r"extension file '([^']+)' must be named '([^']+)' for the conformance it adds")


def tier(p):
    o = p.split("/")[0]
    return {"swift-atoms": "atoms", "swift-molecules": "molecules", "swift-compositions": "compositions",
            "swift-institute": "compositions", "coenttb": "coenttb"}.get(o, "standards")


a = argparse.ArgumentParser()
a.add_argument("lint")
a.add_argument("--tier", action="append")
a.add_argument("--dry-run", action="store_true")
args = a.parse_args()
n = 0
for f in sorted(glob.glob(os.path.join(args.lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if args.tier and tier(p) not in args.tier:
        continue
    repo = os.path.join(root, "repos", p)
    for x in json.load(open(f))["findings"]:
        m = pattern.search(x.get("message", ""))
        if x["rule"] != "extension file naming" or not m:
            continue
        rel = x["fileID"][2:]
        parts = rel.split("/")
        if parts[0] != "Sources" or os.path.basename(rel) != m[1] or m[2].startswith("_"):
            continue
        old = os.path.join(repo, rel)
        new = os.path.join(os.path.dirname(old), m[2])
        target = os.path.join(repo, *parts[:2])
        if not os.path.exists(old):
            continue
        clash = [q for q in glob.glob(os.path.join(glob.escape(target), "**", "*.swift"), recursive=True)
                 if os.path.basename(q) == m[2]]
        if clash:
            print("SKIP exists", p, rel, "->", m[2])
            continue
        n += 1
        print(p, rel, "->", m[2])
        if not args.dry_run:
            subprocess.run(["git", "-C", repo, "mv", rel, os.path.relpath(new, repo)], check=True)
print(n, "renames")
