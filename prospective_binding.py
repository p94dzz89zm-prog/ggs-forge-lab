"""Immutable, revalidated deck/rules bindings for prospective diagnostics.

Deck construction is computed independently of Forge against the declared
frozen Oracle mirror. Mirror provenance is explicit, never publisher approval.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from card_identity_index import IdentityIndex
from deck_legality_audit import audit_deck

HOUSE={'players':4,'starting_life':40,'free_seven_reshuffles':3,
       'commander_damage_loss':False,'profile':'ggs-house-v1'}
DECKS=('Gabe_Food.dck','Destyn_Turtles.dck','GGS_Apex_20261017_v1.dck','Jaymie_Ezio.dck')
CATALOG='01b5875e8c3db034f9fa03439329cce9560c8b0c9e66c04df8b5264ae707c1ad'
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def validate_sources(root):
    root=Path(root);provenance=json.loads((root/'public-oracle-provenance.json').read_text())
    if provenance['catalog_receipt']['sha256']!=CATALOG or sha(root/'public-oracle-catalog.jsonl.gz')!=CATALOG:
        raise ValueError('Frozen public catalog hash mismatch')
    if sha(root/'official-banlist.html')!=json.loads((root/'commander-banlist-snapshot.json').read_text())['source_sha256']:
        raise ValueError('Primary banned-list source hash mismatch')
    selected=json.loads((root/'selected-oracle-cards.json').read_text())
    wanted={x['oracle_id']:canonical(x) for x in selected}
    if len(wanted)!=len(selected):raise ValueError('Duplicate selected Oracle identity')
    found=set();total=0
    with gzip.open(root/'public-oracle-catalog.jsonl.gz','rt') as stream:
        for line in stream:
            card=json.loads(line);total+=1;oid=card.get('oracle_id')
            if oid in wanted and canonical(card)==wanted[oid]:found.add(oid)
    if found!=set(wanted):raise ValueError('Selected Oracle record differs from preserved full public catalog')
    rules=(root/'comprehensive-rules.txt').read_text()
    if 'September 25, 2026' not in rules or '903.5a' not in rules:raise ValueError('Unexpected frozen rules version')
    return dict(catalog_records=total,selected_records_verified=len(found),provider=provenance['provider'],
                catalog_updated_at=provenance['bulk_entry']['updated_at'],publisher_equivalence_certified=False)
def derive(root):
    root=Path(root);sources=validate_sources(root)
    cards=json.loads((root/'selected-oracle-cards.json').read_text());by_id={c['oracle_id']:c for c in cards}
    aliases=IdentityIndex(json.loads((root/'reviewed-identities.json').read_text()))
    bans=json.loads((root/'commander-banlist-snapshot.json').read_text());reports=[]
    for seat,name in enumerate(DECKS):
        path=root/'decks'/name
        report=audit_deck(path.read_text(),cards,bans,game_date='prospective-frozen-profile',snapshot_date='2026-10-23',identity_index=aliases)
        if not report['current_snapshot_rules_checks_passed']:raise ValueError('Deck failed independent construction audit: '+name+' '+canonical(report['violations']+report['evidence_gaps']))
        reports.append(dict(seat=seat,file=name,sha256=sha(path),audit=report,
                            complete_oracle_records={c['oracle_id']:by_id[c['oracle_id']] for c in report['cards']}))
    return dict(sources=sources,decks=reports,configuration=HOUSE,
                level1_legal_relative_to_frozen_snapshot=True,complete_game_certified=False,training_eligible=False)
def build(source,identities,output):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    for name in ['public-oracle-provenance.json','public-oracle-catalog.jsonl.gz','official-banlist.html','commander-banlist-snapshot.json','selected-oracle-cards.json','comprehensive-rules.txt']:
        shutil.copyfile(source/name,output/name)
    shutil.copyfile(identities,output/'reviewed-identities.json');(output/'decks').mkdir()
    for name in DECKS:shutil.copyfile(source/'frozen-decks/2026202030'/name,output/'decks'/name)
    derived=derive(output)
    files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
    manifest=dict(format=1,kind='prospective_deck_rules_binding',files=files,derived=derived,
                  historical_deck_files_unchanged=True,oracle_scope='Frozen independent public mirror, not publisher-certified; official rules and Commander ban list are bound separately')
    (output/'binding.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    return dict(binding_sha256=sha(output/'binding.json'),decks_verified=4,configuration=HOUSE,source_checks=derived['sources'])
def verify(root,expected_sha256):
    root=Path(root).resolve();p=root/'binding.json'
    if sha(p)!=expected_sha256:raise ValueError('Launch binding hash mismatch')
    m=json.loads(p.read_text())
    if m['format']!=1 or m['kind']!='prospective_deck_rules_binding':raise ValueError('Unsupported binding')
    for name,digest in m['files'].items():
        f=root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or f.is_symlink() or not f.resolve().is_relative_to(root) or sha(f)!=digest:
            raise ValueError('Changed or unsafe bound source: '+name)
    actual=derive(root)
    if actual!=m['derived']:raise ValueError('Stored audit differs from independent recomputation')
    return dict(binding_sha256=expected_sha256,decks_verified=len(actual['decks']),configuration=HOUSE,
                construction_checks_passed=True,oracle_publisher_equivalence_certified=False,full_game_rules_approved=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build');b.add_argument('--source',type=Path,required=True);b.add_argument('--identities',type=Path,required=True);b.add_argument('--output',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('root',type=Path);v.add_argument('--sha256',required=True);a=p.parse_args()
    print(json.dumps(build(a.source,a.identities,a.output) if a.mode=='build' else verify(a.root,a.sha256),indent=2))
