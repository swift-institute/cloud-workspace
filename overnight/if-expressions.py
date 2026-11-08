#!/usr/bin/env python3
"""For `statement where expression fits`: an if/else-if/else chain on the finding's line whose every branch is one
`return X` or the same `lhs = X` becomes `return if ... { X } else { Y }` / `lhs = if ...`, keeping the layout.
Skips a chain without a final else, a branch with more than one statement, and differing assignment targets.

    overnight/if-expressions.py <lint-dir> [--dry-run]"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
s = importlib.util.spec_from_file_location("cl", os.path.join(root, "overnight/counter-loops.py"))
code = open(s.origin).read().split("BAD = re.compile")[0].replace("lint, dry = sys.argv[1], \"--dry-run\" in sys.argv", "")
ns = {"__file__": s.origin}; exec(code, ns); mask_of, match_brace = ns["mask_of"], ns["match_brace"]
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}
def skip(w): stats[w] = stats.get(w, 0) + 1
ASSIGN = re.compile(r"^([A-Za-z_][\w.\[\]\"]*)\s=\s(?!=)(.+)$", re.S)
n = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    by = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "statement where expression fits": by.setdefault(x["filePath"][2:], set()).add((x["line"], x["column"]))
    for rel, locs in by.items():
        path = os.path.join(root, "repos", p, rel)
        try: t = open(path).read()
        except OSError: continue
        m = mask_of(t); starts = [0] + [k + 1 for k, c in enumerate(t) if c == "\n"]
        edits = []
        for ln, col in sorted(locs):
            a = starts[ln - 1]; i = t.find("if", a)
            if i < 0 or not m[i] or t[a:i].strip() not in ("",): skip("not at if"); continue
            branches, j, ok, final_else = [], i, True, False
            while True:
                ob = j
                while ob < len(t) and not (m[ob] and t[ob] == "{"): ob += 1
                cb = match_brace(t, m, ob)
                if cb < 0: ok = False; break
                branches.append((ob, cb))
                k = cb + 1
                while k < len(t) and t[k] in " \t\n": k += 1
                if t.startswith("else", k) and m[k]:
                    k2 = k + 4
                    while t[k2] in " \t\n": k2 += 1
                    if t.startswith("if", k2) and not t[k2+2].isalnum(): j = k2; continue
                    if t[k2] == "{":
                        cb2 = match_brace(t, m, k2); branches.append((k2, cb2)); final_else = True
                    break
                break
            if not ok or not final_else: skip("no final else"); continue
            kinds, bodies = set(), []
            for ob, cb in branches:
                body = t[ob + 1:cb].strip()
                bm = m[ob + 1:cb]
                if not body or "\n" in body or ";" in body or "//" in body: kinds.add("bad"); break
                if body.startswith("return "): kinds.add("return"); bodies.append((ob, cb, body[7:]))
                else:
                    am = ASSIGN.match(body)
                    if not am: kinds.add("bad"); break
                    kinds.add("=" + am.group(1)); bodies.append((ob, cb, am.group(2)))
            if len(kinds) != 1 or "bad" in kinds: skip("branches"); continue
            kind = kinds.pop()
            if re.search(r"\b(if|switch|try|await)\b", " ".join(b[2] for b in bodies)): skip("nested"); continue
            prefix = "return " if kind == "return" else kind[1:] + " = "
            ed = [(i, i, prefix)]
            for ob, cb, val in bodies:
                inner = t[ob + 1:cb]
                lead = inner[:len(inner) - len(inner.lstrip())]; trail = inner[len(inner.rstrip()):]
                ed.append((ob + 1, cb, lead + val + trail))
            edits += ed
        if not edits: continue
        for s0, e0, r in sorted(edits, key=lambda x: -x[0]): t = t[:s0] + r + t[e0:]
        n += sum(1 for e in edits if e[0] == e[1])
        if not dry: open(path, "w").write(t)
print("converted", n, "skips", stats, file=sys.stderr)
