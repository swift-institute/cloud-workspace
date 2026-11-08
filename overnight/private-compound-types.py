#!/usr/bin/env python3
"""For `compound type name` on an internal type the rule exempts once private: a type whose name appears in no other
file of its package, and in its own file only in its own body and `extension <name>` headers, becomes `fileprivate`.
Skips @Suite types, a type whose body holds @Test, protocols, and
extensions. Usage: overnight/private-compound-types.py <lint-dir> [--dry-run]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}
def skip(w): stats[w] = stats.get(w, 0) + 1
DECL = re.compile(r"^(\s*)((?:@[\w.]+(?:\([^)]*\))?\s+)*)((?:internal\s+)?)((?:final\s+|indirect\s+)*)(struct|enum|class|actor)\s+([A-Za-z_]\w*)")
n = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    d = os.path.join(root, "repos", p)
    finds = [x for x in json.load(open(f))["findings"] if x["rule"] == "compound type name" and x.get("visibility") == "internal"]
    if not finds: continue
    files = [y for y in glob.glob(os.path.join(d, "**", "*.swift"), recursive=True) if "/.build/" not in y]
    texts = {}
    def text(y):
        if y not in texts: texts[y] = open(y, errors="replace").read()
        return texts[y]
    edits = {}
    for x in finds:
        path = os.path.join(d, x["filePath"][2:])
        try: L = text(path).split("\n")
        except OSError: skip("gone"); continue
        i = x["line"] - 1
        m = DECL.match(L[i])
        if not m: skip("no decl"); continue
        if "@Suite" in L[i] or (i > 0 and "@Suite" in L[i - 1]): skip("suite"); continue
        name = m.group(6)
        rest = "\n".join(L[i:])
        # body up to matching brace
        depth, j, started = 0, 0, False
        for j, ch in enumerate(rest):
            if ch == "{": depth += 1; started = True
            elif ch == "}":
                depth -= 1
                if started and depth == 0: break
        if "@Test" in rest[:j]: skip("holds tests"); continue
        w = re.compile(r"(?<![\w`])" + re.escape(name) + r"(?![\w`])")
        if any(w.search(text(y)) for y in files if y != path): skip("used elsewhere"); continue
        # A declaration outside the type's own body that names it (a property, parameter, result or enclosing
        # member) would then expose a fileprivate type: "… must be declared fileprivate because its type uses a
        # fileprivate type". Only `extension <name>` headers may name it there.
        outside = "\n".join(L[:i]) + "\n" + rest[j + 1:]
        outside = re.sub(r"(?m)^[^\S\n]*(?:@[\w.]+(?:\([^)]*\))?\s+)*(?:\w+\s+)*extension\s+" + re.escape(name) + r"\b", "", outside)
        if w.search(outside): skip("used by other declarations in its file"); continue
        new = m.group(1) + m.group(2) + "fileprivate " + m.group(4) + L[i][m.end(3) + len(m.group(4)):] if False else \
              L[i][:m.start(3)] + "fileprivate " + L[i][m.end(3):]
        edits.setdefault(path, []).append((i, new))
    for path, es in edits.items():
        L = text(path).split("\n")
        for i, new in es: L[i] = new
        n += len(es)
        if not dry: open(path, "w").write("\n".join(L))
print("fileprivate", n, "skips", stats, file=sys.stderr)
