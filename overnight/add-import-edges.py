#!/usr/bin/env python3
"""Declares the target dependency `target import edge` reports missing, when the imported module is a target of the
same package (`.target(name:)`) or a product of a package the manifest already depends on (`.product(name:package:)`).

    overnight/add-import-edges.py <lint-dir> <dumps-dir> [--dry-run]

Edits the committed manifest (the index copy) and writes it to the checkout with skip-worktree cleared, so it can be
committed; run ./localize.py afterwards. Skipped: an import in a file with `#if` (it may be platform- or trait-gated,
and an unconditional edge would change the graph there), a module no declared package provides, and any manifest
whose dump after the edit differs from before in anything but the added dependencies."""
import argparse, collections, glob, json, os, re, subprocess, sys, tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = argparse.ArgumentParser()
a.add_argument("lint")
a.add_argument("dumps")
a.add_argument("--dry-run", action="store_true")
args = a.parse_args()


def norm(s):
    return s.replace(" ", "_").replace("-", "_")


def git(repo, *xs):
    return subprocess.run(["git", "-C", repo, *xs], capture_output=True, text=True)


dumps = {}
for f in glob.glob(os.path.join(args.dumps, "*.json")):
    try:
        dumps[os.path.basename(f)[:-5]] = json.load(open(f))
    except Exception:
        pass
by_identity = {m["name"].lower(): m for m in dumps.values()}

wanted = collections.defaultdict(lambda: collections.defaultdict(list))  # package -> target -> [entry]
for f in sorted(glob.glob(os.path.join(args.lint, "*.json"))):
    p = os.path.basename(f)[:-5].replace("__", "/", 1)
    for x in json.load(open(f))["findings"]:
        if x["rule"] != "target import edge":
            continue
        m = re.search(r": ([^:]+\.swift):(\d+): target '([^']+)' imports '([^']+)'", x["message"])
        if not m:
            continue
        source, _, target, module = m.groups()
        src = os.path.join(root, "repos", p, source)
        if not os.path.exists(src) or "#if" in open(src, encoding="utf8").read():
            print("SKIP conditional", p, target, module, file=sys.stderr)
            continue
        man = dumps.get(p.replace("/", "_"))
        if man is None:
            continue
        own = [t["name"] for t in man["targets"] if norm(t["name"]) == module]
        entry = None
        if own:
            entry = f'.target(name: "{own[0]}")'
        else:
            for dep in man["dependencies"]:
                info = list(dep.values())[0][0]
                dm = by_identity.get((info.get("identity") or "").lower())
                if not dm:
                    continue
                products = [q for q in dm["products"] if any(norm(t) == module for t in q["targets"])]
                products.sort(key=lambda q: (norm(q["name"]) != module, len(q["targets"])))
                if products:
                    entry = f'.product(name: "{products[0]["name"]}", package: "{info["identity"]}")'
                    break
        if entry is None:
            print("SKIP no provider", p, target, module, file=sys.stderr)
            continue
        if entry not in wanted[p][target]:
            wanted[p][target].append(entry)


def call_range(text, name_at):
    """The span of the `.target(` / `.testTarget(` call whose `name:` argument starts at name_at."""
    depth, i = 0, name_at
    while i > 0:
        i -= 1
        c = text[i]
        if c in ")]":
            depth += 1
        elif c in "([":
            if depth == 0:
                break
            depth -= 1
    start = i
    depth, j = 0, start
    while j < len(text):
        c = text[j]
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
            if depth == 0:
                return start, j
        elif c == '"':
            j = text.index('"', j + 1)
        j += 1
    raise ValueError("unbalanced")


