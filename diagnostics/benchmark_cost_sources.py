from pathlib import Path
import json,re,subprocess,time
import argparse
parser=argparse.ArgumentParser(description="Trace-checked two-seed ABBA benchmark of an isolated combat cost-source jar")
for name in ['accepted_jar','candidate_jar','deck_directory','resource_directory','reference_log','output_directory']:
    parser.add_argument(name,type=Path)
args=parser.parse_args()
root=args.output_directory.resolve();root.mkdir(parents=True,exist_ok=True)
accepted=args.accepted_jar.resolve();candidate=args.candidate_jar.resolve()
categories={'Turn','Phase','Add To Stack','Resolve Stack','Damage','Combat','Life'}
def events(text):return [line for line in text.splitlines() if line.split(':',1)[0] in categories]
expected=events(args.reference_log.read_text());assert len(expected)==2146
results={}
for label,jar in [('control-1',accepted),('candidate-1',candidate),('candidate-2',candidate),('control-2',accepted)]:
 print('Starting '+label,flush=True)
 command=['java','-Xmx1536m','-XX:+UseParallelGC','-XX:-TieredCompilation','-XX:CompileThreshold=1000','-XX:-UsePerfData','-Djava.awt.headless=true','-cp',str(jar),'forge.view.Main','sim','-D',str(args.deck_directory.resolve()),'-d','GGS_Layered_v1.dck','Jaymie_Ezio.dck','Gabe_Food.dck','Destyn_Turtles.dck','-f','Commander','-seeds','20261011','20261012','-c','180','-a','Default','Default','Default','Default']
 log=root/('cost-sources-'+label+'.log')
 with log.open('w') as output:
  subprocess.run(command,cwd=args.resource_directory.resolve(),stdout=output,stderr=subprocess.STDOUT,check=True)
 text=log.read_text();actual=events(text)
 if actual!=expected:raise RuntimeError(label+' trace mismatch: '+str(len(actual))+' tracked events')
 games=[json.loads(match) for match in re.findall(r'DragonMind Result: (\{[^\n]+\})',text)]
 assert len(games)==2 and all(game['status']=='completed' for game in games)
 results[label]=games
 (root/'cost-sources-benchmark.json').write_text(json.dumps(results,indent=2)+'\n')
 print(label+': '+str([game['engine_ms'] for game in games])+'; 2146 matching events',flush=True)
