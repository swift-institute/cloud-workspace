#!/usr/bin/env python3
"""UNTESTED: written for the 8 Nov pilot, which was cancelled before it ran. Test on one package first.
Applies fix scripts to the given packages, one round per script, and keeps only changes that pass every gate.

Per round: lint the packages (runner, parallel) -> run the script -> group the changed files into transactions (files
that exchanged declaration lines: a merge, split or move is one transaction) -> per transaction, revert it whole unless
  1. its normalized declaration multiset is unchanged (nothing lost, nothing duplicated),
  2. no rule's finding count in its files rose, and the round's rule fell,
  3. every changed target, Sources and Tests, compiles to SIL against the root build's modules (swiftc -emit-sil -wmo, so
     the ownership checks run, which -typecheck skips; traits on, warnings as errors; no result in 180 s holds the target; an error in a file outside every transaction is pre-existing and ignored),
-> commit per package. Never builds per package and never loops a build. Times every step.

    overnight/gated-batch.py <work-dir> <round[,round...]> <package> ...
    rounds: minimal, suites, split, selectors, exports, merge, loops, ifexpr

Writes <work-dir>/log.jsonl (one line per round and package) and prints one line per step. Needs the runner
(/home/user/tools/runner-main), /home/user/dumps (swift package dump-package per package) and the root build at
/home/user/scratch-warn. Linux only."""
import collections, concurrent.futures as cf, glob, json, os, re, shutil, subprocess, sys, time

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
work, rounds, pkgs = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
os.makedirs(work, exist_ok=True)
P = "/home/user/scratch-warn/out/Products/Debug-linux-x86_64"
J = os.cpu_count() or 4
ROUNDS = {  # name: (rule, argv builder: lint dir -> argv)
    "minimal": ("minimal type body", lambda l: ["overnight/minimal-bodies2.py", l, *pkgs]),
    "suites": ("compound suite name", lambda l: ["overnight/compound-suites.py", l, *pkgs]),
    "split": ("single type per file", lambda l: ["overnight/split-types.py", l, *pkgs]),
    "selectors": ("module selector spelling", lambda l: ["overnight/module-selectors.py", l]),
    "exports": ("exported import", lambda l: ["overnight/exports-file.py", *pkgs]),
    "merge": ("extension file naming", lambda l: ["overnight/merge-extension-files.py", l, *pkgs]),
    "loops": ("counter loop iteration", lambda l: ["overnight/counter-loops.py", l]),
    "ifexpr": ("statement where expression fits", lambda l: ["overnight/if-expressions.py", l]),
}
MODS = r"(?:@[A-Za-z_]+(?:\([^)]*\))?\s+)*(?:(?:public|package|internal|fileprivate|private|open|static|final|mutating|nonmutating|override|nonisolated|consuming|borrowing|indirect|convenience|required|lazy|weak|unowned|dynamic|optional|prefix|postfix|infix)\s+)*"
DECL = re.compile(r"^\s*" + MODS + r"(func|init|deinit|subscript|var|let|case|struct|enum|class|actor|protocol|typealias)\b(.*)$")
TC_FLAGS = ["-swift-version", "6", "-parse-as-library", "-strict-memory-safety", "-I", P, "-Xcc", "-I" + P + "/include",
            "-enable-testing", "-warnings-as-errors", "-D", "DEBUG", "-D", "SWIFT_PACKAGE", "-enable-experimental-feature", "Lifetimes",
            "-plugin-path", "/opt/swift/usr/lib/swift/host/plugins",
            "-external-plugin-path", "/opt/swift/usr/lib/swift/host/plugins/testing#/opt/swift/usr/bin/swift-plugin-server"] + sum(
    (["-enable-upcoming-feature", f] for f in ["ExistentialAny", "InternalImportsByDefault", "MemberImportVisibility",
     "NonisolatedNonsendingByDefault", "InferIsolatedConformances"]), [])
log = open(os.path.join(work, "log.jsonl"), "a")


def sh(*a, cwd=root, check=False):
    r = subprocess.run(a, capture_output=True, text=True, cwd=cwd, errors="replace")
    if check and r.returncode: raise SystemExit(f"failed: {a}\n{r.stderr[-2000:]}")
    return r


def git(p, *a): return sh("git", "-C", os.path.join(root, "repos", p), *a)


def say(msg): print(time.strftime("%H:%M:%S"), msg, flush=True)


def lint(out, which):
    if os.path.isdir(out): shutil.rmtree(out)
    sh("env", f"OUT={out}", f"J={J}", "overnight/lint-par.sh", *which)
    res = {}
    for p in which:
        try: res[p] = json.load(open(os.path.join(out, p.replace("/", "__", 1) + ".json")))["findings"]
        except Exception: res[p] = None
    return res


