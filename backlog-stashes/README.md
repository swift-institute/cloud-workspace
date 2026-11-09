# Half-done fixes from the 9 Nov Mac run

The fix run was stopped while these three agents were mid-edit. Their work was never built or tested. On the Mac it is
`stash@{0}` "cut-off fix run 9 Nov" in each checkout; here it is a patch on the commit it was made on.

| Repository | Issues | Base commit |
|---|---|---|
| swift-iso/swift-iso-9945 | #92, #93 | 65c3963c12b59ff937dc8104340857d0fbcef24f |
| swift-linux-foundation/swift-linux-standard | #18, #15 | cee3380e7a3c4c728fb648d3436a4a30c2127daa |
| swift-standards/swift-css-standard | #8 | cd2dde1b68ad2f8042a123217e9904458a9d4e42 |

Use one as a starting point (`git apply` on its base, then check it against the issue) or redo the fix from scratch.
