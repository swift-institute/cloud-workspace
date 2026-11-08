#!/usr/bin/env python3
"""For `test function naming`: renames a CamelCase `@Test func testInitCreatesEmptyBuffer()` to the backticked
sentence `init creates empty buffer` (a leading `test` dropped, words split at case changes, lower-cased except
acronyms). Skips: a name used elsewhere in the test target (a call or a reference), a new name already in the file,
and a declaration not on the finding's line.

    overnight/test-function-names.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
stats, renamed = {}, 0


def sentence(name):
    n = re.sub(r"^test_?", "", name) or name
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$|_)|[A-Z]?[a-z]+|[A-Z]+|\d+", n)
    out = [w if (len(w) > 1 and w.isupper()) else w.lower() for w in words]
    return " ".join(out)


for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    pkg = os.path.join(root, "repos", p)
    by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "test function naming":
            by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    for rel, lines in by_file.items():
        path = os.path.join(pkg, rel)
        if not os.path.exists(path): continue
        tdir = os.path.join(pkg, *rel.split("/")[:2])
        others = {t: open(t, encoding="utf8", errors="replace").read() for t in glob.glob(os.path.join(tdir, "**/*.swift"), recursive=True)}
        text = others[path]
        L = text.split("\n")
        for ln in lines:
            if ln > len(L): continue
            m = re.search(r"\bfunc\s+([A-Za-z_]\w*)\s*\(", L[ln - 1])
            if not m:
                stats["no func on line"] = stats.get("no func on line", 0) + 1; continue
            old = m[1]
            new = sentence(old)
            if not new or new == old or "`" + new + "`" in text:
                stats["no new name"] = stats.get("no new name", 0) + 1; continue
            uses = sum(len(re.findall(r"\b" + re.escape(old) + r"\b", t)) for t in others.values())
            if uses != 1:
                stats["used elsewhere"] = stats.get("used elsewhere", 0) + 1; continue
            L[ln - 1] = L[ln - 1][:m.start(1)] + "`" + new + "`" + L[ln - 1][m.end(1):]
            text = "\n".join(L)
            others[path] = text
            renamed += 1
        if not dry and text != open(path, encoding="utf8").read():
            open(path, "w", encoding="utf8").write(text)
print("renamed", renamed, "skips", stats, file=sys.stderr)
