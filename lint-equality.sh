#!/usr/bin/env bash
# Compares each Linux lint report in lint-equality/ with the macOS `quality-report` artifact that
# CI's `Quality · source` job kept for the same commit (swift-institute/institute#287).
#
#   ./lint-equality.sh          # needs `gh`, signed in; run where GitHub's artifact storage is reachable
#
# lint-equality/INDEX has one line per comparison: <owner/name> <commit> <Linux fingerprint file>.
# A cloud session cannot run this: its network policy blocks the artifact storage host, and its
# GitHub access covers only the repositories attached to it. Prints one line per repository and
# every difference; exits 1 if any pair differs or an artifact is missing.
set -uo pipefail
cd "$(dirname "$0")"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
status=0
while read -r repository commit fingerprint; do
  [ -n "$repository" ] || continue
  run="$(gh api "repos/$repository/actions/runs?head_sha=$commit&per_page=50" \
    --jq '[.workflow_runs[] | select(.path == ".github/workflows/ci.yml")] | .[0].id // empty')"
  if [ -z "$run" ]; then echo "$repository@$commit: no CI run for this commit"; status=1; continue; fi
  directory="$work/${repository//\//__}-$commit"
  if ! gh run download "$run" --repo "$repository" --name quality-report --dir "$directory" 2>/dev/null; then
    echo "$repository@$commit: run $run kept no quality-report (the job did not run, or the artifact expired)"; status=1; continue
  fi
  echo "run $run, macOS against Linux:"
  python3 lint-equality.py compare "$directory/report.json" "lint-equality/$fingerprint" || status=1
done < lint-equality/INDEX
exit $status
