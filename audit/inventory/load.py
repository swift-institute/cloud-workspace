#!/usr/bin/env python3
"""Loads the inventory's JSON tables into one SQLite file. Usage: load.py <tables dir> <db>"""
import json, sqlite3, sys, os
src, db = sys.argv[1], sys.argv[2]
if os.path.exists(db): os.remove(db)
c = sqlite3.connect(db)
for f in sorted(os.listdir(src)):
    if not f.endswith('.json'): continue
    rows = json.load(open(os.path.join(src, f)))
    name = f[:-5]
    if not rows: 
        print(name, 0); continue
    cols = list(rows[0].keys())
    c.execute(f'create table "{name}" ({",".join(chr(34)+k+chr(34) for k in cols)})')
    c.executemany(f'insert into "{name}" values ({",".join("?"*len(cols))})', [[r.get(k) for k in cols] for r in rows])
    print(name, len(rows))
c.commit()
