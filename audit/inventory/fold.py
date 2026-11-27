import sqlite3, collections, pickle, re, json, functools, sys
sys.setrecursionlimit(100000)
c=sqlite3.connect('inv.db'); d=pickle.load(open('ctx.pkl','rb')); pk=d['pk']; layer=dict(d['layer'])
rank={'atoms':1,'molecules':2,'standards':3,'compositions':4}
dep=collections.defaultdict(set)
for p,i,loc in c.execute("select package,identity,location from package_dependencies"):
    m=re.search(r'github\.com[/:]([^/]+)/([^/.]+)',loc or '')
    if p in pk and m:
        q=f"{m.group(1)}/{m.group(2)}"
        if q in pk and q!=p: dep[p].add(q)
rows=json.load(open('xy.json'))
byname={p.split('/')[1]:p for p in pk}
kinds=[(r['repo'],byname[r['parent']]) for r in rows if r['owns'] and '.' in r['owns'] and r['parent'] and r['dep_parent'] and r['layer']!='standards']
def reach(a,graph):
    seen=set(); st=[a]
    while st:
        x=st.pop()
        for y in graph[x]:
            if y not in seen: seen.add(y); st.append(y)
    return seen
merged={}  # kind -> parent
def canon(p):
    while p in merged: p=merged[p]
    return p
changed=True; why={}
while changed:
    changed=False
    g=collections.defaultdict(set)
    for p in pk:
        for q in dep[p]:
            a,b=canon(p),canon(q)
            if a!=b: g[a].add(b)
    for k,par in kinds:
        if k in merged: continue
        par=canon(par)
        others=g[k]-{par}
        cyc=[o for o in others if par in reach(o,g) or o==par]
        up=[o for o in others if rank[layer[o]]>rank[layer[par]]]
        if cyc: why[k]=('cycle',sorted(x.split('/')[1][6:] for x in cyc)[:4])
        elif up and not all(layer[o]=='molecules' and layer[par]=='atoms' for o in up): why[k]=('layer',sorted(x.split('/')[1][6:] for x in up)[:4])
        elif up: why[k]=('needs-molecule',sorted(x.split('/')[1][6:] for x in up)[:4])
        else:
            merged[k]=par; why[k]=('fold',[]); changed=True
res=collections.Counter(v[0] for v in why.values()); print(res)
for kind in ('fold','needs-molecule','cycle','layer'):
    print(kind.upper())
    for k,v in sorted(why.items()):
        if v[0]==kind: print('  ',k.split('/')[1][6:], '->', canon(k).split('/')[1][6:] if kind=='fold' else ','.join(v[1]))
pickle.dump((merged,why,dict(dep)),open('fold.pkl','wb'))
