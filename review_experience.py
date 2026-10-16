#!/usr/bin/env python3
"""Record scoped referee findings without deleting losses or provisional data."""
import argparse
import json
from pathlib import Path
import adaptive_pilot as a

def record_review(db, run, idx, status, scope, reason, reviewer):
    if not all(str(s).strip() for s in (scope,reason,reviewer)):raise ValueError("Scope, finding and reviewer are required")
    row=db.execute("SELECT * FROM episodes WHERE run=? AND idx=?",(run,idx)).fetchone()
    if row is None:raise ValueError("Unknown episode")
    if status=="pass" and (row["mode"]!="train" or row["status"] not in ("completed","completed_draw") or row["reward"] is None):
        raise ValueError("Only complete, measurable training experience can become eligible")
    db.execute("INSERT INTO review_events(run,idx,status,scope,reason,reviewer) VALUES (?,?,?,?,?,?)",(run,idx,status,scope,reason,reviewer))
    db.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?) ON CONFLICT(run,idx) DO UPDATE SET status=excluded.status,scope=excluded.scope,reason=excluded.reason,reviewer=excluded.reviewer",
               (run,idx,status,scope,reason,reviewer));db.commit()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,required=True);p.add_argument("--run",type=Path,required=True)
    p.add_argument("--episode",type=int,required=True);p.add_argument("--status",choices=["pass","reject","pending"],required=True)
    for name in ("scope","reason","reviewer"):p.add_argument("--"+name,required=True)
    args=p.parse_args();db=a.connect(args.model)
    try:
        import fcntl
        with args.model.with_suffix(args.model.suffix+".lock").open("w") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            record_review(db,str(args.run.resolve()),args.episode,args.status,args.scope,args.reason,args.reviewer)
            a.export(db,args.run.resolve())
        print(json.dumps({"status":args.status,"scope":args.scope,"episode":args.episode}))
    finally:db.close()

if __name__=="__main__":main()
