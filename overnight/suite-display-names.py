#!/usr/bin/env python3
"""For `test display name string` on a @Suite: renames the suite type to its display string as a raw identifier and
drops the string, `@Suite("Parsing", .serialized) struct ParsingTests` -> @Suite(.serialized) struct `Parsing`.
Every whole-word use of the old name in the package's Tests/ is renamed too. Skips: a name with a backtick,
backslash or dot, an old name used outside Tests/ or in a string, a new name already present in the package's Tests/,
and a file changed since linting.

    overnight/suite-display-names.py <lint-dir> [--dry-run]"""
import glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
attr = re.compile(r'@Suite\(\s*"((?:[^"\\]|\\.)*)"\s*(,\s*)?')
decl = re.compile(r"\b(?:struct|enum|class|actor)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "test display name string":
            by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    if not by_file:
        continue
    pkg = os.path.join(root, "repos", p)
    tests = {t: open(t, encoding="utf8").read() for t in glob.glob(os.path.join(pkg, "Tests/**/*.swift"), recursive=True)}
    others = "\n".join(open(s, encoding="utf8", errors="replace").read()
                       for s in glob.glob(os.path.join(pkg, "**/*.swift"), recursive=True)
                       if "/Tests/" not in s and "/.build/" not in s)
    renames = []
    for rel, lines in by_file.items():
        path = os.path.join(pkg, rel)
        mirror = os.path.join("/home/user/lintmirror", p, rel)
        if path not in tests or not os.path.exists(mirror) or tests[path] != open(mirror, encoding="utf8").read():
            continue
        src = tests[path].split("\n")
        for n in sorted(lines, reverse=True):
            i = n - 1
            m = attr.search(src[i])
            if not m or any(c in m[1] for c in "\\`.") or not m[1].strip():
                continue
            name = m[1]
            for j in range(i, min(i + 4, len(src))):
                dm = decl.search(src[j], m.end() if j == i else 0)
                if dm:
                    break
            else:
                continue
            old = dm[1]
            word = re.compile(r"(?<![\w`.\"])" + re.escape(old) + r"(?![\w`\"])")
            if re.search(r"\b" + re.escape(old) + r"\b", others) or any(f"`{name}`" in t for t in tests.values()):
                continue
            if any(re.search(r'"[^"\n]*\b' + re.escape(old) + r'\b[^"\n]*"', t) for t in tests.values()):
                continue
            rest = src[i][m.end():]
            if m[2]:
                new_attr = "@Suite(" + rest
            elif rest.startswith(")"):
                new_attr = "@Suite" + rest[1:]
            else:
                continue
            src[i] = src[i][:m.start()] + new_attr
            tests[path] = "\n".join(src)
            renames.append((old, name))
            for t in tests:
                tests[t] = word.sub(f"`{name}`", tests[t])
            src = tests[path].split("\n")
    if renames:
        for t, text in tests.items():
            if not dry and text != open(t, encoding="utf8").read():
                open(t, "w", encoding="utf8").write(text)
        for old, name in renames:
            print(p, old, "->", f"`{name}`")
