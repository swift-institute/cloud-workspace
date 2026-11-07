#!/usr/bin/env python3
"""Ecosystem audit (coenttb/work#242), part 1.

Inputs, produced by audit/measure.sh:
  $AUDIT_WORK/extract.jsonl   one line per Swift file, from audit/extract (swift-syntax)
  $AUDIT_WORK/dump/*.json     `swift package dump-package` per repository
Outputs: audit/data/*.json and audit/data/*.md tables. Private repositories (private-repos.txt) are counted but
never named, and none of their type names reach audit/: they go to $AUDIT_WORK/private/ for coenttb/work#242.
"""
import collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ["AUDIT_WORK"]
OUT = os.path.join(ROOT, "audit", "data")
PRIV_OUT = os.path.join(WORK, "private")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRIV_OUT, exist_ok=True)

TIERS = ["atoms", "molecules", "standards", "compositions", "coenttb"]
TIER_RANK = {t: i for i, t in enumerate(TIERS)}


def tier_of(repo):
    o = repo.split("/")[0]
    if o == "swift-atoms": return "atoms"
    if o == "swift-molecules": return "molecules"
    if o in ("swift-compositions", "swift-institute"): return "compositions"
    if o == "coenttb": return "coenttb"
    return "standards"


def read_list(name):
    p = os.path.join(ROOT, name)
    return [l.strip() for l in open(p)] if os.path.exists(p) else []


PUBLIC = [r for r in read_list("repos.txt") if r]
PRIVATE = set(r for r in read_list("private-repos.txt") if r)
REPOS = PUBLIC + sorted(PRIVATE)


def dump(o, f):
    json.dump(o, open(os.path.join(OUT, f), "w"), indent=1, sort_keys=True)


# ---------------------------------------------------------------- manifests
manifests = {}
for r in REPOS:
    p = os.path.join(WORK, "dump", r.replace("/", "_") + ".json")
    try:
        manifests[r] = json.load(open(p))
    except Exception:
        manifests[r] = None

identity_to_repo = {r.split("/")[1].lower(): r for r in REPOS}
targets = {}          # (repo, target) -> info
module_to = {}        # module name -> (repo, target), library/regular targets
for r, m in manifests.items():
    if not m: continue
    for t in m["targets"]:
        path = t.get("path") or ("Tests/" if t["type"] == "test" else "Sources/") + t["name"]
        deps = []
        for d in t.get("dependencies", []):
            if "product" in d:
                deps.append(("product", d["product"][0], d["product"][1]))
            elif "target" in d:
                deps.append(("target", d["target"][0], None))
            elif "byName" in d:
                deps.append(("byName", d["byName"][0], None))
        targets[(r, t["name"])] = {"repo": r, "name": t["name"], "type": t["type"], "path": path.rstrip("/"), "deps": deps,
                                   "files": [], "test": t["type"] == "test"}
        if t["type"] in ("regular", "macro", "executable", "system", "binary", "plugin"):
            module_to.setdefault(t["name"].replace(" ", "_"), (r, t["name"]))

products = {}  # (repo, product) -> [targets]
for r, m in manifests.items():
    if not m: continue
    for p in m.get("products", []):
        products[(r, p["name"])] = p["targets"]
    m["_pkgdeps"] = set()
    for d in m.get("dependencies", []):
        for kind in ("fileSystem", "sourceControl", "registry"):
            if kind in d:
                ident = d[kind][0]["identity"]
                if ident in identity_to_repo:
                    m["_pkgdeps"].add(identity_to_repo[ident])


def resolve_dep(repo, dep):
    """Target-level dependency -> list of (repo, target)."""
    kind, name, pkg = dep
    if kind == "target" or (kind == "byName" and (repo, name) in targets):
        return [(repo, name)] if (repo, name) in targets else []
    if kind in ("product", "byName"):
        cands = []
        if pkg:
            pr = identity_to_repo.get(pkg.lower())
            if pr and (pr, name) in products:
                cands = [(pr, t) for t in products[(pr, name)]]
        else:
            for (pr, pn), ts in products.items():
                if pn == name and pr in manifests[repo].get("_pkgdeps", set()):
                    cands = [(pr, t) for t in ts]
        return [c for c in cands if c in targets]
    return []


