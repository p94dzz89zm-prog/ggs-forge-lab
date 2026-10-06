#!/usr/bin/env python3
"""DragonMind: independent seeded games backed by Forge's full Commander rules."""
import argparse, concurrent.futures, hashlib, json, pathlib, re, subprocess, time, os
from run_games import ROOT, validate_deck


ENGINE_FAILURE = re.compile(r'(?:(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*(?:Exception|Error)\b|Exception in thread|StackOverflowError|OutOfMemoryError)')


def parse_result_lines(lines, seeds):
    """Read logs incrementally; retain results rather than entire game transcripts."""
    results = {}
    segment_failed = False
    last_seed = None
    for line in lines:
        if not line.startswith('DragonMind Result: '):
            segment_failed |= bool(ENGINE_FAILURE.search(line))
            continue
        row = json.loads(line[len('DragonMind Result: '):])
        seed = row['seed']
        if type(seed) is not int or seed not in seeds or seed in results:
            raise ValueError('Unexpected or duplicate seed result')
        if row['status'] not in ('completed', 'completed_draw', 'timeout', 'engine_error'):
            raise ValueError('Unknown engine status')
        if row['status'] == 'completed' and (not isinstance(row.get('winner'), str) or not row['winner'].strip()):
            raise ValueError('Completed game has no winner')
        if row['status'] != 'completed' and row.get('winner'):
            raise ValueError('Incomplete/drawn game reported a winner')
        duration = row.get('engine_ms')
        if type(duration) is not int or duration < 0:
            raise ValueError('Missing or invalid engine duration')
        if row['status'] in ('completed','completed_draw') and segment_failed:
            row['status']='engine_error'
            row['winner']=None
        results[seed] = row
        last_seed = seed
        segment_failed = False
    # A failure after the final marker must not leave a trusted completion.
    if segment_failed and last_seed is not None:
        row = results[last_seed]
        if row['status'] in ('completed','completed_draw'):
            row.update(status='engine_error', winner=None)
    return results


def parse_results(text, seeds):
    return parse_result_lines(text.splitlines(), seeds)


def java_runtime_flags(gc, jit):
    gc_flag='-XX:+UseParallelGC' if gc=='parallel' else '-XX:+UseG1GC'
    jit_flags=['-XX:-TieredCompilation','-XX:CompileThreshold=1000'] if jit=='throughput' else []
    return [gc_flag,*jit_flags]


