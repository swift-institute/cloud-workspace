# Overnight: warnings and lint findings, 6–7 Nov

Brief: `BRIEF-overnight.md` (coenttb/work#240). Linux x86_64, Swift 6.4.2, only. Apple and Windows code isn't compiled here; `ci.yml` judges those.

The #239 Linux lane closed at 21:45 UTC (status.md 474523a). Work here starts from `./sync.sh` at 21:49 UTC.

## Method

Tools in `overnight/` (this repository):

- `build-warnings.sh`: every package in tier order (atoms, molecules, standards, compositions with institute, coenttb), `swift build --package-path <repo> --build-tests` with one shared `--scratch-path`, through the workspace's path dependencies; packages that declare traits again with `--enable-all-traits`.
- `count-dia.py`: compiler warnings are read from the serialized diagnostics (`.dia`) the build keeps per source file, not from logs: an incremental build prints nothing for files it doesn't recompile, but their `.dia` stay. Unique by file, line, column and message; the kind is the compiler's diagnostic group. `dia.py` reads the format.
- `lint-all.sh` + `count-lint.py`: the runner (`institute-linter-runner`) built in release from institute main, over a mirror of each checkout with its committed manifest (not the path-dependency rewrite). Bundle by organisation as `ci.yml` picks it: atoms and molecules `primitives`, standards bodies `standards`, the rest `institute`.
- `apply-repairs.py`: applies the runner's own repair rewrites for one rule, only to files unchanged since they were linted, in Sources/ and Tests/; then swift-format with the Institute policy's configuration where the committed file was already stable under it.
- `count-suppressions.sh`: suppression directives written as line comments.

Packages: the 448 in `repos.txt` plus the 7 private portable ones in `private-repos.txt` (455). Mac packages stay out.

## Baseline (before any fix)

**Lint, 22:05 UTC**, runner built from institute main 18cc737, all 455 packages, no package unmeasured, no failed control:

| Tier | Findings |
|---|---|
| atoms | 9,906 |
| molecules | 3,513 |
| standards | 15,906 |
| compositions | 15,798 |
| coenttb | 854 |
| **total** | **45,977** |

99 rules have findings; 9 are errors (6 `apache license` in the private coenttb packages, 2 `bare string dependency`, 1 `variable named impl`), 1,691 notes, the rest warnings. Largest kinds: compound suite name 5,108; minimal type body 4,944; comment in source 4,221; compound identifier 3,330; path name grammar 2,951; raw value access 2,828; extension file naming 2,704; int public parameter 1,665; single type per file 1,603; fully qualified error in typed throws 1,429; compound type name 1,134; counter loop iteration 857; namespace adoption typealias 845; untyped throws 782; module selector spelling 781.

Suppressions: 227 counted by the runner; 334 directive comments (267 `swift-linter:disable`, 45 `swiftlint:disable`, 22 `swift-format-ignore`).

Differs from the published runner CI uses (3a43c13) by institute 79d10ad (`macro expansion short name` escapes), 0b70b0b (`declarative manifest` names the alias extensions), 003bf06 (`bare string dependency` an error). The profile's rule list equals main's inventory for all three bundles (140/143/136).

**Compiler warnings:** read from `.dia` after the build. Atoms and molecules (snapshot 23:09 UTC, before their fixes): 106 (atoms 48, molecules 58): unnecessary-effect-marker, strict-memory-safety, unnecessary-unsafe, variable-never-mutated, unused-import-access. Most manifests set `treatAllWarnings(as: .error)`, so warnings survive mainly in test targets. Standards, compositions and coenttb (04:58 UTC, before their fixes): 707. All tiers: 813 (atoms 48, molecules 58, standards 302, compositions 401, coenttb 4), of which 157 are the intended HTML `@deprecated` warnings. Items: per file, line and kind, from the `.dia`.

## Rule fixes (institute, local commits, pushed with institute's batch)

- `comment in source` admitted only swift-linter directives, so it reported, and its repair deleted, the `// swift-format-ignore` and `// swiftlint:` directives the source gate's other engines need: 47 sites. Fixed with a control and two tests that fail on the old rule (comment in source 4,221 -> 4,174 before any repair).
- `target import edge` treated SDK frameworks and Foundation's Linux modules (SwiftUI, AppKit, Security, FoundationNetworking, ...) as undeclared dependencies, which no manifest can declare: 34 sites. Fixed with a test.

## Round 1: atoms and molecules, pushed 00:28 UTC

85 repositories, one commit each. What changed: the runner's repairs for `comment in source`, `module selector spelling`, `swift protocol qualification` and `counter loop iteration`; 164 renames (fleet-wide) that `extension file naming` names exactly; `@Test` display strings moved into raw-identifier names; compiler fix-its for the warnings above (files whose only `#if` is a trait).
Each changed package built with its tests, default traits and all traits, through the workspace, Linux x86_64. Tests not run here.

Lint, atoms + molecules: 13,419 -> 12,887. Suppressions 12 -> 12.

Held back, broken repairs (rule bugs, not fixed tonight):
- `minimal type body`'s repair broke the build of 5 packages among the 140 files it rewrote in atoms/molecules (swift-algebra, swift-iterator, swift-sequence, swift-store, swift-cursor's tests): a nested type moved to an extension drops sibling names out of scope (swift-algebra's `Type.*`), and an `extension T` drops `~Copyable` suppressions and the `where` clause of the extension T was nested in (swift-iterator, swift-sequence, swift-store); swift-iterator's break failed every package above it in the build. All 140 reverted; the rule's 4,944 findings stay. A guard for the second case is drafted (refuse when the type suppresses a conformance or sits in a constrained extension) but the first needs name-lookup and isn't drafted.
- `counter loop iteration`'s repair moves a loop into a closure even when the body uses a `~Escapable` local (`Span`): swift-array's test no longer compiled. That file reverted.


## Round 2: standards, compositions, coenttb, pushed 06:00–06:34 UTC

74 repositories, one commit each, plus institute's two rule commits (full SHAs of every push in `overnight/pushes.txt`). What changed, files: `comment in source` 395, `module selector spelling` 94, `swift protocol qualification` 52, `counter loop iteration` 98, renames for `extension file naming` 44, `@Test` display strings into raw-identifier names 16, compiler fix-its 51. Each changed package built with its tests, default traits and all traits, through the workspace, Linux x86_64, except as noted under Closing.

Held back here: `module selector spelling`'s repair where a module declares a type of its own name (`W3C_XML`, `SVG_Standard`, `W3C_CSS_Shared`, `WHATWG_*`, `W3C_PNG`): `Module::Name` then names the type, and the build breaks; 30 files reverted. Compiler fix-its for `unused-import-access` where the import is needed under a trait or by a macro expansion (swift-sql's macros, swift-sqlite's GRDB trait, institute's package imports): 51 files reverted.

