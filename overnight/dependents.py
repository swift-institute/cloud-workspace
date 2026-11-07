#!/usr/bin/env python3
"""Prints the given packages plus their direct dependents (packages whose path-dependency manifest names them).

    overnight/dependents.py owner/name [...]"""
import glob, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
deps = {}
for m in glob.glob(os.path.join(root, "repos/*/*/Package.swift")):
    p = "/".join(m.split("/")[-3:-1]); d = os.path.dirname(m)
    deps[p] = {"/".join(os.path.normpath(os.path.join(d, x)).split("/")[-2:])
               for x in re.findall(r'\.package\(\s*(?:name:\s*"[^"]*",\s*)?path:\s*"([^"]+)"', open(m).read())}
want = set(sys.argv[1:])
print("\n".join(sorted(want | {p for p, ds in deps.items() if ds & want})))
