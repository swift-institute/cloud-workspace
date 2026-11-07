#!/usr/bin/env python3
"""For `compound suite name`: moves suites to where the rule wants them, keeping their names.

- A top-level narrative suite goes into `extension <Host> { ... }`, Host taken from the test file's name
  (`Observer.Registrar Tests.swift` -> `Observer.Registrar`). Only when every component of Host is declared as a
  non-generic struct/enum/class/actor in the package's Sources. `extension Name` elsewhere in Tests/ becomes
  `extension Host.Name`; a suite referenced any other way is skipped.
- A non-category suite nested directly in a @Suite type moves to `extension <Path>.<Parent> { ... }` right after
  the parent, which keeps the type nesting, so Swift Testing's IDs and trait inheritance are unchanged.
A concatenated name (`FooTests`) is left alone, as are suites in files whose lines no longer match the lint.

    overnight/compound-suites.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
CATS = {"Unit", "Edge Case", "Integration", "Performance"}
IDENT = r"(?:`[^`\n]+`|[A-Za-z_][A-Za-z0-9_]*)"
stats = {}


def scan(t):
    """Returns (code mask, brace pairs): mask[i] True where t[i] is code."""
    n, i = len(t), 0
    mask = bytearray(n)
    stack = []  # modes: ('code', parens) | ('str', hashes, multi)
    mode = [("code", 0)]
    while i < n:
        m = mode[-1]
        c = t[i]
        if m[0] == "code":
            if t.startswith("//", i):
                j = t.find("\n", i); i = n if j < 0 else j; continue
            if t.startswith("/*", i):
                d, j = 1, i + 2
                while j < n and d:
                    if t.startswith("/*", j): d += 1; j += 2
                    elif t.startswith("*/", j): d -= 1; j += 2
                    else: j += 1
                i = j; continue
            k = i
            while k < n and t[k] == "#": k += 1
            if k < n and t[k] == '"' and (k == i or True):
                hashes = k - i
                if hashes and i > 0 and (t[i - 1].isalnum() or t[i - 1] == "_"):
                    mask[i] = 1; i += 1; continue
                multi = t.startswith('"""', k)
                mode.append(("str", hashes, multi)); i = k + (3 if multi else 1); continue
            mask[i] = 1
            if c == "(":
                mode[-1] = ("code", m[1] + 1)
            elif c == ")":
                if m[1] == 0 and len(mode) > 1:
                    mode.pop(); mask[i] = 0
                else:
                    mode[-1] = ("code", m[1] - 1)
            i += 1
        else:
            _, h, multi = m
            if c == "\\" and t.startswith("#" * h, i + 1):
                j = i + 1 + h
                if j < n and t[j] == "(":
                    mode.append(("code", 0)); i = j + 1; continue
                i = j + 1; continue
            close = ('"""' if multi else '"') + "#" * h
            if t.startswith(close, i):
                mode.pop(); i += len(close); continue
            if c == "\n" and not multi:
                mode.pop()
            i += 1
    pairs, st = {}, []
    for i in range(n):
        if mask[i]:
            if t[i] == "{": st.append(i)
            elif t[i] == "}" and st: pairs[st.pop()] = i
    return mask, pairs


def decl_types(pkg):
    """Names declared as nominal types in Sources: name -> generic?"""
    out = {}
    for f in glob.glob(os.path.join(pkg, "Sources/**/*.swift"), recursive=True):
        for m in re.finditer(r"\b(struct|enum|class|actor|protocol)\s+(" + IDENT + r")\s*(<)?", open(f, errors="replace").read()):
            name = m[2].strip("`")
            g = bool(m[3]) or m[1] == "protocol"
            out[name] = out.get(name, False) or g
    return out


def decl_start(L, offs, j):
    """Line-based start of the declaration on line j: its attributes and comments above it."""
    k = j
    while k > 0:
        prev = L[k - 1].strip()
        if prev.startswith(("@", "//", "/*", "*")):
            k -= 1; continue
        # A multi-line attribute argument list: walk up to its @ line.
        m = k - 1
        while m >= 0 and m > k - 8 and L[m].strip() and not L[m].strip().startswith("@"):
            m -= 1
        if m >= 0 and m > k - 8 and L[m].strip().startswith("@") and "(" in L[m] and not L[m].rstrip().endswith((")", "}")):
            k = m; continue
        break
    return offs[k]


def dedent(chunk, want):
    lines = chunk.split("\n")
    have = min(len(l) - len(l.lstrip(" ")) for l in lines if l.strip())
    d = have - want
    if d <= 0 or any(l.strip() and not l.startswith(" " * d) for l in lines):
        return chunk
    return "\n".join(l[d:] if l.strip() else l for l in lines)


