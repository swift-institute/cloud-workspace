# Shared CI: job time limit and streamed test output (swift-institute/.github#660)

**Status, 12 Nov ~11:00 UTC.**

- The change is ready but not on main. The only blocker is access: a cloud session can't reach swift-institute/.github at all, because the platform refuses repository names that start with a dot, and Coen's admin permission doesn't change that.
- The shortest path is two commands on Coen's Mac, in a checkout of swift-institute/.github on main, shown below.
- The patch doesn't depend on unpublished work: planner b5e810c is already published. If the pin move is unwanted, drop `.institute-ci-pin` and `.institute-ci-planner` from the commit and replace each `${{ fromJSON(needs.plan.outputs.timeout-minutes) }}` with `40`. The stdbuf and `script` lines need no planner.

```bash
git am <cloud-workspace>/ci-timeout-660.patch
```

```bash
git push origin main
```

## Red lines crossed

- **verify-planner-pins.sh not run on the new pin.** It needs GraphQL, which cloud sessions block. Its checks were done by hand over REST. Follow-up: make the script use the REST asset list.
- **Streaming is a workaround.** It goes around SwiftPM's missing flush with stdbuf and a pty instead of fixing it at the source. Follow-up: an upstream SwiftPM patch, a flush after `print` in `SwiftTestCommand.swift`, after which the wrappers go.
- **The probe ran on a session branch of cloud-workspace**, not in a fleet repository. Follow-up: none; the probe workflow is already deleted from that branch.
- **No dispatched run of the patched workflow exists yet.** Follow-up: dispatch on swift-w3c-css, swift-iso-32000 and swift-sqlite once the patch is on main.
- **institute's own Quality · source is red at its pushed heads** (e4cc3be, 1b5e430, 60e45e4). It ran over its own limits for minimal type body (690/687), test function naming (48/45), compound identifier (212/211) and int public parameter (21/20), plus three swift-format nits, one of them mine: the import order in the Ratchet test. Windows release is red too, from swift-process failing to compile (`switch must be exhaustive`). The planner was still published from b5e810c, as from earlier red heads. Follow-up: fix those findings in institute, and swift-process on Windows.

Cloud session, 12 Nov 2026. Takes over from the Mac session stopped on 12 Nov. This file is the record because swift-institute/.github can't be attached to a cloud session: the platform refuses any repository whose name starts with a dot. From here, issue #660 can't be read or commented on, and nothing can be pushed to swift-institute/.github (git proxy: "not in this session's authorized repository set"). Copy this file to #660 as a comment.

## State

| Repository | Head on main (read back from the remote) | What |
|---|---|---|
| swift-institute/institute | `b5e810cfa5748cb2d5b27dbfe521c52eb43be9e6` | planner reads and emits `timeout-minutes` (Mac session; unchanged here) |
| swift-institute/institute release `ci-binaries` | asset `PIN-b5e810cfa5748cb2d5b27dbfe521c52eb43be9e6-43186494497` | **published here**: publish-planner run 43186494497, success |
| swift-institute/.github | `5af683bb12292ab47dd60d68d679b5ff381853d1` (unchanged) | **not pushed**: the change is `ci-timeout-660.patch` beside this file |

## What a session with access to swift-institute/.github must run

On Coen's Mac, or in a cloud session started with swift-institute/.github already selected (it can't be added later with add_repo):

```bash
cd <checkout of swift-institute/.github> && git checkout main && git pull --ff-only
```

```bash
git am <cloud-workspace>/ci-timeout-660.patch
```

```bash
bash .github/actions/institute-ci/verify-planner-pins.sh .institute-ci-pin .institute-ci-planner && git push origin main
```

The patch is based on `5af683b`. If main has moved, `git am` still applies unless the same lines changed. It is one commit: the workflow and the pin move together. The new workflow reads `needs.plan.outputs.timeout-minutes`, which only planner b5e810c emits, so the two must land in the same commit.

Then the proof, from that session:

```bash
gh workflow run ci.yml --repo swift-w3c/swift-w3c-css --ref main
```

```bash
gh workflow run ci.yml --repo swift-iso/swift-iso-32000 --ref main
```

```bash
gh workflow run ci.yml --repo swift-compositions/swift-sqlite --ref main
```

For each run, read back:

- conclusion success, with each platform named (Linux release, macOS, Windows; iOS simulator for swift-sqlite);
- the Plan step summary shows "Time limit per build and test job: 40 minutes";
- in the macOS and Linux release Test logs, test lines carry their own timestamps spread across the step, not one shared second at its end.

## Findings

**The time limit.** Every job in `swift-ci.yml` at `5af683b` already had a fixed `timeout-minutes` (45 for most legs, 30 for the SDK legs, 60 for iOS tests). The gap was not six hours but this:

- the limit was one number per job, in the workflow;
- a repository could not set its own;
- a job the limit stopped reads `cancelled`, the same word as a run someone cancelled by hand.

**Default 40, not 20.** Durations of healthy jobs, from green runs:

