import sys,pathlib,time,json,concurrent.futures,threading,os
BASE=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(BASE/'ggs-forge-lab'))
from dragonmind import batch
OUT=BASE/'batch-audit-results';OUT.mkdir(exist_ok=False)

stop=threading.Event();samples=[]
def monitor():
 while not stop.wait(.5):
  rows=[]
  for p in pathlib.Path('/proc').glob('[0-9]*'):
   try:
    cmd=(p/'cmdline').read_bytes()
    if b'dragonmind-v9.jar' not in cmd or b'java\x00' not in cmd:continue
    status=(p/'status').read_text();rss=int(next(l.split()[1] for l in status.splitlines() if l.startswith('VmRSS:')))
    stat=(p/'stat').read_text().split(); rows.append({'pid':int(p.name),'rss_kib':rss,'cpu_ticks':int(stat[13])+int(stat[14])})
   except (OSError,StopIteration,ValueError):pass
  samples.append({'t':time.monotonic(),'processes':rows})
t=threading.Thread(target=monitor,daemon=True);t.start();allrows=[]
for workers in (1,2,4):
 start=time.monotonic(); jobs=[[20261011,20261012]]*2 if workers<4 else [[20261011],[20261012],[20261011],[20261012]]
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
  futures=[]
  for i,seeds in enumerate(jobs):
   out=OUT/f'w{workers}-job{i}';out.mkdir(exist_ok=True)
   futures.append(pool.submit(batch,BASE/'pod-test-engine',BASE/'forge-source/forge-gui-desktop/target/dragonmind-v9.jar',out,'GGS_Layered_v1',0,seeds,180,False,False,extra_jvm_flags=['-Xlog:gc*:file='+str(out/'gc.log')+':time,level,tags']))
  rows=[r for f in futures for r in f.result()]
 end=time.monotonic();subset=[s for s in samples if start<=s['t']<=end]
 result={'workers':workers,'wall_seconds':end-start,'records':rows,'peak_total_rss_mib':max((sum(p['rss_kib'] for p in s['processes'])/1024 for s in subset),default=0),'samples':subset}
 allrows.append(result);(OUT/'measurements.json').write_text(json.dumps(allrows,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('records','samples')}),flush=True)
stop.set();t.join();print('DONE',flush=True)
