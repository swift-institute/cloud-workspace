# Retrospective, lint and findings work, 6–8 Nov (coenttb/work#242)

Scope cut by Coen, 8 Nov, about 10:35 UTC: no new measurements and no pilot. This page holds:

1. the remaining findings by fix method,
2. the order to tackle them,
3. the top three mistakes and how the next round avoids each.

**Detail behind this page:**

| File | What |
|---|---|
| `timeline.md` | 2,256 minutes, 6 Nov 19:46 → 8 Nov 09:22, from the three session transcripts |
| `yield.md` | per script: fixed, reverted, lost declarations |
| `root-causes.md` | five whys for each of six causes |
| `remaining.md` | Pareto by rule |
| `plan.md` | the full plan; its rate was not measured, because the pilot was cancelled |
| `data/` | the data behind these files |
| `tools/` | the scripts that made it |

## The numbers this rests on

- **Start:** 30,436 findings (`overnight/findings-start.json`).
- **Now:** 21,439 on main, by one lint of all 438 packages with the same runner after the checkpoint push. That's **8,997 fixed on main**.
- **With the held repositories:** 18,992. That figure includes the 22 held repositories' local work, which isn't on main (they hold 5,471 findings there).
- **Last day's rate:** 681 findings per hour (11,444 in 16.8 h, held work included), or 536 per hour on main alone.

## 1. Remaining findings by fix method

21,439 on main. Labels by rule and message, from `tools/label-remaining.py`; per-rule detail is in `remaining.md`.

| Fix method | Findings | What's in it |
|---|---|---|
| **Script** | **7,997** | minimal type body, nested one level (2,412) · file renames for path name grammar, extension file naming and file name nested path (1,669) · compound suite name (934) · single type per file without `#if` or private types (775) · exported import and architecture import boundary (432) · test-local compound type names (382) · extension merges (382) · counter loop iteration (322) · base-type file splits (176) · module selector spelling (147) · test function naming (115) · small mechanical rules (251) |
| **Needs a rule change** | **2,571** | rules the audit sampled as ≥ 70% false: namespace adoption typealias (606), typealiased namespace bridge (465), try optional (415), unification typealias (252), chained rawvalue access (188), existential parameter (154), throwing wrapper init (152) · untyped throws in Tests (239) · trait consistency (100): its repair breaks resolution, so the rule or repair must change |
| **Hand** | **10,871** | semantic pass, new types: compound identifier, int/bool public parameter, raw value access, untyped throws in Sources, unchecked call site … (7,524) · structure step, module renames: target directories, test target and manifest naming (1,079) · public type renames with callers (429) · `#if` files, private types, `do throws for typed catch`, small rules (1,745) · canonical settings tail, a behaviour change (94) |

**Blocked until main is repaired:** 2,894 of the script findings sit in repositories that are held or broken on main. Those are the 22 held, the 31 with trait-repaired manifests, and the 5 below.

## 2. Order

0. **Repair main first.** The checkpoint push left breaks. Found today on Linux by resolving and building origin/main, and by comparing declarations with main before 7 Nov 16:00:
   - **31 manifests** carry the `trait consistency` repair. 652ba46 in swift-parser reverted exactly that on 29 Oct. Consumers fail to resolve: institute, swift-json and swift-linter, 3 of 9 sampled.
   - **swift-linux-standard:** minimal-body moves lost sibling scope (`Flags`, `Opcode`, `Options`).
   - **swift-linear:** `counter-loops.py` captures `borrowing` parameters in closures.
   - **swift-file-system:** `File.Link.Target` declared twice.
   - **swift-layout, swift-memory-mapping:** likely duplicate declarations.

   The full root build was stopped before it finished, so more may exist. Fix these, push, re-read CI.
