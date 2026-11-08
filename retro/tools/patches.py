import os,re,sys,json,email.utils
root=sys.argv[1]; out=[]
for repo in sorted(os.listdir(root)):
    for f in sorted(os.listdir(os.path.join(root,repo))):
        p=os.path.join(root,repo,f); txt=open(p,errors='replace').read()
        head,_,body=txt.partition('\n---\n')
        date=re.search(r'^Date: (.*)$',head,re.M).group(1)
        dt=email.utils.parsedate_to_datetime(date)
        subj=re.search(r'^Subject: (?:\[PATCH[^\]]*\] )?(.*(?:\n [^\n]*)*)',head,re.M).group(1).replace('\n ','')
        stat=re.search(r'(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?',body)
        files=int(stat.group(1)) if stat else 0; ins=int(stat.group(2) or 0) if stat else 0; dels=int(stat.group(3) or 0) if stat else 0
        out.append(dict(repo=repo,n=f[:4],utc=dt.astimezone(email.utils.datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),subj=subj,files=files,ins=ins,dels=dels))
json.dump(out,open(sys.argv[2],'w'),indent=0)
print(len(out))
