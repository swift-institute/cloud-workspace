#!/usr/bin/env python3
"""Labels every remaining lint finding: script / rename / new type (semantic pass) / module rename (structure step) /
likely false positive / hand or held. Reads count-lint.py output (with items) and the checkouts for the lines it needs.
Usage: retro/tools/label-remaining.py <count-lint.json> [repos-dir]  -> JSON on stdout, table on stderr."""
import collections, json, os, re, sys

lint = json.load(open(sys.argv[1]))
repos = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "../../repos")
cache = {}


def lines(pkg, f):
    k = (pkg, f)
    if k not in cache:
        p = os.path.join(repos, pkg, f[2:] if f.startswith("./") else f)
        try:
            cache[k] = open(p, encoding="utf8", errors="replace").read().split("\n")
        except OSError:
            cache[k] = []
    return cache[k]


SEMANTIC = {"compound identifier", "int public parameter", "bool public parameter", "raw value access",
            "unchecked call site", "bitpattern rawvalue chain", "fatal error outside tests",
            "zero or one literal", "string utf8 scanning", "pointer advanced by"}
LIKELY_FP = {  # audit sample false-positive rate >= 70% and the rule not narrowed since (audit/rules-table.md)
    "namespace adoption typealias": "audit 14/20 false", "typealiased namespace bridge": "audit 17/20 false",
    "throwing wrapper init": "audit 19/20 false", "existential parameter": "kept by decision; its tests pin the shape",
    "try optional": "audit 14/20 false", "chained rawvalue access": "audit 16/20 false",
    "unification typealias": "audit 16/20 false (private/local narrowed since, a9c0302)"}
SCRIPT = {"compound suite name", "counter loop iteration", "exported import", "architecture import boundary",
          "module selector spelling", "test function naming", "test display name string", "statement where expression fits",
          "count minus one"}
STRUCTURE = {"test target naming", "manifest naming grammar", "untraited partial dependency", "undeclared module import",
             "target import edge"}
HELD = {"trait consistency": "manifest repair breaks resolution (swift-parser 652ba46)",
        "canonical settings tail": "behaviour change (warnings as errors)"}


def label(it):
    r, m, pkg, f, ln = it["rule"], it["message"], it["package"], it.get("file") or "", it.get("line") or 0
    tests = "/Tests/" in f or f.startswith("./Tests")
    if r in HELD: return "held", HELD[r]
    if r in LIKELY_FP: return "likely false positive", LIKELY_FP[r]
    if r in SEMANTIC: return "new type (semantic pass)", r
    if r in SCRIPT: return "script", r
    if r in STRUCTURE: return "module rename (structure step)", r
    if r == "untyped throws":
        return ("likely false positive", "untyped throws in tests (audit: real by letter, low value)") if tests else ("new type (semantic pass)", "typed error per API")
    if r == "path name grammar":
        if "directory '" in m:
            d = re.search(r"directory '([^']+)'", m).group(1)
            parts = f.lstrip("./").split("/")
            target_dir = len(parts) > 1 and parts[1] == d  # Sources/<Target> or Tests/<Target>: the module's name
            return ("module rename (structure step)", "target directory = module name") if target_dir else ("rename", "directory inside a target")
        return "rename", "file name segment"
    if r == "file name nested path": return "rename", r
    if r == "minimal type body":
        src = lines(pkg, f)
        decl = src[ln - 1] if 0 < ln <= len(src) else ""
        body = "\n".join(src[ln - 1: ln + 80])
        if re.search(r"\bclass\b", decl): return "hand", "class (extension members can't be overridden)"
        if "~Copyable" in decl or "~Escapable" in decl: return "script", "minimal-bodies v2: ~Copyable/~Escapable constraint on the extension"
        if re.search(r"^\s*#if", body, re.M): return "hand", "#if inside the body"
        if decl[:len(decl) - len(decl.lstrip())].strip() == "" and decl.startswith((" ", "\t")): return "script", "minimal-bodies v2: nested type, qualify sibling names"
        return "script", "minimal-bodies v2: plain"
    if r == "single type per file":
        src = "\n".join(lines(pkg, f))
        if re.search(r"\b(private|fileprivate)\s+(struct|enum|class|actor|protocol)\b", src): return "hand", "private type (rule narrowed for some)"
        if re.search(r"^\s*#if", src, re.M): return "hand", "#if in file"
        return "script", "split-types v2 (transactional)"
    if r == "compound type name":
        if tests: return "script", "test-local type: fileprivate or nest under the suite"
        return "rename", "public or cross-file type: nested name, callers updated"
    if r == "extension file naming":
        if "mixes extensions" in m: return "script", "split by base type"
        if "must use the" in m: return "rename", "file rename to the lawful shape"
        return "script", "merge-extension-files v2 (transactional)"
    if r == "do throws for typed catch": return "hand", "error handling: needs the callee's error type"
    return "hand", "small rule"


out = collections.defaultdict(lambda: collections.Counter())
detail = collections.defaultdict(lambda: collections.Counter())
for it in lint["items"]:
    lab, why = label(it)
    out[it["rule"]][lab] += 1
    detail[lab][f"{it['rule']}: {why}"] += 1
tot = collections.Counter()
for r, c in out.items(): tot.update(c)
rows = sorted(out.items(), key=lambda kv: -sum(kv[1].values()))
json.dump({"total": sum(tot.values()), "by_label": dict(tot.most_common()),
           "by_rule": {r: dict(c.most_common()) for r, c in rows},
           "detail": {l: dict(c.most_common()) for l, c in detail.items()}}, sys.stdout, indent=1)
print(f"total {sum(tot.values())}", file=sys.stderr)
for l, k in tot.most_common(): print(f"  {l:32} {k:6}  {100 * k / sum(tot.values()):4.1f}%", file=sys.stderr)
