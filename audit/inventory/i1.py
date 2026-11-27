import sqlite3, re, collections, pickle
c = sqlite3.connect('inv.db')
d = pickle.load(open('ctx.pkl','rb')); pk=d['pk']; layer=d['layer']; tg=d['tg']
norm = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
def stem(p):
    n=p.split('/')[1]; return n[6:] if n.startswith('swift-') else n
kinds={(p,t[0]):t[1] for p in tg for t in tg[p]}
# nested depth-2 public nominal types with representation, in regular targets
T=[]
for p,t,path,kind,sp,cs,inext in c.execute("select package,target,path,kind,stored_properties,cases,in_extension from types where access='public' and kind in ('struct','enum','class','actor')"):
    if p not in pk or kinds.get((p,t))!='regular' or 'Test Support' in t: continue
    parts=path.split('.')
    if len(parts)!=2: continue
    T.append((p,t,path,kind,sp,cs))
# references from same package regular targets, positions that mean "model names it"
named=collections.defaultdict(set)  # (p,path) -> set of from
for p,t,frm,pos,tp,tt,tpkg in c.execute("select package,target,\"from\",position,type_path,type_target,type_package from resolved_references where package=type_package and position in ('stored','parameter','return','case','generic_argument','alias','inheritance','constraint')"):
    if kinds.get((p,t))!='regular': continue
    parts=tp.split('.')
    if len(parts)<2: continue
    key='.'.join(parts[:2])
    if frm==key or frm.startswith(key+'.'): continue
    named[(p,key)].add((t,frm))
res=collections.Counter(); ex=collections.defaultdict(list); per=collections.Counter()
for p,t,path,kind,sp,cs in T:
    root=path.split('.')[0]
    own_root = norm(root)==norm(stem(p)) or norm(stem(p)).startswith(norm(root))
    rep = sp>0 or cs>0
    n = bool(named.get((p,path)))
    k=(layer[p], 'own-root' if own_root else 'foreign-root', 'named-by-model' if n else 'unnamed', 'rep' if rep else 'norep')
    res[k]+=1
    if not n and rep and own_root: ex[layer[p]].append((p,path)); per[p]+=1
for k in sorted(res): print(k,res[k])
print('packages holding an unnamed kind-with-representation:', len(per), 'types:', sum(per.values()))
print(per.most_common(25))
pickle.dump(ex,open('i1.pkl','wb'))