for k, t in targets.items():
    t["resolved"] = sorted(set(x for d in t["deps"] for x in resolve_dep(k[0], d)))

closure_cache = {}


def closure(k):
    if k in closure_cache: return closure_cache[k]
    seen, stack = set(), [k]
    while stack:
        x = stack.pop()
        for y in targets.get(x, {}).get("resolved", []):
            if y not in seen:
                seen.add(y); stack.append(y)
    closure_cache[k] = seen
    return seen


# ---------------------------------------------------------------- files
files = []
target_paths = collections.defaultdict(list)
for (r, n), t in targets.items():
    target_paths[r].append((t["path"] + "/", (r, n)))
for r in target_paths:
    target_paths[r].sort(key=lambda x: -len(x[0]))

with open(os.path.join(WORK, "extract.jsonl")) as fh:
    for line in fh:
        f = json.loads(line)
        rel = f["file"][len("repos/"):] if f["file"].startswith("repos/") else f["file"]
        parts = rel.split("/")
        repo = "/".join(parts[:2]); inner = "/".join(parts[2:])
        if repo not in manifests: continue
        tk = None
        for prefix, k in target_paths.get(repo, []):
            if inner.startswith(prefix):
                tk = k; break
        f["repo"], f["inner"], f["target"] = repo, inner, tk
        f["test"] = (tk is not None and targets[tk]["test"]) or inner.startswith("Tests/") or "/Tests/" in inner
        f["idents"] = set(f["idents"])
        if tk: targets[tk]["files"].append(f)
        files.append(f)

# ---------------------------------------------------------------- 1. declared types
decls = []
for f in files:
    for d in f["decls"]:
        d = dict(d)
        d.update(repo=f["repo"], tier=tier_of(f["repo"]), module=f["target"][1] if f["target"] else None,
                 file=f["inner"], test=f["test"], private_repo=f["repo"] in PRIVATE)
        decls.append(d)
exts_by_repo = collections.defaultdict(list)
for f in files:
    for e in f["extensions"]:
        e = dict(e); e.update(file=f["inner"], test=f["test"], module=f["target"][1] if f["target"] else None)
        exts_by_repo[f["repo"]].append(e)

KINDS = ["struct", "enum", "class", "actor", "protocol", "typealias"]


def tally(ds):
    c = collections.Counter(d["kind"] for d in ds)
    return {k: c.get(k, 0) for k in KINDS} | {"total": len(ds)}


baseline = {"all": {"nontest": tally([d for d in decls if not d["test"]]), "test": tally([d for d in decls if d["test"]])},
            "by_tier": {t: {"nontest": tally([d for d in decls if d["tier"] == t and not d["test"]]),
                            "public_nontest": tally([d for d in decls if d["tier"] == t and not d["test"] and d["access"] in ("public", "open")])}
                        for t in TIERS},
            "public_nontest": tally([d for d in decls if not d["test"] and d["access"] in ("public", "open")]),
            "files": len(files), "repositories": len(REPOS), "private_repositories": len(PRIVATE)}
dump(baseline, "baseline.json")
pub_fields = ["repo", "tier", "module", "kind", "qualified", "access", "generic", "inherits", "file", "line", "endLine", "test"]
dump([{k: d.get(k) for k in pub_fields} | {"stored": len(d.get("stored", []))} for d in decls if not d["private_repo"]], "types.json")
json.dump([{k: d.get(k) for k in pub_fields} for d in decls if d["private_repo"]], open(os.path.join(PRIV_OUT, "types.json"), "w"))

# ---------------------------------------------------------------- 2. reference graph
# A target refers to a declaration when one of its files contains the declaration's simple name as an identifier
# token and the target is the declaring target or depends on it (transitively). Overcounts, never undercounts.
ident_index = collections.defaultdict(set)   # ident -> set of file indices
for i, f in enumerate(files):
    for s in f["idents"]:
        ident_index[s].add(i)

def bare(n): return n.strip("`")

