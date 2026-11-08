# Pilot: one gated batch, predicted before the run (cancelled)

**Cancelled by Coen at about 10:35 UTC, before it ran.** Nothing was applied to or pushed to any package repository; the prediction below stays unmeasured. Found while preparing it: `swiftc -typecheck` passes broken ownership code (swift-linear), `-emit-sil -wmo` catches it in 0.6 s; the cold root build of main takes 578 s on 4 cores and stops at swift-linear.

Written and pushed at 10:15 UTC, 8 Nov (cloud-workspace 1f13121), before the pilot started. 

## Scope

**10 packages:**
- swift-iso-32000
- swift-sql
- swift-standard-library-extensions
- swift-algebra
- swift-w3c-css
- swift-w3c-xml
- swift-svg-render
- swift-posix
- swift-translating
- swift-parsers

They hold the most scriptable findings outside the repositories the pilot keeps out of:
- the 22 held by the checkpoint,
- the 31 with the broken `trait consistency` manifests,
- swift-linux-standard, swift-file-system, swift-layout and swift-memory-mapping (broken or duplicated declarations on main),
- institute.

Candidates in the 10 packages labelled `script`: about 1,465.

**8 rounds**, one per script, run by `overnight/gated-batch.py`:

| Round | Script |
|---|---|
| minimal | `minimal-bodies2.py`, which qualifies sibling names |
| suites | `compound-suites.py` |
| split | `split-types.py` |
| selectors | `module-selectors.py` |
| exports | `exports-file.py` |
| merge | `merge-extension-files.py` |
| loops | `counter-loops.py` |
| ifexpr | `if-expressions.py` |

**Gates, each applied to every change before it's committed:**
1. Declarations kept: a change's normalized declaration multiset doesn't change.
2. No rule rises in the change's files.
3. Every changed target type-checks, Sources and Tests, against the root build's modules.

Then for the whole batch:
1. swift-format on the changed files
2. `decl-diff.py` against origin/main: lost = 0 and duplicated = 0
3. ratchet check on a fresh lint
4. one incremental root build
5. push

## Prediction

| Quantity | Predicted | Basis |
|---|---|---|
| Findings fixed (all rules, net) | **850 ± 150** | candidates × (1 − last run's revert rate per method, lowered where the gate now rejects at apply time): minimal 420 × 0.6, suites 240 × 0.85, split 520 × 0.5, selectors 56 × 0.6, exports 45 × 0.9, merge 70 × 0.55, loops 40 × 0.8, ifexpr 10 |
| Changes reverted by the gates | 30–40% | merges and splits still raise other rules |
| Rounds (lint, apply, gate, type-check, commit) | 2–3 min each, **20 min** for 8 | lint of 10 packages takes seconds (all 438 took 59 s); type-check of about 30 targets, 4 at a time |
| swift-format, decl-diff, ratchet | 3 min | |
| Incremental root build | 10 min | unknown until measured; the cold build is running |
| Push of 10 repositories | 3 min | |
| **Wall clock** | **≈ 40 min** | |
| **Rate** | **≈ 1,300 fixed per hour** of wall clock, including the fixed costs | |

**Against the target.** The last day's rate was 681 per hour (11,444 in 16.8 h, held work included; 536 per hour on main alone). Three times that is 2,043 per hour.

- The pilot carries fixed costs that a full-workspace batch spreads over more findings: the root build, the push and the ratchet check.
- Rounds scale with the number of changed targets.
- So a full batch over all packages should land above the pilot's rate.

The plan's predicted rate is checked against the pilot's measured cost per finding (`plan.md`).
