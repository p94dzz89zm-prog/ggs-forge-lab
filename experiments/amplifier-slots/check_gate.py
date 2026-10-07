import json,sys
from pathlib import Path
from inspect_games import inspect
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;gate=Path(sys.argv[1]);old=WORK/'pure-ggs/gate';rows=json.loads((gate/'summary.json').read_text());assert len(rows)==28 and all(r['status']=='completed' for r in rows)
original={r['seat_rotation']:r for r in json.loads((old/'summary.json').read_text())};clean=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith(('DragonMind Result:','Game Outcome: Match Duration')));checks=[]
for r in rows:
 m=json.loads((gate/'analysis'/f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}-metrics.json").read_text());assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1.0
 audit=inspect(gate,r,["Night's Whisper"]);assert audit['clamp_cleared'];receipt={'variant':r['variant'],'rotation':r['seat_rotation'],'status':r['status'],'life_match':1.0,'clamp_review':audit}
 if r['variant']=='Pure_GGS':
  b=original[r['seat_rotation']];receipt['replay_identical']=clean((gate/r['engine_transcript']).read_text())==clean((old/b['engine_transcript']).read_text());assert receipt['replay_identical']
 checks.append(receipt)
(gate.parent/'gate-receipt.json').write_text(json.dumps(checks,indent=2)+'\n');print('PASS:28 clean games, four identical baseline replays, all creations reconciled')