## Closing

Closed 7 Nov, 08:13 UTC, on Coen's decision relayed by the coordinator: no fix rounds beyond these two; the next order is audit, rule triage, structure, semantic pass, then remaining lint. Everything below was measured on Linux x86_64, Swift 6.4.2, unless it says ci.yml.

### Before and after

**Lint findings**, the runner built from institute main, all 455 packages, 0 unmeasured, 0 failed controls. Before: 18cc737, 22:05 UTC. After: 2ac3965ab4bad61fab3f4557e4b26896c22bcee6 (main plus the two rule fixes), 06:41–06:46 UTC on final main, swift-sqlite again at 07:59 after its fix. Per package and per rule: `overnight/final-lint.json`, which the ratchet starts from.

| Tier | Before | After |
|---|---|---|
| atoms | 9,906 | 9,579 |
| molecules | 3,513 | 3,314 |
| standards | 15,906 | 13,614 |
| compositions | 15,798 | 13,524 |
| coenttb | 854 | 340 |
| **total** | **45,977** | **40,371** |

By kind, what moved: comment in source 4,221 → 12; module selector spelling 781 → 285; swift protocol qualification 222 → 23; counter loop iteration 857 → 501; extension file naming 2,704 → 2,542; test display name string 625 → 541; test function naming 445 → 383; target import edge 551 → 517 (rule fix); bare string dependency 2 → 0. Errors 9 → 7: 6 `apache license` in the private coenttb packages and 1 `variable named impl` in swift-linter. Nothing rose. Suppressions counted by the runner: 227 → 227. Directive comments 334 → 340: the 6 added are fixtures in institute's own tests for the `comment in source` fix, not suppressions.

