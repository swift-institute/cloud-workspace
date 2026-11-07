#!/usr/bin/env python3
"""Type-checks test directories against the modules the root build produced: `swiftc -typecheck` with the
Institute's common settings and the package's own -package-name, so `package` declarations are visible. Compiles
nothing. Checks every Tests/<D>/ directory with Swift files changed since origin/main in the packages given (or all
checkouts with changes). Prints one line per failing directory and its first errors.

    overnight/typecheck-tests.py [-j N] [package ...]"""
import concurrent.futures, glob, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = "/home/user/scratch-warn/out/Products/Debug-linux-x86_64"
argv = sys.argv[1:]
j = 4
if "-j" in argv:
    k = argv.index("-j"); j = int(argv[k + 1]); del argv[k:k + 2]
FLAGS = ["-swift-version", "6", "-parse-as-library", "-strict-memory-safety", "-I", P, "-Xcc", "-I" + P + "/include",
         "-enable-testing", "-D", "DEBUG", "-D", "SWIFT_PACKAGE",
         "-enable-experimental-feature", "Lifetimes"] + sum((["-enable-upcoming-feature", f] for f in
         ["ExistentialAny", "InternalImportsByDefault", "MemberImportVisibility", "NonisolatedNonsendingByDefault",
          "InferIsolatedConformances"]), [])
pkgs = argv or [l.strip() for l in subprocess.run([os.path.join(root, "overnight/changed.sh")], capture_output=True,
                                                  text=True, cwd=root).stdout.split() if l.strip()]
jobs = []
for p in pkgs:
    d = os.path.join(root, "repos", p)
    changed = subprocess.run(["git", "-C", d, "diff", "--name-only", "origin/main", "--", "Tests"],
                             capture_output=True, text=True).stdout.split("\n")
    dirs = sorted({"/".join(c.split("/")[:2]) for c in changed if c.endswith(".swift")})
    for t in dirs:
        jobs.append((p, t))


def check(job):
    p, t = job
    d = os.path.join(root, "repos", p)
    files = glob.glob(os.path.join(d, t, "**/*.swift"), recursive=True)
    if not files: return job, 0, ""
    mod = re.sub(r"[^A-Za-z0-9_]", "_", os.path.basename(t))
    r = subprocess.run(["swiftc", "-typecheck", "-module-name", mod, "-package-name", os.path.basename(p).replace("-", "_")]
                       + FLAGS + files, capture_output=True, text=True)
    errs = [l for l in r.stderr.split("\n") if re.search(r"\.swift:\d+:\d+: error:", l)]
    return job, r.returncode, "\n".join(errs[:3])


bad = 0
with concurrent.futures.ThreadPoolExecutor(j) as pool:
    for (p, t), rc, errs in pool.map(check, jobs):
        if rc:
            bad += 1
            print(f"FAIL {p}|{t}\n{errs}", flush=True)
print(f"{len(jobs)} test directories, {bad} failing", file=sys.stderr)
