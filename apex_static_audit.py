#!/usr/bin/env python3
"""Validate an exact baseline and scan every snapshot-eligible Grixis card.

Retrieval patterns navigate the pool; they are not performance scores. Role
judgments describe Oracle-supported functions and remain provisional.
"""
import argparse,collections,hashlib,json,math,re,sqlite3
from pathlib import Path
from research_tools import connection
from apex_roles import annotate

PATTERNS={
 'fresh_attackers':r'(?:create[^.\n]*token[^.\n]*|token[^.\n]*)(?:haste|attacking)|(?:combat|attack)[^.\n]*create',
 'haste':r'\bhaste\b',
 'combat_access':r"can't be blocked|cannot be blocked|\bfear\b|\bmenace\b|\bshadow\b|\bflying\b|\btrample\b",
 'recovery':r'(?:return|cast|copy)[^.\n]*(?:graveyard)|graveyard[^.\n]*(?:battlefield|your hand|cast)',
 'protection':r'\bhexproof\b|\bindestructible\b|\bphases? out\b|counter target spell|protection from',
 'lifegain':r'\blifelink\b|you gain[^.\n]*life',
 'card_access':r'\bdraw[^.\n]*cards?\b|look at the top|exile the top|\bsurveil\b|\bscry\b',
 'tutors':r'search your library',
 'extra_combat':r'additional combat phase|after this combat phase',
 'dragon':r'\bdragons?\b',
 'defense':r'\breach\b|\bvigilance\b|\bdeathtouch\b|attack you|damage that would be dealt to you',
 'interaction':r'destroy target|exile target|return target.*hand|counter target|sacrifice a creature|creatures get -',
 'mana':r'add \{|treasure token|untap all lands|mana of any',
 'ninjutsu':r'\bninjutsu\b',
}
FACTORIES={'Kari Zev, Skyship Raider','Loyal Apprentice','Fire Navy Trebuchet',"Urabrask's Forge",'Determined Iteration'}
SUPPORT={
 'Baleful Strix':('High-value support','B,F','Cheap draw plus flying/deathtouch defense;1 power keeps Tetsuko access; repeatable draw requires a return/recast line.'),
 'Tetsuko Umezawa, Fugitive':('Core infrastructure','A,C,D','Access for low power OR low toughness, including growing X/1 Forge tokens. No benefit for5/5 Dragons; removal exposes small attackers.'),
 'Goro-Goro and Satoru':('Core infrastructure','D,E','Central commander payoff and paid haste. Fresh creatures must actually deal combat damage; preexisting attackers alone do not qualify.'),
 'War Cadence':('High-value support','C,D,E','Paid access can cover large Dragons as well as carriers; competes for attack-turn mana and is not unconditional unblockability.'),
 'Breath of Fury':('Conditional specialist','D,E,G','Repeated combats require a connection, sacrifice and another attachment recipient. High ceiling; weak with an empty or inaccessible board.'),
 'Purphoros, God of the Forge':('Conditional specialist','D,E,G','Converts creature entries into damage without combat access, often survives creature wipes. Sacrificing it costs an independent finishing route.'),
 'Kindred Discovery':('High-value support','D,F','Type-dependent refill on entry/attack; high setup cost, rewards sustained creature production even before combat damage.'),
 'Frostcliff Siege':('High-value support','C,D,F','Jeskai mode draws once per damaged player/event; Temur mode supplies haste/trample/+1power. The mode changes its role; do not count both simultaneously.'),
 'Grim Hireling':('High-value support','B,F,G','Combat connections produce resources and Treasures can fuel targeted removal; a replacement sacrifices that interaction and mana role.'),
 'Moon-Circuit Hacker':('Flexible slot','A,D,F','Cheap ninjutsu/refill carrier; low late raw body size. A factory replacement raises cast cost and loses Ninja/card-flow capacity.'),
 'Satoru Umezawa':('High-value support','D,E,F,G','Grants4-mana ninjutsu to big threats and filters once per turn; needs unblocked attackers and substantial activation mana.'),
 'Satoru, the Infiltrator':('High-value support','D,F','Rewards qualifying noncast entries; ninjutsu is an activated ability, not a creature spell cast.'),
 'Grazilaxx, Illithid Scholar':('High-value support','C,F','Turns connections into draws and blocked attackers into optional bounce protection. Bounce/recast still costs mana.'),
 'Krenko, Tin Street Kingpin':('High-value support','B,D,E,G','Builds a board when attacking. Its new Goblins are not automatically attacking or hasty in the current combat.'),
 'Karlach, Fury of Avernus':('High-value support','D,E,G','Additional combat pressure with attackers and first-strike utility; fresh attackers must still be legal for the later combat.'),
 'Port Razer':('Conditional specialist','C,D,E,G','Extra combat requires combat damage to a player and attack restrictions matter. Retain its trigger when evaluating ninjutsu swaps.'),
 'Fire Navy Trebuchet':('High-value support','B,C,D,F','Repeatable fresh flying attacker when you attack;0/4 reach body contributes defense. The token is temporary.'),
 'Loyal Apprentice':('High-value support','B,C,D','Fresh flying Thopters while the commander is present; direct commander dependence is intended synergy, assessed with other factories as a package.'),
 'Kari Zev, Skyship Raider':('High-value support','A,B,C,D','Attack creates a fresh2/1 Monkey tapped and attacking; both Kari and token qualify for Tetsuko thresholds. Requires a legal Kari attack.'),
 "Urabrask's Forge":('High-value support','B,C,D,E,G','Persistent noncreature factory with growing X/1 haste/trample;1 toughness preserves Tetsuko access at any power.'),
 'Determined Iteration':('High-value support','B,D,E','Populate needs an existing creature token and does not target. A surviving enchantment alone cannot restart an empty board.'),
 'Dragon Tempest':('High-value support','C,D,E,G','Flying haste and Dragon-entry damage; damage source is the entering Dragon, relevant to lifelink. Needs other bodies to do work.'),
 'Sakashima\'s Student':('Conditional specialist','D,E,F','Flexible ninjutsu copy. Copiable characteristics differ from live pumps/equipment; stock copy choice still needs review.'),
}

