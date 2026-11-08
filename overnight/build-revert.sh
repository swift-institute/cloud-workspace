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
    if [ -n "$c" ] && ! git -C "$d" diff --quiet "$c~1" -- "$rel"; then git -C "$d" checkout "$c~1" -- "$rel"
    elif ! git -C "$d" diff --quiet origin/main -- "$rel" && git -C "$d" cat-file -e "origin/main:$rel" 2>/dev/null; then git -C "$d" checkout origin/main -- "$rel"
    else echo "  unchanged, failing: $r"; fi
    git -C "$d" commit -qm "Revert $rel: it broke the root build (coenttb/work#242)" 2>/dev/null && echo "  reverted $r"
  done
done
