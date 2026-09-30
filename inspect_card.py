#!/usr/bin/env python3
"""Find the GGS pilot's actual stack events for a card, not player-name matches."""
import argparse,json,re
from run_games import ROOT
p=argparse.ArgumentParser();p.add_argument('card');p.add_argument('--output',default='results');p.add_argument('--include-incomplete',action='store_true');a=p.parse_args()
records=json.loads((ROOT/a.output/'audited_records.json').read_text())
for d in records:
    if d['status']!='completed' and not a.include_incomplete:continue
    pattern=re.compile(r'^Add To Stack: Ai\(\d+\)-'+re.escape(d['variant'])+r' (cast|activated|triggered) '+re.escape(a.card)+r'(?: targeting .*)?$',re.M)
    log=(ROOT/d['log']).read_text(errors='replace');events=pattern.findall(log)
    if events:print(json.dumps({'card':a.card,'variant':d['variant'],'seat_rotation':d['seat_rotation'],'seed':d['seed'],'status':d['status'],'winner':d['winner'],'events':events,'log':d['log']},ensure_ascii=False))
