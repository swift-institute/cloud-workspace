import pickle, collections, sqlite3, json, sys
sys.setrecursionlimit(100000)
d=pickle.load(open('ctx.pkl','rb')); pk=d['pk']
merged,why,dep=pickle.load(open('fold.pkl','rb'))
rows=json.load(open('xy.json')); byname={p.split('/')[1]:p for p in pk}
allk={r['repo']:byname[r['parent']] for r in rows if r['owns'] and '.' in r['owns'] and r['parent'] and r['dep_parent'] and r['layer'] in ('atoms','molecules')}
sn=lambda p:p.split('/')[1][6:]
c=sqlite3.connect('inv.db'); w=collections.Counter()
for a,b,n in c.execute("select package,type_package,sum(count) from resolved_references where package<>type_package and target not like '%Tests' and target not like '%Test Support' group by 1,2"): w[(a,b)]+=n
def canon(p):
    while p in allk: p=allk[p]
    return p
def sccs(cuts):
    g=collections.defaultdict(set)
    for p in pk:
        for q in dep.get(p,()):
            if (sn(p),sn(q)) in cuts: continue
            a,b=canon(p),canon(q)
            if a!=b: g[a].add(b)
    idx={}; low={}; st=[]; on=set(); out=[]; i=[0]
    def sc(v):
        idx[v]=low[v]=i[0]; i[0]+=1; st.append(v); on.add(v)
        for x in g[v]:
            if x not in idx: sc(x); low[v]=min(low[v],low[x])
            elif x in on: low[v]=min(low[v],idx[x])
        if low[v]==idx[v]:
            comp=[]
            while True:
                x=st.pop(); on.discard(x); comp.append(x)
                if x==v: break
            if len(comp)>1: out.append(comp)
    for v in list(g):
        if v not in idx: sc(v)
    return out,g
# greedy: repeatedly cut the original edge inside an SCC that (a) is not kind->anything introduced? any edge; choose one maximizing (cycle participation)/ (weight+1): approximate by trying each low-weight edge and measuring SCC size reduction
cuts=set()
for step in range(40):
    comps,g=sccs(cuts)
    if not comps: break
    size=sum(len(x) for x in comps)
    cand=[]
    for comp in comps:
        s=set(comp)
        for p in pk:
            for q in dep.get(p,()):
                if (sn(p),sn(q)) in cuts: continue
                if canon(p) in s and canon(q) in s and canon(p)!=canon(q): cand.append((w[(p,q)],sn(p),sn(q)))
    cand=sorted(set(cand))[:60]
    best=None
    for wt,a,b in cand:
        cs,_=sccs(cuts|{(a,b)}); ns=sum(len(x) for x in cs)
        gain=size-ns
        score=gain/(wt+1)
        if gain>0 and (best is None or score>best[0]): best=(score,wt,a,b,ns)
    if not best:
        # no single edge reduces: cut the lightest
        wt,a,b=cand[0]; cuts.add((a,b)); print(f'cut {a} -> {b} (refs {wt}), no size change'); continue
    cuts.add((best[2],best[3])); print(f'cut {best[2]} -> {best[3]} (refs {best[1]}): cycle members {size} -> {best[4]}')
comps,_=sccs(cuts); print('left:',[sorted(sn(x) for x in comp) for comp in comps]); print(len(cuts),'cuts, total references to rewrite:',sum(w[(byname["swift-"+a],byname["swift-"+b])] for a,b in cuts))
