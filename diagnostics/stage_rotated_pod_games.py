"""Split audited warm batches into per-seed cohorts, selecting explicitly named retries."""
import argparse,json,re,shutil
from pathlib import Path

def stage(raw, output, retries):
    output.mkdir(exist_ok=False,parents=True);selection=[]
    for name in ('apex','layered'):
        folder=raw/name;summaries=json.loads((folder/'summary.json').read_text())
        for rotation in range(4):
            originals=sorted((s for s in summaries if s['seat_rotation']==rotation),key=lambda s:s['seed'])
            assert len(originals)==4
            dest=output/name/f'rotation{rotation}';dest.mkdir(parents=True)
            variant=originals[0]['variant'];labels={r['seed']:f'{variant}__seat{rotation}__seeds{r["seed"]}-{r["seed"]}' for r in originals}
            chunks={}
            for logname in dict.fromkeys(r['log'] for r in originals):
                batch_rows=[r for r in originals if r['log']==logname]
                lines=[]
                for line in (folder/logname).read_text().splitlines():
                    lines.append(line)
                    if line.startswith('DragonMind Result: '):
                        seed=json.loads(line.split(': ',1)[1])['seed'];chunks[seed]='\n'.join(lines)+'\n';lines=[]
                original_audit=folder/'audit'/Path(logname).stem
                for file in original_audit.glob('*.jsonl'):
                    segment=0;previous=0;streams={}
                    try:
                        for line in file.open():
                            row=json.loads(line);turn=row['state']['turn'] if 'state' in row else row['turn']
                            if turn<previous:segment+=1
                            previous=turn;assert segment<len(batch_rows),(file,segment)
                            seed=batch_rows[segment]['seed']
                            if seed not in streams:
                                target=dest/'audit'/labels[seed]/file.name;target.parent.mkdir(parents=True,exist_ok=True);streams[seed]=target.open('w')
                            streams[seed].write(line)
                    finally:
                        for stream in streams.values():stream.close()
                    # Incomplete batches may stop before later seeds begin.
                    assert segment<len(batch_rows),(file,segment)
            accepted=[]
            for original in originals:
                seed=original['seed'];retry=retries/name/f'rotation{rotation}'/f'seed{seed}' if retries else None
                row=original.copy();selected='original'
                if retry and (retry/'summary.json').exists():
                    retry_rows=json.loads((retry/'summary.json').read_text());assert len(retry_rows)==1
                    row=retry_rows[0].copy();selected=str(retry.relative_to(retries))
                    target=dest/'audit'/labels[seed]
                    if target.exists():shutil.rmtree(target)
                    if row['status'] in ('completed','completed_draw'):
                        source=retry/'audit'/Path(row['log']).stem
                        shutil.copytree(source,target)
                        chunks[seed]=(retry/row['log']).read_text()
                selection.append({'deck':name,'rotation':rotation,'seed':seed,'original_status':original['status'],'selected':selected,'accepted_status':row['status']})
                if row['status'] not in ('completed','completed_draw'):
                    target=dest/'audit'/labels[seed]
                    if target.exists():shutil.rmtree(target)
                    continue
                assert seed in chunks
                seat=row['seats'].index(row['variant'])
                assert (dest/'audit'/labels[seed]/f'seat-{seat}.jsonl').exists()
                row['log']=labels[seed]+'.log';(dest/row['log']).write_text(chunks[seed]);accepted.append(row)
            (dest/'summary.json').write_text(json.dumps(accepted,indent=2)+'\n')
            shutil.copyfile(folder/'metadata.json',dest/'metadata.json')
            (dest/'performance.json').write_text(json.dumps({'completed':len(accepted),'engine_seconds':[r['engine_ms']/1000 for r in accepted],'meaning':'Per-rotation accepted cohort; see raw batch performance for throughput.'},indent=2)+'\n')
    (output/'attempt-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    return selection
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path);p.add_argument('output',type=Path);p.add_argument('--retries',type=Path);a=p.parse_args();print(json.dumps(stage(a.raw,a.output,a.retries),indent=2))
