#!/usr/bin/env python3
"""Fixes two leftovers of the findings round's type splits (coenttb/work#242) from a swift build log.

    fix-split-leftovers.py <package dir> <build log>

1. "public import of 'X' was not used in public declarations": the split copied the type file's imports; the
   import becomes internal (`import X`), so any internal use still compiles.
2. "extension outside of file declaring <kind> 'T' prevents automatic synthesis" / "conformance to 'Sendable' must
   occur in the same source file": the split moved T to `<Owner>.T.swift` but left its conformance block
   (`extension Owner.T: P where … {}` lines, with an `#if !hasFeature(Embedded)` Codable line) behind. The block
   moves to the end of T's file, and an empty `extension Owner {\n}` it leaves is removed.

3. "cannot find 'X' in scope" / "cannot find type 'X' in scope" where a minimal-body move took a member out of its
   type's body into `extension Owner.T`: X was a sibling of T, found through T's lexical scope. It's qualified with
   Owner, the enclosing extension's type minus its last component, where it was declared before the move. Paths in
   the log may be a container's (`/pkg/...`): pass `--prefix /pkg` to map them onto <package dir>.

Prints each change; changes nothing else. Rebuild after it, since a fix can uncover the next error."""
import os, re, sys

package, log = sys.argv[1], sys.argv[2]
text = re.sub(r"\x1b\[[0-9;]*m", "", open(log, errors="replace").read())
root = os.path.realpath(package)

imports = set()
for path, line, module in re.findall(r"^(/[^:\n]+\.swift):(\d+):\d+: error: public import of '([^']+)' was not used", text, re.M):
    if os.path.realpath(path).startswith(root + "/"):
        imports.add((path, int(line), module))
for path, line, module in sorted(imports):
    lines = open(path).read().split("\n")
    if lines[line - 1].strip() == f"public import {module}":
        lines[line - 1] = lines[line - 1].replace("public import", "import", 1)
        open(path, "w").write("\n".join(lines))
        print(f"import internal: {os.path.relpath(path, root)}:{line} {module}")

synth = set()
for m in re.finditer(
    r"^(/[^:\n]+\.swift):\d+:\d+: error: (?:extension outside of file declaring \w+ '(\w+)'|conformance to 'Sendable' must occur in the same source file as \w+ '(\w+)')",
    text, re.M,
):
    path = m.group(1)
    if os.path.realpath(path).startswith(root + "/"):
        synth.add((path, m.group(2) or m.group(3)))

for path, name in sorted(synth):
    source = open(path).read()
    block = re.search(
        r"((?:^extension ([\w.]+\." + name + r"): [^\n]*\{\}\n|^#if !hasFeature\(Embedded\)\n    extension [\w.]+\." + name
        + r": Codable[^\n]*\{\}\n#endif\n)+)",
        source, re.M,
    )
    if not block:
        print(f"no block for {name} in {os.path.relpath(path, root)}")
        continue
    full = re.search(r"extension ([\w.]+\." + name + r"):", block.group(1)).group(1)
    owner_file = os.path.join(os.path.dirname(path), full + ".swift")
    if not os.path.exists(owner_file):
        print(f"no file {os.path.basename(owner_file)} for {full}")
        continue
    source = source.replace(block.group(1), "", 1)
    parent = full.rsplit(".", 1)[0]
    source = source.replace(f"extension {parent} {{\n}}\n\n", "", 1)
    source = re.sub(r"\n{3,}", "\n\n", source)
    open(path, "w").write(source)
    with open(owner_file, "a") as f:
        f.write("\n" + block.group(1))
    print(f"conformances moved: {full} -> {os.path.relpath(owner_file, root)}")

prefix = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else None
edits = {}
for path, line, col, name in re.findall(
    r"^(/[^:\n]+\.swift):(\d+):(\d+): error: cannot find (?:type )?'(\w+)' in scope", text, re.M
):
    if prefix and path.startswith(prefix + "/"):
        path = os.path.join(root, path[len(prefix) + 1:])
    if os.path.realpath(path).startswith(root + "/"):
        edits.setdefault(path, set()).add((int(line), int(col), name))
for path, items in sorted(edits.items()):
    lines = open(path).read().split("\n")
    changed = 0
    for line, col, name in sorted(items, key=lambda x: (x[0], -x[1])):
        owner = None
        for k in range(line - 2, -1, -1):
            m = re.match(r"\s*extension ([\w.]+)", lines[k])
            if m and lines[k].startswith(" " * (len(lines[k]) - len(lines[k].lstrip()))):
                owner = m.group(1)
                break
        if not owner or "." not in owner:
            continue
        parent = owner.rsplit(".", 1)[0]
        text_line = lines[line - 1]
        i = col - 1
        if text_line[i:i + len(name)] != name or (i > 0 and text_line[i - 1] == "."):
            continue
        lines[line - 1] = text_line[:i] + parent + "." + text_line[i:]
        changed += 1
    if changed:
        open(path, "w").write("\n".join(lines))
        print(f"qualified {changed}: {os.path.relpath(path, root)}")
