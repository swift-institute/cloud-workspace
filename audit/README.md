# Ecosystem audit and rule triage (coenttb/work#242)

Measured 7 Nov 2026 on Linux x86_64, Swift 6.4.2, statically with swift-syntax 604 (no names matched by grep for the
type data). 455 packages: 448 public (`repos.txt`) and 7 private. Every repository at the SHA in `shas.txt` (synced at
the start of this session; nothing changed in them since, except institute's rule commit cc0d7da, made after the
measurement). Lint at finding level: `institute-linter-runner` built from institute 2ac3965, the runner that wrote
`overnight/final-lint.json`. Private packages are counted everywhere and named nowhere here; their names are on #242.

Re-measure: `AUDIT_WORK=<scratch> audit/measure.sh` (then the lint lines at its end). Scripts: `extract/` (Swift,
swift-syntax: one JSON line per file), `analyze.py` (steps 1–3, 5–7), `molecules.py` (4), `overlap.py` (8),
`rules_sample.py` and `rules_report.py` (part 2). Data in `data/`. Rule table: `rules.md`.

## 1. Declared types (`data/baseline.json`, `data/types.json`)

| | struct | enum | class | actor | protocol | typealias | total |
|---|---|---|---|---|---|---|---|
| non-test | 4,498 | 4,661 | 364 | 46 | 255 | 2,484 | **12,308** |
| test | 11,840 | 1,735 | 259 | 38 | 72 | 1,083 | 15,027 |

Non-test by tier: atoms 2,201, molecules 1,050, standards 5,641, compositions 3,196, coenttb 220. Public non-test: 10,963.
17,233 Swift files. Every row in `types.json` has package, tier, module, access, generics, stored fields, conformances,
file, line and test flag.

## 2. Reference graph (`data/references.json`)

For each public non-test declaration: packages and targets that refer to it, non-test and test apart. A target refers to a
declaration when one of its files has the simple name as an identifier token **and** the target is the declaring target or
depends on it, directly or not. That overcounts (common names), the safe direction, with one exception found by the proof:
a type reached only through a member (`severity.wire.token`) never has its name written, so its uses don't count.
Before deleting anything, the build is the check, not this table.

Proof: `Diagnostic.Severity.Wire` (swift-diagnostic) shows no non-test consumer. Its file removed, swift-lint and
swift-argument built (Linux); institute and one private dependent don't use it textually. Its own package's test target does use
it, through `.wire`, which the table missed (test count 0, really 1). Restored afterwards.

## 3. Wrappers (`data/wrappers.json`, `data/wrappers-summary.json`)

1,806 wrappers: structs and classes with one stored field, enums with one case carrying one payload. Not counted: the 54
`@main` entry points, 69 single-case `Error` enums (errors, not values) and `Tagged` itself.

| Category | Count | What it means | Proposal |
|---|---|---|---|
| Plain | 208 | nothing but storage and forwarding | `Tagged<Tag, X>`. **146 of them are records with one field today** (a `Request` with `accessToken`, a `Stylesheet` with `rules`), not newtypes: only 62 are newtypes by name or field |
| Duplicate | 58 | same name and same stored type in another package | keep the one in the lowest tier, most used (`duplicate_of` per row) |
| Validates | 277 | a throwing or failable init | `Tagged` decodes and takes literals through `_unchecked`. Proposal: keep these as types until `Tagged` gains a `Tag: Validating` hook (one protocol, `static func validate(_:) throws`) that `init(from:)` and the literal inits call; then convert |
| Encoding | 58 | synthesized `Codable`, not `RawRepresentable` | converting changes stored and wire data from `{"y": ...}` to a single value: convert only with a custom `init(from:)` that reads both, or not at all where data is persisted |
| Own behaviour | 949 | members beyond forwarding (582 also record-like) | can become `Tagged` plus `extension Tagged where Tag == X`, but only pays off where the tag is an existing type |
| Language limit | 256 | 103 classes (identity), 149 `@dynamicMemberLookup` (WHATWG HTML attributes), 4 `@propertyWrapper` | `@dynamicMemberLookup` and `@propertyWrapper` must be on the primary declaration, so an extension of `Tagged` can't add them; `~Copyable`/`~Escapable` are not limits |

By tier: atoms 324, molecules 150, standards 865, compositions 443, coenttb 24. The #239 commits added 12 of them
(9 validate, 2 own behaviour, 1 plain).

