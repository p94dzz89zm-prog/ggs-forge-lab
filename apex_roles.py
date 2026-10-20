"""First-pass functional annotations, not measured card-strength rankings."""

# primary, secondary, dependency/tradeoff. Exact costs and rulings remain in
# the joined baseline record; no activation is implied free by these roles.
ROLES={
 'Goro-Goro and Satoru':('Dragon production','team haste','Fresh combat damage to a player; pay haste before the intended attackers need it.'),
 'Balefire Dragon':('combat board control','flying finisher','Must connect to clear that defending player\'s creatures; expensive without Satoru access.'),
 'Baleful Strix':('defensive deterrent','entry draw/evasive carrier','Flying deathtouch body can trade; ninjutsu replays draw but spends mana.'),
 'Changeling Outcast':('cheap unblockable entry','Ninja/tribal connector','Cannot block; changeling helps Ninja draw and chosen-type effects.'),
 'Dauthi Voidwalker':('opponent graveyard suppression','shadow carrier/stolen spell','Shadow seldom defends normal attackers; sacrifice loses persistent graveyard suppression.'),
 'Fallen Shinobi':('opponent card access','fresh combat payoff','Requires unblocked carrier plus ninjutsu payment; stolen spells depend on the opponent library.'),
 'Fire Navy Trebuchet':('fresh flying token factory','reach defense','An attack is required to create the temporary token; the Wall itself has defender.'),
 'Gingerbrute':('early hasty carrier','conditional evasion/emergency life','Access costs mana; three-life sacrifice consumes the carrier and is not repeatable sustain.'),
 'Goldlust Triad':('multi-opponent attack expansion','Treasure production','Myriad needs an actual attack; copies disappear at end of combat and need combat access.'),
 'Goldspan Dragon':('hasty flying pressure','Treasure acceleration','Targeting and combat can fuel mana; expensive body competes with protection reserves.'),
 'Grazilaxx, Illithid Scholar':('combat card advantage','optional blocked-attacker rescue','Needs attackers; returning and replaying bodies still costs mana.'),
 'Grim Hireling':('combat mana engine','Treasure-funded removal','Connections and Treasure supply determine value; removal costs resources and sorcery timing.'),
 'Hope of Ghirapur':('cheap flying carrier','temporary noncreature lock','Must damage the intended player, then sacrifice; cannot repeatedly protect without recovery.'),
 'Ingenious Infiltrator':('Ninja combat draw','fresh ninjutsu body','Ninjas must connect; does not draw for every non-Ninja attacker.'),
 'Kari Zev, Skyship Raider':('repeatable attacking token','early menace/first-strike body','Kari must attack legally; Ragavan token is temporary and enters already attacking.'),
 'Karlach, Fury of Avernus':('extra combat engine','first-strike combat pressure','First combat attack condition and attacker untap matter; does not supply an empty board.'),
 'Krenko, Tin Street Kingpin':('persistent token growth','board expansion/defense','Attack exposes Krenko; Goblins enter untapped but do not automatically join that combat.'),
 'Loyal Apprentice':('flying haste token factory','early body','Lieutenant requires a commander; preserving direct commander synergy is intentional.'),
 'Moon-Circuit Hacker':('cheap Ninja draw/filter','fresh combat carrier','First-turn draw differs from later filtering; replacement loses low-cost card flow.'),
 'Phoenix Chick':('cheap flying haste access','conditional graveyard return','Cannot block; returning needs three attackers and two red mana.'),
 'Port Razer':('repeatable additional combats','independent large attacker','Needs player damage and must obey its attacked-player restriction in later combats.'),
 'Professional Face-Breaker':('combat Treasure generation','Treasure-to-card access','Sacrificing Treasure for impulse access competes with using it for mana/protection.'),
 'Prosperous Thief':('Ninja/Rogue combat mana','fresh ninjutsu body','Treasure trigger requires Ninja or Rogue damage; it is not unrestricted team damage.'),
 'Purphoros, God of the Forge':('independent entry damage','wipe-resistant payoff/team pump','Creature supply is required; indestructibility does not stop exile or bounce.'),
 'Ragavan, Nimble Pilferer':('cheap combat mana','opponent card access/dash','Must connect; dash grants freshness/haste but returns the body and costs mana each use.'),
 "Sakashima's Student":('flexible copied threat','fresh ninjutsu access','Copies copiable characteristics, not live pump/equipment; chosen object and legend rule matter.'),
 'Satoru Umezawa':('large-creature ninjutsu access','once-per-turn card selection','Requires an unblocked carrier and four mana; replacing a valuable attacker can lose damage.'),
 'Satoru, the Infiltrator':('noncast-entry card advantage','early Ninja body','Qualifying entry conditions matter; ninjutsu is an ability, not a spell cast.'),
 'Terror of the Peaks':('independent creature-entry damage','flying pressure','Later creature entries are required; damage depends on their power and legal target.'),
 'Tetsuko Umezawa, Fugitive':('small-stat unblockability','defensive 1/3 body','Power OR toughness at most one; growing X/1 tokens stay eligible until toughness also increases.'),
 'Thousand-Faced Shadow':('cheap flying carrier','ninjutsu attack-copy burst','Copy trigger needs its ninjutsu entry while attacking and another attacking creature.'),
 "Yuriko, the Tiger's Shadow":('Ninja card advantage','noncombat life-loss pressure','Commander ninjutsu does not make her the commander here; GGS remains commander.'),
 'Kaito, Bane of Nightmares':('draw/filter and Ninja support','stun defense/ninjutsu entry','Draw counts opponents who lost life; minus-two may be more valuable than draw against a lethal threat.'),
 "An Offer You Can't Refuse":('cheap noncreature counter','engine protection','Gives controller two Treasures; cannot counter creature spells.'),
 'Chaos Warp':('broad permanent interaction','emergency threat removal','Random replacement can worsen the board; reserve red mana for the actual response window.'),
 'Cyclonic Rift':('instant disruption','overloaded asymmetrical reset','One target versus seven-mana overload are different roles; bounce is temporary.'),
 'Deadly Rollick':('creature exile','commander-supported free interaction','Free condition requires controlling a commander; absent GGS the normal cost matters.'),
 'Deflecting Swat':('target redirection','commander-supported protection','Requires a useful legal target change; does not counter a nontargeted wipe.'),
 'Fell the Profane':('creature/planeswalker destruction','black land option','Spell use spends a potential land; back-face timing/life cost matters.'),
 'Fierce Guardianship':('noncreature counter','commander-supported protection','Free condition requires a commander; cannot counter a creature spell.'),
 'Malakir Rebirth':('death recovery','black land option','Life payment and actual dying are required; exile/bounce do not trigger its return.'),
 'Mana Drain':('broad spell counter','next-main colorless resource','Needs two blue now; delayed colorless mana cannot pay later colored requirements.'),
 'March of Swirling Mist':('phase protection','temporary blocker/threat suppression','Targets and X/payment choices matter; phased permanents do not leave and reenter.'),
 'Sink into Stupor':('spell/permanent bounce','blue land option','Cannot target your own objects; temporary answer trades against land development.'),
 'Swan Song':('cheap selective counter','engine protection','Leaves a flying blocker; cannot counter artifact, planeswalker or creature spells just for being threatening.'),
 'Vampiric Tutor':('critical-card access','instant selection','Costs life and places card on top rather than in hand; next draw and mana remain needed.'),
 'Crux of Fate':('selective creature wipe','Dragon-preserving reset','Choose Dragons or non-Dragons; preserving Dragons may destroy GGS and carrier engines.'),
 'Demonic Tutor':('unrestricted card access','redundancy for critical roles','Two-mana sorcery does not cast the found card; avoid spending needed protection mana.'),
 'Diabolic Intent':('unrestricted card access','token-to-resource conversion','Sacrifice is an additional cost; losing the last carrier/factory may outweigh selection.'),
 'Feed the Swarm':('enchantment interaction','creature removal','Sorcery speed and life loss; valuable Grixis capability that is not casually redundant.'),
 'Vandalblast':('artifact removal','overloaded asymmetrical artifact wipe','One-mana targeted mode versus five-mana overload; neither addresses nonartifact threats.'),
 'Lightning Greaves':('haste/protection','reusable equip','Shroud also obstructs your own targeting/equip; moving it can expose the engine.'),
 'Mithril Coat':('flash legendary protection','reusable indestructible equipment','Free attachment only from its entry trigger to a legendary creature; exile remains a threat.'),
 'Skullclamp':('small-body card conversion','wipe resource recovery','Equip can kill one-toughness carriers before combat; spend expendable bodies intentionally.'),
 'Sword of Feast and Famine':('combat mana reset','protection/discard pressure','Equip and connection needed; +2/+2 can remove Tetsuko access. Land untap supports paid extra combats.'),
 "Urabrask's Forge":('persistent fresh attacker factory','growing independent pressure','Temporary trample token has one toughness; enchantment/artifact removal can still stop the factory.'),
 'Aggravated Assault':('repeatable extra combat outlet','team untap','Five-mana sorcery-speed activation requires a sustainable mana/attack plan, not just the enchantment.'),
 'Breath of Fury':('combat-chain payoff','attacker recycling','Must connect, sacrifice and reattach to another creature; loses function on an empty or locked board.'),
 'Determined Iteration':('existing-token replication','fresh hasty copy','Populate does not target and needs a creature token already present; alone it cannot rebuild from zero.'),
 'Dragon Tempest':('flying haste','Dragon-entry damage','Damage source is the entering Dragon; flying haste does not grant haste to nonflying carriers.'),
 'Frostcliff Siege':('mode-dependent draw or combat support','haste/trample/power in Temur mode','Choose one mode; do not count Jeskai draw and Temur attack support simultaneously.'),
 'Kindred Discovery':('chosen-type draw engine','entry/attack resource refill','Choose type for the actual board; five-mana setup requires bodies and protection.'),
 'War Cadence':('wide combat access','mana-tax manipulation','X and opponent available mana determine blockers; covers large Dragons unlike power-limited alternatives.'),
}
MANA={'Sol Ring','Arcane Signet','Fellwar Stone','Talisman of Creativity','Talisman of Dominance','Talisman of Indulgence'}
MULTILAYER_SUPPORT={'Baleful Strix','Changeling Outcast','Dauthi Voidwalker','Gingerbrute','Hope of Ghirapur','Phoenix Chick','Professional Face-Breaker','Prosperous Thief','Ragavan, Nimble Pilferer',"Yuriko, the Tiger's Shadow",'Chaos Warp','Cyclonic Rift','Deadly Rollick','Deflecting Swat','March of Swirling Mist','Feed the Swarm','Vandalblast','Lightning Greaves'}

