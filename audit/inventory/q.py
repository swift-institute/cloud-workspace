#!/usr/bin/env python3
import sqlite3, sys
c = sqlite3.connect('/home/user/analysis/inv.db')
for q in sys.argv[1:]:
    for r in c.execute(q): print(' | '.join('' if v is None else str(v) for v in r))
    print('--')
