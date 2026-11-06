# Cloud workspace

One Linux checkout of the Institute's and portable coenttb's packages, for work across many repositories at once. Mac apps stay out of it.

    ./sync.sh          # clone or fast-forward everything in repos.txt, into repos/<owner>/<name>
    ./generate.py      # write Package.swift: every checkout as a path dependency

A path dependency at the root overrides that package's URL everywhere in the graph, so an edit in one checkout is seen by everything above it. No repository's own manifest changes.

## Working

1. Edit in `repos/<owner>/<name>`.
2. `swift build --target <Target>` from this folder: builds that target and what it needs, on the local copies.
3. Commit in that repository and push to main. Never force-push. Never push to pointfreeco/TCA26.
4. Tests: public repositories get them from `ci.yml` after the push, so don't wait for it; read the results later. For a repository without CI, `swift test --package-path repos/<owner>/<name>`, after its dependencies are pushed.

State what each green covers: this is Linux only. Apple-specific and Windows code isn't compiled here; `ci.yml` covers those.
