# Rule triage (coenttb/work#242, part 2)

All 143 rules of the three bundles (institute 140, primitives 143, standards 136), measured with the runner from
institute 2ac3965 over 455 packages on Linux: 40,031 findings, 98 rules with findings. For each rule with findings, a
seeded random sample of 20 (all, if fewer) was judged against the rule's own stated intent: 1,668 findings judged,
658 false. Weighted by each rule's count, **about 12,800 of the 40,031 findings (32%) are false.** Data:
`data/rules-judged.json`; the sampler is `rules_sample.py` (seed `coenttb/work#242:<rule>`).

Verdicts: **60 fix, 5 remove, 1 merge, 77 keep** (44 of the keeps have no findings: registered and tested, not read for
dead logic). Private packages' findings were judged but appear only by sample number.

## Fixed in institute main

- **`minimal type body` repair** (cc0d7da): the generated `extension` now keeps `where T: ~Copyable`/`~Escapable`, and
  inside `extension Outer { struct Inner }` the repair declines when moved members name anything beyond the type itself,
  since `extension Outer.Inner` doesn't look names up in `Outer`. Both failures reproduced with swiftc
  ("requires that 'NC' conform to 'Copyable'", "cannot find type 'Helper' in scope"). Three new tests fail on the old
  repair; the rule's 65 tests pass. Not published: the coordinator does that.

## The ones the brief asked about

- **`compound suite name`** (5,108): fix. It is at odds with #239: ~1,043 findings are on the `enum \`Foo Tests\`` with
  `Test.Unit` layout #239 moved suites into (525 on the name, 518 on the category). Make the rule accept that layout
  (one decision for Coen: rule or #239, and the rule is the cheaper side). The other ~4,065 are descriptive suite names, real.
- **`minimal type body`** (4,944): repair fixed above; detection should exempt Tests (samples 5, 14). Keep the rule.
- **`counter loop iteration`** (501): fix. The repair moves a loop body into a `forEach` closure, which can't capture a
  `~Escapable` local such as a `Span` (the overnight revert), and the rule also fires on Span-indexing and triangular
  loops. The rule gives no reason beyond style for `forEach` in low-level Sources: refuse the repair when the body uses a
  `~Escapable`/`~Copyable` local, and make it a note in atoms.
- **`comment in source`** (12 left): fix the repair, not the rule: a removed comment above a declaration should move into
  its doc comment, not vanish (swift-clock's `isolation!` lost its reason this way; restore that one by hand).
- **#241 item 2, `blocking call in async`**: fix. `swift-linter-rules` `Lint.Rule.Concurrency.BlockingCallInAsync.swift:104`
  matches any member call named `wait`, so `.wait(for: x)` or `Action.wait(id)` (an enum case with a payload) counts as
  blocking. Zero findings today only because no code has such a case yet. Check the base type, or drop `wait` from the
  set. Not fixed: it's in swift-linter-rules, outside institute.
- **#241 item 3, suite placement**: no rule checks that a suite sits in the test file for its type; it needs the runner's
  cross-file view (target-level). Listed below as a new rule.
- **#241 item 5, Embedded**: stays advisory: nothing here measured Embedded builds, and no rule claims to.

## Remove or merge

| Rule | Findings | Why |
|---|---|---|
| `fully qualified error in typed throws` | 1,429 | real by the letter in 20/20, but it demands `throws(Foo.Bar.Error)` inside `Foo.Bar`, against the Nest.Name style |
| `safe attribute undocumented` | 133 | 0/20 real: asks for `why:` comments, which `comment in source` forbids in Sources |
| `usable from inline internal import` | 45 | 0/20 real: never checks for an `@inlinable` use; the compiler already rejects the real case |
| `inlinable internal access` | 12 | 0/12 real: `@inlinable internal` is legal and already visible to inlinable code |
| `generic throws missing never` | 5 | its condition (a measured hot loop) can't be seen in syntax |
| `existential throws` → merge into `untyped throws` | 157 | 19/20 are tests, which `untyped throws` already exempts |

## Biggest false-positive sources (fix)

`unchecked call site` 18/20 false (constants built with `Self(__unchecked:)`, `take(__unchecked:)`);
`tagged unchecked with typed alternative` 19/20 (fires on every `_unchecked`, fix only works for literals);
`throwing wrapper init` 19/20 (`self.init` to a validating init); `typealiased namespace bridge` 17/20;
`chained rawvalue access` 16/20; `unification typealias` 16/20; `canimport conditional` 20/20 (module check inside
`#if os(Linux)`); `unknown default` 19/20 (non-frozen enums where Swift requires it); `closure typed throws annotation`
18/20 (untyped closure parameters); `try optional` 14/20; `namespace adoption typealias` 14/20; `raw value access`
11/20; `extension file naming` 11/20 (types from other modules); `int public parameter` 10/20 (protocol witnesses);
`architecture import boundary` and `exported import` (case-sensitive `exports.swift`). Unsafe repairs: `module selector
spelling` (`W3C_XML.parse` → `W3C_XML::parse` misses the same-named type), `canonical settings tail` (rewrites the whole
settings loop, adds `treatAllWarnings`). Every rule's defect is in the table.

## New rules needed, with today's violations

| # | Rule | Catches | Today |
|---|---|---|---|
| 1 | plain wrapper should be `Tagged` | a struct whose only member is one stored field plus forwarding (by shape, not name) | 62 newtypes (208 incl. one-field records) |
| 2 | upward tier edge across packages | an atom depending on a molecule, a molecule on a standard, etc. (`upward layer edge` checks layers inside a package) | 30 edges, 11 atoms |
| 3 | `Core` in a target name | the word `Core` in any target | 75 targets, 49 packages |
| 4 | raw `String` or number in a public signature, name-independent | a public func/init parameter typed `String`, `Int`, `UInt*`, `Double`… unless it's a protocol witness or the wrapped value of a newtype | 4,864 parameters in 249 packages (String 1,684, Int 1,197, Double 895; regex count, approximate) |
| 5 | declared dependency never imported / import without declared dependency | manifest vs. imports, target level | 776 and 544 |
| 6 | suite placement (#241 item 3) | a `@Suite` for `Foo` outside `Tests/.../Foo Tests.swift` | not counted (needs the cross-file pass) |
| 7 | suppression without a specific reason | `swift-linter:disable` with no `REASON:` or a reused generic one | 5 of 242 (`suppression reason required` mostly does this; low priority) |

## Full table

See `rules-table.md` (generated): findings, packages, suppressions, sample real/false and false-positive rate, repair,
verdict and reason for every rule.
