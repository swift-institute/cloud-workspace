# Probe result: cloud session on Linux, 2026-11-06

What a Claude Code cloud session can do with this workspace. Every figure was measured once, in one session. Times are wall clock. "Peak used" is the highest system-wide `free -m` "used" value, sampled every 2 s. It isn't per-process: there is no `/usr/bin/time` here, and the cgroup reports no `memory.peak`.

## 1. Machine

| | |
|---|---|
| `uname -a` | `Linux vm 6.18.44-fc-v242 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux` (Ubuntu 24.04.5 LTS, Firecracker VM) |
| `nproc` | 4 |
| Memory | 15 GiB total, 15 GiB available, no swap |
| Disk | `df` shows 252G size, 26G available at start. This is a per-session allowance. 25G was still free after everything below; `repos/` is 250M and `.build` 551M. |
| Xcode | none (`xcodebuild` and `xcode-select` not found) |
| `swift --version` | `Swift version 6.4.2 (swift-6.4.2-RELEASE)`, `Target: x86_64-unknown-linux-gnu`, at `/usr/local/bin/swift` (→ `/opt/swift`). Already installed, so nothing needed installing. Tools version 6.4 manifests load. |

## 2. Access: `./sync.sh`

- Exit 0, **real 0m33.9s**. Output: `448 repositories in repos/`.
- 448 of 448 cloned, 0 `CLONE FAILED`.
- `private-repos.txt` doesn't exist, so no private repository was attempted.

## 3. Push access

- `gh` is at `/usr/local/bin/gh` but **not logged in**. `gh auth status` exits 1 with `X Failed to log in to github.com using token (GH_TOKEN)` / `The token in GH_TOKEN is invalid.`
- In `repos/swift-iso/swift-iso-4217`, `git push --dry-run origin HEAD:refs/heads/main` exits **128** with this exact error:

  ```
  remote: access denied by the git proxy: swift-iso/swift-iso-4217 is not in this session's authorized repository set, so the proxy will not inject a credential for it. To fix, add the repository to the session's sources.
  fatal: unable to access 'https://github.com/swift-iso/swift-iso-4217.git/': The requested URL returned error: 403
  ```

  Pushing is governed by the session's repository set. This session was started with only `swift-institute/cloud-workspace`. A session can attach more repositories with the `add_repo` tool, subject to the GitHub App installation and org policy, but that is one call per repository. I didn't try it, because the brief said to measure only. Over 448 repositories, plan for this: either start sessions with the repositories they will push to as sources, or have each session call `add_repo` before it pushes.
- `git ls-remote https://github.com/coenttb/swift-licensing.git` exits **128**: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. **The private repository is not readable** without attaching it the same way.
- Pushing to this repository (`swift-institute/cloud-workspace`) works: see the commit that adds this file.

## 4. Size: generate, resolve, build

### 4a. First run, on 9b0cdc1, without `localize.py`

| Step | Result |
|---|---|
| `./generate.py` | exit 0, real 0m44.8s. `448 packages, 1257 library products`, 0 `UNREADABLE`. |
| `swift package resolve` | exit 0, **145 s**, peak used 1153 MiB, 0 "Conflicting identity" warnings. Only 10 remote pins (swift-argument-parser, swift-asn1, swift-cmark, swift-collections, swift-crypto, swift-custom-dump, swift-issue-reporting, swift-markdown, swift-snapshot-testing, swift-syntax). Everything else resolved to the local checkouts. |
| `swift build --target Path` | **Hung, and I killed it at 23 min** (1390 s, exit 143) on the teammate session's instruction, before the 30-min limit. One `swift-build` process ran at 100% of one core with about 200 MB RSS; peak system used was 713 MiB. It printed **1746 "Conflicting identity" warnings**, each like `'swift-iso-32000': Conflicting identity for swift-scale: dependency 'github.com/swift-atoms/swift-scale' and dependency '/home/user/cloud-workspace/repos/swift-atoms/swift-scale' both point to the same package identity…`, and compiled nothing. |
| `swift build --target "RFC 3986"` | not run (the graph-loading phase never finished) |

