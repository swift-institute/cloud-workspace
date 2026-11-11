#!/bin/sh
# Makes each clone in repos/ match its real Mac checkout exactly: the checkout's HEAD (pushed or not) plus its uncommitted
# and untracked source files. A clone's origin is the checkout itself, so nothing is read from GitHub: a checkout behind
# GitHub gives an equally old clone, never a mix. Clones missing from repos/ are cloned from their checkout.
# Package.swift is left to localize.py, which rewrites it for the build. A clone never holds work of its own: anything
# changed in a clone is overwritten here, so fix in the checkouts.
#   [HEAD_ONLY="owner/name ..."|HEAD_ONLY=all] mac/sync.sh [owner/name ...]
# (default: every package in repos.txt, plus the git-ignored private-repos.txt in the ecosystem folder if present)
# HEAD_ONLY names checkouts whose uncommitted files belong to someone else (or all of them, while agents are editing):
# their clones get the committed HEAD only.
W=${W:-$(cd "$(dirname "$0")/.." && pwd)}
cd "$W" || exit 1
if [ $# -gt 0 ]; then list="$*"; else list=$(cat repos.txt private-repos.txt 2>/dev/null | grep -v '^$'); fi
for d in $list; do
  r="repos/$d"
  if [ ! -d "$r/.git" ]; then
    src=$(mac/checkout.sh "$d") || { echo "NO-CHECKOUT $d"; continue; }
    mkdir -p "$(dirname "$r")"; git clone -q --local "$src" "$r" || { echo "CLONE-FAILED $d"; continue; }
  fi
  src=$(git -C "$r" remote get-url origin)
  git -C "$r" fetch -q origin HEAD || { echo "FETCH-FAILED $d"; continue; }
  # localize.py marks the rewritten manifest skip-worktree; with the mark set, a reset to a commit that changed it fails.
  git -C "$r" ls-files -v | sed -n 's/^S //p' | while IFS= read -r f; do git -C "$r" update-index --no-skip-worktree -- "$f"; done
  git -C "$r" reset -q --hard FETCH_HEAD || { echo "RESET-FAILED $d"; continue; }
  git -C "$r" clean -qfd
  case "${HEAD_ONLY:-}" in all) echo "HEAD-ONLY $d"; continue;; esac
  case " ${HEAD_ONLY:-} " in *" $d "*) echo "HEAD-ONLY $d"; continue;; esac
  { git -C "$src" diff --name-only HEAD; git -C "$src" ls-files --others --exclude-standard; } | sort -u | grep -v '^Package.swift$' |
  while IFS= read -r f; do
    if [ -e "$src/$f" ]; then mkdir -p "$(dirname "$r/$f")"; cp "$src/$f" "$r/$f"; else rm -f "$r/$f"; fi
    echo "$r/$f"
  done
done
python3 -I localize.py > /dev/null && echo "manifests localized"
[ -f Package.swift ] || { ALL_TRAITS=1 python3 -I generate.py > gen.log 2>&1 && echo "Package.swift generated"; }
