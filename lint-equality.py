#!/usr/bin/env python3
"""Compares two source-lint reports of one commit, made on different machines.

    lint-equality.py fingerprint <report.json>            # prints the fingerprint as JSON
    lint-equality.py compare <a> <b>                      # a and b: a report.json or a fingerprint

A report is what `institute ci -- source` prints (CI keeps it as the
`quality-report` artifact) and what `institute lint --report <file>` writes.

Two reports of one commit should differ only in where the checkout was and in
which tool binaries ran. So the fingerprint drops exactly that: the package
root is replaced by $ROOT everywhere, and the top-level `profile`, a digest
over the tools' paths and digests, is left out. Everything else is kept: each
section's SHA-256, and every finding in full, so a difference can be named.

`compare` exits 0 when the two are equal, 1 when they differ.
Swift Institute, swift-institute/institute#287.
"""
import hashlib
import json
import sys


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fingerprint(path):
    text = open(path, encoding="utf-8").read()
    document = json.loads(text)
    if document.get("fingerprint") == 1:
        return document
    roots = sorted({subject["root"] for subject in document["subjects"]}, key=len)
    if not roots:
        raise SystemExit(f"{path}: the report names no subject (unmeasured?): {document.get('references')}")
    root = roots[0]
    document = json.loads(text.replace(json.dumps(root)[1:-1], "$ROOT"))
    document.pop("profile", None)
    sections = {key: sha(value) for key, value in document.items() if key != "measurements"}
    engines = {}
    findings = []
    for measurement in document["measurements"]:
        engine = measurement["engine"]
        verdict = measurement["verdict"]
        found = verdict.get("findings", [])
        for finding in found:
            findings.append(
                [
                    engine,
                    finding["rule"]["token"],
                    finding.get("filePath") or finding.get("fileID"),
                    int(finding["line"]),
                    int(finding["column"]),
                    finding["severity"],
                    finding["identifier"],
                    finding["message"],
                ]
            )
        engines[engine] = {
            "state": verdict.get("state") or verdict.get("status"),
            "reasons": verdict.get("reasons", []),
            "findings": len(found),
            "files": len(measurement["files"]),
            "sections": {key: sha(value) for key, value in measurement.items() if key != "engine"},
        }
    findings.sort()
    subject = [s["identity"] for s in document["subjects"] if "@" in s["identity"]]
    return {
        "fingerprint": 1,
        "subject": subject[0] if subject else None,
        "whole": sha(document),
        "sections": sections,
        "engines": engines,
        "findings": findings,
    }


def compare(a, b):
    left, right = fingerprint(a), fingerprint(b)
    lines = []
    if left["subject"] != right["subject"]:
        lines.append(f"different subjects: {left['subject']} and {right['subject']}")
    for key in sorted(set(left["sections"]) | set(right["sections"])):
        if left["sections"].get(key) != right["sections"].get(key):
            lines.append(f"section `{key}` differs")
    for engine in sorted(set(left["engines"]) | set(right["engines"])):
        l, r = left["engines"].get(engine), right["engines"].get(engine)
        if l is None or r is None:
            lines.append(f"{engine}: measured on one side only")
            continue
        if (l["state"], l["reasons"]) != (r["state"], r["reasons"]):
            lines.append(f"{engine}: verdict {l['state']} {l['reasons']} against {r['state']} {r['reasons']}")
        for key in sorted(set(l["sections"]) | set(r["sections"])):
            if l["sections"].get(key) != r["sections"].get(key):
                lines.append(f"{engine}: `{key}` differs ({l['findings']} findings in {l['files']} files against {r['findings']} in {r['files']})")
    only_left = [f for f in left["findings"] if f not in right["findings"]]
    only_right = [f for f in right["findings"] if f not in left["findings"]]
    for name, only in ((a, only_left), (b, only_right)):
        for engine, rule, file, line, column, severity, identifier, message in only:
            lines.append(f"only in {name}: {file}:{line}:{column}: {severity}: [{engine} {rule}] {message}")
    counts = lambda f: ", ".join(f"{engine} {value['findings']}" for engine, value in sorted(f["engines"].items()))
    print(f"{left['subject']}: {len(left['findings'])} findings ({counts(left)}) against {len(right['findings'])} ({counts(right)})")
    if not lines and left["whole"] == right["whole"]:
        print("equal: every section of the two reports is the same once the checkout root and the tool profile are set aside")
        return 0
    for line in lines:
        print(line)
    if not lines:
        print("the reports differ, but in no section this script compares; diff the reports themselves")
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "fingerprint":
        print(json.dumps(fingerprint(sys.argv[2]), sort_keys=True, ensure_ascii=False, indent=0))
    elif len(sys.argv) == 4 and sys.argv[1] == "compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)
