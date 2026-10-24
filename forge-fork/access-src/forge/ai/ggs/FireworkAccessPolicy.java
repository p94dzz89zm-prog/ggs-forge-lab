package forge.ai.ggs;

import forge.ai.*;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.util.*;

/** Public-board, opt-in access decisions; never changes the card's rules. */
public final class FireworkAccessPolicy {
    private FireworkAccessPolicy() {}
    private static AiAbilityDecision decision(boolean play) {
        return new AiAbilityDecision(play ? 100 : 0,
                play ? AiPlayDecision.WillPlay : AiPlayDecision.CantPlayAi);
    }
    public static AiAbilityDecision consider(Player ai, SpellAbility sa) {
        if (!GgsNinjutsuPolicy.enabled(ai) || !sa.isActivatedAbility()) return null;
        String name = sa.getHostCard().getName();
        boolean higure = name.equals("Higure, the Still Wind") && "MakeUnblockable".equals(sa.getParam("AILogic"));
        boolean cadence = name.equals("War Cadence") && "RestrictBlocking".equals(sa.getParam("AILogic"));
        boolean ginger = name.equals("Gingerbrute") && sa.hasParam("StaticAbilities") && "KWPump".equals(sa.getParam("StaticAbilities"));
        if (!higure && !cadence && !ginger) return null;
        // Keep stock main-phase planning; these decisions need actual attackers.
        var phase = ai.getGame().getPhaseHandler();
        if (!phase.isPlayerTurn(ai) || phase.getPhase() != PhaseType.COMBAT_DECLARE_ATTACKERS) return null;
        Combat combat = ai.getGame().getCombat();
        if (combat == null || combat.getAttackingPlayer() != ai) return decision(false);
        if (!ai.getCreaturesInPlay().anyMatch(CommanderEngineProfile::needsFreshCombatConnection)) return decision(false);
        // Do not repeatedly activate an already resolved nonstacking effect.
        String effectName = sa.getParamOrDefault("Name", name + "'s Effect");
        if (ai.isCardInCommand(effectName)) return decision(false);
        List<Card> attackers = new ArrayList<>(combat.getAttackers());
        attackers.sort(Comparator.comparingInt(Card::getId));
        for (Card attacker : attackers) {
            if (attacker.getController() != ai || !attacker.enteredThisTurn() || attacker.getNetCombatDamage() <= 0
                    || !(combat.getDefenderByAttacker(attacker) instanceof Player defender)) continue;
            List<Card> blockers = new ArrayList<>();
            for (Card blocker : defender.getCreaturesInPlay()) {
                if (CombatUtil.canBlock(attacker, blocker)) blockers.add(blocker);
            }
            if (blockers.isEmpty()) continue;
            if (higure) {
                if (!sa.canTarget(attacker)) continue;
                sa.resetTargets(); sa.getTargets().add(attacker);
                if (ComputerUtilCost.canPayCost(sa, ai, false)) return decision(true);
                sa.resetTargets();
            } else if (ginger) {
                if (attacker != sa.getHostCard() || blockers.stream().anyMatch(b -> b.hasKeyword(Keyword.HASTE))) continue;
                return decision(ComputerUtilCost.canPayCost(sa, ai, false));
            } else {
                // One blocker cannot pay if X exceeds its controller's public mana.
                // This is conservative: no opponent hand or hidden information.
                int x = ComputerUtilMana.getAvailableManaEstimate(defender, true) + 1;
                sa.setXManaCostPaid(x);
                if (ComputerUtilCost.canPayCost(sa, ai, false)) return decision(true);
                sa.setXManaCostPaid(0);
            }
        }
        return decision(false);
    }
}
