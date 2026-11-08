#!/usr/bin/env python3
"""For `compound identifier` on a `package` member (the rule exempts below package): drops `package` when the name
appears in no file outside the member's own target directory (other targets, Tests). Only on the finding's line.
Usage: overnight/package-to-internal.py <lint-dir> [--dry-run]"""
import glob, json, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}
def skip(w): stats[w] = stats.get(w, 0) + 1
NAME = re.compile(r"\b(?:func|var|let|case|subscript)\s+`?([A-Za-z_]\w*)")
n = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    d = os.path.join(root, "repos", p)
    finds = [x for x in json.load(open(f))["findings"] if x["rule"] == "compound identifier" and x.get("visibility") == "package"]
    if not finds: continue
    files = [y for y in glob.glob(os.path.join(d, "**", "*.swift"), recursive=True) if "/.build/" not in y]
    cache = {}
    def text(y):
        if y not in cache: cache[y] = open(y, errors="replace").read()
        return cache[y]
    edits = {}
    for x in finds:
        rel = x["filePath"][2:]; path = os.path.join(d, rel)
        parts = rel.split("/")
        tdir = os.path.join(d, *parts[:2])  # Sources/<Target>
        try: L = text(path).split("\n")
        except OSError: skip("gone"); continue
        i = x["line"] - 1; s = L[i]
        if not re.search(r"\bpackage\s", s): skip("no package on line"); continue
        m = NAME.search(s)
        if not m: skip("no name"); continue
        w = re.compile(r"(?<![\w`])" + re.escape(m.group(1)) + r"(?![\w`])")
        if any(w.search(text(y)) for y in files if not y.startswith(tdir + "/")): skip("used outside target"); continue
        edits.setdefault(path, []).append((i, re.sub(r"\bpackage\s+", "", s, count=1)))
    for path, es in edits.items():
        L = text(path).split("\n")
        for i, new in es: L[i] = new
        n += len(es)
        if not dry: open(path, "w").write("\n".join(L))
print("internal", n, "skips", stats, file=sys.stderr)
