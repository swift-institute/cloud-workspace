# Root causes, five whys each

Evidence is in `timeline.md`, `yield.md` and the session transcripts.

## 1. Session stalls and restarts: 478 minutes of 2,256 (21%)

| What | Minutes |
|---|---|
| Idle between turns: a turn ended and the session waited for a coordinator nudge | 221 (B 73, F 147, A 1) |
| Idle waiting for a `/clear` after context ran low (A, 11:10–12:44 and 14:13–16:02) | 203 |
| Weekly usage limit (F, 04:04–05:02) | 54 |

There were four worker restarts in F, and B's 8-hour turn was killed (exit 137) at 04:05.

1. **Why did sessions sit idle?** They ended their turn after a batch or a long wait, and nothing restarted them until the coordinator's half-hourly "Resume…". F alone got 12 such nudges.
2. **Why did they end the turn?** Long jobs ran as foreground polls, each capped at 10 minutes, or as background jobs watched by a Monitor capped at 30 minutes. When a wait ran out, the model wrote a summary and stopped instead of re-arming the wait.
3. **Why did A need `/clear` twice?** It read whole briefs, rule sources, test output and logs into context. It ran low after 1.5 hours (11:10) and again after 1.3 hours (14:13). The session couldn't message the coordinator (`elevated_session_untrusted_device`), so it waited for Coen to clear it.
4. **Why was context so expensive?** A loop of edit, run tests, read the failure, edit again keeps every output in context. Nothing wrote state to a file and dropped it from context.
5. **Why no protection?** The briefs say "keep context small" and "don't stop", but nothing enforces either. No driver script runs the long sequence, so the model itself has to be awake through every step.

**Fix:**
- Long sequences run as one background driver script. It writes progress to a file and exits with a code. The model is woken by its completion notice, not by polling.
- Every step's output goes to a log; the model reads a summary line.
- After every batch, state goes to `status-execute.md` and the session continues without ending its turn.
- A scheduled wake-up (`send_later`) every 20 minutes catches a stopped turn, instead of a human nudge.

## 2. The rejected publishes: about 3.5 hours of publish lead time, no session time

Publish wanted at 11:10 (2a07c96); adopted at 15:11 (f442690). In between, the publishes of 2a07c96 (57 min) and c8f123c (49 min) ran on free macOS runners, and the Mac canary refused them.

1. **Why refused?** The source profile, `Institute.Source.Policy+linterRules.swift`, still named the 6 rules the runner no longer had.
2. **Why still named?** The session left the profile alone on purpose and wrote "the adoption must drop the 6 removed rule ids" in the status file. The coordinator's first publishes didn't do that.
3. **Why didn't a test catch it before the push?** Only the canary, on the Mac after a 15–57-minute publish, compares the profile with the runner's own inventory. institute's `swift test` doesn't.
4. **Why does a 15–57-minute publish sit in that loop?** Coen ruled that publishes use only free hosted macOS runners and go out in batches. That's right for cost, but it makes every wrong publish cost an hour.
5. **Why did it not hurt more?** A built its own runners locally (debug at 10:00 and 10:44, release at 16:26), so the findings work never waited on a publish. The cost fell on the coordinator.

**Fix:**
- Add an institute unit test that checks the profile's rule list equals the runner inventory, and run it before every institute push.
- Push rule commits in one batch, so CI isn't cancelled 14 times in a row (13:14–14:28).

## 3. Lost declarations from merges

Found at 07:30 on 8 Nov, at the end of the run:

| Package | What was lost |
|---|---|
| swift-magnitude, swift-size | Codable conformances |
| swift-interval | Equatable and Hashable |
| swift-email | the Email Received files |
| 32 macro targets | reset to main, because they couldn't be checked |

**New today:** swift-file-system was pushed with `File.Link.Target` declared twice. A split added `File.Link.Target.swift`, then a ratchet revert at 04:03 put `File.swift` back with the type still inside.

1. **Why lost?** A merge is a two-file change: it appends B's declarations to A, then deletes B. A split is the reverse. The reverts worked per file. Restoring A without B, or A without removing the split file, loses or duplicates declarations.
2. **Why per file?** `build-revert.sh`, `ratchet-revert.py` and `tc-fix.sh` each pick files from an error list or a rule count. None of them knows which files moved together.
3. **Why were there so many reverts?** 3,253 of the 10,314 file paths the scripts touched were reverted later. 1,638 of those reverts came from merges that raised another rule over its ratchet limit.
4. **Why was the ratchet hit so often?** A merge or split creates findings of other rules (`single type per file`, `path name grammar`, `file name nested path`), and nobody linted those files before committing.
5. **Why found only at the end?** `lost-declarations.sh` was written at 07:30 on 8 Nov. No script checked its own output's declarations when it wrote it.

**Fix:**
- Every rewriting script records each move as one transaction (source files, target files, the declaration set before and after).
- A move commits only if the declaration multiset is equal before and after, and if a lint of the touched files raises no rule.
- Reverts undo whole transactions, never single files.