### 4b. Second run, on 2c07131, with `localize.py`

Steps: `git pull` (fast-forward to 2c07131), `./localize.py`, `./generate.py`, `rm -rf .build Package.resolved`, then the commands below.

| Step | Result |
|---|---|
| `./localize.py` | real 1.3s. Printed `2685 dependencies rewritten across 448 packages; 0 URLs still naming a checkout`. Each checkout's `Package.swift` is now flagged `S` (skip-worktree) in `git ls-files -v`, and `git status` in the checkout is clean. |
| `./generate.py` | exit 0, real 0m45.2s, `448 packages, 1257 library products`, 0 `UNREADABLE` |
| `swift package resolve` | exit 0, **113 s**, peak used 740 MiB, **0 "Conflicting identity" warnings**. Same 10 remote pins. Most of the time is fetching swift-syntax, swift-crypto and the other remote packages. |
| `swift build --target Path` (clean `.build`) | exit 0, **78 s** wall (`Build complete! (46.92 secs)`, `[1063 / 1066]` tasks), peak used **2115 MiB**, **0 "Conflicting identity"**, no warnings or errors. 55 packages in `.build/out/Intermediates.noindex`. |
| `swift build --target "RFC 3986"` (after Path) | exit 0, **68 s** wall (`Build complete! (38.80 secs)`), peak used **2432 MiB**, 0 "Conflicting identity". 66 packages built in total. |

**The local checkouts are the ones built.** Path's `.SwiftFileList` lists `/home/user/cloud-workspace/repos/swift-atoms/swift-path/Sources/Path/…`, and RFC 3986's lists `/home/user/cloud-workspace/repos/swift-ietf/swift-rfc-3986/Sources/RFC 3986/…`. `.build/checkouts/` holds only the 10 remote pins above.

The build system is the swift-build backend: it writes `manifest.pif` and products land in `.build/out/Products/Debug-linux-x86_64`.

## 5. Incremental rebuild

I appended `// probe: incremental rebuild` to `repos/swift-atoms/swift-path/Sources/Path/Path.swift`, then ran `swift build --target Path`:

- exit 0, **58 s** wall (`Build complete! (27.74 secs)`, `[3 / 8] Path`), peak used 2105 MiB.
- Then `git checkout -- Sources/Path/Path.swift`. swift-path's `git status --short` is clean.
- **A no-op `swift build --target Path`, with nothing changed, also takes 58 s** (`Build complete! (28.13 secs)`; phases `[Computing dependencies]`, `[Provisioning 1 / 107]`, `[Using on-disk description]`). So the edit itself costs almost nothing: every `swift build` on this 448-package graph carries a fixed cost of about 1 minute. About 30 s is loading the package graph and about 28 s is the build system's planning phase. Expect at least a minute per edit-and-check cycle.

## 6. Limits hit

- **No push access outside the session's repository set**, and no read access to private repositories, unless they are attached (§3). This is the main blocker for the campaign.
- `gh` is unusable: `GH_TOKEN` is invalid. Use the GitHub MCP tools for GitHub API work.
- Without `localize.py`, SwiftPM's identity-conflict search doesn't finish (§4a). With it, there were no conflicts.
- No network blocks: github.com clones and the swift-syntax and swift-crypto fetches went through the proxy.
- Memory was never close to a limit: at most about 2.4 GiB used out of 15 GiB. Disk wasn't either: 25G still free.
- Session time: the whole probe took about 1 hour, including the 23-minute hang. A background shell command in this harness is stopped after its timeout, which is 10 min by default. For long builds, pass a longer `timeout` explicitly.
- Not tested: `./sync.sh` after `localize.py`. Each checkout has a locally rewritten manifest under skip-worktree, and `git pull --ff-only` will probably refuse in any checkout whose upstream changes `Package.swift`. Running `./localize.py --restore` before syncing should avoid that.

All results are Linux-only. Apple-specific and Windows code isn't compiled here.

## 7. Follow-up: `sync.sh` on b6679f5, and attaching repositories with `add_repo`

