import pickle, re, collections
d = pickle.load(open('ctx.pkl','rb')); imp,tg,prod,tdep,traits,ntyp,pk,layer = [d[k] for k in ('imp','tg','prod','tdep','traits','ntyp','pk','layer')]
norm = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
APPLE = {'AppKit','UIKit','SwiftUI','AVFoundation','ScreenCaptureKit','Metal','MetalKit','CoreGraphics','Speech','CoreImage','QuartzCore','WebKit','CloudKit','CoreText','CoreMedia','CoreVideo','VideoToolbox','AudioToolbox','CoreAudio','Cocoa','ImageIO','Vision','CoreML','Accelerate','Combine','Security','Network','CryptoKit','IOKit','AVFAudio','PDFKit','UniformTypeIdentifiers','MetalPerformanceShaders','CoreServices','StoreKit','AppIntents','NaturalLanguage','Translation','SwiftData','CoreData','os','OSLog','CoreFoundation','Observation'}
FND = {'Foundation','FoundationEssentials','FoundationNetworking','FoundationInternationalization'}
byname = {p.split('/')[1]: p for p in pk}
def stem(p): 
    n=p.split('/')[1]; return n[6:] if n.startswith('swift-') else n
plat=[]; fnd_main=[]; fnd_int=[]; peer=[]; 
for p in pk:
    reg=[t for t in tg.get(p,[]) if t[1]=='regular']
    pn=norm(stem(p))
    # deps used by which targets
    for (t,k,f,l) in reg:
        ims=imp.get((p,t),set())
        a=ims & APPLE; fo=ims & FND
        ts = 'Test Support' in t
        if a: plat.append((p,t,sorted(a),norm(t)==pn, l))
        if fo:
            (fnd_int if 'Foundation' in t else fnd_main).append((p,t,norm(t)==pn,ts,l))
        # peer glue: external product deps
        ext=[x for x in tdep.get((p,t),[]) if x[0]=='product' and x[2]]
        words=t.split(' ')
        for (k2,n,dp,pl,tr) in ext:
            dn = norm(dp[6:] if dp.startswith('swift-') else dp)
            # target named for both: contains other package stem as word(s) and own stem
            if norm(t)!=pn and dn and dn in norm(t) and dn!=pn and not ts:
                peer.append((p,t,dp,tr,ntyp.get((p,t),0),l, pn in norm(t)))
print('PLATFORM targets', len(plat), 'of which primary', sum(1 for x in plat if x[3]))
c=collections.Counter((layer[x[0]], x[3]) for x in plat); print(c)
for x in plat: print('  ', layer[x[0]][:4], x[0].split('/')[1], '|', x[1], '|', ','.join(x[2]), '| primary' if x[3] else '', x[4])
print('FOUNDATION in targets not named Foundation', len(fnd_main), collections.Counter((layer[x[0]],x[2],x[3]) for x in fnd_main))
for x in fnd_main: print('  ', layer[x[0]][:4], x[0].split('/')[1], '|', x[1], '| primary' if x[2] else '', '| TS' if x[3] else '')
print('FOUNDATION INTEGRATION targets', len(fnd_int), collections.Counter(layer[x[0]] for x in fnd_int))
pickle.dump(peer, open('peer.pkl','wb'))
