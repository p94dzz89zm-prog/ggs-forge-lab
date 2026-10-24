"""Independent read-only check of explicit replay birth correspondence evidence."""
import argparse,json
from pathlib import Path
from executable_delta import digest
from replay_identity_audit import births,compare

def verify(original,original_hash,replay):
    if digest(original)!=original_hash:raise ValueError('Original hash mismatch')
    result=compare(births(original),births(replay))
    bindings=[]
    for line in Path(replay).open():
        row=json.loads(line)
        if 'historical_identity_binding' in row:
            binding=row['historical_identity_binding'].copy()
            if binding.pop('rules_approved') is not False:raise ValueError('Unsupported rules approval')
            bindings.append(binding)
    if bindings!=result['causal_identity_correspondence']:raise ValueError('Missing/extra/mismatched explicit causal binding')
    return dict(verified_explicit_bindings=len(bindings),native_id_differences=result['unresolved_engine_id_discrepancies'],
                original_sha256=original_hash,replay_sha256=digest(replay),complete_state_reconstruction=False,rules_approved=False,
                scope='Causal birth correspondence only; native IDs remain different; full state and legality not certified')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True,type=Path);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',required=True,type=Path);a=p.parse_args()
    print(json.dumps(verify(a.original,a.original_sha256,a.replay),indent=2))
