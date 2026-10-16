#!/usr/bin/env python3
"""Run resumable validation, experimental training and evidence checks together.

This pipeline never promotes unreviewed strategy preferences. Reusing an output
requires the exact engine, sources, resources path and experiment configuration.
Increasing --games resumes the same run with additional attempts.
"""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import adaptive_pilot as a

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("engine", "jar", "forge-source", "testng", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--games", type=int, default=8)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--decks", nargs="+", default=["GGS_Current", "GGS_Two_card_trial"])
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--random-cases", type=int, default=128)
    p.add_argument("--random-start", type=int, default=30000)
    args = p.parse_args()
    if min(args.games, args.timeout, args.random_cases) < 1:
        p.error("Positive attempt, timeout and random-case counts required")
    for key in ("engine", "jar", "forge_source", "testng", "output"):
        setattr(args, key, getattr(args, key).resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    source_files = [ROOT / n for n in ("adaptive_pilot.py", "review_experience.py", "audit_pilot_cycle.py", "dragonmind.py", "run_games.py", "test_adaptive_pilot.py", "train_pilot_cycle.py")]
    source_files += list((ROOT / "forge-fork").glob("*Regression.java"))
    source_files += [ROOT / "forge-fork/RandomCombatReferee.java", ROOT / "forge-fork/run_pilot_recovery.py"]
    source_files += list((ROOT / "forge-fork/pilot-src").rglob("*.java"))
    signature = {"engine": str(args.engine), "jar_sha256": a.sha(args.jar),
                 "forge_source": str(args.forge_source), "testng_sha256": a.sha(args.testng),
                 "source_sha256": {str(f.relative_to(ROOT)): a.sha(f) for f in sorted(set(source_files))},
                 "seed": args.seed, "decks": args.decks, "timeout": args.timeout,
                 "random_cases": args.random_cases, "random_start": args.random_start,
                 "reward_version": a.OUTCOME_REWARD_VERSION}
    signature["deck_sha256"] = {n: a.sha(ROOT / "decks" / (n + ".dck"))
                                  for n in args.decks + ["Jaymie_Ezio", "Gabe_Food", "Destyn_Turtles"]}
    protocol = args.output / "cycle-protocol.json"
    if protocol.exists() and json.loads(protocol.read_text()) != signature:
        p.error("Cycle inputs changed; choose a new output directory")
    a.atomic_json(protocol, signature)

    def run(name, command):
        print(name, flush=True)
        with (args.output / (name + ".log")).open("w") as log:
            result = subprocess.run([sys.executable, *map(str, command)], cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(name + " did not pass; evidence preserved in " + str(args.output))

    run("learner-tests", ["-m", "unittest", "test_adaptive_pilot", "-q"])
    validation = args.output / "validation-r9"
    if validation.exists():
        checks = json.loads((validation / "validation.json").read_text())
        if not checks["all_passed"] or checks["jar_sha256"] != signature["jar_sha256"]:
            p.error("Previous validation did not pass for this engine; choose a new output")
        if any(a.sha(validation / (s["suite"] + ".log")) != s["log_sha256"] for s in checks["suites"]):
            p.error("Validation evidence changed")
    else:
        run("engine-validation", ["forge-fork/run_pilot_recovery.py", "--jar", args.jar,
            "--engine", args.engine, "--forge-source", args.forge_source, "--testng", args.testng,
            "--logs", validation, "--random-cases", args.random_cases, "--random-start", args.random_start])
    model = args.output / "model-v2.sqlite"
    training = args.output / "training-v2"
    run("training", ["-u", "adaptive_pilot.py", "--engine", args.engine, "--jar", args.jar,
        "--output", training, "--model", model, "--games", args.games, "--seed", args.seed,
        "--decks", *args.decks, "--mode", "train", "--pool", "sandbox", "--reward", a.OUTCOME_REWARD_VERSION,
        "--audit", "--timeout", args.timeout])
    run("record-referee", ["referee_games.py", training, "--output", args.output / "referee.json"])
    run("decision-audit", ["audit_pilot_cycle.py", "--model", model, "--directory", training,
        "--output", args.output / "training-review.json"])
    with sqlite3.connect(model) as source, sqlite3.connect(args.output / "model-checkpoint.sqlite") as target:
        source.backup(target)
    print("Cycle complete; experimental preferences preserved, strategic promotion requires review.", flush=True)


if __name__ == "__main__":
    main()
