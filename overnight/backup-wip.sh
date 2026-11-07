#!/usr/bin/env bash
# Backs up local commits: git format-patch origin/main of each checkout with unpushed commits into
# wip/<owner>__<name>/ on branch findings-wip of this repository (a separate worktree), and pushes that branch.
set -u
cd "$(dirname "$0")/.."
W=${WIP:-/home/user/findings-wip}
if [ ! -d "$W" ]; then
  git fetch -q origin findings-wip 2>/dev/null && git worktree add -q "$W" -B findings-wip origin/findings-wip \
    || { git worktree add -q --detach "$W" && git -C "$W" checkout -q --orphan findings-wip && git -C "$W" rm -rq . ; }
fi
rm -rf "$W/wip"; mkdir -p "$W/wip"
for d in repos/*/*; do
  [ -n "$(git -C "$d" log --oneline origin/main..HEAD 2>/dev/null)" ] || continue
  o="$W/wip/$(basename "$(dirname "$d")")__$(basename "$d")"; mkdir -p "$o"
  git -C "$d" format-patch -q origin/main -o "$o"
done
git -C "$W" add -A wip
git -C "$W" commit -qm "${1:-findings-wip backup}" && git -C "$W" push -q -u origin findings-wip
echo "backup: $(ls "$W/wip" | wc -l) repositories"
