#!/usr/bin/env bash
# Re-measures the audit (coenttb/work#242). Run ./sync.sh first. AUDIT_WORK is a scratch directory outside the repo.
set -eu
cd "$(dirname "$0")/.."
W=${AUDIT_WORK:?set AUDIT_WORK}; mkdir -p "$W/dump"
swift build -c release --package-path audit/extract
find repos -name .build -prune -o -name .git -prune -o -name '*.swift' -type f -print | grep -v '/Package.swift$\|/Package@' > "$W/files.txt"
split -n l/8 "$W/files.txt" "$W/part."
ls "$W"/part.?? | xargs -P 8 -I{} sh -c 'audit/extract/.build/release/extract < {} > {}.jsonl'
cat "$W"/part.??.jsonl > "$W/extract.jsonl"
cat repos.txt private-repos.txt | grep -v '^$' | xargs -P 8 -I{} sh -c 'swift package dump-package --package-path repos/{} > '"$W"'/dump/$(echo {} | tr / _).json'
for r in $(cat repos.txt private-repos.txt); do
  git -C "repos/$r" log --grep='work#239' -p --format='COMMIT %H' -- 'Sources/*.swift' 2>/dev/null |
    awk -v r="$r" '/^\+\+\+ b\//{f=substr($0,7)} /^\+[^+].*(struct|enum|class) [A-Z`]/{match($0,/(struct|enum|class) [A-Za-z_`][A-Za-z0-9_` .]*/); print r"\t"f"\t"substr($0,RSTART,RLENGTH)}'
done > "$W/239src.txt"
python3 audit/analyze.py
python3 audit/molecules.py
# Lint at finding level: OUT=$LINT_OUT overnight/lint-all.sh, then:
#   "$RUNNER" --inventory > "$W/inventory.json"; python3 audit/overlap.py; python3 audit/rules_sample.py; python3 audit/rules_report.py
