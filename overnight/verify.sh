#!/usr/bin/env bash
# Verifies the working state: one root-workspace build of every library product (what every package's dependents
# compile against), then --build-tests for each package given (and with all traits where it declares traits).
# Logs to $OUT. Prints one line per step.
set -u
cd "$(dirname "$0")/.."
OUT=${OUT:?set OUT}; SCRATCH=${SCRATCH:-/home/user/scratch-warn}
mkdir -p "$OUT"
if [ -z "${SKIP_ROOT:-}" ]; then
  s=$(date +%s); swift build --scratch-path "$SCRATCH" > "$OUT/_root.log" 2>&1; echo "ROOT rc=$? $(( $(date +%s)-s ))s"
fi
for p in "$@"; do
  f="$OUT/${p/\//__}"
  s=$(date +%s)
  swift build --package-path "repos/$p" --build-tests --scratch-path "$SCRATCH" > "$f.log" 2>&1; echo "$p default rc=$? $(( $(date +%s)-s ))s"
  if grep -q '^\s*traits:' "repos/$p/Package.swift"; then
    s=$(date +%s)
    swift build --package-path "repos/$p" --build-tests --enable-all-traits --scratch-path "$SCRATCH" > "$f.all-traits.log" 2>&1; echo "$p all-traits rc=$? $(( $(date +%s)-s ))s"
  fi
done
