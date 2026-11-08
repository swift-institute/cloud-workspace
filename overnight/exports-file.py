#!/usr/bin/env python3
"""For `exported import` and `architecture import boundary`: moves every whole-module `@_exported import M` outside
`#if` into the target's root `exports.swift` as `@_exported public import M` (created if missing; a root
`Exports.swift` or `*.exports.swift` is renamed or merged into it). The original file keeps `public import M`
(the type-check demotes an unused one); a file left with only imports and comments is removed. Scoped imports
(`@_exported import struct M.X`) and conditional ones stay. Re-export set per module is unchanged.

    overnight/exports-file.py [--dry-run] [package ...]"""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]; dry = "--dry-run" in sys.argv
pkgs = args or subprocess.run([root + "/overnight/packages.sh"], capture_output=True, text=True, cwd=root).stdout.split()
EXP = re.compile(r"^@_exported\s+(?:public\s+)?(?:@preconcurrency\s+)?import\s+(\w+)\s*(?://.*)?$")
stats = {"moved": 0, "files removed": 0, "created": 0, "renamed": 0, "conditional": 0, "scoped": 0}
def git(d, *a): return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
for p in pkgs:
    d = os.path.join(root, "repos", p)
    try: dump = json.load(open(os.path.join("/home/user/dumps", p.replace("/", "__", 1) + ".json")))
    except Exception: continue
    tpaths = {t["name"]: (t.get("path") or ("Sources/" if t["type"] != "test" else "Tests/") + t["name"]) for t in dump["targets"] if t["type"] in ("regular", "executable")}
    allpaths = [v.rstrip("/") for v in tpaths.values()]
    for name, tp in tpaths.items():
        tp = tp.rstrip("/"); td = os.path.join(d, tp)
        if not os.path.isdir(td): continue
        files = []
        for f in glob.glob(os.path.join(td, "**", "*.swift"), recursive=True):
            rel = os.path.relpath(f, d)
            if any(o != tp and o.startswith(tp + "/") and rel.startswith(o + "/") for o in allpaths): continue
            files.append(f)
        target_exports = os.path.join(td, "exports.swift")
        modules, edits, blocks = [], {}, []
        for f in files:
            if f == target_exports: continue
            lines = open(f).read().split("\n"); out = []; moved = []; i = 0
            while i < len(lines):
                l = lines[i]; s = l.strip()
                if s.startswith("#if"):
                    # A top-level #if block of import lines only moves whole.
                    j, depth = i, 0
                    while j < len(lines):
                        t = lines[j].strip()
                        if t.startswith("#if"): depth += 1
                        elif t.startswith("#endif"):
                            depth -= 1
                            if depth == 0: break
                        j += 1
                    block = lines[i:j + 1]
                    inner = [b.strip() for b in block[1:-1]]
                    onlyimports = j < len(lines) and all(not b or b.startswith(("#elseif", "#else", "//")) or re.match(r"^(@_exported\s+)?(public\s+|package\s+|internal\s+)?(@preconcurrency\s+)?import\s+\w+\s*$", b) for b in inner)
                    if onlyimports and any(b.startswith("@_exported") for b in inner) and all(not b.startswith("#if") for b in inner):
                        blocks.append([re.sub(r"^(\s*)@_exported\s+(?:public\s+)?", r"\1@_exported public ", b) if b.strip().startswith("@_exported") else b for b in block])
                        out += [re.sub(r"^(\s*)@_exported\s+(?:public\s+)?", r"\1public ", b) for b in block]
                        moved.append(None); i = j + 1; continue
                    if any(b.startswith("@_exported") for b in inner): stats["conditional"] += 1
                    out += block; i = j + 1; continue
                m = EXP.match(l)
                if m:
                    moved.append(m.group(1)); out.append(f"public import {m.group(1)}")
                else:
                    if s.startswith("@_exported"): stats["scoped"] += 1
                    out.append(l)
                i += 1
            if moved:
                modules += moved; edits[f] = out
        modules_real = [m for m in modules if m]
        existing0 = open(target_exports).read() if os.path.exists(target_exports) else ""
        needs_norm = any(re.match(r"^@_exported\s+(?!public\s)", l) for l in existing0.split("\n"))
        if not modules and not needs_norm: continue
        existing = open(target_exports).read() if os.path.exists(target_exports) else ""
        have = set(EXP.match(l).group(1) for l in existing.split("\n") if EXP.match(l))
        add = []
        for mname in modules_real:
            if mname not in have and mname not in add: add.append(mname)
        stats["moved"] += len(modules); stats["normalised"] = stats.get("normalised", 0) + (not modules)
        if dry: print(p, name, modules); continue
        for f, out in edits.items():
            base = os.path.basename(f)
            body = [l for l in out if l.strip() and not l.strip().startswith("//") and not re.match(r"^(public |package |internal )?(@preconcurrency )?import ", l.strip())]
            exportish = base.lower() == "exports.swift" or base.endswith(".exports.swift") or base.endswith("+exports.swift")
            if not body and (exportish or all(not re.match(r"^\s*$", l) or True for l in out)):
                git(d, "rm", "-qf", os.path.relpath(f, d)); stats["files removed"] += 1
            else:
                open(f, "w").write("\n".join(out))
        lines = existing.rstrip("\n").split("\n") if existing else []
        if not existing: stats["created"] += 1
        # Normalise existing whole-module re-exports to the admitted spelling.
        lines = [f"@_exported public import {EXP.match(l).group(1)}" if EXP.match(l) else l for l in lines]
        lines += [f"@_exported public import {m}" for m in add]
        for b in blocks:
            if "\n".join(b) not in "\n".join(lines): lines += [""] + b
        os.makedirs(td, exist_ok=True); open(target_exports, "w").write("\n".join(lines).lstrip("\n") + "\n")
        git(d, "add", os.path.relpath(target_exports, d))
print(stats, file=sys.stderr)