def batch(engine, jar, out, variant, rotation, seeds, timeout, pilot, audit, gc='parallel', jit='throughput', extra_jvm_flags=()):
    seats = [variant, 'Jaymie_Ezio', 'Gabe_Food', 'Destyn_Turtles']
    seats = seats[rotation:] + seats[:rotation]
    label = f'{variant}__seat{rotation}__seeds{seeds[0]}-{seeds[-1]}'
    flags = []
    if pilot:
        flags.append(f'-Dforge.ai.ggsPilotPlayer=Ai({seats.index(variant)+1})-{variant}')
    if audit:
        flags.append('-Dforge.audit.directory='+str(out/'audit'/label))
    # Forge writes logs, preferences and caches under user.home. Never share that
    # mutable profile between independent JVM games, even with separate audits.
    runtime_home=out/'runtime-home'/label
    runtime_home.mkdir(parents=True,exist_ok=True)
    record_dir=out/'engine-records'/label
    flags.append('-Ddragonmind.resultDirectory='+str(record_dir.resolve()))
    cmd = ['java', '-XX:-UsePerfData', '-Ddragonmind.consoleOnly=true', '-Duser.home='+str(runtime_home.resolve()), '-Xmx1536m', *java_runtime_flags(gc,jit), *extra_jvm_flags, '-Djava.awt.headless=true', *flags, '-jar', str(jar),
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
    parse_error = None
    try:
        with logpath.open(errors='replace') as log:
            rows = parse_result_lines(log, seeds)
        for seed in seeds:
            record=record_dir/(str(seed)+'.json')
            transcript=record_dir/(str(seed)+'.log')
            if record.exists() and transcript.exists():
                recorded=json.loads(record.read_text())
                with transcript.open() as stream:
                    confirmed=parse_result_lines(stream,[seed])[seed]
                if recorded!=confirmed:raise ValueError('Engine result and transcript disagree')
                if seed in rows and any(rows[seed].get(k)!=recorded.get(k) for k in ('seed','status','winner','engine_ms')):
                    raise ValueError('Console and engine result disagree')
                if seed not in rows:
                    # Preserve any console-reported engine exception as a failure.
                    if ENGINE_FAILURE.search(logpath.read_text(errors='replace')):
                        recorded.update(status='engine_error',winner=None)
                    rows[seed]=recorded
                rows[seed]['engine_record']=str(record.relative_to(out))
                rows[seed]['engine_transcript']=str(transcript.relative_to(out))
    except (ValueError, KeyError, TypeError) as error:
        rows = {}
        parse_error = str(error)
    records = []
    for seed in seeds:
        row = rows.get(seed, {'seed':seed, 'status':'not_run', 'winner':None})
        # An abnormal JVM exit means its emitted records cannot be trusted.
        if rc or parse_error:
            row = {'seed':seed, 'status':'process_timeout' if process_timeout else 'process_error', 'winner':None}
        if row['status'] == 'completed' and row['winner'] not in {f'Ai({i+1})-{name}' for i,name in enumerate(seats)}:
            row.update(status='engine_error',winner=None,result_error='Winner does not match a registered seat')
        if parse_error:
            row['result_error'] = parse_error
        row.update(variant=variant, seat_rotation=rotation, seats=seats,
                   pilot='commander-aware' if pilot else 'stock', batch_wall_seconds=round(elapsed,3),
                   batch_size=len(seeds), command=cmd, log=logpath.name)
        records.append(row)
    # Keep a successful process exit with no structured result visibly invalid.
    # An exit status alone is never evidence that a game finished.
    return records


def default_workers():
    """Use the measured two-worker setting on hosts with sufficient capacity."""
    try:
        quota, period = pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().split()
        cores = (os.cpu_count() or 1) if quota == 'max' else int(quota) / int(period)
        memory = pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip()
        if cores >= 4 and memory != 'max' and int(memory) >= 4 * 1024**3:
            return 2
    except (OSError, ValueError, ZeroDivisionError):
        pass
    return 1


def run_jobs(jobs, worker, workers, stop_on_failure=False):
    """Keep only active jobs submitted so a failed gate cannot start a backlog."""
    pending=iter(jobs); stopped=False
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures=set()
        def submit_next():
            job=next(pending,None)
            if job is None:return
            futures.add(pool.submit(worker,job))
        for _ in range(workers):submit_next()
        while futures:
            done,_=concurrent.futures.wait(futures,return_when=concurrent.futures.FIRST_COMPLETED)
            records=[]
            for future in done:
                futures.remove(future);records.extend(future.result())
            if stop_on_failure and any(r['status'] not in ('completed','completed_draw') for r in records):stopped=True
            yield records
            if not stopped:
                for _ in done:submit_next()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=pathlib.Path,required=True,help='Directory containing res/')
    p.add_argument('--jar',type=pathlib.Path,required=True,help='Built DragonMind executable')
    p.add_argument('--variant',default='GGS_Layered_v1')
    p.add_argument('--seed',type=int,default=20261011)
    p.add_argument('--seeds',type=int,default=2,help='Independent seeds per seat')
    p.add_argument('--rotations',type=int,nargs='+',default=[0,1,2,3])
    p.add_argument('--workers',type=int,default=default_workers(),help='Separate JVM workers with independent RNG; default 2 on sufficiently provisioned cgroup hosts, otherwise 1')
    p.add_argument('--batch-size',type=int,default=1,help='Games per JVM; default 1 isolates incomplete games. Larger warm batches are opt-in.')
    p.add_argument('--timeout',type=int,default=90)
    p.add_argument('--gc',choices=['parallel','g1'],default='parallel',help='Recorded JVM garbage collector; parallel won the initial throughput check')
    p.add_argument('--jit',choices=['throughput','default'],default='throughput',help='Recorded compiler policy; throughput favors warmed batch execution')
    p.add_argument('--stock',action='store_true',help='Disable commander-aware ninjutsu policy')
    p.add_argument('--audit',action='store_true',help='Private diagnostic recording; slower')
    p.add_argument('--forecast',choices=['bounded','stock'],default='bounded')
    p.add_argument('--stop-on-failure',action='store_true',help='Stop submitting games after the first invalid result; finish already active games')
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
    if not jar.is_file():p.error('Engine executable is missing; restore the verified build first')
    for required in ('cardsfolder','tokenscripts','editions','languages'):
        if not (engine/'res'/required).is_dir():p.error('Engine resources are missing: res/'+required)
    meta={'product':'DragonMind','rules_engine':'Forge 2.0.15 GPL-3.0-or-later fork',
          'rules_baseline':json.loads((ROOT/'rules-baseline.json').read_text()),
          'jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
          'deck_sha256':{n:hashlib.sha256((ROOT/'decks'/(n+'.dck')).read_bytes()).hexdigest() for n in [a.variant,'Jaymie_Ezio','Gabe_Food','Destyn_Turtles']},
          'arguments':{k:str(v) if isinstance(v,pathlib.Path) else v for k,v in vars(a).items()}}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    jobs=[(r,list(range(a.seed+i,a.seed+min(i+a.batch_size,a.seeds)))) for r in a.rotations for i in range(0,a.seeds,a.batch_size)]
    results=[];start=time.monotonic()
    def worker(job):
        r,seeds=job
        return batch(engine,jar,out,a.variant,r,seeds,a.timeout,not a.stock,a.audit,a.gc,a.jit,
            ('-Ddragonmind.boundedCombatForecast='+str(a.forecast=='bounded').lower(),))
    for records in run_jobs(jobs,worker,a.workers,a.stop_on_failure):
        results.extend(records)
        (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
        print(f'{len(results)} / {len(a.rotations)*a.seeds} attempts recorded',flush=True)
    completed=[r for r in results if r['status'] in ('completed','completed_draw')]
    elapsed = time.monotonic()-start
    perf={'wall_seconds':round(elapsed,3),'attempts':len(results),'completed':len(completed),
          'engine_seconds':[r['engine_ms']/1000 for r in completed],
          'completed_games_per_minute':round(60*len(completed)/elapsed,3),
          'status_counts':{status:sum(r['status']==status for r in results) for status in sorted({r['status'] for r in results})},
          'meaning':'Unattended full-rules games; no external review pauses. Timeouts excluded from completions.'}
    (out/'performance.json').write_text(json.dumps(perf,indent=2)+'\n');print(json.dumps(perf))
    if a.stop_on_failure and len(completed)!=len(results):raise SystemExit(1)


if __name__=='__main__':main()
