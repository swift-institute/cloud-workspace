#!/usr/bin/env python3
"""Commits each changed checkout with a message built from the apply logs of a round.

    overnight/commit-round.py <round-name> <evidence sentence> <package-list-file> <log> [<log> ...]

Each log line is "<owner/name> <path> ..." as apply-repairs.py, apply-fixits.py and rename-extension-files.py print
them; the log's file name says what it applied (apply-<what>.txt). Package.swift (skip-worktree) is never staged."""
import collections, os, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, evidence = sys.argv[1], sys.argv[2]
only = set(open(sys.argv[3]).read().split())
logs = sys.argv[4:]
WHAT = {
    "comment": "plain comments removed from Sources with the runner's `comment in source` repair (documentation, disclosure markers and tool directives kept)",
    "modsel": "a module named with member syntax spelled with a module selector, `Module::Name`, by the runner's `module selector spelling` repair",
    "protq": "standard-library protocols that a module can shadow qualified as `Swift.<Protocol>`, by the runner's `swift protocol qualification` repair",
    "rename": "files renamed to the name `extension file naming` gives for the conformance they add",
    "counter": "range loops over a counter written as `forEach`, by the runner's `counter loop iteration` repair (only loops with no break, continue, return or typed throws)",
    "minimal": "members moved out of type bodies into extensions, by the runner's `minimal type body` repair",
    "fixits": "compiler warnings fixed with the compiler's own fix-its, or by removing the marker a warning points at: unnecessary try, await or unsafe, a missing unsafe, var never mutated, an unused public import",
    "testnames": "a @Test function's display string moved into its name as a raw identifier (`test display name string`)",
}
per_repo = collections.defaultdict(collections.Counter)
for log in logs:
    what = os.path.basename(log)[len("apply-"):-len(".txt")].replace("-am", "").replace("-up", "").replace("-std", "")
    for line in open(log):
        parts = line.split()
        if len(parts) < 2 or "/" not in parts[0] or parts[0].startswith("SKIP"):
            continue
        repo = "/".join(parts[0].split("/")[:2])
        if repo in only:
            per_repo[repo][what] += 1


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


for p, counts in sorted(per_repo.items()):
    repo = os.path.join(root, "repos", p)
    status = git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    paths = [l[3:] for l in status if not l.endswith(" Package.swift") and not l.endswith("Package.swift\"")]
    if not paths:
        continue
    git(repo, "add", "-A", "--", "Sources", "Tests")
    staged = git(repo, "diff", "--cached", "--name-only").stdout.split()
    if not staged:
        continue
    items = "; ".join(f"{WHAT.get(w, w)} ({n} file{'s' if n != 1 else ''})" for w, n in sorted(counts.items()))
    message = (f"Lint findings cleared without behaviour change ({name}, coenttb/work#240): {items}. "
               f"Changed files formatted with the Institute's swift-format configuration where the committed file was already stable under it. {evidence}")
    r = git(repo, "commit", "-q", "-m", message)
    print(p, "committed" if r.returncode == 0 else "FAILED " + r.stderr.strip()[:200])
