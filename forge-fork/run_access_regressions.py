#!/usr/bin/env python3
"""Compile and run the focused repair regressions against a packaged engine."""
import argparse,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('engine','jar','testng','forge-source'):p.add_argument('--'+name,type=pathlib.Path,required=True)
 p.add_argument('--logs',type=pathlib.Path,required=True);a=p.parse_args()
 a.logs.mkdir(parents=True,exist_ok=True)
 suites=['AccessPackageRegression','FireworkPilotRegression','FrostcliffRegression','BoundedForecastRegression']
 with tempfile.TemporaryDirectory() as directory:
  cp=str(a.jar.resolve())+':'+str(a.testng.resolve())
  sources=[a.forge_source/'forge-gui-desktop/src/test/java/forge/ai/AITest.java',*[ROOT/(n+'.java') for n in suites]]
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',cp,'-d',directory,*map(str,sources)],check=True)
  for suite in suites:
   with (a.logs/(suite+'.log')).open('w') as stream:
    subprocess.run(['java','-XX:-UsePerfData','-Xmx1536m','-Djava.awt.headless=true','-cp',cp+':'+directory,suite],
     cwd=a.engine.resolve(),stdout=stream,stderr=subprocess.STDOUT,timeout=90,check=True)
   print(suite+': PASS',flush=True)
if __name__=='__main__':main()
