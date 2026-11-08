#!/usr/bin/env python3
"""Formats every .swift file changed since origin/main with the Institute swift-format configuration, when the file's
origin/main version is already stable under it (a new file: when an origin/main file in its directory is). Commits per
package. Usage: overnight/format-changed.py [package ...]"""
import concurrent.futures as cf, os, subprocess, sys, tempfile
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = "/home/user/tools/swift-format.json"
def git(d, *a): return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
def fmt(text):
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, dir="/home/user/tools/tmp") as f:
        f.write(text); name = f.name
    try:
        r = subprocess.run(["swift-format", "format", "--configuration", CONFIG, name], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    finally: os.unlink(name)
def stable(text): return text is not None and fmt(text) == text
def work(p):
    d = os.path.join(root, "repos", p); n = 0
    files = [f for f in git(d, "diff", "--name-only", "--no-renames", "origin/main", "HEAD").stdout.split("\n") if f.endswith(".swift") and os.path.exists(os.path.join(d, f))]
    dircache = {}
    for f in files:
        o = git(d, "show", f"origin/main:{f}")
        if o.returncode == 0: ok = stable(o.stdout)
        else:
            dd = os.path.dirname(f)
            if dd not in dircache:
                sib = [x for x in git(d, "ls-tree", "--name-only", f"origin/main:{dd}").stdout.split("\n") if x.endswith(".swift")][:2]
                dircache[dd] = bool(sib) and all(stable(git(d, "show", f"origin/main:{dd}/{x}").stdout) for x in sib)
            ok = dircache[dd]
        if not ok: continue
        cur = open(os.path.join(d, f)).read(); new = fmt(cur)
        if new and new != cur: open(os.path.join(d, f), "w").write(new); n += 1
    if n: git(d, "commit", "-qam", "swift-format with the Institute configuration on files this session changed (coenttb/work#242)")
    return p, n
pkgs = sys.argv[1:] or [l for l in subprocess.run([root + "/overnight/changed.sh"], capture_output=True, text=True, cwd=root).stdout.split()]
tot = 0
with cf.ThreadPoolExecutor(4) as ex:
    for p, n in ex.map(work, pkgs):
        if n: print(p, n); tot += n
print("formatted", tot, file=sys.stderr)
