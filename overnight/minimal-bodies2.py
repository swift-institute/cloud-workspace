#!/usr/bin/env python3
"""UNTESTED: written for the 8 Nov pilot, which was cancelled before it ran. Test on one package first.
minimal-bodies.py v2: as v1, and a type nested one level (`extension P { struct C { ... } }`) gets its moved members
qualified, since `extension P.C` no longer sees P's members: the type's own name becomes `Self` (or `P.C` where the moved
code declares a nested type), and each bare name declared directly in P anywhere in the target becomes `P.Name`, unless C
declares a member of that name itself. v1 broke swift-linux-standard on Linux this way (8 Nov).
v1 header follows.
For `minimal type body`: moves a file-scope struct/enum/actor's non-stored members (methods, computed properties,
subscripts, static members, nested types, typealiases) into `extension <Type> { ... }` right after the type, in the
same file. Stored properties, enum cases, initializers and deinit stay. Skips: classes (extension members can't be
overridden), protocols, `~Copyable`/`~Escapable` types, a body with `#if`, a type nested in another declaration (its
siblings would leave scope), and any member more visible than its type (the runner repair's `package` failure).

    overnight/minimal-bodies.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
IDENT = r"(?:`[^`\n]+`|[A-Za-z_][A-Za-z0-9_]*)"
LEVEL = {"private": 0, "fileprivate": 1, "internal": 2, "package": 3, "public": 4, "open": 4}
MOD = r"(?:@[\w.]+(?:\([^)]*\))?\s+|(?:public|private|fileprivate|internal|package|open|static|class|final|nonisolated|mutating|nonmutating|override|consuming|borrowing|isolated|dynamic|lazy|weak|unowned|indirect|required|convenience|distributed)(?:\([^)]*\))?\s+)*"
stats = {}


def skip(why):
    stats[why] = stats.get(why, 0) + 1


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




def header_start(t, mask, p):
    j = p - 1
    while j >= 0 and not (mask[j] and t[j] in "{};"):
        j -= 1
    k = t.find("\n", j + 1) if j >= 0 else -1
    return 0 if j < 0 else k + 1, j


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





def access(text):
    m = re.search(r"\b(public|open|package|internal|fileprivate|private)\b(?!\()", text)
    return LEVEL[m[1]] if m else 2


def members(t, mask, o, c):
    """Spans (start, end, code) of the members directly in the body between braces o..c, one per declaration."""
    out, i = [], o + 1
    depth = 0
    start = None
    j = i
    n = c
    while j < n:
        ch = t[j]
        if mask[j]:
            if start is None and not ch.isspace() and ch not in ";":
                start = j
            if ch in "{([":
                depth += 1
            elif ch in "})]":
                depth -= 1
            if depth == 0 and start is not None:
                # A declaration ends at a newline at depth 0, unless the next code continues it ({, where, ->, ., =).
                k = j + 1
                if ch == "\n" or (ch in "};" and False):
                    pass
        if t[j] == "\n" and depth == 0 and start is not None:
            rest = t[j + 1:c].lstrip()
            prev = t[start:j].rstrip()
            cont = rest[:1] in ("{", ".", "=", ":", ",", "-", "?", "&", "|", ")") or rest.startswith(("where ", "->", "throws", "async", "rethrows")) or prev.endswith((",", "=", "(", "->", "&&", "||", ":")) or re.fullmatch(r"(?:\s*@[\w.]+(?:\([^)]*\))?)+", prev[prev.rfind("\n") + 1:] if "\n" in prev else prev) is not None
            if not cont:
                out.append((start, j))
                start = None
        j += 1
    if start is not None and t[start:c].strip():
        out.append((start, c))
    return out



INDEX = {}
DECLRE = re.compile(r"\b(?:struct|enum|class|actor|protocol|typealias)\s+(" + IDENT + r")")


def target_index(pkg, rel):
    """parent type path -> names declared directly in its body or its extensions, over the whole target directory."""
    tdir = os.path.join(pkg, *rel.split("/")[:2])
    if tdir in INDEX: return INDEX[tdir]
    ix = {}
    for f in glob.glob(os.path.join(tdir, "**/*.swift"), recursive=True):
        try: t = open(f, encoding="utf8").read()
        except OSError: continue
        mask, pairs = scan(t)
        tops = [o for o in pairs if enclosing(pairs, o) is None]
        for o in tops:
            kind, name, _, _ = info(t, mask, o)
            if kind not in ("ext", "type", "generic") or not name: continue
            c = pairs[o]
            inner = sorted(x for x in pairs if o < x < c)
            for m in DECLRE.finditer(t, o + 1, c):
                if not mask[m.start()]: continue
                if any(x < m.start() < pairs[x] for x in inner): continue  # deeper than one level
                ix.setdefault(name, set()).add(m[1])
                # members of that nested type, for shadowing checks
            for x in inner:
                if enclosing(pairs, x) != o: continue
                k2, n2, _, _ = info(t, mask, x)
                if k2 in ("type", "generic") and n2:
                    for m in DECLRE.finditer(t, x + 1, pairs[x]):
                        if mask[m.start()]: ix.setdefault(name + "." + n2, set()).add(m[1])
    INDEX[tdir] = ix
    return ix


def qualify(chunk, parent, own, ix):
    mask, _ = scan(chunk)
    nested = re.search(r"\b(?:struct|enum|class|actor)\s+" + IDENT, chunk) is not None
    sib = ix.get(parent, set()) - ix.get(parent + "." + own, set())
    out, last = [], 0
    for m in re.finditer(r"(?<![.\w`])([A-Z][A-Za-z0-9_]*)\b", chunk):
        if not mask[m.start()]: continue
        n = m[1]
        if n == own: rep = (parent + "." + own) if nested else "Self"
        elif n in sib: rep = parent + "." + n
        else: continue
        out.append(chunk[last:m.start()]); out.append(rep); last = m.end()
    out.append(chunk[last:])
    return "".join(out)


moved_types = 0
moved_members = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    pkg = os.path.join(root, "repos", p)
    by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "minimal type body":
            by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    for rel, lines in sorted(by_file.items()):
        path = os.path.join(pkg, rel)
        if not os.path.exists(path) or not rel.startswith(("Sources/", "Tests/")): skip("gone"); continue
        t = open(path, encoding="utf8").read()
        mask, pairs = scan(t)
        L = t.split("\n")
        offs = [0]
        for l in L: offs.append(offs[-1] + len(l) + 1)
        edits = []
        typelines = set()
        for ln in sorted(set(lines)):
            if ln > len(L): skip("stale"); continue
            pos = offs[ln - 1] + len(L[ln - 1]) - len(L[ln - 1].lstrip())
            if re.search(r"\b(struct|enum|actor|class|protocol)\s+" + IDENT, L[ln - 1]) and not enclosing(pairs, pos):
                typelines.add(ln); continue
            br = enclosing(pairs, pos)
            if br is None: skip("not in a type"); continue
            tl = t.count("\n", 0, br) + 1
            # The type's declaration line: the line holding its keyword before the brace.
            hs = t.rfind("\n", 0, br) + 1
            k = tl
            while k > 0 and not re.search(r"\b(struct|enum|actor|class|protocol|extension)\s+" + IDENT, L[k - 1]):
                k -= 1
                if tl - k > 8: break
            if k > 0 and re.search(r"\b(struct|enum|actor|class|protocol)\s+" + IDENT, L[k - 1]):
                typelines.add(k)
            else:
                skip("container not a type")
        for ln in sorted(typelines):
            m = re.search(r"\b(struct|enum|actor|class|protocol)\s+(" + IDENT + r")", L[ln - 1])
            if not m: skip("no type on line"); continue
            if m[1] in ("class", "protocol"): skip(m[1]); continue
            npos = offs[ln - 1] + m.start(2)
            if not mask[npos]: skip("stale"); continue
            o = t.find("{", npos)
            while o >= 0 and not mask[o]: o = t.find("{", o + 1)
            if o < 0 or o not in pairs: skip("no body"); continue
            c = pairs[o]
            outer = enclosing(pairs, npos)
            prefix, anchor = "", c
            if outer is not None:
                if enclosing(pairs, outer) is not None: skip("nested deeper"); continue
                ok_, oname, _, _ = info(t, mask, outer)
                if ok_ not in ("ext", "type") or not oname or "<" in t[t.rfind("\n", 0, outer):outer] and ok_ == "type":
                    skip("outer not usable"); continue
                prefix, anchor = oname + ".", pairs[outer]
            header = t[offs[ln - 1]:o]
            if "~Copyable" in header or "~Escapable" in header: skip("noncopyable"); continue
            body = t[o + 1:c]
            if re.search(r"^\s*#(?:if|else|elseif|endif)\b", body, re.M): skip("#if in body"); continue
            if t[c + 1:t.find("\n", c) if t.find("\n", c) >= 0 else len(t)].strip(): skip("shares lines"); continue
            tlevel = access(L[ln - 1][:m.start()])
            name = m[2]
            gen = re.match(r"\s*<", t[offs[ln - 1] + m.end():])
            move = []
            for s, e in members(t, mask, o, c):
                code = "".join(ch if mask[s + k] else " " for k, ch in enumerate(t[s:e]))
                km = re.match(r"\s*" + MOD + r"(\w+)", code)
                if not km: continue
                kw = km[1]
                mods = code[:km.end(1)]
                static = re.search(r"\b(static|class)\b", mods)
                if kw in ("case", "init", "deinit"): continue
                if kw in ("let", "var") and not static:
                    # Stored unless `var name: T {` (a computed property): a body brace with no `=` before it.
                    if kw == "let": continue
                    br = code.find("{")
                    if br < 0 or "=" in code[:br] or re.search(r"\b(?:willSet|didSet)\b", code): continue
                elif kw not in ("func", "subscript", "typealias", "struct", "enum", "class", "actor", "protocol", "let", "var"):
                    continue
                if access(mods) > max(tlevel, 2) or (access(mods) > tlevel and tlevel < 2):
                    continue
                if re.search(r"@(?:objc|IBAction|IBOutlet|NSManaged)\b", mods): continue
                # Include the member's leading doc comments and attributes (already in s..e via start), and blank line.
                ls = t.rfind("\n", 0, s) + 1
                k = ls
                while True:
                    pl = t.rfind("\n", 0, k - 1) + 1
                    if k <= o + 1 or pl <= o: break
                    prev = t[pl:k - 1].strip()
                    if prev.startswith(("///", "//", "/*", "*")) or (prev.startswith("@") and not re.search(r"\b(?:var|let|func|case|init)\b", prev)):
                        k = pl; continue
                    break
                ee = t.find("\n", e) if t.find("\n", e) >= 0 and t.find("\n", e) < c else e
                move.append((k, ee))
            if not move: skip("nothing to move"); continue
            if gen and False: pass
            ind = "" if prefix else re.match(r"[ \t]*", L[ln - 1]).group(0)
            chunks = [t[s:e].rstrip() for s, e in move]
            if prefix:
                chunks = [re.sub(r"(?m)^    ", "", ch) if all(not l.strip() or l.startswith("    ") for l in ch.split("\n")) else ch for ch in chunks]
                ix = target_index(pkg, rel)
                chunks = [qualify(ch, prefix[:-1], name, ix) for ch in chunks]
            ext = "\n\n" + ind + "extension " + prefix + name + " {\n" + "\n\n".join(chunks) + "\n" + ind + "}"
            ce = t.find("\n", anchor); ce = len(t) if ce < 0 else ce
            for s, e in move:
                edits.append((s, e + 1 if e < c else e, ""))
            edits.append((ce, ce, ext))
            moved_types += 1; moved_members += len(move)
        if not edits: continue
        edits.sort(key=lambda x: (x[0], x[1]))
        out, last = [], 0
        ok = True
        for s, e, rep in edits:
            if s < last: ok = False; break
            out.append(t[last:s]); out.append(rep); last = e
        if not ok: skip("overlap"); continue
        out.append(t[last:])
        new = "".join(out)
        new = re.sub(r"\{\n(?:[ \t]*\n)+", "{\n", new)
        new = re.sub(r"\n(?:[ \t]*\n){2,}", "\n\n", new)
        new = re.sub(r"\n(?:[ \t]*\n)+([ \t]*\})", r"\n\1", new)
        print(p, rel)
        if not dry: open(path, "w", encoding="utf8").write(new)
print("types", moved_types, "members", moved_members, "skips", stats, file=sys.stderr)
