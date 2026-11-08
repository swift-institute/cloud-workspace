#!/usr/bin/env python3
"""For each package|rule over its ratchet limit (ratchet-check.py output): reverts the files whose count for that
rule rose against the baseline lint (overnight/findings-start.json). A file on origin/main goes back to origin/main;
a file this session added goes, with its directory, back to before the adding commit. Commits per package.
Usage: overnight/ratchet-revert.py <lint-dir> <ratchet-check output>"""
import collections, json, os, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lint, over = sys.argv[1], sys.argv[2]
base = collections.Counter()
for it in json.load(open(os.path.join(root, "overnight/findings-start.json")))["items"]:
    base[(it["package"], it["rule"], it["file"][2:])] += 1
def git(d, *a): return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
for line in open(over):
    if "|" not in line: continue
    p, rule, _ = line.strip().split("|")
    d = os.path.join(root, "repos", p)
    try: data = json.load(open(os.path.join(lint, p.replace("/", "__", 1) + ".json")))
    except OSError: continue
    now = collections.Counter(x["filePath"][2:] for x in data["findings"] if x["rule"] == rule)
    for rel, c in now.items():
        if c <= base[(p, rule, rel)]: continue
        if git(d, "cat-file", "-e", f"origin/main:{rel}").returncode == 0:
            git(d, "checkout", "origin/main", "--", rel); print("origin", p, rel)
        else:
            a = git(d, "log", "--no-renames --diff-filter=A", "--format=%H", "-1", "--", rel).stdout.strip()
            if not a: continue
            dd = os.path.dirname(rel)
            for x in git(d, "diff", "--name-only", "--no-renames --diff-filter=A", f"{a}~1", "HEAD", "--", dd).stdout.split("\n"):
                if x: git(d, "rm", "-qf", "--", x)
            git(d, "checkout", f"{a}~1", "--", dd); print("dir", p, dd)
    git(d, "commit", "-qm", f"Revert files that raised `{rule}` over its ratchet limit (coenttb/work#242)")
