#!/usr/bin/env python3
"""Run external Forge's actual Commander engine; never substitute a resource model."""
import argparse, concurrent.futures, hashlib, json, pathlib, re, subprocess, time, zipfile
ROOT=pathlib.Path(__file__).resolve().parent

def classify(log, returncode=0):
    # Forge can falsely report every player as winner after its timeout!
    if 'Stopping slow match as draw' in log:
        return {'status':'timeout','winner':None}
    if returncode or re.search(r'(?:(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*(?:Exception|Error)\b|Exception in thread|StackOverflowError|OutOfMemoryError)',log):
        return {'status':'engine_error','winner':None}
    outcome_players=set(re.findall(r'^Game Outcome: (.+?) has (?:won|lost)\b',log,re.M))
    if len(outcome_players)!=4:
        return {'status':'unresolved','winner':None}
    draws=re.findall(r'^Game Result: Game \d+ ended in a Draw! Took (\d+) ms\.',log,re.M)
    if len(draws)==1:
        return {'status':'completed_draw','winner':None,'engine_ms':int(draws[0])}
    winners=re.findall(r'^Game Outcome: (.+?) has won because',log,re.M)
    results=re.findall(r'^Game Result: Game \d+ ended in (\d+) ms\. (.+?) has won!',log,re.M)
    if len(winners)!=1 or len(results)!=1 or winners[0]!=results[0][1]:
        return {'status':'unresolved','winner':None}
    turns=re.findall(r'^Turn: Turn (\d+) \(',log,re.M)
    return {'status':'completed','winner':winners[0],'engine_ms':int(results[0][0]),
            'last_logged_turn':int(turns[-1]) if turns else None}

def validate_deck(path):
    section=None; counts={'Commander':0,'Main':0}
    for line in path.read_text().splitlines():
        if line.startswith('['): section=line.strip('[]')
        elif section in counts and line.strip():
            m=re.match(r'^(\d+) (.+)$',line)
            if not m: raise ValueError(f'{path}: malformed card line {line}')
            counts[section]+=int(m[1])
    if sum(counts.values())!=100 or counts['Commander'] not in (1,2):
        raise ValueError(f'{path}: invalid deck sizes {counts}')
    return counts

