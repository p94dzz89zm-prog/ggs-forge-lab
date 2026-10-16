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
          "PilotRecoveryRegression":52, "CombatRecoveryRegression":28, "RandomCombatReferee":64, "AuditScopeRegression":4, "SneakVarietyRegression":18, "AttackLimitRegression":8}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w",dir=path.parent,delete=False) as f:
        json.dump(value,f,indent=2);f.write("\n");f.flush();os.fsync(f.fileno());tmp=f.name
    os.replace(tmp,path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("jar","engine","testng","forge-source","logs"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--random-cases",type=int,default=64)
    p.add_argument("--random-start",type=int,default=0)
    a=p.parse_args()
    if a.random_cases<1:p.error("Positive random case count required")
    suites={**SUITES,"RandomCombatReferee":a.random_cases}
    a.logs.mkdir(parents=True,exist_ok=False)
    manifest={"jar_sha256":digest(a.jar),"suites":[],"all_passed":False,
              "targeted_scenarios":157,"randomized_positions":a.random_cases,"executions":173+a.random_cases,
              "note":"16 Prowler repetitions are repeated scenarios, not independent games."}
    atomic_json(a.logs/"validation.json",manifest)
    with tempfile.TemporaryDirectory() as compiled:
        cp=str(a.jar.resolve())+":"+str(a.testng.resolve())
        sources=[a.forge_source/"forge-gui-desktop/src/test/java/forge/ai/AITest.java",
                 *[ROOT/(s+".java") for s in suites]]
        subprocess.run(["java","-XX:-UsePerfData","-m","jdk.compiler/com.sun.tools.javac.Main",
                        "-cp",cp,"-d",compiled,*map(str,sources)],check=True)
        for suite,expected in suites.items():
            log=a.logs/(suite+".log")
            timed_out=False
            with log.open("w") as stream:
                try:
                    result=subprocess.run(["java","-XX:-UsePerfData","-Xmx1536m","-Djava.awt.headless=true",
                        "-cp",cp+":"+compiled,suite,*([str(a.random_cases),str(a.random_start)] if suite=="RandomCombatReferee" else [])],cwd=a.engine.resolve(),stdout=stream,
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
            atomic_json(a.logs/"validation.json",manifest)
            print(f"{suite}: {'PASS' if passed else 'FAIL'}",flush=True)
            if not passed: raise SystemExit(1)
    manifest["all_passed"]=True;atomic_json(a.logs/"validation.json",manifest)

if __name__=="__main__": main()
