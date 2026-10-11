"""Regression checks against preserved actual games, not invented outcomes."""
import gzip,json,sys
from pathlib import Path
from measure import extract
ROOT=Path(sys.argv[1])
def game(stage,arm,seed,rotation):
 batch=ROOT/f'stage-{stage:03}';row=next(r for r in json.loads((batch/'summary.json').read_text()) if (r['variant'],r['seed'],r['seat_rotation'])==(arm,seed,rotation));key=f'{arm}-{seed}-r{rotation}'
 m=json.loads((batch/'analysis'/(key+'-metrics.json')).read_text());t=json.load(gzip.open(batch/'analysis'/(key+'-timeline.json.gz'),'rt'));return extract(batch,row,m,t)
m=game(64,'Truly_Pure_GGS_v2',202610210,1)
assert m['cards']["Sakashima's Student"]['battlefield_seen']
assert {e['copied_name'] for e in m['student_copies']} >= {'Prosperous Thief','Eagles of the North'}
m=game(64,'Truly_Pure_GGS_v2',202610211,3)
assert len(m['protective_phase_events'])==1
assert not any(d['source']=='March of Swirling Mist' for d in m['disruptions'])
e=next(e for e in m['protection_threats'] if e['source']=='Game Over' and e['turn']==9)
assert e['commander_phased_out'] and e['successful_response_avoided_loss'] and e['another_dragon_within_three_after_response']
m=game(32,'Truly_Pure_GGS_v2',202610202,2)
assert any(e['source']=='Mortify' and e['turn']==3 for e in m['protection_threats'])
m=game(32,'Truly_Pure_GGS_v2',202610208,3)
assert any(d['creation_before_reentry_observed'] for d in m['disruptions'])
assert all(d['next_trigger_turn'] is None or d['reentry_turn'] is not None for d in m['disruptions'])
m=game(64,'Truly_Pure_GGS_v2',202610215,3)
assert any(e['source']=='Kaito, Cunning Infiltrator' for e in m['factory_ammunition_events'])
assert m['kaito_loot_resolutions']
print('PASS: Student identity/forms, protective phasing, canonical target detection, pending-trigger restart separation, Kaito ammunition/loot')
