#!/usr/bin/env python3
"""DragonMind: warm-process batches backed by Forge's full Commander rules."""
import argparse, concurrent.futures, hashlib, json, pathlib, re, subprocess, time
from run_games import ROOT, validate_deck


def parse_results(text, seeds):
    results = {}
    segment = []
    for line in text.splitlines():
        if not line.startswith('DragonMind Result: '):
            segment.append(line)
            continue
        row = json.loads(line[len('DragonMind Result: '):])
        seed = row['seed']
        if seed not in seeds or seed in results:
            raise ValueError('Unexpected or duplicate seed result')
        if row['status'] not in ('completed', 'completed_draw', 'timeout', 'engine_error'):
            raise ValueError('Unknown engine status')
        if row['status'] == 'completed' and not row.get('winner'):
            raise ValueError('Completed game has no winner')
        if row['status'] != 'completed' and row.get('winner'):
            raise ValueError('Incomplete/drawn game reported a winner')
        if row['status'] in ('completed','completed_draw') and re.search(r'(?:(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*(?:Exception|Error)\b|Exception in thread|StackOverflowError|OutOfMemoryError)', '\n'.join(segment)):
            row['status']='engine_error'
            row['winner']=None
        results[seed] = row
        segment = []
    return results


def java_runtime_flags(gc, jit):
    gc_flag='-XX:+UseParallelGC' if gc=='parallel' else '-XX:+UseG1GC'
    jit_flags=['-XX:-TieredCompilation','-XX:CompileThreshold=1000'] if jit=='throughput' else []
    return [gc_flag,*jit_flags]


def batch(engine, jar, out, variant, rotation, seeds, timeout, pilot, audit, gc='parallel', jit='throughput'):
    seats = [variant, 'Jaymie_Ezio', 'Gabe_Food', 'Destyn_Turtles']
    seats = seats[rotation:] + seats[:rotation]
    label = f'{variant}__seat{rotation}__seeds{seeds[0]}-{seeds[-1]}'
    flags = []
    if pilot:
        flags.append(f'-Dforge.ai.ggsPilotPlayer=Ai({seats.index(variant)+1})-{variant}')
    if audit:
        flags.append('-Dforge.audit.directory='+str(out/'audit'/label))
    cmd = ['java', '-Xmx1536m', *java_runtime_flags(gc,jit), '-Djava.awt.headless=true', *flags, '-jar', str(jar),
           'sim', '-D', str(ROOT/'decks'), '-d', *[s+'.dck' for s in seats],
           '-f', 'Commander', '-seeds', *map(str, seeds), '-c', str(timeout),
           '-a', *(['Default']*4)]
    start = time.monotonic()
    process_timeout = False
    logpath = out/(label+'.log')
    with logpath.open('w') as stream:
        try:
            proc = subprocess.run(cmd, cwd=engine, stdout=stream, stderr=subprocess.STDOUT,
                                  timeout=timeout*len(seeds)+45)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = -1
            process_timeout = True
    elapsed = time.monotonic()-start
    rows = parse_results(logpath.read_text(errors='replace'), seeds)
    records = []
    for seed in seeds:
        row = rows.get(seed, {'seed':seed, 'status':'not_run', 'winner':None})
        # An abnormal JVM exit means its emitted records cannot be trusted.
        if rc:
            row = {'seed':seed, 'status':'process_timeout' if process_timeout else 'process_error', 'winner':None}
        row.update(variant=variant, seat_rotation=rotation, seats=seats,
                   pilot='commander-aware' if pilot else 'stock', batch_wall_seconds=round(elapsed,3),
                   batch_size=len(seeds), command=cmd, log=logpath.name)
        records.append(row)
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=pathlib.Path,required=True,help='Directory containing res/')
    p.add_argument('--jar',type=pathlib.Path,required=True,help='Built DragonMind executable')
    p.add_argument('--variant',default='GGS_Layered_v1')
    p.add_argument('--seed',type=int,default=20261011)
    p.add_argument('--seeds',type=int,default=2,help='Independent seeds per seat')
    p.add_argument('--rotations',type=int,nargs='+',default=[0,1,2,3])
    p.add_argument('--workers',type=int,default=1,help='Separate JVM workers, each with independent RNG')
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--timeout',type=int,default=90)
    p.add_argument('--gc',choices=['parallel','g1'],default='parallel',help='Recorded JVM garbage collector; parallel won the initial throughput check')
    p.add_argument('--jit',choices=['throughput','default'],default='throughput',help='Recorded compiler policy; throughput favors warmed batch execution')
    p.add_argument('--stock',action='store_true',help='Disable commander-aware ninjutsu policy')
    p.add_argument('--audit',action='store_true',help='Private diagnostic recording; slower')
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'dragonmind-results')
    a=p.parse_args()
    if min(a.seeds,a.workers,a.batch_size,a.timeout)<1 or any(r not in range(4) for r in a.rotations):
        p.error('Positive counts and seat rotations 0–3 required')
    if len(set(a.rotations))!=len(a.rotations):p.error('Duplicate seat rotations')
    if not (ROOT/'decks'/(a.variant+'.dck')).is_file():p.error('Unknown deck variant')
    for name in [a.variant,'Jaymie_Ezio','Gabe_Food','Destyn_Turtles']:
        validate_deck(ROOT/'decks'/(name+'.dck'))
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'metadata.json').exists():p.error('Use a new output directory to preserve previous results')
    jar=a.jar.resolve();engine=a.engine.resolve()
    meta={'product':'DragonMind','rules_engine':'Forge 2.0.15 GPL-3.0-or-later fork',
          'rules_baseline':json.loads((ROOT/'rules-baseline.json').read_text()),
          'jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
          'deck_sha256':{n:hashlib.sha256((ROOT/'decks'/(n+'.dck')).read_bytes()).hexdigest() for n in [a.variant,'Jaymie_Ezio','Gabe_Food','Destyn_Turtles']},
          'arguments':{k:str(v) if isinstance(v,pathlib.Path) else v for k,v in vars(a).items()}}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    jobs=[(r,list(range(a.seed+i,a.seed+min(i+a.batch_size,a.seeds)))) for r in a.rotations for i in range(0,a.seeds,a.batch_size)]
    results=[];start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(batch,engine,jar,out,a.variant,r,seeds,a.timeout,not a.stock,a.audit,a.gc,a.jit) for r,seeds in jobs]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
            (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
            print(f'{len(results)} / {len(a.rotations)*a.seeds} attempts recorded',flush=True)
    completed=[r for r in results if r['status'] in ('completed','completed_draw')]
    perf={'wall_seconds':round(time.monotonic()-start,3),'attempts':len(results),'completed':len(completed),
          'engine_seconds':[r['engine_ms']/1000 for r in completed],
          'meaning':'Unattended full-rules games; no external review pauses. Timeouts excluded from completions.'}
    (out/'performance.json').write_text(json.dumps(perf,indent=2)+'\n');print(json.dumps(perf))


if __name__=='__main__':main()
