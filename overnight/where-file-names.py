#!/usr/bin/env python3
"""For `extension file naming`'s "must use the 'T where <discriminator>.swift' shape": renames the file (git mv) to
`T where <clause>.swift` when every top-level extension of T in it has the same where clause. `:` is written ` is `
(as `Array where Element is Lint.Rule.Configuration.swift`); a clause with characters some file systems reject
(<>:"|?*\\/) or a name already used in the target is skipped. Usage: overnight/where-file-names.py <lint-dir> [--dry-run]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, dry = sys.argv[1], "--dry-run" in sys.argv
stats = {}; n = 0
def skip(w): stats[w] = stats.get(w, 0) + 1
for f in sorted(glob.glob(os.path.join(lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1); d = os.path.join(root, "repos", p)
    done = set()
    for x in json.load(open(f))["findings"]:
        if x["rule"] != "extension file naming": continue
        m = re.search(r"must use the '(.+) where <discriminator>\.swift' shape", x["message"])
        if not m: continue
        rel = x["filePath"][2:]
        if rel in done: continue
        done.add(rel)
        if not rel.startswith("Sources/"): skip("not Sources"); continue
        T = m.group(1); path = os.path.join(d, rel)
        try: t = open(path).read()
        except OSError: skip("gone"); continue
        ext = re.findall(r"^(?:public |package |internal )?extension\s+([\w.`]+)(?:\s*:\s*[^{]*?)?\s+where\s+([^{]+?)\s*\{", t, re.M)
        allext = re.findall(r"^(?:public |package |internal )?extension\s+([\w.`]+)", t, re.M)
        clauses = set(c.strip() for b, c in ext)
        if not ext or len(clauses) != 1 or len(ext) != len(allext): skip("mixed clauses"); continue
        clause = re.sub(r"\s*:\s*", " is ", clauses.pop())
        clause = re.sub(r"\s+", " ", clause)
        if re.search(r'[<>:"|?*\\/]', clause): skip("bad chars"); continue
        new = f"{T} where {clause}.swift"
        if len(new) > 120: skip("too long"); continue
        tdir = os.path.join(d, *rel.split("/")[:2])
        if any(os.path.basename(y) == new for y in glob.glob(os.path.join(tdir, "**", "*.swift"), recursive=True)): skip("exists"); continue
        dest = os.path.join(os.path.dirname(rel), new)
        n += 1
        if dry: print(p, rel, "->", new); continue
        subprocess.run(["git", "-C", d, "mv", rel, dest], check=True)
print("renamed", n, "skips", stats, file=sys.stderr)
