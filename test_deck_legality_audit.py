import copy
import unittest
from deck_legality_audit import audit_deck,paper_index,partner_pair,eligible

def card(name,oid,typ='Legendary Creature — Human',ci=None,oracle='',layout='normal'):
    return dict(name=name,oracle_id=oid,id=oid,type_line=typ,color_identity=ci or [],oracle_text=oracle,layout=layout,digital=False,games=['paper'],released_at='2024-01-01',legalities={'commander':'legal'})

class DeckLegalityTests(unittest.TestCase):
    def setUp(self):
        self.commander=card('Commander','cmd',ci=['W']);self.land=card('Plains','land','Basic Land — Plains',ci=['W']);self.cards=[self.commander,self.land];self.deck='[Commander]\n1 Commander\n[Main]\n99 Plains\n';self.bans={'banned_names':[]}
    def audit(self):return audit_deck(self.deck,self.cards,self.bans,game_date='2026-10-20',snapshot_date='2026-10-23')
    def test_100_card_basic_exception_does_not_certify_history(self):
        r=self.audit();self.assertTrue(r['current_snapshot_rules_checks_passed']);self.assertFalse(r['historical_deck_legality_certified']);self.assertFalse(r['training_admission'])
    def test_art_card_and_named_alternate_face_cannot_shadow_real_card(self):
        normal=card('Rampant Growth','spell','Sorcery');prepared=card('Student // Rampant Growth','student');prepared['card_faces']=[{'name':'Student'},{'name':'Rampant Growth'}];art=card('Rampant Growth','art',layout='art_series')
        self.assertEqual(paper_index([prepared,art,normal])['Rampant Growth']['oracle_id'],'spell')
    def test_ambiguous_face_alias_fails_closed(self):
        a=card('A // Common','a');b=card('B // Common','b')
        for c in [a,b]:c['card_faces']=[{'name':'Common'}]
        with self.assertRaises(ValueError):paper_index([a,b])
    def test_singleton_count_aggregates_across_zones(self):
        self.deck='[Commander]\n1 Commander\n[Main]\n1 Commander\n98 Plains\n';self.assertIn('singleton_violation',[x['code'] for x in self.audit()['violations']])
    def test_color_identity_uses_oracle_identity_not_casting_color(self):
        self.cards.append(card('Blue','blue','Instant',ci=['U']));self.deck=self.deck.replace('99 Plains','98 Plains\n1 Blue');self.assertIn('color_identity_violation',[x['code'] for x in self.audit()['violations']]);self.commander['color_identity']=['W','U'];self.assertTrue(self.audit()['current_snapshot_rules_checks_passed'])
    def test_basic_land_type_restriction_checked_separately(self):
        self.land['color_identity']=[];self.commander['color_identity']=[];self.assertIn('basic_land_type_violation',[x['code'] for x in self.audit()['violations']])
    def test_primary_banlist_and_mirror_disagreement_are_visible(self):
        self.bans['banned_names']=['Commander'];r=self.audit();self.assertIn('official_commander_ban',[x['code'] for x in r['violations']]);self.assertIn('mirror_primary_banlist_disagreement',[x['code'] for x in r['evidence_gaps']])
    def test_missing_card_and_nonlegendary_commander_fail(self):
        self.commander['type_line']='Creature — Human';self.assertIn('commander_not_eligible',[x['code'] for x in self.audit()['violations']]);self.cards=[];self.assertFalse(self.audit()['current_snapshot_rules_checks_passed'])
    def test_partner_variants_and_named_partners_cannot_mix(self):
        a=card('A','a',oracle='Partner—Character select');b=card('B','b',oracle='Partner');self.assertFalse(partner_pair(a,b));b['oracle_text']='Partner—Character select';self.assertTrue(partner_pair(a,b));a['oracle_text']='Partner with B';b['oracle_text']='Partner with Wrong';self.assertFalse(partner_pair(a,b))
    def test_future_reprint_does_not_invent_a_new_card_release(self):
        self.land['released_at']='2027-04-09';self.assertTrue(self.audit()['current_snapshot_rules_checks_passed']);self.assertFalse(self.audit()['historical_deck_legality_certified'])
    def test_legendary_vehicle_or_spacecraft_needs_power_toughness_box(self):
        for typ in ['Legendary Artifact — Vehicle','Legendary Artifact — Spacecraft']:
            c=card('Ship','ship',typ);self.assertFalse(eligible(c));c.update(power='4',toughness='4');self.assertTrue(eligible(c))

if __name__=='__main__':unittest.main()
