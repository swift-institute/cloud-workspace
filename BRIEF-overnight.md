# Brief: overnight warning and lint remediation

Coen's decision, 6 Nov: reduce warnings and lint findings across the entire ecosystem overnight, using this cloud workspace, iteratively. **This MUST go through the workspace, with everything rebuilt and re-linted together, because a change in one place can cause problems downstream that would otherwise only be found later.** See coenttb/work#239 (latest comments) and coenttb/work#240 (compiler warnings). Attach `coenttb/work` to read them.

Read `CLAUDE.md`, then `status.md` for what the previous session learned. Run `./sync.sh`.

## Wait first

Another session (the #239 Linux lane) is finishing a manifest sweep here. Don't edit repositories until it has posted its closing comment on #239 or `status.md` says it's closed. Check every 15 minutes, for up to 2 hours. After that, start anyway, and `git pull --rebase` before every commit. Re-run `./sync.sh` before you start.

## The loop

Measure, fix, then rebuild and re-lint the whole ecosystem. Repeat until nothing more can be fixed without breaking the limits below.

1. **Baseline, before any fix.** Record in `status-overnight.md`, by package and by rule or warning kind:
   - **Compiler warnings** from building everything through the workspace. Include test targets: the root workspace can't build other packages' tests, so use `swift build --package-path <repo> --build-tests` with one shared `--scratch-path`. Packages with trait-gated targets also build with all traits on.
   - **Lint findings** from the linter runner built on Linux from `institute` main, so the latest rules apply, across all packages. Note where it differs from the published runner CI uses.
2. **Fix in batches, lowest tier first:** atoms, molecules, standards, compositions, then coenttb. Largest kinds first. Fix causes rather than symptoms. A false positive in a rule gets fixed in the rule, with a test shown to fail without the fix, not suppressed package by package.
3. **After each batch, rebuild and re-lint the whole ecosystem** before pushing. A batch that breaks or newly warns downstream gets fixed before it goes out.
4. **Push by batch,** then read CI once per batch. Update `status-overnight.md` with counts after each round.

Packages: every public repository in `repos.txt`, plus the private portable ones (footprint, swift-agent-sessions, swift-app-launch, swift-impact, swift-interface, swift-licensing, swift-youtube). The 19 Mac packages (Laurie, Birdwatch, Kees, Affairs, Ledger and so on) stay out; note anything they'll need to adapt to.

## Limits

- **No behaviour changes.** If a fix would change behaviour or stored or encoded formats, record it instead of making it. Tests must keep passing where they're run.
- **Not the semantic pass.** That's reassessed tomorrow. Don't add newtypes, wrapper types or concept-map entries to clear a finding.
- **A suppression is not a fix.** Use one only for a true false positive that can't be fixed in the rule, always with a specific REASON. Report the suppression count before and after; it shouldn't rise overall. Never raise a ceiling.
- **HTML `@deprecated` warnings are intended and stay.**
- Standing rules: push to main, never force, never pointfreeco/TCA26, no issues or PRs on swiftlang/swift-package-manager. Don't change swift-windows-32's names. Never open personal data or `*.local.json`. Test data is invented.
- Disk is limited and has filled before. Check it before each large build, and clear finished build output rather than let a build die.
- Don't run things in parallel on shared temporary files. That has already corrupted manifests once.
- A commit that only changes docs skips CI's builds and cancels the real run, so don't make one the last push to a repository.

## Evidence

Every green here is Linux x86_64 only; Apple and Windows code isn't compiled, so `ci.yml` judges those. Count a repository as CI-proven only if its latest run really ran Build jobs. Take times from `date -u`. Run the counting command before quoting a number.

## Done

Keep going without waiting for anyone. Nobody can answer you, and you can't message back. At the end, put a closing section in `status-overnight.md` on main, and comment on coenttb/work#240 with:

- warnings and findings before and after, by tier and by kind
- what remains and why, including rules that look wrong
- behaviour changes you held back
- what is proven on which platform

Coen wants the morning summary short.
