# Cloud workspace

One Linux checkout of the Institute's and portable coenttb's packages, for work across many repositories at once. Mac apps stay out of it.

    ./sync.sh          # clone or fast-forward everything in repos.txt, into repos/<owner>/<name>
    ./localize.py      # rewrite each checkout's manifest to path dependencies, marked skip-worktree so it is never committed
    ./generate.py      # write Package.swift: every checkout as a path dependency

Run all three, in this order, before any `swift` command. An edit in one checkout is then seen by everything above it. Without `localize.py`, a root path dependency conflicts with URL dependencies on the same package, and SwiftPM's search for those conflicts doesn't finish on this graph.

To really change a manifest: `./localize.py --restore`, edit, commit, then `./localize.py`.

## Working

1. Edit in `repos/<owner>/<name>`.
2. `swift build --target <Target>` from this folder: builds that target and what it needs, on the local copies.
3. Commit in that repository and push to main. Never force-push. Never push to pointfreeco/TCA26.
4. Tests: public repositories get them from `ci.yml` after the push, so don't wait for it; read the results later. For a repository without CI, `swift test --package-path repos/<owner>/<name>`.

State what each green covers: this is Linux only. Apple-specific and Windows code isn't compiled here; `ci.yml` covers those.
