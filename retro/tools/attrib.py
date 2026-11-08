import os,re,sys,json,collections
root=sys.argv[1]
def method(s):
    s=s.lower()
    rules=[('revert','REVERT'),('reset','REVERT'),('swift-format','format'),('import access fixed','fix-imports'),('duplicate import','fix-imports'),
    ('nested exports','fix-imports'),('weaker duplicate','fix-imports'),('imports a moved','fix-imports'),
    ("runner's repair",'runner-repair'),('runner repairs','runner-repair'),
    ('minimal type body','minimal-bodies.py'),('compound suite name','compound-suites.py'),('test display name','suite-display/drop-display'),
    ('test function naming','test-function-names.py'),('extension file naming: files renamed','own-type/where-file-names.py'),
    ('extension file naming','merge-extension-files.py'),('single type per file','split-types.py'),('counter loop','counter-loops.py'),
    ('statement where expression','if-expressions.py'),('exported import','exports-file.py'),('module selector','module-selectors.py'),
    ('trait consistency','runner-repair(trait)'),('compound type name','private-compound/package-to-internal.py'),('second round','second-round mix')]
    for k,v in rules:
        if k in s: return v
    return 'other:'+s[:40]
out=collections.defaultdict(lambda: dict(commits=0,files=0,reverted_files=0,repos=set()))
files_by_method=collections.defaultdict(set); reverted_by_method=collections.defaultdict(set)
unattributed=0; revfiles=0
for repo in sorted(os.listdir(root)):
    last={}  # path -> method
    for f in sorted(os.listdir(os.path.join(root,repo))):
        t=open(os.path.join(root,repo,f),errors='replace').read()
        head=t.split('\n---\n',1)[0]
        subj=re.search(r'^Subject: (?:\[PATCH[^\]]*\] )?(.*(?:\n [^\n]*)*)',head,re.M).group(1).replace('\n ',' ')
        m=method(subj)
        paths=set()
        for a,b in re.findall(r'^diff --git a/(.*?) b/(.*)$',t,re.M): paths.add(a); paths.add(b)
        # renames: map new->old
        if m=='REVERT':
            for p in paths:
                if p in last:
                    mm=last[p]; key=(repo,p)
                    if key not in reverted_by_method[mm]:
                        reverted_by_method[mm].add(key)
                elif p.endswith('.swift'): unattributed+=1
            out['REVERT']['commits']+=1
        else:
            out[m]['commits']+=1; out[m]['repos'].add(repo)
            for p in paths:
                last[p]=m; files_by_method[m].add((repo,p))
res=[]
for m,v in out.items():
    if m=='REVERT': continue
    nf=len(files_by_method[m]); nr=len(reverted_by_method[m])
    res.append((m,v['commits'],len(v['repos']),nf,nr,round(100*nr/max(nf,1),1)))
res.sort(key=lambda r:-r[3])
print(f"{'method':42} commits repos files reverted %")
for r in res: print(f"{r[0][:42]:42} {r[1]:6} {r[2]:5} {r[3]:6} {r[4]:6} {r[5]:5}")
print('revert commits',out['REVERT']['commits'],'unattributed swift paths',unattributed)
tf=sum(len(v) for v in files_by_method.values()); tr=sum(len(v) for v in reverted_by_method.values())
print('total file-touches',tf,'reverted',tr)
json.dump({m:[len(files_by_method[m]),len(reverted_by_method[m])] for m in files_by_method},open(sys.argv[2],'w'))

# reasons
def reason(s):
    s=s.lower()
    if 'ratchet' in s: return 'ratchet'
    if 'lost' in s or 'codable' in s or 'equatable' in s or 'dropped' in s: return 'lost-content'
    if "can't verify" in s or 'macro' in s or 'cannot' in s or 'uncheck' in s: return 'unverifiable'
    if 'type-check' in s or 'typecheck' in s or 'broke' in s or 'build' in s or 'fail' in s or 'error' in s: return 'build/type-check'
    if 'origin/main' in s: return 'reset-to-main(other)'
    if 'nested a suite' in s or 'namespace of its own' in s: return 'wrong-rewrite'
    return 'other'
X=collections.Counter(); R=collections.Counter(); ex=collections.defaultdict(list)
for repo in sorted(os.listdir(root)):
    last={}
    for f in sorted(os.listdir(os.path.join(root,repo))):
        t=open(os.path.join(root,repo,f),errors='replace').read()
        head=t.split('\n---\n',1)[0]
        body=head.split('\n\n',1)[1] if '\n\n' in head else ''
        subj=re.search(r'^Subject: (?:\[PATCH[^\]]*\] )?(.*(?:\n [^\n]*)*)',head,re.M).group(1).replace('\n ',' ')
        m=method(subj); paths=set(p for ab in re.findall(r'^diff --git a/(.*?) b/(.*)$',t,re.M) for p in ab)
        if m=='REVERT':
            r=reason(subj+' '+body[:400]); R[r]+=1
            if len(ex[r])<4: ex[r].append(subj[:110])
            for p in paths:
                if p in last: X[(last[p],r)]+=1
        else:
            for p in paths: last[p]=m
print(R)
for r,e in ex.items(): print(r,'|', ' || '.join(e))
ms=sorted(set(k[0] for k in X)); rs=sorted(set(k[1] for k in X))
print('method'.ljust(36),' '.join(r[:12].rjust(12) for r in rs))
for m in ms: print(m[:36].ljust(36),' '.join(str(X[(m,r)]).rjust(12) for r in rs))