def edited(text, target, entries):
    m = re.search(r'name:\s*"' + re.escape(target) + r'"', text)
    if not m:
        return None
    start, end = call_range(text, m.start())
    call = text[start:end]
    d = re.search(r"dependencies:\s*\[", call)
    indent = re.search(r"\n([ \t]*)[^\n]*$", text[:m.start()])
    pad = indent.group(1) if indent else "            "
    if d:
        at = start + d.end()
        close = call_range(text, at)[1] if False else None
        body_start = at
        # Insert before the list's closing bracket, after the last entry.
        depth, k = 1, at
        while depth:
            c = text[k]
            if c == "[" or c == "(":
                depth += 1
            elif c == "]" or c == ")":
                depth -= 1
            elif c == '"':
                k = text.index('"', k + 1)
            k += 1
        close = k - 1
        inner = text[body_start:close]
        if inner.strip() == "":
            insertion = ", ".join(entries)
            return text[:body_start] + insertion + text[close:]
        stripped = inner.rstrip()
        trailing_comma = stripped.endswith(",")
        multiline = "\n" in inner
        if multiline:
            item_pad = re.search(r"\n([ \t]*)\S", inner)
            ip = item_pad.group(1) if item_pad else pad + "    "
            insertion = ("" if trailing_comma else ",") + "".join(f"\n{ip}{e}," for e in entries)
        else:
            insertion = ("" if trailing_comma else ",") + "".join(f" {e}" + ("," if i < len(entries) - 1 else "") for i, e in enumerate(entries))
        pos = body_start + len(stripped)
        return text[:pos] + insertion + text[pos:]
    after = m.end()
    comma = text.index(",", after) if text[after:].lstrip().startswith(",") else None
    if comma is None:
        return None
    return text[:comma + 1] + f"\n{pad}dependencies: [{', '.join(entries)}]," + text[comma + 1:]


def dump(text, package):
    with tempfile.TemporaryDirectory(dir="/home/user/tools/tmp") as d:
        mirror = os.path.join("/home/user/lintmirror", package)
        for entry in os.listdir(mirror):
            if entry != "Package.swift":
                os.symlink(os.path.join(mirror, entry), os.path.join(d, entry))
        open(os.path.join(d, "Package.swift"), "w").write(text)
        r = subprocess.run(["swift", "package", "dump-package", "--package-path", d], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else None


os.makedirs("/home/user/tools/tmp", exist_ok=True)
for p, targets in sorted(wanted.items()):
    repo = os.path.join(root, "repos", p)
    before_text = git(repo, "show", ":Package.swift").stdout
    text = before_text
    for target, entries in targets.items():
        new = edited(text, target, entries)
        if new is None:
            print("SKIP shape", p, target, file=sys.stderr)
            continue
        text = new
    if text == before_text:
        continue
    before, after = dump(before_text, p), dump(text, p)
    if before is None or after is None:
        print("SKIP dump failed", p, file=sys.stderr)
        continue
    ok = True
    for tb, ta in zip(before["targets"], after["targets"]):
        added = [x for x in ta["dependencies"] if x not in tb["dependencies"]]
        if ta["dependencies"][:0] != [] or [x for x in tb["dependencies"] if x not in ta["dependencies"]]:
            ok = False
        expected = len(targets.get(ta["name"], []))
        if len(added) != expected:
            ok = False
        tb2, ta2 = dict(tb), dict(ta)
        tb2.pop("dependencies"), ta2.pop("dependencies")
        if tb2 != ta2:
            ok = False
    for key in before:
        if key not in ("targets", "packageKind") and before[key] != after[key]:
            ok = False
    if not ok:
        why = [(ta["name"], [x for x in ta["dependencies"] if x not in tb["dependencies"]], targets.get(ta["name"]))
               for tb, ta in zip(before["targets"], after["targets"]) if tb != ta]
        why += [k for k in before if k not in ("targets", "packageKind") and before[k] != after[k]]
        print("SKIP dump differs beyond the added edges", p, json.dumps(why)[:400], file=sys.stderr)
        continue
    n = sum(len(e) for e in targets.values())
    print(p, n, "edges")
    if not args.dry_run:
        git(repo, "update-index", "--no-skip-worktree", "Package.swift")
        open(os.path.join(repo, "Package.swift"), "w").write(text)
