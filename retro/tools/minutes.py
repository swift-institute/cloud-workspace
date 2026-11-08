import sys,re,datetime as dt,collections
f=sys.argv[1]; t0=None
def ts(s):
    s=s.split(' ')[0].rstrip('Z')
    return dt.datetime.fromisoformat(s[:26])
rows=[]
for line in open(f):
    p=line.rstrip('\n').split('\t')
    if len(p)<4 or p[0]=='timestamp_utc': continue
    try: rows.append((ts(p[0]),p[1],p[2],p[3]))
    except Exception: pass
rows.sort()
start=rows[0][0].replace(second=0,microsecond=0); end=rows[-1][0]
if len(sys.argv)>2: end=dt.datetime.fromisoformat(sys.argv[2])
def cat(cmd):
    c=cmd.lower()
    if re.match(r'^(root build|re-lint|lint |build |typecheck |log growth)',c) or ' rounds' in c or 'completion' in c: return 'wait'
    if re.search(r'\buntil\b|\bsleep\b|monitor|pgrep|tail -f',c) and not re.search(r'swift build|build-revert|verify\.sh|lint-all|typecheck',c.split('until')[0] if 'until' in c else ''): return 'wait'
    if 'build-revert' in c or 'swift build' in c or 'verify.sh' in c or 'root-green' in c or 'swift package' in c: return 'build'
    if 'typecheck' in c or 'swiftc' in c or 'tc-fix' in c: return 'typecheck'
    if 'lint-all' in c or 'lint-par' in c or 'count-lint' in c or 'runner' in c or 'apply-repairs' in c: return 'lint'
    if 'ratchet' in c or 'lost-declarations' in c or 'format-changed' in c: return 'gates'
    if 'push' in c: return 'push'
    return 'other'
running={}  # id -> (cat,start)
intervals=collections.defaultdict(list)
for t,k,s,d in rows:
    if s=='task_started':
        m=re.match(r'(\S+) (\S+) bg=(\S+) (?:tool_use=\S+ |\| )?(.*)',d)
        if m:
            tid,typ,bg,cmd=m.groups()
            if typ=='local_agent': c='subagent'
            elif typ=='monitor' or 'Monitor' in typ: c='wait'
            else: c=cat(cmd)
            running[tid]=(c,t,cmd)
    elif s=='task_notification':
        tid=d.split(' ')[0]
        if tid in running:
            c,t1,cmd=running.pop(tid); intervals[c].append((t1,t,cmd))
unmatched=[(c,t1,cmd[:80]) for tid,(c,t1,cmd) in running.items()]
print('unmatched (no finish notice), excluded:',unmatched)
def awaited(cmd):
    c=cmd.lower()
    if 'build-warnings' in c or 'warn' in c and 'build' in c: return 'build'
    if 'build-revert' in c or 'swift build' in c or 'verify' in c or 'roottests' in c or 'root build' in c or 'br.out' in c or 'br-s3' in c: return 'build'
    if 'swift test' in c: return 'build'
    if 'typecheck' in c: return 'typecheck'
    if 'lint' in c or 'runner' in c: return 'lint'
    if re.search(r'\buntil\b|\bwhile\b|\bsleep\b',c): return 'polled-job'
    return None
uses={}
for t,k,s_,d in rows:
    if s_=='tool_use':
        mm=re.match(r'(\S+) (\S+) (?:\| )?(.*)',d)
        if mm: uses[mm.group(2)]=(t,mm.group(1)+' '+mm.group(3))
    elif s_=='tool_result':
        tid=d.split(' ')[0]
        if tid in uses:
            t1,cmd=uses.pop(tid)
            if (t-t1).total_seconds()>120:
                a=awaited(cmd)
                if a: intervals[a].append((t1,t,cmd))
agent=set()
for t,k,s,d in rows:
    if k in('assistant',) or s in('tool_result',):
        agent.add(t.replace(second=0,microsecond=0))
busy=collections.defaultdict(set)
for c,iv in intervals.items():
    for a,b,_ in iv:
        m=a.replace(second=0,microsecond=0)
        while m<=b: busy[c].add(m); m+=dt.timedelta(minutes=1)
limit=[]
for t,k,s,d in rows:
    if 'weekly limit' in d.lower() or 'hit your' in d.lower(): limit.append(t)
tot=collections.Counter(); m=start; hourly=collections.defaultdict(collections.Counter)
lim_s=min(limit) if limit else None
while m<end:
    if m in agent: k='agent working'
    elif m in busy['build']: k='machine: build'
    elif m in busy['typecheck']: k='machine: typecheck'
    elif m in busy['lint']: k='machine: lint'
    elif m in busy['gates']: k='machine: gates'
    elif m in busy['push']: k='machine: push'
    elif m in busy['polled-job']: k='machine: polled bg job'
    elif m in busy['subagent']: k='subagent working'
    elif m in busy['other']: k='machine: other script'
    elif lim_s and lim_s<=m<=lim_s+dt.timedelta(minutes=60) and not any(x for x in agent if lim_s<x<=m): k='usage limit'
    else: k='idle (nothing running)'
    tot[k]+=1; hourly[m.strftime('%m-%dT%H')][k]+=1; m+=dt.timedelta(minutes=1)
print('window',start,end,'minutes',sum(tot.values()))
for k,v in tot.most_common(): print(f'{k:26} {v:5} min {v/60:5.1f} h')
print('agent-active minutes while a build ran:',len(agent & busy['build']))
print('build busy minutes total:',len(busy['build']),' typecheck',len(busy['typecheck']),' lint',len(busy['lint']),' gates',len(busy['gates']))
print('hourly:')
keys=['agent working','machine: build','machine: typecheck','machine: lint','machine: gates','machine: push','subagent working','machine: other script','usage limit','idle (nothing running)']
print('hour      '+' '.join(k[:8].rjust(8) for k in keys))
for h in sorted(hourly): print(h,' '.join(str(hourly[h][k]).rjust(8) for k in keys))
print('--- longest intervals per category')
for c in intervals:
    iv=sorted(intervals[c],key=lambda x:-(x[1]-x[0]).total_seconds())[:6]
    for a,b,cmd in iv:
        mins=(b-a).total_seconds()/60
        if mins>=4: print(c.ljust(9),a.strftime('%dT%H:%M'),f'{mins:6.1f}',cmd[:110])
