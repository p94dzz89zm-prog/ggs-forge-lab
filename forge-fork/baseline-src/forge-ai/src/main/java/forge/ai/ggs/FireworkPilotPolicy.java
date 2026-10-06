package forge.ai.ggs;

import forge.ai.*;
import forge.card.CardType;
import forge.game.card.*;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.*;

/** Opt-in public-position planning. Does not alter card rules or bypass costs. */
public final class FireworkPilotPolicy {
    private FireworkPilotPolicy() {}

    public static boolean preCombatPermanent(Player ai, SpellAbility sa) {
        if (!GgsNinjutsuPolicy.enabled(ai) || !sa.isSpell()) return false;
        Card c = sa.getHostCard();
        // These engines trigger at beginning of combat; MAIN2 loses a whole cycle.
        if (Set.of("Urabrask's Forge", "Loyal Apprentice", "Fire Navy Trebuchet").contains(c.getName())) return true;
        // Deploy cheap ramp before ranking the rest of MAIN1, rather than reserving
        // mana for it until MAIN2 and losing the opportunity to use its production.
        if (!c.getManaAbilities().isEmpty() && !c.isLand() && c.getCMC() <= 2) return true;
        if ("Krenko, Tin Street Kingpin".equals(c.getName())) {
            for (Card engine : ai.getCreaturesInPlay()) {
                if (CommanderEngineProfile.needsFreshCombatConnection(engine)) {
                    SpellAbility combined = sa.copy(c, false);
                    combined.setActivatingPlayer(ai);
                    combined.setPayCosts(new forge.game.cost.Cost("3 R R", false));
                    return ComputerUtilCost.canPayCost(combined, ai, false);
                }
            }
        }
        return false;
    }

    private static Set<String> manaColors(Card card) {
        Set<String> colors = new HashSet<>();
        for (SpellAbility mana : ComputerUtilMana.getAIPlayableMana(card)) {
            Player previous = mana.getActivatingPlayer();
            try {
                mana.setActivatingPlayer(card.getController());
                for (String color : List.of("U", "B", "R")) if (mana.canProduce(color)) colors.add(color);
            } finally { mana.setActivatingPlayer(previous); }
        }
        return colors;
    }

