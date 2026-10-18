"""Fail-closed admission of reviewed outcomes, separate from raw game results.

A review is an explicit, evidence-bound finding, not an automatic certificate
of perfect Magic. Missing evidence or unresolved limits withhold learning.
"""
import hashlib
import json
from pathlib import Path
from milestone_checkpoint import file_digest

REVIEW_VERSION = 1
FULL_SCOPE = 'full_game_rules_and_critical_decisions'
MECHANICS = frozenset({'turn_structure', 'costs_and_mana', 'targeting',
    'stack_and_triggers', 'combat_and_damage', 'zones_and_state_based_actions',
    'critical_decisions'})


def fingerprint(root, game, signature, weights):
    root = Path(root).resolve()
    files = {}
    for field in ('engine_record', 'engine_transcript', 'log'):
        value = game.get(field)
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            raise ValueError('Missing or unsafe ' + field)
        path = (root / value).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Evidence missing or outside attempt: ' + field)
        files[path.relative_to(root).as_posix()] = file_digest(path)
    audits = sorted((root / 'audit').rglob('*.jsonl'))
    if not audits:
        raise ValueError('Missing decision audit')
    for path in audits:
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError('Audit outside attempt')
        files[resolved.relative_to(root).as_posix()] = file_digest(resolved)
    payload = {'files': files, 'inputs': signature, 'weights': weights,
        'game': {key: game.get(key) for key in ('seed', 'status', 'winner', 'seats', 'variant', 'command')}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def assess(root, game, reports, signature, weights, review=None):
    gate = {'version': REVIEW_VERSION, 'purpose': signature.get('purpose', 'development'),
        'status': 'quarantined', 'reason': 'Incomplete or inconsistent game evidence'}
    if game.get('status') not in ('completed', 'completed_draw'):
        return gate
    if len(reports) != 1 or not reports[0].get('record_integrity_passed'):
        return gate
    seats = game.get('seats', [])
    hashes = signature.get('deck_sha256', {})
    def sha256(value):
        return isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')
    if (not isinstance(seats, list) or len(seats) != 4
            or not all(isinstance(s, str) for s in seats) or len(set(seats)) != 4
            or not sha256(signature.get('jar_sha256')) or not isinstance(hashes, dict)
            or not all(sha256(hashes.get(s)) for s in seats)):
        gate['reason'] = 'Missing engine, deck or seat provenance'
        return gate
    try:
        digest = fingerprint(root, game, signature, weights)
        canonical = json.loads((Path(root) / game['engine_record']).read_text())
        if any(canonical.get(k) != game.get(k) for k in ('seed', 'status', 'winner')):
            raise ValueError('Saved game disagrees with canonical result')
    except (OSError, ValueError, KeyError, TypeError) as error:
        gate['reason'] = str(error)
        return gate
    gate['evidence_fingerprint'] = digest
    if gate['purpose'] != 'development':
        gate.update(status='evaluation_only', reason='Held-out evidence cannot update training')
        return gate
    gate.update(status='pending_review', reason='Record integrity alone does not admit learning')
    if review is None:
        return gate
    if not isinstance(review, dict):
        gate.update(status='quarantined', reason='Malformed review')
        return gate
    if (review.get('version') != REVIEW_VERSION or review.get('scope') != FULL_SCOPE
            or review.get('evidence_fingerprint') != digest):
        gate.update(status='quarantined', reason='Review scope, version or evidence binding mismatch')
        return gate
    if (review.get('rules_status') != 'pass' or review.get('critical_decisions_status') != 'pass'
            or review.get('unresolved_issues') != [] or review.get('limitations') != []
            or len(seats) != 4 or len(set(seats)) != 4
            or not isinstance(review.get('reviewed_seats'), list)
            or not all(isinstance(s, str) for s in review['reviewed_seats'])
            or sorted(review['reviewed_seats']) != sorted(seats)
            or not isinstance(review.get('reviewed_mechanics'), list)
            or not all(isinstance(m, str) for m in review['reviewed_mechanics'])
            or set(review['reviewed_mechanics']) != MECHANICS
            or not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip()
            or not isinstance(review.get('findings'), list) or not review['findings']
            or not all(isinstance(f, str) and f.strip() for f in review['findings'])):
        gate['reason'] = 'Rules, critical decisions, all seats and unresolved limits require review'
        return gate
    viewers = set()
    try:
        for path in (Path(root) / 'audit').rglob('seat-*.jsonl'):
            with path.open() as stream:
                for line in stream:
                    state = json.loads(line).get('state', {})
                    viewer = state.get('viewer')
                    if viewer in viewers:
                        continue
                    own = next((p for p in state.get('players', []) if p.get('id') == state.get('viewer_id')), {})
                    if 'hand' in own:
                        viewers.add(viewer)
                        break
    except (OSError, ValueError, TypeError):
        gate['reason'] = 'Malformed all-seat decision audit'
        return gate
    expected = {f'Ai({i + 1})-{name}' for i, name in enumerate(seats)}
    if not expected.issubset(viewers):
        gate['reason'] = 'Missing private viewer evidence for one or more seats'
        return gate
    gate.update(status='approved_for_learning', reason='Explicit full-scope review bound to evidence',
        reviewed_fingerprint=digest)
    return gate


def feedback(game):
    gate = game.get('learning_gate', {})
    value = game.get('feedback')
    if (gate.get('version') != REVIEW_VERSION or gate.get('status') != 'approved_for_learning'
            or gate.get('purpose') != 'development'
            or not gate.get('evidence_fingerprint')
            or gate.get('evidence_fingerprint') != gate.get('reviewed_fingerprint')
            or value not in (0.0, 1.0)):
        return None
    return value
