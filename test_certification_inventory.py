import copy
import unittest
from certification_inventory import initial_decks,inventory

class CertificationInventoryTests(unittest.TestCase):
    def setUp(self):
        self.text='[Commander]\n1 Test Commander\n[Main]\n99 Plains\n';players=[]
        for pid in range(4):
            def card(i,name,zone,commander):return dict(card_id=pid*1000+i,name=name,zone=zone,owner_id=pid,commander=commander)
            players.append(dict(id=pid,life=40,Command=[card(0,'Test Commander','Command',True),card(100,'Commander Effect','Command',False)],Hand=[],Library=[card(i,'Plains','Library',False) for i in range(1,100)]))
        self.initial=dict(initial_state=dict(players=players),call_id=25,turn=0,phase='null')
        self.inspection=dict(seed=7,initial=self.initial,receipt_verified=True,open_calls=0,structural_gaps=[],complete={'observed':True},config=dict(commander_damage=False,free_seven_mulligans=3),event_counts={},first_events={},raw_sha256='a'*64,records=5,source_commit='b'*40)
    def test_structural_setup_never_proves_oracle_or_game(self):
        r=inventory(self.inspection,[self.text]*4);self.assertEqual(len(r['initial_structure']),4);self.assertFalse(r['complete_game_approved']);self.assertFalse(r['training_admission']);self.assertEqual(r['root_blockers'][0]['anchor']['turn'],0)
    def test_name_aliases_are_explicit_not_guessed(self):
        self.initial['initial_state']['players'][0]['Library'][0]['name']='Plains // Unverified'
        r=initial_decks(self.initial,[self.text]*4)[0];self.assertFalse(r['identity_multiset_matches']);self.assertEqual(r['unresolved_name_bindings']['Main']['deck_only'],{'Plains':1})
    def test_duplicate_physical_card_or_bad_owner_refuses(self):
        for mode in ['id','owner']:
            before=copy.deepcopy(self.initial);p=self.initial['initial_state']['players'][0]
            if mode=='id':p['Library'][0]['card_id']=0
            else:p['Library'][0]['owner_id']=1
            with self.assertRaises(ValueError):initial_decks(self.initial,[self.text]*4)
            self.initial=before
    def test_missing_or_incomplete_history_refuses(self):
        for k,v in [('complete',None),('receipt_verified',False),('open_calls',1),('structural_gaps',['unknown'])]:
            d=copy.deepcopy(self.inspection);d[k]=v
            with self.assertRaises(ValueError):inventory(d,[self.text]*4)
    def test_nonhouse_profile_stays_distinct(self):
        self.inspection['config']=dict(commander_damage=True,free_seven_mulligans=1)
        r=inventory(self.inspection,[self.text]*4);self.assertEqual(r['candidate_profile'],'historical_nonhouse');self.assertEqual(len(r['root_blockers']),2)
    def test_missing_events_are_gaps_not_vacuous_success(self):
        r=inventory(self.inspection,[self.text]*4)
        self.assertTrue(all(x['blocks_certification'] and x['classification']=='missing_applicability_evidence' for x in r['coverage_obligations']))

if __name__=='__main__':unittest.main()
