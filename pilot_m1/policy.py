"""Actor-side opening decision. The rules engine alone executes Selection."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from pilot_architectures import Action, LegalOffer, Selection


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(value):
    return sha256(encode(value).encode()).hexdigest()


def bounded(value, low, high):
    return type(value) is int and low <= value <= high


@dataclass(frozen=True)
class Policy:
    land_fit: int = 2
    early_option: int = 1
    keep_bias: int = 0

    def __post_init__(self):
        if not all(bounded(v, -100, 100) for v in asdict(self).values()):
            raise ValueError('Invalid opening weights')

    def checkpoint(self, parent=None):
        if parent is not None and (not isinstance(parent, str) or len(parent) != 64
                or any(c not in '0123456789abcdef' for c in parent)):
            raise ValueError('Invalid parent digest')
        return dict(schema=1, algorithm='opening-linear-v1', weights=asdict(self), parent=parent)

    @classmethod
    def restore(cls, checkpoint):
        policy = cls(**checkpoint['weights'])
        if encode(checkpoint) != encode(policy.checkpoint(checkpoint['parent'])):
            raise ValueError('Incompatible policy checkpoint')
        return policy


@dataclass(frozen=True)
class Hand:
    lands: int
    early: int
    cheap_commander: bool

    def __post_init__(self):
        if (not bounded(self.lands, 0, 7) or not bounded(self.early, 0, 7-self.lands)
                or type(self.cheap_commander) is not bool):
            raise ValueError('Invalid opening projection')


def unpack(raw):
    if set(raw) != {'game', 'seat', 'revision', 'observation', 'actions'}:
        raise ValueError('Unexpected offer fields')
    seat, rev = raw['seat'], raw['revision']
    if (raw['game'] != 'opening' or not bounded(seat, 0, 3) or not bounded(rev, 0, 2)
            or raw['actions'] != ['keep', 'redraw']):
        raise ValueError('Unsupported native declaration window')
    # No free-form card, feature, opponent, token or engine metadata can cross here.
    hand = Hand(**raw['observation'])
    offer = LegalOffer('opening', rev, str(seat), tuple(Action(a, a) for a in raw['actions']))
    return hand, offer


class Pilot:
    def __init__(self, seat, identity, seed, mode, checkpoint):
        if (not bounded(seat,0,3) or not bounded(identity,0,3) or not bounded(seed,0,2**63-1)
                or mode not in ('certification','exploration')):
            raise ValueError('Invalid pilot configuration')
        self.seat, self.identity, self.seed, self.mode = seat, identity, seed, mode
        self.policy = Policy.restore(checkpoint)
        self.version = fingerprint(checkpoint)
        self.history = []

    def decide(self, raw):
        hand, offer = unpack(raw)
        if (offer.actor != str(self.seat) or offer.revision != len(self.history)
                or (self.history and self.history[-1][1] != 'redraw')):
            raise ValueError('Wrong seat, stale offer, or decision after keep')
        values = dict(land_fit=1 if 2 <= hand.lands <= 5 else -1,
                      early_option=1 if hand.early or hand.cheap_commander else -1, keep_bias=1)
        terms = {k: getattr(self.policy,k)*v for k,v in values.items()}
        scores = {'keep': sum(terms.values()), 'redraw': 0}
        ranking = sorted(scores, key=lambda a: (-scores[a],a))
        margin = 1 if self.mode == 'exploration' else 0
        eligible = [a for a in ranking if scores[ranking[0]]-scores[a] <= margin]
        nonce = [self.seed,self.mode,self.version,self.history,asdict(hand),offer.revision]
        token = min(eligible, key=lambda a: fingerprint([nonce,a]))
        selection = Selection(offer.game, offer.revision, offer.actor, token)
        # One worker per opening. If native execution or verification fails, the host
        # interrupts the entire attempt and quarantines its full journal.
        self.history.append((asdict(hand), token))
        return dict(schema=1, pilot=self.identity, decision_seed=self.seed, policy=self.version,
                    mode=self.mode, offer=json.loads(encode(raw)), selection=asdict(selection),
                    calculations=dict(features=values,keep_terms=terms,scores=scores,
                                      eligible=eligible,margin=margin,scored_actions=len(scores)),
                    rejected=[a for a in ranking if a != token],
                    estimate_kind='heuristic preference units', outcome=None, later_assessment=None,
                    training_admitted=False)
