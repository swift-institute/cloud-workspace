#!/usr/bin/env python3
"""For `single type per file`: moves each additional type declaration out to its own file `<Parent>.<Name>.swift`
(or `<Name>.swift` at top level) in the same directory, inside the original container's extension header
(`extension Parent { ... }`; a container type `struct Parent` becomes `extension Parent`), with the original file's
imports. Sources only. Skips: `private`/`fileprivate` anywhere in the file, a generic or protocol container, a nested
container, a target-wide file-name collision, a declaration sharing lines with other code.

    overnight/split-types.py <lint-dir> [--dry-run] [package ...]"""
import glob, json, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
lint, only, dry = args[0], set(args[1:]), "--dry-run" in sys.argv
IDENT = r"(?:`[^`\n]+`|[A-Za-z_][A-Za-z0-9_]*)"
IMPORT = re.compile(r"^(?:@[\w()]+\s+)*(?:(?:public|package|internal|private|fileprivate)\s+)?import\s", re.M)
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




moved = 0
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if only and p not in only: continue
    pkg = os.path.join(root, "repos", p)
    by_file = {}
    for x in json.load(open(f))["findings"]:
        if x["rule"] == "single type per file":
            by_file.setdefault(x["fileID"][2:], []).append(x["line"])
    for rel, lines in sorted(by_file.items()):
        if not rel.startswith("Sources/"): skip("not Sources"); continue
        path = os.path.join(pkg, rel)
        if not os.path.exists(path): skip("gone"); continue
        t = open(path, encoding="utf8").read()
        if re.search(r"\b(?:private|fileprivate)\b", t): skip("private in file"); continue
        tdir = os.path.join(pkg, *rel.split("/")[:2])
        existing = {os.path.basename(x) for x in glob.glob(os.path.join(tdir, "**/*.swift"), recursive=True)}
        mask, pairs = scan(t)
        L = t.split("\n")
        offs = [0]
        for l in L: offs.append(offs[-1] + len(l) + 1)
        imports = "\n".join(l for l in L if IMPORT.match(l))
        cuts, news = [], []
        for ln in sorted(set(lines)):
            if ln > len(L): skip("stale"); continue
            m = re.search(r"\b(struct|enum|class|actor|protocol)\s+(" + IDENT + r")", L[ln - 1])
            if not m: skip("stale"); continue
            npos = offs[ln - 1] + m.start(2)
            if not mask[npos]: skip("stale"); continue
            o = t.find("{", npos)
            while o >= 0 and not mask[o]: o = t.find("{", o + 1)
            if o < 0 or o not in pairs: skip("no body"); continue
            start = max(header_start(t, mask, npos)[0], decl_start(L, offs, ln - 1))
            end = t.find("\n", pairs[o]); end = len(t) if end < 0 else end
            if t[pairs[o] + 1:end].strip() or t[offs[ln - 1]:npos].count("{"): skip("shares lines"); continue
            name = m[2].strip("`")
            par = enclosing(pairs, npos)
            if par is None:
                fname, head, tail = name + ".swift", "", ""
                block = t[start:end]
            else:
                if enclosing(pairs, par) is not None: skip("nested container"); continue
                kind, cname, _, cstart = info(t, mask, par)
                hdr = t[cstart:par]
                if kind == "ext":
                    if "<" in cname: skip("generic container"); continue
                    head = hdr.rstrip() + " {\n"
                elif kind == "type":
                    if re.search(r"\bprotocol\b", hdr): skip("protocol container"); continue
                    attrs = re.findall(r"^\s*(@available\([^\n]*\))", hdr, re.M)
                    head = "".join(a + "\n" for a in attrs) + "extension " + cname + " {\n"
                else:
                    skip("other container"); continue
                fname = cname.replace("`", "") + "." + name + ".swift"
                tail = "\n}"
                block = t[start:end]
            if fname in existing or any(fname == n for _, n, _ in news): skip("file exists"); continue
            if len(re.findall(r"^\s*#if\b", t[start:end], re.M)) != len(re.findall(r"^\s*#endif\b", t[start:end], re.M)) or re.search(r"^\s*#(?:else|elseif)\b", t[start:end], re.M) and not re.search(r"^\s*#if\b", t[start:end], re.M):
                skip("crosses #if"); continue
            # Inside an #if around the container: the new file would lose the condition.
            pre = t[:start]
            if len(re.findall(r"^\s*#if\b", pre, re.M)) != len(re.findall(r"^\s*#endif\b", pre, re.M)):
                skip("under #if"); continue
            cuts.append((start, end))
            news.append((os.path.join(os.path.dirname(path), fname), fname, (imports + "\n\n" if imports else "") + head + block + tail + "\n"))
        if not cuts: continue
        # Overlapping cuts (a type inside a moved type): keep the outer one.
        cuts.sort()
        keep, keptnews = [], []
        for c, nw in sorted(zip(cuts, news)):
            if keep and c[0] < keep[-1][1]: skip("inside another moved type"); continue
            keep.append(c); keptnews.append(nw)
        out, last = [], 0
        for s, e in keep:
            cs = s
            pre = t[:s]
            if re.search(r"\n[ \t]*\n$", pre): cs = pre.rstrip(" \t").rstrip("\n").rfind("\n") + 1 if False else len(pre.rstrip(" \t")) - 1
            out.append(t[last:cs]); last = e
        out.append(t[last:])
        new = re.sub(r"\{\n\s*\n(\s*\})", r"{\n\1", "".join(out))
        for full, fname, text in keptnews:
            moved += 1
            print(p, rel, "->", fname)
            if not dry:
                open(full, "w", encoding="utf8").write(text)
        if not dry:
            open(path, "w", encoding="utf8").write(new)
            subprocess.run(["git", "-C", pkg, "add", "--", *[os.path.relpath(n[0], pkg) for n in keptnews]])
print("moved", moved, "skips", stats, file=sys.stderr)
