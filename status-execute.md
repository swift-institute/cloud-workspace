# Execute: rule fixes, structure, semantic pass (coenttb/work#242)

Linux x86_64, Swift 6.4.2, 7 Nov. Brief: `BRIEF-execute.md`. Counts: `overnight/execute-lint.json` (runner built from institute d08bbc5, 439 public repositories; private packages not linted, `private-repos.txt` not created).

## Done

| Step | Repository | SHA | What |
|---|---|---|---|
| housekeeping | cloud-workspace | 7e8e5ba | 9 archived molecules out of `repos.txt`; no other checkout names them |
| 1 rules | swift-linter-rules | b124844 | `blocking call in async` `wait` case (#241 item 2); removed `inlinable internal access`, `usable from inline internal import` |
| 1 rules | institute | 3e33185 | removed `fully qualified error in typed throws`, `safe attribute undocumented`, `generic throws missing never`; `existential throws` merged into `untyped throws` |
| 1 rules | institute | 8354283 | `compound suite name` accepts #239's layout |
| 1 rules | institute | 7f5484e | 8 rules skip `Tests/` (raw value access, minimal type body, namespace adoption typealias, typealiased namespace bridge, ad hoc box class, frozen tower type, single type namespace, for loop in result builder) |
| 1 rules | institute | 10f53f6 | `unchecked call site` (own constants, instance methods), `tagged unchecked with typed alternative` (literals only) |
| 1 rules | institute | a9c0302 | `compound identifier` witnesses, `compound type name` local/CodingKeys, `single type per file` private, `unification typealias` private/local, `try optional` in `defer` |
| 1 rules | institute | d08bbc5 | `int public parameter` witnesses and `#line`, `canimport conditional` nested in `#if os` |
| 1 ratchet | institute | 2a07c96 | 3,615 limits, 32,421 findings (was 4,038 / 40,371) |
| 1 rules | institute | b50d560 | `do throws for typed catch` skips pattern catches and catches that never read `error`; `hoisted error in public throws` reports only public/open declarations (incl. `public extension` members), not `do`, closures or non-public API. Second session. |
| 1 rules | institute | 574f43b, 7d18cd8, c7f4dfc | `unknown default` only over enums declared in the file; `closure typed throws annotation` only for callees taking `throws(E)` closures (in-file or map/flatMap/compactMap); `bool public parameter` skips memberwise parameters stored as the same-named property; `extension file naming` ignores suppression-only where clauses. Narrowing only: no policy list or runner change needed. |
| 1 rules | institute | c1c5781, c5194d4, 0b143d9, 93f047e, e7af0b9 | `path name grammar` leaves a file's declared leaf type name to `compound type name`; `counter loop iteration` skips triangular and span loops (detect and repair); `untyped throws` admits Codable container, Decoder and macro witnesses; `fatal error outside tests` skips unavailable declarations and `* Test Support` targets; `file name nested path` strips backticks and skips `__`-hoisted types. Narrowing only. |
| 1 rules | institute | 3b05b34, f574265, 80335c3, 658dd56 | `count minus one` no longer reports ordering lookahead guards (`i + 1 < n`; `==` still reported); `trait consistency` treats `.define(X, .when(traits:))` as that trait's guard; `test target naming` admits Integration/Conformance/Performance suites; `module selector spelling`'s repair writes `M::M.Name` when the file shows a same-named type. Narrowing only. |
| 1 rules | institute | 33ab31c, 9ae2e5c, 5db53be | `bitpattern rawvalue chain` only when the argument is a `.rawValue` access; `string utf8 scanning` skips `unicodeScalars` writes; `type transform placement` skips executor witnesses. Narrowing only. |
| 1 rules | swift-linter-rules | fce317c, aee92a0 | `undeclared module import` skips `Fixtures/` sources; its controls get a test (fails without the fix). Narrowing only. |
| 2 pilot | swift-algebra | bc520ef, fa2521f | absorbs swift-symmetry-algebra behind trait `Symmetry` |
| 2 pilot | swift-symmetry-dimension | e26e210, e4d8542 | uses swift-algebra with `Symmetry` |

Every rule fix has a control or test that fails on the old rule (shown by reverting and running). institute and swift-linter-rules `swift test` pass on Linux.

**Publish wanted:** institute 2a07c96 with swift-linter-rules b124844. The adoption must also drop the 6 removed rule ids from `Institute.Source.Policy+linterRules.swift` (left pinned to the published runner).

**Archive wanted (Coen):** swift-molecules/swift-symmetry-algebra now has no consumer in the workspace.

Pilot CI was red on README-162 and import order (macOS-only checks); fixed in fa2521f and e4d8542. Before each push: README check and swift-format with the Institute's rules.

Not changed, by decision: `existential parameter` (its tests deliberately flag `[any P]` with a parameter-pack suggestion and witness shapes without a visible conformance); `exported import` / `architecture import boundary` (their tests pin the exact `exports.swift` name: rename files instead), `throwing wrapper init` (its test pins `self.init` delegation as a forward).

## Findings by rule, before (40,371, institute 2ac3965) → now (32,421)

raw value access 2,828→1,343 · minimal type body 4,944→3,463 · fully qualified error 1,429→0 · unchecked call site 760→239 · compound suite name 5,108→4,730 · namespace adoption typealias 845→606 · typealiased namespace bridge 712→474 · compound type name 1,134→925 · tagged unchecked 198→0 · int public parameter 1,665→1,493 · existential throws 157→0 · try optional 553→415 · safe attribute undocumented 133→0 · canimport conditional 41→0 · target import edge 517→5 (fixed by others before this session).

## Closing

Second session, 7 Nov, stopped as its context ran low. Linux x86_64, Swift 6.4.2.

- **Rules this session:** 22 narrowed in institute (b50d560 … 5db53be) and 1 in swift-linter-rules (fce317c, aee92a0); each has a control or test shown failing on the old rule, institute and swift-linter-rules `swift test` pass, swift-format clean with the policy configuration. No rule removed or renamed, so the source-policy list and pinned digests are unchanged. **Publish wanted:** institute main with swift-linter-rules aee92a0 (narrowings only).
- **Findings:** not re-counted this session; the ratchet stays at 2a07c96 (counts can only fall). Regenerate with `./ratchet.py` after the next fleet lint.
- **Types and wrappers:** unchanged, 12,308 and 1,806.
- **Not changed, by decision:** `existential parameter` (tests pin `[any P]` and conformance-less witness shapes deliberately); `extension file naming`'s foreign-type case and `closure typed throws`'s cross-file callees need a package type index the runner lacks.
- **Remains, in order:** the rest of `audit/rules-table.md` verdict `fix` (next: `result wrapper for rethrows shim`, `foundation import`, `configuration before content`, `manifest naming grammar`, `extension noncopyable constraint`, `optionset shell pattern`, `tagged extension public init`, `macro expansion short name`, `unlabeled lifecycle closure`, `unsafe storage visibility`, `architecture foundation type`, `unchecked sendable noncopyable`, `raw concept`, `tag suffix`, `property named flags`, `phantom suppression`, `apache license`, `ad hoc box class`, `for loop in result builder`, `comment in source`'s repair); the 8 new rules; Core renames (37 + 21); the 11 atom→molecule edges; unused dependencies; the generated root test package; the semantic pass; remaining lint. The two `target import edge` findings (swift-environment, swift-pdf-standard) still need dependency edges.
- **Tooling note:** the swift-format configuration is generated from `Institute.Source.Policy+swiftFormat.swift` into `/home/user/tools/swift-format.json` (not in the repository; a new container must regenerate it).

## Findings session (BRIEF-findings.md), 7 Nov

Linux x86_64, Swift 6.4.2. Runner built in release from institute main 9205733 (`/home/user/tools/runner-main`; a new container must rebuild it and regenerate `/home/user/tools/swift-format.json`).

- **Baseline:** one lint of 438 packages: **30,436 findings** (`overnight/findings-start.json`).
- **Batch 1, `minimal type body`, by the runner's repair:** 116 files changed. On the 49 packages it touched, the rule went from 2,179 to 1,738 findings: **441 fixed**, so 30,436 → about 29,995 (1.4%). The repair can't fix the remaining 1,738. They wait for hand fixes or the semantic pass.
  - **Committed locally, not pushed:** in 44 package repositories, each with the message "repair applied; root and test builds not yet run". **Unverified:** neither the root build nor the test builds have run on the final state.
  - **Backed up:** as patches on branch `findings-wip` (`wip/<owner>__<name>/`). To restore, `git am` each folder onto that repository's origin/main.
  - **Reverted, because the repair broke them:**
    - All of swift-tree-column, swift-tree-keyed and swift-tree-n: `package` members were moved into extensions of an internal type, which doesn't compile.
    - swift-rfc-4648 `RFC_4648.Strictness.swift` and swift-iso-14496-22 `HeadTable.swift`: sibling names were left out of scope.
    - swift-dependencies `Dependency.swift`, swift-sql `Select.swift` and two swift-rfc-8446 test files: they appeared in the error output of the failed builds.
  - **Kept, by hand:** swift-iterator `Iterator.Buffered.swift`, where the moved extension gets the missing `Base.Element: ~Copyable` constraint.
  - **Pre-existing?** swift-rfc-8446 test errors may predate this batch. Check them against origin/main.
- **Root build:** swift-motion, added 3 Nov, imports AppKit, and that stopped the Linux root build at step 766 of 7,833. `generate.py` now gives products whose targets import Apple-only frameworks outside `#if` a `.when(platforms:)` Apple condition: swift-motion's 3 products.
- **Next:**
  1. Verify batch 1: run the root build, then test builds for the failed packages and swift-iterator.
  2. Batch 2 is ready: `overnight/suite-display-names.py` renames 140 `@Suite("…")` types to raw identifiers. It skips dotted names, because Swift Testing builds test IDs from dotted type paths.
  3. Then work by size, per Coen's target of at least 12,000 findings. Plan for `compound suite name`: 2,295 findings are top-level narrative suites and 2,138 are non-category suites nested under a `@Suite`. Wrap the top-level ones in `extension <Host>`, with the host taken from the file name. Move the nested ones to `extension Host.Parent`, which keeps the type nesting, so Swift Testing's trait inheritance is unchanged.
- **Tools added:** `overnight/dependents.py`, `overnight/backup-wip.sh`, `overnight/suite-display-names.py`.
- **Disk:** the per-session allowance filled up. Deleting institute's and swift-linter-rules' `.build` freed about 11 GB.

### Findings session 2, 7 Nov (running; verified 20:55 UTC)

Linux x86_64, Swift 6.4.2, runner rebuilt from institute 9205733 (same commit as the baseline). Backed up to `findings-wip`.

**Verified at 02:10 UTC (8 Nov) by lint of the changed packages on top of the 01:40 full lint: 30,436 → 23,765, 6,671 fixed (21.9%).** Batch 9 (460 extension-file merges, 752 type splits) applied after 01:40; ratchet gate clean of this session's changes. All local commits backed up to `findings-wip` (370 repositories) at session end.

### Handoff, session end 02:15 UTC

- **State:** every package checkout's work is committed locally and backed up; nothing pushed to any package repository. Root build with tests **not green yet**: batch 9 is unverified by it. The last loop round reverted `swift-division` `Division.Signed.swift` (most likely an unused `public import` left by a split).
- **Start here:** `swift-institute/cloud-workspace` branch `findings-wip` holds the patches (`git am` per `wip/<owner>__<name>/` onto origin/main, then `./sync.sh` first — it restores manifests; apply the patches after it). Rebuild the runner (`swift build -c release --product institute-linter-runner` in institute, about 9 minutes) and `swift package dump-package` every package into `/home/user/dumps/` (used by the type-check and edge tools).
- **Verify batch 9 fast:** `overnight/typecheck-direct.py <dir>` then `overnight/typecheck-direct.sh <dir> 2`: runs swiftc directly per changed target with traits and warnings as errors, and **does catch errors** (proven with a deliberate error). `overnight/typecheck-tests.py` misses some (in-process runs return 0 where the same command returns 1; cause not found; don't trust it). An interrupted run found 9 failing targets. For an unused `public import`, drop `public`; otherwise revert the file (a split's new file: revert its directory to before the adding commit). Then `overnight/build-revert.sh 10` for one confirming root build.
- **Ready, not applied:** `overnight/test-function-names.py` (354 `test function naming` renames, tests only).
- **Fallback list** (`overnight/tests-fallback.txt`): check before any push whether swift-finite `Finite Tests`, swift-email `Email Received Tests`, swift-email-html `Email HTML Rendering Tests` and swift-effects `Effects Built-in Tests` fail on origin/main too, or through a dependency this session changed.
- **Remaining by volume:** `compound identifier` 3,236 (skipped: needs new accessor types), `minimal type body` ~1,600 (classes, `~Copyable`, `#if` bodies, nested deeper: by hand), `extension file naming` ~1,700 (mostly types from other modules: 1,199 have no same-module file), `path name grammar` ~1,850 (mostly target-directory and type-name renames: module renames, structure step), `int public parameter` 1,493 and `raw value access` 1,340 (semantic), `single type per file` ~1,100 (private or `#if`).
- **Root build with tests: not green yet.** `overnight/build-revert.sh` builds, reverts each file an error names to its state before the moves, and lists a test target this session didn't change on `overnight/tests-fallback.txt` (built per package instead). On the list now: swift-slab `Slab Tests` and `Decision Slab Integration Tests` (trait-gated `Slab.Inline`), swift-rfc-8446 and swift-rfc-7519 `Standard Library Integration Tests` (fail on origin/main), swift-finite `Finite Tests`, swift-email `Email Received Tests`, swift-email-html `Email HTML Rendering Tests`, swift-effects `Effects Built-in Tests`. **To check before any push:** whether each of the last four fails on origin/main too, or through a dependency this session changed.
- **Next:** finish the build loop; the remaining `single type per file` splits (767) and `extension file naming` merges (460) with per-file reverts; the rest of `minimal type body`; `raw value access` and `int public parameter` where no new type is needed.
- **Batch 8:** `minimal-bodies.py` again, with failures reverted per file, not per directory (6 type-check rounds), and ratchet rises reverted per file to the state before the moves.
- **`compound identifier` (3,236): skipped.** Its fix is nested accessors (`fetch.all()` for `fetchAll`), which needs a new accessor type for almost every finding; 2,963 are public API, many named after SQL functions. The brief leaves fixes needing new types to the semantic pass.
- **Batch 5:** the runner's own repairs (`minimal type body`, `counter loop iteration`, `test display name string`, `swift protocol qualification`, `comment in source`), type-checked; 16 failing directories left out.
- **Batch 7:** `overnight/minimal-bodies.py` moves non-stored members into an extension of the type (722 types, 2,480 members); classes, `~Copyable`, `#if` bodies and over-visible members skipped; 82 directories failing the type-check or uncheckable left out; 72 targets reverted to origin/main where the move raised a rule over its ratchet limit.
- **Ratchet gate** (`overnight/ratchet-check.py`, institute's limits): no repository over any limit from this session's changes. 63 targets whose changes raised a rule over its limit were reverted to origin/main. Three items are over the limit already on origin/main, not from this session: swift-linter-rules `comment in source` 1>0 and `path name grammar` 17>16, institute `comment in source` 21>0.
- **Lint fix:** `lint-all.sh` mirrors each package alone, as CI checks it out. Sibling mirrors made the runner report about 450 false `target import edge` findings; with isolated mirrors the rule is back at its baseline.
- **Batch 4:** `merge-extension-files.py` (798 merges) and `split-types.py` (855 moves), then reverted where they broke: directories failing the type-check only after the batch, directories the type-check can't verify (C shims, macros), 33 directories where a merged file brought conditional imports mid-file; 45+ unused `public import`s made internal. Institute's generated `Ratchet+limits.swift` kept separate.
- **Pre-push gate:** `overnight/ratchet-check.py` lists every repository rule count over institute's ratchet limit; run before every push.
- **Build:** root build with 682 test targets in one plan (`generate.py` on main): libraries green; test targets type-checked with `overnight/typecheck-tests.py` (2 s per target, shown to fail on a deliberate error); targets failing only through this session's changes reverted to origin/main (svg-render, rfc-8446 Extension tests, 2 more). Fallback list `overnight/tests-fallback.txt`: swift-slab `Slab Tests` (trait-gated `Slab.Inline`), swift-rfc-8446 `Standard Library Integration Tests` (fails on origin/main). 136 targets the root can't take are in `tests-skipped.json` (macro plugins, Apple-only, non-product deps, `package` access). The last root test build stopped on the rfc-8446 target, now on the fallback list; the next batch's build confirms green.
- **Next batch, prepared:** `overnight/merge-extension-files.py` (799 `extension file naming` merges) and `overnight/split-types.py` (1,037 `single type per file` moves), applied together, type-check sweep, one root build.

### Findings session 3, 8 Nov (running)

Linux x86_64, Swift 6.4.2, runner from institute 9205733. Start: full lint 23,768 (`/home/user/lint-s3`). **After batches 10–16, lint of the 200 changed packages: 20,555, so 9,881 fixed (32.5%).** Root build with tests running (`build-revert.sh`, per-file reverts); not green yet.

- Batch 9 verified with `typecheck-direct`: duplicate imports from merges removed (`dedupe-imports.py`, `tc-fix.sh`), unused `public import`s made internal, 8 files and 2 targets (binary-parser, buffer-slab) reverted.
- `test function naming` 360→6 (`test-function-names.py`); `test display name string` 420→30 (suite strings dropped with type names kept, so test IDs are unchanged: `suite-drop-display.py`); `compound suite name` 493→296 (`compound-suites.py`; 54 files reverted where it nested a suite under a namespace of its own name).
- `minimal type body` 2,396→1,153 (batch 10, `minimal-bodies.py` again plus runner repair; type-check failures reverted per target).
- `counter loop iteration` 445→265 (`counter-loops.py`: range loops without break/return/try/await become `forEach`); `statement where expression fits` 179→58 (`if-expressions.py`).
- `exported import` 606→75 and `architecture import boundary` 452→53 (`exports-file.py`: re-exports moved into the target's root `exports.swift`; the per-module re-export set is unchanged).
- Rose: `single type per file` 1,034→1,181 (from the moves; ratchet check pending), `namespace adoption typealias` +15.
- `module selector spelling` 286→59 (`module-selectors.py`); `single type per file` 1,181→757 (`split-types.py` again); batch 18 minimal bodies 1,173→1,081; `trait consistency` 323→19 (runner repair, 38 manifests, committed and re-localized).
- `compound type name` 910→707 (`private-compound-types.py`: internal types named in no other file become `fileprivate`, which the rule exempts); `compound identifier` 3,236→3,138 (`package-to-internal.py`: `package` members used only in their own target become internal).
- **Lint of changed packages at 03:50 UTC: 19,405, so 11,031 fixed (36.2%).** Root build with tests still looping (`build-revert.sh`); two restarts were caused by this session's own file moves during the build and a nested `exports.swift` (7 targets merged into their root file).
- `extension file naming` 1,788→455: `where-file-names.py` (122 files renamed to the `T where <clause>.swift` shape), `own-type-files.py` (412 files of another module's type renamed to `T.swift`), then `merge-extension-files.py` (807 merges into those files); swift-buffer-slab's target reverted (type-check).
- **Lint of changed packages at 04:20 UTC: 18,098, so 12,338 fixed (40.5%): Coen's 12,000 target is reached.** Not yet verified by a green root build with tests: `build-revert.sh` is running on this state (`/home/user/logs/br-s3d.out`); it reverts any file it finds broken, which can lower the count slightly. Source type-check (`typecheck-direct`) is clean on every changed target except known tool limits (macro plugins, C shims, `@_rawLayout`) and pre-existing failures (swift-coder `String.Coder.Lossless`, rfc-9111/9112 coders, swift-witnesses `@preconcurrency`, swift-sqlite `@Table` schema).
- Rises to check with the ratchet gate before any push: `single type per file`, `path name grammar` (new file names from splits), `minimal type body` +10, `exported import` +9.
- Remains: `compound identifier` 3,138 (new accessor types), `path name grammar` 2,106 (mostly target directory and type renames: module renames), `int public parameter` 1,493 and `raw value access` 1,345 (semantic), `minimal type body` 1,091 (classes, `~Copyable`, types whose moves failed the type-check), `single type per file` 756 (private or `#if`), `compound type name` 707 (public or used across files: renames into new namespaces).
- **Ratchet gate (05:10 UTC):** files that raised a rule over its limit were reverted (`ratchet-revert.py`: 199 files in 50 packages, then 30 more; swift-async-sequence and swift-tests `Sources` back to origin/main). Gate clean apart from three items over on origin/main already (swift-linter-rules `comment in source` and `path name grammar`, institute `comment in source`). **Count after the gate: 18,497, so 11,939 fixed (39.2%).** A small top-up batch (~90) follows the build.
- Bug found and fixed in the revert tools: directory reverts used `--diff-filter=A`, which misses renamed files; two leftover copies in swift-tests removed, and no other repository has a renamed file next to its original.
- Root build with tests: running again (`/home/user/logs/br-s3e.out`).
- **06:40 UTC:** the 05:05 root build stalled an hour in resolution: a ratchet revert had restored swift-finite's committed manifest without re-localizing it (fixed with `./localize.py`; `ratchet-revert.py` must be followed by `./localize.py` when it touches a manifest). swift-plist, swift-angle and swift-polygon `Sources` reset to origin/main (partial reverts left them inconsistent; type-check clean after). Top-up batch applied and type-checked (`counter-loops`, `if-expressions`, `private-compound-types`, `own-type-files`, `where-file-names`: ~50). Root build with tests running again (`/home/user/logs/br-s3f.out`). Then: `./ratchet.py`, institute limits, push.
- **08:00 UTC, build loop findings:** content lost through merges and partial reverts, found by the build and by a new check (`overnight/lost-declarations.sh`: declaration lines on origin/main missing from HEAD, access and selector spelling normalized). Reset to origin/main: swift-magnitude and swift-size `Sources` (Codable conformances lost), swift-interval (`Equatable`/`Hashable` lost), swift-email (Email Received files dropped), swift-standard-library-extensions `Tests`, and every changed macro or SwiftSyntax target (32 targets: they can't be type-checked outside the build). The check now finds no other loss in `Sources`. Root build loop still running (`br-s3f.out`, round 12+).
- To check before push: lines where a moved member's closing brace landed on the member's last line (`typealias X = S}`), left by `minimal-bodies.py`; they compile but swift-format will rewrite them.
- **09:10 UTC, pre-push checks:** `lost-declarations.sh` reports no lost declaration in `Sources`; `@Test` counts in `Tests` equal origin/main in every changed repository; manifest changes are trait conditions only (38 packages). swift-format configuration regenerated (it was missing in this container, so earlier repairs got blank-line tidying only); `format-changed.py` formatted 1,165 changed files in 179 repositories whose origin/main versions were stable under it. 44 nested `*.exports.swift` files: imports left by the exports move made internal. Root build loop: round 15 running; then another loop on the formatted state.
- **Checkpoint push (Coen, #242, 8 Nov 07:51):** each changed repository goes to main once it passes zero lost declarations, swift-format, test type-check plus root library build, and no rule over its ratchet limit; failing ones are held. 10:30 UTC: gate 1 clean everywhere (`lost-declarations.sh` empty); gate 2 done (`format-changed.py`); gate 3 running (`build-revert.sh 25`, `br-s3g.out`; swift-ratio `Sources` reset to origin/main); gate 4: full lint of the changed repositories running (`/home/user/lint-final`).

### Checkpoint push, 8 Nov (running)

Root build loop capped at 2 more rounds (Coen); not green at the cap (last round failed in swift-test). Gate stand-in for libraries: a fresh `typecheck-direct` of all 510 changed library targets. Count at the push: 18,992 findings, **11,444 fixed (37.6%)**, by lint of all 400 changed repositories. 379 repositories to push, tier by tier, without force (`overnight/push-checkpoint.sh`, log `overnight/pushes-checkpoint.txt`); the first 10 atoms pushed.

**Held (22), committed locally and backed up on `findings-wip`:**
- swift-atoms/swift-indexed: ratchet: single type per file 1>0
- swift-compositions/swift-darwin: ratchet: exported import and architecture import boundary 9>0
- swift-compositions/swift-linter-rules: ratchet: comment in source and path name grammar over the limit on origin/main already
- swift-institute/institute: ratchet: comment in source 21>0 on origin/main already
- swift-atoms/swift-slab: test targets on the fallback list (trait-gated Slab.Inline), not verified
- swift-atoms/swift-finite: Finite Tests on the fallback list, not verified
- swift-compositions/swift-email: Email Received Tests on the fallback list, not verified
- swift-compositions/swift-email-html: Email HTML Rendering Tests on the fallback list, not verified
- swift-compositions/swift-effects: Effects Built-in Tests on the fallback list, not verified
- swift-atoms/swift-size: Size Tests on the fallback list, not verified
- swift-ietf/swift-rfc-9293: Standard Library Integration Tests on the fallback list
- swift-ietf/swift-rfc-8446: Standard Library Integration Tests on the fallback list (fails on origin/main too)
- swift-ietf/swift-rfc-7519: Standard Library Integration Tests on the fallback list (fails on origin/main too)
- swift-molecules/swift-test: root build: Test.Benchmark files failed in the last capped round
- swift-atoms/swift-coder: type-check: String.Coder.Lossless
- swift-atoms/swift-optic: type-check: tuple with noncopyable element
- swift-compositions/swift-sqlite: type-check: SQLite.Schema (@Table) and an unused public import
- swift-compositions/swift-witnesses: type-check: @preconcurrency import under strict memory safety
- swift-ietf/swift-rfc-9111: type-check: HTTP.Cache.Expires.Coder
- swift-ietf/swift-rfc-9112: type-check: HTTP.Connection.Coder
- swift-molecules/swift-graph: type-check: duplicate import with differing access
- swift-standards/swift-email-standard: type-check: unused public imports
- **Pushed: 379 repositories** to main, plain fast-forward pushes, none forced, none rejected (atoms 167, molecules 49, standards 102, compositions 61). Every pushed SHA is in `overnight/pushes-checkpoint.txt`. **Held: 22** (listed above). Next: read CI once, then `./ratchet.py`.
- **CI, read once (10:05–10:15 UTC), 190 of the 379 pushed repositories** (`overnight/ci-checkpoint.txt`): 12 success, 156 failure, 22 still running. Opened swift-anamorphism's run 42463230253 (the pattern repeats in all chunks read: same window, attempt 2, previous commit green): every build and test job passed (Linux 6.4/release/traits off, macOS, Windows). The red comes from **Quality · source**, which failed before checking anything (`curl: (56) 504` fetching the published planner binary from swift-institute/institute-application's `ci-binaries` release), and **Extended · Embedded**, which fails compiling the swift-syntax dependency under the nightly toolchain (`ambiguous use of 'precondition'` in SwiftSyntax), not package code. `ci-ok` aggregates both. Neither is from this session's changes; I re-ran nothing. **To do:** re-run once the planner download is reachable (someone already re-ran once, in the outage window), then read again; check whether Embedded was green on these repositories before 8 Nov.
- **Not done:** `./ratchet.py` regeneration (institute is held: its `comment in source` is over its limit on origin/main already).

## Cloud session, 9 Nov (BRIEF-cloud.md): one owner for #242 and the backlog

Linux x86_64, Swift 6.4.2, 4 cores. Every green here is Linux only; Apple and Windows code is checked by `ci.yml`.

### 1. Combined build at the pushed SHAs (`backlog-pushed-2026-11-09.tsv`)
- `./sync.sh`: 438 repositories; all 70 pushed repositories at exactly their pushed head.
- `swift build --build-tests` over the whole ecosystem stops at the first failing module, so it ran in rounds. Dependents the 9 Nov push broke, fixed locally (pushed after the build is green):
  - swift-iso-8825: UTF8String decoders need `try` (swift-iso-8824 d736ee7 made `init(contentBytes:)` throw). Also red in CI on all four build jobs.
  - swift-ecma-376 tests: `ISO_21320.Archive.add` now throws (swift-iso-21320). Red in CI on Linux, macOS, Windows.
  - swift-strings: `ISO_9899.String(adopting:count:)` renamed `init(allocated:count:)`.
  - swift-standards/swift-email-standard: `RFC_5322.Message.ID(uniqueId:domain:)` now throws; new `Email.ConversionError.messageID`.
  - swift-standards/swift-ipv6-standard tests: `ScopedAddress.Zone` is its own type (swift-rfc-4007).
  - swift-compositions/swift-sql tests: `ISO_9075.Dialect.render` now throws.
  - swift-compositions/swift-uuids: `v7(unixMilliseconds:fillRandom:)` is gone from swift-rfc-9562; now `v7(at: RFC_9562.Timestamp)`, which also fixes swift-uuids#2.
  - swift-standards/swift-locale-standard: new `RFC_5646.LanguageTag.Region.area` case.
  - swift-ietf/swift-rfc-2046: swift-rfc-5322 950f22c typed the header list subscript (`RFC_5322.Header.Value?`, not `String?`); this API change was not in `api_changes`.
- Root-harness only: `swift-bifunctor|Bifunctor Macro Tests` added to `overnight/tests-fallback.txt` (macro attribute unknown when the test target is declared in the root package). Not caused by the push.

### 2. CI read once, runs after 10:25Z (11:05Z): 14 green, 17 red, 34 still running, 5 without a run (Actions disabled: rfc-3596, 6455, 6891, 7301, 8200)
- Red from the push, compile: swift-iso-8825, swift-ecma-376 (above); swift-windows-32 Windows tests (`Windows.Kernel.File.Stats Tests.swift`).
- Red, Quality · source, swift-format: swift-source (also red before), swift-parser-machine, swift-iso-32000 (also red before). Fixed by swift-format with the source gate's configuration in these and 7 more pushed repositories that would fail it.
- Red, Quality · source, ratchet over its limit: swift-slot-map (do throws for typed catch 19>0), swift-tensor (counter loop 1>0, raw value access 25>22), swift-tree (int public parameter 6>3), swift-rfc-791 (unchecked call site 49>48), swift-rfc-3986 (chained rawvalue access 10>8), swift-iso-21320 (counter loop 1>0), swift-ecma-376 (swift protocol qualification 1>0), swift-rfc-5322 (raw value access 11>10), swift-iso-8824 (string utf8 scanning 1>0), swift-x86-standard (raw value access 6>3, also red before), swift-iso-14496-22 (compound suite name 8>7), swift-iso-9075 (do throws for typed catch 1>0).
- Red, Extended · Embedded (advisory): swift-source, swift-tree (`no such module 'Foundation'`), swift-parser-machine (Memory_Small not imported).
- swift-slot-map: Windows release compiler crash (exception 29 in IRGen of SlotMap Tests.swift).
- No infrastructure failures (no 503/504, no `PIN-*` read errors).

### 3. Backlog
- Fixes run in 12 groups, each repository on a local branch `backlog/<name>` in a worktree, merged into the checkouts only for a whole-ecosystem build before any push.

### 4. Progress, 9 Nov afternoon
- **Rule from Coen (9 Nov):** another session (on the Mac) also pushes repairs. Before fixing any package, pull it and check origin/main; fix it here only if it blocks this session. Already seen: swift-strings 0657448 (the same fix as this session's, so mine was dropped) and swift-sqlite 6e75537, both from the Mac around 12:30Z.
- **Pushed repairs** (each built in the combined build first):
  - swift-iso-8825 7ea8f78, swift-ecma-376 1157edc;
  - swift-ietf/swift-rfc-2046 8a93126; swift-standards/swift-email-standard 2112b28, swift-ipv6-standard e618823, swift-locale-standard 92d64b3;
  - swift-compositions/swift-sql db0daca, swift-uuids 51361e5;
  - swift-format only: swift-source 7630c45 and 04a8998 (Package.swift), swift-parser-machine 41b5b36.
- **Further breaks found, fixed locally, building now:**
  - swift-iso-32000 36b296b removed `Document: Binary.Serializable` when the writer started throwing. New `[Byte](document) throws(ISO_32000.Writer.Error)`; swift-pdf, swift-pdf-render and swift-pdf-html-render tests take `try`.
  - Ratchet overruns in 12 repositories (slot-map, tensor, tree, rfc-791, rfc-3986, iso-21320, ecma-376, rfc-5322, iso-8824, x86-standard, iso-14496-22, iso-9075), cleared without behaviour change.
- **Root-harness only:** test targets behind non-default traits (swift-binary-parser ASCII Decimal Machine Tests; swift-translating Platform, Dependencies and Translated String Tests) and swift-tensor's Tensor Tests (package-access init) are in `overnight/tests-fallback.txt`. CI builds them.
- **CI read 2 (about 12:30Z), 70 pushed repositories:** 27 green, 38 red, 5 queued (Actions disabled). Quality · source was already red before the push in about 20 of the red repositories.
- **Issues ticked and closed: 26**, all in repositories green in CI read 2. Left open: swift-color-standard#5 (two items, fixed on the backlog branch) and swift-rfc-2822#10 (no checklist; checking 1fa28c9 against its acceptance text).
- **Backlog:** 12 fix groups done on local branches: 170 items fixed, 17 left open, each with a reason. Not built yet. Integration comes after the push repairs are green.

### 5. 14:45Z: why nothing was pushed since about 13:30Z
- The whole-ecosystem build ran out of disk: each test target links into its own library, and with debug info they took 15 GB of this session's allowance.
- Fix: the build now runs with `-Xswiftc -gnone -Xcc -g0` (7.5 GB in total). That needed one full rebuild from scratch (about 25 minutes).
- That rebuild was then killed for memory while linking test libraries in parallel. It is resuming with `-j 2`.
- Ready to push once it's green:
  - the lint repairs in 24 repositories;
  - swift-iso-32000 `[Byte](document)` with the swift-pdf, swift-pdf-render and swift-pdf-html-render tests;
  - swift-format in rfc-5280, 6068, 6265, 6455, 6750, 6891 and 7301;
  - swift-rfc-8259.
- **Dropped:** the lint commits for swift-rfc-9557, swift-x86-standard and swift-iso-32000. Their Quality · source was red before the push, so they are out of scope for now.
- **Mac conflict:** swift-w3c-xml 96399ce (`[Byte](bitPatterns:)`) conflicted with the w3c-xml backlog branch. The branch keeps its shared parser, with the Mac's conversion applied inside it.
- **Coen, 9 Nov afternoon:**
  - push what's proven at once;
  - every red the push caused goes out before more backlog;
  - between pushes, build only the changed targets and their dependents; the whole ecosystem once, right before each push;
  - push about hourly, or say here why not.
- **swift-slot-map's Windows release crash** is swift-institute/Issues#224 (IRGenDebugInfo "Incorrect reconstructed type"); the details are in a comment there. It reproduces on Linux with `-enable-round-trip-debug-types`. It's a toolchain bug, not worked around.

### 6. Push at about 15:35Z: 36 repairs
- **Pushed:** lint repairs (ratchet overruns new with the 9 Nov push) in 34 repositories, plus swift-rfc-6068 (swift-format) and swift-iso-32000 958ff92 (`[Byte](document) throws`). SHAs are on #242 (comment 6744089604).
- **Proof (Linux):**
  - `./build.sh` with the 47 test targets of these repositories is green.
  - The last whole round got through 35,744 of 42,221 tasks with no compile error.
  - Lint shows 0 over the limit; swift-format is clean.
- **swift-pdf, swift-pdf-render and swift-pdf-html-render:** fixed and lint-clean, waiting for a whole build with the new linker flag. `-use-ld=lld` changes the compile flags, so the first run recompiles everything, and a `--target` build doesn't link the macro plugins it then needs.
- **Their `Tests/Testing/` directories** (performance and snapshot tests) are in no manifest, so no build ever compiles them; only the source gate's lint reads them.
- **Build settings** are in `build.sh` and CLAUDE.md (f5b84d8).
- **Next:**
  1. CI read 3 at about 16:15Z.
  2. Push the PDF trio once the build is green.
  3. Then the backlog in small groups, lowest layer first, each group with all its API callers fixed:
     - layer 3, 26 repositories, rebased onto main in `/home/user/wt/<name>`;
     - its 5 layer-4 dependents (kernel, file-system, loader, mcp, memory-mapping), already fixed in their worktrees;
     - swift-json (#15) last, since it reaches about 44 call sites including institute.

### 7. Wind-down, 9 Nov about 16:40Z

### The whole-ecosystem build doesn't fit this machine
- With debug info, the linked test libraries alone filled the disk allowance (15 GB).
- Without debug info, ld.gold needed over 12 GB of memory to link the big test libraries.
- With lld (`-Xswiftc -use-ld=lld`, plus `--disable-dead-strip` so macro plugins keep their metadata), swift-build itself still grows past 13.5 GB on a run that goes to the end, and the kernel kills it (rc 137) at about 36,000 of 42,000 tasks.
- So **a whole `--build-tests` run cannot finish in 15 GB**. What works: `./build.sh <Target> ...`, a targeted build of the changed modules and their dependents (compiled, not linked). The settings and this note are in `build.sh` and CLAUDE.md.

### Pushed by this session
Repairs only, for reds the 9 Nov push caused. Each was built (whole rounds up to 35,744 tasks, then targeted) and linted (0 over the ratchet) before its push:
- **10:5x–12:20Z, dependents broken by API changes:**
  - swift-iso-8825 7ea8f78
  - swift-ecma-376 1157edc
  - swift-rfc-2046 8a93126
  - swift-email-standard 2112b28
  - swift-ipv6-standard e618823
  - swift-locale-standard 92d64b3
  - swift-sql db0daca
  - swift-uuids 51361e5
  - swift-source 7630c45 and 04a8998
  - swift-parser-machine 41b5b36
- **15:35Z:** 34 lint repairs, swift-rfc-6068 and swift-iso-32000 958ff92. The SHAs are in comment 6744089604.
- **15:56Z:** swift-pdf-render fd541f6, swift-pdf-html-render cd7c242 and swift-pdf 7ca87f8.
- **Issues:** 27 closed. 26 had every checklist item ticked with its SHA, in repositories green in CI. swift-rfc-2822#10 was checked by hand against its acceptance.
- **The Mac session's pushes were pulled first:**
  - swift-strings 0657448 is the same fix as mine, so mine was dropped;
  - swift-sqlite 6e75537 is theirs;
  - swift-w3c-xml 96399ce conflicted with the w3c-xml backlog branch, and the branch was adapted to it.

### CI after the repairs
CI read 3 (about 16:20Z), latest run of 48 repaired or depending repositories: **36 green** on Plan, macOS, Linux (release, 6.4, traits off) and Windows. Every red has been handled:
- **swift-sql:** tests needing `try`. Fixed by 9cd1e15, pushed from elsewhere at 14:58Z; I kept that version.
- **swift-rfc-2046:** `raw value access` 10>9 from my repair. Fixed in 31e91fa (lint 0 over; RFC 2046 and RFC 2387 test targets build).
- **swift-rfc-2387:** its run was from before the swift-rfc-2046 fix. The failed jobs are re-queued (run 42600956943).
- **swift-rfc-5280:** `Attribute` decoded its SET OF values with the SET reader, which since swift-iso-8825#14 refuses equal tags. Fixed in ad1e2f9: it now uses the SET OF reader. `swift test` passes 181 tests on Linux.
- **swift-windows-32:** the Windows tests' use of the internal `_get`. Fixed in 8c61145, which is the backlog branch's 01bbafa plus a `count minus one` lint fix. Windows-only code, not compiled here.
- **swift-slot-map, Windows:** the toolchain assertion swift-institute/Issues#224.
- **swift-iso-32000:** Quality · source, already red before the push.
- **Still running at 16:20Z:** swift-pdf and swift-pdf-html-render.
- **No CI run at all** (Actions disabled; the open items need a repository setting): swift-rfc-6455, 6891, 7301, 3596 and 8200.

### What's left, in order
1. **Tick and close** the 55 issues in `backlog-stashes/9-nov-cloud/ticks-left.json` (item text and SHA per issue) once their repositories are green. Use `TICK-BRIEF`-style care: tick only matching `- [ ]` lines, and close an issue when none are left.
2. **Backlog, 65 branches, never built** (`backlog-stashes/9-nov-cloud/`, one directory per branch with its base SHA and the issue items it fixes):
   - Merge them a few at a time, lowest layer first. Fix every caller of each changed API in the same round (the API changes and their callers are in `fixes/<repo>.json`), build by target, lint, push.
   - swift-windows-32's branch: its first patch, 01bbafa, is already on main (8c61145).
   - Layer 3 (26 branches) was rebased onto main on 9 Nov afternoon. Its five layer-4 dependents (swift-kernel, swift-file-system, swift-loader, swift-mcp, swift-memory-mapping) already carry the fixes those API changes need.
   - **swift-json#15** (`serialize`/`jsonString` now throw) reaches about 44 call sites, about 15 of them in institute. Give it its own round.
   - **17 items left open, each with a reason**, mostly needing another repository or a decision:
     - swift-kernel#23 and #29 need a public setter and an overflow counter in swift-linux-standard, and F_NOCACHE in swift-iso-9945;
     - swift-glob#1 belongs in swift-posix;
     - swift-storage#14 needs ledger ownership moved across three packages;
     - swift-xml#5 needs located errors in swift-w3c-xml;
     - swift-executors#14 needs the crash reproduced;
     - swiftui-extensions#1 is Apple-only;
     - swift-pdf-render#10: choose between throwing, reporting and embedding a font;
     - swift-w3c-css#13: PageBreak;
     - swift-iso-32000#14: the AFM width tables;
     - swift-iso-9945#93: the Path part, in swift-path.
3. **Not reached at all:** held-back-outside-ecosystem (7 coenttb and 3 swift-whatwg repositories) and open-after-earlier-wave swift-sample#10, swift-time#3 and swift-array#10 (Embedded/toolchain). coenttb/work#184 and #109 are personal dated items, not code.
4. **Quality · source reds from before the push** are out of scope for now and go into the fresh-lint issue (done criterion 5):
   - swift-source, swift-rfc-9557, swift-x86-standard and swift-iso-32000;
   - patches for the last three are in `backlog-stashes/9-nov-cloud/`; swift-rfc-9557's doesn't compile.
5. **swift-slot-map Windows release:** toolchain assertion swift-institute/Issues#224 (details in comment 6741514771). Not worked around.
6. **#242 done criteria 4 (fleet CI read, green on all three platforms) and 5 (fresh fleet lint, new issue by rule)** are still open.

This session stops here.


## Overnight on the Mac, 10 Nov: tier A batches 1 and 2 pushed (05:37Z)

19 sets applied onto main with `git am -3`; all applied cleanly. The whole ecosystem built with tests before the push: 438 packages, 0 errors (macOS 27.2, Swift 6.4.2, macOS only; Linux and Windows come from `ci.yml`).

**Pushed** (repository and head SHA): swift-splat c8724be, swift-vat-standard cda1249, swift-w3c-cssom 3de5b05, swift-itu-r-bs-1770 70dbe59, swift-motion f36402f, swift-w3c-png f8df35a, swift-posix 4c26a88, swift-sql 06ed53c, swift-locale-standard 6723961, swift-loader 99971b4, swift-emailaddress-standard dc1bc7d, swift-email-standard ab91097, swift-process d38e8ed, swift-arguments bbc72d2, swift-git e791367, swift-stores 7deb582, swift-time-to-live 0aac61e, swift-yaml b01ccff, swift-byte-channel 7d97e82.

**Fixed before pushing** (each amended into its set's commit):
- swift-byte-channel: the new test failed to compile under MemberImportVisibility because the error enum's cases live in Async Channel. The test target now declares and imports Async Channel.
- Six new ratchet findings from the sets, each brought back under its limit:
  - swift-splat `count minus one`;
  - swift-w3c-png: two `counter loop iteration`;
  - swift-loader and swift-email-standard: one `compound suite name` each;
  - swift-stores: one `existential parameter`, now a generic `isolated` actor parameter, and three `try optional`, now one helper with a REASON;
  - swift-time-to-live: one `target import edge`, now a declared dependency.

**Issues:** 18 closed (all items fixed). swift-vat-standard#1 has one bullet left. swift-process#6 stays open until Windows CI runs the re-enabled test.

**Decision:** I lint with `/Applications/Xcode-27.2.0.app` (27B52), because the source policy pins its swift-format by hash. The selected Xcode-27.2.app is 27B48, and its swift-format is refused.

**Next:** batches A3 and A4 (13 sets, applied, being linted), then tier B.
