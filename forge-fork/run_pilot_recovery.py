#!/usr/bin/env python3
"""Fresh-process regressions with exact completion markers and resumable evidence.

Exit 0 alone is insufficient: some desktop crash handlers terminate normally.
Artifacts are written atomically after each suite, including failed attempts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
SUITES = {"AccessPackageRegression":28, "FireworkPilotRegression":20,
          "FrostcliffRegression":7, "BoundedForecastRegression":8,
          "PilotRecoveryRegression":52, "CombatRecoveryRegression":28, "RandomCombatReferee":64, "AuditScopeRegression":4, "SneakVarietyRegression":18, "AttackLimitRegression":8, "HasteEconomyRegression":9, "DecisionWeightsRegression":21, "CombinedLethalRegression":18, "MarchDefenseRegression":27, "CounterRescueRegression":24, "CounterRescuePaymentRegression":6, "MarchTrampleRegression":24}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w",dir=path.parent,delete=False) as f:
        json.dump(value,f,indent=2);f.write("\n");f.flush();os.fsync(f.fileno());tmp=f.name
    os.replace(tmp,path)

def completed_evidence(suites):
    """Count only suites with an observed exact completion marker.

    Expected totals describe the plan, including suites never launched after
    a failure. They cannot serve as completed computation.
    """
    passed=[s for s in suites if s['passed']]
    return {'suites_attempted':len(suites),'suites_passed':len(passed),
            'check_groups_passed':sum(s['expected'] for s in passed),
            'randomized_positions_passed':sum(s['expected'] for s in passed if s['suite']=='RandomCombatReferee')}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("jar","engine","testng","logs"):
        p.add_argument("--"+name,type=Path,required=True)
    fixture=p.add_mutually_exclusive_group(required=True)
    fixture.add_argument('--forge-source',type=Path)
    fixture.add_argument('--fixture-classpath',type=Path,
        help='Pinned compiled AITest helper when the upstream source checkout is unavailable')
    p.add_argument("--random-cases",type=int,default=64)
    p.add_argument("--random-start",type=int,default=0)
    p.add_argument('--suite',action='append',help='Run only the named suite(s); a focused new attempt, never an overwrite/resume of old evidence')
    a=p.parse_args()
    if a.random_cases<1:p.error("Positive random case count required")
    suites={**SUITES,"CombinedCounterRescueRegression":14,"MarchShieldRegression":11,"CounterFamilyRegression":28,"TrampleCounterRescueRegression":66,"StrikeCounterRescueRegression":24,"ExileCounterRescueRegression":12,"RegressionLauncherRegression":6,"StudentCopyRegression":6,"RandomCombatReferee":a.random_cases}
    compile_suites=dict(suites)  # Include shared base fixtures even in focused runs.
    if a.suite:
        unknown=set(a.suite)-suites.keys()
        if unknown:p.error('Unknown suite(s): '+', '.join(sorted(unknown)))
        if len(a.suite)!=len(set(a.suite)):p.error('Duplicate suites are not distinct evidence')
        suites={name:suites[name] for name in a.suite}
    a.logs.mkdir(parents=True,exist_ok=False)
    manifest={"jar_sha256":digest(a.jar),"suites":[],"all_passed":False,
              "planned_suites":suites,"planned_check_groups":sum(suites.values()),
              "planned_randomized_positions":suites.get('RandomCombatReferee',0),
              "completed_evidence":completed_evidence([]),"launcher_source_sha256":digest(ROOT/'RegressionLauncher.java'),
              "launch_protocol":"reflection wrapper preserves original thrown failures; exact completion marker still required",
              "note":"16 Prowler repetitions are repeated scenarios, not independent games."}
    if a.fixture_classpath:
        helper=a.fixture_classpath/'forge/ai/AITest.class'
        if not helper.is_file():p.error('Missing pinned AITest helper')
        manifest['fixture_helper_sha256']=digest(helper)
    atomic_json(a.logs/"validation.json",manifest)
    with tempfile.TemporaryDirectory() as compiled:
        cp=str(a.jar.resolve())+":"+str(a.testng.resolve())
        if a.fixture_classpath:cp+=':'+str(a.fixture_classpath.resolve())
        sources=([a.forge_source/"forge-gui-desktop/src/test/java/forge/ai/AITest.java"] if a.forge_source else [])
        sources += [ROOT/'RegressionLauncher.java'] + [ROOT/(s+".java") for s in compile_suites]
        subprocess.run(["java","-XX:-UsePerfData","-m","jdk.compiler/com.sun.tools.javac.Main",
                        "-cp",cp,"-d",compiled,*map(str,sources)],check=True)
        manifest['launcher_class_sha256']=digest(Path(compiled)/'RegressionLauncher.class')
        atomic_json(a.logs/"validation.json",manifest)
        for suite,expected in suites.items():
            log=a.logs/(suite+".log")
            home=(a.logs/"runtime-home"/suite).resolve();home.mkdir(parents=True,exist_ok=False)
            timed_out=False
            with log.open("w") as stream:
                try:
                    result=subprocess.run(["java","-XX:-UsePerfData","-Xmx1536m","-Djava.awt.headless=true","-Duser.home="+str(home),
                        "-cp",cp+":"+compiled,'RegressionLauncher',suite,*([str(a.random_cases),str(a.random_start)] if suite=="RandomCombatReferee" else [])],cwd=a.engine.resolve(),stdout=stream,
                        stderr=subprocess.STDOUT,timeout=150)
                    rc=result.returncode
                except subprocess.TimeoutExpired:
                    rc=None;timed_out=True
            lines=log.read_text(errors="replace").splitlines()
            markers=[l for l in lines if l.startswith("Checks passed:")]
            passed=rc==0 and markers==[f"Checks passed: {expected}"] and not any(
                "AssertionError" in l or "Exception in thread" in l for l in lines)
            manifest["suites"].append({"suite":suite,"passed":passed,"expected":expected,
                "returncode":rc,"timeout":timed_out,"log_sha256":digest(log)})
            manifest['completed_evidence']=completed_evidence(manifest['suites'])
            atomic_json(a.logs/"validation.json",manifest)
            print(f"{suite}: {'PASS' if passed else 'FAIL'}",flush=True)
            if not passed: raise SystemExit(1)
    manifest["all_passed"]=True;atomic_json(a.logs/"validation.json",manifest)

if __name__=="__main__": main()

