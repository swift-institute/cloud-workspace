#!/usr/bin/env bash
# lint-all.sh, J packages at a time (default: CPU count). Same mirrors, same output: $OUT/<owner>__<name>.json.
# Each package gets its own mirror directory, so parallel runs share no temporary files.
# Usage: OUT=<dir> [J=4] overnight/lint-par.sh [package ...]
set -u
cd "$(dirname "$0")/.."
OUT=${OUT:?set OUT}; export OUT RUNNER=${RUNNER:-/home/user/tools/runner-main} MIRROR=${MIRROR:-/home/user/lintmirror}
J=${J:-$(nproc)}
mkdir -p "$OUT"
list=("$@"); [ ${#list[@]} -eq 0 ] && mapfile -t list < <(overnight/packages.sh)
printf '%s\n' "${list[@]}" | xargs -P "$J" -I{} bash -c '
  p={}
  case "$(overnight/tier.sh "$p")" in atoms|molecules) b=primitives;; standards) b=standards;; *) b=institute;; esac
  m="$MIRROR/${p/\//__}/$(basename "$p")"; rm -rf "$m"; mkdir -p "$m"
  tar -C "repos/$p" --exclude=./.git --exclude=./.build --exclude=./.swiftpm -cf - . | tar -C "$m" -xf -
  git -C "repos/$p" show :Package.swift > "$m/Package.swift"
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
    d["failedControls"] = [c for c in d.get("controls", []) if c.get("actualFindings") is not None and c.get("expectation", {}).get("status") == "findings" and c.get("actualFindings") != c["expectation"].get("count")]
    d.pop("observations", None); d.pop("controls", None)
    json.dump(d, open(f, "w"))
PY
