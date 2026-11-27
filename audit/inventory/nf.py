import pickle, re, collections, sqlite3
d = pickle.load(open('ctx.pkl','rb')); imp,tg,prod,tdep,traits,ntyp,pk,layer = [d[k] for k in ('imp','tg','prod','tdep','traits','ntyp','pk','layer')]
c=sqlite3.connect('inv.db')
norm = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
APPLE = {'AppKit','UIKit','SwiftUI','AVFoundation','ScreenCaptureKit','Metal','MetalKit','CoreGraphics','Speech','CoreImage','QuartzCore','WebKit','CloudKit','CoreText','CoreMedia','CoreVideo','Security','Network','CryptoKit','AVFAudio','ImageIO','Combine','SwiftData','os','OSLog','CoreFoundation','WinSDK','Glibc','Darwin','Musl','Foundation','FoundationEssentials','FoundationNetworking','FoundationInternationalization'}
def stem(p):
    n=p.split('/')[1]; return n[6:] if n.startswith('swift-') else n
cls=collections.Counter(); bylayer=collections.Counter(); ex=collections.defaultdict(list)
totreg=0
for p in pk:
    reg=[t for t in tg.get(p,[]) if t[1]=='regular']; totreg+=len(reg)
    if len(reg)<2: 
        for t in reg: cls['only target']+=1
        continue
    pn=norm(stem(p))
    dep={t[0]:set() for t in reg}; idep={t[0]:set() for t in reg}; gated={t[0]:False for t in reg}
    for t in reg:
        for (k,n,dp,pl,tr) in tdep.get((p,t[0]),[]):
            if k=='product' and dp: dep[t[0]].add(dp)
            elif n in dep: idep[t[0]].add(n)
            if tr or pl: gated[t[0]]=True
    names=[t[0] for t in reg]
    prim=next((n for n in names if norm(n)==pn), None)
    # full external closure for every target
    def clo(n,seen=None):
        seen=seen or set(); 
        if n in seen: return set()
        seen.add(n); s=set(dep[n])
        for m in idep[n]: s|=clo(m,seen)
        return s
    # base footprint: the footprint of the primary (or union-min: smallest closure)
    base = clo(prim) if prim else min((clo(n) for n in names), key=len)
    for t in reg:
        n=t[0]
        ims=imp.get((p,n),set())
        if n==prim: k='primary'
        elif 'Test Support' in n: k='mech: Test Support'
        elif 'Shims' in n or t[1]=='system': k='mech: Shims'
        elif ims & APPLE: k='mech: platform or Foundation'
        elif 'Macro' in n or 'Syntax' in n or ims & {'SwiftSyntax','SwiftSyntaxMacros','SwiftCompilerPlugin'}: k='mech: macro'
        elif clo(n)-base: k='footprint grows'
        else: k='same footprint as primary'
        cls[k]+=1; bylayer[(layer[p],k)]+=1
        if k=='same footprint as primary': ex[p].append(n)
print('regular targets',totreg); 
for k,v in cls.most_common(): print(f'  {k:32}{v}')
for k in sorted(bylayer): 
    if k[1] in('same footprint as primary','footprint grows'): print('  ',k,bylayer[k])
pickle.dump(dict(ex),open("samefp.pkl","wb"))
for p,v in sorted(ex.items(), key=lambda x:-len(x[1]))[:25]: print('   ',p.split('/')[1],len(v),v[:5])
# products
libs=sum(1 for p in pk for x in prod.get(p,[]) if x[1]=='library'); print('library products',libs,'packages',len(pk))
