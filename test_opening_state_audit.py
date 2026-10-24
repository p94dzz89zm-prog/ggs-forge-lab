import copy
import unittest
from opening_state_audit import audit_rows

class OpeningStateTests(unittest.TestCase):
    def setUp(self):
        self.rows=[];self.cid=0;players=[]
        for pid in range(4):
            def card(i,z,cmd=False):return dict(card_id=100*pid+i,name='Card'+str(i),owner_id=pid,zone=z,commander=cmd)
            players.append(dict(id=pid,life=40,Library=[card(i,'Library') for i in range(1,100)],Command=[card(0,'Command',True)],Hand=[],Battlefield=[],Graveyard=[],Exile=[]))
        self.event('GameEventGameStarted',firstTurn={'view_id':0},initial_state={'players':players})
        for pid in range(4):
            for i in range(1,8):self.move(pid,100*pid+i,'Library','Hand')
    def event(self,name,**kw):
        self.cid+=1;state=kw.pop('initial_state',None);r=dict(kind='engine_call',call_id=self.cid,turn=0,phase='null',arguments=[dict(record_type=name,**kw)])
        if state:r['initial_state']=state
        self.rows.append(r);return r
    def move(self,pid,cid,origin,dest,turn=0,phase='null'):
        r=self.event('GameEventCardChangeZone',card={'view_id':cid},**{'from':{'zoneType':origin,'player':{'view_id':pid}},'to':{'zoneType':dest,'player':{'view_id':pid}}});r.update(turn=turn,phase=phase);return r
    def choice(self,pid,keep):
        self.cid+=1;hook='Controller.mulliganKeepHand('
        self.rows.extend([dict(kind='engine_call',call_id=self.cid,hook=hook,receiver={'player_id':pid},speculative=False),dict(kind='engine_return',call_id=self.cid,hook=hook,result=keep)])
    def redraw(self,pid):
        for i in range(1,8):self.move(pid,100*pid+i,'Hand','Library')
        self.event('GameEventShuffle',player={'view_id':pid})
        for i in range(8,15):self.move(pid,100*pid+i,'Library','Hand')
    def finish(self,redrawn=False):
        for pid in range(4):
            r=self.event('GameEventTurnBegan',turnOwner={'view_id':pid});r['turn']=pid+1
            if pid==0:
                r=self.event('GameEventPlayerPriority',phase='UPKEEP',priority={'view_id':0});r.update(turn=1,phase='UPKEEP')
            self.move(pid,100*pid+(15 if pid==0 and redrawn else 8),'Library','Hand',pid+1,'DRAW')
        return audit_rows(self.rows)
    def keep_all(self):
        for pid in range(4):self.choice(pid,True)
    def test_expected_top_draws_and_four_first_turn_draws_are_scoped(self):
        self.keep_all();r=self.finish();self.assertEqual(r['counts']['expected_top_card_draws'],32);self.assertEqual(r['counts']['seven_card_opening_hands'],4);self.assertEqual(r['counts']['first_cycle_draw_step_moves'],4);self.assertEqual(r['confirmed_sequence_defects'],[]);self.assertFalse(r['opening_state_certified']);self.assertEqual(r['independently_approved_historical_events'],0)
    def test_original_sequential_mulligan_reproduces_earliest_defect(self):
        self.choice(0,False);self.redraw(0)
        for pid in [1,2,3]:self.choice(pid,True)
        self.choice(0,True);r=self.finish(True);self.assertEqual(len(r['confirmed_sequence_defects']),1);self.assertEqual(r['confirmed_sequence_defects'][0]['undeclared_players'],[1,2,3])
    def test_all_declarations_before_redraw_has_no_sequence_defect(self):
        self.choice(0,False)
        for pid in [1,2,3]:self.choice(pid,True)
        self.redraw(0);self.choice(0,True);r=self.finish(True);self.assertEqual(r['confirmed_sequence_defects'],[]);self.assertIn('draw_after_unrecorded_shuffle_order',r['gaps'])
    def test_wrong_library_top_rejected(self):
        self.rows[1]['arguments'][0]['card']['view_id']=2;self.keep_all()
        with self.assertRaisesRegex(ValueError,'library top'):self.finish()
    def test_card_return_without_rejection_refuses(self):
        self.move(0,1,'Hand','Library');self.keep_all()
        with self.assertRaisesRegex(ValueError,'declaration'):self.finish()
    def test_initial_duplicate_card_or_bad_life_refuses(self):
        for mode in ['identity','life']:
            old=copy.deepcopy(self.rows[0]);p=self.rows[0]['initial_state']['players'][0]
            if mode=='identity':p['Library'][0]['card_id']=0
            else:p['life']=20
            self.keep_all()
            with self.assertRaises(ValueError):self.finish()
            self.setUp()
    def test_kept_player_cannot_decide_again(self):
        self.keep_all();self.choice(0,False)
        with self.assertRaisesRegex(ValueError,'decision actor'):self.finish()
    def test_wrong_first_turn_order_refuses(self):
        self.keep_all();self.event('GameEventTurnBegan',turnOwner={'view_id':1})
        with self.assertRaisesRegex(ValueError,'turn order'):self.finish()
    def test_missing_complete_cycle_not_certified(self):
        self.keep_all()
        with self.assertRaisesRegex(ValueError,'Incomplete'):audit_rows(self.rows)

if __name__=='__main__':unittest.main()
