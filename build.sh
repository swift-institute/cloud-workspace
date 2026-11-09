#!/usr/bin/env bash
# Builds the generated root package on a cloud machine (Linux, 4 cores, 15 GB memory, a fixed disk allowance).
#
#   ./build.sh                  whole ecosystem with tests: once, right before a push
#   ./build.sh <Target> ...     only these targets and what they need, without linking: between pushes
#
# Settings, each needed on this machine (9 Nov, coenttb/work#242):
#   -Xswiftc -gnone -Xcc -g0    no debug info: with it, the linked test libraries alone took 15 GB of disk
#   -Xswiftc -use-ld=lld        lld links the large test libraries in a fraction of gold's memory (gold needed >12 GB)
#   --disable-dead-strip        with lld, --gc-sections drops the Swift metadata macro plugins need ("external macro implementation type ... could not be found")
#   -j 3                        leaves memory for swift-build itself, which grows to about 13.5 GB on a whole run
# Writes build.log and errors.txt (one line per error, paths relative to repos/), prints rc and the errors.
set -u
cd "$(dirname "$0")"
flags=(-j 3 -Xswiftc -gnone -Xcc -g0 -Xswiftc -use-ld=lld --disable-dead-strip)
if [ $# -eq 0 ]; then
  timeout 7000 swift build --build-tests "${flags[@]}" > build.log 2>&1
else
  targets=(); for t in "$@"; do targets+=(--target "$t"); done
  timeout 7000 swift build "${flags[@]}" "${targets[@]}" > build.log 2>&1
fi
rc=$?; echo "rc=$rc"
W=$PWD
sed 's/\x1b\[[0-9;]*m//g' build.log | grep -E "^/.*error:|error: (link|ld|clang)" | sed -E "s|^$W/repos/||" | sort -u > errors.txt
[ $rc = 137 ] && echo "killed for memory: swift-build itself grows past 13.5 GB on a whole run that goes to the end; run again (it resumes) or build targets"
wc -l < errors.txt; cut -c1-260 errors.txt | head -30
exit $rc
