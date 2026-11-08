#!/usr/bin/env python3
"""Fixes two leftovers of the findings round's history (coenttb/work#242) in one package, from a build log.

    fix-history-leftovers.py <package dir> <build log> [--prefix <path the log uses for the package>]

1. Access narrowed by the checkpoint ("compound type name, compound identifier: single-file internal types made
   fileprivate"): on any error naming a fileprivate type ("uses a fileprivate type", "… is fileprivate"), every type
   that a commit of the last 7 days changed from `X struct T` to `fileprivate struct T`, and that still reads so, gets
   its previous line back. The script judged those types single-file by name, but other declarations use them.
2. A rename and a revert that both left their file ("invalid redeclaration"): a file created by an `extension file
   naming: files renamed` commit whose every line is already in its sibling files is deleted;
   the revert meant to undo the rename.

Prints each change and changes nothing else."""
import os, re, subprocess, sys

package, log = sys.argv[1], sys.argv[2]
root = os.path.realpath(package)
text = re.sub(r"\x1b\[[0-9;]*m", "", open(log, errors="replace").read())
if "--prefix" in sys.argv:
    text = text.replace(sys.argv[sys.argv.index("--prefix") + 1].rstrip("/") + "/", root + "/")
mine = [l for l in text.split("\n") if l.startswith(root + "/")]


def git(*args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True).stdout


if any("fileprivate" in l and "error:" in l for l in mine):
    diff = git("log", "-p", "--since=7.days", "--format=", "--", "Sources", "Tests")
    pairs = {}
    removed = None
    for line in diff.split("\n"):
        m = re.match(r"^-(\s*)((?:public |package |internal )?)((?:final )?(?:struct|enum|class|actor) \w+)(.*)$", line)
        if m and "fileprivate" not in line and "private " not in line:
            removed = m
            continue
        a = re.match(r"^\+(\s*)fileprivate ((?:final )?(?:struct|enum|class|actor) \w+)(.*)$", line)
        if a and removed and removed.group(3) == a.group(2):
            pairs[a.group(0)[1:]] = removed.group(0)[1:]
        removed = None
    for dirpath, _, files in os.walk(root):
        if "/.build" in dirpath or "/.git" in dirpath:
            continue
        for f in files:
            if not f.endswith(".swift"):
                continue
            path = os.path.join(dirpath, f)
            source = open(path).read()
            lines = source.split("\n")
            changed = 0
            for i, l in enumerate(lines):
                if l in pairs:
                    lines[i] = pairs[l]
                    changed += 1
            if changed:
                open(path, "w").write("\n".join(lines))
                print(f"access restored {changed}: {os.path.relpath(path, root)}")

def body(path):
    return [l.rstrip() for l in open(path).read().split("\n") if l.strip() and not re.match(r"\s*(@\w+ )*(public |package |internal )?import ", l)]


dirs = {os.path.dirname(l.split(":")[0]) for l in mine if "invalid redeclaration" in l}
for d in sorted(dirs):
    files = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".swift"))
    for f in files:
        created = git("log", "--diff-filter=A", "--format=%s", "--", os.path.relpath(f, root)).split("\n")[0]
        if not created.startswith("extension file naming: files renamed"):
            continue
        others = [l for g in files if g != f and os.path.exists(g) for l in body(g)]
        if body(f) and set(body(f)) <= set(others):
            os.remove(f)
            print(f"duplicate removed: {os.path.relpath(f, root)} (every line is in its siblings)")
