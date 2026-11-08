#!/usr/bin/env python3
"""For each changed repository: is every library and test target's module in the root build's products newer than
the repository's last commit? Targets the root package can't take (tests-skipped.json), executables, macros and
plugins are left out. Prints `pass <pkg>` or `hold <pkg> <reason>`. Usage: overnight/verified-repos.py [package ...]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = "/home/user/scratch-warn/out/Products/Debug-linux-x86_64"
skipped = json.load(open(os.path.join(root, "tests-skipped.json")))
skipnames = set()
for x in (skipped if isinstance(skipped, list) else skipped.get("skipped", skipped)):
    skipnames.add(json.dumps(x) if not isinstance(x, (str, dict)) else (x if isinstance(x, str) else (x.get("package", "") + "|" + x.get("target", x.get("name", "")))))
def skip(p, t): return any(t in s and (p.split("/")[1] in s) for s in skipnames)
pkgs = sys.argv[1:] or subprocess.run([root + "/overnight/changed.sh"], capture_output=True, text=True, cwd=root).stdout.split()
for p in pkgs:
    d = os.path.join(root, "repos", p)
    last = int(subprocess.run(["git", "-C", d, "log", "-1", "--format=%ct"], capture_output=True, text=True).stdout.strip())
    try: dump = json.load(open(os.path.join("/home/user/dumps", p.replace("/", "__", 1) + ".json")))
    except Exception: print("hold", p, "no manifest dump"); continue
    bad = []
    for t in dump["targets"]:
        if t["type"] not in ("regular", "test"): continue
        n = t["name"]
        if re.search(r"Macro|Plugin", n) or skip(p, n): continue
        mod = re.sub(r"[^A-Za-z0-9_]", "_", n)
        f = glob.glob(os.path.join(P, mod + ".swiftmodule", "*.swiftmodule"))
        if not f: bad.append(n + " (not built)"); continue
        if os.path.getmtime(f[0]) < last: bad.append(n + " (built before last change)")
    print(("hold " + p + " root build: " + "; ".join(bad[:3]) + (" …" if len(bad) > 3 else "")) if bad else ("pass " + p))
