#!/bin/sh
# Builds, applies the mechanical repairs, and builds again, up to 25 rounds. Ends with GREEN, or NEEDS HAND FIX and the
# first errors. Edits the real checkouts through fix.sh: never run it while agents are working in them.
W=${W:-$(cd "$(dirname "$0")/.." && pwd)}
for i in $(seq 1 25); do
  out=$("$W/mac/build.sh"); echo "== round $i: $(echo "$out" | head -2 | tr '\n' ' ')"
  echo "$out" | head -1 | grep -q "rc=0" && { echo GREEN; exit 0; }
  fixed=$("$W/mac/fix.sh"); echo "$fixed"
  [ -z "$fixed" ] && { echo "NEEDS HAND FIX"; cut -c1-300 "$W/errors.txt" | head -20; exit 1; }
done
exit 1
