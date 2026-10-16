package forge.ai.ggs;

import forge.ai.ComputerUtilCombat;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.combat.CombatUtil;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;

/** Narrow reconstructed decisions. Ordinary legality, targeting and payment still apply. */
public final class GgsRecoveryPolicy {
    private GgsRecoveryPolicy() {}
    private static boolean enabled(Player ai) {
        return GgsNinjutsuPolicy.enabled(ai) && !Boolean.getBoolean("dragonmind.disableRecoveryPolicy");
    }
    public static boolean rejectSlowSeven(Player ai, int returning) {
        if (!enabled(ai) || returning != 0 || ai.getCardsIn(ZoneType.Hand).size() != 7
                || !ai.getCardsIn(ZoneType.Command).anyMatch(CommanderEngineProfile::needsFreshCombatConnection)) return false;
        int lands = 0;
        boolean early = false;
        for (Card c : ai.getCardsIn(ZoneType.Hand)) {
            if (c.isLand()) { lands++; continue; }
            int mv = c.getCMC();
            if (((c.isCreature() || c.isArtifact() || c.isEnchantment()) && mv <= 3)
                    || ((c.isInstant() || c.isSorcery()) && mv <= 2)) early = true;
        }
        return lands >= AdaptiveStrategy.current().openingLandThreshold && !early;
    }
    public static Card prowlerTarget(Player ai, SpellAbility sa) {
        if (!enabled(ai) || !ai.canGainLife() || !"Nezumi Prowler".equals(sa.getHostCard().getName())
                || sa.getHostCard().getController() != ai || !sa.getHostCard().isInZone(ZoneType.Battlefield)
                || sa.getApi() != ApiType.Pump || sa.getSubAbility() != null
                || !"Deathtouch & Lifelink".equals(sa.getParam("KW"))
                || sa.getTargetRestrictions() == null || sa.getMinTargets() != 1 || sa.getMaxTargets() != 1
                || sa.isCurse()) return null;
        var phase = ai.getGame().getPhaseHandler();
        var combat = ai.getGame().getCombat();
        if (!phase.isPlayerTurn(ai) || combat == null || combat.getAttackingPlayer() != ai
                || (phase.getPhase() != PhaseType.COMBAT_DECLARE_BLOCKERS
                    && phase.getPhase() != PhaseType.COMBAT_FIRST_STRIKE_DAMAGE)) return null;
        Card best = null;
        int amount = 0;
        for (Card c : combat.getAttackers()) {
            if (c.getController() != ai || !combat.isUnblocked(c) || !sa.canTarget(c)
                    || c.hasKeyword(Keyword.LIFELINK)) continue;
            if (phase.getPhase() == PhaseType.COMBAT_FIRST_STRIKE_DAMAGE
                    && c.hasKeyword(Keyword.FIRST_STRIKE) && !c.hasKeyword(Keyword.DOUBLE_STRIKE)) continue;
            if (!(combat.getDefenderByAttacker(c) instanceof Player defender)) continue;
            int damage = ComputerUtilCombat.damageIfUnblocked(c, defender, combat, false);
            if (damage > amount || (damage > 0 && damage == amount && (best == null || c.getId() < best.getId()))) {
                best = c; amount = damage;
            }
        }
        return best;
    }
    public static boolean usefulSwordCombat(Player ai, SpellAbility sa) {
        if (!enabled(ai) || !"Aggravated Assault".equals(sa.getHostCard().getName())
                || sa.getApi() != ApiType.UntapAll || sa.getSubAbility() == null
                || sa.getSubAbility().getApi() != ApiType.AddPhase) return false;
        var phase = ai.getGame().getPhaseHandler();
        if (!phase.isPlayerTurn(ai) || phase.getPhase() != PhaseType.MAIN2 || !ai.getGame().getStack().isEmpty()) return false;
        // Cost/color checks are performed by the normal controller. Here require
        // a repeatable land-based renewal route rather than finite artifact mana.
        int readyLands = 0, redLands = 0;
        for (Card land : ai.getLandsInPlay()) {
            if (land.isTapped() || land.isPhasedOut()
                    || land.getOracleText().toLowerCase(java.util.Locale.ROOT).contains("damage to you")) continue;
            boolean usable = false, red = false;
            for (SpellAbility original : land.getManaAbilities()) {
                SpellAbility mana = original.copy(ai); mana.setActivatingPlayer(ai);
                if (mana.getPayCosts() == null || !mana.getPayCosts().hasOnlySpecificCostType(forge.game.cost.CostTap.class)
                        || mana.hasParam("RestrictValid") || mana.hasParam("RestrictValidPlayer")
                        || mana.hasParam("ManaRestriction") || !mana.canPlay()) continue;
                for (String color : java.util.List.of("W","U","B","R","G","C")) {
                    if (mana.getManaPart().canProduce(color, mana)) {
                        usable = true; if (color.equals("R")) red = true;
                    }
                }
            }
            if (usable) readyLands++;
            if (red) redLands++;
        }
        if (readyLands < 5 || redLands < 2) return false;
        for (Card c : ai.getCreaturesInPlay()) {
            if (c.getNetCombatDamage() <= 0 || !c.getEquippedBy().anyMatch(e -> "Sword of Feast and Famine".equals(e.getName()))) continue;
            for (Player defender : ai.getOpponents()) {
                // A prospective extra combat is after MAIN2: canAttack() rejects
                // the current phase. Use its forecast legality, then restore all
                // present-turn checks except tapping (Assault untaps the body).
                if (c.isPhasedOut() || CombatUtil.isAttackerSick(c, defender)
                        || !CombatUtil.canAttackNextTurn(c, defender)
                        || CombatUtil.getAttackCost(ai.getGame(), c, defender) != null) continue;
                boolean blocked = false;
                for (Card blocker : defender.getCreaturesInPlay()) if (CombatUtil.canBlock(c, blocker)) { blocked = true; break; }
                if (!blocked && ComputerUtilCombat.predictDamageTo(defender, c.getNetCombatDamage(), c, true) > 0) return true;
            }
        }
        return false;
    }
}
