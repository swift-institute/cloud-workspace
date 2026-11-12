# `fatal error outside tests` skips a sole `fatalError` in a `Never` body (swift-institute/Issues#271)

Cloud session, 12 Nov 2026, on the Swift WASM / Embedded coordinator's hand-off. Attaching swift-institute/Issues to this session was denied by its permission check, so I couldn't read #271 or comment on it. The change follows the coordinator's summary of the issue, and this file is the report for #271. Copy it there.

## Heads (read back from the remote)

- swift-institute/institute main `1b5e4307c03e3ea5818ed7b278484e76db88cfc6`:
  - `e4cc3bea976c67681d6cfbcce4d2e9685b1cd73d`: the rule, its tests and its limits.
  - `1b5e430`: the limits table's indentation, which was failing Quality · source.
- swift-institute/cloud-workspace main: `ratchet.py` writes that indentation.

## The rule

A `fatalError(...)` (or `Swift.fatalError`, or a `return` of either) is no longer counted when it is the only statement of:

- the body of a function whose return type is `Never` or `Swift.Never`; or
- the getter of a computed property or subscript of that type, whether the getter is implicit, `get` or `borrowing get`.

Still counted:

- a `Never` body that does anything else first;
- a `fatalError` under a branch, or in a closure, inside a `Never` body;
- the body of any other type (`Int`, `Never?`, no return type);
- a closure of type `() -> Never`;
- a setter.

The leaf-protocol special case (`Parsing`, `Serializing`, `Coding` defaults where `Body == Never`) is covered by the general rule, so it and its helpers are gone. The rule's controls are rewritten to the new shapes: 19 controls, none failing in any repository measured.

## Tests

17 checks in `Lint.Rule.Idiom.FatalErrorOutsideTests Tests.swift`, one per shape. Each was shown failing first, against one of three rules:

| Rule run against | Checks that failed |
|---|---|
| the old rule | the 7 skipped shapes, and the setter |
| a wrong rule that skips any `fatalError` anywhere in a `Never` body | other work first (function and property), branch, closure, setter |
| a wrong rule that skips any sole statement, whatever the type | `Int` function and property, `Never?`, no return type, `Never` closure, setter, branch, closure |

The existing unit tests now use a plain function, because a `Never` one is skipped.

Run on Linux x86_64, Swift 6.4.2: `swift test --filter "fatal error outside tests|Lint.Rule.Bundle.institute|Ratchet|Idiom"` passes 170 tests in 56 suites, 9 in 7 and 5 in 1.

## Limits

Only this rule's rows were regenerated. They were measured with the release runner of this change over the 40 repositories that had a limit for the rule: shallow clones of each main on 12 Nov 2026, listed below. Each new limit is the lower of the old limit and the new count, so none rises.

| Repository | Old limit | Main, old rule | Main, new rule | New limit |
|---|---|---|---|---|
| swift-atoms/swift-coproduct | 1 | 0 | 0 | — |
| swift-atoms/swift-renderer | 7 | 1 | 0 | — |
| swift-compositions/swift-html-render | 6 | 0 | 0 | — |
| swift-compositions/swift-loader | 1 | 0 | 0 | — |
| swift-compositions/swift-pdf-render | 11 | 11 | 0 | — |
| swift-compositions/swift-sql | 16 | 7 | 7 | 7 |
| swift-compositions/swift-svg-render | 10 | 11 | 0 | — |
| swift-compositions/swift-translating | 7 | 5 | 5 | 5 |
| swift-ietf/swift-rfc-4122 | 2 | 0 | 0 | — |
| swift-molecules/swift-binary-parser | 2 | 1 | 1 | 1 |
| swift-molecules/swift-buffer-slab | 2 | 1 | 1 | 1 |
| swift-standards/swift-color-standard | 2 | 0 | 0 | — |

The other 28 repositories are unchanged. The rule's total goes from 155 (table) to 102.

The new rule removes 23 findings, and every one is a sole `fatalError` in a `Never` body:

- swift-pdf-render: 11 `body: Never` view bodies.
- swift-svg-render: 11 `body: Never` view bodies. This repository was 11 against a limit of 10 on main with the old rule; it is now 0.
- swift-renderer: `Renderer.Document.View.unrendered`, the internal trap the WASM / Embedded programme's lane 3 deletes. Nothing was changed in swift-renderer or swift-html-render.

The rest of the drop was already absent on main.

The strict institute lint of the change adds no finding: 1698 findings before and after, counted with the old and new runner.

## CI

