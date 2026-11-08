#!/usr/bin/env python3
"""For `module selector spelling`: at each finding's line and column, `Module.Name` becomes `Module::Name`. When the
module declares a type of its own name (`W3C_XML.W3C_XML`? no: a namespace `Module` reached as `Module.Name`), the
compiler decides: the type-check reverts what it rejects. Only on a line still starting the same way.

    overnight/module-selectors.py <lint-dir>"""
import glob, json, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    by = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "module selector spelling": by.setdefault(x["filePath"][2:], []).append((x["line"], x["column"]))
    for rel, locs in by.items():
        path = os.path.join(root, "repos", p, rel)
        try: t = open(path).read().split("\n")
        except OSError: continue
        ch = 0
        for ln, col in sorted(locs, reverse=True):
            s = t[ln - 1]; i = col - 1
            m = re.match(r"([A-Za-z_]\w*)\.(?=[A-Za-z_`])", s[i:])
            if not m or (i > 0 and (s[i - 1].isalnum() or s[i - 1] in "_.:")): continue
            t[ln - 1] = s[:i] + m.group(1) + "::" + s[i + len(m.group(0)):]; ch += 1
        if ch: open(path, "w").write("\n".join(t)); n += ch
print("rewritten", n)