**Compiler warnings, partial.** Read from the `.dia` each build leaves. Before: 813 (atoms 48, molecules 58, standards 302, compositions 401, coenttb 4), 157 of them the intended HTML `@deprecated`. After: 601 from the last build of each file, of which 157 are HTML `@deprecated` (unchanged) and 444 others (atoms 0, molecules 42, standards 140, compositions 261, coenttb 1). By kind, before → after: strict-memory-safety 199 → 159, unnecessary-effect-marker 186 → 79, unused-import-access 76 → 51, unnecessary-unsafe 63 → 23, variable-never-mutated 41 → 41, other deprecations 69 → 69 (58 CSS, the same kind as HTML, left), the rest 22 → 22. Partial because the final full rebuild was stopped (below) and 41 of the `.dia` read were older than their source, so a few of those 601 may be gone. Warnings are measured again at the remaining-lint step; no `final-warnings.json`.

### What was proven, and where

- **Root build** (`swift build --scratch-path /home/user/scratch-warn` in the workspace root, final main): 07:42:09–07:44:35 UTC, every target builds except swift-motion's `Motion Cache` and `Motion Encoding`, which import AppKit and AVFoundation and can't build on Linux. It could only run after a fix to the workspace generator (3720bd6917a6992ff343f5b29bb8c3b7f5a329f1): the root asked swift-sqlite for default traits only while footprint asks for GRDB, and resolution failed on GRDB. The root now asks each package for the traits other manifests ask of it (51 packages).
- **Each changed package**, with its tests, default traits and all traits, through the workspace, before its push. Exceptions: swift-motion (the package can't build on Linux; the one changed file is in `Motion`, which compiled in the root build; its commit message's "built with its tests" overclaims), institute (default traits; it declares none).
- **Direct dependents where a commit could change a public interface**: one such commit, swift-binary-parser 60e36ee (`public import Binary` → `import Binary`), found by searching every overnight commit's Sources diff for a removed `public`/`package`/`@_exported` import; renames, comment removal, module selectors, `Swift.` qualification, loop rewrites, fix-its and test names don't change a public interface. Its dependents swift-rfc-4291 and swift-rfc-791 built with tests, default and all traits, 07:44–07:46 UTC.
- **Not built:** test targets of unchanged repositories; all-traits builds outside the changed packages. The per-package rebuild of everything was stopped at 07:29 UTC after 87 of its runs (all green but swift-bifunctor's trait-gated default build, which failed before tonight too).
- **Tests weren't run here**, except institute's rule tests for the two rule fixes. ci.yml runs tests and is the only evidence for Apple and Windows.
- **ci.yml**, read 07:47–07:50 UTC for round 2 (atoms/molecules read earlier: 79 of 85 green with builds, 2 infra failures green on re-run): of the 74 round-2 pushes, 58 green, of which 35 have their job lists read showing the Build jobs ran and 23 are green but unread (the planner can skip a platform; it skipped Windows for swift-posix and swift-iso-9945, Linux and Windows for swift-darwin, Linux and macOS for swift-windows). The whole workflow was skipped for swift-interface and swift-impact (private). 9 have no run: swift-iso-4217, swift-app-launch and swift-licensing have no ci.yml; rfc-1034, rfc-3596, rfc-6455, rfc-6891, rfc-7301 and rfc-8200 have only a manual run queued since 1 Nov. swift-iso-32000's Linux traits-off job hung and was cancelled (infra; the other legs and ci-ok passed). swift-w3c-svg's Windows test failed, then passed on re-run. Still running when this closed: swift-tests (Windows test leg failed after my push, green on the run before; re-run started 08:00, run 42347618910) and swift-sqlite's fix (run 42353522901). Neither result is known here.

### Red, reverted, held back

Left red, all for the coordinator:
- swift-molecules/swift-dictionary and swift-tree-keyed: the Windows compiler crashes (exception 0xC000001D in IRGen of a test file) on runs 42327460412 and 42327463609, after my revert of the loop rewrite (b8f29b46eff1209099c5ba4712b998e1e7f8bdc0, 087d2c88f72d66462448725abbaa966d14ab67ef). The rewrite isn't shown to be the cause. Left as they are.
- swift-institute/institute: the Windows test leg fails, as it did on the run before tonight's push (8183d5d, run 42302836067).
- swift-compositions/swift-keychain: Plan fails `README-162` (two paragraphs before `## Laws`); my commit touched only a source file, and this is the first run to get as far as Plan.
- swift-compositions/swift-tests: see above; if the Windows re-run fails again, my commit bcd02c1e194a8e02730129d4a1013f965c7719c3 (comment removal in 111 files, 4 renames, 1 fix-it) is the first suspect.

Reverted after a push: the two above, and swift-sqlite's `some Swift.Sequence` in two `@DatabaseFunction` functions (dd8db514cb7f748b9ec8fd8b595d91f3ddc60083): the macro's expansion can't handle it, CI failed on Linux release and macOS, and my commit message had called the local failure pre-existing because the log it was compared with had been rebuilt after the repair. Fixed: all-traits test build passes. Reverted before any push: 140 `minimal type body` files, 30 `module selector spelling` files, 51 import-access fix-its, one `counter loop iteration` file, swift-institute.org's emptied source (all described above).

### What remains and why

- Not attempted, naming or API, for the semantic pass: compound suite name 5,108, compound identifier 3,330, path name grammar 2,950, raw value access 2,828, int public parameter 1,665, single type per file 1,603, fully qualified error in typed throws 1,429, compound type name 1,134, namespace adoption typealias 845, untyped throws 782, and the rest of `extension file naming` (2,542, names not exact or starting with `_`).
- Stopped by the new order: `minimal type body` 4,944, `counter loop iteration` 501, `test function naming` 383, `target import edge` 517 (106 missing edges in 49 manifests found and checked with `dump-package`, script `overnight/add-import-edges.py`, not applied).
- Compiler warnings left: in files with conditional compilation other than a trait (the warning may hold on this platform only), where no fix-it exists, and where the fix-it is wrong under a trait or macro.

Rules that look wrong:
- `minimal type body`'s repair: moving a nested type to an extension drops sibling names out of scope, and `extension T` loses `~Copyable` suppressions and the enclosing `where` clause. 5 packages broke.
- `counter loop iteration`'s repair moves a loop body into a closure even when it uses a `~Escapable` local.
- `module selector spelling`'s repair breaks where a module declares a type of its own name (`Module::Name` then names the type).
- `swift protocol qualification`'s repair qualifies inside macro-attributed declarations, which macros like `@DatabaseFunction` don't parse.
- Fixed tonight, with tests that fail on the old rule: `comment in source` (it deleted swift-format and SwiftLint directives) and `target import edge` (SDK frameworks and Foundation's Linux modules). These reach CI with the next runner publish.

### Behaviour changes held back

- `canonical settings tail` would add `treatAllWarnings(as: .error)`: a package then fails on a warning it builds with today.
- `trait consistency`'s repairs change which code a trait builds.
- The 106 `target import edge` additions change manifests' dependency graphs.
- Noted, not held back: a `@Test` function renamed to its display string keeps its display name, but its identifier changes, so a `--filter` on the old function name no longer matches.

Every overnight push, with full SHAs: `overnight/pushes.txt` (158 repositories plus institute's two rule commits). Nothing is left unpushed.
