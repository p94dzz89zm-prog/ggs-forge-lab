#!/usr/bin/env python3
"""Build isolated weak-reference diagnostics; never modify production sources."""
import argparse,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--jar',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
s=(a.source/'forge-gui-desktop/src/main/java/forge/view/SimulateMatch.java').read_text()
assert s.count('public class SimulateMatch {')==1 and s.count('final Game g1 = mc.createGame();')==1
s=s.replace('public class SimulateMatch {','public class SimulateMatch {\n public static final java.util.List<java.lang.ref.WeakReference<Game>> auditGames = new java.util.ArrayList<>();')
s=s.replace('final Game g1 = mc.createGame();','final Game g1 = mc.createGame();\n auditGames.add(new java.lang.ref.WeakReference<>(g1));')
target=a.output/'src/forge/view/SimulateMatch.java';target.parent.mkdir(parents=True);target.write_text(s)
classes=a.output/'classes';classes.mkdir()
subprocess.run(['java','com.sun.tools.javac.Main','-cp',str(a.jar.resolve()),'-d',str(classes),str(target),str(pathlib.Path(__file__).with_name('MemoryRetentionCheck.java'))],check=True)
print('Run MemoryRetentionCheck with classes first on classpath, jar second, from engine res/ working directory; pass normal sim arguments.')
