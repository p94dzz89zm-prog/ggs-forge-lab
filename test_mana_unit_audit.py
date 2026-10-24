import unittest
from mana_unit_audit import check, check_rejected_transition


def cost(*shards):return {'unpaid_shards':list(shards),'generic':shards.count('{1}')}

class ManaUnitAuditTests(unittest.TestCase):
    def test_rejected_unit_preserves_cost_and_multiset(self):
        a={'color':'C','source_card_id':9,'snow':False}
        b={'color':'U','source_card_id':10,'snow':False}
        self.assertIsNone(check_rejected_transition(cost('{R}'),cost('{R}'),[a,a,b],[b,a,a]))
        for after in ([a,b],[a,a,a,b]):
            with self.assertRaises(ValueError):
                check_rejected_transition(cost('{R}'),cost('{R}'),[a,a,b],after)

    def test_rejected_unit_cannot_reduce_cost_or_change_restrictions(self):
        a={'color':'C','source_card_id':9,'snow':False,'restrictions':'Artifact'}
        with self.assertRaises(ValueError):check_rejected_transition(cost('{R}'),cost(),[a],[a])
        with self.assertRaises(ValueError):check_rejected_transition(cost('{R}'),cost('{R}'),[a],[{**a,'restrictions':''}])

    def test_rejected_unit_missing_evidence_is_gap_and_malformed_rejected(self):
        self.assertIsNotNone(check_rejected_transition('legacy','legacy',[],[]))
        self.assertIsNotNone(check_rejected_transition(cost(),cost(),None,[]))
        with self.assertRaises(ValueError):check_rejected_transition(cost(),cost(),[{}],[{}])

    def run_check(self,before,after,color='U',snow=False,uses=None):
        unit={'color':color,'source_card_id':9,'snow':snow}
        context={'pool':[unit], 'possible_color_uses':{color:uses if uses is not None else {'U':2,'W':1,'C':32}[color]}}
        return check(before,after,unit,context)
    def test_normal_generic_and_colored(self):
        self.assertIsNone(self.run_check(cost('{1}','{U}'),cost('{U}')))
        self.assertIsNone(self.run_check(cost('{U}'),cost()))
    def test_wrong_color_and_missing_unit_rejected(self):
        with self.assertRaises(ValueError):self.run_check(cost('{W}'),cost())
        with self.assertRaises(ValueError):check(cost('{U}'),cost(),{'color':'U'},{'pool':[]})
    def test_conversion_and_colorless_distinguished(self):
        self.assertIsNone(self.run_check(cost('{W}'),cost(),uses=3))
        with self.assertRaises(ValueError):self.run_check(cost('{C}'),cost())
        self.assertIsNone(self.run_check(cost('{C}'),cost(),color='C'))
    def test_hybrid_and_two_generic_hybrid(self):
        self.assertIsNone(self.run_check(cost('{W/U}'),cost()))
        self.assertIsNone(self.run_check(cost('{2/W}'),cost('{1}')))
        self.assertIsNone(self.run_check(cost('{2/W}'),cost(),color='W'))
    def test_snow_and_unsupported_are_explicit(self):
        self.assertIsNone(self.run_check(cost('{S}'),cost(),snow=True))
        with self.assertRaises(ValueError):self.run_check(cost('{S}'),cost())
        self.assertEqual(self.run_check(cost('{X}'),cost()),'Unsupported unpaid mana shard')
    def test_no_unexplained_multi_unit_payment(self):
        with self.assertRaises(ValueError):self.run_check(cost('{U}','{U}'),cost())

    def test_malformed_conversion_masks_cannot_approve_payment(self):
        for mask in (-1, -64, 64, 65, True, 1.0, '1', None):
            with self.subTest(mask=mask):
                with self.assertRaises(ValueError):
                    self.run_check(cost('{W}'),cost(),uses=mask)

    def test_valid_conversion_boundaries(self):
        with self.assertRaises(ValueError):
            self.run_check(cost('{1}'),cost(),uses=0)
        self.assertIsNone(self.run_check(cost('{C}'),cost(),uses=63))

    def test_snow_conversion_does_not_make_non_snow_mana_snow(self):
        unit={'color':'C','source_card_id':9,'snow':True}
        context={'pool':[unit],'possible_color_uses':{'C':32},'snow_for_color':True}
        self.assertIsNone(check(cost('{U}'),cost(),unit,context))
        unit['snow']=False
        with self.assertRaises(ValueError):check(cost('{S}'),cost(),unit,context)
