# Cloud workspace

One Linux checkout of the Institute's and portable coenttb's packages, for work across many repositories at once. Mac apps stay out of it.

    ./sync.sh          # clone or update everything in repos.txt, rewrite manifests to path dependencies, generate Package.swift

Run it before any `swift` command and after pulling. An edit in one checkout is then seen by everything above it. The rewritten manifests are marked skip-worktree, so they're never committed. Without them, a root path dependency conflicts with URL dependencies on the same package, and SwiftPM's search for those conflicts doesn't finish on this graph.

To really change a manifest: `./localize.py --restore`, edit, commit, then `./localize.py`.

## Working

1. Edit in `repos/<owner>/<name>`.
2. `swift build --target <Target>` from this folder: builds that target and what it needs, on the local copies. Each run costs about a minute before it compiles anything, so build several targets in one command with `--target` per batch rather than one by one. Give long commands a timeout over 10 minutes.
3. Commit in that repository and push to main. Attach a repository with `add_repo` before pushing to it or, if private, reading it: this runs without a prompt here. 23 attached at once worked; a cap above that is unknown. The git proxy allows 2 operations at once per repository. Never force-push. Never push to pointfreeco/TCA26.
4. Tests: public repositories get them from `ci.yml` after the push, so don't wait for it; read the results later. For a repository without CI, `swift test --package-path repos/<owner>/<name>`.

State what each green covers: this is Linux only. Apple-specific and Windows code isn't compiled here; `ci.yml` covers those.

## Results

Nobody can read a cloud session's transcript from outside, and it can't message back. Whatever matters goes in a file on main of this repository, or on the issue it belongs to. Never open personal data or `*.local.json`; test data is invented.

## On the Mac

The same build runs on Coen's Mac from a checkout of this repository, with `repos/` cloned from his real checkouts instead
of GitHub, so unpushed work is built too. Everything is in `mac/`:

    mac/sync.sh     # each clone = its checkout's HEAD plus uncommitted files; clones missing ones; localizes, generates
    mac/build.sh    # swift build --build-tests over everything; writes build.log and errors.txt
    mac/test-sync.sh  # checks sync.sh in a throwaway folder
    mac/loop.sh     # build, apply the mechanical repairs in the real checkouts (mac/fix.sh), build again, until green

While agents are editing checkouts, sync with `HEAD_ONLY=all mac/sync.sh` so only committed work is built, and don't run
`mac/loop.sh` or `mac/fix.sh`: they edit the checkouts. Fix in the checkouts, never in `repos/`: a sync overwrites it.
Build the whole ecosystem after every batch of changes, not only at the end: an incremental build takes minutes.
