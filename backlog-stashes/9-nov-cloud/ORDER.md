# Order for applying the saved backlog patches (overnight 9→10 Nov, coenttb/work#242)

Made on the Mac at 9 Nov ~16:50Z from `index.json`, `fixes/*.json` and the dependency graph of the ecosystem folder.
Every set below was test-applied with `git am -3` onto origin/main of 9 Nov ~16:45Z: all apply cleanly except
swift-microsoft/swift-windows-32, whose Stats test commit is already on main as 8c61145: skip that commit (`git am --skip`).

**layer** = depth in the dependency graph (1 = no Institute dependencies). **dependents** = packages in the ecosystem
that depend on it, directly or not. **kind** = `API` when `fixes/<owner>__<name>.json` lists `api_changes`.

## Tier A: no ripple (33 sets, 55 items)

Internal changes, or API changes nothing depends on. Apply in batches of about 10, lowest layer first; one whole-ecosystem build per batch.

### A1

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 1 | swift-compositions/swift-splat | `backlog/swift-splat` | 0 | internal | 1 |
| 1 | swift-standards/swift-vat-standard | `backlog/swift-vat-standard` | 0 | API | 3 |
| 1 | swift-w3c/swift-w3c-cssom | `backlog/swift-w3c-cssom` | 16 | internal | 1 |
| 5 | swift-standards/swift-itu-r-bs-1770 | `backlog/swift-itu-r-bs-1770` | 0 | API | 3 |
| 14 | swift-compositions/swift-motion | `backlog/swift-motion` | 0 | API | 1 |
| 17 | swift-w3c/swift-w3c-png | `backlog/swift-w3c-png` | 5 | internal | 2 |
| 19 | swift-compositions/swift-posix | `backlog/swift-posix` | 40 | internal | 1 |
| 19 | swift-compositions/swift-sql | `backlog/swift-sql` | 1 | internal | 1 |
| 19 | swift-standards/swift-locale-standard | `backlog/swift-locale-standard` | 0 | API | 1 |

### A2

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 21 | swift-compositions/swift-loader | `backlog/swift-loader` | 1 | internal | 1 |
| 21 | swift-standards/swift-emailaddress-standard | `backlog/swift-emailaddress-standard` | 21 | internal | 1 |
| 22 | swift-standards/swift-email-standard | `backlog/swift-email-standard` | 2 | internal | 2 |
| 24 | swift-compositions/swift-process | `backlog/swift-process` | 10 | internal | 2 |
| 25 | swift-compositions/swift-arguments | `backlog/swift-arguments` | 2 | internal | 2 |
| 25 | swift-compositions/swift-git | `backlog/swift-git` | 1 | internal | 1 |
| 26 | swift-compositions/swift-stores | `backlog/swift-stores` | 0 | internal | 1 |
| 26 | swift-compositions/swift-time-to-live | `backlog/swift-time-to-live` | 0 | API | 1 |
| 26 | swift-compositions/swift-yaml | `backlog/swift-yaml` | 0 | internal | 3 |
| 27 | swift-compositions/swift-byte-channel | `backlog/swift-byte-channel` | 0 | internal | 1 |

### A3

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 27 | swift-compositions/swift-parsers | `backlog/swift-parsers` | 0 | API | 3 |
| 29 | swift-compositions/swift-xml | `backlog/swift-xml` | 2 | internal | 2 |
| 30 | swift-compositions/swift-mcp | `backlog/swift-mcp` | 0 | internal | 1 |
| 30 | swift-compositions/swift-plist | `backlog/swift-plist` | 0 | API | 4 |
| 33 | swift-compositions/swift-linter-rules | `backlog/swift-linter-rules` | 1 | internal | 2 |
| 33 | swift-compositions/swift-xcode | `backlog/swift-xcode` | 0 | internal | 1 |
| 33 | swift-standards/swift-json-feed-standard | `backlog/swift-json-feed-standard` | 0 | internal | 1 |
| 34 | swift-compositions/swift-html-render | `backlog/swift-html-render` | 11 | internal | 1 |
| 34 | swift-compositions/swift-pdf-render | `backlog/swift-pdf-render` | 2 | internal | 3 |
| 35 | swift-compositions/swift-linter | `backlog/swift-linter` | 1 | internal | 1 |

### A4

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 35 | swift-compositions/swift-tests | `backlog/swift-tests` | 0 | API | 3 |
| 38 | swift-compositions/swift-pdf-html-render | `backlog/swift-pdf-html-render` | 1 | internal | 1 |
| 40 | swift-compositions/swift-epub-render | `backlog/swift-epub-render` | 0 | API | 3 |

## Tier B: API changes with 1 to 9 dependents (19 sets, 60 items)

Batches of about 4, lowest layer first. Before building, fix every caller listed in the fix record's `dependents`, and grep the whole ecosystem for each changed name.

