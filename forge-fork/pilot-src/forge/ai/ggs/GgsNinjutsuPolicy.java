package forge.ai.ggs;

import forge.ai.ComputerUtilCard;
import forge.ai.ComputerUtilCombat;
import forge.game.GameEntity;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.trigger.TriggerType;
import forge.game.zone.ZoneType;

/** Opt-in, deterministic heuristic. Uses public positions, never an opponent's hand/library. */
public final class GgsNinjutsuPolicy {
    private GgsNinjutsuPolicy() {}
    public record Plan(Card returned, int score, int dragonBonus, String reason) {}
    public static boolean enabled(Player ai) {
        return ai.getName().equals(System.getProperty("forge.ai.ggsPilotPlayer", ""));
    }
    public static Plan choose(Player ai, SpellAbility sa, Iterable<Card> candidates) {
        Combat combat = ai.getGame().getCombat();
        PhaseType phase = ai.getGame().getPhaseHandler().getPhase();
        // This version optimizes damage-producing swaps, not post-damage rescues/redeployment.
        if (combat == null || (phase != PhaseType.COMBAT_DECLARE_BLOCKERS
                && phase != PhaseType.COMBAT_FIRST_STRIKE_DAMAGE)) return null;
        Card incoming = sa.getHostCard();
        if (!incoming.ignoreLegendRule() && incoming.getType().isLegendary()
                && ai.isCardInPlay(incoming.getName())) return null;
        // A Ninja entering after first-strike damage was not present for that batch,
        // so it still deals regular combat damage even when it has first strike.
        java.util.List<Card> ggsCards = new java.util.ArrayList<>();
        for (Card c : ai.getCreaturesInPlay()) {
            if (CommanderEngineProfile.needsFreshCombatConnection(c)) ggsCards.add(c);
        }
        Plan best = null;
        for (Card outgoing : candidates) {
            if (outgoing.getController() != ai || !combat.isAttacking(outgoing)
                    || !combat.getUnblockedAttackers().contains(outgoing) || outgoing.isPhasedOut()) continue;
            // This policy only proposes offensive swaps. Removing the commander removes
            // the deck's repeatable engine, so a local damage/card advantage score cannot
            // justify it. Rescue/redeployment exceptions require a separate threat model.
            if (outgoing.isCommander() || CommanderEngineProfile.needsFreshCombatConnection(outgoing)) continue;
            // Before first strike, preserve double-strike attackers: two damage batches and
            // repeated triggers need a fuller forecast than this one-connection heuristic.
            if (phase == PhaseType.COMBAT_DECLARE_BLOCKERS && outgoing.hasKeyword(Keyword.DOUBLE_STRIKE)) continue;
            GameEntity defender = combat.getDefenderByAttacker(outgoing);
            if (!(defender instanceof Player opponent) || !opponent.isOpponentOf(ai)) continue;
            Card body = incoming;
            // Stock clone choice still determines the actual copy on resolution.
            if (incoming.getName().equals("Sakashima's Student")) {
                for (Card c : ai.getGame().getCardsIn(ZoneType.Battlefield)) {
                    if (c != outgoing && c.isCreature() && !c.isFaceDown() && !c.isPhasedOut()
                            && (!c.getType().isLegendary() || !ai.isCardInPlay(c.getName()))
                            && ComputerUtilCard.evaluateCreature(c) > ComputerUtilCard.evaluateCreature(body)) body = c;
                }
            }
            int incomingDamage = ComputerUtilCombat.predictDamageTo(opponent, Math.max(0, body.getNetCombatDamage()), body, true);
            int outgoingDamage = damageRemaining(outgoing, opponent, phase);
            if (incomingDamage <= 0) continue;
            // Preserve an already lethal connection; source printed power is not a lethal forecast.
            if (outgoingDamage >= opponent.getLife() && opponent.canLoseLife()
                    && !opponent.cantLoseForZeroOrLessLife()) continue;
            boolean freshConnection = outgoing.enteredThisTurn() && outgoingDamage > 0;
            for (Card other : combat.getUnblockedAttackers()) {
                if (other != outgoing && other.getController() == ai && other.enteredThisTurn()
                        && defender.equals(combat.getDefenderByAttacker(other))
                        && damageRemaining(other, opponent, phase) > 0) freshConnection = true;
            }
            boolean ggs = ggsCards.stream().anyMatch(c -> c != outgoing);
            if (CommanderEngineProfile.needsFreshCombatConnection(body)) ggs = true;
            DecisionWeights strategy = DecisionWeights.current();
            int dragon = ggs && !freshConnection ? strategy.dragon() : 0;
            int combatValue = hitValue(incoming, opponent, combat, outgoing) - (outgoingDamage > 0 ? hitValue(outgoing, opponent, combat, outgoing) : 0);
            int score = strategy.damage() * (incomingDamage - outgoingDamage) + combatValue * strategy.hitPercent() / 100 + dragon
                    + (ComputerUtilCard.evaluateCreature(body) - ComputerUtilCard.evaluateCreature(outgoing)) / strategy.bodyDivisor()
                    - outgoing.getCMC() * strategy.replay() - sa.getPayCosts().getTotalMana().getCMC() * strategy.mana();
            if (outgoing.isToken()) score -= ComputerUtilCard.evaluateCreature(outgoing) / 3;
            int lostEngine = switch (outgoing.getName()) {
                case "Goro-Goro and Satoru" -> 60;
                case "Satoru Umezawa" -> 40;
                case "Tetsuko Umezawa, Fugitive" -> 25;
                default -> 0;
            };
            score -= lostEngine;
            if (incomingDamage >= opponent.getLife() && opponent.canLoseLife()
                    && !opponent.cantLoseForZeroOrLessLife()) score += 1000;
            if (incoming.getName().equals("Thousand-Faced Shadow")) {
                int copyPower = 0;
                for (Card other : combat.getAttackers()) if (other != outgoing && other.getController() == ai)
                    copyPower = Math.max(copyPower, other.getNetCombatDamage());
                score += copyPower * 15;
            }
            if (best == null || score > best.score() || (score == best.score() && outgoing.getId() < best.returned().getId())) {
                best = new Plan(outgoing, score, dragon, "damageDelta=" + (incomingDamage - outgoingDamage)
                        + ",hitValueDelta=" + combatValue + ",additionalGgsDragon=" + (dragon > 0)
                        + ",activationMana=" + sa.getPayCosts().getTotalMana().getCMC()
                        + ",replayMana=" + outgoing.getCMC() + ",lostEngine=" + lostEngine + ",tokenLost=" + outgoing.isToken());
            }
        }
        return best;
    }
    private static int damageRemaining(Card c, Player defender, PhaseType phase) {
        if (phase == PhaseType.COMBAT_FIRST_STRIKE_DAMAGE && c.hasKeyword(Keyword.FIRST_STRIKE)
                && !c.hasKeyword(Keyword.DOUBLE_STRIKE)) return 0;
        return ComputerUtilCombat.predictDamageTo(defender, Math.max(0, c.getNetCombatDamage()), c, true);
    }
    private static int hitValue(Card c, Player opponent, Combat combat, Card returned) {
        // Explicit utility weights, not learned win probabilities or guaranteed card value.
        return switch (c.getName()) {
            case "Moon-Circuit Hacker", "Ninja of the Deep Hours" -> 35;
            case "Yuriko, the Tiger's Shadow" -> 45;
            case "Ingenious Infiltrator" -> {
                int hits = 1;
                for (Card other : combat.getUnblockedAttackers()) {
                    GameEntity defender = combat.getDefenderByAttacker(other);
                    if (other != returned && other.getController() == c.getController()
                            && other.getType().hasCreatureType("Ninja")
                            && defender instanceof Player player
                            && damageRemaining(other, player, c.getGame().getPhaseHandler().getPhase()) > 0) hits++;
                }
                yield 30 * hits;
            }
            case "Prosperous Thief" -> 30;
            case "Fallen Shinobi" -> 80;
            case "Higure, the Still Wind" -> 45;
            case "Silent-Blade Oni" -> opponent.getCardsIn(ZoneType.Hand).isEmpty() ? 0 : 60;
            case "Biting-Palm Ninja" -> opponent.getCardsIn(ZoneType.Hand).isEmpty() ? 0 : 35;
            case "Orochi Soul-Reaver" -> 50;
            case "Ink-Eyes, Servant of Oni" -> opponent.getCardsIn(ZoneType.Graveyard).anyMatch(Card::isCreature) ? 45 : 0;
            case "Throat Slitter" -> opponent.getCreaturesInPlay().anyMatch(x -> !x.isBlack()) ? 35 : 0;
            case "Balefire Dragon" -> opponent.getCreaturesInPlay().isEmpty() ? 0 : 80;
            case "Port Razer" -> 100;
            default -> 0;
        };
    }
}
