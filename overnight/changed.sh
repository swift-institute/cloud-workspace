#!/usr/bin/env bash
# Lists checkouts with uncommitted changes (the path-dependency manifest rewrite aside, a committed-manifest edit
# included) or commits not on origin/main.
cd "$(dirname "$0")/.."
for p in $(overnight/packages.sh); do
  d=repos/$p
  skip=$(git -C $d ls-files -v Package.swift | cut -c1)
  dirty=$(git -C $d status --porcelain --untracked-files=all | grep -v ' Package.swift$' | head -1)
  [ "$skip" != S ] && [ -n "$(git -C $d status --porcelain Package.swift)" ] && dirty=1
  ahead=$(git -C $d rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  if [ -n "$dirty" ] || [ "$ahead" != 0 ]; then echo $p; fi
done
