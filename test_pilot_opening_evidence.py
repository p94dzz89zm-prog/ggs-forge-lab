from copy import deepcopy
from importlib.util import find_spec
import unittest
from pilot_m1.opening_audit import verify_opening
from pilot_m1.references import card_features


class OpeningEvidenceTests(unittest.TestCase):
    def test_foreign_game_seed_rejected_before_replay(self):
        with self.assertRaisesRegex(ValueError,'seed binding'):
            verify_opening([{'evidence_game_id':'25:game'}],24)

    def test_missing_or_invented_rng_receipt(self):
        head=dict(evidence_game_id='24:game',stream_sequence=1,rules_approved=False,
                  random_index=1,kind='opening_random_bits',bits=31,value=-1)
        with self.assertRaisesRegex(ValueError,'randomness mismatch'):
            verify_opening([head],24)
        with self.assertRaisesRegex(ValueError,'Missing or reordered RNG'):
            verify_opening([{**head,'kind':'opening_call'}],24)

    @unittest.skipUnless(find_spec('scryfall_cache'), 'Private Oracle indexer required')
    def test_reversible_physical_printing_projects_real_face_identity(self):
        oid='11111111-1111-1111-1111-111111111111'
        face=dict(name='Test Land',type_line='Land',oracle_text='',oracle_id=oid,mana_cost='')
        row=dict(object='card',id='22222222-2222-2222-2222-222222222222',
                 name='Test Land // Test Land',layout='reversible_card',color_identity=[],
                 legalities={'commander':'legal'},card_faces=[face,deepcopy(face)])
        self.assertEqual(set(card_features(row)),{('Test Land',(oid,True,False))})
