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

**Verified at 22:55 UTC by a lint of all 438 packages: 30,436 → 25,357, 5,079 fixed (16.7%).**

| Rule | Baseline → now (all packages) |
|---|---|
| compound suite name | 4,730 → about 441 |
| extension file naming | 2,531 → about 2,131 |
| minimal type body | 3,463 → about 3,103 |
| single type per file | 1,518 → about 1,368 |
| test display name string | 541 → about 396 |

- **Ratchet gate** (`overnight/ratchet-check.py`, institute's limits): no repository over any limit from this session's changes. 63 targets whose changes raised a rule over its limit were reverted to origin/main. Three items are over the limit already on origin/main, not from this session: swift-linter-rules `comment in source` 1>0 and `path name grammar` 17>16, institute `comment in source` 21>0.
- **Lint fix:** `lint-all.sh` mirrors each package alone, as CI checks it out. Sibling mirrors made the runner report about 450 false `target import edge` findings; with isolated mirrors the rule is back at its baseline.
- **Batch 4:** `merge-extension-files.py` (798 merges) and `split-types.py` (855 moves), then reverted where they broke: directories failing the type-check only after the batch, directories the type-check can't verify (C shims, macros), 33 directories where a merged file brought conditional imports mid-file; 45+ unused `public import`s made internal. Institute's generated `Ratchet+limits.swift` kept separate.
- **Pre-push gate:** `overnight/ratchet-check.py` lists every repository rule count over institute's ratchet limit; run before every push.
- **Build:** root build with 682 test targets in one plan (`generate.py` on main): libraries green; test targets type-checked with `overnight/typecheck-tests.py` (2 s per target, shown to fail on a deliberate error); targets failing only through this session's changes reverted to origin/main (svg-render, rfc-8446 Extension tests, 2 more). Fallback list `overnight/tests-fallback.txt`: swift-slab `Slab Tests` (trait-gated `Slab.Inline`), swift-rfc-8446 `Standard Library Integration Tests` (fails on origin/main). 136 targets the root can't take are in `tests-skipped.json` (macro plugins, Apple-only, non-product deps, `package` access). The last root test build stopped on the rfc-8446 target, now on the fallback list; the next batch's build confirms green.
- **Next batch, prepared:** `overnight/merge-extension-files.py` (799 `extension file naming` merges) and `overnight/split-types.py` (1,037 `single type per file` moves), applied together, type-check sweep, one root build.
