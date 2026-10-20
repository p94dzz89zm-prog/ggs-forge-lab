"""Pre-run provenance gate for a separately reserved natural-game attempt.

Does not allocate seeds, certify deck legality, launch a game or approve rules.
Exact configuration and named policy artifacts are required, not inferred from
system defaults. Keep generated manifests private (paths/config may be private).
"""
import hashlib
import json
from pathlib import Path
from evaluation_batch import resource_fingerprint
from milestone_checkpoint import file_digest


REQUIRED_CONFIG = frozenset({'starting_life', 'commander_damage', 'free_seven_mulligans',
                             'format', 'seats', 'engine_timeout_seconds', 'outer_timeout_seconds'})


def fingerprint(spec):
    if not isinstance(spec, dict) or set(spec) != {'source_commit', 'seed', 'command', 'config',
            'policies', 'files', 'resource_root', 'deck_legality_evidence', 'environment'}:
        raise ValueError('Missing or unrecognized frozen runtime input')
    commit = spec['source_commit']
    if not isinstance(commit, str) or len(commit) != 40 or set(commit) - set('0123456789abcdef'):
        raise ValueError('Exact source commit required')
    if type(spec['seed']) is not int or spec['seed'] < 0:
        raise ValueError('Reserved integer seed required')
    command = spec['command']
    if not isinstance(command, list) or not command or not all(isinstance(s, str) and s for s in command):
        raise ValueError('Exact argv required')
    environment = spec['environment']
    if not isinstance(environment, dict) or not all(
            isinstance(k, str) and k and '=' not in k and '\x00' not in k
            and isinstance(v, str) and '\x00' not in v for k, v in environment.items()):
        raise ValueError('Explicit subprocess environment required; no inherited defaults')
    config = spec['config']
    if not isinstance(config, dict) or not REQUIRED_CONFIG <= set(config):
        raise ValueError('Explicit game configuration required')
    if (type(config['starting_life']) is not int or config['starting_life'] <= 0
            or type(config['commander_damage']) is not bool
            or type(config['free_seven_mulligans']) is not int or config['free_seven_mulligans'] < 0
            or config['format'] != 'Commander' or not isinstance(config['seats'], list)
            or len(config['seats']) != 4 or len(set(config['seats'])) != 4
            or not all(isinstance(s, str) and s for s in config['seats'])
            or type(config['engine_timeout_seconds']) is not int or not 0 < config['engine_timeout_seconds'] <= 600
            or type(config['outer_timeout_seconds']) is not int
            or not config['engine_timeout_seconds'] < config['outer_timeout_seconds'] <= 900):
        raise ValueError('Invalid four-player game configuration')
    policies = spec['policies']
    if not isinstance(policies, list) or len(policies) != 4 or not all(
            isinstance(p, dict) and p.get('architecture') in ('rules_validation', 'native_baseline')
            and isinstance(p.get('version'), str) and p['version'] for p in policies):
        raise ValueError('Four explicit nontraining pilot policies required')
    files = spec['files']
    required = {'engine', 'java', 'rules', 'policy_source'} | {f'deck{i}' for i in range(4)}
    if not isinstance(files, dict) or not required <= set(files):
        raise ValueError('Missing engine, Java, rules, policy or deck artifact')
    artifacts = {}
    for name, raw in files.items():
        path = Path(raw)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError('Inputs must be absolute regular nonsymlink files')
        artifacts[name] = dict(path=str(path), sha256=file_digest(path), bytes=path.stat().st_size)
    legality = spec['deck_legality_evidence']
    if not isinstance(legality, str) or legality not in files:
        raise ValueError('Frozen independent deck-legality evidence required')
    # Binding a legality report is NOT checking the report's findings here.
    payload = dict(spec=spec, artifacts=artifacts,
                   resources=resource_fingerprint(spec['resource_root']))
    data = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    return dict(payload, input_sha256=hashlib.sha256(data).hexdigest(),
                deck_legality_approved=False, game_rules_approved=False,
                training_allowed=False)


def verify_unchanged(manifest):
    fresh = fingerprint(manifest['spec'])
    if fresh != manifest:
        raise ValueError('Runtime inputs changed since pre-run freeze')
    return True
