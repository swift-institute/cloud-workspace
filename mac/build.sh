#!/bin/sh
# Builds the generated root package on the Mac, writes build.log and errors.txt (one line per error, paths relative to
# repos/), and prints rc=<exit code>, the wall time, the error count and the first 30 errors.
#   W=<ecosystem folder> mac/build.sh                 whole ecosystem with tests: before every push
#   W=<ecosystem folder> mac/build.sh <Target> ...    only these targets and what they need: between pushes
# No debug info (-gnone, -g0): this build only checks that everything compiles together, and debug info roughly doubles
# its disk and time (9 Nov, coenttb/work#242). Changing these flags rebuilds everything, so keep them fixed.
W=${W:-$(cd "$(dirname "$0")/.." && pwd)}
cd "$W" || exit 1
flags="-Xswiftc -gnone -Xcc -g0"
start=$(date +%s)
if [ $# -eq 0 ]; then
  timeout 7000 swift build --build-tests $flags > build.log 2>&1; rc=$?
else
  targets=""; for t in "$@"; do targets="$targets --target '$t'"; done
  eval timeout 7000 swift build $flags $targets > build.log 2>&1; rc=$?
fi
echo "rc=$rc minutes=$(( ($(date +%s) - start) / 60 ))"
sed 's/\x1b\[[0-9;]*m//g' build.log | grep -E "^/.*error:|failed with a nonzero exit code" |
  sed -E "s|^$W/repos/||;s|^error: SwiftCompile normal [a-z0-9_]+ $W/repos/|FAILED |;s| failed with.*||" | sort -u > errors.txt
wc -l < errors.txt; cut -c1-260 errors.txt | head -30
exit $rc
