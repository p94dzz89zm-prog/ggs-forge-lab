"""Summarize observed JFR stacks without equating sample counts with causal speedup."""
from collections import Counter
import json
from pathlib import Path


def summarize(path):
    events=json.loads(Path(path).read_text())['recording']['events']
    types=Counter();all_samples=Counter();game_samples=Counter();methods=Counter();truncated=0
    recorder=('forge/ai/bridge/EngineEvidence','forge/ai/bridge/ReadinessTrace',
              'forge/ai/bridge/DurableEvidence','forge/ai/bridge/ReplayCardIdentities')
    for event in events:
        types[event['type']]+=1
        if event['type'] not in {'jdk.ExecutionSample','jdk.NativeMethodSample'}:continue
        trace=event['values'].get('stackTrace') or {}
        frames=trace.get('frames',[])
        names=[f['method']['type']['name'] for f in frames]
        truncated+=trace.get('truncated') is True
        recording=any(n.startswith(recorder) for n in names)
        game=any(n=='forge/game/phase/PhaseHandler' for n in names)
        all_samples['samples']+=1;all_samples['with_recorder_frame']+=recording
        if game:
            game_samples['samples']+=1;game_samples['with_recorder_frame']+=recording
            for f in frames:
                name=f['method']['type']['name']
                if name.startswith('forge/'):
                    methods[name+'.'+f['method']['name']]+=1;break
    return dict(events=dict(types),all_observed_samples=dict(all_samples),
        phase_handler_anchored_samples=dict(game_samples),truncated_sample_stacks=truncated,
        top_application_frames_in_phase_samples=methods.most_common(15),
        scope='Observed sampled stacks, including startup/GC/native sampling biases; no matched-seed causal optimization estimate',
        rules_approved=False,strategic_improvement_established=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('events');a=p.parse_args()
    print(json.dumps(summarize(a.events),indent=2,sort_keys=True))
