#!/usr/bin/env bash
# lint-par.sh for Coen's Mac (coenttb/work#242, local-only rules): lints the local checkouts under
# ~/Developer/coenttb with a runner built from institute main, J packages at a time.
#   OUT=<dir> [J=8] [RUNNER=…] overnight/lint-mac.sh [owner/name ...]
# Output: $OUT/<owner>__<name>.json, the same shape lint-par.sh writes, so count-lint.py and ratchet.py read it.
# Each package is linted from a mirror of its working tree (no .git, .build), so the checkout is never touched.
set -u
here="$(cd "$(dirname "$0")/.." && pwd)"
root="${ROOT:-$HOME/Developer/coenttb}"
OUT=${OUT:?set OUT}; export OUT root
export RUNNER=${RUNNER:-$root/swift-institute/institute/.build/release/institute-linter-runner}
export MIRROR=${MIRROR:-${TMPDIR:-/tmp}/lintmirror}
J=${J:-8}
mkdir -p "$OUT"
list=("$@"); [ ${#list[@]} -eq 0 ] && list=($(cd "$here" && overnight/packages.sh))
map="$OUT/.paths"
: > "$map"
for p in "${list[@]}"; do
  n=${p#*/}
  d=$(find "$root/swift-institute" "$root" -maxdepth 4 -type d -name "$n" -not -path '*/.build/*' -not -path '*/.claude/*' -exec test -d "{}/.git" \; -print 2>/dev/null | head -1)
  [ -n "$d" ] && printf '%s\t%s\n' "$p" "$d" >> "$map" || echo "no checkout: $p" >&2
done
cut -f1,2 "$map" | xargs -P "$J" -L1 bash -c '
  p=$0; d=$1
  case "$("'"$here"'/overnight/tier.sh" "$p")" in atoms|molecules) b=primitives;; standards) b=standards;; *) b=institute;; esac
  m="$MIRROR/${p/\//__}/$(basename "$p")"; rm -rf "$m"; mkdir -p "$m"
  tar -C "$d" --exclude=./.git --exclude=./.build --exclude=./.swiftpm -cf - . | tar -C "$m" -xf -
  (cd "$m" && SWIFT_LINTER_BUNDLE=$b INSTITUTE_REPOSITORY=$p SWIFT_LINTER_FORMAT=structured "$RUNNER" . \
     > "$OUT/${p/\//__}.json" 2> "$OUT/${p/\//__}.err"; echo "$p rc=$?")
  rm -rf "$MIRROR/${p/\//__}"'
python3 - "$OUT" <<'PY'
import glob, json, sys
for f in glob.glob(sys.argv[1] + "/*.json"):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    d.pop("observations", None); d.pop("controls", None)
    json.dump(d, open(f, "w"))
PY
