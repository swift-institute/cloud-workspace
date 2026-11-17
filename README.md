# Cloud workspace

One Linux checkout of the Swift Institute's packages and the portable coenttb packages, for work that spans many
repositories at once. Apps that need macOS stay out of it.

All of it is built as one SwiftPM package whose dependencies are the local checkouts, so an edit in one checkout is
seen by everything that depends on it before anything is pushed.

## Sync

    ./sync.sh

Clones or fast-forwards every repository in `repos.txt` into `repos/<owner>/<name>`, rewrites each manifest to path
dependencies (`localize.py`) and generates the root `Package.swift` (`generate.py`). Run it before any `swift` command
and after pulling.

- `repos.txt` must name every Institute package that any listed manifest depends on. A missing one is reached both by
  URL and by path, and SwiftPM's graph loading does not finish.
- `private-repos.txt` (git-ignored, one `owner/name` per line) lists repositories that need access. `sync.sh` clones
  them with the rest. Attach each one to the session first (below).
- The rewritten manifests are marked skip-worktree, so they are never committed. Without them a root path dependency
  conflicts with URL dependencies on the same package, and SwiftPM's search for those conflicts does not finish.
- To really change a manifest: `./localize.py --restore`, edit, commit, then `./localize.py`. `sync.sh` restores the
  manifests before it pulls, so an uncommitted manifest edit is lost.

## Build

Edit in `repos/<owner>/<name>`, then from this folder:

    ./build.sh <Target> ...   # those targets and what they need, on the local copies, without linking
    ./build.sh                # the whole ecosystem with tests: once, right before each push

Each run costs about a minute before it compiles anything, so name every changed module and its dependents in one
command. Give long commands a long timeout. `--target` and `--build-tests` can't be combined: a test target named
with `--target` is compiled, not linked.

`build.sh` sets what this machine needs. Changing any of these flags recompiles everything.

- No debug info (`-Xswiftc -gnone -Xcc -g0`): with it the test libraries filled the disk.
- lld as the linker (`-Xswiftc -use-ld=lld`): gold ran out of memory on the big test libraries.
- `--disable-dead-strip`: with lld, dead stripping drops the metadata macro plugins need.
- `-j 3`.

A whole run can still grow swift-build itself until it is killed for memory (exit 137). Run it again: it resumes.

## Lint

In a package's folder:

    ../../../lint.sh          # findings, then the outcome
    ../../../lint.sh --fix    # first let swift-format repair what it can

Exit 0 means CI's `Quality · source` would pass, 1 that it would fail, 2 that the lint could not be completed. It is
the same lint as CI's, which runs on `ubuntu-24.04` with Swift 6.4.2. CI's run is the one that counts. On a Mac, run
`institute lint` instead.

`lint.sh` downloads the published `institute` planner once from swift-institute/institute's `ci-binaries` release,
checks its SHA-256 and keeps it under `~/.cache/institute`. Its two lines, `REVISION` and `DIGEST`, move together with
swift-institute/.github: `REVISION` is that repository's `.institute-ci-pin`, `DIGEST` the `linux-x86_64` row for that
revision in its `.institute-ci-planner`.

The planner fetches the lint's tools, each pinned by digest:

- swift-format is the one in the Swift 6.4.2 toolchain for ubuntu24.04 from swift.org, found on `PATH` and run where it
  is (it loads the toolchain's runtime from beside itself). Any other build, from another Ubuntu release, architecture
  or Swift release, has another digest and is refused with a message naming both.
- SwiftLint is the dynamic Linux binary, not `swiftlint-static`: some rules need SourceKit, which it loads from the
  toolchain on `PATH`. Without one it stops and the report is unmeasured, never clean.
- The linter runner is the Linux build of the pinned revision. The planner puts the toolchain's runtime on its loader
  path.

In a checkout whose manifest is localized, `lint.sh` lints the committed manifest and puts the rewrite back.

## Push

Commit in the package's repository and push to main. Never force-push.

Attach a repository with `add_repo` before pushing to it, or before reading it if it is private.
`.claude/settings.json` lets that run without a prompt. The git proxy allows two operations at once per repository.

Public repositories get their tests from `ci.yml` after the push; read the results later instead of waiting. For a
repository without CI, `swift test --package-path repos/<owner>/<name>`.

Every green here is Linux only. Apple-specific and Windows code isn't compiled here; `ci.yml` covers those. Say so
when reporting a result.

## Results

A cloud session's transcript can't be read from outside, and the session can't message back. Whatever matters goes on
the GitHub issue it belongs to. Never open personal data or `*.local.json`; test data is invented.

`ratchet.py` regenerates the lint limits in institute; `lint-equality.sh` and `lint-equality.py` compare a Linux lint
report with CI's macOS `quality-report` artifact. Read each script's header before using it.

## On a Mac

The same build runs on a Mac from a checkout of this repository, with `repos/` cloned from local checkouts instead of
GitHub, so unpushed work is built too. Everything is in `mac/`:

    mac/sync.sh       # each clone = its checkout's HEAD plus uncommitted files; clones missing ones; localizes, generates
    mac/build.sh      # swift build --build-tests over everything, or `mac/build.sh <Target> ...` for some; no debug info
    mac/test-sync.sh  # checks sync.sh in a throwaway folder
    mac/loop.sh       # build, apply the mechanical repairs in the real checkouts (mac/fix.sh), build again, until green

While agents are editing checkouts, sync with `HEAD_ONLY=all mac/sync.sh` so only committed work is built, and don't
run `mac/loop.sh` or `mac/fix.sh`: they edit the checkouts. Fix in the checkouts, never in `repos/`: a sync overwrites
it. Build the whole ecosystem after every batch of changes, not only at the end.
