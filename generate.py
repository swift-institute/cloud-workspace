#!/usr/bin/env python3
"""Writes Package.swift: every checkout in repos/ as a path dependency, so a change in one is seen by all above it.
A path dependency at the root overrides the same package's URL everywhere in the graph, so no repository's own manifest changes."""
import concurrent.futures, glob, json, os, re, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
packages = sorted(p for p in glob.glob("repos/*/*") if os.path.exists(p + "/Package.swift"))
# Traits a package's own manifest asks of another, unconditionally. The root's path dependency must ask for them too:
# otherwise resolution follows the root's (default traits only), leaves out what the trait needs, and fails, as it did
# for footprint's swift-sqlite with GRDB ("exhausted attempts to resolve ... 'grdb.swift'").
requested = {}


APPLE = re.compile(r"^(?:public |package |@preconcurrency )*import (?:AppKit|UIKit|SwiftUI|ScreenCaptureKit|AVFoundation|CoreGraphics|CoreImage|Metal)\b", re.M)


def apple_only(dirs):
    """A product whose targets import an Apple-only framework outside any #if: built on Apple platforms only."""
    for d in dirs:
        for f in glob.glob(os.path.join(d, "**/*.swift"), recursive=True):
            t = open(f, errors="replace").read()
            if "#if" not in t and APPLE.search(t):
                return True
    return False


def dump(path):
    r = subprocess.run(["swift", "package", "dump-package", "--package-path", path], capture_output=True, text=True)
    if r.returncode:
        print("UNREADABLE", path, r.stderr[-300:], file=sys.stderr)
        return path, None, [], None
    m = json.loads(r.stdout)
    paths = {t["name"]: os.path.join(path, t.get("path") or f"Sources/{t['name']}") for t in m["targets"]}
    libs = [(p["name"], apple_only(paths.get(t, "") for t in p["targets"])) for p in m["products"] if "library" in p["type"]]
    for d in m["dependencies"]:
        for v in next(iter(d.values())):
            for t in v.get("traits") or []:
                if t["name"] != "default" and not t.get("condition"):
                    requested.setdefault(v["identity"].lower(), set()).add(t["name"])
    return path, m["name"], libs, m


with concurrent.futures.ThreadPoolExecutor(os.cpu_count() or 4) as pool:
    dumped = list(pool.map(dump, packages))



def dependency(p):
    traits = sorted(requested.get(os.path.basename(p).lower(), ()))
    if not traits:
        return f'        .package(path: "{p}"),\n'
    return f'        .package(path: "{p}", traits: [.defaults, {", ".join(chr(34) + t + chr(34) for t in traits)}]),\n'


deps = "".join(dependency(p) for p, _, _, _ in dumped)
products = "".join(
    f'                .product(name: "{l}", package: "{os.path.basename(p)}"'
    + (", condition: .when(platforms: [.macOS, .iOS, .tvOS, .watchOS, .visionOS])" if apple else "") + "),\n"
    for p, n, libs, _ in dumped for l, apple in libs
)

# Test targets: every repository's tests, declared in the root, so one `swift build --build-tests` plans them all.
# A dependency on a target of the same package goes through a library product holding it; a non-product target is
# declared in the root as well. Clashing names are renamed here only (tests-renamed.json); targets the root can't take
# are listed in tests-skipped.json, to be type-checked instead.
def q(x):
    return json.dumps(x)


def setting(st):
    (k, v), = st["kind"].items()
    cond = st.get("condition") or {}
    if cond.get("platformNames") or cond.get("config") or cond.get("traits"):
        return None
    a = v.get("_0") if isinstance(v, dict) else None
    if k == "define": return f".define({q(a)})"
    if k == "enableUpcomingFeature": return f".enableUpcomingFeature({q(a)})"
    if k == "enableExperimentalFeature": return f".enableExperimentalFeature({q(a)})"
    if k == "strictMemorySafety": return ".strictMemorySafety()"
    if k == "unsafeFlags": return f".unsafeFlags({q(a)})"
    if k == "swiftLanguageMode": return f".swiftLanguageMode(.v{str(a.get('_0', a) if isinstance(a, dict) else a).split('.')[0]})" if a else None
    if k == "interoperabilityMode": return f".interoperabilityMode(.{a})"
    return None


