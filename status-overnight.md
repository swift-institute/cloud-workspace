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

99 rules have findings; 9 are errors (`bare string dependency`, now an error by default), 1,691 notes, the rest warnings. Largest kinds: compound suite name 5,108; minimal type body 4,944; comment in source 4,221; compound identifier 3,330; path name grammar 2,951; raw value access 2,828; extension file naming 2,704; int public parameter 1,665; single type per file 1,603; fully qualified error in typed throws 1,429; compound type name 1,134; counter loop iteration 857; namespace adoption typealias 845; untyped throws 782; module selector spelling 781.

Suppressions: 227 counted by the runner; 334 directive comments (267 `swift-linter:disable`, 45 `swiftlint:disable`, 22 `swift-format-ignore`).

Differs from the published runner CI uses (3a43c13) by institute 79d10ad (`macro expansion short name` escapes), 0b70b0b (`declarative manifest` names the alias extensions), 003bf06 (`bare string dependency` an error). The profile's rule list equals main's inventory for all three bundles (140/143/136).

**Compiler warnings:** read from `.dia` after the build. Atoms and molecules (snapshot 23:09 UTC, before their fixes): 106 (atoms 48, molecules 58): unnecessary-effect-marker, strict-memory-safety, unnecessary-unsafe, variable-never-mutated, unused-import-access. Most manifests set `treatAllWarnings(as: .error)`, so warnings survive mainly in test targets. Upper tiers follow.

## Rule fixes (institute, local commits, pushed with institute's batch)

- `comment in source` admitted only swift-linter directives, so it reported, and its repair deleted, the `// swift-format-ignore` and `// swiftlint:` directives the source gate's other engines need: 47 sites. Fixed with a control and two tests that fail on the old rule (comment in source 4,221 -> 4,174 before any repair).
- `target import edge` treated SDK frameworks and Foundation's Linux modules (SwiftUI, AppKit, Security, FoundationNetworking, ...) as undeclared dependencies, which no manifest can declare: 34 sites. Fixed with a test.

## Round 1: atoms and molecules, pushed 00:28 UTC

85 repositories, one commit each. What changed: the runner's repairs for `comment in source`, `module selector spelling`, `swift protocol qualification` and `counter loop iteration`; 164 renames (fleet-wide) that `extension file naming` names exactly; `@Test` display strings moved into raw-identifier names; compiler fix-its for the warnings above (files whose only `#if` is a trait).
Each changed package built with its tests, default traits and all traits, through the workspace, Linux x86_64. Tests not run here.

Lint, atoms + molecules: 13,419 -> 12,887. Suppressions 12 -> 12.

Held back, broken repairs (rule bugs, not fixed tonight):
- `minimal type body`'s repair broke 6 of 140 rewritten files in atoms/molecules: a nested type moved to an extension drops sibling names out of scope (swift-algebra's `Type.*`), and an `extension T` drops `~Copyable` suppressions and the `where` clause of the extension T was nested in (swift-iterator, swift-sequence, swift-store). All 140 reverted; the rule's 4,944 findings stay. A guard for the second case is drafted (refuse when the type suppresses a conformance or sits in a constrained extension) but the first needs name-lookup and isn't drafted.
- `counter loop iteration`'s repair moves a loop into a closure even when the body uses a `~Escapable` local (`Span`): swift-array's test no longer compiled. That file reverted.