def line_start(t, i):
    return t.rfind("\n", 0, i) + 1


def header_start(t, mask, brace_or_name):
    """Start of the declaration holding position p: after the previous code { } ; boundary, at a line start."""
    j = brace_or_name - 1
    while j >= 0 and not (mask[j] and t[j] in "{};"):
        j -= 1
    k = t.find("\n", j + 1) if j >= 0 else -1
    return 0 if j < 0 else k + 1, j


def enclosing(pairs, pos):
    best = None
    for o, c in pairs.items():
        if o < pos < c and (best is None or o > best):
            best = o
    return best


def info(t, mask, o):
    """(kind, name/type, has @Suite, start) for the declaration whose body opens at o."""
    s, _ = header_start(t, mask, o)
    h = t[s:o]
    code = "".join(ch if mask[s + k] else " " for k, ch in enumerate(h))
    m = re.search(r"\bextension\s+(" + IDENT + r"(?:\." + IDENT + r")*)", code)
    if m:
        return "ext", m[1], False, s
    m = re.search(r"\b(struct|enum|class|actor)\s+(" + IDENT + r")\s*(<)?", code)
    if m:
        return ("generic" if m[3] else "type"), m[2], "@Suite" in code, s
    return "other", None, False, s


def process(p, rel, lines, tests, types):
    path = os.path.join(root, "repos", p, rel)
    t = tests[path]
    mask, pairs = scan(t)
    L = t.split("\n")
    offs = [0]
    for l in L: offs.append(offs[-1] + len(l) + 1)
    stem = os.path.basename(rel)[:-len(" Tests.swift")] if rel.endswith(" Tests.swift") else None
    host = None
    if stem and "+" in stem:
        stem = stem.split("+")[0]
    if stem and re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", stem):
        comps = stem.split(".")
        if all(c in types and not types[c] for c in comps):
            host = stem
    tops, nested = [], {}  # tops: (start, end, name); nested: parent open -> [(start,end)]
    for ln in sorted(set(lines)):
        if ln > len(L): continue
        m = re.search(r"\b(struct|enum|class|actor)\s+(" + IDENT + r")", L[ln - 1])
        if not m:
            stats["stale"] = stats.get("stale", 0) + 1; continue
        name = m[2]
        npos = offs[ln - 1] + m.start(2)
        o = t.find("{", npos)
        while o >= 0 and not mask[o]: o = t.find("{", o + 1)
        if o < 0 or o not in pairs: continue
        if "@Suite" not in t[header_start(t, mask, npos)[0]:npos]:
            stats["stale"] = stats.get("stale", 0) + 1; continue
        start, _ = header_start(t, mask, npos)
        start = max(start, decl_start(L, offs, ln - 1))
        end = t.find("\n", pairs[o]); end = len(t) if end < 0 else end
        if t[pairs[o] + 1:end].strip():
            stats["inline"] = stats.get("inline", 0) + 1; continue
        un = name.strip("`")
        if un.endswith("Tests") and not un.endswith(" Tests"):
            stats["concatenated"] = stats.get("concatenated", 0) + 1; continue
        par = enclosing(pairs, npos)
        if par is None:
            if not host:
                stats["no host"] = stats.get("no host", 0) + 1; continue
            if un in CATS: continue
            tops.append((start, end, name))
        else:
            kind, pname, suite, pstart = info(t, mask, par)
            if kind != "type" or not suite or un in CATS:
                stats["nested other"] = stats.get("nested other", 0) + 1; continue
            gp = enclosing(pairs, par)
            anchor = None
            if gp is None:
                prefix = None  # resolved below: Host if the parent is wrapped, else none
            else:
                gk, gname, _, _ = info(t, mask, gp)
                if gk != "ext" or enclosing(pairs, gp) is not None:
                    stats["nested deep"] = stats.get("nested deep", 0) + 1; continue
                prefix = gname
                anchor = gp
            nested.setdefault(par, [prefix, pname, [], anchor])[2].append((start, end))
    if not tops and not nested:
        return []
    # References to a wrapped suite: only `extension Name` is rewritten.
    wrapped_names = []
    for s, e, name in list(tops):
        others = [(tp, tx) for tp, tx in tests.items()]
        bad = False
        pat = re.compile(r"(?<![\w`.])" + re.escape(name) + r"(?![\w`])")
        for tp, tx in others:
            for m in pat.finditer(tx):
                if tp == path and s <= m.start() < e: continue
                if re.search(r"\bextension\s+$", tx[max(0, m.start() - 20):m.start()]): continue
                bad = True; break
            if bad: break
        if bad:
            stats["referenced"] = stats.get("referenced", 0) + 1; tops.remove((s, e, name))
        else:
            wrapped_names.append(name)
    top_spans = {(s, e) for s, e, _ in tops}
    # Edits on the original text, applied from the end.
    edits = []  # (start, end, replacement)
    moved = set()
    for par, (prefix, pname, kids, anchor) in nested.items():
        a = anchor if anchor is not None else par
        pe = t.find("\n", pairs[a]); pe = len(t) if pe < 0 else pe
        ps = line_start(t, a)
        wrapped = any(s <= ps and pe <= e for s, e in top_spans)
        if prefix is None:
            prefix = host if wrapped else None
        target = (prefix + "." if prefix else "") + pname
        indent = re.match(r"[ \t]*", t[ps:]).group(0)
        body = []
        for s, e in sorted(kids):
            if any(s >= a and e <= b for a, b in moved): continue
            moved.add((s, e))
            chunk = t[s:e]
            # Drop the blank line before the child too.
            cs = s
            if t[max(0, cs - 2):cs] == "\n\n" or re.search(r"\n[ \t]*\n$", t[:cs]):
                cs = t.rfind("\n", 0, cs - 1) + 1
            edits.append((cs, e + 1 if e < len(t) else e, "", 0))
            body.append(dedent(chunk, len(indent) + 4))
        if body:
            text = "\n\n" + indent + "extension " + target + " {\n" + "\n\n".join(body) + "\n" + indent + "}"
            edits.append((pe, pe, text, 1))
    for s, e, name in tops:
        edits.append((s, s, "extension " + host + " {\n", 0))
        edits.append((e, e, "\n}", 0))
        edits.append(("indent", s, e))
    # Indentation: done on the final text by marking ranges; simplest is to apply in order with an indent pass.
    out, last = [], 0
    marks = sorted([x for x in edits if x[0] != "indent"], key=lambda x: (x[0], x[1], x[3]))
    indents = [(x[1], x[2]) for x in edits if x[0] == "indent"]
    for s, e, rep, _ in marks:
        if s < last: return []
        seg = t[last:s]
        out.append(seg_indent(seg, last, indents, t))
        out.append(rep)
        last = e
    out.append(seg_indent(t[last:], last, indents, t))
    new = "".join(out)
    tests[path] = new
    # `extension Name` -> `extension Host.Name` in the target's tests.
    for name in wrapped_names:
        pat = re.compile(r"(\bextension\s+)" + re.escape(name) + r"(?![\w`])")
        for tp in tests:
            tests[tp] = pat.sub(lambda m: m[1] + host + "." + name, tests[tp])
    return [(rel, len(tops), sum(len(k[2]) for k in nested.values()))]


