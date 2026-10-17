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
    private static boolean supportedRemoval(SpellAbility removal) {
        if (removal.getApi() == ApiType.Destroy && removal.getSubAbility() == null) return true;
        // Match the tested exile spell's complete effect shape. Its three-life
        // loss happens on resolution; it is not an additional casting cost.
        SpellAbility loss = removal.getSubAbility();
        return removal.getApi() == ApiType.ChangeZone
                && removal.getHostCard().getName().equals("Anguished Unmaking")
                && "Battlefield".equals(removal.getParam("Origin"))
                && "Exile".equals(removal.getParam("Destination"))
                && loss != null && loss.getApi() == ApiType.LoseLife
                && "3".equals(loss.getParam("LifeAmount"))
                && !loss.hasParam("Defined") && loss.getSubAbility() == null;
    }
    private static int incomingDamage(Card attacker, Player ai, Combat combat) {
        if (combat.isUnblocked(attacker))
            return ComputerUtilCombat.damageIfUnblocked(attacker, ai, combat, false);
        if (!attacker.hasKeyword(Keyword.TRAMPLE)) return 0;
        if (attacker.hasKeyword(Keyword.INFECT)
                || attacker.hasKeyword(Keyword.DEATHTOUCH)) return -1;
        var blockers = combat.getBlockers(attacker);
        boolean strike = attacker.hasFirstStrike() || attacker.hasDoubleStrike();
        for (Card blocker : blockers) strike |= blocker.hasFirstStrike() || blocker.hasDoubleStrike();
        if (strike) {
            // One blocker only. Retaining its entire shield for both steps
            // deliberately undercounts double-strike spill when it dies early.
            // Do not assign a later step to an attacker killed in first strike.
            if (blockers.size() != 1) return -1;
            Card blocker = blockers.get(0);
            if (blocker.hasKeyword(Keyword.DEATHTOUCH) || blocker.hasKeyword(Keyword.INFECT)
                    || blocker.hasKeyword(Keyword.WITHER)) return -1;
            int early = (blocker.hasFirstStrike() || blocker.hasDoubleStrike())
                    ? ComputerUtilCombat.predictDamageTo(attacker, blocker.getNetCombatDamage(), blocker, true) : 0;
            if (early >= attacker.getLethalDamage()) return -1;
            int spill = Math.max(0, attacker.getNetCombatDamage() - blocker.getLethalDamage());
            int damage = ComputerUtilCombat.predictDamageTo(ai, spill, attacker, true);
            return damage * (attacker.hasDoubleStrike() ? 2 : 1);
        }
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
        if (removal == null || !removal.isSpell() || !supportedRemoval(removal)
                || removal.getActivatingPlayer() == null
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
            if (other.isPhasedOut() || other.hasKeyword(Keyword.INFECT)) return false;
            // Only the removal target gains the strike-combat extension.
            // Preserve the existing boundary for a separate strike attacker.
            if (other != attacker && (other.hasFirstStrike() || other.hasDoubleStrike())) return false;
            int damage = incomingDamage(other, ai, combat);
            if (damage < 0) return false;
            combined += Math.max(0, damage);
        }
        return combined >= ai.getLife() && combined - removedDamage < ai.getLife();
    }
}

