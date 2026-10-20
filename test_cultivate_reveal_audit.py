import copy,json,tempfile,unittest
from pathlib import Path
from decision_tape import ZONE_EMPTY
from audit_cultivate_reveal import audit

class RevealAuditTest(unittest.TestCase):
    def rows(self):
        cards=[dict(card_id=11),dict(card_id=22)];views=[dict(view_id=11),dict(view_id=22)]
        source=dict(source=dict(card_id=5))
        def call(i,hook,args,**extra):return dict(kind='engine_call',call_id=i,hook=hook,arguments=args,turn=10,**extra)
        def returned(i,result=None):return dict(kind='engine_return',call_id=i,result=result)
        return [call(1,'forge/game/ability/effects/ChangeZoneEffect.resolve(',[source]),
                call(2,'forge/ai/PlayerControllerAi'+ZONE_EMPTY,['Library',['Library'],source,cards,dict(owner=dict(view_id=1),cards=views),'first',True,dict(player_id=1)]),
                call(3,'look',[views],visibility_operation='delivery',entitled_player_ids=[1]),returned(3),returned(2,cards[0]),
                call(4,'forge/ai/PlayerControllerAi'+ZONE_EMPTY,['Library',['Library'],source,[cards[1]],None,'second',True,dict(player_id=1)]),returned(4,cards[1]),
                call(5,'public',[cards],visibility_operation='reveal_all',entitled_player_ids=[0,1,2,3]),returned(5),returned(1)]
    def check(self,rows):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.jsonl';path.write_text(''.join(json.dumps(row)+'\n' for row in rows));return audit(path,5,10)
    def test_private_and_public_audiences_and_order_are_independently_checked(self):
        rows=self.rows();self.assertEqual(self.check(rows)['public_selected_ids'],[11,22])
        wrong=copy.deepcopy(rows);wrong[2]['entitled_player_ids']=[0,1]
        with self.assertRaisesRegex(ValueError,'Unauthorized'):self.check(wrong)
        wrong=copy.deepcopy(rows);wrong[7]['entitled_player_ids']=[1]
        with self.assertRaisesRegex(ValueError,'all four'):self.check(wrong)
        wrong=copy.deepcopy(rows);wrong[2]['arguments']=[[dict(view_id=22),dict(view_id=11)]]
        with self.assertRaisesRegex(ValueError,'order/domain'):self.check(wrong)

if __name__=='__main__':unittest.main()
