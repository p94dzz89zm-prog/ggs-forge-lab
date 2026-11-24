"""Referee-only verification of frozen decks and the seat summaries used by the policy."""
from collections import Counter, defaultdict
from dataclasses import asdict
import gzip
from hashlib import file_digest
import json
from pathlib import Path
from zipfile import ZipFile
from .policy import Hand, encode


def sha(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()


def key(name):
    return name.split(' // ')[0].replace('꞉',':')


def deck_zones(path):
    result={'Commander':Counter(),'Main':Counter()}
    section=None
    for line in path.read_text().splitlines():
        if line.startswith('['):
            section=line.strip('[]')
        elif line and section in result:
            quantity,name=line.split(' ',1)
            result[section][key(name.split('|')[0])]+=int(quantity)
    if sum(map(sum,(row.values() for row in result.values()))) != 100:
        raise ValueError('Expected a four-player Commander input of 100 cards')
    return result


def card_features(card):
    """Normalize reversible physical printings through the existing Oracle identity indexer."""
    from reliability.opening.trials import features
    from scryfall_cache import card_versions
    for oid, view in card_versions(card):
        lands, early, _, _=features(view)
        yield key(view['name']), (oid,lands,early)


def prepare(snapshot, decks, plan):
    if sha(snapshot)!=plan['oracle_generation']:
        raise ValueError('Wrong Oracle generation')
    zones=[]
    for seat in plan['seats']:
        path=decks/(seat+'.dck')
        if sha(path)!=plan['deck_hashes'][path.name]:
            raise ValueError('Wrong deck input')
        zones.append(deck_zones(path))
    wanted={n for row in zones for group in row.values() for n in group}
    possibilities=defaultdict(set)
    with ZipFile(snapshot) as archive, archive.open('default_cards.jsonl.gz') as feed:
        with gzip.GzipFile(fileobj=feed) as stream:
            for line in stream:
                card=json.loads(line)
                name=key(card['name'])
                if name in wanted and card.get('legalities',{}).get('commander')=='legal':
                    for alias, facts in card_features(card):
                        if alias in wanted:
                            possibilities[alias].add(facts)
    if any(len(possibilities[n])!=1 for n in wanted):
        raise ValueError('Ambiguous or absent Oracle opening feature')
    return dict(generation=plan['oracle_generation'],deck_hashes=plan['deck_hashes'],zones=zones,
                cards={n:list(possibilities[n].pop()) for n in sorted(wanted)})


def check(rows,records,reference):
    entries=[r for r in rows if r['kind']=='opening_call']
    for seat, entry in enumerate([r for r in entries if r['hook']=='shuffle'][:4]):
        player=entry['state']['players'][seat]
        actual={'Main':Counter(key(c['name']) for c in player['Library']),
                'Commander':Counter(key(c['name']) for c in player['Command'] if c['commander'])}
        if actual!=reference['zones'][seat]:
            raise ValueError('Native initial physical deck differs from selected deck')
    for entry,record in zip([r for r in entries if r['hook']=='mulligan_decision'],records,strict=True):
        seat=entry['player_id']
        p=entry['state']['players'][seat]
        cards=reference['cards']
        own=[cards[key(c['name'])] for c in p['Hand']]
        cheap=any(cards[key(c['name'])][2] for c in p['Command'] if c['commander'])
        observed=asdict(Hand(sum(c[1] for c in own),sum(c[2] for c in own),cheap))
        if record['seat']!=seat or observed!=record['observation']:
            raise ValueError('Pilot projection differs from Oracle-bound actor hand')
    return len(records)


if __name__=='__main__':
    import sys
    snapshot,decks,plan,out=map(Path,sys.argv[1:])
    value=prepare(snapshot,decks,json.loads(plan.read_text()))
    with out.open('x') as f: f.write(encode(value)+'\n')
