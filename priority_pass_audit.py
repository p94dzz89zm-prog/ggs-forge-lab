"""Scoped priority/pass disclosure checks; not independent priority derivation.

CR117.3d/106.4b require announcing floating mana when passing priority.
The recorder emits that announcement immediately after the controller return.
Missing legacy announcements remain coverage gaps, never synthesized passes.
"""
from collections import Counter

CHOICE = '.chooseSpellAbilityToPlay()Ljava/util/List;'
ANNOUNCE = 'forge/game/player/Player.announceManaPool(Ljava/lang/String;Ljava/util/Map;)V'
COLORS = {'W', 'U', 'B', 'R', 'G', 'C'}


class PriorityPassAudit:
    def __init__(self):
        self.pending = None
        self.passes = 0
        self.entitlements = 0
        self.disclosures = 0
        self.gaps = Counter()
        self.active_players = None

    def next_row(self, row):
        state = row.get('elimination_state_after', row.get('initial_state'))
        if isinstance(state, dict):
            players = state.get('players')
            if isinstance(players, list) and players and all(
                isinstance(p, dict) and type(p.get('id')) is int and type(p.get('active')) is bool
                for p in players
            ) and len({p['id'] for p in players}) == len(players):
                self.active_players = {p['id'] for p in players if p['active']}
            else:
                self.active_players = None
        if self.pending is None:
            return
        actor, counts = self.pending
        self.pending = None
        if row.get('kind') != 'engine_call' or row.get('hook') != ANNOUNCE:
            self.gaps['Missing immediate recorded priority-pass mana announcement'] += 1
            return
        payload = row.get('public_payload', {})
        if payload.get('reason') != 'priority_pass':
            raise ValueError('Priority-pass announcement reason mismatch')
        if type(payload.get('player_id')) is not int or payload['player_id'] != actor:
            raise ValueError('Priority-pass announcement player mismatch')
        actual = payload.get('counts')
        if not isinstance(actual, dict) or any(c not in COLORS or type(n) is not int or n <= 0 for c, n in actual.items()):
            raise ValueError('Malformed public floating-mana counts')
        if actual != counts:
            raise ValueError('Public floating-mana counts differ from recorded pool')
        if row.get('visibility_operation') != 'public_mana_pool_announcement':
            raise ValueError('Missing public priority-pass announcement visibility')
        recipients = row.get('entitled_player_ids')
        if not isinstance(recipients, list) or any(type(p) is not int for p in recipients) or len(set(recipients)) != len(recipients) or actor not in recipients:
            raise ValueError('Malformed priority-pass announcement audience')
        if self.active_players is None:
            self.gaps['Missing recorded active-player audience for announcement'] += 1
            return
        if set(recipients) != self.active_players:
            raise ValueError('Priority-pass announcement audience differs from recorded active players')
        self.disclosures += 1

    def returned(self, entry, row, *, nested_priority=False):
        if not entry.get('hook', '').endswith(CHOICE) or nested_priority:
            return
        speculative = entry.get('speculative')
        if type(speculative) is not bool:
            self.gaps['Missing typed priority speculation status'] += 1
            return
        if speculative or row.get('result') not in (None, []):
            return
        self.passes += 1
        actor = entry.get('receiver', {})
        player, priority = actor.get('player_id'), entry.get('priority_player_id')
        if type(player) is not int or type(priority) is not int:
            self.gaps['Missing typed recorded priority entitlement'] += 1
        elif player != priority or actor.get('lost') is not False:
            raise ValueError('Priority passed by a different or eliminated player')
        elif entry.get('phase') == 'UNTAP':
            raise ValueError('Ordinary priority pass during untap')
        elif entry.get('phase') in (None, 'null'):
            self.gaps['Missing priority phase'] += 1
        else:
            self.entitlements += 1
        if entry.get('arguments') != [] or row.get('arguments_after') != []:
            raise ValueError('Priority-pass arguments mutated')
        pool = entry.get('mana_context', {}).get('pool')
        if pool is None:
            self.gaps['Missing priority-pass mana pool snapshot'] += 1
            return
        if not isinstance(pool, list) or any(not isinstance(u, dict) or u.get('color') not in COLORS for u in pool):
            raise ValueError('Malformed priority-pass mana pool')
        if pool and type(player) is int:
            self.pending = (player, dict(Counter(u['color'] for u in pool)))

    def report(self):
        gaps = self.gaps.copy()
        if self.pending is not None:
            gaps['Missing immediate recorded priority-pass mana announcement'] += 1
        return dict(priority_passes=self.passes,
                    recorded_priority_entitlement_checks=self.entitlements,
                    priority_mana_disclosure_checks=self.disclosures,
                    priority_pass_gaps=dict(gaps),
                    priority_derivation_approved=False)
