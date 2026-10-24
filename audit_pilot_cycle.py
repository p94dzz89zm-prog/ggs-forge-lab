#!/usr/bin/env python3
"""Verify preserved training evidence and inspect a narrowly tested decision error.

This is an automated integrity/referee report, never a strategic approval.
"""
import argparse
import json
import sqlite3
from pathlib import Path
import adaptive_pilot as a
from review_experience import verify_evidence


def inspect_decisions(directory):
    files = decisions = redundant = private_leaks = 0
    haste = []
    for path in sorted(directory.rglob("seat-*.jsonl")):
        files += 1
        with path.open() as stream:
            for line in stream:
                row = json.loads(line)
                state = row.get("state", {})
                viewer = state.get("viewer_id")
                players = state.get("players", [])
                for player in players:
                    if player.get("id") != viewer and "hand" in player:
                        private_leaks += 1
                action = row.get("decision", {}).get("action", "")
                if row.get("kind") == "priority" and action != "pass":
                    decisions += 1
                if action != "[{1}{R}: Creatures you control gain haste until end of turn.]":
                    continue
                own = next(p for p in players if p["id"] == viewer)
                beneficiaries = [c["name"] for c in own["battlefield"]
                                 if "Creature" in c.get("type", "")
                                 and c.get("summoning_sick")
                                 and not c.get("phased_out")
                                 and "Haste" not in c.get("keywords", [])]
                redundant += not beneficiaries
                haste.append({"file": str(path.relative_to(directory)),
                              "turn": state.get("turn"), "phase": state.get("phase"),
                              "potential_beneficiaries": beneficiaries})
    return {"audit_files": files, "nonpass_priority_decisions": decisions,
            "redundant_haste_activations": redundant,
            "opponent_private_hand_exposures": private_leaks,
            "haste_decisions": haste,
            "scope": "Snapshot check for one observed error and private-hand exposure; not exhaustive decision review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.model.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    results = []
    try:
        for row in db.execute("SELECT * FROM episodes ORDER BY run,idx"):
            result = {k: row[k] for k in ("run", "idx", "profile", "status", "reward")}
            if row["mode"] != "train" or row["status"] not in ("completed", "completed_draw"):
                result.update(integrity="withheld", reason="Not a completed training attempt")
            else:
                try:
                    verify_evidence(row)
                    result["integrity"] = "pass"
                except (ValueError, OSError, KeyError) as error:
                    result.update(integrity="fail", reason=str(error))
            results.append(result)
        report = {"episodes": results, "decisions": inspect_decisions(args.directory),
                  "strategy_approved": db.execute("SELECT COUNT(*) FROM reviews WHERE status='pass'").fetchone()[0],
                  "review_state": "Automated checks do not approve strategy or promote sandbox preferences"}
        a.atomic_json(args.output, report)
        print(json.dumps({"episodes": len(results), "integrity_passed": sum(r["integrity"] == "pass" for r in results),
                          "redundant_haste": report["decisions"]["redundant_haste_activations"],
                          "strategy_approved": report["strategy_approved"]}))
        if any(r["integrity"] == "fail" for r in results) or report["decisions"]["opponent_private_hand_exposures"]:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
