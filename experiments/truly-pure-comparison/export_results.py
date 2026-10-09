"""Export the completed frozen comparison, never an interim sample as final."""
import argparse,json,gzip,hashlib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=WORK/'truly-pure-comparison');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((HERE/'protocol.json').read_text());summary=json.loads((a.root/'comparison-128.json').read_text())
assert summary['valid_games']==256 and summary['seed_blocks']==32
assert all(summary['arms'][arm]['ignition']['n']==128 for arm in protocol['arms'])
saved={};archives=[]
for mp in sorted((a.root/'checkpoints').glob('part-*-manifest.json')):
 number=mp.name.split('-')[1];receipt=json.loads((a.root/'checkpoints'/f'part-{number}-receipt.json').read_text());assert receipt['saved']
 manifest=json.loads(mp.read_text());archive=f'Truly_Pure_Comparison_Evidence_Part_{number}.tar.gz';archives.append({'archive':archive,'keys':manifest['keys'],'member_sha256':manifest['files']})
 for key in manifest['keys']:saved[key]=archive
reviews=json.loads((HERE/'manual-review.json').read_text())['reviews'];games=[];identities=set()
for stage in (32,64,96,128):
 batch=a.root/f'stage-{stage:03}';rows=json.loads((batch/'summary.json').read_text());assert len(rows)==64
 for row in rows:
  assert row['status']=='completed';identity=(row['variant'],row['seed'],row['seat_rotation']);assert identity not in identities;identities.add(identity)
  key=f"{row['variant']}-{row['seed']}-r{row['seat_rotation']}";m=json.loads((batch/'analysis'/(key+'-extended.json')).read_text());timeline=json.load(gzip.open(batch/'analysis'/(key+'-timeline.json.gz'),'rt'))
  assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
  archivekey=f"{batch.name}/{row['variant']}/{row['seed']}/r{row['seat_rotation']}";assert archivekey in saved
  triggers=m['fresh_connection_trigger_events'];m['first_trigger_observed_turn']=triggers[0]['turn'] if triggers else None;m['second_trigger_observed_turn']=triggers[1]['turn'] if len(triggers)>1 else None
  m['final_hand_count']=timeline['states'][-1]['hand'];m['first_trigger_fidelity']='Observed triggers and resolved Dragon creation are separate; earliest creation confirms production. Multiple tokens can arise from one trigger.'
  m['hand_resource_trace']=[{k:s[k] for k in ('turn','global_turn','phase','ggs_present','hand','treasures','fresh_ready','ggs_dragons','ggs_total')} for s in timeline['states'] if s['active'] and s['phase'] in ('COMBAT_BEGIN','COMBAT_END','END_OF_TURN')]
  m['evidence']={'archive':saved[archivekey],'game_key':archivekey,'transcript':str(batch.name+'/'+row['engine_transcript']),'record':str(batch.name+'/'+row['engine_record']),'audit':str(batch.name+'/audit/'+Path(row['log']).stem)}
  m['manual_reviews']=[review for review in reviews if (review['variant'],review['seed'],review['rotation'])==identity]
  games.append(m)
assert len(games)==256
for arm in protocol['arms']:
 assert {(m['seed'],m['rotation']) for m in games if m['variant']==arm}=={(s,r) for s in range(202610202,202610234) for r in range(4)}
a.out.mkdir(parents=True,exist_ok=True)
for filename,value in [('Truly_Pure_Comparison_Per_Game.json',games),('Truly_Pure_Comparison_Summary.json',summary),('Truly_Pure_Comparison_Evidence_Index.json',archives),('Truly_Pure_Comparison_Protocol.json',protocol)]:
 (a.out/filename).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'exported_games':len(games),'files':[str(p) for p in sorted(a.out.iterdir())]}))
