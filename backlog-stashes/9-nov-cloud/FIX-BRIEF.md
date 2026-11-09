# Brief for a backlog fix agent

You fix open GitHub issues in a few Swift packages of the Swift Institute ecosystem (Linux, Swift 6.4.2). A coordinator
builds the whole ecosystem, runs tests and lint, and pushes. You only edit and commit locally. Nobody can answer
questions: decide yourself and say what you decided in your report.

## Where to work

Every package is checked out at `/home/user/cloud-workspace/repos/<owner>/<name>`. Do NOT edit those directories:
a whole-ecosystem build reads them while you work. For each repository you are given, make a worktree and work there:

    git -C /home/user/cloud-workspace/repos/<owner>/<name> worktree add /home/user/wt/<name> -b backlog/<name> HEAD

Commit on that branch (author identity is already configured; never add any Claude or co-author trailer). Never push,
never touch `main` of the checkout, never comment on or edit GitHub issues. The worktree's `Package.swift` is the
committed manifest; change it only if the fix needs it.

Other packages are readable under `/home/user/cloud-workspace/repos/` (dependencies' APIs, conventions).

## What to fix

Read each issue with the GitHub MCP tool `mcp__github__issue_read` (method "get"; load it with ToolSearch
"select:mcp__github__issue_read"). The issue body has a checklist. Fix every open `- [ ]` item. Items already `- [x]`
are done or dropped: ignore them. The one-line note you were given is only a summary; the issue is authoritative.
Check each item against the current code first: some may already be fixed.

An item may need a decision only the owner can make, another repository, generated data, a GitHub setting, or a
platform you can't check. Leave such an item open and give the reason. Don't invent large redesigns; prefer the
smallest change that makes the behaviour correct and honest (throw a typed error instead of trapping on caller input,
validate instead of silently dropping, follow the cited spec).

## How to write it

- Follow the surrounding code exactly: naming, nesting (`extension Outer { struct Inner }`), one type per file named
  after the type, `public` API style, typed throws `throws(E)`, `do throws(E) { } catch { }` for typed catches,
  `unsafe` markers where the code already uses them, `#if os(...)` guards as neighbours do.
- No plain `//` comments in Sources (a lint rule forbids them); a `///` doc comment on new public API is fine.
  No force `try!`, no `fatalError`/`precondition` on caller input. Avoid `for i in 0..<n` counter loops when a
  collection loop works. Don't access `.rawValue` chains where a typed API exists.
- Adding a case to a public enum or making a function throw is an API change: then search every package under
  `/home/user/cloud-workspace/repos/` for uses and list them in your report (don't edit other repositories unless you
  were given them; the coordinator fixes dependents).
- Add a regression test for each fixed behaviour in the package's existing test target, in the file for that type
  (or a new `<Type> Tests.swift` next to it), copying the layout of the neighbouring tests exactly: Swift Testing,
  `enum \`X Tests\` {}` namespaces with `extension \`X Tests\` { @Suite struct ... }` or `extension \`X Tests\`.Test`,
  backtick sentence test names, `#expect(throws: ...)`.
- You can't build: the machine has 4 cores and the coordinator owns the build. Be careful with types and labels: read
  the declarations you call. You may run `swiftc -parse <file>` to catch syntax errors, and must run
  `swift format format -i --configuration /home/user/tools/swift-format.json <changed .swift files>` before committing.
- Commit per item or per coherent change. Message: one plain sentence saying what the code now does, ending with
  `(<owner>/<name>#<issue>)`. Example: `Domain.init(unicode:) converts U-labels with IDNA instead of always failing
  (swift-standards/swift-domain-standard#10)`.

## Report

Write `/tmp/claude-0/-home-user-cloud-workspace/189c63d5-61db-5cdd-9f55-ce350d6cb51b/scratchpad/fixes/<owner>__<name>.json`
per repository:

    {"repo": "owner/name", "branch": "backlog/<name>", "worktree": "/home/user/wt/<name>",
     "items": [{"issue": 10, "item": "<first ~80 characters of the checklist line, verbatim>",
                "status": "fixed" | "already-fixed" | "open", "sha": "<full sha or null>", "reason": "<for open/already-fixed>"}],
     "api_changes": ["..."], "dependents": ["owner/name: file:line ..."], "notes": "..."}

Then reply with a short summary: per repository, items fixed / open (with reason), and API changes.
