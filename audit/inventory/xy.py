import sqlite3, re, collections, json
c = sqlite3.connect('/home/user/analysis/inv.db')
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
layer = {r[0]: r[1] for r in c.execute("select path, layer from repositories")}
pk = [r[0] for r in c.execute("select package from packages where nested=0")]
names = {p.split('/')[1]: p for p in pk if layer.get(p) in ('atoms','molecules','standards','compositions')}
# public types in regular targets
types = collections.defaultdict(list)
for p, t, path, kind, inext in c.execute("""select t.package, t.target, t.path, t.kind, t.in_extension from types t join targets g on g.package=t.package and g.target=t.target
   where g.kind in ('regular','macro','executable') and t.access in ('public','package')"""):
    types[p].append((t, path, kind, inext))
deps = collections.defaultdict(set)
for p, i in c.execute("select package, identity from package_dependencies"): deps[p].add(i)
rows = []
for name, p in sorted(names.items()):
    w = name.split('-')[1:] if name.startswith('swift-') else name.split('-')
    if len(w) < 2: continue
    ts = types[p]
    roots = {x[1] for x in ts if '.' not in x[1] and x[2] != 'typealias'}
    allpaths = {norm(x[1]): x[1] for x in ts}
    full = norm(''.join(w))
    # candidate dotted readings
    res = {'repo': p, 'layer': layer[p], 'words': w}
    res['parent'] = next((('swift-' + '-'.join(w[:k])) for k in range(len(w)-1, 0, -1) if ('swift-' + '-'.join(w[:k])) in names), None)
    res['tailpkg'] = next((('swift-' + '-'.join(w[k:])) for k in range(1, len(w)) if ('swift-' + '-'.join(w[k:])) in names), None)
    res['dep_parent'] = bool(res['parent'] and res['parent'] in deps[p])
    res['dep_tail'] = bool(res['tailpkg'] and res['tailpkg'] in deps[p])
    # does it declare a path whose normalised dotted form equals full name
    hit = None
    for tpath in sorted({x[1] for x in ts}, key=len):
        if norm(tpath) == full: hit = tpath; break
    res['owns'] = hit
    res['roots'] = sorted(roots)[:6]
    res['nroots'] = len(roots)
    res['ntypes'] = len(ts)
    # foreign-root nested public types
    foreign = collections.Counter(x[1].split('.')[0] for x in ts if '.' in x[1] and x[1].split('.')[0] not in roots)
    res['foreign'] = foreign.most_common(4)
    rows.append(res)
json.dump(rows, open('/home/user/analysis/xy.json','w'))
import sys
cl = collections.Counter()
for r in rows:
    o = r['owns']
    if o and '.' in o: k = 'dotted'
    elif o: k = 'compound-root'
    else: k = 'other'
    r['class'] = k
    cl[(r['layer'], k, bool(r['parent']), r['dep_parent'])] += 1
for k, v in sorted(cl.items()): print(k, v)
print(len(rows), 'multi-word of', len(names))
json.dump(rows, open('/home/user/analysis/xy.json','w'))
