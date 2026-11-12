# Source lint on Linux, and `institute lint` (swift-institute/institute#287)

Cloud session, 12 Nov 2026. Steps 1 and 3 are on institute main, step 2 is a patch beside this file, step 4 is untouched.

**Not done: the comparison with the macOS `quality-report` artifacts.** This session could not download any of them. Its network policy refuses GitHub's artifact storage host (`productionresultssa5.blob.core.windows.net`, 403 at the proxy), and attaching the four packages for API access was refused by the permission check. What could be compared from here is institute itself, through its macOS job logs: see the table. One command on a machine with `gh` finishes it:

```bash
./lint-equality.sh
```

## Heads (read back from the remotes)

| Repository | Commit | What |
|---|---|---|
| swift-institute/institute | `2da5e30ffe3666a41c1779ba7ea8dca8e45e0bcd` | institute's own lint findings that kept `Quality · source` red since b5e810c |
| swift-institute/institute | `d1f2ca2014d9d4bc42d3c7223ab4dbb483aa0f4b` | steps 1 and 3 |
| swift-compositions/swift-process | `6d32f129a656785c4dad9b6007f1d5f69cd92805` | the Windows build of everything that depends on it, institute included |
| swift-institute/institute release `ci-binaries` | TBD-PIN-ASSET | planner published from d1f2ca2, unpinned |

## The command a Linux session runs

In a package directory of a checkout, with this repository checked out beside it as on a cloud machine:

```bash
/home/user/cloud-workspace/lint.sh
```

With `--fix` it first rewrites what swift-format can repair. Exit 0 means `Quality · source` would pass, 1 that it would fail, 2 that the lint could not be completed. `lint.sh` downloads the planner published from d1f2ca2 once, checks its SHA-256, and runs `institute lint`. On a Mac, `institute lint` is the same command once the installed planner is at d1f2ca2 or later.

## Step 1: where each Linux tool comes from

| Tool | Source | SHA-256 |
|---|---|---|
| swift-format | the Swift toolchain on the machine: `swift-6.4.2-RELEASE` for ubuntu24.04 from swift.org, found on `PATH`, run where it is | `50a1cb95ded4d8f4ac934649fe2b61b5ccabddace84848b9ffda0b4d9f915883` |
| SwiftLint 0.65.1 | `swiftlint` in `swiftlint_linux_amd64.zip` of its release (archive `caeed6f4a679c35539ffaf124f6c4ab4a8416917f7d8796279dc52b74026059d`) | `3384e7a44d6f2b6f9820404111e2a777b08ba99de087979ed40f6832efc073f5` |
| institute-linter-runner | the Linux build of the pinned revision 2d6a4f5, `ci-binaries` release, publish-planner run 42534160338 | `0f2cae97638b9f9d23d5acd8b8c26696fbb604a57dc6fb3bdd982e7d86bc3fb5` |

- **swift-format is the toolchain already on the machine, not a download.** It is accepted only when it hashes to the pin. I checked the pin against swift.org's own archive (`swift-6.4.2-RELEASE-ubuntu24.04.tar.gz`, SHA-256 `2e9ebec040ad459dd89a6d093a02d8314939135104850fae4d5c0f174fb3ba8c`): its `usr/bin/swift-format` has that digest. It can't be copied out as the Xcode one is, because it loads the toolchain's runtime from beside itself. A download would be 1 GB per cold cache.
- **The pin is one build.** Another Ubuntu release, another architecture or Swift 6.4.3 has another digest and is refused with a message naming both digests. Step 2's job therefore names `ubuntu-24.04` and Swift `6.4.2` exactly.
- **SwiftLint is the dynamic binary, not `swiftlint-static`.** `statement_position` and the custom rules' match kinds need SourceKit, which the static binary lacks. It loads SourceKit from the toolchain on `PATH`; without one it stops with status 132 and the report is unmeasured, never clean.
- **The runner needs the toolchain's runtime.** It is run with an environment of its own, so the planner adds `LD_LIBRARY_PATH=<toolchain>/usr/lib/swift/linux`, derived from where the pinned swift-format is.
- `--xcode-application` is optional. Without it macOS uses the pinned `/Applications/Xcode_27.2.app`. Anywhere but macOS it is refused.

