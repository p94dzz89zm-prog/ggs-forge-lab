import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
AMPS={'Purphoros':'Purphoros, God of the Forge','Tempest':'Dragon Tempest','Throne':'Roaming Throne','Karlach':'Karlach, Fury of Avernus','Port_Razer':'Port Razer','Assault':'Aggravated Assault'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def count(text):
 c=collections.Counter()
 for l in text.splitlines():
  if l and l[0].isdigit():n,card=l.split(' ',1);c[card]+=int(n)
 return c
text=(ROOT/'decks/Pure_GGS.dck').read_text();original=count(text);assert sum(original.values())==100
assert sha(ROOT/'decks/Pure_GGS.dck')=='166a88df0207b4792d3784f7ef0218510e3c0114a7208368b079ce99bdc07cf7'
arms=[]
for short,card in AMPS.items():
 name='Pure_Slot_'+short;v=text.replace('Name=Pure_GGS','Name='+name).replace('1 '+card+'\n',"1 Night's Whisper\n");c=count(v)
 assert sum(c.values())==100 and c-original==collections.Counter({"Night's Whisper":1}) and original-c==collections.Counter({card:1})
 path=ROOT/'decks'/f'{name}.dck'
 if path.exists():assert path.read_text()==v
 else:path.write_text(v)
 arms.append({'name':name,'removed':card,'sha256':sha(path)})
protocol={'arms':arms,'replacement':"Night's Whisper",'baseline_sha256':sha(ROOT/'decks/Pure_GGS.dck'),'control_sha256':sha(ROOT/'decks/GGS_Firework_Protocol_v1_0.dck'),'engine_sha256':sha(ROOT/'experiments/pure-ggs/engine-casual-seven.jar'),'pod_sha256':{n:sha(ROOT/'decks'/f'{n}.dck') for n in ['Jaymie_Ezio','Gabe_Food','Destyn_Turtles']},'gate_seed':202610060,'rotations':[0,1,2,3],'stages':[16,32,64,96,128],'minimum':64,'maximum':128,'stop_rule':'At least64 valid/arm and20 exposed pairs; primary unconditional ignition/basic/strong/threat retention effects change<=10pp and observed median timing effects change<=1 turn versus preceding planned cumulative stage. Extend unstable arms, report uncertainty at cap.','primary':['ignition','basic','strong','threat'],'secondary':['conditional ignited conversion/snowball','timing','recovery','stall categories','exposure and contribution','wins'],'estimand':'Entire amplifier card versus a common ordinary draw spell, holding the other five amplifiers constant; not simultaneous six-card removal or isolated ability text.','matching':'Common seeds and seats. Different deck/card choices can consume RNG differently; no identical-counterfactual assumption.','runtime':'Actual Forge v28, casual-seven mulligans, unchanged pilot/cards, four isolated JVMs,300-second limit, all-seat audits and canonical logs.','interrupted_gate':'Prior unsaved checkpoint lost in workspace reset. Do not count unavailable games. Original128-game study and saved protocol intact.'}
assert protocol['engine_sha256']=='43b8dded3ad4316c12632cd0ed359f687b79c461da3b8a68e365481d5f15dcfb'
path=HERE/'protocol.json'
if path.exists():assert json.loads(path.read_text())==protocol
else:path.write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps(arms,indent=2))
