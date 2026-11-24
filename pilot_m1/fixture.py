"""Four-seat declaration engine for frozen seven-card opening scenarios.

Each seat has four precomputed looks. This tests offer/execute, redraw barriers,
and isolation. No shuffled deck, card-specific effect or full game is simulated.
"""
from pilot_architectures import Action, LegalOffer, step
from .policy import Hand


class OpeningFixture:
    def __init__(self, looks, first=0):
        if (type(first) is not int or first not in range(4) or len(looks) != 4
                or any(len(row) != 4 or any(type(h) is not Hand for h in row) for row in looks)):
            raise ValueError('Expected four independent seven-card look series')
        self.looks = tuple(tuple(row) for row in looks)
        self.round = 0
        self.queue = [(first+n)%4 for n in range(4)]
        self.redrawing = []
        self.executed = []
        self.forced = []

    def legal_offer(self):
        if not self.queue:
            raise ValueError('Opening complete')
        return LegalOffer('opening',self.round,str(self.queue[0]),
                          (Action('keep','keep'),Action('redraw','redraw')))

    def actor_view(self):
        from dataclasses import asdict
        offer = self.legal_offer()
        seat = int(offer.actor)
        return dict(game=offer.game, seat=seat, revision=offer.revision,
                    observation=asdict(self.looks[seat][self.round]),
                    actions=[a.token for a in offer.actions])

    def execute(self, selection):
        if not self.queue:
            return False
        current = self.legal_offer()
        if ((selection.game,selection.revision,selection.actor) !=
                (current.game,current.revision,current.actor)
                or selection.token not in {a.token for a in current.actions}):
            return False
        seat = self.queue.pop(0)
        self.executed.append(selection)
        if selection.token == 'redraw':
            self.redrawing.append(seat)
        if not self.queue:
            self.round += 1
            if self.round < 3:
                self.queue = self.redrawing
            else:
                self.forced = self.redrawing
            self.redrawing = []
        return True


def exercise(engine, pod):
    class Routed:
        def choose(self, offer):
            raw = engine.actor_view()
            choice = pod.choose(raw)
            if (offer.game,offer.revision,offer.actor) != (
                    choice['game'],choice['revision'],choice['actor']):
                raise ValueError('Offer changed while dispatching')
            return choice['token']
    while engine.queue:
        _, accepted = step(engine,Routed())
        if not accepted:
            raise ValueError('Rejected declaration')
    return engine.executed

def branch(looks, first, prefix, alternative):
    """Referee-only replay to one exact fixture position and alternative execution."""
    engine = OpeningFixture(looks,first)
    for choice in prefix:
        if not engine.execute(choice):
            raise ValueError('Invalid counterfactual prefix')
    before = engine.actor_view()
    if not engine.execute(alternative):
        raise ValueError('Illegal counterfactual')
    return before, engine
