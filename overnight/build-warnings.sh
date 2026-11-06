#!/usr/bin/env bash
# Builds every package (or those given) with its tests through the workspace's path dependencies, one shared scratch,
# default traits and, where the package declares traits, all traits. Logs go to $OUT/<owner>__<name>[.all-traits].log.
set -u
cd "$(dirname "$0")/.."
OUT=${OUT:?set OUT}; SCRATCH=${SCRATCH:-/home/user/scratch-warn}
mkdir -p "$OUT"
list=("$@"); [ ${#list[@]} -eq 0 ] && mapfile -t list < <(overnight/packages.sh)
for p in "${list[@]}"; do
  f="$OUT/${p/\//__}"
  avail=$(df --output=avail -k / | tail -1)
  if [ "$avail" -lt 4000000 ]; then echo "LOW DISK before $p: ${avail}k" >&2; fi
  s=$(date +%s)
  swift build --package-path "repos/$p" --build-tests --scratch-path "$SCRATCH" > "$f.log" 2>&1; rc=$?
  echo "$p default rc=$rc $(( $(date +%s)-s ))s"
  if grep -q '^\s*traits:' "repos/$p/Package.swift"; then
    s=$(date +%s)
    swift build --package-path "repos/$p" --build-tests --enable-all-traits --scratch-path "$SCRATCH" > "$f.all-traits.log" 2>&1; rc=$?
    echo "$p all-traits rc=$rc $(( $(date +%s)-s ))s"
  fi
done