1. **Rule changes, 2,571, in their own short session, parallel to the next step.** Narrowings only lower counts, so they never undo script work. Each change needs a test that fails without it, as before. Fix the `trait consistency` repair, or remove it.
2. **Scripts, 7,997, largest first, through a gated driver:**
   1. minimal type body, with qualified sibling names (2,412)
   2. compound suite name (934)
   3. file renames (1,669): they carry no compile risk
   4. single type per file (775) and merges (382), only once they no longer create `path name grammar` / `file name nested path` findings
   5. exports (432)
   6. test-local compound type names (382)
   7. counter loops (322), only after the `borrowing` fix
   8. selectors, test names, base-type splits
3. **Hand fixes, 2,268:** `#if`, private types, typed catches, public renames, small rules. By rule, in batches.
4. **Structure step (1,079) and semantic pass (7,524)** as their own steps, with targets counted in modules and types, not findings.

## 3. Top three mistakes, and how the next round avoids each

**1. The gate couldn't see what broke, and "couldn't check" counted as a pass.**

What happened:
- `swiftc -typecheck` passed swift-linear while it's broken: ownership errors only appear at SIL. `-emit-sil -wmo` shows its 34 errors in 0.6 s.
- `typecheck-direct` skipped targets with C shims or macros, so swift-linux-standard went out unverified.
- The root build loop never went green.
- The `trait consistency` repair was re-applied to 31 manifests without resolving a single consumer, although swift-parser's history explains why it fails.

*Next round:*
- Every change is compiled to SIL against a root build of main, Sources and Tests, before it's committed.
- A target with no result is **held**, never passed.
- Every manifest change is followed by `swift package resolve` of its direct consumers.

**2. Multi-file changes were made and undone file by file, and scripts created findings in other rules.**

What happened:
- 3,253 of 10,314 changed file paths (32%) were reverted later. Merges lost 55%, splits 77% and minimal-body moves 68% of the paths they touched.
- Most merge and split reverts were ratchet reverts: the new files raised `single type per file`, `path name grammar` or `file name nested path`.
- Per-file reverts of two-file moves lost Codable, Equatable and Hashable conformances (swift-magnitude, swift-size, swift-interval). They also left a duplicate type on main (swift-file-system).
- 894 fixes were reverted in the 4.6 hours of gates after the 12,338 peak.
- `build-revert.sh` used 444 background minutes finding one layer of errors per 9-minute build.

*Next round:*
- Each move, merge or split is one transaction. Before it's committed:
  - its declaration multiset must be unchanged,
  - a lint of its files must show no rule rising,
  - it must pass the SIL check.
- If any check fails, the whole transaction is reverted.
- No build loop and no revert by file.
- The lint of all packages now takes 59 s with 4 parallel jobs (`overnight/lint-par.sh`), so this check costs seconds.

**3. Sessions stopped and sat idle: 478 of the 2,256 minutes (21%).**

| Where | What | Minutes |
|---|---|---|
| A | context ran out twice; waited for a `/clear` | 94 + 110 |
| B, F | turns ended; waited for the coordinator's half-hourly nudge (F had 12 of them) | 221 |
| F | weekly usage limit | 54 |

Builds ran with the model waiting for another 784 minutes. Rule work took 8.2 hours for about 2.6 hours of session work.

*Next round:*
- **One background driver per batch.** The session is woken by its completion, never by polling or a 10-minute foreground wait.
- **Context stays small.** Each step writes a one-line summary to a file; the session reads summaries, not logs.
- **State on main after every batch,** so a restart costs minutes.
- **A `send_later` every 20 minutes** replaces the human nudge.
- **Rule work in its own short session,** in parallel.
- **The usage limit** is checked before a long run.

## Also

- The status file's written times drifted up to 2.5 hours from its commit times. Use `date -u` or commit times.
- The findings session ran at effort `low`. Its scripts needed 2–3 rewrites. Use higher effort to write a script, low to drive it.
- **New tools from this retro, not yet used for fixes:**

  | Tool | State |
  |---|---|
  | `overnight/lint-par.sh` | measured |
  | `overnight/swift-format-config.py` | used |
  | `overnight/untrait-local.sh` | used |
  | `retro/tools/decl-diff.py` | used |
  | `overnight/gated-batch.py` | untested: the pilot was cancelled |
  | `overnight/minimal-bodies2.py` | dry-run only |
