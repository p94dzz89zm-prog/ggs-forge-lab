import sys,json,hashlib,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import dragonmind
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args();assert 1<=a.workers<=4
root=Path(__file__).resolve().parents[2];out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
jar=Path(__file__).resolve().parent/'engine-casual-seven.jar';engine=root.parent/'forge-upstream/forge-gui'
expected='166a88df0207b4792d3784f7ef0218510e3c0114a7208368b079ce99bdc07cf7'
assert hashlib.sha256((root/'decks/Pure_GGS.dck').read_bytes()).hexdigest()==expected
meta={'deck_sha256':{n:hashlib.sha256((root/'decks'/(n+'.dck')).read_bytes()).hexdigest() for n in ['Pure_GGS','Jaymie_Ezio','Gabe_Food','Destyn_Turtles','GGS_Firework_Protocol_v1_0']},'base_v28_sha256':'d9278b1ddd644ef6dd458b19cfabee20d3c2e9fde51d1cf10827a91c842616ee','house_mulligan_jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'house_mulligan':'seven cards; redraw only zero land faces, six+ land faces, or one without Sol Ring; all seats; no bottoming or sculpting','seed':a.seed,'seeds_per_rotation':a.seeds,'rotations':[0,1,2,3],'workers':a.workers,'timeout':300}
(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
jobs=[(r,[s]) for s in range(a.seed,a.seed+a.seeds) for r in range(4)]
def worker(job):
 r,seeds=job
 return dragonmind.batch(engine,jar,out,'Pure_GGS',r,seeds,300,True,True,extra_jvm_flags=('-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.casualSeven=true'))
rows=[];start=time.monotonic()
for rs in dragonmind.run_jobs(jobs,worker,a.workers,True):
 rows+=rs;(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'/ ',len(jobs),flush=True)
perf={'wall_seconds':round(time.monotonic()-start,3),'attempted':len(rows),'valid':sum(r['status']=='completed' for r in rows),'statuses':[r['status'] for r in rows]};(out/'performance.json').write_text(json.dumps(perf,indent=2)+'\n');print(perf)
if perf['valid']!=len(jobs):raise SystemExit(1)
