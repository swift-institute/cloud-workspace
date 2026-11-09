#!/bin/sh
# Prints the real Mac checkout of an ecosystem package, given its repos/ path (owner/name).
# Checkouts live under $CHECKOUTS as <owner>/<name>, swift-standards/<owner>/<name> or <name>.
C=${CHECKOUTS:-$HOME/Developer/coenttb/swift-institute}
owner=${1%%/*}; name=${1#*/}
for d in "$C/$owner/$name" "$C/swift-standards/$owner/$name" "$C/$name"; do
  [ -d "$d/.git" ] && { echo "$d"; exit 0; }
done
exit 1
