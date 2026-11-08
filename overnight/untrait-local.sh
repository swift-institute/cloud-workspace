#!/usr/bin/env bash
# Working-tree only: takes the `trait consistency` repair (pushed 8 Nov) back out of each checkout's manifest, so the
# workspace resolves. The committed manifest (what lint and CI read) is untouched; localize.py then marks it skip-worktree.
# SwiftPM never adds a dependency required only by a transitively enabled trait (swift-parser 652ba46).
cd "$(dirname "$0")/.."
for d in repos/*/*; do
  c=$(git -C "$d" log --format=%H --grep='^trait consistency' origin/main -- Package.swift | head -1)
  [ -n "$c" ] || continue
  git -C "$d" update-index --no-skip-worktree Package.swift; git -C "$d" checkout -- Package.swift
  if git -C "$d" diff "$c~1" "$c" -- Package.swift | git -C "$d" apply -R; then echo "untraited $d"; else echo "FAILED $d"; fi
done
./localize.py
