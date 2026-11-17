#!/usr/bin/env bash
# Builds the whole ecosystem in parts, for when ./build.sh with no arguments is killed for memory before it ends:
# first every library (the root's `Everything` target), then every test target in groups of 90, compiled and not linked.
# Stops at the first part that fails and leaves its errors in errors.txt. A part killed for memory is run again, three times at most.
# To run a package's tests, which needs them linked: swift test --package-path repos/<owner>/<name> with build.sh's flags.
set -u
cd "$(dirname "$0")"
part() {
  local rc=137 try=0
  while [ $rc = 137 ] && [ $try -lt 3 ]; do ./build.sh "$@" > /dev/null; rc=$?; try=$((try + 1)); done
  return $rc
}
part Everything || { echo "libraries: failed"; cut -c1-260 errors.txt | head -30; exit 1; }
echo "libraries: built"
mapfile -t tests < <(sed -n 's/^targets\.append(\.testTarget(name: "\([^"]*\)".*/\1/p' Package.swift)
for ((i = 0; i < ${#tests[@]}; i += 90)); do
  part "${tests[@]:i:90}" || { echo "test targets $i to $((i + 89)): failed"; cut -c1-260 errors.txt | head -30; exit 1; }
  echo "test targets $i to $((i + 89)): compiled"
done
echo "${#tests[@]} test targets compiled"
