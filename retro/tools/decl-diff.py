#!/usr/bin/env python3
"""Declarations lost or duplicated between two refs of one checkout, Sources only.
Lost: a normalized declaration line removed more often than added (a move keeps it).
Duplicated: a type declaration (struct/enum/class/actor/protocol N) added more often than removed, where the name is now
declared more than once in the same target directory, and more often than at base.
Usage: decl-diff.py <checkout> <base-ref> <head-ref>  -> one JSON line."""
import collections, json, re, subprocess, sys

d, base, head = sys.argv[1:4]
MODS = r"(?:@[A-Za-z_]+(?:\([^)]*\))?\s+)*(?:(?:public|package|internal|fileprivate|private|open|static|final|mutating|nonmutating|override|nonisolated|consuming|borrowing|indirect|convenience|required|lazy|weak|unowned|dynamic|optional|prefix|postfix|infix)\s+)*"
DECL = re.compile(r"^\s*" + MODS + r"(func|init|deinit|subscript|var|let|case|struct|enum|class|actor|protocol|typealias|extension)\b(.*)$")
TYPE = re.compile(r"^\s*" + MODS + r"(struct|enum|class|actor|protocol)\s+(`[^`]+`|\w+)")


def norm(line):
    m = DECL.match(line)
    if not m: return None
    s = (m.group(1) + m.group(2)).strip()
    s = re.sub(r"\s*\{.*$", "", s); s = s.replace("::", "."); s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b(?:Swift|Self)\.", "", s)
    return s


diff = subprocess.run(["git", "-C", d, "diff", "-U0", "--no-renames", base, head, "--", "Sources"], capture_output=True, text=True, errors="replace").stdout
rem, add, add_types = collections.Counter(), collections.Counter(), collections.Counter()
cur = None
for line in diff.split("\n"):
    if line.startswith("+++ b/"): cur = line[6:]
    elif line.startswith("-") and not line.startswith("---"):
        k = norm(line[1:]);  rem[k] += 1 if k else 0
    elif line.startswith("+") and not line.startswith("+++"):
        k = norm(line[1:]); add[k] += 1 if k else 0
        t = TYPE.match(line[1:])
        if t and cur: add_types[(t.group(2), "/".join(cur.split("/")[:2]))] += 1
lost = {k: rem[k] - add[k] for k in rem if k and rem[k] > add[k]}
dups = []
for (name, tdir), n in add_types.items():
    def count(ref):
        g = subprocess.run(["git", "-C", d, "grep", "-c", "-P", r"^\s*" + MODS + r"(struct|enum|class|actor|protocol)\s+" + re.escape(name) + r"\b", ref, "--", tdir],
                           capture_output=True, text=True, errors="replace").stdout
        return sum(int(x.rsplit(":", 1)[1]) for x in g.split("\n") if x.strip())
    h = count(head)
    if h > 1 and h > count(base): dups.append({"type": name, "target": tdir, "declared": h})
print(json.dumps({"repo": d, "lost": len(lost), "lost_lines": list(lost)[:15], "duplicated": dups}))
