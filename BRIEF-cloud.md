# Brief: one cloud session for the backlog and #242

From 9 Nov, one cloud session owns this work. It replaces two local sessions on Coen's Mac: the #242 coordinator
and the issue backlog session (coenttb/issues), which used too many of the Mac's resources. Coen is hands-off: take your own
decisions, record them on coenttb/work#242, and stop for him only where `BRIEF-execute.md` says to.

## Read first, in this order

1. `CLAUDE.md` here: how the workspace builds, and the push rules.
2. On coenttb/work#242, the two newest comments headed **Handover**: the last local push (SHAs, CI result, what was held
   back and why, open issue items) and the coordinator's list of what remains. They override this file.
3. `BRIEF-execute.md` and `status-execute.md` (its `## Closing`) for the order of the #242 work, and
   `retro/remaining.md` for the remaining findings by fix method.

## Method

The whole ecosystem builds as one package here (`./sync.sh`, then `swift build --build-tests`), so every edit is seen
by everything that depends on it. Use that for every batch:

1. Fix in `repos/<owner>/<name>`, and commit there.
2. After each batch, rebuild the **whole** ecosystem with tests and run the fleet lint and `overnight/ratchet-check.py`
   before pushing anything. Don't build packages one by one against GitHub: they can't see each other's unpushed
   changes, which is how one API change (swift-cardinal) turned half a layer red.
3. Push the batch in dependency order, read CI once, record counts and SHAs in `status-execute.md` on main.

This is Linux only. Apple-only code is checked by `ci.yml` after the push; say so for every green.

## Work, in order

1. The CI reds from the last local push, from the Handover comment. Never leave a repository red that a push made red.
2. The issue items the last fix run left open that don't need Coen. Fix them in the same batches, and close each issue
   with the fixing SHA after its push is green.
3. #242 in the order of `status-execute.md`'s `## Closing`: rule fixes, structure, semantic pass, remaining lint.

## Done

After each batch, a comment on #242: what was pushed, CI per platform, what remains and why. Nobody can read this
session or answer it: anything that matters goes on main here or on the issue.
