#!/usr/bin/env python3
"""Drives the root build with tests to green: builds, and for each failing file under repos/<o>/<n>/Tests/<T>/,
reverts that test target's files changed since origin/main (and commits the revert) when the target has changes,
else lists the target in overnight/tests-fallback.txt (a failure outside the batch: traits, graph) and regenerates.
A failure in Sources is reported and stops the loop. Repeats until green or --max rounds.

    overnight/root-green.py [--max N]"""
import os, re, subprocess, sys, time

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 8
LOG = "/home/user/logs/roottests.log"
ansi = re.compile(r"\x1b\[[0-9;]*m")
for rnd in range(MAX):
    s = time.time()
    with open(LOG, "w") as f:
        rc = subprocess.run(["swift", "build", "--build-tests", "-j", "3", "--scratch-path", "/home/user/scratch-warn"],
                            stdout=f, stderr=subprocess.STDOUT).returncode
    print(f"round {rnd} rc={rc} {int(time.time() - s)}s", flush=True)
    if rc == 0:
        print("GREEN"); sys.exit(0)
    text = ansi.sub("", open(LOG, errors="replace").read())
    files = sorted(set(re.findall(r"(repos/[^:\n]+?\.swift):\d+:\d+: error:", text)))
    if not files:
        print("failed without a file error:", text[-1500:]); sys.exit(1)
    regen = False
    for f in files:
        m = re.match(r"repos/([^/]+/[^/]+)/(Tests/[^/]+)/", f)
        if not m:
            print("SOURCES FAILURE", f); sys.exit(1)
        pkg, tdir = "repos/" + m[1], m[2]
        changed = subprocess.run(["git", "-C", pkg, "diff", "--name-only", "origin/main", "--", tdir],
                                 capture_output=True, text=True).stdout.split("\n")
        changed = [c for c in changed if c]
        if changed:
            subprocess.run(["git", "-C", pkg, "checkout", "origin/main", "--", tdir], check=True)
            subprocess.run(["git", "-C", pkg, "commit", "-qm",
                            f"Revert this session's changes to {tdir}: they broke the root test build (coenttb/work#242)"])
            print("reverted", pkg, tdir, len(changed), "files", flush=True)
        else:
            # The target's name: the testTarget whose path is this directory.
            pm = re.search(r'\.testTarget\(name: "([^"]+)"[^\n]*path: "' + re.escape(pkg + "/" + tdir) + '"', open("Package.swift").read())
            name = pm[1] if pm else os.path.basename(tdir)
            with open("overnight/tests-fallback.txt", "a") as fb:
                fb.write(f"{pkg}|{name}\n")
            regen = True
            print("fallback", pkg, name, flush=True)
    if regen:
        subprocess.run(["./generate.py"], check=True, stdout=subprocess.DEVNULL)
print("not green after", MAX, "rounds"); sys.exit(1)
