#!/bin/sh
# Applies the mechanical repairs to every package with errors in errors.txt, in its real checkout (never in the clone),
# then syncs the clones again. Prints what it changed; prints nothing when nothing mechanical is left.
# Edits the real checkouts: never run it while agents are working in them.
W=${W:-$(cd "$(dirname "$0")/.." && pwd)}
cd "$W" || exit 1
grep -oE "^(FAILED )?[^/]+/[^/]+/" errors.txt | sed 's/^FAILED //;s|/$||' | sort -u | while read p; do
  d=$(git -C "repos/$p" remote get-url origin 2>/dev/null)
  [ -n "$d" ] && { python3 overnight/fix-split-leftovers.py "$d" build.log --prefix "$W/repos/$p"; python3 overnight/fix-history-leftovers.py "$d" build.log --prefix "$W/repos/$p"; } | sed "s|^|$p: |"
done
# Test targets the root package can't build because of `package` access across its generated layout are built per
# package instead: recorded in overnight/tests-fallback.txt and in fallback-pending.txt, checked one by one at the end.
grep -E "^[^ ].*/Tests/[^/]+/.*inaccessible due to 'package' protection level" errors.txt |
  sed -E 's|^([^/]+/[^/]+)/Tests/([^/]+)/.*|repos/\1\|\2|' | sort -u | while IFS= read -r line; do
  grep -qxF "$line" overnight/tests-fallback.txt || { echo "$line" >> overnight/tests-fallback.txt; echo "$line" >> fallback-pending.txt; echo "fallback: $line"; }
done
grep -q "inaccessible due to 'package'" errors.txt && ALL_TRAITS=1 python3 -I generate.py > gen.log 2>&1
python3 -I mac/fix-loops-and-test-names.py
mac/sync.sh > /dev/null
