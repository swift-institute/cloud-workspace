#!/usr/bin/env python3
"""For `path name grammar`'s "directory 'X' contains concatenated word(s) ...; rename the directory": renames the
directory to its spaced form (`BitPattern` -> `Bit Pattern`, `SQLite CloudKit` -> `SQLite Cloud Kit`), with git mv,
in Sources/ only, below a target's root. Skips a directory named in the manifest (target path, exclude, resource),
one holding resources, and a target whose directory would collide.

    overnight/rename-directories.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
pat = re.compile(r"directory '([^']+)' contains concatenated word")
stats, renamed = {}, 0


def spaced(word):
    # Split lower->Upper and Upper->Upper+lower boundaries; keep acronyms (SQLite, URL) whole.
    w = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", word)
    w = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", w)
    return w


def skip(why):
    stats[why] = stats.get(why, 0) + 1


for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    pkg = os.path.join(root, "repos", p)
    manifest = subprocess.run(["git", "-C", pkg, "show", ":Package.swift"], capture_output=True, text=True).stdout
    dirs = set()
    for x in json.load(open(f))["findings"]:
        if x["rule"] != "path name grammar": continue
        m = pat.search(x["message"])
        if not m: continue
        rel = x["fileID"][2:]
        parts = rel.split("/")
        if parts[0] != "Sources" or m[1] not in parts[2:-1]:
            skip("not below a Sources target root"); continue
        i = parts.index(m[1], 2)
        dirs.add("/".join(parts[:i + 1]))
    # Deepest first, so a parent's rename doesn't move a child out from under us.
    for d in sorted(dirs, key=lambda d: -d.count("/")):
        name = os.path.basename(d)
        new = " ".join(spaced(w) for w in name.split(" "))
        if new == name: skip("no split"); continue
        src, dst = os.path.join(pkg, d), os.path.join(pkg, os.path.dirname(d), new)
        if not os.path.isdir(src): skip("gone"); continue
        if os.path.exists(dst): skip("exists"); continue
        if f'"{name}' in manifest or f"/{name}" in manifest: skip("named in manifest"); continue
        if any(not x.endswith(".swift") for x in glob.glob(os.path.join(src, "**/*"), recursive=True) if os.path.isfile(x)):
            skip("holds non-Swift files"); continue
        renamed += 1
        print(p, d, "->", new)
        if not dry:
            subprocess.run(["git", "-C", pkg, "mv", d, os.path.join(os.path.dirname(d), new)], check=True)
print("renamed", renamed, "skips", stats, file=sys.stderr)