**Tags.** Each `Tagged<X, Y>` still needs a tag `X`. 1,164 wrappers are nested in a type that can be the tag (no sibling
of the same stored type); 642 need a new tag declaration. A conversion with a new tag removes one type and adds one:
it doesn't reduce the count. So converting every wrapper but the language limits (1,550) nets **−966** declared types
(12,308 → 11,342, −7.8%); plain and duplicate only (266) nets −180.

## 4. Molecules (`data/molecules.md`, `data/molecules-verdicts.json`)

64 molecules: **9 delete, 1 fold, 54 keep.** Delete: under 60 source lines and no consumer in the workspace
(axis-dimension, complex-dimension, geometry-boundary, geometry-pair, module, symmetry-finite, symmetry-linear,
symmetry-pair, version-carrier). Fold: symmetry-algebra into swift-algebra behind a trait. Most molecules are real
structures with their own dependents (buffer-linear 38, memory-allocation 51, ownership-shared 30) or depend on other
molecules, which would put a molecule edge into an atom. Fold cost: one trait and optional dependency on the host,
covered by `--enable-all-traits`; the traits-off job stops compiling the folded code, so the host needs a trait-on test
leg; no candidate has platform code (Windows unaffected); Embedded unaffected with the trait off by default.

## 5. Low value (`data/low-value.json`)

- 1,172 public types (non-typealias) with no non-test use outside their own file; 1,315 used in exactly one other file.
- 119 packages with no dependent in the workspace (apps and Rule Institute not checked: "no consumer in the workspace").
- 722 products nothing in the workspace depends on (many are entry products for apps: needs the Mac check).
- `Bounded`: 15 declarations named `Bounded`, not 10 (the extra 5 are internal or nested). Per-row consumers in the file.

## 6. `Core` names (`data/core-names.json`)

75 targets in 49 packages carry the word `Core` (word match: no false hit; swift-corecursive has none). Groups:
- **37 `X Macro Core`** (one target each, used only by its own `X Macro Plugin`): it holds `enum Derivation`, the
  derivation logic kept apart so it's testable. Rename to **`X Macro Derivation`**.
- **21 `X Core`**: the implementation behind a public umbrella. Merge into the umbrella where nothing outside the package
  depends on it (none does today); rename by content where it is a product.
- **14 test targets** named after them (`X Core Tests`) follow, plus 1 other.
The brief's 58 packages counted differently; this is the swift-syntax count from manifests.

## 7. The open hunt (`data/hunt.json`)

Most important first:
1. **About a third of all lint findings are false.** Weighted by each rule's sampled false-positive rate: ~12,800 of 40,031. 60 rules need fixing (`rules.md`).
2. **Re-export chains are deep.** 870 targets `@_exported import`, 2,170 lines; the longest chain of re-exports is 32
   targets, 652 targets sit 3 or more deep. 544 imports reach a module only through such a chain, with no declared
   dependency: the real dependency graph is hidden.
3. **776 target dependencies are never imported** by the target's files (176 package dependencies unused by any target).
4. **Atoms depend on molecules: 30 edges from 11 atom packages.** The tier order is broken at the bottom. Re-tier the 11 or move what they need down.
5. **466 library targets hold one declaration or none.**
6. Legacy names: 139 targets with `Standard`, 153 `X Foundation Integration`, 11 `Shared`, 4 `Primitives`.
7. `Foundation` imported in non-test sources of atoms (14 files) and molecules (24).
8. 149 `@available(..., deprecated/unavailable)` (standards 113, compositions 36). No `#if false`.
9. Suppressions are in good shape: 242 directives, 237 with a specific reason, 5 without.
10. Parallel names: 205 packages declare a public `Error`, mostly nested and fine; `Kind` (37), `Derivation` (27, the macro cores) are the repeated ones.
11. The 20 largest packages: 13 are standards or compositions with 25+ dependencies; they hold 30% of the wrappers
    (whatwg-html alone 175) and most raw-`String` signatures. They're the wrappers' home, not the atoms.

## 8. Overlap with lint (`data/overlap.json`)

Fresh location-level run: 40,031 findings (the 340 fewer than `final-lint.json` are the runner's own later fixes being
on main). **1,613 (4.0%) sit on code that would be deleted, converted or folded**; 3,318 (8.3%) counting every wrapper
the semantic pass revisits. The overlap is small. But 31,412 (78%) belong to naming and API rules the semantic pass
rewrites, and ~32% are false: the order holds, for those reasons rather than the structure step.

## Not measured here

Apple and Windows code paths (only parsed, never compiled). The Mac apps and Rule Institute (coordinator's check).
Tests weren't run, apart from institute's `minimal type body` tests.