refs = []
public_decls = [d for d in decls if d["access"] in ("public", "open") and not d["test"] and d["module"]]
for d in public_decls:
    home = (d["repo"], d["module"])
    nontest_pk, test_pk, nontest_t, test_t, nontest_files_other = set(), set(), set(), set(), 0
    for i in ident_index.get(bare(d["name"]), ()):
        f = files[i]
        tk = f["target"]
        if tk is None: continue
        if tk != home and home not in closure(tk): continue
        same_file = f["repo"] == d["repo"] and f["inner"] == d["file"]
        if f["test"]:
            test_pk.add(f["repo"]); test_t.add(tk)
        else:
            if not same_file:
                nontest_files_other += 1
                nontest_pk.add(f["repo"]); nontest_t.add(tk)
    refs.append({"repo": d["repo"], "module": d["module"], "qualified": d["qualified"], "kind": d["kind"], "file": d["file"], "line": d["line"],
                 "nontest_packages": len(nontest_pk), "nontest_other_packages": len(nontest_pk - {d["repo"]}),
                 "nontest_targets": len(nontest_t), "nontest_files_other": nontest_files_other,
                 "test_packages": len(test_pk), "test_targets": len(test_t), "private_repo": d["private_repo"],
                 "tier": d["tier"]})
dump([r for r in refs if not r["private_repo"]], "references.json")

# ---------------------------------------------------------------- 3. wrappers
FORWARDING = {"description", "debugDescription", "hash", "hashValue", "==", "<", "rawValue", "underlying", "id", "init",
              "encode", "playgroundDescription", "customMirror"}
SPECIAL_ATTRS = ("@propertyWrapper", "@dynamicMemberLookup", "@resultBuilder", "@dynamicCallable", "@main", "@objc")
CODABLE = {"Codable", "Swift.Codable", "Encodable", "Decodable", "Swift.Encodable", "Swift.Decodable"}

ext_index = collections.defaultdict(list)  # (repo, simple name) -> extensions
for r, es in exts_by_repo.items():
    for e in es:
        nm = e["extended"].split("<")[0]
        ext_index[(r, nm)].append(e)
        ext_index[(r, nm.split(".")[-1])].append(e)


ERROR_CONFORMANCES = {"Error", "Swift.Error", "Swift::Error"}
GENERIC_NAMES = {"Error", "Parse", "Options", "Output", "Input", "Iterator", "Index", "Storage", "State", "Configuration",
                 "Context", "Result", "Value", "Element", "Builder", "Coder", "Kind", "Mode", "Box", "Handle", "Token",
                 "Wrapper", "Base", "Inner", "View", "Body", "Content", "Item", "Entry", "Format", "Type", "Size", "Count"}
excluded = collections.Counter()


def is_wrapper(d):
    if d["test"]: return None
    if bare(d["name"]) == "Tagged" and d["repo"].endswith("/swift-tagged"): excluded["Tagged itself"] += 1; return None
    if any(a.startswith("@main") for a in d.get("attributes", [])): excluded["@main entry point"] += 1; return None
    if d["kind"] == "enum" and set(d["inherits"]) & ERROR_CONFORMANCES: excluded["single-case Error enum"] += 1 if len(d.get("cases", [])) == 1 and d["cases"][0]["payload"] == 1 else 0; return None
    if d["kind"] in ("struct", "class") and len(d.get("stored", [])) == 1 and d.get("nested", 0) >= 0:
        return d["stored"][0]["type"]
    if d["kind"] == "enum":
        cs = d.get("cases", [])
        if len(cs) == 1 and cs[0]["payload"] == 1:
            return cs[0]["payloadTypes"][0]
    return None


