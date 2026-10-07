import gzip,json,shutil,tarfile
from pathlib import Path
WORK=Path(__file__).resolve().parents[3]
for archive in sorted((WORK/'amplifier-recovery/Magic Decks').glob('Pure_GGS_Evidence_Part_0[2-5].tar.gz')):
 with tarfile.open(archive) as t:
  summaries=[m for m in t.getmembers() if m.name.endswith('/summary.json')];wanted=set()
  for m in summaries:
   d=Path(m.name).parent;rows=json.load(t.extractfile(m))
   for r in rows:wanted.add(str(d/'audit'/Path(r['log']).stem/f"seat-{r['seats'].index('Pure_GGS')}.jsonl"))
  for m in t:
   if not m.isfile():continue
   if m.name in wanted:
    dest=WORK/Path(m.name).with_suffix('.jsonl.gz');dest.parent.mkdir(parents=True,exist_ok=True)
    with t.extractfile(m) as src,gzip.open(dest,'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
   elif m.name.endswith('.log') and '/audit/' not in m.name or m.name.endswith(('/summary.json','/metadata.json','/performance.json')):
    dest=WORK/m.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with t.extractfile(m) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst)
 print('Restored',archive.name,flush=True)
