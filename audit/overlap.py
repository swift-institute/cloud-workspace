#!/usr/bin/env python3
"""Part 1 step 8: how many lint findings sit on code the structure and semantic steps would delete or change.

Reads the runner's location-level output ($LINT_OUT/<owner>__<name>.json, from overnight/lint-all.sh) and the audit
data. A finding overlaps when its file and line fall inside the declaration span of a candidate:
  delete   public type with no non-test consumer outside its own file (references.json)
  convert  wrapper sorted plain or duplicate (wrappers.json)
  change   any other sorted wrapper (validates, encoding, own behaviour), which the semantic pass revisits
  fold     every finding in a molecule repository marked fold in molecules-verdicts.json (the code moves; findings move with it)
Writes audit/data/overlap.json.
"""
import collections, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "audit", "data")
LINT = os.environ["LINT_OUT"]
WORK = os.environ["AUDIT_WORK"]

types = json.load(open(os.path.join(D, "types.json")))
priv_types = json.load(open(os.path.join(WORK, "private", "types.json")))
span = {(t["repo"], t["file"], t["line"]): t["endLine"] for t in types + priv_types}
refs = json.load(open(os.path.join(D, "references.json")))
wr = json.load(open(os.path.join(D, "wrappers.json"))) + json.load(open(os.path.join(WORK, "private", "wrappers.json")))
verdicts = {}
vp = os.path.join(D, "molecules-verdicts.json")
if os.path.exists(vp):
    verdicts = {m["repo"]: m["verdict"] for m in json.load(open(vp))}

spans = collections.defaultdict(list)  # (repo, file) -> [(start, end, kind)]
for r in refs:
    if r["nontest_files_other"] == 0 and r["kind"] != "typealias":
        e = span.get((r["repo"], r["file"], r["line"]))
        if e: spans[(r["repo"], r["file"])].append((r["line"], e, "delete"))
for w in wr:
    k = "convert" if w["category"] in ("plain", "duplicate") else "change"
    spans[(w["repo"], w["file"])].append((w["line"], w["endLine"], k))

total = 0
hit = collections.Counter()
by_rule_total = collections.Counter(); by_rule_hit = collections.Counter()
for f in glob.glob(os.path.join(LINT, "*.json")):
    repo = os.path.basename(f)[:-5].replace("__", "/", 1)
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for x in d.get("findings", []):
        total += 1
        by_rule_total[x["rule"]] += 1
        path = (x.get("filePath") or x.get("fileID") or "").removeprefix("./")
        kinds = set()
        if verdicts.get(repo) == "fold": kinds.add("fold")
        for s, e, k in spans.get((repo, path), ()):
            if s <= x.get("line", 0) <= e: kinds.add(k)
        for k in kinds: hit[k] += 1
        if kinds & {"delete", "convert", "fold"}:
            hit["delete, convert or fold"] += 1; by_rule_hit[x["rule"]] += 1
        if kinds:
            hit["any, including change"] += 1

out = {"findings": total, "overlap": hit, "share_delete_convert_fold": round(hit["delete, convert or fold"] / max(total, 1), 4),
       "share_any": round(hit["any, including change"] / max(total, 1), 4),
       "by_rule": sorted(((r, by_rule_total[r], by_rule_hit[r]) for r in by_rule_total), key=lambda x: -x[1])}
json.dump(out, open(os.path.join(D, "overlap.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("findings", "overlap", "share_delete_convert_fold", "share_any")}))
