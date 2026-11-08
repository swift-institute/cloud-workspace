# Plan for the remaining findings

The goal is to fix the remaining findings at least 3× faster than the last day. The last day ran 681 per hour, counting the held work (11,444 in 16.8 h); on main alone it was 536 per hour. Three times 681 is **2,043 per hour**.

Rates below are checked against the pilot (`pilot.md`): predicted first, then measured.

## Decisions

Each decision has a recommendation.

### 1. Repair main before anything else

The checkpoint push left these broken on main. All were found today: by resolving and building origin/main on Linux, and by `decl-diff.py`.

- **31 manifests** with the `trait consistency` repair. Consumers fail resolution: institute, swift-json, swift-linter, 3 of 9 sampled.
- **swift-linux-standard:** minimal-body moves lost sibling scope (`Flags`, `Opcode`, `Options`).
- **swift-linear:** `counter-loops.py` captured `borrowing` parameters in closures. It's an ownership error, invisible to `-typecheck`.
- **swift-file-system:** `File.Link.Target` declared twice (a split, then a revert).
- **swift-layout, swift-memory-mapping:** probably the same duplicate pattern.
- Whatever else the full root build lists in `data/pushed-breaks.txt`.

**Recommend:** one short session (about 1 h), before any new batch:
1. Revert the manifest part of the 31 trait commits.
2. Fix or reset the listed targets through the gated driver, with the new gate.
3. Push.
4. Re-read CI.

It also unlocks the 2,894 scriptable findings that sit in these repositories and the held ones.

### 2. The gate is SIL, not type-check

`swiftc -typecheck` passed swift-linear while it's broken. `-emit-sil -wmo` reports its 34 errors in 0.6 s.

**Recommend:**
- Every change is compiled to SIL against a root build of main, Sources and Tests.
- A target with no result (C shims, macros, timeout) is **held**, not passed.
- Apply the same rule to "can't verify" everywhere.

### 3. Every change is a transaction, gated before it's committed

`overnight/gated-batch.py` (built and used in the pilot):
1. Groups the changed files that exchanged declarations: a merge, split or move is one transaction.
2. Reverts a transaction whole if any of these hold:
   - its declarations aren't kept,
   - any rule rises in its files,
   - its rule doesn't fall,
   - its target fails SIL.
3. Commits per package.

There's no build loop and no revert-by-file.

**Recommend:** all scripted work goes through it. Retire `build-revert.sh`, `ratchet-revert.py` and `tc-fix.sh`.

### 4. Order

| Step | Findings | Lane |
|---|---|---|
| a. Repair main (decision 1) | – (unlocks 2,894) | A |
| b. Scripted rules, largest first: minimal type body v2 (2,412), compound suite name (934), single type per file (775), test-local compound type names (382), merges (382), exports (432), counter loops (322, after the `borrowing` fix), selectors (147), test names (115), base-type splits (176) | 6,328 | A |
| c. File renames: path name grammar file segments (1,267), extension file naming shape (240), file name nested path (143) | 1,650 | A |
| d. Narrow the rules the audit found mostly false, in a separate session (counts only fall): namespace adoption typealias, typealiased namespace bridge, try optional, chained rawvalue access, unification typealias, throwing wrapper init, untyped throws in Tests, existential parameter | 2,471 | R, parallel to A |
| e. Public type renames with callers (429), hand fixes (1,745) | 2,174 | A, later |
| f. Structure step: module renames (1,079) | 1,079 | separate step |
| g. Semantic pass: new types (7,524) | 7,524 | separate step, measured in types, not findings |

**Recommend:** a–d now (about 10,900 findings), e after, f and g as their own steps with their own targets. A finding there costs a type or a module, so a findings-per-hour target doesn't fit them.

### 5. Tools to build or fix first

| Tool | State | Measured |
|---|---|---|
| `overnight/lint-par.sh`: all packages linted 4 at a time | **built** | all 438 in 59 s (the sequential lint took about 12 min) |
| `overnight/gated-batch.py`: transactional gate and driver | **built** | pilot |
| `overnight/minimal-bodies2.py`: nested moves qualify sibling names | **built** | pilot |
| `overnight/swift-format-config.py`: the format configuration from the policy file (a new container lacked it) | **built** | – |
| `overnight/untrait-local.sh`: workspace resolves despite the trait manifests (working tree only) | **built** | – |
| `retro/tools/decl-diff.py`: lost and duplicated declarations against any base | **built** | 379 repositories in 5 s |
| Root build as module cache, once per batch, incremental | exists | cold 578 s; incremental: pilot |
| `counter-loops.py`: skip loops whose body uses a `borrowing`, `consuming` or `~Copyable` value | **to fix** | – |
| `split-types.py`, `merge-extension-files.py`: name new files so `path name grammar` and `file name nested path` don't rise | **to fix** | the main cause of reverts (1,638 + 426 files) |
| institute test: the source profile's rules equal the runner inventory | **to add** | would have saved the two refused publishes |
| generated root test package that builds green | partly: 672 test targets plan in the root, but it was never green | replaced by SIL per changed test target |

### 6. Session design

The aim is to keep one cloud session working through a long sequence without restarts or idle time.

1. **One driver per batch, in the background.** Run `gated-batch.py <rounds> <packages>` with `run_in_background`. The session is woken by the completion notice, never by polling. No foreground command runs over 10 minutes.
2. **Context stays small.** Each step prints one line. The model reads `log.jsonl`'s summary lines, never build logs; it reads the last 20 lines of a log only on failure.
3. **State goes in files after every batch:** `status-execute.md` on main, a `findings-wip` backup, `log.jsonl`. A restart costs minutes, not an hour of re-onboarding (A's restarts cost 9–12 min each to the first commit, plus 94 and 110 min waiting for `/clear`).
4. **No idle gaps.**
   - The session ends a turn only when the plan is done.
   - A `send_later` every 20 min wakes it if a turn ended anyway.
   - These replace the coordinator's half-hourly nudges: F had 12 of them and 147 idle minutes.
5. **Effort:** high for writing or changing a script, low for driving batches. F ran at low effort throughout, and its scripts needed 2–3 rewrites.
6. **Rules in a separate short session**, running in parallel. Narrowings only lower counts, so they never invalidate the lane's work.
7. **Usage limit:** F lost 54 min to the weekly limit. Check the limit before a long run, and plan a batch boundary at the reset time.

### 7. Predicted rate and finish time

Not measured: the pilot was cancelled (Coen, 8 Nov). The only measured costs: lint of all packages 59 s; root build of main cold 578 s plus 2–3 min of planning per incremental round; SIL check of one target 0.6 s (swift-linear). The predicted pilot rate (about 1,300 per hour including fixed costs, `pilot.md`) is untested.

### 8. Pushing and CI

**Recommend:**
- Push after each batch that passes its gates, tier order, plain fast-forward.
- Read CI once, through a subagent that returns a per-repository summary.
- Before trusting a green, confirm that the Build jobs ran and that consumers resolve.

### 9. The 22 held repositories

**Recommend:**
- Rebase their local work onto main through the gated driver: each change re-gated, the rest dropped.
- For the 4 ratchet holds over the limit on main already (institute, swift-linter-rules), regenerate the limits after repair (decision 1). Don't raise any.
