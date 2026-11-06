#!/usr/bin/env bash
# Clones or fast-forwards every repository in repos.txt, plus private-repos.txt if present, into repos/<owner>/<name>,
# then rewrites the manifests and generates Package.swift. Manifests are restored first, or a changed one would stop the pull.
# An uncommitted manifest edit is lost here: commit it first.
set -u
cd "$(dirname "$0")"
[ -d repos ] && ./localize.py --restore
cat repos.txt private-repos.txt 2>/dev/null | grep -v '^$' | xargs -P 16 -I{} bash -c '
  d=repos/{}
  if [ -d "$d/.git" ]; then git -C "$d" pull -q --ff-only || echo "PULL FAILED {}"
  else mkdir -p "$(dirname "$d")"; git clone -q --filter=blob:none "https://github.com/{}.git" "$d" || echo "CLONE FAILED {}"; fi'
echo "$(find repos -mindepth 2 -maxdepth 2 -type d | wc -l | tr -d " ") repositories in repos/"
./localize.py
./generate.py
