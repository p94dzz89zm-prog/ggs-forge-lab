#!/usr/bin/env python3
"""Audit game-record integrity and flag review leads. Not a strategic oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from dragonmind import parse_results, ENGINE_FAILURE

def inspect(directory):
 reports=[]
 for record in sorted(directory.rglob("engine-records/*/*.json")):
  trace=record.with_suffix(".log");issues=[];leads=[]
  expected=json.loads(record.read_text());text=trace.read_text(errors="replace")
  try:
   parsed=parse_results(text,[expected["seed"]])
   if len(parsed)!=1 or parsed[expected["seed"]]!=expected:issues.append("canonical result/transcript mismatch")
  except (ValueError,KeyError,TypeError) as error:issues.append("invalid result: "+str(error))
  if expected["status"] not in ("completed","completed_draw"):issues.append("game incomplete")
  if ENGINE_FAILURE.search(text):issues.append("engine error in transcript")
  for line in text.splitlines():
   if "Goro-Goro and Satoru" in line and "was put into Hand from Battlefield" in line:
    leads.append({"kind":"commander-return","event":line,"meaning":"Could be legitimate interaction; inspect cause before calling it an error."})
  console=record.parents[2]/(record.parent.name+".log")
  zone_warnings=console.read_text(errors="replace").count("Correcting zone for") if console.exists() else None
  reports.append({"record":str(record),"seed":expected["seed"],"status":expected["status"],
   "record_integrity_passed":not issues,"issues":issues,"review_leads":leads,
   "control_change_diagnostics":zone_warnings,"diagnostic_meaning":"Controller-change messages alone are informational, not proof of an engine error.","learning_eligibility":"withheld" if issues or zone_warnings is None else "pending strategic review",
   "record_sha256":hashlib.sha256(record.read_bytes()).hexdigest(),
   "transcript_sha256":hashlib.sha256(trace.read_bytes()).hexdigest(),
   "rules_review":"Only covered mechanics have scenario-level tests; no full-game correctness certificate.",
   "strategy_review":"pending; this script never approves learning experience"})
 return reports

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("directory",type=Path);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 reports=inspect(a.directory);a.output.write_text(json.dumps({"games":reports,"scope":"record integrity and review leads only"},indent=2)+"\n")
 print(json.dumps({"games":len(reports),"integrity_passed":sum(r["record_integrity_passed"] for r in reports),"strategy_approved":0}))
 if not reports or any(not r["record_integrity_passed"] for r in reports):raise SystemExit(1)

if __name__=="__main__":main()
