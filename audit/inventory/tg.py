import sqlite3, re, collections, json
c = sqlite3.connect('/home/user/analysis/inv.db')
layer = {r[0]: r[1] for r in c.execute("select path, layer from repositories")}
IN = ('atoms','molecules','standards','compositions')
pk = {r[0]: r[1] for r in c.execute("select package,name from packages where nested=0") if layer.get(r[0]) in IN}
FW = {'AppKit','UIKit','SwiftUI','AVFoundation','ScreenCaptureKit','Metal','MetalKit','CoreGraphics','Speech','CoreImage','QuartzCore','WebKit','CloudKit','CoreText','CoreMedia','CoreVideo','VideoToolbox','AudioToolbox','CoreAudio','Cocoa','ImageIO','Vision','CoreML','Accelerate','Combine','Observation','XCTest','Testing','os','OSLog','CoreFoundation','Security','Network','CryptoKit','IOKit','AVFAudio','PDFKit','UniformTypeIdentifiers','MetalPerformanceShaders','CoreServices','StoreKit','WidgetKit','AppIntents','NaturalLanguage','Translation','SwiftData','CoreData','CoreLocation','MapKit','UserNotifications','WinSDK','Musl','Android','Bionic','Glibc','Darwin','Foundation','FoundationEssentials','FoundationNetworking','Dispatch','Synchronization','_Concurrency','Swift','RegexBuilder','_StringProcessing','Distributed','SwiftSyntax','SwiftParser','SwiftSyntaxMacros','SwiftCompilerPlugin','SwiftSyntaxBuilder','SwiftDiagnostics','SwiftOperators','SwiftSyntaxMacroExpansion','SwiftParserDiagnostics','SwiftIfConfig','SwiftBasicFormat','SwiftSyntaxMacrosTestSupport','SwiftSyntaxMacrosGenericTestSupport'}
imp = collections.defaultdict(set)
for p,t,m in c.execute("select package,target,module from imports"): imp[(p,t)].add(m.split('.')[0])
tg = collections.defaultdict(list)
for p,t,k,path,f,l in c.execute("select package,target,kind,path,files,lines from targets"):
    if p in pk: tg[p].append((t,k,f,l))
prod = collections.defaultdict(list)
for p,n,k,lt,ts in c.execute("select package,name,kind,library_type,targets from products"):
    if p in pk: prod[p].append((n,k,lt,ts.split(',')))
tdep = collections.defaultdict(list)
for p,t,k,n,dp,pl,tr in c.execute("select package,target,kind,name,dependency_package,platforms,traits from target_dependencies"):
    tdep[(p,t)].append((k,n,dp,pl,tr))
traits = collections.defaultdict(list)
for p,n,e in c.execute("select package,name,enables from traits"): traits[p].append((n,e))
ntyp = collections.Counter(); 
for p,t,n in c.execute("select package,target,count(*) from types where access in ('public','package') group by 1,2"): ntyp[(p,t)] = n
json.dump({'pk':pk,'layer':layer}, open('ctx.json','w'))
import pickle; pickle.dump(dict(imp=dict(imp),tg=dict(tg),prod=dict(prod),tdep=dict(tdep),traits=dict(traits),ntyp=dict(ntyp),pk=pk,layer=layer,FW=FW), open('ctx.pkl','wb'))
# summary
def prim(p):
    n = p.split('/')[1]; n = n[6:] if n.startswith('swift-') else n
    return n
norm = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
dist = collections.Counter(); 
for p in pk:
    reg = [t for t in tg[p] if t[1] in ('regular','macro','system')]
    dist[(layer[p], min(len(reg),6))] += 1
for k in sorted(dist): print(k, dist[k])
# I4: primary product
bad=collections.Counter(); ex=collections.defaultdict(list); tot=collections.Counter()
for p in pk:
    L=layer[p]; libs=[x for x in prod[p] if x[1]=='library']; 
    if not libs: bad[(L,'no library product')]+=1; continue
    tot[L]+=1
    pn = norm(prim(p))
    names=[norm(x[0]) for x in libs]
    if pn not in names:
        bad[(L,'no product named for package')]+=1; ex[(L,'noprimary')].append((p,[x[0] for x in libs][:3]))
    primary = next((x[0] for x in libs if norm(x[0])==pn), None)
    if primary:
        others=[x[0] for x in libs if x[0]!=primary and not x[0].startswith(primary+' ')]
        if others: bad[(L,'other product not primary+role')]+=1; ex[(L,'otherrole')].append((p,others[:4]))
    dyn=[x[0] for x in libs if x[2] not in ('automatic','')]
    if dyn: bad[(L,'non-automatic library')]+=1; ex[(L,'dyn')].append((p,dyn[:3]))
print(dict(tot)); 
for k in sorted(bad): print(k,bad[k])
for k in sorted(ex): 
    print(k, len(ex[k])); 
    for e in ex[k][:14]: print('   ',e)