wrappers = []
for d in decls:
    raw = is_wrapper(d)
    if raw is None: continue
    es = ext_index.get((d["repo"], d["qualified"]), []) or ext_index.get((d["repo"], d["name"]), [])
    seen = set(); es = [e for e in es if not (id(e) in seen or seen.add(id(e)))]
    conformances = set(d["inherits"]) | set(x for e in es for x in e["inherits"])
    member_names = list(d.get("memberNames", [])) + [n for e in es if not e["test"] for n in e.get("memberNames", [])]
    field = d["stored"][0]["name"] if d.get("stored") else None
    behaviour = [n for n in member_names if n not in FORWARDING and n != field]
    custom_coding = d.get("customDecode") or d.get("customEncode") or any(e.get("customDecode") or e.get("customEncode") for e in es)
    validates = d.get("validatingInit") or any(e.get("validatingInit") for e in es if not e["test"])
    codable = bool(conformances & CODABLE) or any(c.endswith("Codable") for c in conformances)
    limit = None
    single_value = bool(conformances & {"RawRepresentable", "Swift.RawRepresentable", "Swift::RawRepresentable", "OptionSet", "Swift.OptionSet", "Swift::OptionSet"})
    if single_value and not codable: pass
    if conformances & {"OptionSet", "Swift.OptionSet", "Swift::OptionSet"}: behaviour = behaviour or ["OptionSet"]
    if d["kind"] == "class": limit = "reference semantics (class identity or inheritance)"
    elif any(a.startswith(SPECIAL_ATTRS) for a in d.get("attributes", [])): limit = "attribute that must be on the primary declaration: " + ",".join(a for a in d["attributes"] if a.startswith(SPECIAL_ATTRS))
    elif d.get("stored") and d["stored"][0].get("binding") == "var" and ("weak" in raw or "unowned" in raw): limit = "weak or unowned storage"
    elif d["kind"] == "enum" and d.get("cases") and d["cases"][0].get("payload") == 1 and "indirect" in " ".join(d.get("attributes", [])): limit = "indirect enum"
    if limit: cat = "language limit"
    elif codable and not custom_coding and not single_value: cat = "encoding"
    elif validates: cat = "validates"
    elif behaviour: cat = "own behaviour"
    else: cat = "plain"
    wrappers.append({"repo": d["repo"], "tier": d["tier"], "module": d["module"], "qualified": d["qualified"], "name": d["name"], "kind": d["kind"],
                     "access": d["access"], "raw": raw, "generic": d["generic"], "nestedIn": d["nestedIn"], "file": d["file"],
                     "line": d["line"], "endLine": d["endLine"], "category": cat, "field": d["stored"][0]["name"] if d.get("stored") else d["cases"][0]["name"], "limit": limit, "codable": codable,
                     "custom_coding": bool(custom_coding), "validates": bool(validates), "behaviour_members": len(behaviour),
                     "behaviour_sample": behaviour[:6], "conformances": sorted(conformances), "private_repo": d["private_repo"]})

# duplicates: same simple name and same raw type in two or more repositories
by_key = collections.defaultdict(list)
for w in wrappers:
    by_key[(bare(w["name"]), re.sub(r"\s", "", w["raw"]))].append(w)
ref_by = {(r["repo"], r["qualified"]): r for r in refs}
for k, ws in by_key.items():
    if len(set(w["repo"] for w in ws)) < 2 or k[0] in GENERIC_NAMES: continue
    ranked = sorted(ws, key=lambda w: (TIER_RANK[w["tier"]], -(ref_by.get((w["repo"], w["qualified"]), {}).get("nontest_packages", 0))))
    survivor = ranked[0]
    for w in ws:
        w["duplicate_of"] = None if w is survivor else (survivor["repo"] if not survivor["private_repo"] else "(private)") + ":" + survivor["qualified"]
        if w is not survivor and w["category"] in ("plain", "own behaviour"):
            w["category"] = "duplicate"

# tags: a wrapper nested in a type can use that type as its tag unless a sibling with the same raw type does too
nest_raw = collections.Counter((w["repo"], w["nestedIn"], re.sub(r"\s", "", w["raw"])) for w in wrappers if w["nestedIn"])
for w in wrappers:
    if w["nestedIn"] and nest_raw[(w["repo"], w["nestedIn"], re.sub(r"\s", "", w["raw"]))] == 1:
        w["tag"] = "reuse enclosing " + w["nestedIn"]
    else:
        w["tag"] = "new tag declaration"

# wrappers whose declaration line was added by a commit naming coenttb/work#239 (measure.sh greps the history)
added239 = set()
p239 = os.path.join(WORK, "239src.txt")
if os.path.exists(p239):
    for line in open(p239):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            added239.add((parts[0], parts[1], parts[-1].split(" ", 1)[1].strip().split(" ")[0].strip("`")))
NEWTYPE_FIELDS = {"rawValue", "value", "underlying", "storage", "base", "wrapped", "raw", "bits", "_value", "_storage", "_rawValue", "id", "identifier"}
NEWTYPE_SUFFIX = ("ID", "Identifier", "Name", "Number", "Index", "Code", "Count", "Offset", "Address", "Port", "Version", "Token", "Key", "Tag")
for w in wrappers:
    w["added_by_239"] = (w["repo"], w["file"], bare(w["name"])) in added239

