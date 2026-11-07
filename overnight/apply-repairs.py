#!/usr/bin/env python3
"""Applies the runner's own repair rewrites for one rule from a lint-all.sh run, to the checkouts.

    overnight/apply-repairs.py <lint-dir> <rule> [--tier T ...] [--package owner/name ...] [--dry-run]

Only a file whose working copy still equals what was linted is rewritten. Sources outside Sources/ and Tests/
(Examples, Benchmarks, Package.swift) are left alone unless the rule is a manifest rule. A changed file is then
formatted with the Institute policy's swift-format configuration if its committed version is already stable under
it; otherwise only blank lines left behind are tidied (no leading blank lines, at most one in a row). A file the
repair would empty is left alone: it may be its target's only source. Prints one line per file changed."""
import argparse, glob, json, os, re, subprocess, sys, tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.environ.get("SWIFT_FORMAT_CONFIG", "/home/user/tools/swift-format.json")
MANIFEST_RULES = {"trait consistency", "canonical settings tail"}


def tier(p):
    o = p.split("/")[0]
    return {"swift-atoms": "atoms", "swift-molecules": "molecules", "swift-compositions": "compositions",
            "swift-institute": "compositions", "coenttb": "coenttb"}.get(o, "standards")


def git(repo, *args, input=None):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, input=input)


def swift_format(text):
    with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, dir="/home/user/tools/tmp") as f:
        f.write(text)
        name = f.name
    try:
        r = subprocess.run(["swift-format", "format", "--configuration", CONFIG, name], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    finally:
        os.unlink(name)


def tidy(text):
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.lstrip("\n")
    text = re.sub(r"\{\n\n", "{\n", text)
    text = re.sub(r"\n\n(\s*\})", r"\n\1", text)
    return text if text.endswith("\n") else text + "\n"


a = argparse.ArgumentParser()
a.add_argument("lint")
a.add_argument("rule")
a.add_argument("--tier", action="append")
a.add_argument("--package", action="append")
a.add_argument("--dry-run", action="store_true")
a.add_argument("--no-format", action="store_true")
a.add_argument("--require-format", action="store_true", help="skip a file whose committed version isn't swift-format-stable")
a.add_argument("--skip-containing", action="append", default=[], help="skip a file whose text contains this")
args = a.parse_args()
os.makedirs("/home/user/tools/tmp", exist_ok=True)

changed = 0
for f in sorted(glob.glob(os.path.join(args.lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    if args.tier and tier(p) not in args.tier:
        continue
    if args.package and p not in args.package:
        continue
    d = json.load(open(f))
    repo = os.path.join(root, "repos", p)
    for r in d["repairProposals"]:
        if r["rule"] != args.rule or r["proposal"]["status"] != "edits":
            continue
        for e in r["proposal"]["edits"]:
            if e["operation"] != "rewrite":
                print("SKIP operation", e["operation"], p, e.get("path"), file=sys.stderr)
                continue
            rel = e["path"]
            manifest = rel == "Package.swift"
            if manifest != (args.rule in MANIFEST_RULES):
                print("SKIP scope", p, rel, file=sys.stderr)
                continue
            if not manifest and not (rel.startswith("Sources/") or rel.startswith("Tests/")):
                print("SKIP outside Sources/Tests", p, rel, file=sys.stderr)
                continue
            path = os.path.join(repo, rel)
            mirror = os.path.join("/home/user/lintmirror", p.replace("/", "__", 1), os.path.basename(p), rel)
            if manifest:
                current = git(repo, "show", ":Package.swift").stdout
            else:
                current = open(path, encoding="utf8").read() if os.path.exists(path) else None
            linted = open(mirror, encoding="utf8").read() if os.path.exists(mirror) else None
            if current is None or current != linted:
                print("SKIP changed since lint", p, rel, file=sys.stderr)
                continue
            if any(token in current for token in args.skip_containing):
                print("SKIP contains", p, rel, file=sys.stderr)
                continue
            new = e["contents"]
            if not args.no_format:
                head = git(repo, "show", f"HEAD:{rel}").stdout
                stable = head and swift_format(head) == head
                formatted = swift_format(new) if stable else None
                if formatted is None and args.require_format:
                    print("SKIP not formattable", p, rel, file=sys.stderr)
                    continue
                new = formatted if formatted is not None else tidy(new)
            if new == current:
                continue
            changed += 1
            print(p, rel, "formatted" if not args.no_format and formatted is not None else "tidied")
            if args.dry_run:
                continue
            if not new.strip():
                print("SKIP would empty the file (a target may have no other source)", p, rel, file=sys.stderr)
                continue
            if manifest:
                git(repo, "update-index", "--no-skip-worktree", "Package.swift")
            open(path, "w", encoding="utf8").write(new)
print(f"{changed} files", file=sys.stderr)