def indent_text(s):
    return "\n".join(("    " + l) if l.strip() else l for l in s.split("\n"))


def seg_indent(seg, base, indents, t):
    if not any(a < base + len(seg) and base < b for a, b in indents):
        return seg
    out = []
    pos = base
    for part in re.split(r"(\n)", seg):
        if part == "\n":
            out.append(part); pos += 1; continue
        ls = line_start(t, pos) == pos
        if ls and part.strip() and any(a <= pos < b for a, b in indents):
            out.append("    " + part)
        else:
            out.append(part)
        pos += len(part)
    return "".join(out)


total = [0, 0]
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "compound suite name":
            by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    if not by_file: continue
    pkg = os.path.join(root, "repos", p)
    types = decl_types(pkg)
    for rel in by_file:
        tdir = os.path.join(pkg, *rel.split("/")[:2])
        tests = {t: open(t, encoding="utf8").read() for t in glob.glob(os.path.join(tdir, "**/*.swift"), recursive=True)}
        before = dict(tests)
        path = os.path.join(pkg, rel)
        if path not in tests: continue
        try:
            r = process(p, rel, by_file[rel], tests, types)
        except Exception as e:
            print("ERROR", p, rel, e, file=sys.stderr); continue
        for rr in r:
            total[0] += rr[1]; total[1] += rr[2]
            print(p, rr[0], "top", rr[1], "nested", rr[2])
        if not dry:
            for tp, tx in tests.items():
                if tx != before[tp]: open(tp, "w", encoding="utf8").write(tx)
print("total top", total[0], "nested", total[1], "skips", stats, file=sys.stderr)