| Repository | Runs | Longest job |
|---|---|---|
| swift-w3c/swift-w3c-css | 43178596687, 43136398474 | Windows release, 10 and 11 min; macOS 7–8 |
| swift-iso/swift-iso-32000 | 42345206029, 42274624607 | Windows release, 11 and 14 min |
| swift-compositions/swift-sqlite | 42974734656, 42964261072, 42353522901, 42298554965 | iOS Simulator tests: 25.2, 18.4, 15.1, 19.3 min |

The Mac session also measured a 25.4-minute Windows release build. With a 20-minute limit, healthy jobs would be stopped. The planner's 40 (`Institute.CI.Timeout.default`) stands. A repository raises or lowers it with `timeout-minutes:` in its `.github/metadata.yaml`, a whole number from 1 to 360. Any other value refuses the plan, the same way a bad `platforms:` does.

**Why test output is buffered.** It isn't the workflow and it isn't `institute`: the Test steps run `swift test` directly. The cause is in SwiftPM:

- `swift test` passes the test process's output on with `print($0, terminator: "")`. That is `Sources/Commands/SwiftTestCommand.swift:935` in swiftlang/swift-package-manager at `dbcaa9b22ba83aa273a8652401f25b8b1efe5e3f`.
- When stdout is a pipe, as on a runner, C stdio holds what `print` writes until its buffer fills or the process exits.
- The test runner run by itself streams.

Shown on Linux here (Swift 6.4.2) and on GitHub runners (cloud-workspace branch `coenttb/charming-volta-ftybc4`, runs 43186766916 and 43187400177). In a probe of three tests that each sleep 10 seconds, plain `swift test` logged all its test lines in one second:

| Runner | Swift | Plain `swift test`: every test line at |
|---|---|---|
| macos-26 | 6.3.3 | 08:55:42 |
| windows-latest | 6.2.4 | 08:57:41 |
| swift:6.2 container | 6.2 | 09:00:11 |

**The fix in the patch.**

- **Linux release:** `stdbuf -oL swift test …`
- **macOS:** `TERM=dumb NO_COLOR=1 script -q /dev/null swift test … < /dev/null`. macOS has no stdbuf, and `/usr/bin/swift` is a protected shim that drops DYLD variables, so the test runs on a pseudo-terminal instead.

In the same probe, each line then landed when it was written, 10 seconds apart:

- swift:6.2 container: 09:00:11 → :21 → :31 → :41
- macos-26: 09:00:03 → :13 → :23 → :33

A failing test still exits 1 under both. The macOS lines are plain text with no escape codes, and `script` returns the child's exit status (shown with `exit 7`).

**Windows stays buffered.** Git Bash has neither stdbuf nor a pseudo-terminal. The time limit still stops a hung Windows job, but the hung test's name only appears once SwiftPM flushes. The real fix is upstream: flush after that `print` (or write through `swiftCommandState.outputStream` and flush it). That is an issue and patch for swiftlang/swift-package-manager. I didn't file it there, because it is outside the Institute; Coen decides whether to. The iOS simulator leg runs xcodebuild, not swift test, and was not examined.

**Plain words when the limit stops a job.** ci-ok gains the step "Jobs ended by the time limit":

- It reads the run's jobs (`actions: read`, which the generated caller grants).
- For each cancelled job that ran to within 30 seconds of the limit, it writes an error and a summary line: "<job> was stopped after N minutes by the 40-minute time limit. It did not finish, so it neither passed nor failed: the last line of its log is where it was when it was stopped. A repository whose healthy jobs need longer sets timeout-minutes: in its .github/metadata.yaml."
- It is `continue-on-error`, so the verdict stays Aggregate's.

## Proven / not proven

Proven:

- The published assets for b5e810c (Linux and macOS binaries and graphs) hash to the pinned rows; downloaded over REST and checked.
- The published Linux planner's `plan` emits `"timeout-minutes": "40"` with no key and `"75"` for `timeout-minutes: 75`. It refuses `0` and `20m` with "timeout-minutes in .github/metadata.yaml is '…'; it must be a whole number of minutes from 1 to 360."
- The streaming mechanism, on macos-26 and the swift:6.2 container, as above.
- actionlint shows nothing new; its only findings are the four pre-existing `xcode-27` label warnings.
- `verify-planner-pins-tests.sh` passes.
- `verify-planner-pins.sh` on the new pin couldn't finish here: it lists release assets with `gh release view`, which uses GraphQL, and GraphQL is blocked in cloud sessions. The same checks were done by hand over REST, and all pass.

Not proven:

- The patched `swift-ci.yml` itself: it isn't pushed, so no dispatched run exists.
- The ci-ok time-limit step, which has never run.
- The limit actually firing. This can be shown safely without breaking a real repository: dispatch on a repository whose `.github/metadata.yaml` sets `timeout-minutes: 1`. Its macOS build then runs past one minute and is stopped, which exercises GitHub's cancel and the ci-ok message. Revert the key afterwards. That needs a push to a fleet repository's metadata, so it was left for the session that pushes the patch.
- Windows streaming, which is not fixed.

All runtime evidence is from Linux x86_64 (this container), the swift:6.2 container, macos-26 and windows-latest, as named above.
