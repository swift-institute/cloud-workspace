# Brief: rule fixes, structure and semantic pass

Coen approved all six checkpoint decisions on 7 Nov (coenttb/work#242, read its comments: they override this file). Read `CLAUDE.md`, `BRIEF-cleanup.md` (limits and evidence rules still apply), `audit/README.md`, `audit/rules.md`. Run `./sync.sh`. Take your own decisions and record them on #242. Nobody can answer you and you can't message back.

Already done by the coordinator: the 9 molecules are archived (axis-dimension, complex-dimension, geometry-boundary, geometry-pair, module, symmetry-finite, symmetry-linear, symmetry-pair, version-carrier). Remove them from `repos.txt` and from anything that names them. The ratchet is in `institute` (`Institute.CI.Command.Source.Ratchet`); limits regenerate with `./ratchet.py`, which refuses a rise in a rule's total unless the rule changed in the same commit (`--allow-rise`). The coordinator publishes runners and adopts them on the Mac: push institute commits and write in `status-execute.md` when a publish is wanted.

## Continuing

A first session stopped when its context ran out: read `status-execute.md` (its `## Closing` lists what remains, in order) and continue from there. Keep each session's context small: work in batches, write to `status-execute.md` after each, and don't read whole logs into context.

## Order

1. **Rule fixes** (institute and swift-linter-rules): the 60 faulty rules, removing the 5, `compound suite name` accepting #239's layout, removing `fully qualified error in typed throws`, `blocking call in async`'s `wait(...)` case. Each fix has a test shown to fail without it. Then add the new rules from the checkpoint in its order, each as: write, count, sweep to zero, make an error. Regenerate the ratchet after rule changes.
2. **Structure:** fold symmetry-algebra into swift-algebra as the pilot; Core renames (`X Macro Core` → `X Macro Derivation`, `X Core` merged into its umbrella); the 11 atom→molecule edges; unused dependencies and re-export reliance. Before the first batch, try putting every test target into one generated root package so a whole-ecosystem rebuild plans once (#242); if it fails, rebuild changed packages and their dependents per batch, and run a full per-package pass at the end of the step.
3. **Semantic pass** to the approved target (about 1,100 wrappers, 11,600 types): plain and duplicate wrappers first, then own-behaviour ones, atoms upward. Encoding wrappers only where no stored data depends on their coding; record each one you skip.
4. **Remaining lint**, then rules become errors one by one.

Each batch: rebuild and re-lint the whole ecosystem before pushing, push, read CI once, update `status-execute.md` on main with counts and SHAs. Never leave a repository red you made red. Stop for Coen only for something that deletes or archives a repository, or a behaviour or stored-format change you can't avoid.

## Done

`## Closing` in `status-execute.md` and a comment on #242: types and wrappers before and after, findings before and after by rule, what remains and why, what is proven on which platform. Keep it short.