def resolve(db,name):
 row=db.execute('SELECT * FROM cards WHERE name=?',(name,)).fetchone()
 if row is None:row=db.execute("SELECT * FROM cards WHERE substr(name,1,instr(name,' // ')-1)=?",(name,)).fetchone()
 if row is None:raise ValueError('Unresolved exact card name: '+name)
 return dict(row)

def audit(snapshot,baseline,output,engine_res=None):
 snapshot,baseline,output=map(Path,(snapshot,baseline,output));output.mkdir(parents=True,exist_ok=False)
 db=connection(snapshot);db.row_factory=sqlite3.Row
 assert db.execute('pragma quick_check').fetchone()[0]=='ok'
 raw=baseline.read_text();entries=[]
 for line in raw.splitlines():
  if not line.strip():continue
  match=re.fullmatch(r'(\d+) (.+)',line.strip())
  if not match:raise ValueError('Malformed baseline line: '+line)
  count=int(match[1]);name=match[2]
  if count<1:raise ValueError('Positive card quantities required')
  r=resolve(db,name)
  if r['legal_commander']!='legal' or not r['grixis_eligible']:raise ValueError('Commander identity/legality violation: '+name)
  entries.append({'quantity':count,'listed_name':name,**r})
 if sum(e['quantity'] for e in entries)!=100:raise ValueError('Exactly100 cards required')
 if entries[0]['listed_name']!='Goro-Goro and Satoru':raise ValueError('Expected GGS commander first')
 ids=collections.Counter()
 for e in entries:ids[e['oracle_id']]+=e['quantity']
 for e in entries:
  if ids[e['oracle_id']]>1 and 'Basic Land' not in e['type_line']:raise ValueError('Singleton violation: '+e['listed_name'])
 if any(e['listed_name'] in ('Mistblade Shinobi','Faerie Seer') for e in entries):raise ValueError('Listed reference must not silently insert a physical extra or removed card')
 definitions={}
 if engine_res:
  for path in (Path(engine_res)/'cardsfolder').rglob('*.txt'):
   text=path.read_text(errors='replace');name=next((l[5:] for l in text.splitlines() if l.startswith('Name:')),None)
   if name:definitions[name]=str(path.relative_to(engine_res))
 for e in entries:
  name=e['listed_name'];text=e['oracle_text'] or '';faces=json.loads(e['card_faces_json'] or '[]')
  e['engine_definition_present']=name in definitions;e['engine_definition_path']=definitions.get(name);e['rules_evidence']=[dict(r) for r in db.execute('SELECT source,published_at,comment FROM rulings WHERE oracle_id=?',(e['oracle_id'],))]
  if name in SUPPORT:classification,layers,note=SUPPORT[name]
  elif 'Land' in e['type_line'] and not faces:classification,layers,note='Core infrastructure','A,B,C,D,E,F,G','Mana-base slot supports the system; individual land names remain replaceable. Physical land inventory is unreconciled.'
  elif name in {'Sol Ring','Arcane Signet','Fellwar Stone','Talisman of Creativity','Talisman of Dominance','Talisman of Indulgence'}:classification,layers,note='Core infrastructure','A,B,D,E,F','Mana acceleration/fixing; preserve the resource role when replacing individual pieces.'
  elif re.search(r'counter target|protection|hexproof|indestructible|phases out',text,re.I):classification,layers,note='High-value support','F','Interaction/protection by Oracle text; available mana, timing and targeting determine whether it protects a critical engine.'
  elif 'Land' in e['type_line'] or any('Land' in f.get('type_line','') for f in faces):classification,layers,note='High-value support','A,F','Spell/land flexibility; casting the spell removes that land option and enters-tapped/life costs affect timing.'
  elif e['mana_value']>=5:classification,layers,note='Conditional specialist','D,E,G','Large threat or payoff; requires sufficient mana/access. Mana value alone is not evidence of underperformance.'
  elif re.search('draw|look at|search your library',text,re.I):classification,layers,note='High-value support','F','Card/resource access; expenditure and restrictions remain material.'
  else:classification,layers,note='Flexible slot','A,D,E,F','Useful Oracle-supported contribution; slot priority awaits a more specific dependency/experiment review.'
  e['classification']=classification;e['layers']=layers.split(',');e['role_judgment']=note;e['classification_evidence']='Oracle/rulings and described dependencies; provisional, no per-card win-rate attribution'
  e['mana_investment']={'cast':e['mana_cost'],'mana_value':e['mana_value'],'ability_costs':'See exact Oracle text; cast cost alone omits equip, activation, sacrifice and replay costs.'}
  e['performance_without_GGS']='Mana/interaction/draw works independently; commander-specific value is additional.' if name not in {'Goro-Goro and Satoru','Loyal Apprentice'} else ('Commander itself; central identity.' if name=='Goro-Goro and Satoru' else 'Thopter trigger needs a commander present; body remains, assess package resilience.')
  e['timing_and_stages']={'early':'Cast/activation requirements and opening resource support constrain execution.','middle':'Layer coverage and interactions above determine access/payoff value.','late':'Board, mana and remaining targets determine floor; no universal stage score.'}
  annotate(e)
 tags=[];counts=collections.Counter();eligible=list(db.execute('SELECT * FROM cards WHERE grixis_eligible=1 ORDER BY name'))
 for row in eligible:
  e=dict(row);text='\n'.join([e['oracle_text'] or '']+[f.get('oracle_text','') for f in json.loads(e['card_faces_json'] or '[]')])
  for role,pattern in PATTERNS.items():
   m=re.search(pattern,text,re.I)
   if m:tags.append({'oracle_id':e['oracle_id'],'name':e['name'],'role':role,'matched_text':text[max(0,m.start()-40):min(len(text),m.end()+100)],'manual_review_required':True});counts[role]+=1
 with sqlite3.connect(output/'pool-discovery.sqlite') as target:
  target.execute('CREATE TABLE retrieval_tags(oracle_id TEXT,name TEXT,role TEXT,matched_text TEXT,manual_review_required INTEGER)')
  target.executemany('INSERT INTO retrieval_tags VALUES(?,?,?,?,?)',[(t['oracle_id'],t['name'],t['role'],t['matched_text'],1) for t in tags]);target.execute('CREATE INDEX tags_role ON retrieval_tags(role)')
 lands=[e for e in entries if 'Land' in e['type_line'] and not json.loads(e['card_faces_json'] or '[]')];mdfc=[e for e in entries if any('Land' in f.get('type_line','') for f in json.loads(e['card_faces_json'] or '[]'))]
 def lowland(n):return sum(math.comb(n,k)*math.comb(99-n,7-k)/math.comb(99,7) for k in (0,1))
 def seen(n,draws=11):return 1-math.comb(99-n,draws)/math.comb(99,draws)
 facts={'cards':100,'unique_oracle_ids':len(ids),'all_resolved':True,'singleton_passed':True,'grixis_identity_passed':True,'commander_legal_in_snapshot':True,'listed_land_fronts':len(lands),'additional_spell_land_MDFCs':len(mdfc),'repeatable_factory_definition':sorted(FACTORIES),'factory_seen_in_first11_cards_baseline':seen(len(FACTORIES)),'factory_seen_in_first11_cards_plus_one':seen(len(FACTORIES)+1),'no_mulligan_probability_zero_or_one_land_front_in7':lowland(len(lands)),'no_mulligan_probability_zero_or_one_land_capable_in7':lowland(len(lands)+len(mdfc)),'probability_limits':'Exact library combinatorics,99-card library. No mulligan, casting/color/ETB timing, gameplay or win-rate inference. MDFC bounds use all or none as lands.','physical_inventory_reconciled':False,'physical_Mistblade_displaced_card':None,'physical_land_match_verified':False,'explicitly_absent':['Faerie Seer','Mistblade Shinobi'],'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'eligible_pool_scanned':len(eligible),'retrieval_tag_counts':dict(counts),'classification_counts':dict(collections.Counter(e['classification'] for e in entries)),'underperformer_verdicts':[],'legality_scope':'Snapshot identity and Commander flags only. A current official banned-list/release-availability crosscheck is external evidence, not performed by this script.'}
 (output/'baseline-cards.json').write_text(json.dumps(entries,indent=2)+'\n');(output/'audit-summary.json').write_text(json.dumps(facts,indent=2)+'\n');(output/'retrieval-patterns.json').write_text(json.dumps(PATTERNS,indent=2)+'\n')
 db.close();return facts

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('snapshot','baseline','output','engine-res'):p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();print(json.dumps(audit(a.snapshot,a.baseline,a.output,a.engine_res),indent=2))
if __name__=='__main__':main()
