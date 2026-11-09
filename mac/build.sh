#!/bin/sh
# Builds the whole ecosystem with its tests in one go, writes build.log and errors.txt (one line per error, paths relative
# to repos/), and prints rc=<exit code>, the error count and the first 30 errors.
W=${W:-$(cd "$(dirname "$0")/.." && pwd)}
cd "$W" || exit 1
timeout 3500 swift build --build-tests > build.log 2>&1; echo rc=$?
sed 's/\x1b\[[0-9;]*m//g' build.log | grep -E "^/.*error:|failed with a nonzero exit code" |
  sed -E "s|^$W/repos/||;s|^error: SwiftCompile normal [a-z0-9_]+ $W/repos/|FAILED |;s| failed with.*||" | sort -u > errors.txt
wc -l < errors.txt; cut -c1-260 errors.txt | head -30
