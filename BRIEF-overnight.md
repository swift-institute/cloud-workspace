# Brief: the overnight session on the Mac, 9→10 Nov (coenttb/work#242)

You are the only session doing this work tonight, on Coen's Mac. Coen is asleep and hands-off: take your own decisions,
record them, and keep going. Nobody will answer questions before morning.

## What happened, and why you're on the Mac

The 9 Nov cloud session repaired every red the 9 Nov push caused (about 50 repositories, 27 issues closed), but it could
not run the one build of the whole ecosystem: on its 15 GB machine swift-build itself was killed for memory. It saved
everything it hadn't built as patches. Its handover is https://github.com/coenttb/work/issues/242#issuecomment-6745365354.
The Mac runs that build (see "Measured" below).

## Read first

1. This file.
2. `backlog-stashes/9-nov-cloud/ORDER.md`: the 65 patch sets to apply, in tiers and batches. This is your work list.
3. `backlog-stashes/9-nov-cloud/README.md`, and `fixes/<owner>__<name>.json` for each set when you get to it: its issue
   items, the API changes it makes, and the callers it knows about.
4. The `## On the Mac` section of `CLAUDE.md`.

## The loop

Folders: the real checkouts are under `~/Developer/coenttb/swift-institute` (`mac/checkout.sh owner/name` gives the
path); the ecosystem build folder is `E=/Users/coenttb/Developer/.claude/worktrees/ecosystem`. Fix only in the checkouts;
`repos/` in `$E` is overwritten by every sync.

For each batch in `ORDER.md`, in order:

1. In each checkout: `git pull --ff-only`. If the checkout is dirty or on another branch, another session is working
   there: skip that set, record it, and go on.
2. `git am -3 <cloud-workspace>/backlog-stashes/9-nov-cloud/<dir>/*.patch`. On a conflict, resolve it keeping both
   sides' intent; if that isn't clear, `git am --abort`, skip the set and record why.
3. For API changes (tiers B and C): fix every caller before building. Use the fix record's `dependents`, and grep
   `$E/repos` and `~/Developer/coenttb/swift-institute/institute` for each changed name. Commit the caller fixes in
   their own repositories.
4. Build: `W=$E mac/sync.sh` (only for the repositories you touched: pass them as arguments), then
   `W=$E mac/build.sh <Target> ...` for the changed modules and their dependents while you're fixing, and
   `W=$E mac/build.sh` (the whole ecosystem with tests) once, before pushing. Fix every error and rebuild until green.
   Search for every use of a changed API before rebuilding, rather than letting each build round find one break.
5. Lint the changed repositories (the `lint` skill: `institute ci -- source`) and keep every ratchet at or under its limit.
6. Push each repository in dependency order: `git push origin HEAD:main`, plain fast-forward. Never force. If a push
   is rejected because main moved, pull, rebuild what changed, push again.
7. Tick each fixed item in its issue with the SHA; close an issue once nothing in it is open. Also tick the 55 issues
   in `ticks-left.json` once their repositories are green in CI.
8. Post on #242: what was pushed (repository and SHA), what was skipped and why, what's next.
   Add the same to `status-execute.md` here and push it.
9. Read CI for that batch once, at the start of the next batch (don't wait for it). Fix any red the batch caused
   before starting new sets.

## Rules

- **One session, in order.** No fix branches and no parallel fix agents on branches. If you use agents, at most 3,
  each editing different checkouts directly, and only for caller fixes within the current batch.
- **Pull before you fix, and expect other pushes.** Other Mac sessions may push to Institute repositories. If one
  already fixed what a set fixes, keep theirs, drop yours, and record it.
- **A push every 90 minutes.** If two hours pass without one, write in `status-execute.md` why, then make the batch
  smaller: split it until something can go out.
- **Stop conditions.** Stop and write a handover on #242 if: a whole-ecosystem build can't finish twice in a row; the Mac
  starts swapping heavily (`sysctl vm.swapusage` used > 8 GB); or the same break defeats you for an hour (record it,
  skip that set, continue with the next).
- **Toolchain bugs** go to swift-institute/Issues (swift-slot-map's Windows crash is already #224). Don't work around them.
- **Out of scope tonight:** the three held-back lint sets (`ORDER.md`, "Not applied"), and Quality · source reds that
  were red before 9 Nov.
- Pushing to Institute and coenttb repositories is a standing yes. Never force-push. Never push to pointfreeco/TCA26.
  Work on main only. Never touch `~/Library/Application Support/Laurie`.
- Every green you report says what it covers: the Mac build is macOS only; Linux and Windows come from `ci.yml`.

## When the list is done

Then, if time remains, #242's done criteria:
1. **Criterion 4:** one fleet CI read, green on macOS, Linux and Windows, with SHAs.
2. **Criterion 5:** a fresh fleet lint, and a new issue tracking the remaining findings by rule. That includes the three
   held-back lint sets and the reds that predate 9 Nov.

If both hold, close #242.

## In the morning

Post a comment on #242 headed **Overnight result**. Include:
- the counts: sets pushed, skipped and left;
- issues closed;
- CI per platform;
- every decision you took;
- what remains, in the order you would do it.

## Measured

On 9 Nov at about 17:15Z, from origin/main of every Institute repository at about 16:45Z, macOS 27.2, Swift 6.4.2, 8 cores,
24 GB, with other sessions running alongside:

- **Cold whole-ecosystem build with tests:** 21 minutes. swift-build peaked at 6.5 GB resident; swap didn't grow. It
  found one error: swift-tensor's tests call a `package`-scoped initializer, which the generated root package can't see.
  That's a quirk of the combined build, not a break: CI is green on main, and cloud-workspace's
  `overnight/tests-fallback.txt` already lists those tests.
- **Warm rebuild:** green, 0 errors, 5.5 minutes. That's the baseline: **everything builds together at current main**,
  so any error tonight comes from tonight's changes.
- The build cache in `$E/.build` is warm. Keep the flags in `mac/build.sh` as they are: changing them rebuilds everything.
- `$E/generate.py`, `$E/localize.py` and `$E/overnight/tests-fallback.txt` are links to this repository's files, so there's
  one copy of each. A test target that only fails in the root package (`package` access, a trait the root doesn't
  enable) goes on `overnight/tests-fallback.txt` here, with a commit saying why.