for w in wrappers:
    w["record_like"] = w["kind"] != "enum" and w["field"].strip("`") not in NEWTYPE_FIELDS and not bare(w["name"]).endswith(NEWTYPE_SUFFIX)
dump([w for w in wrappers if not w["private_repo"]], "wrappers.json")
json.dump([w for w in wrappers if w["private_repo"]], open(os.path.join(PRIV_OUT, "wrappers.json"), "w"), indent=1)

wsum = {"excluded_from_wrappers": excluded, "total": len(wrappers), "by_category": collections.Counter(w["category"] for w in wrappers),
        "by_kind": collections.Counter(w["kind"] for w in wrappers),
        "by_tier": {t: collections.Counter(w["category"] for w in wrappers if w["tier"] == t) for t in TIERS},
        "public": sum(1 for w in wrappers if w["access"] in ("public", "open")),
        "tag_reuse": collections.Counter(w["tag"].split(" ")[0] for w in wrappers),
        "convertible_plain_and_duplicate": sum(1 for w in wrappers if w["category"] in ("plain", "duplicate"))}
plain = [w for w in wrappers if w["category"] == "plain"]
wsum["plain_newtype_vs_record_like"] = collections.Counter("record-like" if w["record_like"] else "newtype" for w in plain)
wsum["added_by_239"] = collections.Counter(w["category"] for w in wrappers if w["added_by_239"])
wsum["record_like_by_category"] = collections.Counter(w["category"] for w in wrappers if w["record_like"])
wsum["plain_tag"] = collections.Counter(w["tag"].split(" ")[0] for w in plain)
wsum["raw_types_top"] = collections.Counter(re.sub(r"\s", "", w["raw"]) for w in wrappers).most_common(25)
wsum["limits"] = collections.Counter(w["limit"] for w in wrappers if w["limit"])
dump(wsum, "wrappers-summary.json")

# ---------------------------------------------------------------- 4. molecules
repo_deps = {r: set(m["_pkgdeps"]) if m else set() for r, m in manifests.items()}
dependents = collections.defaultdict(set)
for r, ds in repo_deps.items():
    for x in ds: dependents[x].add(r)


def repo_closure(r):
    seen, st = set(), [r]
    while st:
        x = st.pop()
        for y in repo_deps.get(x, ()):
            if y not in seen: seen.add(y); st.append(y)
    return seen


repo_lines = collections.Counter(); repo_src_lines = collections.Counter(); repo_decls = collections.Counter()
platform_cond = collections.Counter(); foundation_imports = collections.Counter()
for f in files:
    repo_lines[f["repo"]] += f["lines"]
    if not f["test"]:
        repo_src_lines[f["repo"]] += f["lines"]
        repo_decls[f["repo"]] += len(f["decls"])
        if {"Windows", "WinSDK", "Darwin", "Glibc", "Musl"} & f["idents"]: platform_cond[f["repo"]] += 1
        if any(i["module"].split(".")[0] in ("Foundation", "FoundationEssentials") for i in f["imports"]): foundation_imports[f["repo"]] += 1

molecules = []
for r in REPOS:
    if tier_of(r) != "molecules": continue
    m = manifests[r] or {}
    atom_deps = sorted(x for x in repo_deps[r] if tier_of(x) == "atoms")
    mol_deps = sorted(x for x in repo_deps[r] if tier_of(x) == "molecules")
    deps_by = sorted(dependents[r])
    traits = [t["name"] for t in m.get("traits", []) if t["name"] != "default"]
    # fold host: the atom dependency with the most of this molecule's dependents already depending on it
    host = None
    if atom_deps:
        host = max(atom_deps, key=lambda a: (sum(1 for x in deps_by if a in repo_closure(x)), -repo_src_lines[a]))
    molecules.append({"repo": r, "source_lines": repo_src_lines[r], "declarations": repo_decls[r], "atom_deps": atom_deps,
                      "molecule_deps": mol_deps, "other_deps": sorted(x for x in repo_deps[r] if tier_of(x) not in ("atoms", "molecules")),
                      "dependents": len(deps_by), "dependents_by_tier": collections.Counter(tier_of(x) for x in deps_by),
                      "traits": traits, "platform_files": platform_cond[r], "foundation_files": foundation_imports[r],
                      "fold_host": host,
                      "host_dependents_already_reach_host": sum(1 for x in deps_by if host and host in repo_closure(x)) if host else 0})
