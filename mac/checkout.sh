#!/bin/sh
# Prints the real Mac checkout of an ecosystem package, given its repos/ path (owner/name).
# Institute checkouts live under $CHECKOUTS as <owner>/<name>, swift-standards/<owner>/<name> or <name>; any other
# repository (private-repos.txt) under $DEVELOPER as <name> or <folder>/<owner>/<name>.
C=${CHECKOUTS:-$HOME/Developer/coenttb/swift-institute}
D=${DEVELOPER:-$HOME/Developer/coenttb}
owner=${1%%/*}; name=${1#*/}
for d in "$C/$owner/$name" "$C/swift-standards/$owner/$name" "$C/$name" "$D/$name" "$D"/*/"$owner/$name"; do
  [ -d "$d/.git" ] && { echo "$d"; exit 0; }
done
exit 1