FALLBACK = set(l.strip() for l in open("overnight/tests-fallback.txt") if l.strip() and not l.startswith("#")) if os.path.exists("overnight/tests-fallback.txt") else set()
_pkg_decls = {}


def uses_package_access(path, tdir):
    if path not in _pkg_decls:
        names = set()
        for f in glob.glob(os.path.join(path, "Sources/**/*.swift"), recursive=True):
            for m in re.finditer(r"\bpackage\s+(?:(?:static|final|override|mutating|nonisolated|convenience|required|lazy)\s+)*(?:func|var|let|init|struct|enum|class|actor|typealias|protocol|subscript)\s*(`[^`]+`|\w+)?", open(f, errors="replace").read()):
                names.add(m[1] or "init")
        names.discard("init")
        _pkg_decls[path] = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\b") if names else None
    pat = _pkg_decls[path]
    if not pat: return False
    return any(pat.search(open(f, errors="replace").read()) for f in glob.glob(os.path.join(tdir, "**/*.swift"), recursive=True))


taken = {t["name"] for _, _, _, m in dumped if m for t in m["targets"]}
test_targets, extra_targets, renamed, skipped, test_names = [], [], {}, [], []
own_copies = {}
for path, name, libs, m in dumped:
    if not m: continue
    pkg = os.path.basename(path)
    by_name = {t["name"]: t for t in m["targets"]}
    product_of = {}
    for pr in m["products"]:
        if "library" in pr["type"]:
            for t in pr["targets"]:
                product_of.setdefault(t, pr["name"])
    lib_names = {l for l, _ in libs}
    for t in m["targets"]:
        if t["type"] != "test": continue
        tdir = os.path.join(path, t.get("path") or f"Tests/{t['name']}")
        if (path + "|" + t["name"]) in FALLBACK:
            skipped.append((path, t["name"], "listed in overnight/tests-fallback.txt")); continue
        if uses_package_access(path, tdir):
            skipped.append((path, t["name"], "uses package-access declarations (the root can't give it its package's -package-name)")); continue
        if apple_only([tdir]):
            skipped.append((path, t["name"], "imports an Apple-only framework")); continue
        deps, why = [], None
        for d in t["dependencies"]:
            (k, v), = d.items()
            cond = v[-1] if isinstance(v[-1], dict) else None
            if cond and (cond.get("platformNames") or cond.get("traits")):
                if cond.get("traits") or not set(cond["platformNames"]) & {"linux"}:
                    continue
            if k in ("target", "byName"):
                tn = v[0]
                if tn in product_of and product_of[tn] in lib_names:
                    deps.append(f".product(name: {q(product_of[tn])}, package: {q(pkg)})")
                elif tn in by_name and by_name[tn]["type"] == "regular":
                    # Redeclaring it in the root clashes with the original: target names are unique across the graph.
                    why = f"depends on non-product target {tn}"; break
                elif tn in product_of:
                    why = f"dependency {tn} is only in an Apple-only product"; break
                else:
                    why = f"dependency {tn} is neither a product nor a regular target"; break
            elif k == "product":
                deps.append(f".product(name: {q(v[0])}, package: {q(v[1] or v[0])})")
        if why:
            skipped.append((path, t["name"], why)); continue
        n = t["name"]
        if n in test_names or sum(1 for _, _, _, mm in dumped if mm for x in mm["targets"] if x["name"] == n) > 1:
            n2 = f"{n} ({pkg})"; renamed[n2] = [path, n]; n = n2
        test_names.append(n)
        sets = [x for x in (setting(st) for st in t.get("settings", []) if st["tool"] == "swift") if x]
        sets.append(f".unsafeFlags([\"-package-name\", {q(pkg.replace('-', '_'))}])")
        res = [f".{r['rule'] if r['rule'] in ('copy', 'process') else 'process'}({q(r['path'])})" for r in t.get("resources", [])]
        test_targets.append(
            f"        .testTarget(name: {q(n)}, dependencies: [{', '.join(deps)}], path: {q(tdir)}"
            + (f", exclude: {q(t['exclude'])}" if t.get("exclude") else "")
            + (f", resources: [{', '.join(res)}]" if res else "")
            + f", swiftSettings: [{', '.join(sets)}]),\n")
