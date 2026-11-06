# Cloud workspace

One Linux checkout of the Institute's and portable coenttb's packages, for work across many repositories at once. Mac apps stay out of it.

    ./sync.sh          # clone or update everything in repos.txt, rewrite manifests to path dependencies, generate Package.swift

Run it before any `swift` command and after pulling. An edit in one checkout is then seen by everything above it. The rewritten manifests are marked skip-worktree, so they're never committed. Without them, a root path dependency conflicts with URL dependencies on the same package, and SwiftPM's search for those conflicts doesn't finish on this graph.

To really change a manifest: `./localize.py --restore`, edit, commit, then `./localize.py`.

## Working

1. Edit in `repos/<owner>/<name>`.
2. `swift build --target <Target>` from this folder: builds that target and what it needs, on the local copies. Each run costs about a minute before it compiles anything, so build several targets in one command with `--target` per batch rather than one by one. Give long commands a timeout over 10 minutes.
3. Commit in that repository and push to main. A repository has to be attached to the session before you can push to it or read it if private: the proxy says so otherwise. Never force-push. Never push to pointfreeco/TCA26.
4. Tests: public repositories get them from `ci.yml` after the push, so don't wait for it; read the results later. For a repository without CI, `swift test --package-path repos/<owner>/<name>`.

State what each green covers: this is Linux only. Apple-specific and Windows code isn't compiled here; `ci.yml` covers those.
