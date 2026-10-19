"""Per-decision replay obligations; local checks never certify a full game.

Consumes extracted decisions and their original paired payloads. Original
archives remain authoritative. No omniscient row is a learning example.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

OBLIGATIONS = {
 'chooseStartingPlayer': ('pregame', 'choose first active player', ['CR103.1', 'eligible live player; authorized chooser']),
 'mulliganKeepHand': ('mulligan', 'keep or reshuffle through engine procedure', ['CR103.5', 'recorded format/free-mulligan policy; hand and library order']),
 'chooseSpellAbilityToPlay': ('priority', 'pass, cast, activate or special action', ['CR117', 'CR601', 'CR602', 'priority holder; timing; candidate identity; targets/modes/X; costs']),
 'payManaCost': ('payment', 'produce and spend actual resources', ['CR106', 'CR118', 'CR601.2f-h', 'source availability; restrictions; cost modifications; exact payment choices']),
 'orderAndPlaySimultaneousSa': ('triggers', 'order and put abilities on stack', ['CR603.3b', 'APNAP; simultaneous order; modes and legal targets']),
 'chooseSingleEntityForEffect': ('effect choice', 'bind selected live entity', ['CR608.2d', 'engine-offered domain; mandatory/optional choice; reveal entitlement']),
 'confirmAction': ('optional effect', 'accept or decline prompted action', ['CR608.2d', 'prompt/source binding; may versus mandatory; resolution context']),
 'chooseSingleCardForZoneChange': ('zone choice', 'select source then execute zone transition', ['CR400.7', 'CR608.2d', 'origin/destination; legal domain; delayed reveal; ownership']),
 'chooseSingleReplacementEffect': ('replacement', 'select applicable replacement then recompute', ['CR616.1', 'affected player; applicability; prohibition on repeated application']),
 'declareAttackers': ('combat attack', 'declare and pay attack costs', ['CR508', 'controller; untapped/haste; attack restrictions/requirements; costs']),
 'declareBlockers': ('combat block', 'declare blocking assignments', ['CR509', 'live attackers/blockers; evasion; restrictions/requirements; costs']),
 'confirmTrigger': ('optional trigger', 'accept or decline optional triggered action', ['CR603', 'may/mandatory; source/targets; correct controller and timing']),
 'orderMoveToZoneList': ('ordered zone transition', 'order objects before moving', ['CR400', 'exact membership/permutation; ordered zones; replacement effects']),
 'chooseCounterType': ('counter choice', 'select offered counter type then engine applies', ['CR122', 'offered domain; source binding; replacement effects']),
 'assignCombatDamage': ('combat damage', 'assign then deal damage simultaneously', ['CR510', 'legal recipients; power; lethal/deathtouch/trample; first/double strike']),
 'chooseColors': ('color choice', 'choose permitted color set', ['CR105', 'CR608.2d', 'allowed colors; min/max; exclude-color restrictions']),
}


def local_priority_check(entry, returned):
    """Independent of the driver/encoder, but trusts recorded priority entitlement.

    Full priority derivation, pending state-based actions and stack readiness
    are separate, currently unresolved obligations.
    """
    if entry.get('arguments') != [] or returned.get('arguments_after') != []:
        return 'mutated_priority_arguments'
    if returned.get('result') is not None and returned['result'] != []:
        return 'selected_action_not_a_pass'
    actor = entry['receiver']
    if actor.get('lost') is not False or actor.get('player_id') != entry.get('priority_player_id'):
        return 'recorded_priority_entitlement_mismatch'
    if entry.get('phase') in (None, 'null', 'UNTAP', 'CLEANUP'):
        return 'no_ordinary_priority_in_recorded_step'
    if entry.get('mana_context', {}).get('pool') != []:
        return 'mana_announcement_unverified'
    return None


def classify(decision, entry, returned):
    name = entry['hook'].split('.', 1)[1].split('(', 1)[0]
    mechanic, transition, obligations = OBLIGATIONS[name]  # unknown family fails
    row = dict(decision_index=decision['index'], hook=entry['hook'], mechanic=mechanic,
               state_transition=transition, legality_requirements=obligations,
               support='driver_contract' if decision['kind'] == 'decision' else 'unsupported',
               source_call_record=decision['source_call_record'], source_return_record=decision['source_return_record'],
               original_game_decision_executed=False, full_rules_approved=False)
    if name == 'chooseSpellAbilityToPlay':
        land = decision.get('decision_type') == 'play_land'
        spell = decision.get('decision_type') == 'plain_hand_permanent_spell'
        if land or spell:
            source = returned['result'][0]['source']
            issue = None if (source['card_id'] == decision['land_card_id' if land else 'source_card_id'] and source['zone'] == 'Hand' and source['owner_id'] == entry['receiver']['player_id'] == entry.get('priority_player_id') == entry.get('turn_player_id') and entry.get('phase') in ('MAIN1', 'MAIN2')) else 'recorded_hand_action_context_inconsistent'
        else:
            issue = local_priority_check(entry, returned)
        row['independent_local_check'] = issue or ('recorded_hand_action_context_consistent; live legality and payment checks required' if land or spell else 'recorded_entitlement_and_empty_pool_consistent')
        if row['support'] == 'driver_contract' and issue:
            raise ValueError('Driver coverage contradicts local priority check: ' + issue)
    if row['support'] == 'driver_contract' and name in ('chooseSingleReplacementEffect', 'chooseCounterType', 'chooseColors'):
        args, selected = entry['arguments'], returned['result']
        if args != returned['arguments_after']:
            raise ValueError('Effect choice mutated arguments')
        if name == 'chooseSingleReplacementEffect':
            # Equality here includes the original full source state; the driver
            # separately rebinds a stable trait fingerprint to a live object.
            if sum(item == selected for item in args[0]) != 1:
                raise ValueError('Replacement not uniquely offered')
        elif name == 'chooseCounterType':
            if sum(item == selected for item in args[0]) != 1:
                raise ValueError('Counter not uniquely offered')
        elif not (set(selected) - {'C'} <= set(args[4]) and args[2] <= len(set(selected) - {'C'}) <= args[3]):
            raise ValueError('Color outside permitted domain/cardinality')
        row['independent_local_check'] = 'original_offered_domain_and_pure_return_consistent'
    row['remaining_global_obligations'] = ['independently reconstruct state, priority, stack and visibility',
                                          'execute recorded choices against live legal options',
                                          'verify resulting transitions and outcome',
                                          'derive effect/replacement applicability independently of offered list']
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--payloads', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    decisions = [json.loads(s) for s in args.decisions.open()]
    if decisions[-1]['kind'] != 'decision_tape_complete':
        raise ValueError('Unsealed extracted decision sequence')
    decisions.pop(); supported = Counter(); unsupported = Counter()
    with args.output.open('x') as output:
        count = 0
        for count, line in enumerate(args.payloads.open(), 1):
            payload = json.loads(line); decision = decisions[count - 1]
            if decision['index'] != count - 1 or decision['source_call_id'] != payload['entry']['call_id']:
                raise ValueError('Decision/payload identity mismatch')
            row = classify(decision, payload['entry'], payload['return'])
            (supported if row['support'] == 'driver_contract' else unsupported)[row['mechanic']] += 1
            output.write(json.dumps(row) + '\n')
        if count != len(decisions):
            raise ValueError('Missing decision payloads')
    print(json.dumps({'driver_supported_decisions': sum(supported.values()), 'total': count,
                      'by_mechanic_supported': dict(supported), 'by_mechanic_unsupported': dict(unsupported),
                      'original_game_decisions_executed': 0, 'full_rules_approved': False}, indent=2))
