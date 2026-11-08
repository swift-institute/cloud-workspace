#!/usr/bin/env bash
# Commits every checkout's working-tree changes (the path-dependency manifest aside) with message $1.
cd "$(dirname "$0")/.."
for p in $(overnight/packages.sh 2>/dev/null); do d=repos/$p
  [ -n "$(git -C $d status --porcelain --untracked-files=all | grep -v ' Package.swift$')" ] || continue
  git -C $d add -A -- . ':!Package.swift' && git -C $d commit -qm "$1" && echo "$p"
done