def play(engine,out,variant,seat,seed,timeout,pilot="stock",audit=False):
    opponents=['Jaymie_Ezio','Gabe_Food','Destyn_Turtles']
    seats=[variant]+opponents
    seats=seats[seat:]+seats[:seat]
    stem=f'{variant}__seat{seat}__seed{seed}'
    logpath=out/'logs'/f'{stem}.log'
    jar=engine/'forge-gui-desktop-2.0.15-jar-with-dependencies.jar'
    pilot_flags=[] if pilot=='stock' else [f'-Dforge.ai.ggsPilotPlayer=Ai({seats.index(variant)+1})-{variant}']
    if audit: pilot_flags.append('-Dforge.audit.directory='+str(out/'decision_audit'/stem))
    cmd=['java','-Xmx1536m','-Djava.awt.headless=true','-Dfile.encoding=UTF-8',*pilot_flags,'-jar',str(jar),
         'sim','-D',str(ROOT/'decks'),'-d',*[x+'.dck' for x in seats],'-f','Commander',
         '-n','1','-s',str(seed),'-c',str(timeout),'-a',*(['Default']*len(seats))]
    start=time.monotonic(); outer_timeout=False
    with logpath.open('w') as f:
        try:
            p=subprocess.run(cmd,cwd=engine,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+90)
            rc=p.returncode
        except subprocess.TimeoutExpired:
            outer_timeout=True; rc=-1; f.write('\nHARNESS_PROCESS_TIMEOUT\n')
    log=logpath.read_text(errors='replace')
    result=classify(log,rc)
    if outer_timeout: result={'status':'process_timeout','winner':None}
    casts=re.findall(r'^Add To Stack: Ai\(\d+\)-'+re.escape(variant)+r' cast (.+)$',log,re.M)
    result.update(returncode=rc,variant=variant,seat_rotation=seat,seed=seed,seats=seats,
                  wall_seconds=round(time.monotonic()-start,3),log=str(logpath.relative_to(ROOT)),
                  command=cmd,pilot=pilot,ai_profiles=['Default']*len(seats),ggs_casts=casts,log_sha256=hashlib.sha256(logpath.read_bytes()).hexdigest())
    (out/'records'/f'{stem}.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def make_jobs(variants, games_per_variant, seed, baseline_games=None):
    counts={v:baseline_games if v=='GGS_Current' and baseline_games is not None else games_per_variant for v in variants}
    if any(n<=0 for n in counts.values()): raise ValueError('Game counts must be positive')
    return [(v,i%4,seed+i//4) for i in range(max(counts.values())) for v in variants if i<counts[v]]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=pathlib.Path,required=True)
    p.add_argument('--audit',action='store_true',help='Record private post-game decision audit per match')
    p.add_argument('--pilot',choices=['stock','ggs-v1'],default='stock',help='Opt-in ninjutsu policy for the GGS seat; requires patched Forge')
    p.add_argument('--output',default='results')
    p.add_argument('--games-per-variant',type=int,default=4)
    p.add_argument('--baseline-games',type=int,help='Optional separate attempt count for GGS_Current')
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--timeout',type=int,default=240)
    p.add_argument('--seed',type=int,default=20260930)
    p.add_argument('--variants',nargs='+')
    p.add_argument('--resume',action='store_true',help='Reuse prior records with matching engine/deck hashes and run configuration')
    a=p.parse_args(); engine=a.engine.resolve(); out=ROOT/a.output
    for folder in ('logs','records'): (out/folder).mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'manifest.json').read_text())
    variants=a.variants or [k for k in manifest['decks'] if k.startswith('GGS_')]
    for v in variants:
        if v not in manifest['decks']: p.error(f'Unknown variant: {v}')
    for deck in (ROOT/'decks').glob('*.dck'): validate_deck(deck)
    jar=engine/'forge-gui-desktop-2.0.15-jar-with-dependencies.jar'
    if a.pilot=='ggs-v1':
        with zipfile.ZipFile(jar) as z:
            if 'forge/ai/ggs/GgsNinjutsuPolicy.class' not in z.namelist(): p.error('ggs-v1 requires the patched Forge build')
    metadata={'deck_sha256':{d.name:hashlib.sha256(d.read_bytes()).hexdigest() for d in (ROOT/'decks').glob('*.dck')},
              'engine_jar_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
              'arguments':{k:str(v) if isinstance(v,pathlib.Path) else v for k,v in vars(a).items()},
              'opponents':'Jaymie supplied main deck; stock Food and Fellowship; stock Turtle Power with Leonardo/Michelangelo',
              'limitations':'Forge AI decisions; stock proxies for two decks; upcoming Visitor script; no human pod win-rate inference.'}
    metadata_path=out/'run_metadata.json'
    if a.resume:
        if not metadata_path.exists(): p.error('Resume requires saved run metadata')
        old=json.loads(metadata_path.read_text())
        if old.get('engine_jar_sha256')!=metadata['engine_jar_sha256'] or old.get('deck_sha256')!=metadata['deck_sha256']:
            p.error('Cannot resume: engine or deck hashes differ or were not recorded')
        for key in ('seed','timeout','games_per_variant','variants','baseline_games','pilot','audit'):
            if old['arguments'].get(key)!=metadata['arguments'].get(key):p.error(f'Cannot resume: {key} differs')
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    jobs=make_jobs(variants,a.games_per_variant,a.seed,a.baseline_games)
    results=[]
    if a.resume:
        pending=[]
        for v,seat,seed in jobs:
            saved=out/'records'/f'{v}__seat{seat}__seed{seed}.json'
            if saved.exists():results.append(json.loads(saved.read_text()))
            else:pending.append((v,seat,seed))
        jobs=pending
        print(f'Reused {len(results)} saved records; {len(jobs)} games remain.',flush=True)
    total=len(results)+len(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(play,engine,out,v,seat,seed,a.timeout,a.pilot,a.audit) for v,seat,seed in jobs]
        for f in concurrent.futures.as_completed(futures):
            r=f.result(); results.append(r)
            (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
            print(f"{len(results)}/{total} {r['variant']} seat {r['seat_rotation']}: {r['status']} {r['winner']}",flush=True)
    print('All requested games attempted. Inspect statuses before interpreting outcomes.',flush=True)
if __name__=='__main__': main()
