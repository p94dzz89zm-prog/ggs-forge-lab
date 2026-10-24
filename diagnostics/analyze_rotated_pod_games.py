"""Analyze homogeneous rotated cohorts and export only numeric/outcome fields."""
import argparse, json, statistics, collections
from pathlib import Path
from analyze_five_pod_games import summarize

def analyze(root, per_rotation):
    full={}; public={}; metrics={}
    for name in ('apex','layered'):
        counts=[len(json.loads((root/name/f'rotation{r}'/'summary.json').read_text())) for r in range(4)]
        assert all(0<c<=per_rotation for c in counts)
        cohorts=[summarize(root/name/f'rotation{r}',expected_games=counts[r]) for r in range(4)]
        full[name]=cohorts; rows=[]; triggers=0; combats=[]; first_casts=[]; nj=collections.Counter()
        for rotation,cohort in enumerate(cohorts):
            seat=cohort['summary'][0]['seats'].index(cohort['summary'][0]['variant'])
            for g in cohort['games']:
                row={k:g[k] for k in ('seed','status','winner','engine_ms','last_logged_turn','commander_casts','peak_observed_creature_board','peak_observed_ggs_creatures','excluded_priority_snapshots_without_ggs','ggs_outcome_reason','observed_combat_turns')}
                row.update(rotation=rotation,ggs_seat=seat,ggs_win=g['winner']==f'Ai({seat+1})-'+cohort['summary'][0]['variant'],logged_ggs_triggers=g['trigger_counts'].get('Goro-Goro and Satoru',0))
                rows.append(row);triggers+=row['logged_ggs_triggers'];combats+=list(row['observed_combat_turns'].values());nj.update(g['ninjutsu_evaluation_counts'])
                if g['commander_casts'] and g['commander_casts'][0]['own_turn'] is not None:first_casts.append(g['commander_casts'][0]['own_turn'])
        wins=sum(r['ggs_win'] for r in rows)
        metrics[name]={'planned_games':4*per_rotation,'games':len(rows),'missing_planned_slots':4*per_rotation-len(rows),'wins':wins,'draws':sum(r['status']=='completed_draw' for r in rows),'wins_by_seat':{seat:sum(r['ggs_win'] for r in rows if r['ggs_seat']==seat) for seat in range(4)},'games_by_seat':{seat:sum(r['ggs_seat']==seat for r in rows) for seat in range(4)},'median_audited_seconds':statistics.median(r['engine_ms']/1000 for r in rows),'logged_ggs_triggers':triggers,'median_first_ggs_cast_own_turn':statistics.median(first_casts) if first_casts else None,'ggs_observed_combat_turns':sum(c['ggs_named_creature_seen'] for c in combats),'fresh_attack_with_ggs_turns':sum(c['fresh_attack_with_ggs_seen'] for c in combats),'fresh_unblocked_with_ggs_turns':sum(c['fresh_unblocked_with_ggs_seen'] for c in combats),'ninjutsu_evaluation_counts':dict(nj)}
        public[name]={'games':rows,'metadata':{k:cohorts[0]['metadata'][k] for k in ('jar_sha256','deck_sha256')},'log_sha256':{f'rotation{r}/'+k:v for r,c in enumerate(cohorts) for k,v in c['log_sha256'].items()}}
    common=set.intersection(*({(g['rotation'],g['seed']) for g in d['games']} for d in public.values()))
    for name,d in public.items():
        for g in d['games']:g['matched_valid_pair']=(g['rotation'],g['seed']) in common
        metrics[name]['matched_games']=len(common)
        metrics[name]['matched_wins']=sum(g['ggs_win'] for g in d['games'] if g['matched_valid_pair'])
    return full,public,metrics
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--per-rotation',type=int,default=4);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args()
    full,public,metrics=analyze(a.root,a.per_rotation);a.public_output.mkdir(parents=True,exist_ok=True)
    (a.root/'full-analysis.json').write_text(json.dumps(full,indent=2)+'\n')
    (a.public_output/'analysis.json').write_text(json.dumps(public,indent=2)+'\n')
    (a.public_output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics,indent=2))
