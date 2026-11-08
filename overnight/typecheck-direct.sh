#!/usr/bin/env bash
# Runs each argument file from typecheck-direct.py with swiftc, J at a time; prints FAIL lines with the error files.
d=$1; J=${2:-2}
ls "$d"/*.args | xargs -P "$J" -I{} bash -c 'out=$(xargs -0 swiftc < "{}" 2>&1); rc=$?; if [ $rc != 0 ]; then echo "FAIL $(basename "{}" .args)"; echo "$out" | grep -oE "/home/user/cloud-workspace/repos/[^:]+\.swift:[0-9]+:[0-9]+: error: .{0,120}" | sort -u | head -20; fi'
