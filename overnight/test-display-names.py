#!/usr/bin/env python3
"""For `test display name string` on a @Test function: moves the display string into the function's name as a raw
identifier, `@Test("does x") func doesX()` -> @Test func `does x`(). Other @Test arguments stay. @Suite is left alone
(its type is referenced by name elsewhere). Skips a name with a backtick, backslash or interpolation, and a file
where the new name already exists.

    overnight/test-display-names.py <lint-dir> [--dry-run]"""
import glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
attr = re.compile(r'@Test\(\s*"((?:[^"\\]|\\.)*)"\s*(,\s*)?')
changed = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    lines_by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "test display name string":
            lines_by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    for rel, lines in lines_by_file.items():
        path = os.path.join(root, "repos", p, rel)
        mirror = os.path.join("/home/user/lintmirror", p, rel)
        text = open(path, encoding="utf8").read()
        if text != open(mirror, encoding="utf8").read():
            continue
        src = text.split("\n")
        done = 0
        for n in sorted(lines, reverse=True):
            i = n - 1
            m = attr.search(src[i])
            if not m or "\\" in m[1] or "`" in m[1]:
                continue
            name = m[1].strip()
            # The function declaration: this line or one of the next three.
            for j in range(i, min(i + 4, len(src))):
                fm = re.search(r"\bfunc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", src[j])
                if fm:
                    break
            else:
                continue
            if f"`{name}`" in text:
                continue
            rest = src[i][m.end():]
            if m[2]:
                new_attr = "@Test(" + rest
            else:
                new_attr = "@Test" + rest[1:] if rest.startswith(")") else None
            if new_attr is None:
                continue
            src[i] = src[i][:m.start()] + new_attr
            src[j] = src[j][:fm.start(1)] + f"`{name}`" + src[j][fm.end(1):]
            done += 1
        if done:
            changed += 1
            print(p, rel, done)
            if not dry:
                open(path, "w", encoding="utf8").write("\n".join(src))
print(changed, "files", file=sys.stderr)
