#!/usr/bin/env bash
# Counts suppression directives written as comments in Swift sources and manifests of every checkout:
# swift-linter:disable…, swiftlint:disable…, swift-format-ignore. String fixtures inside tests aren't comments and don't count.
cd "$(dirname "$0")/../repos"
grep -rhoE '^\s*//\s*(swift-linter:disable[a-z:]*|swiftlint:disable[a-z:]*|swift-format-ignore)' --include=*.swift . \
  | sed -E 's#^\s*//\s*##; s#:(next|this|previous|line)$##' | sort | uniq -c | sort -rn
grep -rhoE '//\s*(swift-linter:disable|swiftlint:disable|swift-format-ignore)' --include=*.swift . | grep -c '' | sed 's/^/all comment-position directives incl. trailing: /'