dump(molecules, "molecules.json")

# ---------------------------------------------------------------- 5. low value
lowvalue = {}
lowvalue["public_no_nontest_consumer"] = [r for r in refs if r["nontest_files_other"] == 0 and r["kind"] != "typealias"]
lowvalue["public_used_once"] = [r for r in refs if r["nontest_files_other"] == 1 and r["kind"] != "typealias"]
lowvalue["no_dependents"] = sorted(r for r in REPOS if not dependents[r])
used_products = set()
for (r, n), t in targets.items():
    for d in t["deps"]:
        if d[0] in ("product", "byName"):
            pkg = identity_to_repo.get((d[2] or "").lower())
            if pkg: used_products.add((pkg, d[1]))
            else:
                for x in repo_deps.get(r, ()):
                    if (x, d[1]) in products: used_products.add((x, d[1]))
lowvalue["products_unused"] = sorted(f"{r}:{p}" for (r, p) in products if (r, p) not in used_products and tier_of(r) != "coenttb")
lowvalue["bounded"] = [r for r in refs if bare(r["qualified"].split(".")[-1]) == "Bounded"] + \
    [{"repo": d["repo"], "qualified": d["qualified"], "access": d["access"], "file": d["file"], "line": d["line"], "private_repo": d["private_repo"]}
     for d in decls if bare(d["name"]) == "Bounded" and d["access"] not in ("public", "open")]
lv_pub = {k: [x for x in v if not (isinstance(x, dict) and x.get("private_repo")) and not (isinstance(x, str) and x.split(":")[0] in PRIVATE)]
          for k, v in lowvalue.items()}
lv_pub["no_dependents"] = [r for r in lowvalue["no_dependents"] if r not in PRIVATE]
lv_pub["counts_including_private"] = {k: len(v) for k, v in lowvalue.items()}
dump(lv_pub, "low-value.json")

# ---------------------------------------------------------------- 6. Core names
core = []
for (r, n), t in targets.items():
    if re.search(r"\bCore\b", n):
        core.append({"repo": r, "target": n, "type": t["type"], "private_repo": r in PRIVATE,
                     "group": "X Macro Core" if n.endswith("Macro Core") or n.endswith("Macros Core") else
                              "X Core" if n.endswith(" Core") else "Core inside name",
                     "dependents_in_repo": sum(1 for k2, t2 in targets.items() if k2[0] == r and (r, n) in t2["resolved"]),
                     "dependents_outside": sum(1 for k2, t2 in targets.items() if k2[0] != r and (r, n) in t2["resolved"]),
                     "in_products": [p for (pr, p), ts in products.items() if pr == r and n in ts]})
false_core = [r for r in REPOS if "core" in r.lower() and not any(c["repo"] == r for c in core)]
dump({"targets": [c for c in core if not c["private_repo"]], "packages": len(set(c["repo"] for c in core)),
      "targets_total": len(core), "groups": collections.Counter(c["group"] for c in core),
      "macro_core_distinct": len(set(c["target"] for c in core if c["group"] == "X Macro Core")),
      "repo_name_contains_core_without_core_target": false_core}, "core-names.json")

# ---------------------------------------------------------------- 7. the open hunt
hunt = {}
# tier inversions at package level
inv = []
for r, ds in repo_deps.items():
    for x in ds:
        if TIER_RANK[tier_of(x)] > TIER_RANK[tier_of(r)]:
            inv.append({"from": r, "from_tier": tier_of(r), "to": x, "to_tier": tier_of(x)})
hunt["tier_inversions"] = inv
# package cycles (Tarjan)
idx, low, on, st, sccs, counter = {}, {}, set(), [], [], [0]
sys.setrecursionlimit(10000)


