#!/usr/bin/env python3
"""Drops a duplicate `import M` line when the same file also imports M with wider access (left by extension-file
merges), in files changed since origin/main. Usage: overnight/dedupe-imports.py [package ...]"""
import os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LV = {"private": 0, "fileprivate": 1, "internal": 2, "": 2, "package": 3, "public": 4, "@_exported": 5}
RX = re.compile(r"^(@_exported |(?:public|package|internal|fileprivate|private) )?import (\w+)\s*$")
pkgs = sys.argv[1:] or subprocess.run([root + "/overnight/changed.sh"], capture_output=True, text=True, cwd=root).stdout.split()
n = 0
for p in pkgs:
    d = os.path.join(root, "repos", p)
    for f in subprocess.run(["git", "-C", d, "diff", "--name-only", "origin/main"], capture_output=True, text=True).stdout.split("\n"):
        if not f.endswith(".swift") or not os.path.exists(os.path.join(d, f)): continue
        path = os.path.join(d, f); lines = open(path).read().split("\n")
        best = {}
        for l in lines:
            m = RX.match(l)
            if m: k = m.group(2); best[k] = max(best.get(k, -1), LV[(m.group(1) or "").strip()])
        out, seen = [], set()
        for l in lines:
            m = RX.match(l)
            if m:
                k = m.group(2); lv = LV[(m.group(1) or "").strip()]
                if lv < best[k] or k in seen: continue
                seen.add(k)
            out.append(l)
        if out != lines:
            open(path, "w").write("\n".join(out)); n += 1; print(p, f)
print(n, "files", file=sys.stderr)
