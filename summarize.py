#!/usr/bin/env python3
"""Regenerate measured observations using the current conservative parser."""
import argparse,collections,hashlib,json,pathlib,re
from run_games import ROOT,classify
p=argparse.ArgumentParser();p.add_argument('--output',default='results');a=p.parse_args()
out=ROOT/a.output; records=[]
for path in sorted((out/'records').glob('*.json')):
    d=json.loads(path.read_text());logpath=ROOT/d['log'];log=logpath.read_text(errors='replace')
    raw_hash=hashlib.sha256(logpath.read_bytes()).hexdigest()
    recorded_hash=d['log_sha256']
    if recorded_hash!=raw_hash and recorded_hash!=hashlib.sha256(log.encode()).hexdigest():raise ValueError(f'Log integrity check failed: {logpath}')
    d['runtime_log_sha256']=recorded_hash
    d['runtime_log_hash_input']='raw bytes' if recorded_hash==raw_hash else 'newline-normalized UTF-8 text (legacy runner)'
    d['log_sha256']=raw_hash
    state=classify(log,d.get("returncode",0))
    if d["status"]=="engine_error" and state["status"]=="completed":state={"status":"engine_error","winner":None}
    if d['status']=='process_timeout':state={'status':'process_timeout','winner':None}
    d.update(state)
    player=re.compile(r'^Add To Stack: Ai\(\d+\)-'+re.escape(d['variant'])+r' (cast|activated|triggered) (.+)$',re.M)
    events=player.findall(log)
    d['ggs_commander_cast_attempts']=sum(kind=='cast' and card=='Goro-Goro and Satoru' for kind,card in events)
    d['ggs_trigger_stack_entries']=sum(kind=='triggered' and card=='Goro-Goro and Satoru' for kind,card in events)
    d['ggs_event_counts']=dict(collections.Counter(kind+': '+card for kind,card in events))
    records.append(d)
summary={}
for d in records:
    v=d['variant'];s=summary.setdefault(v,{'attempts':0,'statuses':{},'ggs_wins_completed':0,'opponent_wins_completed':{},'commander_cast_attempts_completed':[],'event_counts_completed':{}})
    s['attempts']+=1;s['statuses'][d['status']]=s['statuses'].get(d['status'],0)+1
    if d['status']=='completed':
        if d['winner'].endswith('-'+v):s['ggs_wins_completed']+=1
        else:
            opponent=d['winner'].split('-',1)[1]
            s['opponent_wins_completed'][opponent]=s['opponent_wins_completed'].get(opponent,0)+1
        s['commander_cast_attempts_completed'].append(d['ggs_commander_cast_attempts'])
        for k,n in d['ggs_event_counts'].items():s['event_counts_completed'][k]=s['event_counts_completed'].get(k,0)+n
(out/'audited_records.json').write_text(json.dumps(records,indent=2)+'\n')
(out/'audited_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Measured game outcomes','',
'Counts only; no inferred human win rates. Completed games exclude runtime errors and timeouts. Missing games are not losses. Four exploratory games per variant cannot distinguish small improvements.', '',
'| Version | Attempts | Completed | GGS wins in completed games | Timeouts | Engine errors | Other incomplete |',
'|---|---:|---:|---:|---:|---:|---:|']
for v,s in summary.items():
    c=s['statuses'];incomplete=sum(n for k,n in c.items() if k not in ('completed','completed_draw','timeout','engine_error'))
    lines.append(f"| {v} | {s['attempts']} | {c.get('completed',0)+c.get('completed_draw',0)} | {s['ggs_wins_completed']} | {c.get('timeout',0)} | {c.get('engine_error',0)} | {incomplete} |")
lines+=['','## Commander usage in completed games','',
'These are cast attempts and triggered abilities put on the stack. They do not prove every spell or trigger resolved. Repeated casting is evidence that recasting happened; it does not measure complete board-wipe recovery.','',
'| Version | Commander cast attempts per completed game | GGS trigger stack entries across completed games |','|---|---|---:|']
for v,s in summary.items():
    lines.append(f"| {v} | {', '.join(map(str,s['commander_cast_attempts_completed'])) or 'none'} | {s['event_counts_completed'].get('triggered: Goro-Goro and Satoru',0)} |")
lines+=['','True completed draws, if any, have status `completed_draw` in the audited JSON and are included in the completed column. Individual audited records and original full logs are included. The three-player infrastructure smoke test is excluded. The separate invalid four-player timeout smoke test is also excluded.']
(out/'MEASURED_RESULTS.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:{'attempts':s['attempts'],'statuses':s['statuses'],'ggs_wins_completed':s['ggs_wins_completed']} for k,s in summary.items()},indent=2))
