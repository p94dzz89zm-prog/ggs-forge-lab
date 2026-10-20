import copy,json,tempfile,unittest
from pathlib import Path
from audit_partner_looks import searches
from decision_tape import ZONE_EMPTY

class PartnerLooksAuditTest(unittest.TestCase):
    def rows(self):
        cards=[dict(view_id=10,zone='Library',owner=dict(view_id=0))]
        args=['Hand',['Library'],dict(source=dict(card_id=101,name='Sam, Loyal Attendant'),targets=[]),[],dict(cards=cards,owner=dict(view_id=0),zones=['Library']),'search',True,dict(player_id=0)]
        return [dict(kind='engine_call',call_id=1,hook='forge/ai/PlayerControllerAi'+ZONE_EMPTY,arguments=args),
                dict(kind='engine_call',call_id=2,hook='delivery',visibility_operation='delivery',entitled_player_ids=[0],arguments=[cards]),
                dict(kind='engine_return',call_id=2,result=None),dict(kind='engine_return',call_id=1,result=None)]
    def audit(self,rows):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.jsonl';path.write_text(''.join(json.dumps(row)+'\n' for row in rows));return searches(path)
    def test_real_delivery_required_and_wrong_audience_or_domain_rejected(self):
        rows=self.rows();self.assertEqual(self.audit(rows)[0]['deliveries'],1)
        wrong=copy.deepcopy(rows);wrong[1]['entitled_player_ids']=[0,1]
        with self.assertRaisesRegex(ValueError,'unauthorized'):self.audit(wrong)
        wrong=copy.deepcopy(rows);wrong[1]['arguments'][0][0]['view_id']=99
        with self.assertRaisesRegex(ValueError,'domain/order'):self.audit(wrong)
        with self.assertRaisesRegex(ValueError,'Missing look'):self.audit([rows[0],rows[-1]])

if __name__=='__main__':unittest.main()
