# Brief: ecosystem audit and rule triage

Coen's decisions, 7 Nov: coenttb/work#242 (attach `coenttb/work` and read it first; its comments override this file). The order is ratchet, audit, rule triage, structure, semantic pass, remaining lint. **This session does the audit and rule triage, then stops at one checkpoint.** A coordinator session on Coen's Mac does the ratchet, runner publishing and canaries.

Coen's aim: the ecosystem says what its values mean by reusing shared semantic types, with significantly fewer declared newtypes and `swift-tagged` by default, and refactoring is accepted to get there. He also wants molecules assessed for folding into atoms with traits, unused or low-value types found, `Core` removed from module names, and linter rules that enforce all of it. He can't list everything, so **finding what nobody has named yet is part of the job.**

Read `CLAUDE.md`, `status.md`, `status-overnight.md`. Run `./sync.sh`. Create the git-ignored `private-repos.txt` as `BRIEF.md` step 5 describes. Coen is hands-off: take your own decisions and record them.

## Before you start

`status-overnight.md` on main must contain `## Closing`. If it doesn't, wait and check every 15 minutes: nothing edits repositories alongside that session. The coordinator confirms this before starting you, so it should already be there.

## Limits

- **The audit changes no package.** Output goes to `audit/` in this repository, on main. Triage may change `institute`'s rules (below).
- **This repository is public, and 7 of the packages aren't.** Don't put private packages' type names or source in `audit/`. Give counts here, and put names on coenttb/work#242.
- The Mac packages and Rule Institute aren't in this workspace. Don't call anything unused on your own evidence: label it "no consumer in the workspace". The coordinator checks those lists on the Mac.
- Pin everything to one set of SHAs and record them. Run the counting command before quoting a number. Work statically where you can; disk is limited, and builds are only for proving a specific claim.
- Standing rules: never force, never pointfreeco/TCA26, no issues or PRs on swiftlang/swift-package-manager, don't change swift-windows-32's names, never open personal data or `*.local.json`, test data is invented.
- Don't run things in parallel on shared temporary files.
- Don't delete, archive or create a repository.

## Part 1: audit

Parse with swift-syntax, not grep, so results don't depend on names. Commit the scripts to `audit/`, and the data as JSON so it can be re-measured after each later step.

1. **Declared types:** every struct, enum, class, actor, protocol and typealias: package, tier, module, access, generic or not, stored fields, conformances, file and line, test or non-test. This is the baseline: declared types overall, and by tier.
2. **Reference graph:** for each public declaration, which packages and targets refer to it, with non-test and test uses counted apart. Token matching may overcount, which is the safe direction for deletion. Prove a sample by removing the declaration and building.
3. **Wrappers:** every struct with one stored field, plus enums with one payload case and classes doing the same job. Sort each into one of these:
   - **Plain:** becomes `Tagged<X, Y>`.
   - **Validates:** `Tagged` decodes and takes literals through `_unchecked`, so its check would be lost. Propose what to do, not just "keep".
   - **Own behaviour:** real members beyond forwarding.
   - **Encoding:** synthesized `Codable` encodes `{"y": ...}` where `Tagged` encodes a single value, so converting changes stored or wire data. Check for custom coding before placing it here.
   - **Language limit:** something `Tagged` genuinely can't express. Name it and show it. `~Copyable` and `~Escapable` alone aren't one: `Tagged` supports both.
   - **Duplicate:** the same concept declared elsewhere. Say which one survives.
   Include the wrappers #239 added: they aren't exempt. Count what each `Tagged` would still declare as a tag, and how tags can be reused.
4. **Molecules:** for all 64: size, dependencies, dependents, and what folding into an atom behind a trait would cost, including `--enable-all-traits`, the traits-off job, Embedded and Windows. Verdict: fold, keep or delete, with the reason. Don't assume folding is right: the fold needs a real benefit.
5. **Low value:** public types with no non-test consumer, types used once, thin forwarders, whole packages with no dependents and no clear purpose, products nothing uses, and `*.Bounded` specifically (10 declarations). The one in swift-buffer-linear has its own header and storage, so judge by consumers, not shape.
6. **`Core` names:** 58 packages have a target with `Core` in its name, 37 distinct names being `X Macro Core`. Group them, and give each group its proper name or merge. Check the `swift-corecursive` false match.
7. **The open hunt:** look for what else is wrong that nobody named. Start with these, and add your own:
   - a lower tier depending on a higher one, cycles, repositories in the wrong org
   - unused dependencies, targets and traits in manifests
   - `exports.swift` re-export chains that hide real dependencies
   - empty or single-declaration targets, packages that only contain tests
   - parallel names for one concept across packages
   - legacy names left from older structures (`Primitives`, `Standard`, `Foundation Integration` where they no longer mean anything)
   - `Foundation` imports where the tier shouldn't have them
   - `#if false`, stale `@available`, and suppressions without a real reason
   - what the top 20 largest packages have in common
8. **Overlap:** intersect the deletion and conversion candidates with the lint findings in `overnight/final-lint.json`, with a fresh location-level run of the runner. How many of the ~45,000 findings sit on code that would go or change? This tests the order Coen chose. If the overlap is small, say so plainly.

## Part 2: rule triage

For every rule in all three bundles, with or without findings. Put a table in `audit/rules.md`:

- Findings, count of packages, and suppressions.
- A random sample of 20 findings (all, if fewer), judged real or false, with the false-positive rate.
- Whether a repair exists and whether it's safe, shown by applying it and building.
- Verdict: keep, fix, split, merge or remove, with the reason.

Then:

- **Fix what's clearly wrong, in `institute` main,** with a test shown to fail without the fix. Remove or merge a rule only if the audit shows why. Don't publish: the coordinator does that.
- **Check these first:** `compound suite name` (5,108, possibly at odds with #239's suite moves), `minimal type body`'s repair (sibling names leave scope, `~Copyable` and `where` get dropped), `counter loop iteration`'s repair (`~Escapable` locals, and whether `forEach` in low-level Sources is actually better: the rule needs a reason beyond style), `comment in source` (does it destroy reasoning that should move into a doc comment? see swift-clock's `isolation!`).
- **#241 items 2, 3 and 5:** `blocking call in async` reading an enum case named `wait` as a call; no check for suite placement, which needs a cross-file check; Embedded staying advisory.
- **List the new rules needed,** each with what it would catch and a count of today's violations. At least: a plain wrapper that should be `Tagged`, `Core` in target names, a lower tier depending on a higher one, a name-independent limit on raw `String` and numbers in public signatures, suppressions without a specific reason.

## Checkpoint: stop here

Write `audit/README.md`: what was measured, at which SHAs, on which platform. Then comment on coenttb/work#242 with one short list:

1. **Newtype target:** today's count, what it would be if every sorted wrapper converts, and a recommended target.
2. **Delete list, fold list, rename list:** sizes and the file to read, with a recommendation. Name each repository that would be deleted or archived.
3. **Does the order still hold?** The overlap result, in a sentence.
4. **New rules** you recommend, in order.
5. **What you found that nobody named,** most important first.
6. **The plan for structure and semantic steps:** batches, order and pilot chain, with effort estimates you can defend.

Every decision numbered, each with a recommendation, in plain words. Coen wants this short: under a page, with the detail in `audit/`. Then stop. Nothing is deleted, folded or renamed until Coen answers.
