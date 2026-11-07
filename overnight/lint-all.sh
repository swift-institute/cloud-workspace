#!/usr/bin/env bash
# Lints every package (or those given) with the runner built from institute main. Each checkout's working tree is
# mirrored to $MIRROR with its committed manifest (the index copy, not the path-dependency rewrite), so it can run
# while a build uses the checkouts. Structured JSON goes to $OUT/<owner>__<name>.json.
set -u
cd "$(dirname "$0")/.."
OUT=${OUT:?set OUT}; R=${RUNNER:-/home/user/tools/runner-main}; MIRROR=${MIRROR:-/home/user/lintmirror}
mkdir -p "$OUT"
list=("$@"); [ ${#list[@]} -eq 0 ] && mapfile -t list < <(overnight/packages.sh)
for p in "${list[@]}"; do
  case "$(overnight/tier.sh "$p")" in atoms|molecules) b=primitives;; standards) b=standards;; *) b=institute;; esac
  m="$MIRROR/$p"; rm -rf "$m"; mkdir -p "$m"
  tar -C "repos/$p" --exclude=./.git --exclude=./.build --exclude=./.swiftpm -cf - . | tar -C "$m" -xf -
  git -C "repos/$p" show :Package.swift > "$m/Package.swift"
  (cd "$m" && SWIFT_LINTER_BUNDLE=$b INSTITUTE_REPOSITORY=$p SWIFT_LINTER_FORMAT=structured "$R" . \
     > "$OUT/${p/\//__}.json" 2> "$OUT/${p/\//__}.err"; echo "$p rc=$?")
done
# Keep findings, suppressions, repairs and the summary; drop per-file observations and control records to save disk.
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
