#!/usr/bin/env python3
"""Run isolated planner checks; preserve every attempt and require exact markers."""
import argparse,hashlib,json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
SUITES={'PlannerForkRegression':8,'LinePlannerRegression':17,'CommanderPlannerScopeRegression':3}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('jar','engine','testng','fixture-classpath','output'):p.add_argument('--'+k,type=pathlib.Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 cp=':'.join(str(x.resolve()) for x in (a.jar,a.testng,a.fixture_classpath));state={'jar_sha256':sha(a.jar),'constructed_check_groups':28,'natural_games':0,'all_passed':False,'suites':[]}
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',cp,'-d',tmp,*[str(ROOT/(s+'.java')) for s in SUITES]],check=True)
  for suite,count in SUITES.items():
   home=(a.output/'homes'/suite).resolve();home.mkdir(parents=True);log=a.output/(suite+'.log');rc=None;timedout=False
   with log.open('w') as f:
    try:rc=subprocess.run(['java','-XX:-UsePerfData','-Xmx1536m','-Djava.awt.headless=true','-Duser.home='+str(home),'-cp',cp+':'+tmp,suite],cwd=a.engine.resolve(),stdout=f,stderr=subprocess.STDOUT,timeout=150).returncode
    except subprocess.TimeoutExpired:timedout=True
   text=log.read_text();markers=[x for x in text.splitlines() if x.startswith('Checks passed:')];ok=rc==0 and not timedout and markers==[f'Checks passed: {count}'] and 'AssertionError' not in text and 'Exception in thread' not in text
   state['suites'].append({'suite':suite,'passed':ok,'returncode':rc,'timeout':timedout,'log_sha256':sha(log),'check_groups':count});(a.output/'validation.json').write_text(json.dumps(state,indent=2)+'\n');print(suite,ok,flush=True)
   if not ok:raise SystemExit(1)
 state['all_passed']=True;(a.output/'validation.json').write_text(json.dumps(state,indent=2)+'\n')
if __name__=='__main__':main()
