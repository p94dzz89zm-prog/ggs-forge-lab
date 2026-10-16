#!/usr/bin/env python3
"""Record scoped referee findings without deleting losses or provisional data."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import adaptive_pilot as a

def verify_evidence(row):
    """Recompute eligibility from preserved files, never from a proxy score alone."""
    evidence=json.loads(row["evidence"])
    game=evidence.get("game",{})
    root=(Path(row["run"])/f"attempt-{row['idx']:06d}").resolve()
    console_relative=game.get("log")
    if not isinstance(console_relative,str) or Path(console_relative).is_absolute():raise ValueError("Missing console provenance")
    console=(root/console_relative).resolve()
    if not console.is_relative_to(root) or not console.is_file():raise ValueError("Console outside episode or missing")
    if hashlib.sha256(console.read_bytes()).hexdigest()!=evidence.get("console_sha256"):raise ValueError("Console evidence hash mismatch")
    console_text=console.read_text(errors="replace")
    if a.dragonmind.ENGINE_FAILURE.search(console_text):raise ValueError("Engine failure in console")
    paths={}
    for field,hash_field in (("engine_record","record_sha256"),("engine_transcript","transcript_sha256")):
        relative=game.get(field)
        if not isinstance(relative,str) or not relative or Path(relative).is_absolute():raise ValueError("Missing or unsafe canonical evidence path")
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise ValueError("Canonical evidence missing or outside episode")
        expected=evidence.get(hash_field)
        if not expected or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError("Canonical evidence hash mismatch")
        paths[field]=path
    record=json.loads(paths["engine_record"].read_text())
    text=paths["engine_transcript"].read_text()
    parsed=a.dragonmind.parse_results(text,[row["seed"]])
    if len(parsed)!=1 or parsed.get(row["seed"])!=record:raise ValueError("Canonical result/transcript mismatch")
    if a.dragonmind.ENGINE_FAILURE.search(text):raise ValueError("Engine failure in canonical transcript")
    if record.get("status")!=row["status"] or game.get("status")!=row["status"] or record.get("seed")!=row["seed"]:raise ValueError("Episode/result mismatch")
    seats=game.get("seats",[]);variant=game.get("variant")
    if len(seats)!=4 or len(set(seats))!=4 or seats.count(variant)!=1:raise ValueError("Invalid seat provenance")
    own=f"Ai({seats.index(variant)+1})-{variant}"
    metrics=a.effects(text.splitlines(),own)
    if metrics!=evidence.get("metrics"):raise ValueError("Saved effects disagree with canonical events")
    if game.get("winner")!=record.get("winner"):raise ValueError("Winner provenance mismatch")
    actual=a.utility(metrics,record.get("winner")==own)
    if not isinstance(row["reward"],(int,float)) or not math.isclose(actual,row["reward"],abs_tol=1e-12):raise ValueError("Reward disagrees with observed effects")

def record_review(db, run, idx, status, scope, reason, reviewer):
    if not all(str(s).strip() for s in (scope,reason,reviewer)):raise ValueError("Scope, finding and reviewer are required")
    row=db.execute("SELECT * FROM episodes WHERE run=? AND idx=?",(run,idx)).fetchone()
    if row is None:raise ValueError("Unknown episode")
    if status=="pass" and (row["mode"]!="train" or row["status"] not in ("completed","completed_draw") or row["reward"] is None):
        raise ValueError("Only complete, measurable training experience can become eligible")
    if status=="pass":verify_evidence(row)
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