## 4. Broken repairs

These repairs broke the build on real code:

- **`minimal type body`:**
  - `package` members moved into extensions of an internal type
  - sibling names out of scope (swift-algebra; today swift-linux-standard, pushed)
  - `~Copyable` dropped
- **`counter loop iteration`:** a `~Escapable` local captured in a closure
- **`module selector spelling`:** a module with a type of its own name
- **`swift protocol qualification`:** inside macro-attributed declarations
- **`trait consistency`:** re-adds conditions SwiftPM can't resolve transitively. Pushed today; 3 of 9 sampled consumers fail resolution.

1. **Why broken?** Each repair is a syntax rewrite checked against fixtures. Name lookup, access levels, `~Copyable` and the resolver's trait rules are semantic.
2. **Why didn't the fixtures cover them?** They're written from the rule's description, not drawn from the corpus that's going to be rewritten.
3. **Why were they applied fleet-wide anyway?** Overnight, then again in batches 5 and 18, the repair was treated as safe once the audit's named defects were fixed. Each new defect showed up only in a build.
4. **Why did a known-bad pattern reach main again?** Batch 10's minimal-body moves in swift-linux-standard sit in `#if os(Linux)` code in a package with C shims. `typecheck-direct` skips targets with C shims as "uncheckable", and the capped root build never went green. So the push gate had no evidence for that target, and pushed it anyway. swift-parser's 29 Oct revert explains exactly why its trait conditions can't be used, but no tool reads commit history before re-applying a repair.
5. **Why no evidence gate?** "Pushed" was decided per repository from 4 gates. "Type-check couldn't run" counted as a pass, not as "hold".

**Fix:**
- **Repair acceptance:** a repair is enabled fleet-wide only after it's applied to every finding in a sample of 20 packages and those packages type-check, including C-shim and macro targets through a real build.
- **Push gate:** a target with no type-check evidence is held, not passed.
- **Manifests:** manifest repairs are off until the resolver question is settled. Every manifest change gets a `swift package resolve` of its direct consumers.

## 5. The 9-minute build-per-error loop: 444 background minutes in F

1. **Why 9 minutes per error?** `build-revert.sh` ran a full root build with tests (`-j 3`) to find errors. It reverted the files named, then built again.
2. **Why one error, or a few, per round?** SwiftPM stops building a target's dependents when the target fails. Errors downstream of a broken module appear only after it's fixed, one layer per round.
3. **Why use the root build to find errors?** The type-check tools came late. `typecheck-tests.py` returned 0 where the same command failed (cause not found), and `typecheck-direct` came at 02:12. Even then the loop kept running as the final gate: 21 runs, longest 88 min.
4. **Why does the root build take that long?** About 7,800 steps on 4 cores. After file moves, many modules recompile. And the 05:05 run stalled an hour in resolution, because a revert restored a committed manifest without re-localizing it.
5. **Why no cache of good modules?** Nobody built origin/main's modules once to type-check each changed target against them in parallel. That would have shown every error at once.

**Fix:**
- Build origin/main once into a module cache.
- Type-check every changed target against it in parallel, so all errors show in one pass. Measured in the pilot.
- Fix or revert whole transactions.
- Run one root build at the end as confirmation.
- Never revert in a build loop.

## 6. Rule work took a day instead of hours

From the overnight close at 08:13 to "rule work stops here" at 16:23 is 8.2 hours. A spent 158 minutes working; the 22 narrowings of its second stretch took about 3 minutes each (12:56–14:12).

1. **Why a day?**
   - 203 minutes idle waiting for `/clear`.
   - 100 minutes of builds and verify, 79 of them a duplicated `verify.sh` that was killed with no result.
   - The rest went to briefs and onboarding after each restart: A's first commit after each `/clear` came 12 minutes (12:44 → 12:56) and 9 minutes (16:05 → 16:14) later.
2. **Why the restarts?** Context, as in cause 1.
3. **Why did rule work and findings work run in sequence in one session?** The order in #242 put rules before lint.
4. **Why not parallel?** Rule commits change the runner, so the fixes would chase a moving count. But narrowings only lower counts, so a parallel findings session would have lost nothing.
5. **Why wasn't that seen?** Nobody predicted the step's time before starting. Coen's "no step over 20 minutes" rule came at 19:00, after the day was spent.

**Fix:** rule narrowings (counts only fall) run in their own short session, in parallel with findings work. Each session predicts its step time before starting, and re-plans when it's 50% over.

## Also found

- **Rates were measured on the wrong denominator.** The 12,338 headline came from linting the changed packages only. After the gates it was 11,444 (−894). Measure only on the gated state.
- **The status file's times drift up to 2.5 hours** from commit times ("10:30 UTC" written at 08:04). Times come from `date -u` or commits only.
- **The findings session ran at effort level `low`** (session record). Given how many scripts needed two or three revisions (`compound-suites.py` alone had 3), a higher effort for writing scripts, and low effort only for driving them, is worth testing.
