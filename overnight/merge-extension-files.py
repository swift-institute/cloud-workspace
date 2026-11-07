#!/usr/bin/env python3
"""For `extension file naming`'s "holds member-only extensions of 'T'; those live in the type's own file 'T.swift'"
and "adds only standard-library conformances; those stay in the type's own file 'T.swift'": appends the extension
file's declarations to T.swift in the same target and removes the file (git rm). Imports the extension file has and
T.swift lacks are added to T.swift's import block. Skips: T.swift not in the same target (or more than one), either
file under #if at top level around imports, a file whose findings disagree on the target, Tests/ files.

    overnight/merge-extension-files.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
pat = re.compile(r"extension file '([^']+)' (?:holds member-only extensions of '[^']+'; those live in|adds only standard-library conformances; those stay in) the type's own file '([^']+)'")
IMPORT = re.compile(r"^(?:@[\w()]+\s+)*(?:(?:public|package|internal|private|fileprivate)\s+)?import\s+(?:(?:struct|enum|class|protocol|func|var|typealias)\s+)?([\w.]+)", re.M)
stats = {}


def split_header(text):
    """(imports block lines, rest) — leading comments, blank lines and imports form the header."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s.startswith("//") or IMPORT.match(lines[i]):
            i += 1; continue
        break
    return lines[:i], "\n".join(lines[i:])


def skip(why):
    stats[why] = stats.get(why, 0) + 1


merged = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    pkg = os.path.join(root, "repos", p)
    wants = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] != "extension file naming": continue
        m = pat.search(x["message"])
        if m:
            wants.setdefault(x["fileID"][2:], set()).add(m[2])
    for rel, targets in sorted(wants.items()):
        if not rel.startswith("Sources/"): skip("not Sources"); continue
        if len(targets) != 1: skip("several targets"); continue
        src = os.path.join(pkg, rel)
        if not os.path.exists(src): skip("gone"); continue
        tdir = os.path.join(pkg, *rel.split("/")[:2])
        name = next(iter(targets))
        cands = [c for c in glob.glob(os.path.join(tdir, "**", name), recursive=True)]
        if len(cands) != 1: skip("type file not unique in target"); continue
        dst = cands[0]
        if os.path.abspath(dst) == os.path.abspath(src): skip("same file"); continue
        a, b = open(src, encoding="utf8").read(), open(dst, encoding="utf8").read()
        if re.match(r"\s*#if", split_header(a)[1]) and "#endif" in a[-40:] and "#if" not in b:
            pass
        ha, body = split_header(a)
        hb, _ = split_header(b)
        have = {m[1] for l in hb for m in [IMPORT.match(l)] if m}
        add = [l for l in ha if IMPORT.match(l) and IMPORT.match(l)[1] not in have]
        if any(IMPORT.match(l) and "@_exported" in l for l in add):
            skip("exported import"); continue
        body = body.strip("\n")
        if not body: skip("empty"); continue
        bl = b.split("\n")
        if add:
            last = max((i for i, l in enumerate(bl) if IMPORT.match(l)), default=-1)
            if last < 0:
                # No import block: put them after the leading comments.
                k = 0
                while k < len(bl) and bl[k].strip().startswith("//"): k += 1
                bl[k:k] = add + [""]
            else:
                bl[last + 1:last + 1] = add
        new = "\n".join(bl).rstrip("\n") + "\n\n" + body + "\n"
        merged += 1
        print(p, os.path.relpath(src, pkg), "->", os.path.relpath(dst, pkg))
        if not dry:
            open(dst, "w", encoding="utf8").write(new)
            subprocess.run(["git", "-C", pkg, "rm", "-q", os.path.relpath(src, pkg)], check=True)
print("merged", merged, "skips", stats, file=sys.stderr)