def strong(v):
    idx[v] = low[v] = counter[0]; counter[0] += 1; st.append(v); on.add(v)
    for w in repo_deps.get(v, ()):
        if w not in idx: strong(w); low[v] = min(low[v], low[w])
        elif w in on: low[v] = min(low[v], idx[w])
    if low[v] == idx[v]:
        comp = []
        while True:
            w = st.pop(); on.discard(w); comp.append(w)
            if w == v: break
        if len(comp) > 1: sccs.append(sorted(comp))


for v in REPOS:
    if v not in idx: strong(v)
hunt["package_cycles"] = sccs
# unused target dependencies: a dependency target none of whose modules the target's files import
unused_deps = []
target_imports = {}
for k, t in targets.items():
    target_imports[k] = set(i["module"].split(".")[0] for f in t["files"] for i in f["imports"])
for k, t in targets.items():
    if not t["files"] or t["type"] in ("plugin", "binary", "system"): continue
    for d in t["deps"]:
        res = resolve_dep(k[0], d)
        mods = set(x[1].replace(" ", "_") for x in res)
        if res and not (mods & target_imports[k]):
            unused_deps.append({"repo": k[0], "target": k[1], "dependency": d[1], "test": t["test"]})
hunt["unused_target_dependencies"] = {"count": len(unused_deps), "nontest": sum(1 for u in unused_deps if not u["test"]),
                                      "items": [u for u in unused_deps if u["repo"] not in PRIVATE]}
# unused package dependencies
unused_pkg = []
for r, m in manifests.items():
    if not m: continue
    used = set()
    for k, t in targets.items():
        if k[0] != r: continue
        for x in t["resolved"]: used.add(x[0])
    for x in m["_pkgdeps"]:
        if x not in used: unused_pkg.append({"repo": r, "dependency": x})
hunt["unused_package_dependencies"] = [u for u in unused_pkg if u["repo"] not in PRIVATE]
hunt["unused_package_dependencies_count"] = len(unused_pkg)
# traits declared but never referenced in source (#if) or manifest conditions
unused_traits = []
for r, m in manifests.items():
    if not m: continue
    text = open(os.path.join(ROOT, "repos", r, "Package.swift")).read() if os.path.exists(os.path.join(ROOT, "repos", r, "Package.swift")) else ""
    for tr in m.get("traits", []):
        n = tr["name"]
        if n == "default": continue
        used = any(n in f["idents"] for f in files if f["repo"] == r) or text.count('"' + n + '"') > 1
        if not used: unused_traits.append({"repo": r, "trait": n})
hunt["unused_traits"] = [u for u in unused_traits if u["repo"] not in PRIVATE]
# library targets in no product and depended on by nothing
orphan = []
for k, t in targets.items():
    if t["type"] != "regular": continue
    in_prod = any(k[0] == pr and k[1] in ts for (pr, _), ts in products.items())
    used = any(k in t2["resolved"] for t2 in targets.values())
    if not in_prod and not used: orphan.append({"repo": k[0], "target": k[1]})
hunt["orphan_targets"] = [o for o in orphan if o["repo"] not in PRIVATE]
# exports.swift chains
exported = collections.defaultdict(set)
for k, t in targets.items():
    for f in t["files"]:
        for i in f["imports"]:
            if i["exported"]: exported[k].add(i["module"].split(".")[0])
chain_len = {}


depth_memo = {}


def exp_depth(k, stack=frozenset()):
    """Longest chain of @_exported imports starting at target k (cycles cut)."""
    if k in depth_memo: return depth_memo[k]
    best = 0
    for mod in exported.get(k, ()):
        nk = module_to.get(mod)
        if nk and nk not in stack and nk != k:
            best = max(best, 1 + exp_depth(nk, stack | {k}))
    depth_memo[k] = best
    return best


depths = {k: exp_depth(k) for k in exported}
reexported_total = {k: len(exported[k]) for k in exported}
hunt["exported_imports"] = {"targets_with_exports": len(exported), "exported_import_lines": sum(reexported_total.values()),
                            "max_chain_depth": max(depths.values() or [0]),
                            "chains_depth_ge_3": sorted(f"{k[0]}:{k[1]} ({v})" for k, v in depths.items() if v >= 3 and k[0] not in PRIVATE),
                            "depth_histogram": collections.Counter(depths.values())}
