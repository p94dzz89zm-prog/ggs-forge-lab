#!/usr/bin/env python3
"""Run one bounded, exclusively locked training/validation batch.

Scheduling is external. This command finishes a batch; it is not a daemon and
never automatically promotes unreviewed settings into the trusted pilot.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import adaptive_pilot as a
from referee_games import inspect

ROOT=Path(__file__).resolve().parent


def run(args):
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'cycle.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another cycle owns the lock; no duplicate work started.');return
        existing=[int(p.name.split('-')[1]) for p in args.output.glob('cycle-*') if p.is_dir() and p.name.split('-')[1].isdigit()]
        idx=args.cycle_number if args.cycle_number is not None else max(existing,default=-1)+1
        if idx<0:raise ValueError('Cycle number must be nonnegative')
        out=args.output/f'cycle-{idx:03d}';out.mkdir(exist_ok=False)
        record={'cycle':idx,'status':'running','pid':os.getpid(),'started_unix':time.time(),
            'engine_sha256':a.sha(args.jar),'development_seed':2026110000+idx*10,
            'reserved_holdout_seed':2026120000+idx*10,'random_start':50000+idx*128,
            'policy_promotion':False,'strategy_review':'pending; automated record checks do not approve strategy',
            'source_files':{n:a.sha(ROOT/n) for n in ['day_training_cycle.py','policy_search.py','learning_gate.py','forge-fork/run_pilot_recovery.py']}}
        a.atomic_json(out/'cycle.json',record);a.atomic_json(args.output/'latest.json',record)

        def execute(name,command):
            with (out/(name+'.log')).open('w') as stream:
                result=subprocess.run([sys.executable,*map(str,command)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            record[name+'_returncode']=result.returncode;a.atomic_json(out/'cycle.json',record)
            if result.returncode:raise RuntimeError(name+' failed; preserve logs and investigate before another candidate')

        try:
            execute('python-tests',['-m','unittest','discover','-s','.','-p','test_*.py','-q'])
            execute('engine-validation',['-u','forge-fork/run_pilot_recovery.py','--jar',args.jar,
                '--engine',args.engine,'--testng',args.testng,'--fixture-classpath',args.fixture_classpath,
                '--logs',out/'validation','--random-cases','128','--random-start',record['random_start']])
            execute('paired-search',['-u','policy_search.py','--jar',args.jar,'--engine',args.engine,
                '--output',out/'paired-search','--seed',record['development_seed'],'--candidates',args.candidates,
                '--pairs','4','--timeout',args.timeout])
            reports=inspect(out/'paired-search');a.atomic_json(out/'record-referee.json',{'games':reports})
            record['attempts']=len(reports)
            record['record_integrity_passed']=sum(r['record_integrity_passed'] for r in reports)
            record['technical_errors_observed']=sum(not r['record_integrity_passed'] for r in reports)
            if len(reports)!=args.candidates*4:raise RuntimeError('Missing canonical attempt records')
            record['status']='completed' if record['technical_errors_observed']==0 else 'completed_with_failures'
            record['scoped_technical_gate_passed']=record['technical_errors_observed']==0
            record['improvement_established']=False
        except Exception as error:
            record.update(status='blocked',error=str(error),scoped_technical_gate_passed=False,improvement_established=False)
        finally:
            record['finished_unix']=time.time()
            a.atomic_json(out/'cycle.json',record);a.atomic_json(args.output/'latest.json',record)
        print(json.dumps(record,indent=2))
        if record['status']!='completed':raise SystemExit(1)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['engine','jar','testng','fixture-classpath','output']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--candidates',type=int,default=3);p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--cycle-number',type=int,help='Explicit next number from the durable day ledger after workspace recovery')
    args=p.parse_args()
    for key in ['engine','jar','testng','fixture_classpath']:setattr(args,key,getattr(args,key).resolve())
    if args.candidates<2 or args.timeout<1:p.error('At least two candidates and positive timeout required')
    run(args)


if __name__=='__main__':main()
