# #239 Linux lane: status

Plan: (1) re-pin swift-format in Institute.Source.Policy and adopt it through .github/.institute-ci-pin/.institute-ci-planner, with the concept rules wired into ci.yml and ceilings re-measured; (2) read CI on every Institute main, fix real failures and move colliding test suites; (3) test the seven private portable coenttb packages on Linux and close on coenttb/work#239.

Every green here is Linux x86_64, Swift 6.4.2. Apple and Windows code isn't compiled here; ci.yml judges those after the pushes.

## 1. Source gate re-pin: done, adopted

- Cause: GitHub's xcode-27 image 20261104.0337 carries Xcode 27.2 build 27B52, whose swift-format hashes to 475d31f4…; the pin recorded 27B48's d16e0788….
- `institute` 3a43c132b72118b045a4eeb002fcd2937e974414: pin 475d31f4… and 27B52; File.Path from File System instead of ISO 9945 Kernel File (POSIX); bundle test master list; swift-format findings. publish-planner run 42245057187.
- **Adopted from the Mac:** `swift-institute/.github` main 3409f30bbc645c5672c50ef3226037ea02cbb196 pins planner 326e729 from publish run 42249866520. Canary: adoptable, 0 regressions on all 4 canary repositories, Mac only. A swift-format re-pin can't pass a canary run on one Xcode, so `institute` c84206b adds `--candidate-xcode`.
- Fleet CI only re-runs on a push or a re-run, so the red results from before adoption don't clear on their own: failed jobs re-run in 82 repositories whose latest main run failed Quality · source; the rest get new runs from the step 4 pushes.

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

Second read, 19:00 UTC: 338 pass, 69 fail, 41 no checks, 11 running. Every red is Quality · source (24 repositories) or advisory Embedded (22); no build or test job fails.
- 14 ran the old pin (institute 8cf32d7) before adoption: failed jobs re-run.
- swift-stores: artifact upload failed (ENOTFOUND), re-run.
- swift-witnesses: UNMEASURED, a duplicate finding. `macro expansion short name` read `"\n\n    "` as two key paths to a type `n`. Rule fixed at its source, institute 79d10ad (two new tests that fail without it); CI runs the published runner, so the fleet gets it at the next runner publish and re-pin. Until then swift-witnesses moves that literal out of `expansion` (commit pending its test build in step 4).
- swift-format findings fixed and pushed, each linted clean locally: international-system-of-units d76e3dc, rfc-6066 4fb92c0 (`try!` with a reason takes `swift-format-ignore: NeverUseForceTry`), linter-rules 4143528, package-graph 8c474cc, swift-institute.org 53920ce, iso-21320 61f9fb6 (its test file goes with its suite move), github-standard b6971f3, rss-standard fddce42.
- swift-linter-rules' `comment` message had no citation, and `diagnostic message format` takes no suppression. Coordinator's decision (the peer session): cite a research document recording the decision as cd45d05 states it, with no made-up rule ID. A package repository's generated shape allowlist admits no `Research/`, so the document is `Research/no-source-comments.md` in swift-institute/institute (e3aefc6). swift-linter-rules e1349f5 cites it; the 3a43c13 runner reports nothing on the file.

Third read, about 21:30 UTC: 361 pass, 47 fail, 40 no checks, 14 running. Embedded (advisory) 25; Quality · source 5 failed, 16 cancelled.
- 16 Quality · source runs from 4 Nov were cancelled and never re-run: re-run under the current pin.
- Network failures re-run: rfc-5234 (macOS: harden-runner download), iso-8825 (ci-binaries download), swift-source (artifact upload). ecma-376's Windows build crashed inside SwiftPM ("error: fatalError"): re-run once, not pursued.
- rfc-6066 was UNMEASURED, not just format: swift-linter can't read a target dependency written as a static-var alias on Target.Dependency ("unhandled target dependency '.rfc8446'"). Seven manifests use that shape; all now write the dependency out: rfc-1034 ab95c50, rfc-3596 1d981e3, rfc-6066 6256828, rfc-6455 6605236, rfc-6891 625b498, rfc-7301 c9fdd8c, rfc-8200 3c6dec3. For each, `swift package dump-package` gives the same targets, settings, products and dependencies, and the 3a43c13 runner exits 0 on it.
- international-system-of-units fa0c1c7: swiftlint's shorthand_operator and force_try are errors; `+=` and a swiftlint directive. Target builds on Linux.
- swift-manifests 08b9b20: two test files' imports sorted.

## 4. Suite-name collisions: in progress

- Each `extension T { @Suite … }` where T isn't declared in the test module moves to a namespace `` `T Tests` `` the test module declares (an existing type of that name is reused); references are rewritten, then changed files are formatted with swift-format where the committed file is already stable under it. `compound suite name` accepts the shape.
- `institute` a41bfd4 + 29b5e53: 149 suites; every test target builds and passes on Linux.
- The rest: 146 repositories. Each one's test targets must build on Linux before it's committed and pushed; the tests themselves run in ci.yml.
- **Build route.** The shared root workspace can't build other packages' test targets: SwiftPM builds only the root package's tests. What works is one shared `--scratch-path` for every package's `swift build --package-path <repo> --build-tests`: built dependencies are reused across packages. swift-witness's tests built in 4 s after swift-version's, against about 5 minutes each from a fresh scratch. Used for the last 100 repositories.
- Progress: 60 of the last 100 built when the disk allowance ran out (swift-uri hit it; to rebuild). institute's own 6.9G .build was removed to free space. Before that, 54 of the last 100 built; 6 failed, all on Linux. effects, email, email-html, stores: the suites test trait-gated targets that a default-trait build leaves out, so the original fails the same way; to rebuild with all traits. github: the moved suites used the old extension's nested types bare (`Client`, `Request`, `Page`); typealiases added in each namespace. pdf-render: the namespace already existed in another file as a suite; reused. cpu and bifunctor were done earlier.
- No lint rule: whether T is declared in the test module is a question across files, which a per-file rule can't answer.

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

## Follow-ups

- `blocking call in async` reads an enum case pattern named `wait` as a call, and takes no suppression.
- Windows' Path literal conformance: File System Core re-exports Kernel File on Windows (swift-file-system d67e77a), and institute's Source Policy imports File System (bfc0752). Windows not compiled here.
