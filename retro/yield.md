# Yield per method, findings work 7 Nov 16:34 – 8 Nov 09:22

## Where the numbers come from

- **Fixed on main:** the rule's count in `findings-start.json` (30,436, institute 9205733) minus its count in today's lint of origin/main after the checkpoint push. All 438 packages, same runner commit, 09:5x UTC: 21,439, so **8,997 fixed on main**. The session's own 11,444 also counts local work in the 22 held repositories (5,471 findings at start, unchanged on main).
- **Files touched / reverted:** the 2,734 package commits on `findings-wip`. Each revert commit's files are attributed to the method that last changed them (`tools/attrib.py`): 10,314 file paths touched, 3,253 reverted.
- **Lost or duplicated declarations:**
  - from the status file, for what the session found and reset;
  - `tools/decl-diff.py`, run today on all 379 pushed repositories (base = main before 7 Nov 16:00): **0 lost, 3 repositories with a type declared twice**.
- **False-positive rate:** the audit's 20-finding sample for the rule (`audit/rules-table.md`). It's the share of the method's edits that changed code for a finding that wasn't real.
- **Time:**
  - first mention of the script in the transcript to its last forward commit (wall clock; batches overlap);
  - agent-minutes, i.e. minutes in which the model issued a command naming the script. This is a lower bound: script writing was mostly done by subagents.

## By method

| Method | Rule(s) | Fixed on main | Files touched | Reverted | Lost / dup decl. | Rule FP (audit) | Window | Agent-min |
|---|---|---|---|---|---|---|---|---|
| `compound-suites.py` | compound suite name | **3,796** | 1,978 | 220 (11%) | 0 | 2/20 | 18:32–19:34, redone 02:27 | 13 |
| `merge-extension-files.py` + `own-type-files.py` + `where-file-names.py` | extension file naming | **1,733** | 4,302 | 1,854 (43%) | 3 lost: Magnitude, Size Codable; Interval Equatable/Hashable (reset) | 11/20 | 19:35–03:46 | 8 |
| `minimal-bodies.py` + runner repair | minimal type body | **963** (claimed ~2,370) | 840 | 534 (64%) | broke swift-linux-standard on Linux (pushed) | 2/20 | 22:34–03:17 | 8 |
| `exports-file.py` | exported import, architecture import boundary | **648** | 437 | 39 (9%) | 0 | 8/20, 9/20 | 02:39–02:40 | 3 |
| `suite-display-names.py`, `suite-drop-display.py` | test display name string | **487** | 209 | 2 (1%) | 0 | 0/20 | 18:28–02:26 | 4 |
| `split-types.py` | single type per file | **341** | 627 | 485 (77%) | 1 dup confirmed (swift-file-system), 2 candidates (swift-layout, swift-memory-mapping) | 3/20 | 22:34–03:06 | 3 |
| `test-function-names.py` | test function naming | **245** | 81 | 1 (1%) | 0 | 0/20 | 01:48–02:25 | 3 |
| runner repair (manifests) | trait consistency | 224, **not valid** | 38 | 1 | breaks resolution: 3 of 9 sampled consumers | 2/20 (repair judged "safe": wrong) | 03:24 | – |
| `private-compound-types.py`, `package-to-internal.py` | compound type name, compound identifier | **179** | 151 | 18 (12%) | 0 | 7/20, 8/20 | 03:27–03:32 | 5 |
| `counter-loops.py` + runner repair | counter loop iteration | **165** | 164 | 17 (10%) | 0 | 4/20 | 02:33–06:08 | 3 |
| `module-selectors.py` | module selector spelling | **138** | 37 | 15 (41%) | 0 | 0/20 | 02:43–03:06 | 3 |
| `if-expressions.py` | statement where expression fits | **98** | 102 | 6 (6%) | 0 | 0/20 | 02:35 | 3 |
| side effects | path name grammar +80, file name nested path +1 | −81 | | | | | | |
| `format-changed.py` | swift-format only | 0 | 1,181 | 5 | 0 | – | 07:42 | 2 |
| import fixes (`tc-fix.sh`, `dedupe-imports.py`) | none (repairs after moves) | 0 | 150 | 56 (37%) | 0 | – | 21:23–07:40 | 10 |
| **Total** | | **8,997** | 10,314 | 3,253 (32%) | | | | |

## Gates and verification (no findings fixed)

| Tool | Background minutes | Agent-min | Result |
|---|---|---|---|
| `build-revert.sh` (root build with tests, revert, repeat) | 444 (21 runs, longest 88) | 45 | never green; capped |
| `typecheck-tests.py` | – | 19 | missed errors (returned 0 on failure) |
| `typecheck-direct.py/.sh` | 64 | 15 | caught errors, but skips C-shim and macro targets |
| `ratchet-check.py` / `ratchet-revert.py` | 10 | 7 | 229 files reverted in 50 packages; −399 findings |
| `lost-declarations.sh` | – | 3 | found the Codable/Equatable losses at 07:30 |
| `push-checkpoint.sh` | 53 (08:29–09:22) | 36 | 379 pushed, 22 held |

## Why each revert happened

Files per method, by the reason in the revert commit's subject:

| Method | build / type-check | ratchet over limit | can't verify (macro, C shim) | wrong rewrite | lost content | other |
|---|---|---|---|---|---|---|
| merge-extension-files.py | 215 | **1,638** | 2 | – | 18 | 263 |
| split-types.py | 71 | **426** | 5 | – | – | – |
| minimal-bodies.py | 176 | 256 | **248** | – | – | 1 |
| compound-suites.py | 103 | 11 | – | **106** | – | – |
| runner repairs | – | 80 | 7 | – | – | 1 |
| fix-imports | 40 | 12 | 20 | – | 1 | – |

**Reading:**
- **Merges and splits** were mostly reverted because they *created findings of other rules*: `single type per file`, `path name grammar`, `file name nested path`. Nobody linted the touched files before committing.
- **Minimal-body moves** were reverted because they broke the type-check, or couldn't be type-checked.
- **Compound-suite moves** were reverted where they nested a suite under a namespace of its own name.

## What the numbers say

1. **Best value per minute:** small single-rule scripts written after the 02:17 `/clear`. Each was written, applied and committed in 2–5 minutes with ≤12% reverts:
   - `exports-file.py`, 648 fixed in about 2 min
   - `if-expressions.py`
   - `counter-loops.py`
   - `test-function-names.py`
   - `private-compound-types.py`

   Together: about 1,300 fixed, 02:33–03:32.
2. **Largest single yield:** `compound-suites.py`, 3,796 fixed, 11% reverts, though it took two rewrites to get right.
3. **Worst value:** merges and splits.
   - 4,929 file paths touched for 2,074 fixed on main.
   - 2,339 of those paths reverted (47%).
   - At least 3 declaration losses and 1–3 duplicates.
   - Most of the 444 build-loop minutes and all the ratchet reverts.
4. **Runner repairs** are not safe as a class: `minimal type body` and `trait consistency` both reached main broken today.
5. **False positives:**
   - Changing code for the five `exports-file`/`compound type name` rules (FP 35–45% in the audit) meant code edits for findings that weren't real. They were harmless here (moves of re-exports, `fileprivate`), but don't count as quality gains.
   - The best rules to fix in code are the 0–3/20 ones: suites, display names, test names, minimal bodies, if-expressions, module selectors, single type per file.
