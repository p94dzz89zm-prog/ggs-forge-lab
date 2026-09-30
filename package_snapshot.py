#!/usr/bin/env python3
"""Archive code and finished game records; never include engine binaries or partial logs."""
import argparse,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('destination',type=pathlib.Path);p.add_argument('--checkpoint',action='store_true');a=p.parse_args()
allowed_logs=set();valid_records=set()
for f in ROOT.glob('*/records/*.json'):
    try:
        d=json.loads(f.read_text());allowed_logs.add(d['log']);valid_records.add(str(f.relative_to(ROOT)))
    except (ValueError,KeyError):pass
with zipfile.ZipFile(a.destination,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.rglob('*')):
        if not f.is_file() or any(part in ('.git','__pycache__') for part in f.parts) or f.suffix in ('.jar','.pyc','.tmp','.zip'):continue
        rel=f.relative_to(ROOT)
        if len(rel.parts)>1 and rel.parts[1]=='logs' and str(rel) not in allowed_logs:continue
        if len(rel.parts)>1 and rel.parts[1]=='records' and str(rel) not in valid_records:continue
        z.write(f,pathlib.Path(ROOT.name)/rel)
    if a.checkpoint:z.writestr('ggs-forge-lab/CHECKPOINT.txt','Interim snapshot. Games remain running; these results are incomplete.\n')
print(a.destination.resolve())
