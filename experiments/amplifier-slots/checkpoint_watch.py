"""Save terminal records more frequently after an observed workspace rollback."""
import fcntl,json,time
from pathlib import Path
from checkpoint import save
OUT=Path(__file__).resolve().parents[3]/'amplifier-slots'
lock=(OUT/'checkpoint-watch.lock').open('w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
while not (OUT/'collection-completed.json').exists():
 for d in sorted(OUT.glob('stage-*')):
  if not (d/'summary.json').exists():continue
  rows=json.loads((d/'summary.json').read_text())
  saved=set(json.loads((d/'saved-game-keys.json').read_text())) if (d/'saved-game-keys.json').exists() else set()
  pending=[r for r in rows if f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}" not in saved]
  if len(pending)>=4:save(d)
 time.sleep(10)
