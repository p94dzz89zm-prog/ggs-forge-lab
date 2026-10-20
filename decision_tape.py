"""Extract private root controller choices without dropping unsupported decisions.

Input must be an already sealed referee tape, pinned by its archived SHA256.
This checks extraction structure, not rules legality or admission to learning.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile

CONTROLLERS = ('forge/ai/PlayerControllerAi.', 'forge/ai/bridge/PlayerControllerBridge.',
               'forge/game/player/PlayerController.')
NUMBER = '.chooseNumber(Lforge/game/spellability/SpellAbility;Ljava/lang/String;II)I'
CARDS = '.chooseCardsForEffect(Lforge/game/card/CardCollectionView;Lforge/game/spellability/SpellAbility;Ljava/lang/String;IIZLjava/util/Map;)Lforge/game/card/CardCollectionView;'
PRIORITY = '.chooseSpellAbilityToPlay()Ljava/util/List;'
REPLACEMENT = '.chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;'
COUNTER = '.chooseCounterType(Ljava/util/List;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Ljava/util/Map;)Lforge/game/card/CounterType;'
COLORS = '.chooseColors(Ljava/lang/String;Lforge/game/spellability/SpellAbility;IILforge/card/ColorSet;)Lforge/card/ColorSet;'
START = '.chooseStartingPlayer(Z)Lforge/game/player/Player;'
MULLIGAN = '.mulliganKeepHand(Lforge/game/player/Player;I)Z'
PAYMENT = '.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z'
TRIGGER_STACK = '.orderAndPlaySimultaneousSa(Ljava/util/List;)V'
SINGLE_PLAYER = '.chooseSingleEntityForEffect(Lforge/util/collect/FCollectionView;Lforge/game/player/DelayedReveal;Lforge/game/spellability/SpellAbility;Ljava/lang/String;ZLforge/game/player/Player;Ljava/util/Map;)Lforge/game/GameEntity;'
ATTACK = '.declareAttackers(Lforge/game/player/Player;Lforge/game/combat/Combat;)V'
ZONE_EMPTY = '.chooseSingleCardForZoneChange(Lforge/game/zone/ZoneType;Ljava/util/List;Lforge/game/spellability/SpellAbility;Lforge/game/card/CardCollection;Lforge/game/player/DelayedReveal;Ljava/lang/String;ZLforge/game/player/Player;)Lforge/game/card/Card;'
CONFIRM_ACTION = '.confirmAction(Lforge/game/spellability/SpellAbility;Lforge/game/player/PlayerActionConfirmMode;Ljava/lang/String;Ljava/util/Map;)Z'
PRIORITY_PHASES = {'UPKEEP', 'DRAW', 'MAIN1', 'COMBAT_BEGIN', 'COMBAT_DECLARE_ATTACKERS',
                   'COMBAT_DECLARE_BLOCKERS', 'COMBAT_FIRST_STRIKE_DAMAGE', 'COMBAT_DAMAGE',
                   'COMBAT_END', 'MAIN2', 'END_OF_TURN'}


RAMPANT_PARAMETERS = dict(Origin='Library',ChangeTypeDesc='basic land',Destination='Battlefield',ChangeType='Land.Basic',SpellDescription='Search your library for a basic land card, put that card onto the battlefield tapped, then shuffle.',ChangeNum='1',SP='ChangeZone',Tapped='True',StackDescription='Search your library for a basic land card, put that card onto the battlefield tapped, then shuffle.')


SWAN_PARAMETERS = dict(SpellDescription='Counter target enchantment, instant or sorcery spell. Its controller creates a 2/2 blue Bird creature token with flying.',TargetType='Spell',ValidTgts='Enchantment,Instant,Sorcery',SubAbility='DBToken',TgtPrompt='Select target enchantment, instant or sorcery spell',SP='Counter')


def swan(ability):
    return ability.get('api')=='Counter' and ability.get('source',{}).get('name')=='Swan Song' and ability.get('parameters')==SWAN_PARAMETERS


def counter_target(entry,ability):
    hints=entry.get('replay_counter_announcements',{}).get(str(ability['source']['card_id'])+':'+str(ability['ability_id']),[])
    return hints[0] if len(hints)==1 else None


def rampant(ability):
    return ability.get('api')=='ChangeZone' and ability.get('source',{}).get('name')=='Rampant Growth' and ability.get('parameters')==RAMPANT_PARAMETERS


def choice(hook):
    return hook.startswith(CONTROLLERS) and not any('.' + name + '(' in hook for name in ('reveal', 'tempShowCards', 'endTempShowCards'))


def trait_identity(value):
    return {'trait_type': value['trait_type'], 'source_card_id': value['source']['card_id'],
            'parameters': value['parameters']}


def trigger_cost_boundary(entry, row):
    """Recognize actual offered-trigger adjustment, not forecast mana probes."""
    offered=entry.get('arguments',[[]])[0]
    args=row.get('arguments',[])
    if len(offered)!=1 or len(args)!=3 or args[2] is not False:
        return False
    original=offered[0];ability=args[1]
    return (isinstance(ability,dict) and ability.get('ability_id')==original.get('ability_id')
            and ability.get('source',{}).get('card_id')==original.get('source',{}).get('card_id')
            and args[0]==original.get('pay_costs')=='{0}')

def encode(entry, returned, index, call_line, return_line):
    hook, args = entry['hook'], entry['arguments']
    row = {'kind': 'unsupported_decision', 'index': index, 'hook': hook,
           'actor_id': entry['receiver'].get('player_id'), 'source_call_id': entry['call_id'],
           'source_call_record': call_line, 'source_return_record': return_line}
    if hook.endswith(ATTACK):
        row['reason']='attack_costs_banding_or_declaration_unsupported'
        after=returned.get('arguments_after',[])
        if len(args)==2 and len(after)==2 and args[0]==after[0] and args[1]['attacks']==[] and returned['result'] is None and entry.get('replay_attack_unknown_calls',0)==0:
            attacks=after[1]['attacks']
            if len(attacks)==1 and after[1]['attacking_player']==args[1]['attacking_player']==args[0] and args[0]['player_id']==row['actor_id']:
                attack=attacks[0]; card=attack['attacker']; defender=attack['defender']
                if (card['name']=='Phoenix Chick' and card['controller_id']==row['actor_id'] and card['zone']=='Battlefield' and not card['tapped'] and not card['phased_out'] and attack['blockers']==[] and attack['blocked'] is False
                    and type(defender.get('player_id')) is int and defender['player_id']!=row['actor_id'] and defender['lost'] is False):
                    row.update(kind='decision',decision_type='single_phoenix_attack',attacker_id=card['card_id'],defender_player_id=defender['player_id'],
                               context={k:entry[k] for k in ('turn','phase','turn_player_id')},random_scope='Reviewed attack-selector only; no effect calls; live attack costs rejected')
                    row.pop('reason',None)
        return row
    if hook.endswith(ZONE_EMPTY):
        row['reason']='hidden_search_domain_reveal_or_choice_unsupported'
        if len(args)==8 and args==returned.get('arguments_after') and returned['result'] is None and args[0:2]==['Hand',['Library']] and args[3]==[] and args[6] is True and entry.get('replay_hidden_random_requests',0)==0:
            ability=args[2]; reveal=args[4]; chooser=args[7]
            name=ability['source']['name']
            partner='Card.namedSam; Loyal Attendant' if name=='Frodo, Adventurous Hobbit' else 'Card.namedFrodo; Adventurous Hobbit'
            parameters=dict(DB='ChangeZone',Origin='Library',Destination='Hand',Chooser='Targeted',Optional='True',ChangeType=partner,ValidTgts='Player',Hidden='True')
            if (name in ('Frodo, Adventurous Hobbit','Sam, Loyal Attendant') and ability['api']=='ChangeZone' and ability['parameters']==parameters and isinstance(reveal,dict) and reveal['zones']==['Library']
                and reveal['owner']['view_id']==chooser['player_id']==row['actor_id'] and chooser['lost'] is False
                and all(c['zone']=='Library' and c['owner']['view_id']==row['actor_id'] for c in reveal['cards'])):
                ids=[c['view_id'] for c in reveal['cards']]
                if len(ids)==len(set(ids)):
                    row.update(kind='decision',decision_type='empty_partner_search',source_ability=str(ability['source']['card_id'])+':'+str(ability['ability_id']),ability_api=ability['api'],ability_parameters=parameters,
                               reveal_card_ids=ids,reveal_owner_id=row['actor_id'],reveal_message=reveal['message'],title=args[5],selected_card_id=None,recorded_random_requests=0)
                    row.pop('reason',None)
        return row
    if hook.endswith(CONFIRM_ACTION):
        row['reason']='confirmation_context_or_mutation_unsupported'
        if len(args)==4 and args==returned.get('arguments_after') and args[3] is None and isinstance(args[0],dict) and isinstance(args[1],str) and isinstance(args[2],str) and type(returned['result']) is bool:
            ability=args[0]
            row.update(kind='decision',decision_type='confirm_action',source_ability=str(ability['source']['card_id'])+':'+str(ability['ability_id']),
                       ability_api=ability['api'],ability_parameters=ability['parameters'],mode=args[1],title=args[2],accept=returned['result'])
            row.pop('reason',None)
        return row
    if hook.endswith(SINGLE_PLAYER):
        row['reason'] = 'entity_domain_reveal_or_context_unsupported'
        if len(args) == 7 and args == returned.get('arguments_after') and args[1] is None and args[5:] == [None,None] and type(args[4]) is bool:
            offered = args[0]; selected = returned['result']
            if offered and all(isinstance(p,dict) and type(p.get('player_id')) is int and p.get('lost') is False for p in offered):
                ids = [p['player_id'] for p in offered]
                chosen = None if selected is None else selected.get('player_id')
                if len(ids) == len(set(ids)) and (chosen in ids or (selected is None and args[4])):
                    ability=args[2]
                    row.update(kind='decision',decision_type='single_player_effect',available_player_ids=ids,selected_player_id=chosen,
                               source_ability=str(ability['source']['card_id'])+':'+str(ability['ability_id']),ability_api=ability['api'],
                               ability_parameters=ability['parameters'],title=args[3],optional=args[4])
                    row.pop('reason',None)
        return row
    if hook.endswith(TRIGGER_STACK):
        row['reason'] = 'trigger_preparation_or_targets_unsupported'
        offered = args[0] if len(args) == 1 else []
        announcements = entry.get('replay_trigger_announcements', [])
        if len(offered) == 1 and len(announcements) == 1 and entry.get('replay_trigger_order') == offered and entry.get('replay_trigger_unknown_rng', 0) == 0 and entry.get('replay_trigger_effect_calls', 0) == 0:
            ability = offered[0]; source = ability['source']; event = announcements[0]; stack = event['si']
            targets = stack.get('target_players', [])
            if (source['name'] in ('Frodo, Adventurous Hobbit', 'Sam, Loyal Attendant') and ability['api'] == 'ChangeZone'
                and ability['trigger'] is True and ability['spell'] is False and ability['x'] is None and ability['pay_costs'] == '{0}'
                and ability['targets'] == [] and ability['paying_mana'] == [] and ability['alternative_costs'] == [] and ability['optional_costs'] == []
                and event['sa']['ability_id'] == ability['ability_id'] and stack['source']['view_id'] == source['card_id']
                and stack['activating_player']['view_id'] == row['actor_id'] and not stack['target_cards'] and len(targets) == 1
                and returned['arguments_after'] == args and returned['result'] is None
                and entry.get('replay_trigger_zero_payments') == 1):
                row.update(kind='decision', decision_type='partner_trigger_stack', source_card_id=source['card_id'], source_name=source['name'],
                           original_ability_id=ability['ability_id'], selected_api='ChangeZone', target_player_ids=[t['view_id'] for t in targets],
                           target_provenance='Original public GameEventSpellAbilityCast stack announcement; apply choices to live underlying ability',
                           random_scope='Partner target selector before actual zero-cost stack payment; actual effect scopes excluded',
                           context={k:entry[k] for k in ('turn','phase','priority_player_id','turn_player_id')})
                row.pop('reason', None)
        return row
    if hook.endswith(PRIORITY):
        if args != [] or returned.get('arguments_after') != []:
            row['reason'] = 'priority_argument_mutation'
        elif returned['result'] is not None and returned['result'] != []:
            selected = returned['result']
            if isinstance(selected, list) and len(selected) == 1:
                ability = selected[0]; source = ability.get('source', {})
                target=counter_target(entry,ability) if swan(ability) else None
                if (target and ability.get('spell') is True and ability.get('activated') is False and ability.get('trigger') is False and ability.get('x') is None
                    and ability.get('targets')==[] and ability.get('paying_mana')==[] and ability.get('alternative_costs')==[] and ability.get('optional_costs')==[]
                    and source.get('zone')=='Hand' and source.get('owner_id')==row['actor_id'] and entry.get('priority_player_id')==row['actor_id']):
                    row.update(kind='decision',decision_type='swan_song_spell',source_card_id=source['card_id'],source_name=source['name'],selected_api='Counter',mana_cost=source['mana_cost'],original_ability_id=ability['ability_id'],ability_parameters=ability['parameters'],
                               target_spell_card_id=target['card_id'],target_spell_name=target['name'],target_provenance=target,context={k:entry[k] for k in ('turn','phase','priority_player_id','turn_player_id')})
                    return row
                if (((ability.get('api') in ('PermanentCreature', 'PermanentNoncreature') and ability.get('parameters') == {}) or rampant(ability) or (swan(ability) and counter_target(entry,ability)))
                    and ability.get('spell') is True and ability.get('activated') is False and ability.get('trigger') is False
                    and ability.get('x') is None and ability.get('targets') == [] and ability.get('paying_mana') == []
                    and ability.get('alternative_costs') == [] and ability.get('optional_costs') == []
                    and (source.get('zone') == 'Hand' or (source.get('zone') == 'Command' and source.get('commander') is True and type(ability.get('prior_commander_casts')) is int and ability['prior_commander_casts'] >= 0)) and source.get('owner_id') == row['actor_id']
                    and entry.get('priority_player_id') == row['actor_id'] == entry.get('turn_player_id')
                    and entry.get('phase') in ('MAIN1', 'MAIN2') and 'X' not in source.get('mana_cost', 'X')):
                    row.update(kind='decision', decision_type='rampant_growth_spell' if rampant(ability) else 'command_permanent_spell' if source['zone'] == 'Command' else 'plain_hand_permanent_spell',
                               source_card_id=source['card_id'], source_name=source['name'],
                               selected_api=ability['api'], mana_cost=source['mana_cost'],
                               original_ability_id=ability['ability_id'],
                               context={key: entry[key] for key in ('turn', 'phase', 'priority_player_id', 'turn_player_id')})
                    if rampant(ability):
                        row['ability_parameters']=ability['parameters']
                    if source['zone'] == 'Command':
                        row.update(prior_commander_casts=ability['prior_commander_casts'], commander_tax=2*ability['prior_commander_casts'])
                    return row
                if (ability.get('api') == 'null' and ability.get('parameters') == {} and ability.get('pay_costs') == 'no cost'
                    and ability.get('spell') is False and ability.get('activated') is False and ability.get('trigger') is False
                    and ability.get('x') is None and ability.get('targets') == [] and ability.get('paying_mana') == []
                    and ability.get('alternative_costs') == [] and ability.get('optional_costs') == []
                    and source.get('zone') == 'Hand' and source.get('owner_id') == row['actor_id']
                    and entry.get('priority_player_id') == row['actor_id'] == entry.get('turn_player_id')
                    and entry.get('phase') in ('MAIN1', 'MAIN2')):
                    row.update(kind='decision', decision_type='play_land', land_card_id=source['card_id'],
                               land_name=source['name'], land_owner_id=source['owner_id'],
                               ability_identity_basis='live hand land special action; ephemeral ability ID is not object identity',
                               context={key: entry[key] for key in ('turn', 'phase', 'priority_player_id', 'turn_player_id')})
                    return row
            row['reason'] = 'selected_ability_requires_choices_and_mutations'
        elif entry.get('priority_player_id') != row['actor_id'] or entry['receiver'].get('lost') is not False or entry.get('phase') not in PRIORITY_PHASES:
            row['reason'] = 'priority_entitlement_or_phase_unverified'
        elif entry.get('mana_context', {}).get('pool') != []:
            pool = entry.get('mana_context', {}).get('pool')
            if isinstance(pool, list) and all(m.get('snow') is False and m.get('restricted') is False for m in pool):
                row.update(kind='decision', decision_type='priority_pass',
                           pass_return='null' if returned['result'] is None else 'empty_list', empty_mana_pool=False,
                           expected_pool=[{k: m[k] for k in ('color', 'source_card_id', 'snow', 'restricted')} for m in pool],
                           context={key: entry[key] for key in ('turn', 'phase', 'priority_player_id', 'turn_player_id')},
                           visibility_requirement='Replay emits public pool announcement; original announcement remains a separate audit obligation')
            else:
                row['reason'] = 'restricted_or_unrecorded_mana_pool'
        else:
            row.update(kind='decision', decision_type='priority_pass',
                       pass_return='null' if returned['result'] is None else 'empty_list',
                       empty_mana_pool=True,
                       context={key: entry[key] for key in ('turn', 'phase', 'priority_player_id', 'turn_player_id')})
        return row
    if hook.endswith(PAYMENT):
        row['reason'] = 'payment_requires_actual_resource_choices'
        operations = entry.get('replay_payment_operations', [])
        if len(args) == 5 and args[2:] == [None, None, False] and returned['result'] is True and operations:
            ability = args[1]; after = returned['arguments_after'][1]
            before_without_mana = {k: v for k, v in ability.items() if k != 'paying_mana'}
            after_without_mana = {k: v for k, v in after.items() if k != 'paying_mana'}
            activations = [step for step in operations if step['op'] == 'activate_basic']
            spent = [step['mana'] for step in operations if step['op'] == 'spend' and step.get('expected_success', True)]
            ids = [step['card_id'] for step in activations]
            capacity = Counter({step['card_id']: {'1': 1, '2': 2}.get(step.get('parameters', {}).get('Amount', '1'), 0) for step in activations})
            spending = Counter(m['source_card_id'] for m in spent)
            if (((ability.get('api') in ('PermanentCreature', 'PermanentNoncreature') and ability.get('parameters') == {}) or rampant(ability) or (swan(ability) and counter_target(entry,ability)))
                and ability.get('spell') is True and ability.get('x') is None and ability.get('targets') == []
                and ability.get('paying_mana') == [] and ability.get('alternative_costs') == [] and ability.get('optional_costs') == []
                and (ability['source'].get('commander') is False or (ability['source'].get('commander') is True and type(ability.get('prior_commander_casts')) is int and ability['prior_commander_casts'] >= 0)) and ability['source'].get('zone') == 'Stack'
                and 'X' not in args[0] and args[0] != '{0}' and before_without_mana == after_without_mana
                and entry.get('mana_context', {}).get('pool') == [] and entry.get('replay_payment_unknown_random_requests', 0) == 0
                and len(ids) == len(set(ids)) and ids and spent and not (spending - capacity) and all(step.get('valid') is True for step in activations)
                and spent == after.get('paying_mana') and all(m['source_card_id'] in ids and not m['snow'] and not m['restricted'] for m in spent)):
                row.update(kind='decision', decision_type='selected_tap_mana' if ability['source'].get('commander') or any(step.get('card_name') in ('Command Tower', 'Brushland') for step in activations) else 'fixed_tap_mana' if any(step.get('card_name') == 'Sol Ring' for step in activations) else 'basic_land_mana', component=args[0],
                           source_ability=str(ability['source']['card_id'])+':'+str(ability['ability_id']),
                           ability_api=ability['api'], operations=operations,
                           recorded_random_requests=entry.get('replay_payment_random_requests', 0),
                           random_scope='ComputerUtilMana selector only; actual effect scopes excluded',
                           payment_basis='Recorded tap-payment decisions and individual attempted mana-spending arguments; execute actual engine actions')
                row.pop('reason', None)
                if rampant(ability) or swan(ability):
                    row['ability_parameters']=ability['parameters']
                if swan(ability):
                    target=counter_target(entry,ability);row.update(target_spell_card_id=target['card_id'],target_spell_name=target['name'],target_provenance=target)
                row['commander'] = ability['source'].get('commander')
                if row['commander']:
                    row.update(prior_commander_casts=ability['prior_commander_casts'], commander_tax=2*ability['prior_commander_casts'])
                row['adjusted_cost'] = entry.get('replay_payment_adjusted_cost')
                for step in activations:
                    if step.get('parameters', {}).get('Produced', '').startswith('Combo '):
                        color = step.get('color_choice')
                        if not color or color.get('selected_color') not in ('W', 'U', 'B', 'R', 'G'):
                            row.update(kind='unsupported_decision', reason='missing_selected_mana_color')
                return row
        if len(args) == 5 and args == returned.get('arguments_after'):
            ability = args[1]
            if (args[0] == '{0}' and args[2] is None and args[3] is None and args[4] is True
                and returned['result'] is True and ability.get('pay_costs') == '{0}'
                and ability.get('x') is None and ability.get('paying_mana') == []
                and not ability.get('alternative_costs') and not ability.get('optional_costs')
                and 'Announce' not in ability.get('parameters', {})):
                row.update(kind='decision', decision_type='zero_effect_mana',
                           source_ability=str(ability['source']['card_id']) + ':' + str(ability['ability_id']),
                           ability_api=ability['api'], ability_parameters=ability['parameters'],
                           payment_choice='pay', effect=True, component='{0}',
                           adjustment_requirement='live zero component and zero-only ability cost; reject X, waterbend and announce')
                row.pop('reason', None)
        return row
    if hook.endswith((START, MULLIGAN)):
        try:
            if args != returned.get('arguments_after') or entry.get('turn') != 0 or entry.get('phase') != 'null':
                raise ValueError('pregame_context_or_arguments_diverged')
            if hook.endswith(START):
                eligible = entry.get('replay_initial_player_ids', [])
                selected = returned['result']['player_id']
                if type(args[0]) is not bool or selected not in eligible or returned['result'].get('lost') is not False:
                    raise ValueError('starting_player_domain_unverified')
                row.update(kind='decision', decision_type='starting_player', first_game=args[0], eligible_player_ids=eligible, selected_player_id=selected)
            else:
                if type(args[0].get('player_id')) is not int or type(args[1]) is not int or args[1] < 0 or type(returned['result']) is not bool:
                    raise ValueError('invalid_mulligan_prompt_or_choice')
                row.update(kind='decision', decision_type='mulligan_keep', starting_player_id=args[0]['player_id'], mulligan_count=args[1], keep=returned['result'])
        except (KeyError, TypeError, ValueError) as error:
            row['reason'] = str(error)
        return row
    if hook.endswith((REPLACEMENT, COUNTER, COLORS)):
        try:
            if args != returned.get('arguments_after'):
                raise ValueError('effect_choice_argument_mutation')
            if hook.endswith(REPLACEMENT):
                offered = [trait_identity(item) for item in args[0]]
                selected = trait_identity(returned['result'])
                if len({json.dumps(item, sort_keys=True) for item in offered}) != len(offered) or selected not in offered:
                    raise ValueError('ambiguous_or_unoffered_replacement')
                row.update(kind='decision', decision_type='replacement_choice', available_effects=offered, selected_effect=selected)
            else:
                ability = args[1]
                row['source_ability'] = None if ability is None else str(ability['source']['card_id']) + ':' + str(ability['ability_id'])
                if hook.endswith(COUNTER):
                    offered, selected = args[0], returned['result']
                    if not all(type(item) is str for item in offered) or type(selected) is not str or len(set(offered)) != len(offered) or selected not in offered:
                        raise ValueError('unoffered_or_ambiguous_counter')
                    if not isinstance(args[3], dict) or any(value is not None for value in args[3].values()):
                        raise ValueError('non_null_counter_parameters_need_binding')
                    row.update(kind='decision', decision_type='counter_choice', title=args[2], available_counters=offered, selected_counter=selected, null_parameter_keys=sorted(args[3]))
                else:
                    allowed, selected = args[4], returned['result']
                    if not all(type(text) is str and text and set(text) <= set('WUBRGC') and len(text) == len(set(text)) for text in (allowed, selected)):
                        raise ValueError('unencoded_color_set')
                    min_, max_ = args[2:4]; colors = set(selected) - {'C'}
                    if type(min_) is not int or type(max_) is not int or not min_ <= len(colors) <= max_ or not colors <= set(allowed):
                        raise ValueError('illegal_color_choice')
                    row.update(kind='decision', decision_type='color_choice', title=args[0], min=min_, max=max_, allowed_colors=allowed, selected_colors=selected)
        except (KeyError, TypeError, ValueError) as error:
            row['kind'] = 'unsupported_decision'; row['reason'] = str(error)
        return row
    if not (hook.endswith(NUMBER) or hook.endswith(CARDS)):
        row['reason'] = 'unsupported_hook'
        return row
    if args != returned.get('arguments_after'):
        row['reason'] = 'recorded_argument_mutation_requires_driver_support'
        return row
    try:
        offset = 0 if hook.endswith(NUMBER) else 1
        ability = args[offset]
        binding = None if ability is None else str(ability['source']['card_id']) + ':' + str(ability['ability_id'])
        row.update(source_ability=binding, title=args[offset + 1], min=args[offset + 2], max=args[offset + 3])
        if type(row['min']) is not int or type(row['max']) is not int or type(row['title']) is not str or type(row['actor_id']) is not int:
            raise ValueError('Unencoded prompt/bounds/controller')
        if hook.endswith(NUMBER):
            n = returned['result']
            if type(n) is not int or not row['min'] <= n <= row['max']:
                raise ValueError('Illegal recorded number')
            row['number'] = n
        else:
            available = [c['card_id'] for c in args[0]]
            selected = [c['card_id'] for c in returned['result']]
            optional = args[5]
            if type(optional) is not bool or any(type(c) is not int for c in available + selected):
                raise ValueError('Unencoded card choice')
            if len(set(available)) != len(available) or len(set(selected)) != len(selected) or not set(selected) <= set(available):
                raise ValueError('Invalid or duplicate card choice')
            if len(selected) > row['max'] or (len(selected) < row['min'] and not (optional and not selected)):
                raise ValueError('Illegal recorded card count')
            row.update(available_card_ids=available, selected_card_ids=selected, optional=optional)
        row['kind'] = 'decision'
    except (KeyError, TypeError, ValueError) as error:
        row['reason'] = str(error)
    return row


def extract(source, expected_sha256, output):
    output = Path(output)
    checksum, stack, roots = hashlib.sha256(), [], {}
    count, calls, initial, terminal, records = 0, 0, 0, False, 0
    initial_players = []
    # Registered identities are immutable pregame input, not copied outcomes.
    # Forge emits GameStarted after its first pregame controller choices.
    with Path(source).open('rb') as header:
        for raw in header:
            candidate = json.loads(raw)
            if 'initial_state' in candidate:
                initial_players = [p['id'] for p in candidate['initial_state'].get('players', []) if p['active'] and not p['lost']]
                break
    counter_announcements = {}
    with Path(source).open('rb') as announcements:
        for record,raw in enumerate(announcements,1):
            item=json.loads(raw)
            if item.get('kind')!='engine_call' or not item.get('hook','').startswith('forge/game/Game.fireEvent('):continue
            event=item['arguments'][0]
            if not isinstance(event,dict) or event.get('record_type')!='GameEventSpellAbilityCast':continue
            ability=event['sa'];stack_item=event['si']
            if ability['source']['name']!='Swan Song':continue
            match=re.fullmatch(r'Swan Song \((\d+)\) - Counter Rampant Growth \((\d+)\)\. ',stack_item['text'])
            if not match or int(match[1])!=ability['source']['view_id'] or stack_item['target_cards'] or stack_item['target_players']:continue
            key=str(ability['source']['view_id'])+':'+str(ability['ability_id'])
            counter_announcements.setdefault(key,[]).append(dict(card_id=int(match[2]),name='Rampant Growth',source_record=record,basis='Public original GameEventSpellAbilityCast stack announcement; no resolution outcomes used'))
    supported, unsupported = Counter(), Counter()
    fd, temporary = tempfile.mkstemp(dir=output.parent, prefix='.decision-extract-')
    try:
        with os.fdopen(fd, 'w') as result, Path(source).open('rb') as stream:
            for records, line in enumerate(stream, 1):
                checksum.update(line); row = json.loads(line)
                if terminal or row.get('format') != 1 or row.get('audience') != 'offline_referee_only':
                    raise ValueError('Invalid/late referee record')
                kind = row['kind']
                if kind == 'engine_call':
                    calls += 1
                    if row['call_id'] != calls or row.get('parent_call_id', 0) != (stack[-1][0] if stack else 0):
                        raise ValueError('Call sequence/parent gap')
                    is_choice = choice(row['hook'])
                    if is_choice and not row.get('speculative', False) and not any(item[1] for item in stack):
                        row['replay_counter_announcements']=counter_announcements
                        roots[row['call_id']] = (row, records)
                    stack.append((row['call_id'], is_choice, row['hook']))
                    initial += 'initial_state' in row
                    if 'initial_state' in row:
                        observed_players = [p['id'] for p in row['initial_state'].get('players', []) if p['active'] and not p['lost']]
                        if observed_players != initial_players:
                            raise ValueError('Initial registered-player identities changed during extraction')
                    if row['call_id'] in roots and row['hook'].endswith(START):
                        row['replay_initial_player_ids'] = initial_players
                    for entry, _ in roots.values():
                        if entry['hook'].endswith(ATTACK) and not (row['hook'].endswith(ATTACK) or row['hook'].startswith('forge/game/cost/CostAdjustment.adjust(')):
                            entry['replay_attack_unknown_calls']=entry.get('replay_attack_unknown_calls',0)+1
                        if entry['hook'].endswith(TRIGGER_STACK):
                            # AI threat forecasting inspects unrelated mana costs.
                            # Only the offered trigger's own adjustment starts the
                            # actual zero-cost stack-payment boundary. In particular,
                            # a tapped Command Tower probe is not a payment/effect.
                            if row['hook'].startswith('forge/game/cost/CostAdjustment.adjust(') and trigger_cost_boundary(entry,row):
                                entry['replay_trigger_effects_started'] = True
                            if row['hook'].startswith('forge/game/ability/effects/'):
                                entry['replay_trigger_effect_calls'] = entry.get('replay_trigger_effect_calls',0)+1
                            if row['hook'].startswith('forge/game/Game.fireEvent('):
                                event = row['arguments'][0]
                                if isinstance(event, dict) and event.get('record_type') == 'GameEventSpellAbilityCast':
                                    entry.setdefault('replay_trigger_announcements', []).append(event)
                        if not entry['hook'].endswith(PAYMENT) or row.get('speculative', False):
                            continue
                        if row['hook'].startswith('forge/game/cost/CostTap.payAsDecided('):
                            payer, payment, ability, effect = row['arguments']; source = ability['source']; params = ability['parameters']
                            entry.setdefault('replay_payment_operations', []).append(dict(op='activate_basic',
                                card_id=source['card_id'], card_name=source['name'], parameters=params,
                                valid=(source['name'] in ('Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes', 'Sol Ring', 'Command Tower', 'Brushland')
                                       and ability['api'] == 'Mana' and (params.get('Produced') in ('W', 'U', 'B', 'R', 'G', 'C') or (source['name'] == 'Command Tower' and params.get('Produced') == 'Combo ColorIdentity') or (source['name'] == 'Brushland' and params.get('Produced') == 'Combo G W'))
                                       and params.get('Amount', '1') in ('1', '2')
                                       and effect is False and ability['pay_costs'] == '{T}' and source['controller_id'] == payer['player_id'] == entry['receiver']['player_id']
                                       and payment == dict(count=0, type=None, cards=[], mana=None, players=None, abilities=None))))
                        elif row['hook'].startswith('forge/game/mana/ManaPool.tryPayCostWithMana(') and row['arguments'][3] is False:
                            entry.setdefault('replay_payment_adjusted_cost', row['arguments'][1])
                            entry.setdefault('replay_payment_operations', []).append(dict(op='spend', mana=row['arguments'][2], source_call_id=row['call_id']))
                        elif row['hook'].endswith('.chooseColor(Ljava/lang/String;Lforge/game/spellability/SpellAbility;Lforge/card/ColorSet;)B'):
                            title, ability, offered = row['arguments']
                            for operation in entry.get('replay_payment_operations', []):
                                if operation.get('op') == 'activate_basic' and operation['card_id'] == ability['source']['card_id']:
                                    operation['color_choice'] = dict(call_id=row['call_id'], hook=row['hook'], title=title, offered=offered)
                elif kind == 'engine_return':
                    if not stack or (row['call_id'], row['hook']) != (stack[-1][0], stack[-1][2]):
                        raise ValueError('Unpaired/out-of-order return')
                    stack.pop()
                    for entry, _ in roots.values():
                        if entry['hook'].endswith(TRIGGER_STACK):
                            if row['hook'].endswith('.orderSimultaneousSa(Ljava/util/List;)Ljava/util/List;'):
                                entry['replay_trigger_order'] = row['result']
                            if row['hook'].startswith('forge/game/player/PlayerController.payManaCost(') and row['arguments_after'][0] == '{0}' and row['arguments_after'][2:] == [None,None,False] and row['result'] is True:
                                entry['replay_trigger_zero_payments'] = entry.get('replay_trigger_zero_payments',0)+1
                        if entry['hook'].endswith(PAYMENT):
                            for operation in entry.get('replay_payment_operations', []):
                                if operation.get('source_call_id') == row['call_id']:
                                    operation['expected_success'] = row['result']
                                if operation.get('color_choice', {}).get('call_id') == row['call_id']:
                                    operation['color_choice'].update(selected_mask=row['result'], selected_color={1:'W',2:'U',4:'B',8:'R',16:'G'}.get(row['result']))
                    if row['call_id'] in roots:
                        entry, start = roots.pop(row['call_id']); decision = encode(entry, row, count, start, records)
                        (supported if decision['kind'] == 'decision' else unsupported)[decision['hook']] += 1
                        result.write(json.dumps(decision, separators=(',', ':')) + '\n'); count += 1
                elif kind == 'engine_tape_complete':
                    if stack or row['calls'] != calls:
                        raise ValueError('Incomplete calls at completion')
                    terminal = True
                elif kind == 'random_bits':
                    for entry, _ in roots.values():
                        if entry['hook'].endswith(ZONE_EMPTY):
                            entry['replay_hidden_random_requests']=entry.get('replay_hidden_random_requests',0)+1
                    for entry, _ in roots.values():
                        if entry['hook'].endswith(TRIGGER_STACK) and entry.get('replay_trigger_effects_started'):
                            entry['replay_trigger_unknown_rng'] = entry.get('replay_trigger_unknown_rng',0)+1
                        if entry['hook'].endswith(PAYMENT):
                            entry['replay_payment_random_requests'] = entry.get('replay_payment_random_requests', 0) + 1
                            if not stack or not stack[-1][2].startswith('forge/ai/ComputerUtilMana.payManaCost('):
                                entry['replay_payment_unknown_random_requests'] = entry.get('replay_payment_unknown_random_requests', 0) + 1
                else:
                    raise ValueError('Unknown referee record')
            if not terminal or initial != 1 or stack or roots or checksum.hexdigest() != expected_sha256:
                raise ValueError('Missing initial/completion state or source checksum mismatch')
            result.write(json.dumps({'kind': 'decision_tape_complete', 'decisions': count,
                                     'source_sha256': expected_sha256, 'unsupported_decisions': sum(unsupported.values()),
                                     'rules_approved': False}) + '\n')
            result.flush(); os.fsync(result.fileno())
        os.link(temporary, output)
        directory = os.open(output.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'source_sha256': expected_sha256, 'records': records, 'root_decisions': count,
            'supported': dict(supported), 'unsupported': dict(unsupported),
            'all_root_choices_retained': True, 'full_game_replay': False, 'rules_approved': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.sha256, args.output), indent=2))
