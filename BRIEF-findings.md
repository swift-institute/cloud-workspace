# Brief: fix the lint findings

Coen's decision, 7 Nov (coenttb/work#242): rule work has stopped. Now fix the findings in code, across the whole ecosystem, in this workspace. Read `CLAUDE.md` and the latest `## Closing` in `status-execute.md`. Attach `coenttb/work` and read #242, whose comments override this file. Nobody can answer you, and you can't message back.

## No measuring phase

The counts exist. Don't build a baseline or re-measure before you start fixing. Start from the latest lint output: `status-execute.md`'s closing and `overnight/execute-lint.json` (or whatever its closing names). Re-lint only the packages you changed, to see each batch's effect.

## Tools (all exist; read their headers)

- `./sync.sh`: clone and update, path-dependency manifests, root `Package.swift`.
- `overnight/lint-all.sh` and `count-lint.py`: lint every package, or those given, with a runner built in release from institute main, then count. Build the runner once from current institute main and reuse it: those are the latest rules. Also generate `/home/user/tools/swift-format.json` from `Institute.Source.Policy+swiftFormat.swift`.
- `overnight/apply-repairs.py`: the runner's own repair for one rule, only on files unchanged since linting. Use it only for repairs shown safe (`audit/rules.md` and `status-execute.md` name the broken ones).
- `overnight/rename-extension-files.py`, `test-display-names.py`, `apply-fixits.py`: mechanical fixes.
- `overnight/verify.sh`: one root-workspace build of every library product, then `--build-tests` for the packages given. The root build took about 2.5 minutes warm.
- `overnight/changed.sh`: checkouts with uncommitted changes or unpushed commits.
- `overnight/commit-round.py`: commit each changed checkout with a message built from the apply logs.

## Fast checks first

1. **Syntax:** `swiftc -parse <files>` on the changed files: no build, seconds.
2. **Lint:** the runner on the changed packages.
3. **Build:** the root build (`verify.sh` with `SKIP_ROOT` unset), which compiles every library against your changes.
4. **Tests:** `--build-tests` for the changed packages and their direct dependents. Work out dependents from the manifests once, as a small script in `overnight/`. **Never run tests** (`swift test` or a test binary): build them only. CI runs them after the final push.

## The loop

1. Pick the largest rule judged sound (verdict `keep`, or fixed today). Fix its findings across every package: by safe repair where one exists, by hand otherwise. Fix the cause, never suppress, unless it's a true false positive with a specific REASON. Make no behaviour or stored-format change: record any you'd need instead.
2. Run the fast checks above. Fix whatever breaks, downstream included, before moving on.
3. **Commit locally** in each changed repository, one commit per batch, with a message saying what changed and what was built (Linux x86_64, Swift 6.4.2; tests built, not run).
4. **Don't push to any package repository.** Every push goes out at the end, one per repository.
5. **Back up after every batch,** because this container can be lost: write `git format-patch origin/main` for each repository with local commits into `wip/<owner>__<name>/` on a branch `findings-wip` of this repository, and push that branch. It's one push to one repository, and it triggers no fleet CI. Never commit it to main.
6. Update `status-execute.md` on main: findings before and after the batch for that rule, and the total.

Then the next rule. Order: the largest sound rules first, then the mechanical ones (`extension file naming` renames, `test display name string`), then the rest. Naming and API rules the semantic pass will rewrite (`raw value access`, `int public parameter`, `compound identifier`, `compound type name`) go last, and only where the fix doesn't introduce a new type.

## The end

When most findings are fixed and the root build passes with tests built for every changed package:

1. One final lint of every package and `./ratchet.py` (limits only fall). Commit the new limits to institute main with the ratchet test passing, and write "publish wanted" in `status-execute.md`.
2. **Push every changed repository once,** tier by tier: atoms, molecules, standards, compositions, coenttb. Never force.
3. Read CI once, and fix anything red you caused.
4. Write `## Closing` in `status-execute.md` and comment on #242: findings before and after by rule, what remains and why, what's proven on which platform.

Don't stop when context runs low: it compacts automatically, and `status-execute.md` plus the `findings-wip` branch hold the state. Stop only when done, or for something that deletes or archives a repository, or a behaviour or stored-format change you can't avoid.
