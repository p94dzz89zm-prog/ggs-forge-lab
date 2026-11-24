import copy
from dataclasses import asdict, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pilot_architectures import Selection
from pilot_m1.benchmark import compare, configs
from pilot_m1.fixture import OpeningFixture, branch, exercise
from pilot_m1.lesson import lesson, replay
from pilot_m1.policy import Hand, Pilot, Policy, encode, fingerprint, unpack
from pilot_m1.workers import Pod, load_version, save_version


BASE = Policy().checkpoint()
SEEDS = [7,11,13,17]


def settings():
    return configs(0,[BASE]*4,SEEDS)


def looks():
    return [[Hand(0,3,False),Hand(3,1,True),Hand(7,0,False),Hand(4,1,True)]
            for i in range(4)]


def raw(seat=0):
    return dict(game='opening',seat=seat,revision=0,actions=['keep','redraw'],
                observation=asdict(Hand(3,1,False)))


class IndependentOpeningTests(unittest.TestCase):
    def play(self, root, name, positions):
        engine = OpeningFixture(positions,first=2)
        with Pod(settings(),root/name) as pod:
            self.assertEqual(len({c.pid for c in pod.children.values()}),4)
            exercise(engine,pod)
        records = []
        for seat in range(4):
            p = root/name/f'pilot-{seat}'
            data = (p/'decisions.jsonl').read_bytes()
            rows = [json.loads(r) for r in data.splitlines()]
            self.assertTrue(all(row['offer']['seat']==seat for row in rows))
            self.assertEqual(rows,list(replay(settings()[seat],rows)))
            self.assertTrue(all(row['training_admitted'] is False for row in rows))
            records.append(data)
        return engine,records

    def test_all_four_distinct_processes_use_actual_legal_offer_and_repeat(self):
        with TemporaryDirectory() as d:
            a,records = self.play(Path(d),'a',looks())
            b,repeated = self.play(Path(d),'b',looks())
            self.assertEqual(a.executed,b.executed)
            self.assertEqual(records,repeated)
            self.assertEqual([s.actor for s in a.executed],list('23012301'))
            self.assertEqual([s.token for s in a.executed],['redraw']*4+['keep']*4)

    def test_changes_to_other_hands_future_looks_and_scheduling_are_invisible(self):
        with TemporaryDirectory() as d:
            positions=looks()
            _,before=self.play(Path(d),'a',positions)
            positions[0][3]=Hand(7,0,False)
            positions[1:]=[[Hand(2,1,True)]*4 for _ in range(3)]
            _,after=self.play(Path(d),'b',positions)
            self.assertEqual(before[0],after[0])
            self.assertTrue(all(before[i]!=after[i] for i in (1,2,3)))

    def test_inputs_are_allowlisted(self):
        for field in ('hands','library','rng','outcome'):
            bad=raw()
            bad[field]=['hidden']
            with self.assertRaises(ValueError):
                unpack(bad)
            bad=raw()
            bad['observation'][field]='hidden'
            with self.assertRaises(TypeError):
                unpack(bad)
        for change in ({'seat':True},{'revision':3},{'actions':['keep','cast']},
                       {'observation':{'lands':4,'early':4,'cheap_commander':False}}):
            with self.assertRaises(ValueError):
                unpack({**raw(),**change})

    def test_no_repeated_or_cross_seat_action_after_keep(self):
        p=Pilot(**settings()[0])
        with self.assertRaises(ValueError):
            p.decide(raw(1))
        row=p.decide(raw())
        self.assertEqual(row['selection']['token'],'keep')
        for rev in [0,1]:
            with self.assertRaises(ValueError):
                p.decide({**raw(),'revision':rev})
        self.assertEqual(len(p.history),1)

    def test_fabricated_wrong_actor_and_stale_selections_do_not_advance_engine(self):
        game=OpeningFixture(looks())
        valid=Selection('opening',0,'0','keep')
        for bad in (replace(valid,revision=1),replace(valid,actor='2'),
                    replace(valid,game='another'),replace(valid,token='draw8')):
            self.assertFalse(game.execute(bad))
            self.assertEqual(game.executed,[])
        self.assertTrue(game.execute(valid))
        self.assertFalse(game.execute(valid))
        self.assertEqual(len(game.executed),1)

    def test_fourth_redraw_never_offered(self):
        with TemporaryDirectory() as d:
            game,logs=self.play(Path(d),'cap',[[Hand(0,0,False)]*4 for _ in range(4)])
            self.assertEqual(len(game.executed),12)
            self.assertEqual(set(game.forced),set(range(4)))
            self.assertTrue(all(len(s.splitlines())==3 for s in logs))

    def test_rejected_and_alternative_choice_at_same_position(self):
        engine=OpeningFixture(looks(),first=1)
        prefix=[Selection('opening',0,'1','redraw')]
        choice=Selection('opening',0,'2','keep')
        a,keep=branch(looks(),1,prefix,choice)
        b,redraw=branch(looks(),1,prefix,replace(choice,token='redraw'))
        self.assertEqual(a,b)
        self.assertNotEqual(keep.redrawing,redraw.redrawing)
        self.assertEqual(engine.executed,[])
        with self.assertRaises(ValueError):
            branch(looks(),1,prefix,replace(choice,actor='1'))

    def test_policy_checkpoints_are_separate_and_roll_back(self):
        with TemporaryDirectory() as d:
            ids=[save_version(d,i,BASE) for i in range(4)]
            edited=Policy(land_fit=-8).checkpoint(ids[0])
            changed=save_version(d,0,edited)
            self.assertNotEqual(changed,ids[0])
            for i in range(4):
                self.assertEqual(load_version(d,i,ids[i]),BASE)
            with self.assertRaises(ValueError):
                load_version(d,1,changed)
            cfg=settings()[0]
            self.assertEqual(Pilot(**cfg).decide(raw())['selection']['token'],'keep')
            self.assertEqual(Pilot(**{**cfg,'checkpoint':load_version(d,0,changed)})
                             .decide(raw())['selection']['token'],'redraw')

    def test_modes_vary_only_within_margin_and_replay(self):
        initial=Policy(0,0,1).checkpoint()
        def choices(mode):
            return [Pilot(0,0,i,mode,initial).decide(raw())['selection']['token'] for i in range(50)]
        self.assertEqual(set(choices('certification')),{'keep'})
        self.assertEqual(set(choices('exploration')),{'keep','redraw'})
        self.assertEqual(choices('exploration'),choices('exploration'))

    def test_explanation_is_bound_to_calculations_and_detects_tampering(self):
        cfg=settings()[0]
        row=Pilot(**cfg).decide(raw())
        self.assertIn('keep score was 3',lesson(row))
        bad=copy.deepcopy(row)
        bad['calculations']['scores']['keep']=500
        with self.assertRaises(ValueError):
            list(replay(cfg,[bad]))

    def test_legal_choices_never_turn_into_outcome_labels(self):
        row=Pilot(**settings()[0]).decide(raw())
        self.assertIsNone(row['outcome'])
        self.assertIsNone(row['later_assessment'])
        self.assertIs(row['training_admitted'],False)
        self.assertNotIn('feedback',row)
        self.assertNotIn('engine',row['offer'])

    def test_benchmark_matches_all_seats_conditions_budgets_and_denominators(self):
        positions=[('one',[Hand(4,0,False)]*4),('two',[Hand(1,0,True)]*4)]
        lineups={'previous':[BASE]*4,'fixed':[BASE]*4,'other':[Policy(-9).checkpoint()]*4,
                 'historical':[Policy(0).checkpoint()]*4}
        result=compare(positions,lineups,SEEDS,'heldout')
        self.assertEqual(result,compare(positions,lineups,SEEDS,'heldout'))
        self.assertEqual(result['opening_blocks'],2)
        self.assertIsNone(result['win_rate'])
        for report in result['lineups'].values():
            self.assertEqual(report['decisions'],32)
            self.assertEqual(report['counts']['scored_actions'],64)
            self.assertEqual({(r[2],r[3]) for r in report['records']},
                             {(s,i) for s in range(4) for i in range(4)})
        self.assertEqual(result['lineups']['previous'],result['lineups']['fixed'])
        with self.assertRaises(ValueError):
            compare(positions*2,lineups,SEEDS,'heldout')
