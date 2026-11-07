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

Stopped after the first pass of step 1 and the step 2 pilot; the context of one session ran out, not the work.

- **Types and wrappers:** unchanged, 12,308 non-test types and 1,806 wrappers (audit baseline); the semantic pass (step 3) has not started. The fold moved 3 files, adding no type.
- **Findings:** 40,371 → 32,421 (−7,950), every change from rule fixes and removals, none from code edits besides the pilot.
- **Remains, in order:** about 40 of the 60 faulty rules (list: `audit/rules-table.md`, verdict `fix`, minus those above; largest: extension file naming, path name grammar, bool public parameter, counter loop iteration's repair, closure typed throws annotation, unknown default); the 8 new rules; Core renames (37 + 21); the 11 atom→molecule edges; unused dependencies; the generated root test package; the semantic pass; remaining lint. The two new `target import edge` findings (swift-environment, swift-pdf-standard) need dependency edges.
- **Proven where:** Linux x86_64, Swift 6.4.2: institute and swift-linter-rules tests; swift-algebra without traits (143 tests), with `Symmetry` and all traits; swift-symmetry-dimension (22 tests). Apple and Windows: only through `ci.yml`.

**Second session (7 Nov):** institute b50d560 fixed 2 more rules (tests fail on the old rules, `swift test` all pass on Linux, swift-format clean with the policy's configuration, written to `/home/user/tools/swift-format.json` from `Institute.Source.Policy+swiftFormat.swift`). Not re-counted: the ratchet stays at 2a07c96's limits (findings can only fall); regenerate with the next rule batch. Then 574f43b, 7d18cd8, c7f4dfc (4 rules, same evidence). `extension file naming`'s foreign-type case needs a package type index; not done.
