#!/usr/bin/env python3
"""For `counter loop iteration`: `for x in a..<b { body }` -> `(a..<b).forEach { x in body }` on the finding's line.
Skips a body with break, return, throw, try, await, yield or a label, a `where` clause, a non-identifier pattern,
and `continue` when the body has a nested loop (a top-level `continue` becomes `return`).

    overnight/counter-loops.py <lint-dir> [--dry-run]"""
import glob, importlib.util, json, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}
def skip(w): stats[w] = stats.get(w, 0) + 1

def mask_of(t):
    """1 where t[i] is code (not in a comment or string literal)."""
    n, i, m = len(t), 0, bytearray(len(t))
    while i < n:
        if t.startswith("//", i):
            j = t.find("\n", i); i = n if j < 0 else j; continue
        if t.startswith("/*", i):
            j = t.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        if t[i] == '"' or (t[i] == "#" and t[i:i+2] in ('#"',)):
            h = 0
            while t[i] == "#": h += 1; i += 1
            if t.startswith('"""', i):
                end = '"""' + "#" * h; j = t.find(end, i + 3); i = n if j < 0 else j + len(end); continue
            j = i + 1
            while j < n and t[j] != "\n":
                if t[j] == "\\": j += 2; continue
                if t.startswith('"' + "#" * h, j): break
                j += 1
            i = j + 1 + h; continue
        m[i] = 1; i += 1
    return m

def match_brace(t, m, i):
    d = 0
    for j in range(i, len(t)):
        if not m[j]: continue
        if t[j] == "{": d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0: return j
    return -1

BAD = re.compile(r"\b(break|return|throw|try|await|yield)\b|^\s*\w+\s*:\s*(for|while|repeat)\b", re.M)
FOR = re.compile(r"\bfor\s+([A-Za-z_]\w*)\s+in\s+")
n = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    by = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "counter loop iteration": by.setdefault(x["filePath"][2:], set()).add(x["line"])
    for rel, lines in by.items():
        path = os.path.join(root, "repos", p, rel)
        try: t = open(path).read()
        except OSError: skip("gone"); continue
        edits = []
        starts = [0] + [k + 1 for k, c in enumerate(t) if c == "\n"]
        m = mask_of(t)
        for ln in sorted(lines):
            if ln > len(starts): skip("gone"); continue
            a = starts[ln - 1]; e = t.find("\n", a); e = len(t) if e < 0 else e
            fm = FOR.search(t, a, e)
            if not fm or not m[fm.start()]: skip("no for"); continue
            ob = -1
            for j in range(fm.end(), e):
                if m[j] and t[j] == "{": ob = j
            if ob < 0: skip("multiline header"); continue
            expr = t[fm.end():ob].strip()
            if re.search(r"\bwhere\b", expr): skip("where"); continue
            cb = match_brace(t, m, ob)
            if cb < 0: skip("unbalanced"); continue
            body = t[ob + 1:cb]
            bm = m[ob + 1:cb]
            code = "".join(c if bm[k] else " " for k, c in enumerate(body))
            if BAD.search(code): skip("control flow"); continue
            if re.search(r"\bcontinue\b", code):
                if re.search(r"\b(for|while|repeat)\b", code): skip("continue nested"); continue
            if any(fm.start() < x[1] and x[0] < cb for x in edits): skip("overlap"); continue
            depth, top = 0, False
            for k, c in enumerate(expr):
                depth += c in "([{"; depth -= c in ")]}"
                if depth == 0 and (expr.startswith("...", k) or expr.startswith("..<", k)): top = True
            recv = f"({expr})" if top else expr
            newbody = re.sub(r"\bcontinue\b", "return", body) if "continue" in code else body
            if "continue" in code:
                # Only replace code occurrences.
                out = list(body)
                for mm in re.finditer(r"\bcontinue\b", code): out[mm.start():mm.end()] = list("return  ")[:0] or list("return")
                newbody = "".join(out) if False else re.sub(r"\bcontinue\b", "return", code) if False else body
                parts, last = [], 0
                for mm in re.finditer(r"\bcontinue\b", code):
                    parts.append(body[last:mm.start()]); parts.append("return"); last = mm.end()
                parts.append(body[last:]); newbody = "".join(parts)
            edits.append((fm.start(), cb + 1, f"{recv}.forEach {{ {fm.group(1)} in{newbody}}}"))
        if not edits: continue
        for s, e, r in sorted(edits, reverse=True): t = t[:s] + r + t[e:]
        n += len(edits)
        if not dry: open(path, "w").write(t)
        else: print(p, rel, len(edits))
print("converted", n, "skips", stats, file=sys.stderr)
