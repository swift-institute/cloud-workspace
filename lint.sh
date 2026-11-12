#!/usr/bin/env bash
# Lints the package in the current directory as CI's `Quality · source` does, on Linux x86_64.
#
#   cd repos/<owner>/<name> && ../../../lint.sh          # findings, then the outcome; exit 0 when CI would pass
#   ../../../lint.sh --fix                               # first rewrite what swift-format can repair
#   ../../../lint.sh --report report.json                # also write the JSON report CI keeps as quality-report
#
# It runs `institute lint` from the published planner named below: downloaded once from
# swift-institute/institute's ci-binaries release, checked against its SHA-256, kept under
# ~/.cache/institute. The planner fetches the lint's own tools, each pinned by digest. One of them,
# swift-format, is the Swift 6.4.2 toolchain's own (swift.org, ubuntu24.04): that toolchain must be
# first on PATH, as it is on a cloud machine.
#
# Move both lines together when swift-institute/.github's .institute-ci-pin moves: the row for
# linux-x86_64 in its .institute-ci-planner. Exit status: 0 CI would pass, 1 it would fail, 2 the
# lint could not be completed.
set -euo pipefail
REVISION=__REVISION__
DIGEST=__DIGEST__

[ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ] || { echo "lint.sh: Linux x86_64 only; on macOS run \`institute lint\`" >&2; exit 2; }
command -v swift >/dev/null || { echo "lint.sh: no swift on PATH" >&2; exit 2; }
cache="${XDG_CACHE_HOME:-$HOME/.cache}/institute/planner"
binary="$cache/institute-linux-x86_64-$DIGEST"
if [ ! -x "$binary" ] || [ "$(sha256sum "$binary" | cut -d' ' -f1)" != "$DIGEST" ]; then
  mkdir -p "$cache"
  curl --fail --silent --show-error --location --retry 5 -o "$binary.download" \
    "https://github.com/swift-institute/institute/releases/download/ci-binaries/institute-linux-x86_64-$DIGEST"
  [ "$(sha256sum "$binary.download" | cut -d' ' -f1)" = "$DIGEST" ] \
    || { echo "lint.sh: the planner of $REVISION does not hash to $DIGEST" >&2; rm -f "$binary.download"; exit 2; }
  chmod +x "$binary.download"
  mv "$binary.download" "$binary"
fi
# The planner loads the Swift runtime from the toolchain: usr/lib/swift/linux beside the usr/bin swift is in.
runtime="$(cd "$(dirname "$(readlink -f "$(command -v swift)")")/../lib/swift/linux" && pwd -P)"
export LD_LIBRARY_PATH="$runtime${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# In this workspace a checkout's Package.swift is rewritten to path dependencies and marked
# skip-worktree (localize.py). CI lints the committed manifest, so that is put back for the run and
# the rewrite restored after it. A repair of the manifest is therefore not kept: it is reported.
if [ -f Package.swift ] && git ls-files -v -- Package.swift 2>/dev/null | grep -q '^S '; then
  localized="$(mktemp)"
  cp Package.swift "$localized"
  trap 'cp "$localized" Package.swift; rm -f "$localized"' EXIT
  git show :Package.swift > Package.swift
  status=0
  "$binary" lint "$@" || status=$?
  git show :Package.swift | cmp -s - Package.swift \
    || echo "lint.sh: --fix rewrote Package.swift, which is localized here, so the rewrite was not kept; ./localize.py --restore, repair and commit it" >&2
  exit "$status"
fi
exec "$binary" lint "$@"
