#!/usr/bin/env python3
"""The work list per package, from the pickles of xy.py, tg.py, nf.py, partial.py and fold.py. Writes worklist.tsv:
package, rule, action, detail. Run the other scripts first (see README)."""
import pickle, json, re, collections, sqlite3
A='/home/user/analysis/'
d=pickle.load(open(A+'ctx.pkl','rb')); imp,tg,prod,tdep,pk,layer=[d[k] for k in ('imp','tg','prod','tdep','pk','layer')]
c=sqlite3.connect(A+'inv.db')
norm=lambda s: re.sub(r'[^a-z0-9]','',s.lower())
def stem(p):
    n=p.split('/')[1]; return n[6:] if n.startswith('swift-') else n
out=[]
add=lambda p,r,a,x='': out.append((p,r,a,x))
# N5 strata
STR=re.compile(r'\b(Primitive|Primitives|Core|Shared|Protocol|Namespace|Internal|Base|Common)$')
for p,ts in pickle.load(open(A+'samefp.pkl','rb')).items():
    for t in ts:
        if STR.search(t): add(p,'N5','fold stratum target into the primary target',t)
# N3 kinds
merged,why,dep=pickle.load(open(A+'fold.pkl','rb'))
for k,v in why.items():
    a={'fold':'fold kind package into its parent','cycle':'kind package: a fold makes a cycle; decide in the base redesign','layer':'kind package stays: it needs a higher layer','needs-molecule':'kind package: needs a molecule; decide in the base redesign'}[v[0]]
    add(k,'N3',a,(merged.get(k,'') if v[0]=='fold' else ','.join(v[1])))
# N4 glue repositories: no public type of their own root, two parents by name
rows=json.load(open(A+'xy.json'))
for r in rows:
    if r['layer']=='standards': continue
    if r['parent'] and r['tailpkg'] and r['dep_tail'] and not r['owns'] and r['ntypes']<=3: add(r['repo'],'N4','glue repository: fold into the higher package behind a trait',f"{r['parent']} + {r['tailpkg']}")
    if r['ntypes']==0 and not r['tailpkg']: add(r['repo'],'N4','repository declares no public type: fold or delete',r['parent'] or '')
# N4 glue targets without a trait
seen=set()
for (p,t,q,ql,tr,named,nt,ne,l) in pickle.load(open(A+'partial.pkl','rb')):
    if (p,t,q) in seen: continue
    seen.add((p,t,q))
    if not tr: add(p,'N4/I7','dependency only a secondary target needs has no trait',f'{t} -> {q}')
# N6 products
for p in pk:
    libs=[x for x in prod.get(p,[]) if x[1]=='library']
    if not libs: continue
    pn=norm(stem(p)); primary=next((x[0] for x in libs if norm(x[0])==pn),None)
    if not primary: add(p,'N6','no product named for the package',', '.join(x[0] for x in libs[:4]))
    else:
        o=[x[0] for x in libs if x[0]!=primary and not x[0].startswith(primary+' ')]
        if o: add(p,'N6','product is not the primary name plus a role',', '.join(o[:6]))
# I2 platform framework in the primary target
APPLE={'AppKit','UIKit','SwiftUI','AVFoundation','ScreenCaptureKit','Metal','MetalKit','CoreGraphics','Speech','CoreImage','QuartzCore','WebKit','CloudKit','CoreText','CoreMedia','CoreVideo','Security','Network','CryptoKit','AVFAudio','ImageIO','Combine','SwiftData'}
for p in pk:
    for t in tg.get(p,[]):
        if t[1]=='regular' and norm(t[0])==norm(stem(p)) and imp.get((p,t[0]),set())&APPLE: add(p,'I2','primary target imports a platform framework',','.join(sorted(imp[(p,t[0])]&APPLE)))
# N8 organization
multi={r['repo'] for r in rows}
def canon(p):
    while p in merged: p=merged[p]
    return p
g=collections.defaultdict(set)
for p in pk:
    for q in dep.get(p,()):
        a,b=canon(p),canon(q)
        if a!=b: g[a].add(b)
L=dict(layer); ch=True
while ch:
    ch=False
    for p in pk:
        if p not in merged and L[p]=='molecules' and p not in multi and all(L[q]=='atoms' for q in g[p]): L[p]='atoms'; ch=True; add(p,'N8','root package: move to swift-atoms')
for p in pk:
    if p in merged: continue
    m=sorted(stem(q) for q in g[p] if L[q]=='molecules')
    if m and p not in multi and L[p] in ('atoms','molecules'): add(p,'N8','root package depends on a molecule: decide in the base redesign',','.join(m))
# N7 duplicate dotted paths
kinds={(p,t[0]):t[1] for p in tg for t in tg[p]}
paths=collections.defaultdict(set)
for p,t,path in c.execute("select package,target,path from types where access='public' and kind<>'typealias'"):
    if p in pk and kinds.get((p,t))=='regular' and 'Test Support' not in t: paths[path].add(p)
for path,ps in paths.items():
    if len(ps)>1:
        for p in ps: add(p,'N7','public dotted path is declared in more than one package',path)
out.sort()
open(A+'worklist.tsv','w').write('package\trule\taction\tdetail\n'+''.join('\t'.join(r)+'\n' for r in out))
cnt=collections.Counter((r[1],r[2]) for r in out)
for k,v in sorted(cnt.items()): print(v,k[0],k[1])
print(len(out),'items in',len({r[0] for r in out}),'packages')
