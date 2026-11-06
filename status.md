# #239 Linux lane: status

Plan: (1) re-pin swift-format in Institute.Source.Policy and adopt it through .github/.institute-ci-pin/.institute-ci-planner, with the concept rules wired into ci.yml and ceilings re-measured; (2) read CI on every Institute main, fix real failures and move colliding test suites; (3) test the seven private portable coenttb packages on Linux and close on coenttb/work#239.

Every green here is Linux x86_64, Swift 6.4.2. Apple and Windows code isn't compiled here; ci.yml judges those after the pushes.

## 1. Source gate re-pin: committed and published; adoption waits for the Mac

- Cause: GitHub's xcode-27 image 20261104.0337 carries Xcode 27.2 build 27B52, whose swift-format hashes to 475d31f4…; the pin recorded 27B48's d16e0788….
- `institute` 3a43c132b72118b045a4eeb002fcd2937e974414: pin 475d31f4… and 27B52; institute targets take File.Path from File System instead of ISO 9945 Kernel File, which doesn't build on Windows (institute's Windows build has been red since 53a421e); bundle test master list; swift-format findings. publish-planner run 42245057187: success.
- **Blocked here: adoption.** `swift-institute/.github` can't be attached to a cloud session (names starting with `.` are refused), and `institute planner canary` needs Xcode. The adoption to run is in the "For the Mac" section below.

## 2. Concept rules in ci.yml (decision 25): committed and published

- `institute` 326e72947c607e69f8bdd2bba172fb7af477e567: runner 3a43c13 (macos-arm64 e3629c0a…); profiles add `raw concept`, `concept parallel`, and `blocking call in async` (new in swift-linter-rules; the engine requires the profile to equal the runner's inventory). Inventories 140/143/136 checked equal against the runner. publish-planner run 42249866520.
- In CI, `raw concept` is a warning and warnings never fail the gate: the concept rules report there; the ratchet stays `coenttb lint`'s.
- Ceilings reset once from a real measure (the 3a43c13 runner over 448 Institute + 7 private packages, on Linux). They rose because the widened rule sees more: github-standard 6, iso-32000 4, w3c-css 4, iso-14496-22 3, ecma-424 2, iso-5962 2, manifest 2, rfc-5322 2, w3c-epub 2, rfc-3986 1. swift-licensing falls to 0. Apps and swift-processes unchanged (not here, not measured).
- The institute's 27 unlisted hits: suppressed with reasons naming the types looked at (commit message lists them).
- `blocking call in async`: one finding across the fleet, a false positive on a `.wait` case pattern; swift-cache 33b72cf renames the case (24 tests pass).

## 3. CI read and fixes

Read at 15:15 UTC: 299 pass, 107 fail, 42 no checks. Quality · source 67 (63 the hash), Embedded 20, Windows 7, macOS 2, Linux release 2.

Fixed and pushed:
- swift-path e66bf99: Path's Codable out of Embedded.
- swift-manifest d5ec249: test uses Path(validating:) (Windows). 2 tests pass.
- swift-windows-32 347f318: the raw-string test was wrong (`\#(` ate the separator).
- swift-linter 689d936: documents are `/`-separated on every platform; empty-variable test not on Windows. 173 tests pass.
- swift-package-manager 748df8f: checkout and workspace-state paths joined by component (Windows); `Materialized.source` returns File.Path. 52 tests pass.
- swift-svg 1f77ea7: dropped the dependency on swift-test-application, which no longer clones.
- swift-cache 33b72cf: see step 2.
- swift-dependencies: Windows crash was a 5 Nov run; re-run.

Not fixed, by decision: Embedded failures other than swift-path's are advisory (`ci-ok` passes without them) and structural (swift-syntax's precondition, key paths, Foundation, Task). swift-witnesses' source failure is a 5 Nov run, before the re-pin.

Not yet: a second read after these pushes.

## 4. Suite-name collisions: not started

1,344 suite-bearing `extension T {}` blocks in 169 repositories. `compound suite name` already accepts a top-level `` `X Tests` `` suite, so the move lints clean, but moving a suite out of `extension T` breaks unqualified lookups of T's members inside it.

## 5. Private portable packages: all seven pass on Linux

| Package | Tests | Change |
|---|---|---|
| swift-licensing | 33 pass, License.Email's included | bce5c16: License Keychain only where Security exists |
| footprint | 21 pass | 75873d9: FoundationNetworking where it exists |
| swift-app-launch | 42 pass | b6c9cad: FoundationNetworking/FoundationXML |
| swift-agent-sessions | 9 pass | none |
| swift-impact | 27 pass | none |
| swift-interface | 55 pass | none |
| swift-youtube | 4 pass | none |

No Docker build was made, so the licensing deploy's own condition isn't met by this.

## For the Mac

The new pin is the swift-format of Xcode 27.2 build 27B52. The canary runs planners with the Mac's own Xcode, whose 27B48 swift-format hashes to d16e0788…, so the candidate will probably refuse until the Mac has 27B52 (an untested inference from the source, not run). Then, after publish-planner run 42249866520 succeeds:

    institute planner canary --publish-run 42249866520
    institute planner adopt --publish-run 42249866520 --evidence-path <evidence.json the canary wrote> --github-checkout <path to swift-institute/.github>
    git -C <path to swift-institute/.github> push

## Follow-ups

- `blocking call in async` reads an enum case pattern named `wait` as a call, and takes no suppression.
- Institute targets that write File.Path literals need Windows' literal conformance (Windows 32 Kernel File); read after the Windows build.