def annotate(card):
 name=card['listed_name'];is_land=card['type_line'].startswith(('Land','Basic Land','Legendary Land'))
 if is_land:
  primary,secondary,dependency='mana infrastructure','printed utility/fixing where available','Exact production, entry conditions, fetch targets and channel costs are in Oracle text; physical inventory remains unreconciled.'
 elif name in MANA:
  primary,secondary,dependency='mana development','colored fixing' if name!='Sol Ring' else 'colorless acceleration','Cast cost delays other plays; colorless mana cannot pay colored pips. Fellwar Stone depends on opposing land capabilities.' if name=='Fellwar Stone' else 'Cast cost delays other plays; colorless mana cannot pay colored pips.'
 else:primary,secondary,dependency=ROLES[name]
 if name in MULTILAYER_SUPPORT:card['classification']='High-value support'
 if name=='Aggravated Assault':card['classification']='Conditional specialist'
 mana=card['mana_value']
 card['primary_function']=primary;card['secondary_function']=secondary
 card['required_support_and_constraints']=dependency
 card['defensive_contribution']='Direct defense/interaction: '+primary+'; exact restrictions above.' if any(w in (primary+' '+secondary).lower() for w in ['defen','protection','counter','removal','interaction','wipe','stun','deterrent','suppression']) else ('Funds interaction and development; no combat body.' if is_land or name in MANA else 'Creature body may defend if untapped and legally able; attack commitment can sacrifice this defense.' if 'Creature' in card['type_line'] else 'Indirect package support; no independent blocker.')
 card['recovery_contribution']='Direct recovery or persistent source: '+primary if any(w in (primary+' '+secondary).lower() for w in ['recover','graveyard','factory','wipe-resistant']) else 'Resource support or surviving targets may help recovery; this is not automatically an empty-board rebuild tool.'
 card['timing_and_stages']={'early':'Mana development or available opening utility.' if is_land or name in MANA else ('Low cast cost enables early setup; activation costs and colors still matter.' if mana<=2 else 'Usually requires prior mana development or alternative access.'),'middle':'Execute '+primary+' with the supporting constraints above.','late':'Retains '+secondary+' when its conditions hold; empty-board floor and resource cost remain material.'}
 card['opportunity_cost']='Replacing this slot sacrifices '+primary+' and '+secondary+'; compare a candidate that repairs the identified package bottleneck.'
 card['model_review_scope']='First-pass functional annotation for each listed card, not exhaustive interaction certification or measured individual strength.'
 return card
