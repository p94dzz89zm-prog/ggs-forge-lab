"""Non-overridable coverage gate: completed capture is not complete certification."""
CAPTURE = {
    'canonical_decks_and_frozen_references': 'external_binding_required',
    'seeded_rng_and_shuffle_permutations': 'native_observer_and_independent_scoped_reader',
    'starting_player_selection': 'initial_list_protocol_only',
    'mulligans_and_bottoming': 'native_controls_and_transcript; general_state_oracle_pending',
    'opening_pregame_actions_and_first_turn': 'incomplete',
    'complete_legal_action_alternatives': 'incomplete',
    'priority_and_stack': 'partial_existing_capture',
    'mana_costs_targets_and_restrictions': 'partial_existing_capture',
    'triggers_replacements_and_continuous_effects': 'partial_existing_capture',
    'combat_ninjutsu_and_equipment': 'partial_existing_capture',
    'state_based_actions_and_object_identity': 'partial_existing_capture',
    'elimination_and_victory': 'partial_existing_capture',
}


def gate(configuration):
    errors=[]
    expected={'players':4,'starting_life':40,'free_seven_reshuffles':3,
              'commander_damage_loss':False,'profile':'ggs-house-v1'}
    if configuration != expected or any(type(configuration.get(k)) is not type(v) for k,v in expected.items()):
        errors.append('Exact explicit house configuration required; no inferred London substitution')
    # Neither a caller-provided pass flag nor complete simulator output can fill
    # absent independent derivations. Add implemented verifiers before opening.
    return dict(can_start_full_certification_game=False,can_certify_complete_game=False,
                configuration_errors=errors,capture_coverage=dict(CAPTURE),
                blockers=['Canonical deck/reference binding and complete opening oracle required',
                          'Complete engine-generated legal alternatives not yet captured',
                          'General independent action/effect/SBA/terminal derivation not implemented'],
                training_eligible=False)
