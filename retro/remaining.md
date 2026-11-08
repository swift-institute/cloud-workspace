# The remaining findings

These counts come from today's lint of origin/main: all 438 packages, runner from institute 9205733, after the checkpoint push.

- **21,439 on main.**
- **18,992** if the local work in the 22 held repositories is counted. Those repositories hold 5,471 findings on main, unchanged.
- Data: `data/remaining-labelled.json`, made by `tools/label-remaining.py`.

## By label

| Label | Findings | Share | What it takes |
|---|---|---|---|
| New type (semantic pass) | 7,524 | 35% | a typed wrapper, accessor or error type per API. Not lint work: semantic pass |
| Script | 6,328 | 30% | an existing or v2 script through the gated batch |
| Likely false positive | 2,471 | 12% | narrow the rule (audit sample ≥ 70% false). No code change |
| Rename | 2,098 | 10% | file renames (1,650, no compile risk) and public type renames with callers (429) |
| Hand | 1,745 | 8% | `#if` files, private types, `do throws for typed catch`, small rules |
| Module rename (structure step) | 1,079 | 5% | target directories named after modules, test target names, manifest naming |
| Held | 194 | 1% | `trait consistency` (the resolver can't do it), `canonical settings tail` (behaviour change) |

**Where the scriptable findings sit:** 2,894 of the 6,328 are in repositories that are held or broken on main:
- the 22 held,
- the 31 with trait-repaired manifests,
- swift-linux-standard, swift-file-system, swift-layout, swift-memory-mapping, swift-linear.

They can only be worked once main is repaired.

## Pareto by rule (top 30 = 95%)

| # | Rule | Now | Start | Label | Cum. |
|---|---|---|---|---|---|
| 1 | compound identifier | 3,179 | 3,244 | new type: nested accessors (`fetch.all()`) | 14.8% |
| 2 | minimal type body | 2,500 | 3,463 | script: 2,412 nested one level (v2 qualifies sibling names); 58 `#if` bodies by hand; classes by hand | 26.5% |
| 3 | path name grammar | 1,942 | 1,862 | rename: 1,267 file names + 19 inner directories; module rename: 656 target directories | 35.5% |
| 4 | int public parameter | 1,493 | 1,493 | new type (audit: 10/20 false) | 42.5% |
| 5 | raw value access | 1,340 | 1,340 | new type (audit: 11/20 false) | 48.8% |
| 6 | single type per file | 1,177 | 1,518 | script: 775 transactional split; hand: 273 `#if`, 129 private | 54.3% |
| 7 | compound suite name | 934 | 4,730 | script | 58.6% |
| 8 | compound type name | 811 | 925 | script: 382 test-local; rename: 429 public or cross-file | 62.4% |
| 9 | extension file naming | 798 | 2,531 | script: 382 merges, 176 base-type splits; rename: 240 | 66.1% |
| 10 | untyped throws | 652 | 652 | new type: 413 in Sources; likely FP: 239 in Tests | 69.2% |
| 11 | namespace adoption typealias | 606 | 606 | likely FP (14/20) | 72.0% |
| 12 | typealiased namespace bridge | 465 | 474 | likely FP (17/20) | 74.1% |
| 13 | bool public parameter | 443 | 443 | new type | 76.2% |
| 14 | try optional | 415 | 415 | likely FP (14/20) | 78.2% |
| 15 | do throws for typed catch | 361 | 361 | hand: needs the callee's error type | 79.8% |
| 16 | counter loop iteration | 322 | 487 | script, **after** `counter-loops.py` learns to skip `borrowing`/`~Copyable` captures (it broke swift-linear) | 81.3% |
| 17 | unification typealias | 252 | 253 | likely FP (16/20; partly narrowed) | 82.5% |
| 18 | exported import | 241 | 617 | script | 83.6% |
| 19 | unchecked call site | 239 | 239 | new type (narrowed in 10f53f6) | 84.8% |
| 20 | architecture import boundary | 191 | 463 | script | 85.6% |
| 21 | chained rawvalue access | 188 | 188 | likely FP (16/20) | 86.5% |
| 22 | test target naming | 180 | 180 | module rename | 87.4% |
| 23 | existential parameter | 154 | 154 | likely FP (kept by decision) | 88.1% |
| 24 | throwing wrapper init | 152 | 152 | likely FP (19/20) | 88.8% |
| 25 | module selector spelling | 147 | 285 | script | 89.5% |
| 26 | fatal error outside tests | 144 | 144 | new type or hand | 90.1% |
| 27 | file name nested path | 143 | 142 | rename | 90.8% |
| 28 | test function naming | 115 | 360 | script | 91.3% |
| 29 | bitpattern rawvalue chain | 100 | 100 | new type | 91.8% |
| 30 | trait consistency | 100 | 324 | held | 92.3% |

The other 76 rules hold 1,643 findings (7.7%), mostly hand fixes of under 100 each.

**What this means for the plan:** at most about 10,900 findings are lint work in the narrow sense:
- script 6,328
- file renames 1,650
- false positives removed by narrowing rules 2,471
- test-local types (already counted under script)

The other 8,600 are the semantic pass (7,524) and the structure step (1,079). Their unit of work is a type or a module, not a finding.
