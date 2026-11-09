#!/usr/bin/env python3
"""Two mechanical repairs from errors.txt, made in each package's real checkout (the clone's origin):
`(a..<b).forEach { i in` inside a result builder becomes `for i in a..<b {`, and a @Test display name that repeats the
function's own name moves into the backticked function name."""
import os, re, subprocess

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errs = open(os.path.join(W, "errors.txt")).read().split("\n")
origins = {}


def real(rel):
    parts = rel.split("/")
    p = "/".join(parts[:2])
    if p not in origins:
        r = subprocess.run(["git", "-C", os.path.join(W, "repos", p), "remote", "get-url", "origin"], capture_output=True, text=True)
        origins[p] = r.stdout.strip() if r.returncode == 0 else None
    return os.path.join(origins[p], "/".join(parts[2:])) if origins[p] else None


done = set()
for e in errs:
    m = re.match(r"^([^ ][^:]*\.swift):(\d+):\d+: error: type '\(\)' cannot conform", e)
    if m and m.group(1) not in done:
        done.add(m.group(1))
        f = real(m.group(1))
        if not f:
            continue
        s = open(f).read()
        s2, n = re.subn(r"\(([^()\n]+?(?:\.\.\.|\.\.<)[^()\n]+?)\)\.forEach \{ (\w+) in", r"for \2 in \1 {", s)
        if n:
            open(f, "w").write(s2)
            print(f"builder loops {n}: {m.group(1)}")
for e in errs:
    m = re.match(r"^([^ ][^:]*\.swift):(\d+):\d+: error: Attribute 'Test' specifies display name '([^']+)' for function with implicit display name '([^']+)'", e)
    if not m:
        continue
    f = real(m.group(1))
    if not f:
        continue
    L = open(f).read().split("\n")
    i = int(m.group(2)) - 1
    shown, implicit = m.group(3), m.group(4)
    for j in (i, i + 1, i + 2):
        if j < len(L) and f"`{implicit}`" in L[j] and "func " in L[j]:
            L[j] = L[j].replace(f"`{implicit}`", f"`{shown}`", 1)
            break
    else:
        continue
    L[i] = re.sub(r'@Test\(\s*"' + re.escape(shown) + r'"\s*\)', "@Test", L[i])
    L[i] = re.sub(r'@Test\(\s*"' + re.escape(shown) + r'"\s*,\s*', "@Test(", L[i])
    open(f, "w").write("\n".join(L))
    print(f"test name: {m.group(1)}:{i + 1} {shown}")
