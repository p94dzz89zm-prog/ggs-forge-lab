"""Summarize nested timers without adding overlapping inclusive durations."""
import csv, sys
from collections import defaultdict
from pathlib import Path

rows=list(csv.DictReader(Path(sys.argv[1]).open()))
root_total=sum(int(r['inclusive_ns']) for r in rows if ' > ' not in r['path'])
exclusive_total=sum(int(r['exclusive_ns']) for r in rows)
assert root_total==exclusive_total,(root_total,exclusive_total)
assert all(int(r['exclusive_ns'])>=0 for r in rows)
groups=defaultdict(lambda:[0,0,0])
for r in rows:
    label=r['path'].split(' > ')[-1].split(' :: ')[-1]
    for i,key in enumerate(('calls','inclusive_ns','exclusive_ns')):groups[label][i]+=int(r[key])
print('Sum of per-thread instrumented root seconds:',round(root_total/1e9,3))
print('Root durations can overlap across threads; this is NOT whole-game wall time.')
print('All method counts include nested invocations; inclusive times overlap.')
print('label,calls,inclusive_seconds,exclusive_seconds')
for label,(calls,inc,exc) in sorted(groups.items(),key=lambda kv:kv[1][2],reverse=True):
    print(f'{label},{calls},{inc/1e9:.6f},{exc/1e9:.6f}')
print('\nRoot boundaries: path,calls,inclusive_seconds')
for r in sorted(rows,key=lambda r:int(r['inclusive_ns']),reverse=True):
    if ' > ' not in r['path']:print(f"{r['path']},{r['calls']},{int(r['inclusive_ns'])/1e9:.6f}")
print('\nStatic rebuilding by enclosing path: path,calls,inclusive_seconds')
for r in sorted(rows,key=lambda r:int(r['inclusive_ns']),reverse=True):
    if 'static-rebuild' in r['path'].split(' > ')[-1]:print(f"{r['path']},{r['calls']},{int(r['inclusive_ns'])/1e9:.6f}")
