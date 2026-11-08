#!/usr/bin/env python3
"""For `extension file naming`'s "holds member-only extensions of 'T'; those live in the type's own file 'T.swift'"
when the target has no `T.swift`: renames one such file per (target, T) to `T.swift` (git mv). The other files for
the same T are then merged into it by merge-extension-files.py on a fresh lint. Sources only.
Usage: overnight/own-type-files.py <lint-dir> [--dry-run]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}; n = 0
def skip(w): stats[w] = stats.get(w, 0) + 1
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1); d = os.path.join(root, "repos", p)
    taken = set()
    for x in json.load(open(f))["findings"]:
        if x["rule"] != "extension file naming": continue
        m = re.search(r"holds member-only extensions of '([^']+)'; those live in the type's own file '([^']+)'", x["message"])
        if not m: continue
        rel = x["filePath"][2:]
        if not rel.startswith("Sources/"): skip("not Sources"); continue
        new = m.group(2)
        if re.search(r'[<>:"|?*\\]', new): skip("bad chars"); continue
        tdir = os.path.join(d, *rel.split("/")[:2])
        key = (tdir, new)
        if key in taken: skip("second file"); continue
        if not os.path.exists(os.path.join(d, rel)): skip("gone"); continue
        if any(os.path.basename(y) == new for y in glob.glob(os.path.join(tdir, "**", "*.swift"), recursive=True)): skip("type file exists"); continue
        taken.add(key); n += 1
        if dry: continue
        subprocess.run(["git", "-C", d, "mv", rel, os.path.join(os.path.dirname(rel), new)], check=True)
print("renamed", n, "skips", stats, file=sys.stderr)