# exported but not a declared dependency of the target (hides a real dependency is the inverse: used but only via export)
hidden = 0; hidden_items = []
for k, t in targets.items():
    direct_mods = set(x[1].replace(" ", "_") for x in t["resolved"])
    for mod in target_imports[k]:
        nk = module_to.get(mod)
        if not nk or nk[0] == k[0] or mod in direct_mods: continue
        if nk in closure(k):
            hidden += 1
            if k[0] not in PRIVATE and len(hidden_items) < 400: hidden_items.append(f"{k[0]}:{k[1]} imports {mod} without depending on it")
hunt["imports_reached_only_transitively"] = {"count": hidden, "items": hidden_items}
# empty or single-declaration targets
small = []
for k, t in targets.items():
    if t["test"] or t["type"] != "regular": continue
    n = sum(len(f["decls"]) + len(f["extensions"]) for f in t["files"])
    if n <= 1: small.append({"repo": k[0], "target": k[1], "declarations_and_extensions": n, "files": len(t["files"])})
hunt["empty_or_single_declaration_targets"] = {"count": len(small), "items": [s for s in small if s["repo"] not in PRIVATE]}
test_only = [r for r in REPOS if repo_src_lines[r] == 0]
hunt["packages_without_sources"] = [r for r in test_only if r not in PRIVATE]
# parallel names for one concept: same public simple name declared at top level in 3+ repositories
pubtop = collections.defaultdict(set)
for d in decls:
    if not d["test"] and d["access"] in ("public", "open") and d["kind"] != "typealias":
        pubtop[bare(d["name"])].add(d["repo"])
hunt["same_public_name_in_many_packages"] = sorted(((n, len(rs)) for n, rs in pubtop.items() if len(rs) >= 8), key=lambda x: -x[1])
# legacy names
legacy = collections.defaultdict(list)
for (r, n), t in targets.items():
    for word in ("Primitives", "Standard", "Foundation Integration", "Shared", "Utilities", "Helpers", "Kit"):
        if word in n.split(" ") or n.endswith(word):
            legacy[word].append(f"{r}:{n}" if r not in PRIVATE else "(private)")
hunt["legacy_target_words"] = {w: {"count": len(v), "items": v} for w, v in legacy.items()}
# Foundation where the tier shouldn't have it
fnd = collections.Counter(); fnd_items = []
for f in files:
    if f["test"]: continue
    t = tier_of(f["repo"])
    for i in f["imports"]:
        if i["module"].split(".")[0] in ("Foundation", "FoundationEssentials", "FoundationNetworking"):
            fnd[t] += 1
            if t in ("atoms", "molecules", "standards") and f["repo"] not in PRIVATE:
                fnd_items.append(f"{f['repo']}/{f['inner']}:{i['line']} {i['module']}")
hunt["foundation_imports_nontest_by_tier"] = fnd
hunt["foundation_imports_low_tiers"] = fnd_items
hunt["if_false_blocks"] = [f"{f['repo']}/{f['inner']}" for f in files if f["ifFalse"] and f["repo"] not in PRIVATE]
hunt["available_deprecated_or_unavailable"] = {"count": sum(f["availableDeprecated"] for f in files),
                                               "by_tier": collections.Counter({t: sum(f["availableDeprecated"] for f in files if tier_of(f["repo"]) == t) for t in TIERS})}
# top 20 largest packages
largest = sorted(REPOS, key=lambda r: -repo_src_lines[r])[:20]
hunt["largest_20"] = [{"repo": r if r not in PRIVATE else "(private)", "tier": tier_of(r), "source_lines": repo_src_lines[r],
                       "declarations": repo_decls[r], "targets": sum(1 for k in targets if k[0] == r and not targets[k]["test"]),
                       "dependencies": len(repo_deps[r]), "dependents": len(dependents[r]),
                       "wrappers": sum(1 for w in wrappers if w["repo"] == r),
                       "core_targets": sum(1 for c in core if c["repo"] == r)} for r in largest]
dump(hunt, "hunt.json")

# for later steps
json.dump({"repo_deps": {r: sorted(v) for r, v in repo_deps.items()}, "src_lines": repo_src_lines}, open(os.path.join(WORK, "graph.json"), "w"))
print(json.dumps({"baseline": baseline["all"], "wrappers": wsum["by_category"], "core": len(core)}, default=str))
