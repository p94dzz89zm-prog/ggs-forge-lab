#!/usr/bin/env python3
"""Experimental, resumable strategy-profile learner backed by actual Forge games.

This is a contextual bandit over three bounded strategies, not a neural pilot
or a system that learns Magic's rules. No mutation of decks or Java source.
Training selects a profile, plays a game, measures a fixed utility vector and
updates its preference automatically. Evaluation freezes preferences.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time
import dragonmind
from run_games import validate_deck

PROFILES = ("BALANCED", "ENGINE", "ECONOMY")
REWARD_VERSION = "ggs-effects-v1"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path, data):
    with tempfile.NamedTemporaryFile("w",dir=path.parent,delete=False) as f:
        json.dump(data,f,indent=2);f.write("\n");f.flush();os.fsync(f.fileno());tmp=f.name
    os.replace(tmp,path)

def connect(path):
    db=sqlite3.connect(path)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("""CREATE TABLE IF NOT EXISTS episodes (
        run TEXT, idx INTEGER, context TEXT, mode TEXT, seed INTEGER,
        profile TEXT, status TEXT, reward REAL, evidence TEXT,
        PRIMARY KEY(run,idx))""")
    db.execute("""CREATE TABLE IF NOT EXISTS reviews (
        run TEXT, idx INTEGER, status TEXT CHECK(status IN ('pass','reject','pending')),
        scope TEXT, reason TEXT, reviewer TEXT, PRIMARY KEY(run,idx))""")
    db.execute("""CREATE TABLE IF NOT EXISTS review_events (
        id INTEGER PRIMARY KEY, run TEXT, idx INTEGER, status TEXT, scope TEXT,
        reason TEXT, reviewer TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    db.commit();return db

def statistics(db, context, reviewed=False):
    review_filter="AND EXISTS (SELECT 1 FROM reviews r WHERE r.run=episodes.run AND r.idx=episodes.idx AND r.status='pass')" if reviewed else ""
    rows=db.execute(f"""SELECT profile,COUNT(*) n,AVG(reward) mean FROM episodes
        WHERE context=? AND mode='train' AND status IN ('completed','completed_draw') AND reward BETWEEN 0 AND 1 {review_filter} GROUP BY profile""",(context,)).fetchall()
    found={r["profile"]:dict(r) for r in rows}
    return {p:found.get(p,{"profile":p,"n":0,"mean":0.0}) for p in PROFILES}

def select_profile(stats, training):
    if not training:
        # A tiny training sample cannot replace the audited default.
        if min(s["n"] for s in stats.values())<2:return "BALANCED"
        return max(PROFILES,key=lambda p:(stats[p]["mean"],-PROFILES.index(p)))
    for profile in PROFILES:
        if stats[profile]["n"]==0:return profile
    total=sum(s["n"] for s in stats.values())
    return max(PROFILES,key=lambda p:stats[p]["mean"]+math.sqrt(2*math.log(total)/stats[p]["n"]))

def effects(lines, own):
    """Metrics from observed events, not inferred missed opportunities.

    Combat damage is opponent-player damage during this seat's turn. This is
    an episode metric, not a causal attribution to a particular card or choice.
    GGS counts triggered abilities placed on stack, not guaranteed Dragon tokens.
    """
    turns=ggs=damage=gain=0;active=None
    for line in lines:
        m=re.fullmatch(r"Turn: Turn \d+ \((.*)\)",line.strip())
        if m:
            active=m[1]
            if active==own:turns+=1
        if line.strip()=="Add To Stack: "+own+" triggered Goro-Goro and Satoru":ggs+=1
        if active==own:
            m=re.fullmatch(r"Damage: .* deals (\d+) combat damage to (Ai\(\d+\)-[^.]+)\.",line.strip())
            if m and m[2]!=own:damage+=int(m[1])
        m=re.fullmatch(r"Life: Life: "+re.escape(own)+r" (-?\d+) > (-?\d+)",line.strip())
        if m:gain+=max(0,int(m[2])-int(m[1]))
    if turns==0:raise ValueError("No own-turn markers: refuse unmeasurable experience")
    return {"own_turns":turns,"ggs_triggers":ggs,"opponent_combat_damage_on_own_turn":damage,"life_gained":gain}

def utility(metrics, won):
    turns=metrics["own_turns"]
    # Fixed, inspectable proxy. No claim this spans all card usefulness.
    return (.55*min(metrics["ggs_triggers"]/turns/2,1)
           +.25*min(metrics["opponent_combat_damage_on_own_turn"]/turns/15,1)
           +.10*min(metrics["life_gained"]/turns/5,1)+.10*int(won))

def export(db, out):
    rows=[dict(r) for r in db.execute("SELECT * FROM episodes WHERE run=? ORDER BY idx",(str(out),))]
    for row in rows:
        row["evidence"]=json.loads(row["evidence"] or "{}")
        review=db.execute("SELECT status,scope,reason,reviewer FROM reviews WHERE run=? AND idx=?",(row["run"],row["idx"])).fetchone()
        row["review"]=dict(review) if review else {"status":"pending","scope":"not yet reviewed"}
    contexts={r["context"] for r in rows}
    atomic_json(out/"experience.json",{"reward_version":REWARD_VERSION,"episodes":rows,
        "preferences":{c:statistics(db,c) for c in contexts},
        "reviewed_preferences":{c:statistics(db,c,True) for c in contexts},
        "promotion":"experimental; no automatic claim of improved or error-free play"})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("engine","jar","output","model"):p.add_argument("--"+arg,type=Path,required=True)
    p.add_argument("--games",type=int,default=6,help="Total attempts in this run, including earlier interrupted attempts")
    p.add_argument("--seed",type=int,default=2026102100)
    p.add_argument("--decks",nargs="+",default=["GGS_Current"])
    p.add_argument("--mode",choices=["train","evaluate"],default="train")
    p.add_argument("--pool",choices=["reviewed","sandbox"],default="reviewed",
        help="Default inference uses only reviewed experience; sandbox is explicitly provisional")
    p.add_argument("--timeout",type=int,default=300)
    a=p.parse_args()
    if a.games<1 or a.timeout<1:p.error("Positive game count and timeout required")
    a.jar=a.jar.resolve();a.engine=a.engine.resolve();a.output=a.output.resolve();a.model=a.model.resolve()
    if not a.jar.is_file():p.error("Missing engine JAR")
    if not (a.engine/"res/cardsfolder").is_dir():p.error("Missing engine resources")
    decks=list(dict.fromkeys(a.decks))
    for name in decks:
        if Path(name).name!=name:p.error("Use a deck name from decks/, without a path")
    all_decks=decks+["Jaymie_Ezio","Gabe_Food","Destyn_Turtles"]
    hashes={}
    for name in all_decks:
        path=dragonmind.ROOT/"decks"/(name+".dck");validate_deck(path);hashes[name]=sha(path)
    signature={"jar_sha256":sha(a.jar),"deck_sha256":hashes,"decks":decks,
        "mode":a.mode,"seed":a.seed,"timeout":a.timeout,"reward_version":REWARD_VERSION,
        "model":str(a.model),"profiles":PROFILES,"pool":a.pool}
    # Normalize tuple/list before comparing a restored JSON manifest.
    signature=json.loads(json.dumps(signature))
    a.output.mkdir(parents=True,exist_ok=True);a.model.parent.mkdir(parents=True,exist_ok=True)
    manifest=a.output/"manifest.json"
    if manifest.exists():
        if json.loads(manifest.read_text())!=signature:p.error("Run inputs changed; choose a new output directory")
    else:atomic_json(manifest,signature)
    db=connect(a.model)
    try:
        # Serialize writers for this run. Do not open the same model in two trainers.
        import fcntl
        with a.model.with_suffix(a.model.suffix+".lock").open("w") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            db.execute("UPDATE episodes SET status='interrupted' WHERE run=? AND status='running'",(str(a.output),));db.commit()
            start=db.execute("SELECT COALESCE(MAX(idx)+1,0) FROM episodes WHERE run=?",(str(a.output),)).fetchone()[0]
            frozen_path=a.output/"frozen-profiles.json"
            frozen=json.loads(frozen_path.read_text()) if frozen_path.exists() else {}
            for idx in range(start,a.games):
                deck=decks[idx%len(decks)];rotation=idx%4;seed=a.seed+idx
                context=hashlib.sha256(json.dumps({"jar":signature["jar_sha256"],"reward":REWARD_VERSION,
                    "deck":hashes[deck],"pod":{n:hashes[n] for n in all_decks if n not in decks}},sort_keys=True).encode()).hexdigest()
                if db.execute("SELECT 1 FROM episodes WHERE seed=? AND mode!=? LIMIT 1",(seed,a.mode)).fetchone():
                    raise ValueError("Training/evaluation seed overlap; use a disjoint seed range")
                stats=statistics(db,context,a.pool=="reviewed")
                if db.execute("SELECT 1 FROM episodes WHERE context=? AND seed=? AND mode=? AND status IN ('completed','completed_draw') LIMIT 1",(context,seed,a.mode)).fetchone():
                    raise ValueError("Duplicate completed experience; choose new seeds")
                if a.mode=="evaluate":
                    profile=frozen.setdefault(context,select_profile(stats,False));atomic_json(frozen_path,frozen)
                else:
                    profile=PROFILES[idx%len(PROFILES)] if a.pool=="reviewed" and min(s["n"] for s in stats.values())==0 else select_profile(stats,True)
                db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,NULL,?)",(str(a.output),idx,context,a.mode,seed,profile,"running",json.dumps({"deck":deck,"rotation":rotation,"statistics_before":stats})));db.commit()
                export(db,a.output)
                attempt=a.output/f"attempt-{idx:06d}";attempt.mkdir(exist_ok=False)
                print(f"{idx+1}/{a.games}: {a.mode} {deck}, {profile}, seed {seed}",flush=True)
                rows=dragonmind.batch(a.engine,a.jar,attempt,deck,rotation,[seed],a.timeout,True,False,
                    extra_jvm_flags=("-Ddragonmind.strategyProfile="+profile,"-Ddragonmind.boundedCombatForecast=true"))
                if sha(a.jar)!=signature["jar_sha256"] or any(sha(dragonmind.ROOT/"decks"/(n+".dck"))!=h for n,h in hashes.items()):
                    raise ValueError("Engine or decks changed during game; refuse training")
                row=rows[0];evidence={"game":row,"statistics_before":stats,"experimental":True,"pool":a.pool,"review_status":"pending"}
                reward=None
                if row["status"] in ("completed","completed_draw"):
                    trace=attempt/row["engine_transcript"];own=f"Ai({row['seats'].index(deck)+1})-{deck}"
                    vector=effects(trace.read_text(errors="replace").splitlines(),own)
                    reward=utility(vector,row.get("winner")==own) if a.mode=="train" else None
                    evidence.update(metrics=vector,evaluation_utility=utility(vector,row.get("winner")==own),
                        transcript_sha256=sha(trace),record_sha256=sha(attempt/row["engine_record"]))
                atomic_json(attempt/"experience.json",evidence)
                db.execute("UPDATE episodes SET status=?,reward=?,evidence=? WHERE run=? AND idx=?",
                    (row["status"],reward,json.dumps(evidence),str(a.output),idx));db.commit();export(db,a.output)
                print(f"  {row['status']}; learned reward={reward}",flush=True)
    finally:db.close()

if __name__=="__main__":
    try:main()
    except BlockingIOError:
        raise SystemExit("Another trainer or evaluator is using this model. Let it finish before resuming.")
    except ValueError as error:
        raise SystemExit(str(error))
