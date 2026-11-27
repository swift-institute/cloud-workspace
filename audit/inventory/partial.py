import pickle, re, collections, sqlite3
d = pickle.load(open('ctx.pkl','rb')); imp,tg,prod,tdep,traits,ntyp,pk,layer = [d[k] for k in ('imp','tg','prod','tdep','traits','ntyp','pk','layer')]
c = sqlite3.connect('inv.db')
next_ = collections.Counter()
for p,t,n in c.execute("select package,target,count(*) from extensions where conformances<>'' group by 1,2"): next_[(p,t)]=n
norm = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
byname={p.split('/')[1]:p for p in pk}
def stem(n): return n[6:] if n.startswith('swift-') else n
rows=[]
for p in pk:
    reg=[t for t in tg.get(p,[]) if t[1]=='regular' and 'Test Support' not in t[0]]
    if len(reg)<2: continue
    pn=norm(stem(p.split('/')[1]))
    primary=[t for t in reg if norm(t[0])==pn]
    # package deps per target (direct)
    dep={t[0]:{} for t in reg}
    for t in reg:
        for (k,n,dp,pl,tr) in tdep.get((p,t[0]),[]):
            if k=='product' and dp: dep[t[0]][dp]=tr or dep[t[0]].get(dp,'')
    # internal closure for primary
    if not primary: continue
    pt=primary[0][0]
    seen={pt}; st=[pt]; pdeps=set(dep[pt])
    while st:
        x=st.pop()
        for (k,n,dp,pl,tr) in tdep.get((p,x),[]):
            if k=='target' and n in dep and n not in seen: seen.add(n); st.append(n); pdeps|=set(dep[n])
    for t in reg:
        if t[0] in seen: continue
        extra={q:tr for q,tr in dep[t[0]].items() if q not in pdeps}
        for q,tr in extra.items():
            ql=layer.get(byname.get(q,''),'ext')
            named = norm(stem(q)) in norm(t[0])
            rows.append((p,t[0],q,ql,tr,named,ntyp.get((p,t[0]),0),next_.get((p,t[0]),0),t[3]))
pickle.dump(rows,open('partial.pkl','wb'))
print(len(rows),'partial target->package edges in', len({(r[0],r[1]) for r in rows}),'targets of',len({r[0] for r in rows}),'packages')
c1=collections.Counter((layer[r[0]], 'gated' if r[4] else 'ungated', 'named' if r[5] else 'unnamed') for r in rows)
for k in sorted(c1): print(k,c1[k])
c2=collections.Counter((layer[r[0]], r[3]) for r in rows); print(sorted(c2.items()))
