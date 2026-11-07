#!/usr/bin/env python3
"""Part 1 step 4: a verdict for each molecule, from audit/data/molecules.json. Rules, in order:

1. delete   no dependent in the workspace and under 60 source lines: nothing here uses it
            and it holds too little to be worth a repository. Labelled "no consumer in the workspace": the Mac apps and
            Rule Institute are checked by the coordinator before anything goes.
2. fold     a bridge between two or more atoms (its name is made of its atom dependencies' names), no molecule
            dependency beyond the bridged ones, at most 600 source lines, with or without dependents: it becomes a trait of its host atom. Benefit: one repository, manifest,
            CI matrix and release fewer, and consumers stop needing a third package for two they already have.
3. keep     everything else, with the reason: it depends on other molecules (folding would put a molecule edge into an
            atom), it is large, or it is a data structure or runtime with its own dependents.
Fold cost, per candidate: the host gains a trait and an optional dependency; `--enable-all-traits` builds it; the
traits-off job no longer compiles the bridged code, so the host needs a trait-on test leg; no candidate has platform
conditionals (Windows unaffected) and Embedded is unaffected because the trait is off by default.
"""
import json, os

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit", "data")
ms = json.load(open(os.path.join(D, "molecules.json")))
out = []
for m in ms:
    name = m["repo"].split("/")[1].removeprefix("swift-")
    atoms = {a.split("/")[1].removeprefix("swift-") for a in m["atom_deps"]}
    parts = name.split("-")
    bridge = len(parts) >= 2 and sum(1 for p in parts if p in atoms or p + "s" in atoms or p.rstrip("s") in atoms) >= 2
    host = None
    if bridge:
        cands = [a for a in m["atom_deps"] if a.split("/")[1].removeprefix("swift-") in parts]
        host = cands[0] if cands else m["fold_host"]
    if m["dependents"] == 0 and m["source_lines"] < 60:
        v, why = "delete", "no consumer in the workspace and %d declarations in %d source lines" % (m["declarations"], m["source_lines"])
    elif bridge and m["source_lines"] <= 600 and all(x.split("/")[1].removeprefix("swift-") in parts for x in m["molecule_deps"]) and not (m["molecule_deps"] and not host):
        v, why = "fold", "bridge of %s; fold into %s behind a trait" % (", ".join(sorted(atoms & set(parts))), host)
    elif m["molecule_deps"]:
        v, why = "keep", "depends on molecules (%s): folding would give an atom a molecule edge" % ", ".join(x.split("/")[1] for x in m["molecule_deps"])
    elif m["dependents"] == 0:
        v, why = "keep", "no consumer in the workspace, but %d source lines of its own: ask, don't fold" % m["source_lines"]
    else:
        v, why = "keep", "its own structure with %d dependents and %d atom dependencies; no single host" % (m["dependents"], len(m["atom_deps"]))
    out.append(dict(m, verdict=v, reason=why, bridge=bridge, fold_into=host if v == "fold" else None))
json.dump(out, open(os.path.join(D, "molecules-verdicts.json"), "w"), indent=1, sort_keys=True)
with open(os.path.join(D, "molecules.md"), "w") as f:
    f.write("| Molecule | Lines | Decls | Atom deps | Molecule deps | Dependents | Traits | Verdict | Reason |\n|---|---|---|---|---|---|---|---|---|\n")
    for m in sorted(out, key=lambda m: ({"delete": 0, "fold": 1, "keep": 2}[m["verdict"]], m["source_lines"])):
        f.write("| %s | %d | %d | %d | %d | %d | %s | **%s** | %s |\n" % (m["repo"].split("/")[1], m["source_lines"], m["declarations"], len(m["atom_deps"]),
                len(m["molecule_deps"]), m["dependents"], ", ".join(m["traits"]) or "-", m["verdict"], m["reason"]))
import collections
print(collections.Counter(m["verdict"] for m in out))
for m in out:
    if m["verdict"] != "keep": print(m["verdict"], m["repo"], m["reason"])
