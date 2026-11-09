#!/bin/sh
# Tests mac/sync.sh in a throwaway folder: a clone whose checkout changed Package.swift after localize.py marked the
# clone's copy skip-worktree and rewrote it must still end on the checkout's HEAD, with the checkout's uncommitted files.
set -u
here=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
C="$T/checkouts"; W="$T/w"
mkdir -p "$C/swift-atoms/swift-example" "$W"
cp -R "$here" "$W/mac"
# localize.py stand-in: rewrite each clone's manifest and mark it skip-worktree, as the real one does.
cat > "$W/localize.py" <<'PY'
import glob, os, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__)))
for p in glob.glob("repos/*/*"):
    open(p + "/Package.swift", "a").write("// localized\n")
    subprocess.run(["git", "-C", p, "update-index", "--skip-worktree", "Package.swift"], check=True)
PY
echo "// generated" > "$W/Package.swift"
echo "swift-atoms/swift-example" > "$W/repos.txt"
g() { git -C "$C/swift-atoms/swift-example" -c user.name=t -c user.email=t@t "$@"; }
g init -q -b main
echo "// v1" > "$C/swift-atoms/swift-example/Package.swift"; echo "a" > "$C/swift-atoms/swift-example/A.swift"
g add . && g commit -q -m v1
CHECKOUTS="$C" W="$W" "$W/mac/sync.sh" > /dev/null
echo "// v2" > "$C/swift-atoms/swift-example/Package.swift"; g commit -q -am v2
echo "b" > "$C/swift-atoms/swift-example/B.swift"
CHECKOUTS="$C" W="$W" "$W/mac/sync.sh" > "$T/out" 2>&1
fail=0
want=$(g rev-parse HEAD); got=$(git -C "$W/repos/swift-atoms/swift-example" rev-parse HEAD)
[ "$want" = "$got" ] || { echo "FAIL: clone on $got, checkout on $want"; cat "$T/out"; fail=1; }
[ -f "$W/repos/swift-atoms/swift-example/B.swift" ] || { echo "FAIL: uncommitted B.swift not copied"; fail=1; }
grep -q "^// v2" "$W/repos/swift-atoms/swift-example/Package.swift" || { echo "FAIL: manifest not v2"; fail=1; }
[ $fail = 0 ] && echo "PASS"; exit $fail
