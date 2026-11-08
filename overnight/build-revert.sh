#!/usr/bin/env bash
# Root build with tests; reverts each file the compiler reports an error in to its state before this session's
# minimal-body moves (or origin/main), commits, and builds again, up to N rounds. Prints one line per round.
set -u
cd "$(dirname "$0")/.."
N=${1:-8}
for round in $(seq 1 $N); do
  s=$(date +%s); swift build --build-tests -j 3 --scratch-path /home/user/scratch-warn > /home/user/logs/roottests.log 2>&1; rc=$?
  echo "round $round rc=$rc $(( $(date +%s)-s ))s"
  [ $rc = 0 ] && { echo GREEN; exit 0; }
  files=$(sed 's/\x1b\[[0-9;]*m//g' /home/user/logs/roottests.log | grep -oE "/home/user/cloud-workspace/repos/[^:]+\.swift:[0-9]+:[0-9]+: error" | cut -d: -f1 | sort -u)
  [ -n "$files" ] || { echo "no file errors"; exit 1; }
  for f in $files; do :; done
  echo "$files" | while IFS= read -r f; do
    r=${f#/home/user/cloud-workspace/}; d=$(echo "$r" | cut -d/ -f1-3); rel=${r#$d/}
    c=$(git -C "$d" log --reverse --format=%H --grep="^minimal type body: \(non-stored\|more non-stored\)" | head -1)
    if ! git -C "$d" cat-file -e "origin/main:$rel" 2>/dev/null; then
      # Added by this session (a split): its directory goes back to before the commit that added it.
      a=$(git -C "$d" log --diff-filter=A --format=%H -1 -- "$rel"); dd=$(dirname "$rel")
      git -C "$d" diff --name-only --diff-filter=A "$a~1" HEAD -- "$dd" | while IFS= read -r x; do git -C "$d" rm -qf -- "$x"; done
      git -C "$d" checkout "$a~1" -- "$dd"
    elif [ -n "$c" ] && ! git -C "$d" diff --quiet "$c~1" -- "$rel"; then git -C "$d" checkout "$c~1" -- "$rel"
    elif ! git -C "$d" diff --quiet origin/main -- "$rel" && git -C "$d" cat-file -e "origin/main:$rel" 2>/dev/null; then git -C "$d" checkout origin/main -- "$rel"
    else
      # Unchanged by this session: a test target goes on the fallback list (built per package), and the root regenerates.
      tdir=$(echo "$rel" | cut -d/ -f1-2)
      name=$(grep -F "path: \"$d/$tdir\"" Package.swift | grep -o "testTarget(name: \"[^\"]*\"" | head -1 | sed "s/testTarget(name: \"\\(.*\\)\"/\\1/")
      if [ -n "$name" ]; then echo "$d|$name" >> overnight/tests-fallback.txt; ./generate.py > /dev/null 2>&1; echo "  fallback $d|$name"
      else echo "  unchanged, failing: $r"; fi
    fi
    git -C "$d" commit -qm "Revert $rel: it broke the root build (coenttb/work#242)" 2>/dev/null && echo "  reverted $r"
  done
done
