#!/usr/bin/env python3
"""Check the frozen pod and executable before starting a Firework reliability gate."""
import argparse,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
HASHES={
 'GGS_Firework_Protocol_v1_0':'38298044b173295ac7d0d2d91f2ba4b5c357bc29bf574caaf55103df9f506456',
 'Jaymie_Ezio':'6ed38c348b58f0819c0fe7ce74df02fdf16617c41bbfe74b5c1d0c2f253c2b0e',
 'Gabe_Food':'38afc1adb2bd377aa1c8eb428fb7e29e562c81f0f100550af2b6af724fd270b0',
 'Destyn_Turtles':'3bc8af816de79a50644367bebcf00c8bea6ea79bbd246b292539cd254efd9f8a'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',type=pathlib.Path,required=True);p.add_argument('--jar',type=pathlib.Path,required=True);a=p.parse_args()
 import sys;sys.path.insert(0,str(ROOT));from run_games import validate_deck
 decks={}
 for name,expected in HASHES.items():
  path=ROOT/'decks'/(name+'.dck');counts=validate_deck(path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest!=expected:raise SystemExit('Frozen input differs: '+name)
  decks[name]={'counts':counts,'sha256':digest}
 for required in ('cardsfolder','tokenscripts','editions','languages'):
  if not (a.engine/'res'/required).is_dir():raise SystemExit('Required engine resources missing: '+required)
 with zipfile.ZipFile(a.jar) as z:
  if z.testzip() is not None:raise SystemExit('Engine archive is corrupt')
  for entry in ('forge/ai/ggs/FireworkAccessPolicy.class','forge/ai/ability/ChooseGenericAi.class'):
   if entry not in z.namelist():raise SystemExit('Required repair missing: '+entry)
 print(json.dumps({'ready':True,'decks':decks,'jar_sha256':hashlib.sha256(a.jar.read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':main()