## Equality

Linux: this cloud machine, Ubuntu 24.04, Swift 6.4.2, release build of d1f2ca2. macOS: the `Quality · source` job of that commit's CI run, planner b5e810c, Xcode 27.2. Both run linter runner 2d6a4f5 and SwiftLint 0.65.1.

| Repository (layer) | Commit | Linux report | macOS report | Result |
|---|---|---|---|---|
| swift-institute/institute (control) | `60e45e4` | complete, 1992 findings: swift-format 4, swift-linter 1696, SwiftLint 292; 4 rules over limit | run 43208715474, log: 1992 findings, 50 printed, 4 rules over limit | **equal as far as the log shows**: same total, the 50 printed findings identical and in the same order (all 4 swift-format findings and 46 swift-linter ones), the same 4 counts over limit. 1942 findings not compared |
| swift-institute/institute (control) | `d1f2ca2` | complete, 1971 findings: swift-format 0, swift-linter 1680, SwiftLint 291; exit 0 | run 43312055073, log: 1971 findings, 50 printed, exit 0 | **equal as far as the log shows**: same total, the 50 printed findings identical and in the same order, same exit status. 1921 findings not compared |
| swift-atoms/swift-geometry (atoms) | `65618d9` | complete, 133: swift-linter 133; exit 0 | not reachable | not compared |
| swift-molecules/swift-raster (molecules) | `7bf565c` | complete, 22: SwiftLint 22; exit 0 | not reachable | not compared |
| swift-standards/swift-iso-639 (standards) | `d0f9319` | complete, 1: swift-linter 1; 1 rule over limit, exit 1 | not reachable | not compared |
| swift-compositions/swift-picture (compositions) | `272df60` | complete, 0; exit 0 | not reachable | not compared |
| swift-compositions/swift-motion (compositions) | `bb374ca` | complete, 34: swift-format 2, swift-linter 19, SwiftLint 13; 2 rules over limit, exit 1 | not reachable | not compared |

- Each Linux report's fingerprint is in `lint-equality/`: every finding in full, and a SHA-256 of every other section, with the checkout root and the tool profile set aside. `lint-equality.py compare` names each differing finding.
- **No difference was found** in what could be compared. That is 100 findings and two totals of one repository, not the five packages asked for.
- **swift-format versions.** Xcode 27.2's swift-format calls itself `main` (27B52); Linux's is 6.4.2. I could not show they are the same source. Their findings agreed on institute at both commits: 4 of 4 at 60e45e4 across 747 files, and none at d1f2ca2 across 756.
- **Lint of record.** I recommend the platform CI runs on: macOS until step 2 lands, Linux after. If the two ever disagree, CI's verdict stands and the disagreement is a defect to pin down, not a second opinion.

## CI of institute at d1f2ca2 (run 43312055073)

TBD-CI

## Step 2, prepared: `lint-287-step2.patch`

TBD-STEP2

## What is left

- **The equality check for the five packages**: `./lint-equality.sh` on a machine with `gh`.
- **Step 2**: apply the patch, in the order its section gives.
- **Step 4**: untouched.
- `Institute.CI.Plan`'s comment on `packageWorkLegs` still says `source` needs a macOS runner. It is true until step 2 lands.
- `institute install` is macOS only. A Linux session gets the planner through `lint.sh`.
- swift-compositions/swift-motion at `bb374ca` and swift-standards/swift-iso-639 at `d0f9319` fail the lint on Linux (2 errors and 2 rules over limit; 1 rule over limit). I changed neither.

## Red lines crossed

- **swift-compositions/swift-process was pushed without a local compile.** The change is three `case` patterns under `#if os(Windows)`. Follow-up: its Windows CI job is the check.
- **The retired-surface test lost `lint`.** `institute lint` was a retired verb the CLI tests refused; #287 asks for it again, so the test now refuses `lint run` instead. Follow-up: none, unless the old retirement had a reason #287 did not weigh.
- **Institute's own lint was made green by changing institute's code**, not only by adding the feature: `Deviation.timeoutMinutes` is now `Deviation.timeout`, `Institute.CI.Timeout.init(minutes:)` is no longer public, two test names changed. No rule or limit was touched. Follow-up: none.
