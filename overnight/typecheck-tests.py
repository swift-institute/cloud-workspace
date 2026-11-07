#!/usr/bin/env python3
"""With --sources: Sources/<D> directories instead (a library module against the others' built modules).
With --base FILE (lines p|Tests/D): checks those directories as they are on origin/main instead.
Type-checks test directories against the modules the root build produced: `swiftc -typecheck` with the
Institute's common settings and the package's own -package-name, so `package` declarations are visible. Compiles
nothing. Checks every Tests/<D>/ directory with Swift files changed since origin/main in the packages given (or all
checkouts with changes). Prints one line per failing directory and its first errors.

    overnight/typecheck-tests.py [-j N] [package ...]"""
import concurrent.futures, glob, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = "/home/user/scratch-warn/out/Products/Debug-linux-x86_64"
argv = sys.argv[1:]
j = 4
base = None
area = "Tests"
if "--sources" in argv:
    argv.remove("--sources"); area = "Sources"
if "--base" in argv:
    k = argv.index("--base"); base = argv[k + 1]; del argv[k:k + 2]
if "-j" in argv:
    k = argv.index("-j"); j = int(argv[k + 1]); del argv[k:k + 2]
FLAGS = ["-swift-version", "6", "-parse-as-library", "-strict-memory-safety", "-I", P, "-Xcc", "-I" + P + "/include",
         "-enable-testing"] + (["-warnings-as-errors"] if os.environ.get("WERROR") else []) + ["-D", "DEBUG", "-D", "SWIFT_PACKAGE",
         "-enable-experimental-feature", "Lifetimes"] + sum((["-enable-upcoming-feature", f] for f in
         ["ExistentialAny", "InternalImportsByDefault", "MemberImportVisibility", "NonisolatedNonsendingByDefault",
          "InferIsolatedConformances"]), [])
pkgs = argv or [l.strip() for l in subprocess.run([os.path.join(root, "overnight/changed.sh")], capture_output=True,
                                                  text=True, cwd=root).stdout.split() if l.strip()]
jobs = []
if base:
    jobs = [tuple(l.strip().split("|", 1)) for l in open(base) if "|" in l]
    pkgs = []
for p in pkgs:
    d = os.path.join(root, "repos", p)
    changed = subprocess.run(["git", "-C", d, "diff", "--name-only", "origin/main", "--", area],
                             capture_output=True, text=True).stdout.split("\n")
    dirs = sorted({"/".join(c.split("/")[:2]) for c in changed if c.endswith(".swift")})
    for t in dirs:
        jobs.append((p, t))


def check(job):
    p, t = job
    d = os.path.join(root, "repos", p)
    tmp = None
    if base:
        import tempfile
        tmp = tempfile.mkdtemp(dir="/tmp/claude-0")
        subprocess.run(f'git -C "{d}" archive origin/main "{t}" | tar -x -C "{tmp}"', shell=True, capture_output=True)
        d = tmp
    files = glob.glob(os.path.join(d, t, "**/*.swift"), recursive=True)
    if not files: return job, 0, ""
    mod = re.sub(r"[^A-Za-z0-9_]", "_", os.path.basename(t))
    r = subprocess.run(["swiftc", "-typecheck", "-module-name", mod, "-package-name", os.path.basename(p).replace("-", "_")]
                       + FLAGS + files, capture_output=True, text=True)
    if tmp: subprocess.run(["rm", "-rf", tmp])
    errs = [l for l in r.stderr.split("\n") if re.search(r"\.swift:\d+:\d+: error:", l)]
    return job, r.returncode, "\n".join(errs[:50])


bad = 0
with concurrent.futures.ThreadPoolExecutor(j) as pool:
    for (p, t), rc, errs in pool.map(check, jobs):
        if rc:
            bad += 1
            print(f"FAIL {p}|{t}\n{errs}", flush=True)
print(f"{len(jobs)} test directories, {bad} failing", file=sys.stderr)
