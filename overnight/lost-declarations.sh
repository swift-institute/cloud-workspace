#!/usr/bin/env bash
# Lists declaration lines (func/init/var/let/case/struct/enum/class/actor/protocol/typealias/extension, normalized)
# present in origin/main's Sources but not in HEAD's: a move keeps them, so a loss means content was dropped.
# Module selector rewrites (A::B for A.B) are normalized away. Prints package and count, then the lines with -v.
cd "$(dirname "$0")/.."
norm() { sed -E 's/^\s+//; s/\s*\{.*$//; s/::/./g; s/\s+/ /g; s/\b(package|internal|fileprivate|private) //g' | grep -E '^(@[A-Za-z_]+(\([^)]*\))? )*((public|package|internal|private|fileprivate|open|static|final|mutating|nonmutating|override|nonisolated|consuming|borrowing|indirect|convenience|required|lazy) )*(func|init|var|let|case|struct|enum|class|actor|protocol|typealias|extension|subscript)\b' | sort -u; }
for p in $(overnight/packages.sh 2>/dev/null); do d=repos/$p
  [ -n "$(git -C $d log --oneline origin/main..HEAD 2>/dev/null | head -1)" ] || continue
  m=$(comm -23 <(git -C $d grep -h "" origin/main -- Sources 2>/dev/null | norm) <(git -C $d grep -h "" HEAD -- Sources 2>/dev/null | norm))
  n=$(printf "%s" "$m" | grep -c .)
  [ "$n" -gt 0 ] && { echo "$p $n"; [ "$1" = -v ] && echo "$m" | head -5 | sed 's/^/    /'; }
done
