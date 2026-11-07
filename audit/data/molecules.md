| Molecule | Lines | Decls | Atom deps | Molecule deps | Dependents | Traits | Verdict | Reason |
|---|---|---|---|---|---|---|---|---|
| swift-complex-dimension | 3 | 0 | 4 | 0 | 0 | - | **delete** | no consumer in the workspace and 0 declarations in 3 source lines |
| swift-geometry-pair | 8 | 1 | 2 | 0 | 0 | - | **delete** | no consumer in the workspace and 1 declarations in 8 source lines |
| swift-symmetry-pair | 8 | 1 | 2 | 0 | 0 | - | **delete** | no consumer in the workspace and 1 declarations in 8 source lines |
| swift-symmetry-finite | 22 | 0 | 4 | 0 | 0 | - | **delete** | no consumer in the workspace and 0 declarations in 22 source lines |
| swift-geometry-boundary | 23 | 0 | 4 | 0 | 0 | - | **delete** | no consumer in the workspace and 0 declarations in 23 source lines |
| swift-version-carrier | 24 | 3 | 2 | 0 | 0 | - | **delete** | no consumer in the workspace and 3 declarations in 24 source lines |
| swift-axis-dimension | 32 | 4 | 2 | 0 | 0 | - | **delete** | no consumer in the workspace and 4 declarations in 32 source lines |
| swift-symmetry-linear | 33 | 0 | 3 | 0 | 0 | - | **delete** | no consumer in the workspace and 0 declarations in 33 source lines |
| swift-module | 51 | 4 | 0 | 1 | 0 | - | **delete** | no consumer in the workspace and 4 declarations in 51 source lines |
| swift-symmetry-algebra | 150 | 0 | 2 | 0 | 1 | - | **fold** | bridge of algebra, symmetry; fold into swift-atoms/swift-algebra behind a trait |
| swift-symmetry-dimension | 76 | 0 | 5 | 1 | 0 | - | **keep** | depends on molecules (swift-symmetry-algebra): folding would give an atom a molecule edge |
| swift-async-fanout | 86 | 1 | 1 | 0 | 1 | - | **keep** | its own structure with 1 dependents and 1 atom dependencies; no single host |
| swift-stack | 149 | 5 | 6 | 2 | 7 | - | **keep** | depends on molecules (swift-buffer-linear, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-builder | 183 | 2 | 2 | 2 | 1 | - | **keep** | depends on molecules (swift-buffer-linear, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-async-bridge | 203 | 3 | 7 | 4 | 0 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-set-algebra | 220 | 0 | 3 | 1 | 0 | - | **keep** | depends on molecules (swift-builder): folding would give an atom a molecule edge |
| swift-async-barrier | 234 | 6 | 1 | 1 | 2 | - | **keep** | depends on molecules (swift-async-waiter): folding would give an atom a molecule edge |
| swift-diagnostic | 253 | 7 | 1 | 1 | 4 | - | **keep** | depends on molecules (swift-source): folding would give an atom a molecule edge |
| swift-slot-map | 262 | 4 | 7 | 2 | 0 | - | **keep** | depends on molecules (swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-range | 291 | 8 | 1 | 0 | 0 | - | **keep** | no consumer in the workspace, but 291 source lines of its own: ask, don't fold |
| swift-loader-vocabulary | 302 | 10 | 3 | 0 | 6 | - | **keep** | its own structure with 6 dependents and 3 atom dependencies; no single host |
| swift-set-ordered | 305 | 2 | 8 | 4 | 2 | - | **keep** | depends on molecules (swift-buffer-linear, swift-hash-table, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-buffer-slots | 316 | 2 | 11 | 1 | 1 | - | **keep** | depends on molecules (swift-memory-allocation): folding would give an atom a molecule edge |
| swift-queue-linked | 319 | 5 | 3 | 2 | 0 | - | **keep** | depends on molecules (swift-buffer-linked, swift-buffer-ring): folding would give an atom a molecule edge |
| swift-copy-on-write | 337 | 4 | 1 | 0 | 2 | - | **keep** | its own structure with 2 dependents and 1 atom dependencies; no single host |
| swift-tree-column | 349 | 6 | 5 | 5 | 0 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared, swift-tree): folding would give an atom a molecule edge |
| swift-async-waiter | 362 | 12 | 7 | 4 | 5 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-snapshot | 367 | 13 | 1 | 0 | 0 | - | **keep** | no consumer in the workspace, but 367 source lines of its own: ask, don't fold |
| swift-async-sequence | 397 | 16 | 1 | 1 | 0 | - | **keep** | depends on molecules (swift-async-stream): folding would give an atom a molecule edge |
| swift-source | 398 | 8 | 2 | 0 | 9 | - | **keep** | its own structure with 9 dependents and 2 atom dependencies; no single host |
| swift-buffer-linked | 404 | 5 | 4 | 2 | 2 | - | **keep** | depends on molecules (swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-token | 447 | 3 | 1 | 0 | 1 | - | **keep** | its own structure with 1 dependents and 1 atom dependencies; no single host |
| swift-algebra-modular | 455 | 7 | 8 | 0 | 0 | - | **keep** | no consumer in the workspace, but 455 source lines of its own: ask, don't fold |
| swift-tree | 556 | 19 | 8 | 5 | 3 | Property | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared, swift-stack): folding would give an atom a molecule edge |
| swift-async-broadcast | 560 | 15 | 8 | 9 | 1 | - | **keep** | depends on molecules (swift-async-barrier, swift-async-channel, swift-buffer-linear, swift-buffer-ring, swift-dictionary, swift-dictionary-ordered, swift-hash-table, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-dictionary | 561 | 3 | 5 | 4 | 10 | - | **keep** | depends on molecules (swift-buffer-linear, swift-hash-table, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-async-semaphore | 612 | 8 | 5 | 3 | 2 | - | **keep** | depends on molecules (swift-async-waiter, swift-buffer-ring, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-list-linked | 631 | 15 | 13 | 1 | 0 | - | **keep** | depends on molecules (swift-buffer-linked): folding would give an atom a molecule edge |
| swift-benchmark | 634 | 26 | 3 | 0 | 2 | - | **keep** | its own structure with 2 dependents and 3 atom dependencies; no single host |
| swift-dictionary-ordered | 634 | 4 | 7 | 6 | 8 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-dictionary, swift-hash-table, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-array | 636 | 10 | 13 | 3 | 7 | - | **keep** | depends on molecules (swift-buffer-linear, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-ownership-shared | 682 | 1 | 13 | 4 | 30 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-hash-table, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-foundation-extensions | 775 | 1 | 0 | 0 | 1 | - | **keep** | its own structure with 1 dependents and 0 atom dependencies; no single host |
| swift-cache | 813 | 23 | 9 | 6 | 1 | Effect | **keep** | depends on molecules (swift-array, swift-async-waiter, swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-layout | 1117 | 35 | 5 | 0 | 3 | Boundary | **keep** | its own structure with 3 dependents and 5 atom dependencies; no single host |
| swift-memory-allocation | 1301 | 32 | 13 | 0 | 51 | MemoryAligned, MemoryAllocatorArena, MemoryInline, MemorySmall | **keep** | its own structure with 51 dependents and 13 atom dependencies; no single host |
| swift-tree-n | 1306 | 38 | 9 | 7 | 0 | - | **keep** | depends on molecules (swift-array, swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared, swift-stack, swift-tree): folding would give an atom a molecule edge |
| swift-buffer-slab | 1339 | 15 | 14 | 2 | 1 | - | **keep** | depends on molecules (swift-bit-vector, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-lint | 1349 | 42 | 6 | 2 | 3 | - | **keep** | depends on molecules (swift-diagnostic, swift-source): folding would give an atom a molecule edge |
| swift-hash-table | 1354 | 19 | 13 | 3 | 17 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-slots, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-machine | 1394 | 32 | 3 | 1 | 3 | Analyze | **keep** | depends on molecules (swift-graph): folding would give an atom a molecule edge |
| swift-calendar-gregorian | 1412 | 29 | 9 | 0 | 5 | Julian | **keep** | its own structure with 5 dependents and 9 atom dependencies; no single host |
| swift-tensor | 1556 | 36 | 12 | 2 | 0 | - | **keep** | depends on molecules (swift-buffer-linear, swift-memory-allocation): folding would give an atom a molecule edge |
| swift-lexer | 1610 | 12 | 11 | 1 | 3 | LexerStandardLibraryIntegration | **keep** | depends on molecules (swift-token): folding would give an atom a molecule edge |
| swift-tree-keyed | 1748 | 37 | 9 | 9 | 2 | - | **keep** | depends on molecules (swift-buffer-linear, swift-buffer-ring, swift-dictionary, swift-dictionary-ordered, swift-hash-table, swift-memory-allocation, swift-ownership-shared, swift-stack, swift-tree): folding would give an atom a molecule edge |
| swift-parser-machine | 1862 | 51 | 9 | 3 | 2 | - | **keep** | depends on molecules (swift-graph, swift-machine, swift-stack): folding would give an atom a molecule edge |
| swift-graph | 1907 | 31 | 15 | 9 | 5 | Algorithms | **keep** | depends on molecules (swift-array, swift-bit-vector, swift-buffer-linear, swift-buffer-ring, swift-hash-table, swift-memory-allocation, swift-ownership-shared, swift-set-ordered, swift-stack): folding would give an atom a molecule edge |
| swift-buffer-linear | 2102 | 30 | 14 | 1 | 38 | - | **keep** | depends on molecules (swift-memory-allocation): folding would give an atom a molecule edge |
| swift-buffer-ring | 2271 | 30 | 16 | 1 | 25 | - | **keep** | depends on molecules (swift-memory-allocation): folding would give an atom a molecule edge |
| swift-binary-parser | 2302 | 50 | 13 | 4 | 2 | ASCIIDecimalMachine | **keep** | depends on molecules (swift-buffer-linear, swift-graph, swift-machine, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-test | 2409 | 54 | 10 | 2 | 2 | - | **keep** | depends on molecules (swift-benchmark, swift-source): folding would give an atom a molecule edge |
| swift-async-channel | 2681 | 71 | 11 | 6 | 5 | - | **keep** | depends on molecules (swift-async-barrier, swift-async-waiter, swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
| swift-bit-vector | 3232 | 67 | 14 | 0 | 2 | - | **keep** | its own structure with 2 dependents and 14 atom dependencies; no single host |
| swift-async-stream | 3632 | 72 | 12 | 6 | 4 | - | **keep** | depends on molecules (swift-async-broadcast, swift-async-channel, swift-buffer-linear, swift-buffer-ring, swift-memory-allocation, swift-ownership-shared): folding would give an atom a molecule edge |
