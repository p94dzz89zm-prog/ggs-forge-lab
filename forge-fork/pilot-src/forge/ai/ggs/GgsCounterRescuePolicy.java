package forge.ai.ggs;

import forge.ai.ComputerUtilAbility;
import forge.ai.ComputerUtilCombat;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Do not spend a tested counter to preserve an attacker about to kill us.
 * This is a narrow public-state guard, not a multiplayer counterspell solver.
 */
public final class GgsCounterRescuePolicy {
    private GgsCounterRescuePolicy() {}
    private static final java.util.Set<String> SUPPORTED_COUNTERS = java.util.Set.of(
            "Swan Song", "An Offer You Can't Refuse", "Counterspell");
    private static int incomingDamage(Card attacker, Player ai, Combat combat) {
        if (combat.isUnblocked(attacker))
            return ComputerUtilCombat.damageIfUnblocked(attacker, ai, combat, false);
        if (!attacker.hasKeyword(Keyword.TRAMPLE)) return 0;
        // Ordinary blockers-step spill only. Complex strike/poison/deathtouch
        // assignments retain stock evaluation rather than a guessed rescue.
        if (attacker.hasKeyword(Keyword.FIRST_STRIKE)
                || attacker.hasKeyword(Keyword.DOUBLE_STRIKE)
                || attacker.hasKeyword(Keyword.INFECT)
                || attacker.hasKeyword(Keyword.DEATHTOUCH)) return -1;
        var blockers = combat.getBlockers(attacker);
        for (Card blocker : blockers) if (blocker.hasKeyword(Keyword.FIRST_STRIKE)
                || blocker.hasKeyword(Keyword.DOUBLE_STRIKE)) return -1;
        int spill = Math.max(0, attacker.getNetCombatDamage()
                - ComputerUtilCombat.totalShieldDamage(attacker, blockers));
        return ComputerUtilCombat.predictDamageTo(ai, spill, attacker, true);
    }
    public static boolean rejectLethalRescueCounter(Player ai, SpellAbility counter) {
        if (!GgsNinjutsuPolicy.enabled(ai)
                || Boolean.getBoolean("dragonmind.disableCounterRescuePolicy")
                || counter.getApi() != ApiType.Counter || !counter.isSpell()
                || !SUPPORTED_COUNTERS.contains(counter.getHostCard().getName())
                || ai.getGame().getStack().size() != 1
                || ai.getGame().getPhaseHandler().getPhase() != PhaseType.COMBAT_DECLARE_BLOCKERS
                || !ai.canLoseLife() || ai.cantLoseForZeroOrLessLife() || ai.getLife() <= 0) return false;
        var combat = ai.getGame().getCombat();
        if (combat == null || combat.getAttackingPlayer() == ai) return false;
        SpellAbility removal = ComputerUtilAbility.getTopSpellAbilityOnStack(ai.getGame(), counter);
        if (removal == null || !removal.isSpell() || removal.getApi() != ApiType.Destroy
                || removal.getSubAbility() != null || removal.getActivatingPlayer() == null
                || !removal.getActivatingPlayer().isOpponentOf(ai)
                || removal.getTargets().getTargetCards().size() != 1) return false;
        Card attacker = removal.getTargets().getTargetCards().get(0);
        if (!(attacker.isCreature() && attacker.getController().isOpponentOf(ai)
                && !attacker.isPhasedOut() && combat.isAttacking(attacker)
                && ai.equals(combat.getDefenderByAttacker(attacker)))) return false;
        int removedDamage = incomingDamage(attacker, ai, combat);
        if (removedDamage >= ai.getLife()) return true;
        // A smaller attacker can be the difference between lethal combined
        // damage and survival. Keep this extension to an ordinary
        // life-damage batch aimed at us; complicated combat retains
        // the existing policy rather than guessing a removal outcome.
        if (removedDamage <= 0) return false;
        int combined = 0;
        for (Card other : combat.getAttackers()) {
            if (!ai.equals(combat.getDefenderByAttacker(other))) continue;
            if (other.isPhasedOut()
                    || other.hasKeyword(Keyword.FIRST_STRIKE)
                    || other.hasKeyword(Keyword.DOUBLE_STRIKE)
                    || other.hasKeyword(Keyword.INFECT)) return false;
            int damage = incomingDamage(other, ai, combat);
            if (damage < 0) return false;
            combined += Math.max(0, damage);
        }
        return combined >= ai.getLife() && combined - removedDamage < ai.getLife();
    }
}

