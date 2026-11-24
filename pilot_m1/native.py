"""Trusted host for a single native opening. The worker never sees the game seed or tape."""
import argparse
from dataclasses import asdict
from hashlib import file_digest
import json
from pathlib import Path
import subprocess
from threading import Timer

from .opening_audit import verify_opening
from . import references
from .benchmark import configs
from .policy import Policy, encode, fingerprint
from .workers import Pod, load_version, save_version


def file_hash(path):
    with path.open('rb') as f:
        return file_digest(f,'sha256').hexdigest()


def verify_trace(rows, choices, seed):
    """Bind policy replies to actual native declarations and every installed redraw hand."""
    finding = verify_opening(rows,seed)
    if finding.pop('declarations') != choices:
        raise ValueError('Policy/native declaration mismatch')
    return dict(scope='native opening declarations and final redraws',choices=len(choices),
                seats=4,projection_features_independently_certified=False,rules=finding,
                observed_game_outcome=None,training_admitted=False)


def run(args):
    root=args.output.resolve()
    root.mkdir(parents=True,exist_ok=False)
    plan=json.loads(args.plan.read_text())
    cp=[Policy().checkpoint() for _ in range(4)]
    registry=(args.registry or root/'registry').resolve()
    if args.versions:
        cp=[load_version(registry,i,h) for i,h in enumerate(args.versions)]
    else:
        for i, version in enumerate(cp):
            save_version(registry,i,version)
    setup=configs(args.rotation,cp,plan['pilot_decision_seeds'],args.mode)
    if args.seed not in plan['native_opening_only_seeds']:
        raise ValueError('Seed outside allocated opening controls')
    original=plan['deck_hashes']
    seats=plan['seats']
    if len(seats)!=4 or len(set(seats))!=4:
        raise ValueError('Four frozen decks required')
    decks=[s+'.dck' for s in seats]
    if any(Path(n).name!=n or file_hash(args.decks/n)!=original[n] for n in decks):
        raise ValueError('Deck provenance mismatch')
    if file_hash(args.jar)!=args.engine_sha256:
        raise ValueError('Engine provenance mismatch')
    reference=references.prepare(args.oracle, args.decks, plan)
    argv=['java','-Xmx760m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true',
          '-Ddragonmind.houseProfile=ggs-house-v1','-Ddragonmind.openingFixture=true',
          f'-Dforge.audit.directory={root}/referee', f'-Duser.home={root}/home',f'-Ddragonmind.resultDirectory={root}/result',
          f'-Ddragonmind.prospectiveOpening={root}/opening.jsonl','-jar',str(args.jar.resolve()),
          'sim','-D',str(args.decks.resolve()),'-d',*decks,'-f','Commander','-seeds',str(args.seed),
          '-c','60','-a',*(['Default']*4)]
    (root/'inputs.json').write_text(encode(dict(argv=argv,engine_sha256=args.engine_sha256,
            plan=plan,rotation=args.rotation,policy_ids=[fingerprint(x) for x in cp]))+'\n')
    choices=[]
    offers=[]
    boundary=0
    with Pod(setup,root/'workers') as pod, (root/'stdout.log').open('x') as log, (
            root/'stderr.log').open('x') as err, subprocess.Popen(argv,cwd=args.forge,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True) as game:
        timer=Timer(90,game.kill)
        timer.start()
        try:
            for line in game.stdout:
                log.write(line)
                if line.startswith('DM_OFFER '):
                    raw=json.loads(line.removeprefix('DM_OFFER '))
                    answer=pod.choose(raw)
                    offers.append(raw)
                    choices.append(answer)
                    game.stdin.write('{game} {actor} {revision} {token}\n'.format(**answer))
                    game.stdin.flush()
                elif line.strip()=='OPENING_FIXTURE_FIRST_PRIORITY':
                    boundary+=1
            game.wait()
        finally:
            timer.cancel()
            if game.poll() is None:
                game.kill()
    if boundary!=1:
        raise ValueError('Native first-priority boundary missing or duplicated')
    tapes=[p for p in [root/'opening.jsonl',root/'opening.jsonl.partial'] if p.is_file()]
    if len(tapes)!=1:
        raise ValueError('Expected one opening capture')
    rows=[json.loads(line) for line in tapes[0].read_text().splitlines()]
    receipt=verify_trace(rows,choices,args.seed)
    verified_projections=references.check(rows,offers,reference)
    receipt.update(projection_features_independently_certified=True,verified_projections=verified_projections,
                   generation=reference['generation'],actor_reference_sha256=fingerprint(reference))
    for cfg in setup:
        sub=root/'workers'/('pilot-%s' % cfg['identity'])
        with (sub/'decisions.jsonl').open() as journal:
            records=[json.loads(line) for line in journal]
        local=[c for c in choices if c['actor']==str(cfg['seat'])]
        if local!=[r['selection'] for r in records]:
            raise ValueError('Private pilot journal disagrees with native choices')
        (sub/'opening-receipt.json').write_text(encode(dict(journal_sha256=file_hash(sub/'decisions.jsonl'),
            executed_declarations=len(local),kept_hand_size=7,training_admitted=False))+'\n')
    receipt.update(process_exit=game.returncode,tape_sha256=file_hash(tapes[0]),choices_sha256=fingerprint(choices))
    (root/'verified.json').write_text(encode(receipt)+'\n')


if __name__ == '__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('plan','jar','forge','decks','output','oracle'):
        cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--seed',type=int,required=True)
    cli.add_argument('--engine-sha256',required=True)
    cli.add_argument('--rotation',type=int,default=0)
    cli.add_argument('--mode',choices=['certification','exploration'],default='certification')
    cli.add_argument('--registry',type=Path)
    cli.add_argument('--versions',nargs=4)
    run(cli.parse_args())
