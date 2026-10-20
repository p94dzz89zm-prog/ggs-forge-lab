import hashlib
from pathlib import Path
import tempfile
import unittest

from pilot_architectures import (Action, LegalOffer, RulesValidationPilot,
                                 StrategicPilot, step, evaluate_position)


class EngineDouble:
    def __init__(self):
        self.offer = LegalOffer('game', 0, 'seat0', (
            Action('cast1', 'cast', (('advantage', 2),)),
            Action('cast2', 'cast', (('advantage', 1),)),
            Action('pass', 'pass')))
        self.executions = []
        self.reject = False

    def legal_offer(self):return self.offer

    def execute(self, selection):
        # A native adapter must replace this double with full atomic rules checks.
        if self.reject or (selection.game, selection.revision, selection.actor) != (
                self.offer.game, self.offer.revision, self.offer.actor):
            return False
        self.executions.append(selection)
        return True


class PilotArchitectureTests(unittest.TestCase):
    def test_deterministic_and_order_independent(self):
        a, b = RulesValidationPilot(42), RulesValidationPilot(42)
        offer = EngineDouble().offer
        reverse = LegalOffer(offer.game, offer.revision, offer.actor, offer.actions[::-1])
        self.assertEqual([a.choose(offer) for _ in range(20)], [b.choose(reverse) for _ in range(20)])

    def test_rules_pilot_exercises_action_kinds(self):
        engine = EngineDouble();pilot = RulesValidationPilot(42)
        actions = [step(engine, pilot)[0].token for _ in range(6)]
        self.assertIn('pass', actions)
        self.assertTrue(set(actions) & {'cast1', 'cast2'})
        self.assertEqual(pilot.kinds, {'cast': 3, 'pass': 3})

    def test_engine_rejection_cannot_be_overridden_by_either_pilot(self):
        for pilot in (RulesValidationPilot(42), StrategicPilot({'advantage': 1})):
            engine = EngineDouble();engine.reject = True
            selection, accepted = step(engine, pilot)
            self.assertFalse(accepted)
            self.assertEqual(engine.executions, [])

    def test_state_changes_between_offer_and_execution_are_engine_rejected(self):
        engine = EngineDouble()
        class StalePilot:
            def choose(self, offer):
                engine.offer = LegalOffer('game', 1, 'seat0', offer.actions)
                return offer.actions[0].token
        self.assertFalse(step(engine, StalePilot())[1])
        self.assertEqual(engine.executions, [])

    def test_unoffered_action_never_reaches_execution(self):
        class BadPilot:
            def choose(self, offer):return 'invented-free-spell'
        engine = EngineDouble()
        with self.assertRaises(ValueError):step(engine, BadPilot())
        self.assertEqual(engine.executions, [])

    def test_ambiguous_offer_rejected(self):
        for revision, actions in ((True, (Action('a','pass'),)), (0, ()),
                                  (0, (Action('a','pass'), Action('a','cast')))):
            with self.assertRaises(ValueError):LegalOffer('g', revision, 'p', actions)

    def test_strategic_scoring_does_not_change_rules_pilot(self):
        engine = EngineDouble()
        a = RulesValidationPilot(4);b = RulesValidationPilot(4)
        strategy = StrategicPilot({'advantage': 1})
        self.assertEqual(strategy.choose(engine.offer), 'cast1')
        self.assertEqual(a.choose(engine.offer), b.choose(engine.offer))
        self.assertEqual(engine.executions, [])

    def test_nonfinite_strategy_inputs_rejected(self):
        for value in (True, float('nan'), float('inf')):
            with self.assertRaises(ValueError):StrategicPilot({'x': value})
        pilot = StrategicPilot({'x': 1})
        for features in ((('x', float('nan')),), (('x', True),), (('x', 1), ('x', 2))):
            offer = LegalOffer('g', 0, 'p', (Action('x', 'cast', features),))
            with self.assertRaises(ValueError):pilot.choose(offer)

    def test_offline_position_gate_binds_bytes_and_never_executes_or_trains(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'position';path.write_bytes(b'independent position evidence')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            engine = EngineDouble();pilot = StrategicPilot({'advantage': 1})
            for verdict in (False, None, 1, 'approved'):
                with self.assertRaises(ValueError):evaluate_position(engine, pilot,
                    evidence_path=path, expected_sha256=digest, verify_position=lambda *a: verdict)
            result = evaluate_position(engine, pilot, evidence_path=path,
                expected_sha256=digest, verify_position=lambda data, offer: data == path.read_bytes())
            self.assertFalse(result['outcome_training_allowed'])
            self.assertFalse(result['complete_game_approved'])
            self.assertEqual(engine.executions, [])
            path.write_bytes(b'changed')
            with self.assertRaises(ValueError):evaluate_position(engine, pilot,
                evidence_path=path, expected_sha256=digest, verify_position=lambda *a: True)