### `./sync.sh`, now running all three steps

`git pull` brought this checkout to b6679f5. `./sync.sh` exited 0 in **real 1m43.4s** (about 1m of that is `generate.py`). It printed:

```
restored 448 manifests
448 repositories in repos/
2685 dependencies rewritten across 448 packages; 0 URLs still naming a checkout
448 packages, 1257 library products
```

No `PULL FAILED` lines, and **0 URLs left**.

### `add_repo` for `swift-iso/swift-iso-4217` (access `push`)

**It was refused at once, and no approval prompt was shown.** It returned in under 0.1 s. Before the call reached the backend, this session's permission layer (auto mode) denied it with this exact error:

```
Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Access Added As A Means]. ... To allow this type of action in the future, the user can add a permission rule for mcp__claude-code-remote__add_repo to their settings.
```

So this probe didn't find out whether the backend would accept the attachment, how long it takes, or whether there is a limit. In this session's permission mode, the agent can't attach repositories on its own. A person has to allow `mcp__claude-code-remote__add_repo`, either by a permission rule in settings or by approving it. Alternatively, the repositories can be the session's sources from the start.

I made no attempt to get around the denial. After it, the dry-run push in `repos/swift-iso/swift-iso-4217` still exits 128 with the same error as in §3:

```
remote: access denied by the git proxy: swift-iso/swift-iso-4217 is not in this session's authorized repository set, so the proxy will not inject a credential for it. To fix, add the repository to the session's sources.
fatal: unable to access 'https://github.com/swift-iso/swift-iso-4217.git/': The requested URL returned error: 403
```

**Not attempted:** attaching `coenttb/swift-licensing` and the batch of 20 from `repos.txt`. Both depend on the first attachment working.

## 8. Follow-up: `add_repo` with `.claude/settings.json` allowing it

`.claude/settings.json` is present at 283044e and allows `mcp__claude-code-remote__add_repo`. Every call below used `access: "push"`.

### `swift-iso/swift-iso-4217`

**It completed unattended: no refusal and no approval prompt.** The tool returned `"status":"appended"` and `Session currently has 2 repo(s): swift-institute/cloud-workspace, swift-iso/swift-iso-4217.`

A fresh `git clone --depth 1` into `/tmp/probe` took 3.5 s. In that clone, `git push --dry-run origin HEAD:refs/heads/main` exits **0** and prints:

```
Everything up-to-date
```

In §3 and §7, the same command exited 128 with the proxy's 403.

### `coenttb/swift-licensing` (private)

Attached the same way, unattended. `git ls-remote https://github.com/coenttb/swift-licensing.git` now exits **0** and reads it (§3: exit 128, `could not read Username`):

```
4b59e89d517b0b0250a15dffe4ff64f2ff994dfd	HEAD
4b59e89d517b0b0250a15dffe4ff64f2ff994dfd	refs/heads/main
```

### The first 20 lines of `repos.txt`

`swift-arm-ltd/swift-arm-standard` and `swift-atoms/swift-addition` through `swift-atoms/swift-binary`, one call each, sent in two batches of 10. **All 20 completed unattended, with no limit hit.** The session then had 23 repositories. Times, from shell timestamps around each batch, so they include the agent's own turn overhead:

- first batch of 10: about 39 s
- second batch of 10: about 13.5 s

So each call costs at most a few seconds, and 20 took under a minute. I didn't time single calls. 23 repositories isn't near 448; whether a cap exists further up is still unknown.

`swift-atoms/swift-binary` (the 20th) cloned into `/tmp/probe` in 0.9 s. `git push --dry-run origin HEAD:refs/heads/main` exits **0**: `Everything up-to-date`.

### Notes

- Each `add_repo` result tells the agent to clone into `/home/user/<name>` and call `register_repo_root`. I didn't: the brief said to clone into `/tmp`. For work in `repos/`, the existing checkouts are what count; attaching only changes what the git proxy authorizes.
- The result also says the proxy allows 2 concurrent smart-HTTP operations per repository, and a third gets HTTP 429.
- Nothing was pushed to any repository except this one.
