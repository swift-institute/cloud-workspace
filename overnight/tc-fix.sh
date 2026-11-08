#!/usr/bin/env bash
# Repairs what a typecheck-direct.sh log names: an unused `public import` becomes internal; a weaker duplicate import
# line goes; macro-plugin and missing-module errors (tool limits) are ignored; any other error reverts the file
# (build-revert.sh's rules: before the minimal-body moves, else origin/main; a split's new file: its directory back to
# before the adding commit). Commits per file. Usage: overnight/tc-fix.sh <log>
cd "$(dirname "$0")/.."
log=$1
grep -oE "/home/user/cloud-workspace/repos/[^:]+\.swift:[0-9]+:[0-9]+: error: .*" "$log" | sort -u > /tmp/tcfix.$$
# Mechanical ones first.
grep -E "UnusedImportAccess|is imported as" /tmp/tcfix.$$ | while IFS=: read -r f l c rest; do
  if echo "$rest" | grep -q UnusedImportAccess; then sed -i "${l}s/^\([[:space:]]*\)public import /\1import /" "$f"
  else sed -i "${l}s/^.*import .*$/__DROP__/" "$f"; fi
done
grep -E "is imported as" /tmp/tcfix.$$ | cut -d: -f1 | sort -u | while IFS= read -r f; do sed -i "/^__DROP__$/d" "$f"; done
grep -E "UnusedImportAccess|is imported as" /tmp/tcfix.$$ | cut -d: -f1 | sort -u | while IFS= read -r f; do
  r=${f#/home/user/cloud-workspace/}; d=$(echo "$r" | cut -d/ -f1-3); git -C "$d" commit -qam "Import access fixed after moves (type-check, coenttb/work#242)" && echo "imports $d"
done
grep -vE "UnusedImportAccess|is imported as|external macro implementation|no such module|missing required module|_SwiftSyntax" /tmp/tcfix.$$ | cut -d: -f1 | sort -u | while IFS= read -r f; do
  r=${f#/home/user/cloud-workspace/}; d=$(echo "$r" | cut -d/ -f1-3); rel=${r#$d/}
  c=$(git -C "$d" log --reverse --format=%H --grep="^minimal type body: \(non-stored\|more non-stored\)" | head -1)
  if ! git -C "$d" cat-file -e "origin/main:$rel" 2>/dev/null; then
    a=$(git -C "$d" log --no-renames --diff-filter=A --format=%H -1 -- "$rel"); dd=$(dirname "$rel")
    [ -n "$a" ] || continue
    git -C "$d" diff --name-only --no-renames --diff-filter=A "$a~1" HEAD -- "$dd" | while IFS= read -r x; do git -C "$d" rm -qf -- "$x"; done
    git -C "$d" checkout "$a~1" -- "$dd"
  elif [ -n "$c" ] && ! git -C "$d" diff --quiet "$c~1" -- "$rel"; then git -C "$d" checkout "$c~1" -- "$rel"
  elif ! git -C "$d" diff --quiet origin/main -- "$rel"; then git -C "$d" checkout origin/main -- "$rel"
  else echo "unchanged, failing: $r"; continue; fi
  git -C "$d" commit -qm "Revert $rel: it broke the type-check (coenttb/work#242)" && echo "reverted $r"
done
rm -f /tmp/tcfix.$$