### B1

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 1 | swift-standards/swift-git-standard | `backlog/swift-git-standard` | 2 | API | 1 |
| 6 | swift-standards/swift-smpte-st-12 | `backlog/swift-smpte-st-12` | 1 | API | 1 |
| 21 | swift-w3c/swift-w3c-svg | `backlog/swift-w3c-svg` | 8 | API | 5 |
| 24 | swift-compositions/swift-memory-mapping | `backlog/swift-memory-mapping` | 1 | API | 4 |

### B2

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 24 | swift-standards/swift-json-rpc-standard | `backlog/swift-json-rpc-standard` | 2 | API | 1 |
| 25 | swift-compositions/swift-dependencies | `backlog/swift-dependencies` | 9 | API | 2 |
| 25 | swift-compositions/swift-svg | `backlog/swift-svg` | 5 | API | 1 |
| 25 | swift-standards/swift-yaml-standard | `backlog/swift-yaml-standard` | 1 | API | 1 |

### B3

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 26 | swift-compositions/swift-translating | `backlog/swift-translating` | 5 | API | 4 |
| 27 | swift-w3c/swift-w3c-xml | `backlog/swift-w3c-xml` | 4 | API | 6 |
| 32 | swift-iso/swift-iso-32000 | `backlog/swift-iso-32000` | 4 | API | 16 |
| 32 | swift-standards/swift-uri-standard | `backlog/swift-uri-standard` | 9 | API | 1 |

### B4

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 33 | swift-standards/swift-spm-standard | `backlog/swift-spm-standard` | 5 | API | 3 |
| 34 | swift-compositions/swift-manifests | `backlog/swift-manifests` | 2 | API | 2 |
| 34 | swift-compositions/swift-package-manager | `backlog/swift-package-manager` | 3 | API | 4 |
| 34 | swift-w3c/swift-w3c-epub | `backlog/swift-w3c-epub` | 2 | API | 2 |

### B5

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 36 | swift-compositions/swift-css-html-layout-render | `backlog/swift-css-html-layout-render` | 8 | API | 1 |
| 37 | swift-compositions/swift-css | `backlog/swift-css` | 7 | API | 3 |
| 38 | swift-compositions/swift-markdown-html-render | `backlog/swift-markdown-html-render` | 5 | API | 2 |

## Tier C: API changes with 10 or more dependents, and swift-json (14 sets, 68 items)

One set per round, lowest layer first: apply, grep every changed name across the ecosystem (and institute), fix every caller, build the whole ecosystem, push the set and its callers together. swift-json#15 (`serialize`/`jsonString` throw, about 44 call sites, about 15 in institute) last.

| layer | repository | branch | dependents | kind | items |
|---|---|---|---|---|---|
| 18 | swift-iso/swift-iso-9945 | `backlog/swift-iso-9945` | 43 | API | 5 |
| 18 | swift-microsoft/swift-windows-32 | `backlog/swift-windows-32` | 38 | API | 9 |
| 18 | swift-standards/swift-color-standard | `backlog/swift-color-standard` | 14 | API | 3 |
| 18 | swift-standards/swift-domain-standard | `backlog/swift-domain-standard` | 26 | API | 1 |
| 19 | swift-linux-foundation/swift-linux-standard | `backlog/swift-linux-standard` | 39 | API | 4 |
| 19 | swift-standards/swift-darwin-standard | `backlog/swift-darwin-standard` | 39 | API | 1 |
| 21 | swift-w3c/swift-w3c-css | `backlog/swift-w3c-css` | 15 | API | 20 |
| 22 | swift-standards/swift-css-standard | `backlog/swift-css-standard` | 12 | API | 1 |
| 23 | swift-compositions/swift-kernel | `backlog/swift-kernel` | 36 | API | 5 |
| 24 | swift-compositions/swift-witnesses | `backlog/swift-witnesses` | 25 | API | 3 |
| 25 | swift-compositions/swift-executors | `backlog/swift-executors` | 15 | API | 3 |
| 27 | swift-compositions/swift-io-kernel | `backlog/swift-io-kernel` | 13 | API | 2 |
| 29 | swift-compositions/swift-json | `backlog/swift-json` | 8 | API | 5 |
| 32 | swift-compositions/swift-file-system | `backlog/swift-file-system` | 10 | API | 6 |

## Not applied

- swift-intel/swift-x86-standard `lint/swift-x86-standard`: lint repair held back: Quality · source red before the 9 Nov push (done criterion 5)
- swift-iso/swift-iso-32000 `lint2/swift-iso-32000`: lint repair held back: Quality · source red before the 9 Nov push (done criterion 5)
- swift-ietf/swift-rfc-9557 `lint2/swift-rfc-9557`: held back, and does not compile (members moved into extensions)
