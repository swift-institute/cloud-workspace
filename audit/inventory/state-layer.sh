#!/usr/bin/env bash
# Adds the line `layer: <layer>` to .github/metadata.yaml of each organization's .github repository.
# A cloud session cannot attach a repository whose name begins with a dot, so this runs where `gh` is signed in.
# Not run yet: written in a cloud session without `gh` access. Run it without --write first.
#
#   ./state-layer.sh            # print what would change, change nothing
#   ./state-layer.sh --write    # commit the line to each repository's default branch
#
# It is safe to run twice: an organization that already states a layer is left alone.
set -euo pipefail
write="${1:-}"
while read -r layer organization; do
  file=$(gh api "repos/$organization/.github/contents/.github/metadata.yaml" 2>/dev/null) || { echo "$organization: no .github/metadata.yaml, skipped"; continue; }
  sha=$(jq -r .sha <<<"$file")
  text=$(jq -r .content <<<"$file" | base64 --decode)
  if grep -q '^layer:' <<<"$text"; then echo "$organization: already states $(grep '^layer:' <<<"$text")"; continue; fi
  echo "$organization: layer: $layer"
  [ "$write" = "--write" ] || continue
  printf '%s\nlayer: %s\n' "$text" "$layer" | base64 | tr -d '\n' > /tmp/state-layer.b64
  gh api -X PUT "repos/$organization/.github/contents/.github/metadata.yaml" \
    -f message="metadata: this organization's layer is $layer" -f sha="$sha" -F content=@/tmp/state-layer.b64 --silent
done <<'ROSTER'
control swift-institute
atoms swift-atoms
molecules swift-molecules
compositions swift-compositions
standards swift-standards
standards swift-arm-ltd
standards swift-bipm
standards swift-ecma
standards swift-iec
standards swift-ieee
standards swift-ietf
standards swift-incits
standards swift-intel
standards swift-iso
standards swift-linux-foundation
standards swift-microsoft
standards swift-riscv
standards swift-w3c
standards swift-whatwg
ROSTER