for (path, tn), t in own_copies.items():
    pkg = os.path.basename(path)
    product_of = {}
    for pr in next(mm for pp, _, _, mm in dumped if pp == path)["products"]:
        for x in pr["targets"]: product_of.setdefault(x, pr["name"])
    deps = []
    for d in t["dependencies"]:
        (k, v), = d.items()
        if k in ("target", "byName") and v[0] in product_of:
            deps.append(f".product(name: {q(product_of[v[0]])}, package: {q(pkg)})")
        elif k == "product":
            deps.append(f".product(name: {q(v[0])}, package: {q(v[1] or v[0])})")
    sets = [x for x in (setting(st) for st in t.get("settings", []) if st["tool"] == "swift") if x]
    sets.append(f".unsafeFlags([\"-package-name\", {q(pkg.replace('-', '_'))}])")
    extra_targets.append(f"        .target(name: {q(tn)}, dependencies: [{', '.join(deps)}], path: {q(os.path.join(path, t.get('path') or 'Sources/' + tn))}, swiftSettings: [{', '.join(sets)}]),\n")
json.dump(renamed, open("tests-renamed.json", "w"), indent=1)
json.dump(skipped, open("tests-skipped.json", "w"), indent=1)
tests_decl = "".join(extra_targets) + "".join(test_targets)

def appends(var, items):
    return "".join(f"{var}.append({x.strip().rstrip(',')})\n" for x in items if x.strip())


local = {os.path.basename(p).lower() for p, _, _, _ in dumped}
remote = {}
for _, _, _, m in dumped:
    for d in (m or {}).get("dependencies", []):
        for v in d.get("sourceControl", []):
            if v["identity"].lower() in local or v["identity"] in remote: continue
            url = v["location"]["remote"][0]["urlString"]; r = v["requirement"]
            if "range" in r: req = f'"{r["range"][0]["lowerBound"]}"..<"{r["range"][0]["upperBound"]}"'
            elif "exact" in r: req = f'exact: "{r["exact"][0]}"'
            elif "branch" in r: req = f'branch: "{r["branch"][0]}"'
            elif "revision" in r: req = f'revision: "{r["revision"][0]}"'
            else: continue
            remote[v["identity"]] = f'.package(url: "{url}", {req})'
dep_lines = [dependency(p) for p, _, _, _ in dumped] + list(remote.values())
product_lines = products.split("\n")
test_lines = (tests_decl).split("\n")
open("Package.swift", "w").write(
    "// swift-tools-version: 6.4\n// Generated by generate.py. Not committed.\nimport PackageDescription\n\n"
    "var dependencies: [Package.Dependency] = []\n" + appends("dependencies", dep_lines)
    + "var everything: [Target.Dependency] = []\n" + appends("everything", product_lines)
    + "var targets: [Target] = [.target(name: \"Everything\", dependencies: everything)]\n" + appends("targets", test_lines)
    + """
let package = Package(
    name: "cloud-workspace",
    platforms: [.macOS(.v27), .iOS(.v27), .tvOS(.v27), .watchOS(.v27), .visionOS(.v27)],
    dependencies: dependencies,
    targets: targets
)
"""
)
os.makedirs("Sources/Everything", exist_ok=True)
open("Sources/Everything/Everything.swift", "w").write("// Holds the graph together. Never built on its own.\n")
print(f"{len(test_targets)} test targets, {len(extra_targets)} non-product targets, {len(renamed)} renamed, {len(skipped)} skipped")
print(f"{len(dumped)} packages, {sum(len(l) for _, _, l, _ in dumped)} library products, {sum(a for _, _, l, _ in dumped for _, a in l)} Apple-only")
