#!/usr/bin/env python3
"""Compare an audited batch; expose missing data and seed-block dependence."""
import argparse, collections, itertools, json, math
from run_games import ROOT, make_jobs

def wilson(wins, n):
    if not n: return None
    z=1.959963984540054; p=wins/n; denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return max(0,center-half),min(1,center+half)

def block_sign_p(differences):
    # Treat seats sharing one seed as a block, rather than independent games.
    weights=[abs(d) for d in differences if d]
    if not weights: return 1.0
    observed=abs(sum(differences))
    extreme=sum(abs(sum(s*w for s,w in zip(signs,weights)))>=observed
                for signs in itertools.product((-1,1),repeat=len(weights)))
    return extreme/(2**len(weights))

def compare(output):
    folder=ROOT/output
    rows=json.loads((folder/'audited_records.json').read_text())
    metadata=json.loads((folder/'run_metadata.json').read_text())
    manifest=json.loads((ROOT/'manifest.json').read_text())['decks']
    args=metadata['arguments']
    variants=args.get('variants') or [v for v in manifest if v.startswith('GGS_')]
    scheduled=make_jobs(variants,args['games_per_variant'],args['seed'],args.get('baseline_games'))
    expected=set(scheduled)
    keys=[(r['variant'],r['seat_rotation'],r['seed']) for r in rows]
    if len(keys)!=len(set(keys)) or any(k not in expected for k in keys):
        raise ValueError('Duplicate or unscheduled results')
    bykey=dict(zip(keys,rows)); report=[]
    def finished(r):return r['status'] in ('completed','completed_draw')
    def win(r):return int(r.get('winner','') is not None and r.get('winner','').endswith('-'+r['variant']))
    for v in variants:
        rr=[r for r in rows if r['variant']==v]
        valid=[r for r in rr if finished(r)]
        scheduled_n=sum(x==v for x,s,z in scheduled)
        wins=sum(win(r) for r in valid)
        observed_losses=len(valid)-wins
        ci=wilson(wins,len(valid))
        item={'variant':v,'scheduled':scheduled_n,'recorded':len(rr),
              'statuses':dict(collections.Counter(r['status'] for r in rr)),
              'completed':len(valid),'wins':wins,'observed_completed_fraction':wins/len(valid) if valid else None,
              'wilson95_descriptive_only':ci,
              'all_scheduled_win_fraction_bounds':[wins/scheduled_n,(scheduled_n-observed_losses)/scheduled_n]}
        if v!='GGS_Current':
            paired=[]; differences=collections.defaultdict(int); unpaired=0
            candidates=set(manifest[v]['swaps'].values())
            item['candidate_cast_games']={c:sum(r.get('ggs_event_counts',{}).get('cast: '+c,0)>0 for r in valid) for c in candidates}
            item['candidate_activated_games']={c:sum(r.get('ggs_event_counts',{}).get('activated: '+c,0)>0 for r in valid) for c in candidates}
            item['candidate_triggered_games']={c:sum(r.get('ggs_event_counts',{}).get('triggered: '+c,0)>0 for r in valid) for c in candidates}
            for r in rr:
                base=bykey.get(('GGS_Current',r['seat_rotation'],r['seed']))
                if base and finished(base) and finished(r):
                    d=win(r)-win(base);paired.append(d);differences[r['seed']]+=d
                else:unpaired+=1
            item.update(paired_completed=len(paired),unpaired_recorded=unpaired,
                        paired_net_additional_wins=sum(paired),paired_seed_blocks=len(differences),
                        exploratory_block_sign_p=block_sign_p(list(differences.values())))
        report.append(item)
    tests=[r for r in report if r['variant']!='GGS_Current']
    ordered=sorted(tests,key=lambda r:r['exploratory_block_sign_p']); prior=0
    for i,r in enumerate(ordered):
        prior=max(prior,min(1,r['exploratory_block_sign_p']*(len(ordered)-i)))
        r['exploratory_holm_adjusted_p']=prior
    done=len(rows)==len(scheduled)
    data={'complete':done,'scheduled':len(scheduled),'recorded':len(rows),'versions':report}
    (folder/'COMPARISON.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# 1,000-game comparison','',f"Status: {'all attempts recorded' if done else 'INCOMPLETE — interim checkpoint'}. {len(rows)}/{len(scheduled)} attempts recorded.",'',
      'These are Forge AI observations. Missing outcomes are not losses. The primary paired comparison uses only seed/seat pairs where both games completed; exclusion can bias results. Seeds match inputs but do not guarantee equal draws or AI choices across changed decks.','',
      '| Version | Recorded / scheduled | Completed | GGS wins | Paired completed | Net trial wins in pairs | Adjusted exploratory p |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for r in report:
        p=r.get('exploratory_holm_adjusted_p')
        lines.append(f"| {r['variant']} | {r['recorded']}/{r['scheduled']} | {r['completed']} | {r['wins']} | {r.get('paired_completed','—')} | {r.get('paired_net_additional_wins','—')} | {p:.4f} |" if p is not None else f"| {r['variant']} | {r['recorded']}/{r['scheduled']} | {r['completed']} | {r['wins']} | — | — | — |")
    lines += ['', '## Interpretation limits','',
      'Paired net wins are trial victories minus baseline victories in the same completed seed/seat pairs. The exploratory sign-flip calculation aggregates all seats of a seed into one block and corrects across all trial lists with Holm adjustment. It assumes exchangeability of the signs under the null; it is not a causal estimate of a card’s strength. Interim p values are not grounds for choosing a winner or stopping the batch early.','',
      'COMPARISON.json includes failure counts, candidate cast/activation/trigger exposure and worst/best all-scheduled bounds for unknown outcomes. Wilson intervals are descriptive only and assume independent games, an assumption weakened by seats sharing seeds. A small p value cannot repair missing-data bias, poor AI choices or stock opponent proxies. Recasts and stack entries do not prove board-wipe recovery or resolved triggers.','',
      'No recommendation is justified merely because a version has the highest raw tally. First check completion, paired evidence, candidate exposure, direction across seeds and whether the AI executed the intended synergies.']
    (folder/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'complete':done,'recorded':len(rows),'scheduled':len(scheduled)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='thousand_games');a=p.parse_args();compare(a.output)
