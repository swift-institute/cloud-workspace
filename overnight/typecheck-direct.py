#!/usr/bin/env python3
"""Writes one argument file per changed Sources target (swiftc -typecheck, the package's traits, -warnings-as-errors,
the root build's modules), for overnight/typecheck-direct.sh to run with swiftc directly: typecheck-tests.py's
in-process runs miss errors (cause not found). Usage: overnight/typecheck-direct.py <out-dir> [package ...]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = "/home/user/scratch-warn/out/Products/Debug-linux-x86_64"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
pkgs = sys.argv[2:] or subprocess.run([os.path.join(root, "overnight/changed.sh")], capture_output=True, text=True, cwd=root).stdout.split()
FLAGS = ["-swift-version", "6", "-parse-as-library", "-strict-memory-safety", "-I", P, "-Xcc", "-I" + P + "/include",
         "-enable-testing", "-warnings-as-errors", "-D", "DEBUG", "-D", "SWIFT_PACKAGE", "-enable-experimental-feature", "Lifetimes"] + sum(
    (["-enable-upcoming-feature", f] for f in ["ExistentialAny", "InternalImportsByDefault", "MemberImportVisibility",
     "NonisolatedNonsendingByDefault", "InferIsolatedConformances"]), [])
n = 0
for p in pkgs:
    d = os.path.join(root, "repos", p)
    try:
        dump = json.load(open(os.path.join("/home/user/dumps", p.replace("/", "__", 1) + ".json")))
    except Exception:
        continue
    traits = sum((["-D", t["name"]] for t in dump.get("traits") or [] if t["name"] != "default"), [])
    changed = subprocess.run(["git", "-C", d, "diff", "--name-only", "origin/main", "--", "Sources"], capture_output=True, text=True).stdout.split("\n")
    targets = [(t["name"], t.get("path") or "Sources/" + t["name"]) for t in dump["targets"] if t["type"] in ("regular", "executable")]
    for name, tp in targets:
        if not any(c.startswith(tp.rstrip("/") + "/") and c.endswith(".swift") for c in changed): continue
        nested = [x for _, x in targets if x != tp and x.startswith(tp.rstrip("/") + "/")]
        files = [f for f in glob.glob(os.path.join(d, tp, "**/*.swift"), recursive=True) if not any(f.startswith(os.path.join(d, x) + "/") for x in nested)]
        if not files: continue
        mod = re.sub(r"[^A-Za-z0-9_]", "_", name)
        args = ["-typecheck"] + traits + ["-module-name", mod, "-package-name", os.path.basename(p).replace("-", "_")] + FLAGS + files
        open(os.path.join(out, f"{p.replace('/', '__')}__{mod}.args"), "w").write("\0".join(args))
        n += 1
print(n, "targets")
