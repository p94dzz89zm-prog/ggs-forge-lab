"""Two experimental policy architectures; legality and execution belong to engine.

This adapter is not yet wired into Forge. Forge's bridge candidate list is NOT
a LegalOffer: payment and target completion still require engine validation.
No engine/referee tape or opponents' private state is accepted by this API.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Protocol


@dataclass(frozen=True)
class Action:
    token: str                 # opaque engine-issued capability, not card text
    kind: str
    features: tuple = ()       # engine-sanitized policy features, never legality


@dataclass(frozen=True)
class LegalOffer:
    game: str
    revision: int
    actor: str
    actions: tuple

    def __post_init__(self):
        if (not all(isinstance(x, str) and x for x in (self.game, self.actor))
                or type(self.revision) is not int or self.revision < 0
                or not isinstance(self.actions, tuple) or not self.actions
                or not all(isinstance(a, Action) and isinstance(a.token, str) and a.token
                           and isinstance(a.kind, str) and a.kind for a in self.actions)
                or len({a.token for a in self.actions}) != len(self.actions)):
            raise ValueError('Invalid engine offer')


@dataclass(frozen=True)
class Selection:
    game: str
    revision: int
    actor: str
    token: str


class Engine(Protocol):
    def legal_offer(self) -> LegalOffer: ...
    def execute(self, selection: Selection) -> bool:
        """Atomically recheck revision, actor, targets, costs and legality.

        Return false without mutation on stale/illegal selection. Never treat
        a cached policy score, canPlay() result or token membership as sufficient.
        """
        ...


def step(engine: Engine, pilot):
    offer = engine.legal_offer()
    token = pilot.choose(offer)
    if token not in {a.token for a in offer.actions}:
        raise ValueError('Pilot selected an unoffered action')
    selection = Selection(offer.game, offer.revision, offer.actor, token)
    # Policy never changes state and cannot bypass this engine check.
    return selection, engine.execute(selection)


class RulesValidationPilot:
    """Pilot A: deterministic interaction coverage, not win-rate optimization.

    Least-visited action kinds first, then token visits and seeded stable ties.
    Includes pass only if engine offers it. A fresh instance per seat/game is
    required; seed and policy version must be frozen in runtime provenance.
    No scripted terminal outcome or turn cap masquerading as a game result.
    """
    version = 'rules-validation-v1-experimental'

    def __init__(self, seed):
        if type(seed) is not int:
            raise ValueError('Integer seed required')
        self.seed, self.kinds, self.tokens = seed, {}, {}

    def choose(self, offer):
        def key(a):
            tie = json.dumps([self.seed, offer.game, offer.actor, offer.revision, a.token])
            return (self.kinds.get(a.kind, 0), self.tokens.get(a.token, 0),
                    sha256(tie.encode()).hexdigest())
        action = min(offer.actions, key=key)
        self.kinds[action.kind] = self.kinds.get(action.kind, 0) + 1
        self.tokens[action.token] = self.tokens.get(action.token, 0) + 1
        return action.token


class StrategicPilot:
    """Pilot B: fixed feature scorer scaffold. No training/self-play promotion.

    Engine supplies sanitized own/public features; rules do not live here.
    Opponent modeling, hidden-state belief and long-term planning are future
    capabilities, not implied by this deliberately small architecture.
    """
    version = 'strategic-v1-offline-only'

    def __init__(self, weights):
        import math
        if not isinstance(weights, dict) or not all(
                isinstance(k, str) and type(v) in (int, float) and math.isfinite(v)
                for k, v in weights.items()):
            raise ValueError('Finite named weights required')
        self.weights = dict(weights)

    def choose(self, offer):
        import math
        def key(action):
            if (not isinstance(action.features, tuple)
                    or any(not isinstance(pair, tuple) or len(pair) != 2
                           or not isinstance(pair[0], str) or type(pair[1]) not in (int, float)
                           or not math.isfinite(pair[1]) for pair in action.features)
                    or len({k for k, v in action.features}) != len(action.features)):
                raise ValueError('Invalid policy features')
            score = sum(self.weights.get(k, 0) * v for k, v in action.features)
            if not math.isfinite(score):
                raise ValueError('Nonfinite policy score')
            return -score, action.token
        return min(offer.actions, key=key).token


def evaluate_position(engine, pilot, *, evidence_path, expected_sha256, verify_position):
    """Offline only: supplied independent verifier must bind position evidence.

    Position approval is not approval of a containing game or outcome training.
    This API does not call execute(), update weights or admit a dataset.
    """
    from pathlib import Path
    data = Path(evidence_path).read_bytes()
    if sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Position evidence changed')
    offer = engine.legal_offer()
    finding = verify_position(data, offer)
    if finding is not True:
        raise ValueError('Position lacks independent rules approval')
    token = pilot.choose(offer)
    if token not in {a.token for a in offer.actions}:
        raise ValueError('Unoffered offline action')
    return dict(token=token, outcome_training_allowed=False,
                complete_game_approved=False, policy_version=pilot.version)
