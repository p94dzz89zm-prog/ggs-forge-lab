package forge.ai.ggs;

import forge.ai.ComputerUtilAbility;
import forge.ai.ComputerUtilCombat;
import forge.game.ability.ApiType;
import forge.game.card.Card;
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
        return attacker.isCreature() && attacker.getController().isOpponentOf(ai)
                && !attacker.isPhasedOut() && combat.isAttacking(attacker)
                && combat.isUnblocked(attacker) && ai.equals(combat.getDefenderByAttacker(attacker))
                && ComputerUtilCombat.damageIfUnblocked(attacker, ai, combat, false) >= ai.getLife();
    }
}
