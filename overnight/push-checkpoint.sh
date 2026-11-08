#!/usr/bin/env bash
# Pushes each listed checkout's HEAD to origin main, never forced: fetches first and holds a repository whose
# origin/main moved (not a fast-forward). Appends "<tier> <pkg> <sha> pushed|held: reason" to overnight/pushes-checkpoint.txt.
# Usage: overnight/push-checkpoint.sh <tier> < list-of-packages
cd "$(dirname "$0")/.."
t=$1
while read -r p; do d=repos/$p
  ok=0; for i in 1 2 3; do git -C $d fetch -q origin main 2>/dev/null && { ok=1; break; }; sleep $((2**i)); done
  [ $ok = 1 ] || { echo "$t $p - held: fetch failed" | tee -a overnight/pushes-checkpoint.txt; continue; }
  git -C $d merge-base --is-ancestor origin/main HEAD || { echo "$t $p - held: origin/main moved" | tee -a overnight/pushes-checkpoint.txt; continue; }
  [ -n "$(git -C $d log --oneline origin/main..HEAD | head -1)" ] || { echo "$t $p - nothing to push" | tee -a overnight/pushes-checkpoint.txt; continue; }
  r=held; for i in 1 2 3 4; do out=$(git -C $d push origin HEAD:main 2>&1) && { r=pushed; break; }; echo "$out" | grep -q "403\|denied" && break; sleep $((2**i)); done
  echo "$t $p $(git -C $d rev-parse HEAD) $r$( [ $r = held ] && echo ": $(echo "$out" | tail -1 | cut -c1-120)")" | tee -a overnight/pushes-checkpoint.txt
done
