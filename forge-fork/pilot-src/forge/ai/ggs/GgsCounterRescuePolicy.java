package forge.ai.ggs;

import forge.ai.ComputerUtilAbility;
import forge.ai.ComputerUtilCombat;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Do not spend Swan Song to preserve an unblocked attacker about to kill us.
 * This is a narrow public-state guard, not a multiplayer counterspell solver.
 */
public final class GgsCounterRescuePolicy {
    private GgsCounterRescuePolicy() {}
    public static boolean rejectLethalRescueCounter(Player ai, SpellAbility counter) {
        if (!GgsNinjutsuPolicy.enabled(ai)
                || Boolean.getBoolean("dragonmind.disableCounterRescuePolicy")
                || counter.getApi() != ApiType.Counter || !counter.isSpell()
                || !"Swan Song".equals(counter.getHostCard().getName())
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
                && combat.isUnblocked(attacker) && ai.equals(combat.getDefenderByAttacker(attacker)))) return false;
        int removedDamage = ComputerUtilCombat.damageIfUnblocked(attacker, ai, combat, false);
        if (removedDamage >= ai.getLife()) return true;
        // A smaller attacker can be the difference between lethal combined
        // damage and survival. Keep this extension to an ordinary unblocked
        // life-damage batch aimed entirely at us; complicated combat retains
        // the existing policy rather than guessing a removal outcome.
        if (removedDamage <= 0) return false;
        int combined = 0;
        for (Card other : combat.getAttackers()) {
            if (other.isPhasedOut() || !combat.isUnblocked(other)
                    || !ai.equals(combat.getDefenderByAttacker(other))
                    || other.hasKeyword(Keyword.FIRST_STRIKE)
                    || other.hasKeyword(Keyword.DOUBLE_STRIKE)
                    || other.hasKeyword(Keyword.INFECT)) return false;
            combined += Math.max(0, ComputerUtilCombat.damageIfUnblocked(other, ai, combat, false));
        }
        return combined >= ai.getLife() && combined - removedDamage < ai.getLife();
    }
}

