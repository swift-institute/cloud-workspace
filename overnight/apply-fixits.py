#!/usr/bin/env python3
"""Applies the compiler's own fix-its for chosen warning kinds, read from the .dia files under the shared scratch.

    overnight/apply-fixits.py <kind> [<kind> ...] [--package owner/name ...] [--dry-run]

Skipped: a file changed after its .dia was written (offsets would be stale), a file with any `#if` (the warning
may hold on this platform only), and overlapping fix-its. Prints one line per file changed."""
import argparse, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dia

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repos = os.path.join(root, "repos")
a = argparse.ArgumentParser()
a.add_argument("kinds", nargs="+")
a.add_argument("--package", action="append")
a.add_argument("--scratch", default="/home/user/scratch-warn")
a.add_argument("--dry-run", action="store_true")
args = a.parse_args()

edits = {}  # real path -> {(start, end, text)}
dia_time = {}
for path in glob.glob(os.path.join(args.scratch, "**", "*.dia"), recursive=True):
    try:
        entries = dia.read(path, fixits=True)
    except Exception:
        continue
    mtime = os.path.getmtime(path)
    for sev, file, line, col, message, flag, fixits in entries:
        kind = flag.rstrip("/").split("/")[-1] if flag else ""
        if sev != "warning" or kind not in args.kinds:
            continue
        if not fixits and kind == "unnecessary-effect-marker" and os.path.exists(file):
            # No fix-it attached: remove the marker the warning points at, when the source there is exactly it.
            lines = open(file, "rb").read().split(b"\n")
            offset = sum(len(l) + 1 for l in lines[:line - 1]) + col - 1
            text = lines[line - 1][col - 1:]
            for marker in (b"try ", b"await "):
                if marker.strip().decode() in message and text.startswith(marker) and not text.startswith(b"try?") and not text.startswith(b"try!"):
                    fixits = [(file, offset, offset + len(marker), "")]
        if not fixits:
            continue
        real = os.path.realpath(file)
        rel = os.path.relpath(real, repos)
        if rel.startswith(".."):
            continue
        if args.package and "/".join(rel.split("/")[:2]) not in args.package:
            continue
        if any(os.path.realpath(f) != real for f, *_ in fixits):
            continue
        edits.setdefault(real, set()).update((s, e, t) for _, s, e, t in fixits)
        dia_time[real] = min(dia_time.get(real, mtime), mtime)

changed = 0
for real, fixes in sorted(edits.items()):
    rel = os.path.relpath(real, repos)
    if os.path.getmtime(real) > dia_time[real]:
        print("SKIP changed since compiled", rel, file=sys.stderr)
        continue
    data = open(real, "rb").read()
    if b"#if" in data:
        print("SKIP conditional compilation", rel, file=sys.stderr)
        continue
    ordered = sorted(fixes, reverse=True)
    if any(ordered[i][0] < ordered[i + 1][1] for i in range(len(ordered) - 1)):
        print("SKIP overlapping fix-its", rel, file=sys.stderr)
        continue
    for start, end, text in ordered:
        data = data[:start] + text.encode() + data[end:]
    changed += 1
    print(rel, len(fixes))
    if not args.dry_run:
        open(real, "wb").write(data)
print(f"{changed} files", file=sys.stderr)
