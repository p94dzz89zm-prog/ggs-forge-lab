#!/usr/bin/env python3
"""Combine independently seeded runs without inferring human win rates."""
import collections,json,re
from run_games import ROOT
records=[]
for directory in ('results','followup'):
    path=ROOT/directory/'audited_records.json'
    if path.exists():records+=json.loads(path.read_text())
by_variant=collections.defaultdict(list)
for d in records:by_variant[d['variant']].append(d)
status=collections.Counter(d['status'] for d in records)
lines=['# Game results','',f"{len(records)} attempted games recorded. Status counts: "+', '.join(f'{n} {k}' for k,n in sorted(status.items()))+'.','',
'True completed draws, if any, are included in the completed column with no winner. Actual four-player Commander games in Forge. Jaymie uses the supplied main deck; Gabe and Destyn use stock proxy lists. These are Forge AI outcomes, not estimates of the human pod’s win rates. Completed-game outcomes exclude every logged exception, timeout, nonzero exit and ambiguous or incomplete outcome. Exclusion can bias the sample.','',
'| Version | Recorded attempts | Completed | GGS wins in completed games | Timeouts | Engine errors | Other incomplete |','|---|---:|---:|---:|---:|---:|---:|']
manifest=json.loads((ROOT/'manifest.json').read_text())
for v in manifest['decks']:
    if not v.startswith('GGS_'):continue
    rows=by_variant[v];counts=collections.Counter(d['status'] for d in rows)
    wins=sum(d['status']=='completed' and d['winner'].endswith('-'+v) for d in rows)
    other=sum(n for k,n in counts.items() if k not in ('completed','completed_draw','timeout','engine_error'))
    lines.append(f"| {v} | {len(rows)} | {counts['completed']+counts['completed_draw']} | {wins} | {counts['timeout']} | {counts['engine_error']} | {other} |")
lines+=['','## Candidate exposure','',
'Games with a GGS cast attempt or activation of each candidate, among completed games of a version containing it. This does not prove resolution or usefulness. A candidate with no observed use is untested in practical play by this sample, even if its deck version won.','',
'| Candidate | Completed games with cast/activation | Trigger stack entries |','|---|---:|---:|']
deck_cards={v:{line.split(' ',1)[1] for line in (ROOT/meta['file']).read_text().splitlines() if re.match(r'^\d+ ',line)} for v,meta in manifest['decks'].items()}
candidates=sorted({n for d in manifest['decks'].values() for n in d.get('swaps',{}).values()}|{'Goldspan Dragon','Determined Iteration'})
for card in candidates:
    used=0;triggered=0
    for d in records:
        if d['status']!='completed' or card not in deck_cards[d['variant']]:continue
        events=d.get('ggs_event_counts',{})
        if any(key==kind+': '+card or key.startswith(kind+': '+card+' targeting ') for key in events for kind in ('cast','activated')):used+=1
        triggered+=sum(n for key,n in events.items() if key=='triggered: '+card or key.startswith('triggered: '+card+' targeting '))
    lines.append(f'| {card} | {used} | {triggered} |')
lines+=['','Four exploratory games per version in the first batch; four more games with a fresh seed for Current, Orochi, Throne and Higure in the follow-up. Seat rotations are not independent seeds. These samples cannot reliably rank close card choices.','',
'Forge’s type-choice scripts for Arcane Adaptation, Kindred Discovery, Cover of Darkness and Roaming Throne prefer the most prominent creature type in the deck. The runner does not override these choices. Consequently the Higure/Adaptation games do not guarantee that the AI named Ninja, and Discovery games do not guarantee that it named Dragon. That limits comparison with intended human play.','',
'Keep the supplied main list as the baseline. The logs have not established that cutting Goldspan Dragon or Determined Iteration improves it. Higure is a legitimate potential trial without Adaptation, but no mainboard change is prescribed by these automated counts.','',
'Original logs, commands, seeds and classifications are included in both run directories. Invalid output is retained, never hidden or converted into a loss.']
(ROOT/'GAME_RESULTS.md').write_text('\n'.join(lines)+'\n')
(ROOT/'all_audited_records.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({'recorded_attempts':len(records),'statuses':dict(status)},indent=2))
