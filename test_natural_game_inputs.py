import copy
from pathlib import Path
import tempfile
import unittest
from natural_game_inputs import fingerprint, verify_unchanged


class NaturalInputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'res').mkdir();(self.root/'res'/'card').write_text('oracle')
        names = ['engine','java','rules','policy_source','legality']+[f'deck{i}' for i in range(4)]
        for name in names:(self.root/name).write_text(name)
        self.spec = dict(source_commit='a'*40, seed=123, command=['java','-jar','engine'], environment={},
            config=dict(starting_life=40, commander_damage=False, free_seven_mulligans=3,
                format='Commander', seats=['a','b','c','d'], engine_timeout_seconds=300, outer_timeout_seconds=330),
            policies=[dict(architecture='rules_validation', version='test-v1') for i in range(4)],
            files={name:str(self.root/name) for name in names}, resource_root=str(self.root),
            deck_legality_evidence='legality')

    def test_full_freeze_still_grants_no_legality_or_training_approval(self):
        result = fingerprint(self.spec)
        self.assertTrue(verify_unchanged(result))
        self.assertFalse(result['deck_legality_approved'])
        self.assertFalse(result['training_allowed'])

    def test_house_profile_requires_active_unambiguous_jvm_flag(self):
        self.spec['config']['rules_profile']='ggs-house-v1'
        flag='-Ddragonmind.houseProfile=ggs-house-v1'
        self.spec['command'].insert(1,flag)
        self.assertFalse(fingerprint(self.spec)['game_rules_approved'])
        for command in (['java','-jar','engine'],['java','-jar','engine',flag],
                        ['java',flag,flag,'-jar','engine'],
                        ['java',flag,'-Ddragonmind.houseProfile=other','-jar','engine']):
            with self.subTest(command=command),self.assertRaises(ValueError):
                fingerprint({**self.spec,'command':command})

    def test_house_profile_rejects_mismatched_declared_rules(self):
        self.spec['config']['rules_profile']='ggs-house-v1'
        self.spec['command'].insert(1,'-Ddragonmind.houseProfile=ggs-house-v1')
        for key,value in [('starting_life',20),('commander_damage',True),('free_seven_mulligans',1),('rules_profile','unknown')]:
            spec=copy.deepcopy(self.spec);spec['config'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):fingerprint(spec)

    def test_changed_deck_policy_or_resources_rejected(self):
        for name in ('deck0', 'policy_source', 'res/card'):
            with self.subTest(name=name):
                result = fingerprint(self.spec)
                path = self.root/name;original = path.read_bytes();path.write_bytes(original+b'changed')
                with self.assertRaises(ValueError):verify_unchanged(result)
                path.write_bytes(original)

    def test_implicit_inputs_and_strategic_game_policy_rejected(self):
        for key in ('seed','command','config','policies','files','resource_root','deck_legality_evidence','environment'):
            spec = copy.deepcopy(self.spec);del spec[key]
            with self.subTest(key=key), self.assertRaises(ValueError):fingerprint(spec)
        self.spec['policies'][0]['architecture'] = 'strategic'
        with self.assertRaises(ValueError):fingerprint(self.spec)

    def test_symlinks_and_ambiguous_house_rules_rejected(self):
        path = self.root/'link';path.symlink_to(self.root/'rules')
        self.spec['files']['rules'] = str(path)
        with self.assertRaises(ValueError):fingerprint(self.spec)
        self.spec['files']['rules'] = str(self.root/'rules')
        self.spec['config']['commander_damage'] = 0
        with self.assertRaises(ValueError):fingerprint(self.spec)
