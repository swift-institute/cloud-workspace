#!/usr/bin/env python3
"""Rewrites each checkout's Package.swift so dependencies between checkouts are path dependencies, and marks the file
skip-worktree so the rewrite is never committed. SwiftPM's search for identity-conflict chains doesn't finish on a graph
this size when a root path dependency overrides URL dependencies, so the graph must hold no such conflict at all.

    ./localize.py             rewrite every checkout
    ./localize.py --restore   put every manifest back, to change one for real; run again afterwards
    ./localize.py --dry-run   report only
"""
import glob, os, re, subprocess, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
packages = sorted(p for p in glob.glob("repos/*/*") if os.path.exists(p + "/Package.swift"))
checkouts = {os.path.basename(p).lower(): p for p in packages}
url = re.compile(r'url:\s*"https://github\.com/([^/"]+)/([^/"]+?)(?:\.git)?/?"\s*,\s*branch:\s*"main"')


def git(path, *args):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True)


if "--restore" in sys.argv:
    for p in packages:
        git(p, "update-index", "--no-skip-worktree", "Package.swift")
        git(p, "checkout", "--", "Package.swift")
    print(f"restored {len(packages)} manifests")
    sys.exit()

total = 0
for p in packages:
    manifest = p + "/Package.swift"
    source = open(manifest, encoding="utf8").read()

    def path(match):
        global total
        target = checkouts.get(match[2].lower())
        if target is None:
            return match[0]
        total += 1
        return f'path: "{os.path.relpath(target, p)}"'

    rewritten = url.sub(path, source)
    if "--dry-run" not in sys.argv and rewritten != source:
        open(manifest, "w", encoding="utf8").write(rewritten)
        git(p, "update-index", "--skip-worktree", "Package.swift")

left = [
    (os.path.basename(p), u)
    for p in packages
    for u in re.findall(r'url:\s*"([^"]+)"', open(p + "/Package.swift", encoding="utf8").read())
    if re.sub(r"\.git$", "", u.rstrip("/")).split("/")[-1].lower() in checkouts
]
print(f"{total} dependencies rewritten across {len(packages)} packages; {len(left)} URLs still naming a checkout")
for item in left[:20]:
    print(" ", item)
