import copy,json,tempfile,unittest
from pathlib import Path
from decision_tape import ZONE_EMPTY
from audit_misty_search import audit

class MistySearchAuditTest(unittest.TestCase):
    def test_positive_and_missing_lineage_or_private_disclosure_reject(self):
        card=dict(view_id=274,owner=dict(view_id=2),zone='Library')
        ability=dict(source=dict(card_id=216,zone='Graveyard'),native_original_distinct_instance=True,native_original_source_card_id=216,native_original_ability_id=1225)
        entry=dict(kind='engine_call',call_id=1,turn=11,hook='forge/ai/bridge/PlayerControllerBridge'+ZONE_EMPTY,arguments=['Battlefield',['Library'],ability,[dict(card_id=274)],dict(cards=[card],owner=dict(view_id=2),zones=['Library']), 'Select a card from your library',True,dict(player_id=2)])
        delivery=dict(kind='engine_call',call_id=2,hook='controller.reveal(X)V',arguments=[[card]],visibility_operation='delivery',entitled_player_ids=[2])
        end=dict(kind='engine_return',call_id=1,result=dict(card_id=274))
        rows=[entry,delivery,dict(kind='engine_return',call_id=2,result=None),end]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'search.jsonl'
            path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            result,lineage=audit(path,216,11,True);self.assertEqual(lineage,1225);self.assertEqual(result['selected'],274)
            for mutation in ('lineage','audience','order','selected'):
                bad=copy.deepcopy(rows)
                if mutation=='lineage':bad[0]['arguments'][2].pop('native_original_distinct_instance')
                elif mutation=='audience':bad[1]['entitled_player_ids']=[0,1,2,3]
                elif mutation=='order':bad[1]['arguments'][0][0]['view_id']=999
                else:bad[3]['result']['card_id']=999
                path.write_text(''.join(json.dumps(row)+'\n' for row in bad))
                with self.assertRaises(ValueError,msg=mutation):audit(path,216,11,True)

if __name__=='__main__':unittest.main()
