package forge.ai.ggs;

import forge.ai.ComputerUtilCard;
import forge.ai.ComputerUtilCombat;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Offensive Sneak swaps only; the engine remains responsible for casting legality. */
public final class GgsSneakPolicy {
    private GgsSneakPolicy() {}
    public static boolean applies(Player ai, SpellAbility sa) {
        var phase=ai.getGame().getPhaseHandler();
        return GgsNinjutsuPolicy.enabled(ai) && !Boolean.getBoolean("dragonmind.disableSneakPolicy")
            && sa.isSneak() && phase.isPlayerTurn(ai) && phase.getPhase()==PhaseType.COMBAT_DECLARE_BLOCKERS
            && ai.getGame().getStack().isEmpty()
            && ai.getCreaturesInPlay().anyMatch(CommanderEngineProfile::needsFreshCombatConnection);
    }
    public static Card chooseReturn(Player ai, SpellAbility sa, Iterable<Card> options) {
        if(!applies(ai,sa))return null;
        var combat=ai.getGame().getCombat();Card incoming=sa.getHostCard();
        if(combat==null || combat.getAttackingPlayer()!=ai || !incoming.isCreature() || incoming.getNetCombatDamage()<=0
            || CommanderEngineProfile.needsFreshCombatConnection(incoming)
            || incoming.hasKeyword(Keyword.FIRST_STRIKE) || incoming.hasKeyword(Keyword.DOUBLE_STRIKE)
            || (!incoming.ignoreLegendRule() && incoming.getType().isLegendary() && ai.isCardInPlay(incoming.getName())))return null;
        Card best=null;
        for(Card old:options){
            if(old.getController()!=ai || !combat.isAttacking(old) || !combat.isUnblocked(old)
                || old.enteredThisTurn() || old.isPhasedOut() || old.isCommander()
                || CommanderEngineProfile.needsFreshCombatConnection(old) || old.getNetCombatDamage()>3
                || old.hasKeyword(Keyword.FIRST_STRIKE) || old.hasKeyword(Keyword.DOUBLE_STRIKE))continue;
            if(!(combat.getDefenderByAttacker(old) instanceof Player defender))continue;
            int damage=ComputerUtilCombat.predictDamageTo(defender,Math.max(0,old.getNetCombatDamage()),old,true);
            if(damage>=defender.getLife() && defender.canLoseLife() && !defender.cantLoseForZeroOrLessLife())continue;
            if(ComputerUtilCombat.predictDamageTo(defender,incoming.getNetCombatDamage(),incoming,true)<=0)continue;
            if(best==null || ComputerUtilCard.evaluateCreature(old)<ComputerUtilCard.evaluateCreature(best)
                || (ComputerUtilCard.evaluateCreature(old)==ComputerUtilCard.evaluateCreature(best)&&old.getId()<best.getId()))best=old;
        }
        return best;
    }
    public static boolean beneficialProwler(Player ai, Card card, SpellAbility cast, SpellAbility trigger) {
        return "Nezumi Prowler".equals(card.getName()) && applies(ai,cast)
            && trigger.getApi()==ApiType.Pump && trigger.getSubAbility()==null
            && "Creature.YouCtrl".equals(trigger.getParam("ValidTgts"))
            && "Deathtouch & Lifelink".equals(trigger.getParam("KW"))
            && !trigger.hasParam("NumAtt") && !trigger.hasParam("NumDef")
            && ai.getGame().getCombat()!=null
            && chooseReturn(ai,cast,ai.getGame().getCombat().getUnblockedAttackers())!=null;
    }
}
