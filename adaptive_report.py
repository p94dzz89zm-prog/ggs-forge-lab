#!/usr/bin/env python3
"""Render a self-contained, read-only learning report from preserved experience."""
import argparse
from html import escape
import json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("experiences",type=Path,nargs="+")
 p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 episodes=[];preferences={};reviewed={}
 for source in a.experiences:
  data=json.loads(source.read_text());episodes.extend(data["episodes"]);preferences.update(data["preferences"]);reviewed.update(data.get("reviewed_preferences",{}))
 completed=[e for e in episodes if e["status"] in ("completed","completed_draw")]
 train=[e for e in completed if e["mode"]=="train"]
 held=[e for e in completed if e["mode"]=="evaluate"]
 triggers=sum(e["evidence"].get("metrics",{}).get("ggs_triggers",0) for e in completed)
 cards=[]
 for label,value,detail in [("Learner games",len(completed),f"{len(episodes)-len(completed)} incomplete / interrupted"),("Sandbox trials",len(train),"Rejected records excluded from estimates"),("Held-out games",len(held),"Excluded from training"),("Reviewed samples",sum(s["n"] for stats in {c:st for c,st in reviewed.items()}.values() for s in stats.values()),"Only scoped reviews can make data eligible")]:
  cards.append(f'<article class="stat"><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>')
 rows=[]
 for e in episodes:
  m=e["evidence"].get("metrics",{});utility=e["evidence"].get("evaluation_utility")
  game=e["evidence"].get("game",{});deck=game.get("variant",e["evidence"].get("deck","—"))
  values=[e["seed"],deck,e["mode"],e["profile"],e["status"],e.get("review",{}).get("status","pending"),m.get("own_turns","—"),m.get("ggs_triggers","—"),m.get("opponent_combat_damage_on_own_turn","—"),m.get("life_gained","—"),game.get("winner") or "—",f"{utility:.3f}" if utility is not None else "—"]
  rows.append('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in values)+'</tr>')
 profiles=[]
 for context,stats in preferences.items():
  for name,s in stats.items():
   profiles.append(f'<tr><td><code>{escape(context[:10])}</code></td><td>{escape(name)}</td><td>{s["n"]}</td><td>{s["mean"]:.3f}</td><td><span class="badge">Experimental</span></td></tr>')
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DragonMind · Pilot lab</title>
<style>
:root{color-scheme:dark;--bg:#10151b;--panel:#19212a;--line:#303d49;--text:#edf2f5;--muted:#a9b8c5;--gold:#edc080;--mint:#9cdeca}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:55px 28px 80px}.eyebrow{font-size:12px;letter-spacing:.18em;color:var(--gold);font-weight:700}h1{font-size:clamp(34px,5vw,58px);line-height:1.1;letter-spacing:-.04em;margin:14px 0 18px}h2{font-size:23px;letter-spacing:-.02em;margin:0 0 18px}.intro{max-width:760px;color:var(--muted);font-size:18px}.status{display:inline-block;border:1px solid #415c58;border-radius:30px;padding:7px 14px;color:var(--mint);font-size:13px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:35px 0}.stat,.section,.note{background:var(--panel);border:1px solid var(--line);border-radius:16px}.stat{padding:22px}.stat span,.stat small{display:block;color:var(--muted)}.stat strong{font-size:43px;line-height:1.5;font-weight:600}.stat small{font-size:12px}.section{padding:26px;margin:20px 0}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;text-align:left;white-space:nowrap}th{color:var(--muted);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.05em}td,th{border-bottom:1px solid var(--line);padding:12px 14px 12px 0}tr:last-child td{border-bottom:0}.badge{color:var(--gold);background:#3b3023;padding:3px 9px;border-radius:20px;font-size:11px}.note{padding:22px 26px;border-left:3px solid var(--gold);color:var(--muted)}.note strong{color:var(--text)}footer{color:var(--muted);font-size:12px;margin-top:25px}a{color:var(--mint)}@media(max-width:800px){.stats{grid-template-columns:repeat(2,1fr)}main{padding:30px 18px}}@media print{body{background:white;color:black}.section,.stat,.note{background:white;border-color:#bbb}td,th{color:black}}
</style><main><div class="eyebrow">DRAGONMIND / PILOT LAB</div><h1>Experience, made inspectable.</h1><div class="status">Persistent strategy learning · experimental</div><p class="intro">A record of what the pilot played, what happened, and what it learned. Rules stay in Forge. This learner adjusts preferences among three bounded strategies.</p><div class="stats">'''+''.join(cards)+'''</div><aside class="note"><strong>Learning is active. Improvement is not yet established.</strong><br>Small samples do not certify stronger play. Training games update preferences; held-out games measure them separately. Completed losses remain in the record. Separate control games and randomized probes are outside this learner-only table.</aside><section class="section"><h2>Strategy preferences</h2><div class="scroll"><table><thead><tr><th>Deck / engine context</th><th>Profile</th><th>Training samples</th><th>Mean proxy utility</th><th>Evidence status</th></tr></thead><tbody>'''+''.join(profiles)+'''</tbody></table></div></section><section class="section"><h2>Every attempt</h2><div class="scroll"><table><thead><tr><th>Seed</th><th>Deck</th><th>Use</th><th>Profile</th><th>Result status</th><th>Review</th><th>Own turns</th><th>GGS triggers</th><th>Combat damage</th><th>Life gained</th><th>Winner</th><th>Utility</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div></section><section class="section"><h2>What the score means</h2><p>The fixed proxy combines GGS triggers per own turn (55%), opponent-player combat damage during own turns (25%), life gained per own turn (10%), and winning (10%). Effects are scaled and capped. A trigger on the stack does not guarantee a Dragon token.</p><p>It does not yet measure card advantage, every defensive benefit, missed opportunities, or whether a specific card caused the result. This is a strategy-profile learner, not a neural pilot or a system that learns card rules.</p></section><footer>Read-only report · no remote scripts, tracking, or training processes · generated from preserved experience</footer></main></html>'''
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(html)
 print(a.output)

if __name__=="__main__":main()
