#!/usr/bin/env python3
"""For `test display name string` on a @Suite the rename script skips (dotted names, names used elsewhere): drops the
display string and keeps the type name, so the test ID is unchanged. `@Suite("A.B - c", .serialized)` ->
`@Suite(.serialized)`, `@Suite("x")` -> `@Suite`. Only on the finding's line, in a file whose line still matches.

    overnight/suite-drop-display.py <lint-dir>"""
import glob, json, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rx = re.compile(r'@Suite\(\s*"(?:[^"\\]|\\.)*"\s*(,\s*)?')
n = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    by = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "test display name string": by.setdefault(x["filePath"][2:], []).append(x["line"])
    for rel, lines in by.items():
        path = os.path.join(root, "repos", p, rel)
        try: t = open(path).read().split("\n")
        except OSError: continue
        ch = False
        for l in lines:
            s = t[l - 1]
            def rep(m): return "@Suite(" if m.group(1) else "@Suite("
            new = rx.sub(rep, s, count=1)
            new = new.replace("@Suite()", "@Suite")
            if new != s: t[l - 1] = new; ch = True; n += 1
        if ch: open(path, "w").write("\n".join(t))
print("dropped", n)