def per_file(findings):
    c = collections.defaultdict(collections.Counter)
    for x in findings or []: c[x["fileID"][2:]][x["rule"]] += 1
    return c


def norm(line):
    m = DECL.match(line)
    if not m: return None
    s = (m.group(1) + m.group(2)).strip()
    s = re.sub(r"\s*\{.*$", "", s).replace("::", "."); s = re.sub(r"\s+", " ", s)
    return re.sub(r"\b(?:Swift|Self)\.", "", s)


def transactions(p):
    git(p, "add", "-A", "Sources", "Tests")
    st = [l.split("\t") for l in git(p, "diff", "--cached", "--name-status", "--no-renames").stdout.splitlines() if l]
    files = {f: s for s, f in st if f.startswith(("Sources/", "Tests/"))}
    rem, add = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for f in files:
        cur = None
        for line in git(p, "diff", "--cached", "-U0", "--no-renames", "--", f).stdout.split("\n"):
            if line.startswith(("---", "+++")): continue
            if line.startswith("-"):
                k = norm(line[1:]); rem[f][k] += 1 if k else 0
            elif line.startswith("+"):
                k = norm(line[1:]); add[f][k] += 1 if k else 0
    parent = {f: f for f in files}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    by_line = collections.defaultdict(set)
    for f in files:
        for k in list(rem[f]) + list(add[f]):
            if k: by_line[k].add(f)
    for k, fs in by_line.items():
        if any(rem[f][k] for f in fs) and any(add[f][k] for f in fs) and len(fs) > 1:
            fs = sorted(fs)
            for g in fs[1:]: parent[find(g)] = find(fs[0])
    groups = collections.defaultdict(list)
    for f in files: groups[find(f)].append(f)
    out = []
    for fs in groups.values():
        r, a = collections.Counter(), collections.Counter()
        for f in fs: r.update(rem[f]); a.update(add[f])
        r.pop(None, None); a.pop(None, None)
        out.append({"files": sorted(fs), "status": {f: files[f] for f in fs}, "lost": sum((r - a).values()), "dup": sum((a - r).values())})
    return out


def revert(p, txn):
    for f in txn["files"]:
        if txn["status"][f] == "A":
            git(p, "rm", "-q", "--cached", "--", f)
            try: os.remove(os.path.join(root, "repos", p, f))
            except OSError: pass
        else:
            git(p, "checkout", "HEAD", "--", f)


def targets_of(p, files):
    try: dump = json.load(open(os.path.join("/home/user/dumps", p.replace("/", "__", 1) + ".json")))
    except Exception: return []
    out = []
    for t in dump["targets"]:
        if t["type"] not in ("regular", "executable", "test"): continue
        tp = (t.get("path") or (("Tests/" if t["type"] == "test" else "Sources/") + t["name"])).rstrip("/")
        if any(f.startswith(tp + "/") for f in files): out.append((t["name"], tp, t["type"], dump))
    return out


def tc_args(p, name, tp, dump):
    d = os.path.join(root, "repos", p)
    nested = [(t.get("path") or "").rstrip("/") for t in dump["targets"] if t.get("path") and t["path"].rstrip("/") != tp and t["path"].startswith(tp + "/")]
    files = [f for f in glob.glob(os.path.join(d, tp, "**/*.swift"), recursive=True) if not any(f.startswith(os.path.join(d, x) + "/") for x in nested)]
    traits = sum((["-D", t["name"]] for t in dump.get("traits") or [] if t["name"] != "default"), [])
    mod = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return ["swiftc", "-emit-sil", "-wmo", "-o", "/dev/null", *traits, "-module-name", mod, "-package-name", os.path.basename(p).replace("-", "_"), *TC_FLAGS, *files]


def typecheck(jobs):
    """jobs: [(p, name, tp, dump)] -> {(p, name): [error file paths relative to the package]}"""
    def one(j):
        p, name, tp, dump = j
        try:
            r = subprocess.run(tc_args(p, name, tp, dump), capture_output=True, text=True, errors="replace", timeout=180)
        except subprocess.TimeoutExpired:
            return (p, name), ([], True, "timeout after 180 s")
        base = os.path.join(root, "repos", p) + "/"
        errs = sorted(set(m[len(base):] for m in re.findall(r"(" + re.escape(base) + r"[^:\n]+\.swift):\d+:\d+: error:", r.stderr)))
        unresolved = r.returncode != 0 and not errs
        return (p, name), (errs, unresolved, r.stderr[-600:] if r.returncode else "")
    with cf.ThreadPoolExecutor(J) as ex:
        return dict(ex.map(one, jobs))