    /** Fix an absent commander color before default land/ramp ranking. No claim
     * that color coverage alone is a full mana-payment or tappedness forecast. */
    public static CardCollection preferMissingColorLands(Player ai, CardCollection options) {
        if (!GgsNinjutsuPolicy.enabled(ai)) return options;
        boolean needsEngine = ai.getCardsIn(ZoneType.Command, ZoneType.Hand).anyMatch(
                CommanderEngineProfile::needsFreshCombatConnection);
        if (!needsEngine) return options;
        Set<String> missing = new HashSet<>(List.of("U", "B", "R"));
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) missing.removeAll(manaColors(c));
        if (missing.isEmpty()) return options;
        CardCollection best = new CardCollection(); int bestScore = 0;
        for (Card c : options) {
            Set<String> colors = manaColors(c); colors.retainAll(missing);
            int score = colors.size();
            if (score > bestScore) { best.clear(); bestScore = score; }
            if (score == bestScore && score > 0) best.add(c);
        }
        return best.isEmpty() ? options : best;
    }

    public static String coverType(Player ai, Collection<String> valid) {
        Collection<String> types = valid == null || valid.isEmpty() ? CardType.getAllCreatureTypes() : valid;
        String best = ""; double bestScore = -Double.MAX_VALUE;
        for (String type : new TreeSet<>(types)) {
            double score = 0;
            for (Card c : ai.getCreaturesInPlay()) if (c.getType().hasSubtype(type)) score += fearGain(c, ai.getOpponents().getCreaturesInPlay());
            for (Player opp : ai.getOpponents()) for (Card c : opp.getCreaturesInPlay()) {
                if (c.getType().hasSubtype(type)) score -= fearGain(c, ai.getCreaturesInPlay());
            }
            // Small future benefit breaks ties; current opponent downside dominates.
            for (Card c : ai.getCardsIn(ZoneType.Hand)) if (c.isCreature() && c.getType().hasSubtype(type)) score += .2;
            if (score > bestScore) { best = type; bestScore = score; }
        }
        return best;
    }

    private static double fearGain(Card c, Iterable<Card> blockers) {
        if (c.isPhasedOut() || c.hasKeyword(Keyword.FEAR) || c.getNetCombatDamage() <= 0) return 0;
        int ordinary = 0, fearLegal = 0;
        for (Card b : blockers) if (!b.isPhasedOut() && CombatUtil.canBlock(c, b)) {
            ordinary++;
            if (b.isArtifact() || b.getColor().hasBlack()) fearLegal++;
        }
        if (ordinary == 0) return 0;
        return (fearLegal == 0 ? 3 : 1) * Math.max(1, c.getNetCombatDamage());
    }

    public static boolean marchTargets(Player ai, SpellAbility sa) {
        sa.resetTargets();
        List<Card> preferred = new ArrayList<>();
        // Save creatures threatened by the current stack before considering combat.
        for (Object threatened : ComputerUtil.predictThreatenedObjects(ai, null, true)) {
            if (threatened instanceof Card c && c.getController() == ai && c.isCreature()
                    && !c.isPhasedOut() && sa.canTarget(c) && !preferred.contains(c)) preferred.add(c);
        }
        Combat combat = ai.getGame().getCombat();
        PhaseType phase = ai.getGame().getPhaseHandler().getPhase();
        // A blockers-step snapshot has actual assignments. Do not guess pre-blocks.
        if (combat != null && (phase == PhaseType.COMBAT_DECLARE_BLOCKERS || phase == PhaseType.COMBAT_FIRST_STRIKE_DAMAGE)) {
            boolean serious = ComputerUtilCombat.lifeInSeriousDanger(ai, combat);
            for (Card c : combat.getAttackers()) {
                if (c.getController().isOpponentOf(ai) && ai.equals(combat.getDefenderByAttacker(c))
                        && combat.getUnblockedAttackers().contains(c) && sa.canTarget(c)
                        && (serious || ComputerUtilCombat.damageIfUnblocked(c, ai, combat, false) >= 4)) preferred.add(c);
            }
            for (Card c : ai.getCreaturesInPlay()) if (sa.canTarget(c) && !preferred.contains(c)
                    && ComputerUtilCombat.combatantWouldBeDestroyed(ai, c, combat)) preferred.add(c);
        }
        // Access must be purchased BEFORE blockers: removing a blocker after
        // assignment does not make an already blocked attacker unblocked.
        if (preferred.isEmpty() && combat != null && phase == PhaseType.COMBAT_DECLARE_ATTACKERS
                && combat.getAttackingPlayer() == ai
                && ai.getCreaturesInPlay().anyMatch(CommanderEngineProfile::needsFreshCombatConnection)) {
            for (Card attacker : combat.getAttackers()) {
                if (!attacker.enteredThisTurn() || attacker.getNetCombatDamage() <= 0
                        || !(combat.getDefenderByAttacker(attacker) instanceof Player defender)) continue;
                List<Card> blockers = new ArrayList<>();
                for (Card c : defender.getCreaturesInPlay()) if (CombatUtil.canBlock(attacker, c)) blockers.add(c);
                if (blockers.size() == 1 && sa.canTarget(blockers.get(0))) { preferred.add(blockers.get(0)); break; }
            }
        }
        if (preferred.isEmpty()) return false;
        preferred.sort(Comparator.comparingInt((Card c) -> ComputerUtilCard.evaluateCreature(c)).reversed().thenComparingInt(Card::getId));
        int max = ComputerUtilCost.setMaxXValue(sa, ai, false);
        if (max < 1) return false;
        int count = Math.min(max, preferred.size());
        sa.setXManaCostPaid(count);
        for (int i = 0; i < count; i++) sa.getTargets().add(preferred.get(i));
        if (!sa.isTargetNumberValid() || !ComputerUtilCost.canPayCost(sa, ai, false)) { sa.resetTargets(); return false; }
        return true;
    }
}
