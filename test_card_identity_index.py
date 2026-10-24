import copy
from collections import Counter
import json
from pathlib import Path
import unittest
from card_identity_index import IdentityIndex

class IdentityIndexTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(Path(__file__).with_name('reviewed_split_identities.json').read_text());self.index=IdentityIndex(self.manifest)
    def test_explicit_half_and_full_names_bind_one_physical_identity(self):
        c,b=self.index.normalize(Counter({'Dusk':1,'Double Jump':1}));self.assertEqual(c,Counter({'Dusk // Dawn':1,'Double Jump // Flying Kick':1}));self.assertEqual(len(b),2)
    def test_unknown_split_looking_name_is_not_guessed(self):
        c,b=self.index.normalize(Counter({'Unknown // Face':1,'Unknown':1}));self.assertEqual(len(c),2);self.assertEqual(b,[])
    def test_distinct_half_entries_still_count_two_physical_cards(self):
        c,b=self.index.normalize(Counter({'Dusk':1,'Dawn':1}));self.assertEqual(c['Dusk // Dawn'],2)
    def test_colliding_alias_or_duplicate_canonical_rejected(self):
        for canonical in ['Other','Dusk // Dawn']:
            d=copy.deepcopy(self.manifest);d['cards'].append(dict(canonical_name=canonical,names=[canonical,'Dusk'],primary_sources=d['cards'][0]['primary_sources']))
            with self.assertRaises(ValueError):IdentityIndex(d)
    def test_missing_or_untrusted_provenance_rejected(self):
        for sources in [[],['https://example.com/card'],['http://magic.wizards.com/card']]:
            d=copy.deepcopy(self.manifest);d['cards'][0]['primary_sources']=sources
            with self.assertRaises(ValueError):IdentityIndex(d)
    def test_manifest_digest_changes_with_identity_evidence(self):
        d=copy.deepcopy(self.manifest);d['checked_date']='2026-10-24';self.assertNotEqual(self.index.sha256,IdentityIndex(d).sha256)

if __name__=='__main__':unittest.main()