for rnd in rounds:
    rule, argv = ROUNDS[rnd]
    T = {"round": rnd, "rule": rule}
    t0 = time.time()
    dirty = [p for p in pkgs if git(p, "status", "--porcelain", "--", "Sources", "Tests").stdout.strip()]
    if dirty: raise SystemExit(f"uncommitted changes in {dirty}: commit or reset first")
    pre = lint(os.path.join(work, f"{rnd}-pre"), pkgs); T["lint_pre_s"] = round(time.time() - t0, 1)
    t1 = time.time(); r = sh("python3", *argv(os.path.join(work, f"{rnd}-pre"))); T["apply_s"] = round(time.time() - t1, 1)
    say(f"{rnd}: applied ({T['apply_s']}s) {r.stderr.strip().splitlines()[-1][:160] if r.stderr.strip() else ''}")
    t2 = time.time()
    txns = {p: transactions(p) for p in pkgs}
    changed = [p for p in pkgs if txns[p]]
    post = lint(os.path.join(work, f"{rnd}-post"), changed) if changed else {}
    T["group_lint_s"] = round(time.time() - t2, 1)
    reasons = collections.Counter(); kept = collections.defaultdict(list)
    for p in changed:
        a, b = per_file(pre[p]), per_file(post[p])
        for x in txns[p]:
            if x["lost"] or x["dup"]: reasons["declarations"] += 1; revert(p, x); continue
            before, after = collections.Counter(), collections.Counter()
            for f in x["files"]: before.update(a.get(f, {})); after.update(b.get(f, {}))
            rose = [k for k in after if after[k] > before[k]]
            if rose: reasons["rule rose: " + rose[0]] += 1; revert(p, x); continue
            if after[rule] >= before[rule]: reasons["no gain"] += 1; revert(p, x); continue
            kept[p].append(x)
    t3 = time.time()
    for attempt in (1, 2):
        jobs = [j for p in changed if kept[p] for j in [(p, *t) for t in targets_of(p, [f for x in kept[p] for f in x["files"]])]]
        if not jobs: break
        res = typecheck(jobs)
        bad = 0
        for (p, name), (errs, unresolved, tail) in res.items():
            if not errs and not unresolved: continue
            tp = next(j[2] for j in jobs if j[0] == p and j[1] == name)
            inside = [x for x in kept[p] if any(f.startswith(tp + "/") for f in x["files"])]
            hit = [x for x in inside if set(x["files"]) & set(errs)]
            if unresolved or (attempt == 2 and hit): hit = inside  # no evidence, or still failing: hold the whole target
            for x in hit:
                revert(p, x); kept[p].remove(x); reasons["type-check" + (" (unresolved)" if unresolved else "")] += 1; bad += 1
            if unresolved: T.setdefault("unresolved", []).append(f"{p} {name}: {tail[-200:]}")
        T[f"typecheck{attempt}_targets"] = len(jobs)
        if not bad: break
    T["typecheck_s"] = round(time.time() - t3, 1)
    t4 = time.time()
    final = lint(os.path.join(work, f"{rnd}-final"), changed) if changed else {}
    fixed = 0
    for p in changed:
        n0 = sum(1 for x in pre[p] or [] if x["rule"] == rule); n1 = sum(1 for x in final[p] or [] if x["rule"] == rule)
        tot0, tot1 = len(pre[p] or []), len(final[p] or [])
        git(p, "add", "-A", "Sources", "Tests")
        if kept[p] and git(p, "diff", "--cached", "--quiet").returncode:
            git(p, "commit", "-qm", f"{rule}: {argv('')[0].split('/')[-1]} (gated batch, coenttb/work#242)\n\nKept {len(kept[p])} of {len(txns[p])} changes; each kept change keeps its declarations, raises no rule in its files and type-checks with its target (swiftc against the workspace root build, Linux x86_64, Swift 6.4.2; tests type-checked, not run). {rule}: {n0} -> {n1}; all rules: {tot0} -> {tot1}.")
        fixed += tot0 - tot1
        log.write(json.dumps({"round": rnd, "package": p, "txns": len(txns[p]), "kept": len(kept[p]), "rule_before": n0, "rule_after": n1, "total_before": tot0, "total_after": tot1}) + "\n")
    T["final_lint_commit_s"] = round(time.time() - t4, 1); T["total_s"] = round(time.time() - t0, 1)
    T["txns"] = sum(len(v) for v in txns.values()); T["kept"] = sum(len(v) for v in kept.values()); T["reverted"] = dict(reasons); T["fixed_all_rules"] = fixed
    log.write(json.dumps(T) + "\n"); log.flush()
    say(f"{rnd}: kept {T['kept']}/{T['txns']}, fixed {fixed} (all rules), reverted {dict(reasons)}, {T['total_s']}s")