- At `e4cc3be` (run 43199482081), Linux release, Linux 6.4, Linux traits off and macOS are green. Two jobs are red for reasons that predate the change, the same as at `b5e810c`:
  - **Quality · source:** 51 swift-format "unindent by 4 spaces" errors, all on the limits table. `1b5e430` fixes them, and `ratchet.py` now writes that indentation.
  - **Windows release:** fails compiling the dependency swift-process (`switch must be exhaustive` in `Process.Spawn.Capture.Windows.swift:109` and `Process.Spawn.Capture.swift:39`). That is outside institute, and I didn't touch it.
- At `1b5e430` (run 43203631570), Linux release, Linux 6.4, Linux traits off and macOS are green, and the table's format errors are gone. Two jobs are still red:
  - **Quality · source** now shows the overruns the format errors had hidden: institute's own limits for minimal type body (690/687), test function naming (48/45), compound identifier (212/211) and int public parameter (21/20), plus three swift-format nits.
  - **Windows** is still red from swift-process.

  Not fixed here, on Coen's go-ahead to push through: see Red lines crossed in ci-timeout-660.md.

## swift-institute/Issues#273 (institute `60e45e4`)

- **Cause:** `bool public parameter` declared no suppression policy, and `Lint.Rule`'s default is `.none`, so every directive for it was ignored without a word.
- **Fix:** it sanctions `disable:next` with a `REASON:` line.
- **Tests:** three suppression tests; "disable next with a reason is sanctioned" failed first.
- **Other rules affected:** yes. 121 of the 126 institute rules take the `.none` default and silently ignore any directive. Only fatal error outside tests, try, do throws for typed catch and untyped throws (`.next`) and raw concept (`.both`) sanction one.
- **Recommended follow-up:** the linter reports a directive its rule doesn't sanction as a finding, instead of ignoring it.

## swift-institute/Issues#272 (institute `60e45e4`)

- **Fix:** `Ratchet.counts` leaves out note-severity findings. Severity is the typed fact behind "non-counting review prompt".
- This covers namespace adoption typealias and typealiased namespace bridge, and also lifecycle typealias review, the third note rule. Its prompt ("Confirm the primitive…") is the same kind; that choice is mine.
- **Limits:** the three rules' 159 rows leave the table, so no limit rises.
- **Tests:** two; both failed before the change. swift-html-render is untouched.
- **Not yet done:** `ratchet.py` still counts notes when it regenerates the table. Follow-up: skip note-severity items there.

## Clones measured (main, 12 Nov 2026)

```
swift-atoms/swift-async ff5c757c2c6b
swift-atoms/swift-coproduct 211aa38e5441
swift-atoms/swift-glob bb596a4d5c0e
swift-atoms/swift-indexed c7c004a89f47
swift-atoms/swift-path 926f1c6d4cf5
swift-atoms/swift-renderer 3ea6ec0efa67
swift-atoms/swift-storage 92374320ae4e
swift-atoms/swift-string b4b5d2e6e275
swift-compositions/swift-arguments bbc72d25df65
swift-compositions/swift-css eae11ffc02f8
swift-compositions/swift-dependencies f5e9c253d326
swift-compositions/swift-file-system 37b95976ac90
swift-compositions/swift-html-render 27f3c44961b8
swift-compositions/swift-kernel 6d011af1a2f2
swift-compositions/swift-loader 99971b46a85e
swift-compositions/swift-pdf-render 343dfcf3285f
swift-compositions/swift-sql 798593ef31d4
swift-compositions/swift-sqlite a7e06fe447be
swift-compositions/swift-svg-render 360c7ccaa693
swift-compositions/swift-translating 64735d50ddbc
swift-compositions/swift-witnesses 1ad790724e9c
swift-ietf/swift-rfc-2046 31e91faad9eb
swift-ietf/swift-rfc-4122 1e22d4fdeb6f
swift-ietf/swift-rfc-6455 953b4d0a94cc
swift-iso/swift-iso-8824 63c1afb8798a
swift-iso/swift-iso-8825 8d73396a09a0
swift-iso/swift-iso-9945 0ab0bfa84f4d
swift-microsoft/swift-windows-32 8c6114529630
swift-molecules/swift-algebra-modular fae4e96497fd
swift-molecules/swift-binary-parser 8a7fed8c28ef
swift-molecules/swift-buffer-slab 79d26e130bbb
swift-molecules/swift-list-linked ea572a619db8
swift-molecules/swift-machine 5e7b111eaf6d
swift-molecules/swift-parser-machine 6c970252e7a8
swift-molecules/swift-queue-linked fe4feb4fb4e6
swift-standards/swift-color-standard 144516896915
swift-standards/swift-github-standard b6e792ff1030
swift-standards/swift-rss-standard d261752d92ef
swift-standards/swift-uri-standard d985eb94fec0
swift-w3c/swift-w3c-css 97381c270ecb
```
