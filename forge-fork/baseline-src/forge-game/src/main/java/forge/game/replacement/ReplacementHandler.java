/*
 * Forge: Play Magic: the Gathering.
 * Copyright (C) 2011  Forge Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package forge.game.replacement;

import java.util.*;

import forge.game.card.*;
import forge.game.phase.PhaseType;

import org.apache.commons.lang3.StringUtils;

import com.google.common.collect.Lists;
import com.google.common.collect.Multiset;
import com.google.common.collect.Sets;

import forge.game.CardTraitBase;
import forge.game.Game;
import forge.game.GameEntity;
import forge.game.GameEntityCounterTable;
import forge.game.GameLogEntryType;
import forge.game.IHasSVars;
import forge.game.event.GameEventAddLog;
import forge.game.ability.AbilityFactory;
import forge.game.ability.AbilityKey;
import forge.game.ability.AbilityUtils;
import forge.game.ability.ApiType;
import forge.game.player.Player;
import forge.game.player.PlayerCollection;
import forge.game.spellability.AbilitySub;
import forge.game.spellability.Spell;
import forge.game.spellability.SpellAbility;
import forge.game.zone.Zone;
import forge.game.zone.ZoneType;
import forge.util.Localizer;
import forge.util.TextUtil;
import forge.util.Visitor;

public class ReplacementHandler {
    private final Game game;
    private static final class ManaSources {
        final Map<ReplacementType, CardCollection> sources = new EnumMap<>(ReplacementType.class);
        final Map<ZoneType, CardCollection[]> combatTraits = new EnumMap<>(ZoneType.class);
        final Map<Player, Map<ApiType, CardCollection>> combatDefenses = new IdentityHashMap<>();
        final Map<Player, CardCollection> keywordPumpHosts = new IdentityHashMap<>();
        final Map<Card, Map<Card, Boolean[]>> blockingEligibility = new IdentityHashMap<>();
        CardCollectionView combatAllRuleSources;
        CardCollection combatRuleSources;
        CardCollection combatReplacementRuleSources;
        ManaSources parent;
        boolean combat;
        boolean invalidated;
    }
    private final ThreadLocal<ManaSources> manaInspection = new ThreadLocal<>();

    public final class ManaInspection implements AutoCloseable {
        private final ManaSources previous;
        private boolean closed;
        private ManaInspection(ManaSources previous) { this.previous = previous; }
        @Override public void close() {
            if (closed) return;
            closed = true;
            if (previous == null) manaInspection.remove(); else manaInspection.set(previous);
        }
    }

    /** Scoped to AI source inspection before payment; never retains results across actions. */
    public ManaInspection beginReadOnlyManaInspection() {
        ManaSources previous = manaInspection.get();
        if (previous == null) {
            ManaSources snapshot = new ManaSources();
            snapshot.sources.put(ReplacementType.Tap, new CardCollection());
            snapshot.sources.put(ReplacementType.ProduceMana, new CardCollection());
            game.forEachCardInGame(card -> {
                for (ReplacementEffect effect : card.getReplacementEffects()) {
                    CardCollection list = snapshot.sources.get(effect.getMode());
                    if (list != null) list.add(card);
                }
                return true;
            });
            manaInspection.set(snapshot);
        }
        return new ManaInspection(previous);
    }

    public void invalidateReadOnlyManaInspection() {
        ManaSources snapshot = manaInspection.get();
        while (snapshot != null) {
            snapshot.invalidated = true;
            snapshot = snapshot.parent;
        }
    }

    /** One read-only AI search: cache hosts, never eligibility or damage results. */
    public ManaInspection beginReadOnlyCombatInspection() {
        ManaSources previous = manaInspection.get();
        if (!Boolean.getBoolean("dragonmind.disableCombatIndex")
                && (previous == null || previous.invalidated || !previous.combat)) {
            ManaSources snapshot = new ManaSources();
            snapshot.parent = previous;
            snapshot.combat = true;
            snapshot.sources.put(ReplacementType.DamageDone, null);
            snapshot.sources.put(ReplacementType.Tap, null);
            snapshot.sources.put(ReplacementType.Untap, null);
            snapshot.sources.put(ReplacementType.ProduceMana, null);
            manaInspection.set(snapshot);
        }
        return new ManaInspection(previous);
    }

    /** Scoped host discovery only; callers still read current traits and conditions. */
    public CardCollectionView getReadOnlyCombatTraitSources(ZoneType zone, boolean triggers) {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatTraitIndex")) return game.getCardsIn(zone);
        CardCollection[] sources = snapshot.combatTraits.get(zone);
        if (sources == null) {
            sources = new CardCollection[]{new CardCollection(), new CardCollection()};
            for (Card card : game.getCardsIn(zone)) {
                if (!card.getStaticAbilities().isEmpty()) sources[0].add(card);
                if (!card.getTriggers().isEmpty()) sources[1].add(card);
            }
            if (!snapshot.invalidated) snapshot.combatTraits.put(zone, sources);
        }
        // Trait synthesis can invalidate the enclosing query while discovering hosts.
        return snapshot.invalidated ? game.getCardsIn(zone) : sources[triggers ? 1 : 0];
    }

    /** Ordered complete source snapshot for callers whose extra-source dedup priority matters. */
    public CardCollectionView getReadOnlyCombatAllRuleSources() {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatRuleIndex")) {
            return game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES);
        }
        if (snapshot.combatAllRuleSources == null) {
            snapshot.combatAllRuleSources = game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES);
        }
        return snapshot.combatAllRuleSources;
    }

    /** Share ordered rule hosts in one forecast; applicability remains live. */
    public CardCollectionView getReadOnlyCombatRuleSources() {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatRuleIndex")) {
            return game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES);
        }
        if (snapshot.combatRuleSources == null) {
            CardCollection hosts = new CardCollection();
            // Preserve the original zone/player ordering and phased-card rules.
            for (Card card : getReadOnlyCombatAllRuleSources()) {
                if (!card.getStaticAbilities().isEmpty()) hosts.add(card);
            }
            if (!snapshot.invalidated) snapshot.combatRuleSources = hosts;
        }
        return snapshot.invalidated ? game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES)
            : snapshot.combatRuleSources;
    }

    /** Share ordered replacement hosts; modes, zones, amounts and conditions stay live. */
    public CardCollectionView getReadOnlyCombatReplacementRuleSources() {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatReplacementRuleIndex")) {
            return game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES);
        }
        if (snapshot.combatReplacementRuleSources == null) {
            CardCollection hosts = new CardCollection();
            for (Card card : getReadOnlyCombatAllRuleSources()) {
                if (!card.getReplacementEffects().isEmpty()) hosts.add(card);
            }
            if (!snapshot.invalidated) snapshot.combatReplacementRuleSources = hosts;
        }
        return snapshot.invalidated ? game.getCardsIn(ZoneType.STATIC_ABILITIES_SOURCE_ZONES)
                : snapshot.combatReplacementRuleSources;
    }

    /** Share defensive-ability hosts in a bounded forecast, not costs or targets. */
    public CardCollectionView getReadOnlyCombatDefenseSources(Player controller, ApiType api) {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatDefenseIndex")
                || (api != ApiType.Regenerate && api != ApiType.PreventDamage)) return controller.getCardsIn(ZoneType.Battlefield);
        Map<ApiType, CardCollection> sources = snapshot.combatDefenses.get(controller);
        if (sources == null) {
            sources = new EnumMap<>(ApiType.class);
            sources.put(ApiType.Regenerate, new CardCollection());
            sources.put(ApiType.PreventDamage, new CardCollection());
            for (Card card : controller.getCardsIn(ZoneType.Battlefield)) {
                for (SpellAbility ability : card.getSpellAbilities()) {
                    CardCollection hosts = sources.get(ability.getApi());
                    if (hosts != null) hosts.add(card);
                }
            }
            if (!snapshot.invalidated) snapshot.combatDefenses.put(controller, sources);
        }
        return snapshot.invalidated ? controller.getCardsIn(ZoneType.Battlefield) : sources.get(api);
    }

    /** Hosts only: keyword match, targeting, combat state and payment stay live. */
    public CardCollectionView getReadOnlyCombatKeywordPumpSources(Player controller) {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat
                || Boolean.getBoolean("dragonmind.disableCombatKeywordPumpIndex"))
            return controller.getCardsIn(ZoneType.Battlefield);
        CardCollection hosts = snapshot.keywordPumpHosts.get(controller);
        if (hosts == null) {
            hosts = new CardCollection();
            for (Card card : controller.getCardsIn(ZoneType.Battlefield)) {
                for (SpellAbility ability : card.getAllSpellAbilities()) {
                    if (ability.isActivatedAbility() && ability.getApi() == ApiType.Pump
                            && ability.hasParam("KW") && !ability.hasParam("ActivationPhases")
                            && !ability.hasParam("SorcerySpeed")) {
                        hosts.add(card);
                        break;
                    }
                }
            }
            if (!snapshot.invalidated) snapshot.keywordPumpHosts.put(controller, hosts);
        }
        return snapshot.invalidated ? controller.getCardsIn(ZoneType.Battlefield) : hosts;
    }

    /** Basic pair eligibility only, before actual combat; never assignment legality. */
    public boolean getReadOnlyPrecombatBlockEligibility(Card attacker, Card blocker,
            boolean nextTurn, java.util.function.Supplier<Boolean> calculate) {
        ManaSources snapshot = manaInspection.get();
        if (snapshot == null || snapshot.invalidated || !snapshot.combat || game.getCombat() != null
                || Boolean.getBoolean("dragonmind.disableCombatEligibilityCache")) return calculate.get();
        Map<Card, Boolean[]> byBlocker = snapshot.blockingEligibility.computeIfAbsent(attacker, c -> new IdentityHashMap<>());
        Boolean[] results = byBlocker.computeIfAbsent(blocker, c -> new Boolean[2]);
        int slot = nextTurn ? 1 : 0;
        if (results[slot] != null) return results[slot];
        boolean result = calculate.get();
        if (!snapshot.invalidated) results[slot] = result;
        return result;
    }

    private Set<ReplacementEffect> hasRun = Sets.newHashSet();

    // List of all replacement effect candidates for DamageDone event, in APNAP order
    private final List<Map<ReplacementEffect, List<Map<AbilityKey, Object>>>> replaceDamageList = new ArrayList<>();

    /**
     * ReplacementHandler.
     * @param gameState
     */
    public ReplacementHandler(Game gameState) {
        game = gameState;
    }

    public List<ReplacementEffect> getReplacementList(final ReplacementType event, final Map<AbilityKey, Object> runParams, final ReplacementLayer layer) {
        ManaSources snapshot = manaInspection.get();
        if (snapshot != null && !snapshot.invalidated && snapshot.combat
                && snapshot.sources.containsKey(event) && snapshot.sources.get(event) == null) {
            snapshot.sources.replaceAll((mode, hosts) -> new CardCollection());
            game.forEachCardInGame(card -> {
                for (ReplacementEffect effect : card.getReplacementEffects()) {
                    CardCollection hosts = snapshot.sources.get(effect.getMode());
                    if (hosts != null) hosts.add(card);
                }
                return true;
            });
        }
        CardCollectionView sources = snapshot == null || snapshot.invalidated ? null : snapshot.sources.get(event);
        return getReplacementList(event, runParams, layer, sources);
    }

    /** Sources for one read-only mana-source inspection, never a cross-action cache. */
    public CardCollectionView getManaReplacementSources() {
        CardCollection sources = new CardCollection();
        game.forEachCardInGame(card -> {
            for (ReplacementEffect effect : card.getReplacementEffects()) {
                if (effect.getMode() == ReplacementType.ProduceMana) {
                    sources.add(card);
                    break;
                }
            }
            return true;
        });
        return sources;
    }

    /** Conditions are reevaluated for every source and ability; only source membership is reused. */
    public List<ReplacementEffect> getManaReplacementList(final Map<AbilityKey, Object> runParams,
            final CardCollectionView sources) {
        return getReplacementList(ReplacementType.ProduceMana, runParams, ReplacementLayer.Other, sources);
    }

    private List<ReplacementEffect> getReplacementList(final ReplacementType event,
            final Map<AbilityKey, Object> runParams, final ReplacementLayer layer,
            final CardCollectionView candidateSources) {
        final CardCollection preList = new CardCollection();
        Card affectedLKI = null;
        Card affectedCard = null;

        if (ReplacementType.Moved.equals(event) && ZoneType.Battlefield.equals(runParams.get(AbilityKey.Destination))) {
            // if it was caused by an replacement effect, use the already calculated RE list
            // otherwise the RIOT card would cause a StackError
            final ReplacementEffect causeRE = (ReplacementEffect) runParams.get(AbilityKey.ReplacementEffect);
            if (causeRE != null && !causeRE.getOtherChoices().isEmpty()
                    && ReplacementType.Moved.equals(causeRE.getMode()) && layer.equals(causeRE.getLayer())) {
                // only return for same layer
                return causeRE.getOtherChoices();
            }

            // CR 614.12 ETB replacements look at what the card would be on the battlefield
            affectedCard = (Card) runParams.get(AbilityKey.Affected);
            // must force cache the CardState ETB replacements so the LKI copies them
            affectedCard.getReplacementEffects();
            affectedLKI = CardCopyService.getLKICopy(affectedCard);
            affectedLKI.setLastKnownZone(affectedCard.getController().getZone(ZoneType.Battlefield));

            // need to apply Counters to check its future state on the battlefield
            @SuppressWarnings("unchecked")
            Map<Optional<Player>, Multiset<CounterType>> etbCounters = (Map<Optional<Player>, Multiset<CounterType>>) runParams.get(AbilityKey.CounterMap);
            affectedLKI.putEtbCounters(etbCounters);
            preList.add(affectedLKI);
            game.getAction().checkStaticAbilities(false, Sets.newHashSet(), preList);

            runParams.put(AbilityKey.Affected, affectedLKI);
        }

        final List<ReplacementEffect> possibleReplacers = Lists.newArrayList();

        // Round up Static replacement effects
        Visitor<Card> inspect = crd -> {
            Card c = preList.get(crd);
            Zone cardZone = game.getZoneOf(c);

            // all tap/untap/produce mana replacements are active from the battlefield or the
            // command zone (e.g. Ood Sphere); skip other zones - this is a major hot path, as
            // canTap/canUntap run a cantHappenCheck per mana source per AI cost check, and
            // groupSourcesByManaColor runs a ProduceMana check per mana ability on top of that
            // (performance mode only, in case a custom card wants one active from elsewhere)
            if (Spell.isPerformanceMode()
                    && (event == ReplacementType.Tap || event == ReplacementType.Untap
                            || event == ReplacementType.ProduceMana)
                    && cardZone != null
                    && cardZone.getZoneType() != ZoneType.Battlefield
                    && cardZone.getZoneType() != ZoneType.Command) {
                return true;
            }

            // only when not prelist
            boolean noLKIstate = c != crd || event != ReplacementType.Moved || c.isImmutable() || runParams.get(AbilityKey.LastStateBattlefield) == null;
            if (!noLKIstate) {
                Card lastState = ((CardCollectionView) runParams.get(AbilityKey.LastStateBattlefield)).get(c);
                if (lastState != c) {
                    // use LKI because it has the right RE from the state before the effect started
                    c = lastState;
                    cardZone = lastState.getLastKnownZone();
                } else if (cardZone != null && cardZone.is(ZoneType.Battlefield)) {
                    // no LKI found so it shouldn't apply, this can happen during simultaneous zone changes
                    return true;
                }
            }

            for (final ReplacementEffect replacementEffect : c.getReplacementEffects()) {
                if (!replacementEffect.hasRun() && !hasRun.contains(replacementEffect)
                        && (layer == null || replacementEffect.getLayer() == layer)
                        && replacementEffect.modeCheck(event, runParams)
                        && !possibleReplacers.contains(replacementEffect)
                        && replacementEffect.zonesCheck(cardZone)
                        && replacementEffect.requirementsCheck(game)
                        && replacementEffect.canReplace(runParams)) {
                    possibleReplacers.add(replacementEffect);
                    if (layer == ReplacementLayer.CantHappen) {
                        return false;
                    }
                }
            }
            return true;
        };
        if (candidateSources == null) {
            game.forEachCardInGame(inspect, affectedCard != null && affectedCard.isInZone(ZoneType.Sideboard));
        } else {
            inspect.visitAll(candidateSources);
        }

        if (affectedLKI != null) {
            // need to set the Host Card there so it is not connected to LKI anymore?
            // need to be done after canReplace check
            for (final ReplacementEffect re : affectedLKI.getReplacementEffects()) {
                re.setHostCard(affectedCard);
            }
            // need to copy stored keywords from lki into real object to prevent the replacement effect from making new ones
            affectedCard.setStoredKeywords(affectedLKI.getStoredKeywords(), true);
            affectedCard.setStoredReplacements(affectedLKI.getStoredReplacements());
            if (affectedCard.getCastSA() != null && affectedCard.getCastSA().getKeyword() != null) {
                // need to readd the CastSA Keyword into the Card
                affectedCard.addKeywordForStaticAbility(affectedCard.getCastSA().getKeyword());
            }
            runParams.put(AbilityKey.Affected, affectedCard);
            runParams.put(AbilityKey.NewCard, CardCopyService.getLKICopy(affectedLKI));

            game.getAction().checkStaticAbilities(false);
        }

        return possibleReplacers;
    }

    public boolean cantHappenCheck(final ReplacementType event, final Map<AbilityKey, Object> runParams) {
        return !getReplacementList(event, runParams, ReplacementLayer.CantHappen).isEmpty();
    }

    /**
     *
     * Runs any applicable replacement effects.
     *
     * @param runParams
     *            the run params,same as for triggers.
     * @return ReplacementResult, an enum that represents what happened to the replacement effect.
     */
    public ReplacementResult run(ReplacementType event, final Map<AbilityKey, Object> runParams) {
        invalidateReadOnlyManaInspection();
        final Object affected = runParams.get(AbilityKey.Affected);
        Player decider = null;

        // Figure out who decides which of multiple replacements to apply
        // as well as whether or not to apply optional replacements.
        if (affected instanceof Player) {
            decider = (Player) affected;
        } else {
            decider = ((Card) affected).getController();
        }

        // try out all layer
        for (ReplacementLayer layer : ReplacementLayer.values()) {
            ReplacementResult res = run(event, runParams, layer, decider);
            if (res != ReplacementResult.NotReplaced) {
                return res;
            }
        }

        return ReplacementResult.NotReplaced;
    }

    private ReplacementResult run(final ReplacementType event, final Map<AbilityKey, Object> runParams, final ReplacementLayer layer, final Player decider) {
        final List<ReplacementEffect> possibleReplacers = getReplacementList(event, runParams, layer);

        if (possibleReplacers.isEmpty()) {
            return ReplacementResult.NotReplaced;
        }

        ReplacementEffect chosenRE;
        // "can't" is never a choice
        if (layer == ReplacementLayer.CantHappen) {
            chosenRE = possibleReplacers.get(0);
        } else {
            chosenRE = decider.getController().chooseSingleReplacementEffect(possibleReplacers);
        }

        possibleReplacers.remove(chosenRE);

        chosenRE.setHasRun(true);
        hasRun.add(chosenRE);
        chosenRE.setOtherChoices(possibleReplacers);
        ReplacementResult res = executeReplacement(runParams, chosenRE, decider);
        if (res == ReplacementResult.NotReplaced) {
            if (!possibleReplacers.isEmpty()) {
                res = run(event, runParams);
            }
            chosenRE.setHasRun(false);
            hasRun.remove(chosenRE);
            chosenRE.setOtherChoices(null);
            return res;
        }

        // Log there
        String message = chosenRE.getDescription();
        if (!StringUtils.isEmpty(message)) {
            game.fireEvent(new GameEventAddLog(GameLogEntryType.EFFECT_REPLACED, message));
        }

        // if its updated, try to call event again
        if (res == ReplacementResult.Updated) {
            Map<AbilityKey, Object> params = AbilityKey.newMap(runParams);
            params.remove(AbilityKey.ReplacementResult);

            // CR 614.16
            if (params.containsKey(AbilityKey.EffectOnly)) {
                params.put(AbilityKey.EffectOnly, true);
            }
            ReplacementResult result = run(event, params);
            switch (result) {
            case NotReplaced:
            case Updated: {
                runParams.putAll(params);
                // effect was updated
                runParams.put(AbilityKey.ReplacementResult, ReplacementResult.Updated);
                break;
            }
            default:
                // effect was replaced with something else
                res = result;
                runParams.put(AbilityKey.ReplacementResult, result);
                break;
            }
        }

        chosenRE.setHasRun(false);
        hasRun.remove(chosenRE);
        chosenRE.setOtherChoices(null);

        return res;
    }

    /**
     *
     * Runs a single replacement effect.
     *
     * @param replacementEffect
     *            the replacement effect to run
     */
    private ReplacementResult executeReplacement(final Map<AbilityKey, Object> runParams,
        final ReplacementEffect replacementEffect, final Player decider) {
        Card host = replacementEffect.getHostCard();
        // AlternateState for OriginsPlaneswalker
        // FaceDown for cards like Necropotence
        if (host.hasAlternateState() || host.isFaceDown()) {
            host = game.getCardState(host);
        }

        // TODO: the source of replacement effect should be the source of the original effect
        SpellAbility effectSA = replacementEffect.ensureAbility();
        if (effectSA != null) {
            SpellAbility tailend = effectSA;
            do {
                replacementEffect.setReplacingObjects(runParams, tailend);
                //set original Params to update them later
                tailend.setReplacingObject(AbilityKey.OriginalParams, runParams);
                tailend.setReplacingObjectsFrom(runParams, AbilityKey.InternalTriggerTable, AbilityKey.SimultaneousETB);
                tailend = tailend.getSubAbility();
            } while (tailend != null);

            effectSA.setLastStateBattlefield((CardCollectionView) Objects.requireNonNullElse(runParams.get(AbilityKey.LastStateBattlefield), game.getLastStateBattlefield()));
            effectSA.setLastStateGraveyard((CardCollectionView) Objects.requireNonNullElse(runParams.get(AbilityKey.LastStateGraveyard), game.getLastStateGraveyard()));
            if (replacementEffect.isIntrinsic()) {
                effectSA.setIntrinsic(true);
                effectSA.changeText();
            }
            effectSA.setReplacementEffect(replacementEffect);
        }

        // Decider gets to choose whether or not to apply the replacement.
        if (replacementEffect.hasParam("Optional")) {
            Player optDecider = decider;
            if (replacementEffect.hasParam("OptionalDecider")) {
                optDecider = AbilityUtils.getDefinedPlayers(host, replacementEffect.getParam("OptionalDecider"), effectSA).get(0);
            }

            String name = Objects.requireNonNullElse(host.getRenderForUI() ? host.getCardForUi() : null, host).getTranslatedName();
            String effectDesc = TextUtil.fastReplace(replacementEffect.getDescription(), "CARDNAME", name);
            final String question = runParams.containsKey(AbilityKey.Card)
                ? Localizer.getInstance().getMessage("lblApplyCardReplacementEffectToCardConfirm", name, runParams.get(AbilityKey.Card).toString(), effectDesc)
                : Localizer.getInstance().getMessage("lblApplyReplacementEffectOfCardConfirm", name, effectDesc);
            GameEntity affected = (GameEntity) runParams.get(AbilityKey.Affected);
            boolean confirmed = optDecider.getController().confirmReplacementEffect(replacementEffect, effectSA, affected, question);
            if (!confirmed) {
                return ReplacementResult.NotReplaced;
            }
        }

        boolean isPrevent = "True".equals(replacementEffect.getParam("Prevent"));
        if (isPrevent || replacementEffect.hasParam("PreventionEffect")) {
            if (Boolean.TRUE.equals(runParams.get(AbilityKey.NoPreventDamage))) {
                // If can't prevent damage, result is not replaced
                // But still put "prevented" amount for buffered SA
                if (replacementEffect.hasParam("AlwaysReplace")) {
                    runParams.put(AbilityKey.PreventedAmount, runParams.get(AbilityKey.DamageAmount));
                } else {
                    runParams.put(AbilityKey.PreventedAmount, 0);
                }
                return ReplacementResult.NotReplaced;
            }
            if (isPrevent) {
                return ReplacementResult.Prevented; // Nothing should replace the event.
            }
        }

        if ("True".equals(replacementEffect.getParam("Skip"))) {
            return ReplacementResult.Skipped;
        }
        Player player = host.getController();

        if (effectSA != null) {
            ApiType apiType = effectSA.getApi();
            if (replacementEffect.getMode() != ReplacementType.DamageDone ||
                (apiType == ApiType.ReplaceDamage || apiType == ApiType.ReplaceSplitDamage || apiType == ApiType.ReplaceEffect)) {
                effectSA.setActivatingPlayer(host.getController());
                player.getController().playSpellAbilityNoStack(effectSA, true);
            } else {
                // The SA if buffered, but replacement result should be set to Replaced
                runParams.put(AbilityKey.ReplacementResult, ReplacementResult.Replaced);
            }

            // these ones are special for updating
            if (apiType == ApiType.ReplaceToken || apiType == ApiType.ReplaceEffect || apiType == ApiType.ReplaceMana) {
                runParams.put(AbilityKey.ReplacementResult, ReplacementResult.Updated);
            }
        }

        if (replacementEffect.hasParam("ReplacementResult")) {
            return ReplacementResult.valueOf(replacementEffect.getParam("ReplacementResult")); // Event is replaced without SA.
        }

        // if the spellability is a replace effect then its some new logic
        // if ReplacementResult is set in run params use that instead
        if (runParams.containsKey(AbilityKey.ReplacementResult)) {
            return (ReplacementResult) runParams.get(AbilityKey.ReplacementResult);
        }

        return ReplacementResult.Replaced;
    }

    private void getPossibleReplaceDamageList(PlayerCollection players, final boolean isCombat, final CardDamageTable damageMap, final SpellAbility cause) {
        for (Map.Entry<GameEntity, Map<Card, Integer>> et : damageMap.columnMap().entrySet()) {
            final GameEntity target = et.getKey();
            int playerIndex = target instanceof Player ? players.indexOf(((Player) target)) :
                                players.indexOf(((Card) target).getController());
            if (playerIndex == -1) continue;
            Map<ReplacementEffect, List<Map<AbilityKey, Object>>> replaceCandidateMap = replaceDamageList.get(playerIndex);
            for (Map.Entry<Card, Integer> e : et.getValue().entrySet()) {
                Card source = e.getKey();
                Integer damage = e.getValue();
                if (damage > 0) {
                    boolean prevention = source.canDamagePrevented(isCombat) &&
                                            (cause == null || !cause.hasParam("NoPrevention"));
                    final Map<AbilityKey, Object> repParams = AbilityKey.mapFromAffected(target);
                    repParams.put(AbilityKey.DamageSource, source);
                    repParams.put(AbilityKey.DamageAmount, damage);
                    repParams.put(AbilityKey.IsCombat, isCombat);
                    repParams.put(AbilityKey.NoPreventDamage, !prevention);
                    if (cause != null) {
                        repParams.put(AbilityKey.Cause, cause);
                    }

                    List<ReplacementEffect> reList = getReplacementList(ReplacementType.DamageDone, repParams, ReplacementLayer.Other);
                    for (ReplacementEffect re : reList) {
                        if (!replaceCandidateMap.containsKey(re)) {
                            replaceCandidateMap.put(re, new ArrayList<>());
                        }
                        List<Map<AbilityKey, Object>> runParamList = replaceCandidateMap.get(re);
                        runParamList.add(repParams);
                    }
                }
            }
        }
    }

    private void runSingleReplaceDamageEffect(ReplacementEffect re, Map<AbilityKey, Object> runParams, Map<ReplacementEffect, List<Map<AbilityKey, Object>>> replaceCandidateMap,
                                              Map<ReplacementEffect, List<Map<AbilityKey, Object>>> executedDamageMap, Player decider, final CardDamageTable damageMap, final CardDamageTable preventMap) {
        List<Map<AbilityKey, Object>> executedParamList = executedDamageMap.get(re);
        ApiType apiType = re.getOverridingAbility() != null ? re.getOverridingAbility().getApi() : null;
        Card source = (Card) runParams.get(AbilityKey.DamageSource);
        GameEntity target = (GameEntity) runParams.get(AbilityKey.Affected);
        int damage = (int) runParams.get(AbilityKey.DamageAmount);
        Map<String, String> mapParams = re.getMapParams();

        ReplacementResult res = executeReplacement(runParams, re, decider);
        GameEntity newTarget = (GameEntity) runParams.get(AbilityKey.Affected);
        int newDamage = (int) runParams.get(AbilityKey.DamageAmount);

        // ReplaceSplitDamage will split the damage event into two event, so need to create run params for old event
        // (original run params is changed for new event)
        Map<AbilityKey, Object> oldParams = null;

        if (res != ReplacementResult.NotReplaced) {
            // Remove this event from other possible replacers
            Iterator<Map.Entry<ReplacementEffect, List<Map<AbilityKey, Object>>>> itr = replaceCandidateMap.entrySet().iterator();
            while (itr.hasNext()) {
                Map.Entry<ReplacementEffect, List<Map<AbilityKey, Object>>> entry = itr.next();
                if (entry.getKey() == re) continue;
                if (entry.getValue().contains(runParams)) {
                    entry.getValue().remove(runParams);
                    if (entry.getValue().isEmpty()) {
                        itr.remove();
                    }
                }
            }
            // Add updated event to possible replacers
            if (res == ReplacementResult.Updated || apiType == ApiType.ReplaceSplitDamage) {
                Map<ReplacementEffect, List<Map<AbilityKey, Object>>> newReplaceCandidateMap = replaceCandidateMap;
                if (!target.equals(newTarget)) {
                    PlayerCollection players = game.getPlayersInTurnOrder();
                    int playerIndex = newTarget instanceof Player ? players.indexOf(((Player) newTarget)) :
                                       players.indexOf(((Card) newTarget).getController());
                    newReplaceCandidateMap = replaceDamageList.get(playerIndex);
                }

                List<ReplacementEffect> reList = getReplacementList(ReplacementType.DamageDone, runParams, ReplacementLayer.Other);
                for (ReplacementEffect newRE : reList) {
                    // Skip if this has already been executed by given replacement effect
                    if (executedDamageMap.containsKey(newRE) && executedDamageMap.get(newRE).contains(runParams)) {
                        continue;
                    }
                    if (!newReplaceCandidateMap.containsKey(newRE)) {
                        newReplaceCandidateMap.put(newRE, new ArrayList<>());
                    }
                    List<Map<AbilityKey, Object>> runParamList = newReplaceCandidateMap.get(newRE);
                    runParamList.add(runParams);
                }
            }
            // Add old updated event too for ReplaceSplitDamage
            if (apiType == ApiType.ReplaceSplitDamage && res == ReplacementResult.Updated) {
                oldParams = AbilityKey.newMap(runParams);
                oldParams.put(AbilityKey.Affected, target);
                oldParams.put(AbilityKey.DamageAmount, damage - newDamage);
                List<ReplacementEffect> reList = getReplacementList(ReplacementType.DamageDone, oldParams, ReplacementLayer.Other);
                for (ReplacementEffect newRE : reList) {
                    if (!replaceCandidateMap.containsKey(newRE)) {
                        replaceCandidateMap.put(newRE, new ArrayList<>());
                    }
                    List<Map<AbilityKey, Object>> runParamList = replaceCandidateMap.get(newRE);
                    runParamList.add(oldParams);
                }
            }
        }

        @SuppressWarnings("unchecked")
        Map<ReplacementEffect, ReplacementResult> resultMap = (Map<ReplacementEffect, ReplacementResult>) runParams.get(AbilityKey.ReplacementResultMap);
        resultMap.put(re, res);

        // Update damage map and prevent map
        switch (res) {
        case NotReplaced:
            break;
        case Updated:
            // check if this is still the affected card or player
            if (target.equals(newTarget)) {
                damageMap.put(source, target, newDamage - damage);
            } else if (apiType == ApiType.ReplaceSplitDamage) {
                damageMap.put(source, target, -newDamage);
            }
            if (!target.equals(newTarget)) {
                if (apiType != ApiType.ReplaceSplitDamage) {
                    damageMap.remove(source, target);
                }
                damageMap.put(source, newTarget, newDamage);
            }
            if (apiType == ApiType.ReplaceDamage) {
                preventMap.put(source, target, damage - newDamage);
                // Record prevented amount
                runParams.put(AbilityKey.PreventedAmount, damage - newDamage);
            }
            break;
        default:
            damageMap.remove(source, target);
            if (apiType == ApiType.ReplaceDamage ||
                    (mapParams.containsKey("Prevent") && mapParams.get("Prevent").equals("True")) ||
                    mapParams.containsKey("PreventionEffect")) {
                preventMap.put(source, target, damage);
                // Record prevented amount
                runParams.put(AbilityKey.PreventedAmount, damage);
            }
            if (apiType == ApiType.ReplaceSplitDamage) {
                damageMap.put(source, newTarget, newDamage);
            }
        }

        // Put run params into executed param list so this replacement effect won't handle them again
        // (For example, if the damage is redirected back)
        executedParamList.add(runParams);
        if (apiType == ApiType.ReplaceSplitDamage) {
            executedParamList.add(oldParams);
        }

        // Log the replacement effect
        if (res != ReplacementResult.NotReplaced) {
            String message = re.getDescription();
            if (!StringUtils.isEmpty(message)) {
                game.fireEvent(new GameEventAddLog(GameLogEntryType.EFFECT_REPLACED, message));
            }
        }
    }

    private void executeReplaceDamageBufferedSA(Map<ReplacementEffect, List<Map<AbilityKey, Object>>> executedDamageMap) {
        for (Map.Entry<ReplacementEffect, List<Map<AbilityKey, Object>>> entry : executedDamageMap.entrySet()) {
            ReplacementEffect re = entry.getKey();
            if (re.getOverridingAbility() == null) {
                continue;
            }
            SpellAbility bufferedSA = re.getOverridingAbility();
            ApiType apiType = bufferedSA.getApi();
            if (apiType == ApiType.ReplaceDamage || apiType == ApiType.ReplaceSplitDamage || apiType == ApiType.ReplaceEffect) {
                bufferedSA = bufferedSA.getSubAbility();
                if (bufferedSA == null) {
                    continue;
                }
            }

            List<Map<AbilityKey, Object>> executedParamList = entry.getValue();
            if (executedParamList.isEmpty()) {
                continue;
            }

            Map<String, String> mapParams = re.getMapParams();
            boolean isPrevention = (mapParams.containsKey("Prevent") && mapParams.get("Prevent").equals("True")) || mapParams.containsKey("PreventionEffect");
            boolean executePerSource = mapParams.containsKey("ExecuteMode") && mapParams.get("ExecuteMode").equals("PerSource");
            boolean executePerTarget = mapParams.containsKey("ExecuteMode") && mapParams.get("ExecuteMode").equals("PerTarget");

            while (!executedParamList.isEmpty()) {
                Map<AbilityKey, Object> runParams = AbilityKey.newMap();
                List<Card> damageSourceList = new ArrayList<>();
                List<GameEntity> affectedList = new ArrayList<>();
                int damageSum = 0;

                Iterator<Map<AbilityKey, Object>> itr = executedParamList.iterator();
                while (itr.hasNext()) {
                    Map<AbilityKey, Object> executedParams = itr.next();

                    @SuppressWarnings("unchecked")
                    Map<ReplacementEffect, ReplacementResult> resultMap = (Map<ReplacementEffect, ReplacementResult>) executedParams.get(AbilityKey.ReplacementResultMap);
                    ReplacementResult res = resultMap.get(re);
                    if (res == ReplacementResult.NotReplaced && (!isPrevention || Boolean.FALSE.equals(executedParams.get(AbilityKey.NoPreventDamage)))) {
                        itr.remove();
                        continue;
                    }

                    Card source = (Card) executedParams.get(AbilityKey.DamageSource);
                    if (executePerSource && !damageSourceList.isEmpty() && !damageSourceList.contains(source)) {
                        continue;
                    }

                    GameEntity target = (GameEntity) executedParams.get(AbilityKey.Affected);
                    if (executePerTarget && !affectedList.isEmpty() && !affectedList.contains(target)) {
                        continue;
                    }

                    itr.remove();
                    int damage = (int) executedParams.get(isPrevention ? AbilityKey.PreventedAmount : AbilityKey.DamageAmount);
                    if (!damageSourceList.contains(source)) {
                        damageSourceList.add(source);
                    }
                    if (!affectedList.contains(target)) {
                        affectedList.add(target);
                    }
                    damageSum += damage;
                }

                if (damageSum > 0) {
                    runParams.put(AbilityKey.DamageSource, damageSourceList.size() > 1 ? damageSourceList : damageSourceList.get(0));
                    runParams.put(AbilityKey.Affected, affectedList.size() > 1 ? affectedList : affectedList.get(0));
                    runParams.put(AbilityKey.DamageAmount, damageSum);

                    re.setReplacingObjects(runParams, re.getOverridingAbility());
                    bufferedSA.setActivatingPlayer(re.getHostCard().getController());
                    AbilityUtils.resolve(bufferedSA);
                }
            }
        }
    }

    public void runReplaceDamage(final boolean isCombat, final CardDamageTable damageMap, final CardDamageTable preventMap,
                                 final GameEntityCounterTable counterTable, final SpellAbility cause) {
        PlayerCollection players = game.getPlayersInTurnOrder();
        for (int i = 0; i < players.size(); i++) {
            replaceDamageList.add(new HashMap<>());
        }

        // Map of all executed replacement effect for DamageDone event, including run params
        Map<ReplacementEffect, List<Map<AbilityKey, Object>>> executedDamageMap = new HashMap<>();

        // First, gather all possible replacement effects
        getPossibleReplaceDamageList(players, isCombat, damageMap, cause);

        // Next, handle replacement effects in APNAP order
        // Handle "Prevented this way" and abilities like "Phantom Nomad", by buffer the replaced SA
        // and only run them after all prevention and redirection effects are processed.
        while (true) {
            Player decider = null;
            Map<ReplacementEffect, List<Map<AbilityKey, Object>>> replaceCandidateMap = null;
            for (int i = 0; i < players.size(); i++) {
                if (replaceDamageList.get(i).isEmpty()) continue;
                decider = players.get(i);
                replaceCandidateMap = replaceDamageList.get(i);
                break;
            }
            if (replaceCandidateMap == null) {
                break;
            }

            List<ReplacementEffect> possibleReplacers = new ArrayList<>(replaceCandidateMap.keySet());
            // TODO should be able to choose different order for each entity
            ReplacementEffect chosenRE = decider.getController().chooseSingleReplacementEffect(possibleReplacers);
            List<Map<AbilityKey, Object>> runParamList = replaceCandidateMap.get(chosenRE);

            if (!executedDamageMap.containsKey(chosenRE)) {
                executedDamageMap.put(chosenRE, new ArrayList<>());
            }

            // Run all possible events for chosen replacement effect
            chosenRE.setHasRun(true);
            SpellAbility effectSA = chosenRE.getOverridingAbility();
            ApiType apiType = null;
            SpellAbility bufferedSA = effectSA;
            boolean needRestoreSubSA = false;
            boolean needDivideShield = false;
            boolean needChooseSource = false;
            int shieldAmount = 0;
            if (effectSA != null) {
                apiType = effectSA.getApi();
                // Temporary remove sub ability from ReplaceDamage, ReplaceSplitDamage and ReplaceEffect API so they could be run later
                if (apiType == ApiType.ReplaceDamage || apiType == ApiType.ReplaceSplitDamage || apiType == ApiType.ReplaceEffect) {
                    bufferedSA = effectSA.getSubAbility();
                    if (bufferedSA != null) {
                        needRestoreSubSA = true;
                        effectSA.setSubAbility(null);
                    }
                }

                // Determine if need to divide shield among affected entity and
                // determine if the prevent next N damage shield is large enough to replace all damage
                if ((chosenRE.hasParam("PreventionEffect") && chosenRE.getParam("PreventionEffect").equals("NextN"))
                        || apiType == ApiType.ReplaceSplitDamage) {
                    if (apiType == ApiType.ReplaceDamage) {
                        shieldAmount = AbilityUtils.calculateAmount(effectSA.getHostCard(), effectSA.getParamOrDefault("Amount", "1"), effectSA);
                    } else if (apiType == ApiType.ReplaceSplitDamage) {
                        shieldAmount = AbilityUtils.calculateAmount(effectSA.getHostCard(), effectSA.getParamOrDefault("VarName", "1"), effectSA);
                    }
                    int damageAmount = 0;
                    boolean hasMultipleSource = false;
                    boolean hasMultipleTarget = false;
                    Card firstSource = null;
                    GameEntity firstTarget = null;
                    for (Map<AbilityKey, Object> runParams : runParamList) {
                        // Only count damage that can be prevented
                        if (apiType == ApiType.ReplaceDamage && Boolean.TRUE.equals(runParams.get(AbilityKey.NoPreventDamage))) continue;
                        damageAmount += (int) runParams.get(AbilityKey.DamageAmount);
                        if (firstSource == null) {
                            firstSource = (Card) runParams.get(AbilityKey.DamageSource);
                        } else if (!firstSource.equals(runParams.get(AbilityKey.DamageSource))) {
                            hasMultipleSource = true;
                        }
                        if (firstTarget == null) {
                            firstTarget = (GameEntity) runParams.get(AbilityKey.Affected);
                        } else if (!firstTarget.equals(runParams.get(AbilityKey.Affected))) {
                            hasMultipleTarget = true;
                        }
                    }
                    if (damageAmount > shieldAmount && runParamList.size() > 1) {
                        if (hasMultipleSource)
                            needChooseSource = true;
                        if (effectSA.hasParam("DivideShield") && hasMultipleTarget)
                            needDivideShield = true;
                    }
                }
            }

            // Ask the decider to divide shield among affected damage target
            Map<GameEntity, Integer> shieldMap = null;
            if (needDivideShield) {
                Map<GameEntity, Integer> affected = new HashMap<>();
                for (Map<AbilityKey, Object> runParams : runParamList) {
                    GameEntity target = (GameEntity) runParams.get(AbilityKey.Affected);
                    Integer damage = (Integer) runParams.get(AbilityKey.DamageAmount);
                    affected.merge(target, damage, Integer::sum);
                }
                shieldMap = decider.getController().divideShield(chosenRE.getHostCard(), affected, shieldAmount);
            }

            // CR 615.7
            // If damage would be dealt to the shielded permanent or player by two or more applicable sources at the same time,
            // the player or the controller of the permanent chooses which damage the shield prevents.
            if (needChooseSource) {
                CardCollection sourcesToChooseFrom = new CardCollection();
                for (Map<AbilityKey, Object> runParams : runParamList) {
                    if (apiType == ApiType.ReplaceDamage && Boolean.TRUE.equals(runParams.get(AbilityKey.NoPreventDamage))) continue;
                    sourcesToChooseFrom.add((Card) runParams.get(AbilityKey.DamageSource));
                }
                final String choiceTitle = Localizer.getInstance().getMessage("lblChooseSource") + " ";
                while (shieldAmount > 0 && !sourcesToChooseFrom.isEmpty()) {
                    Card source = decider.getController().chooseSingleEntityForEffect(sourcesToChooseFrom, effectSA, choiceTitle, null);
                    sourcesToChooseFrom.remove(source);
                    Iterator<Map<AbilityKey, Object>> itr = runParamList.iterator();
                    while (itr.hasNext()) {
                        Map<AbilityKey, Object> runParams = itr.next();
                        if (source.equals(runParams.get(AbilityKey.DamageSource))) {
                            itr.remove();
                            if (shieldMap != null) {
                                GameEntity target = (GameEntity) runParams.get(AbilityKey.Affected);
                                if (shieldMap.containsKey(target) && shieldMap.get(target) > 0) {
                                    Integer dividedShieldAmount = shieldMap.get(target);
                                    runParams.put(AbilityKey.DividedShieldAmount, dividedShieldAmount);
                                    shieldAmount -= dividedShieldAmount;
                                } else {
                                    continue;
                                }
                            } else {
                                shieldAmount -= (int) runParams.get(AbilityKey.DamageAmount);
                            }
                            if (!runParams.containsKey(AbilityKey.ReplacementResultMap)) {
                                Map<ReplacementEffect, ReplacementResult> resultMap = new HashMap<>();
                                runParams.put(AbilityKey.ReplacementResultMap, resultMap);
                            }
                            runSingleReplaceDamageEffect(chosenRE, runParams, replaceCandidateMap, executedDamageMap, decider, damageMap, preventMap);
                        }
                    }
                }
            } else {
                for (Map<AbilityKey, Object> runParams : runParamList) {
                    if (shieldMap != null) {
                        GameEntity target = (GameEntity) runParams.get(AbilityKey.Affected);
                        if (shieldMap.containsKey(target) && shieldMap.get(target) > 0) {
                            Integer dividedShieldAmount = shieldMap.get(target);
                            runParams.put(AbilityKey.DividedShieldAmount, dividedShieldAmount);
                        } else {
                            continue;
                        }
                    }
                    if (!runParams.containsKey(AbilityKey.ReplacementResultMap)) {
                        Map<ReplacementEffect, ReplacementResult> resultMap = new HashMap<>();
                        runParams.put(AbilityKey.ReplacementResultMap, resultMap);
                    }
                    runSingleReplaceDamageEffect(chosenRE, runParams, replaceCandidateMap, executedDamageMap, decider, damageMap, preventMap);
                }
            }

            // Restore temporary removed SA
            if (needRestoreSubSA) {
                effectSA.setSubAbility((AbilitySub)bufferedSA);
            }
            chosenRE.setHasRun(false);
            replaceCandidateMap.remove(chosenRE);
        }

        replaceDamageList.clear();

        // Finally, run all buffered SA to finish the replacement processing
        executeReplaceDamageBufferedSA(executedDamageMap);
    }

    /**
     *
     * Creates an instance of the proper replacement effect object based on raw
     * script.
     *
     * @param repParse
     *            A raw line of script
     * @param host
     *            The cards that hosts the replacement effect.
     * @return A finished instance
     */
    public static ReplacementEffect parseReplacement(final String repParse, final Card host, final boolean intrinsic) {
        return parseReplacement(repParse, host, intrinsic, host);
    }
    public static ReplacementEffect parseReplacement(final String repParse, final Card host, final boolean intrinsic, final IHasSVars sVarHolder) {
        return ReplacementHandler.parseReplacement(AbilityFactory.getMapParams(repParse), host, intrinsic, sVarHolder);
    }

    /**
     *
     * Creates an instance of the proper replacement effect object based on a
     * parsed script.
     *
     * @param mapParams
     *            The parsed script
     * @param host
     *            The card that hosts the replacement effect
     * @return The finished instance
     */
    private static ReplacementEffect parseReplacement(final Map<String, String> mapParams, final Card host, final boolean intrinsic, final IHasSVars sVarHolder) {
        final ReplacementType rt = ReplacementType.smartValueOf(mapParams.get("Event"));
        ReplacementEffect ret = rt.createReplacement(mapParams, host, intrinsic);

        String activeZones = mapParams.get("ActiveZones");
        if (null != activeZones) {
            ret.setActiveZone(EnumSet.copyOf(ZoneType.listValueOf(activeZones)));
        }

        if (mapParams.containsKey("ReplaceWith") && sVarHolder != null) {
            ret.setOverridingAbility(AbilityFactory.getAbility(host, mapParams.get("ReplaceWith"), sVarHolder));
        }

        if (sVarHolder instanceof CardState) {
            ret.setCardState((CardState)sVarHolder);
        } else if (sVarHolder instanceof CardTraitBase) {
            ret.setCardState(((CardTraitBase)sVarHolder).getCardState());
        }
        return ret;
    }

    /**
     * Helper function to check if a phase would be skipped for AI.
     */
    public boolean wouldPhaseBeSkipped(final Player player, final PhaseType phase) {
        final Map<AbilityKey, Object> repParams = AbilityKey.mapFromAffected(player);
        repParams.put(AbilityKey.Phase, phase);
        List<ReplacementEffect> list = getReplacementList(ReplacementType.BeginPhase, repParams, ReplacementLayer.Control);
        if (list.isEmpty()) {
            return false;
        }
        return true;
    }

    /**
     * Helper function to check if an extra turn would be skipped for AI.
     */
    public boolean wouldExtraTurnBeSkipped(final Player player) {
        final Map<AbilityKey, Object> repParams = AbilityKey.mapFromAffected(player);
        repParams.put(AbilityKey.ExtraTurn, true);
        List<ReplacementEffect> list = getReplacementList(ReplacementType.BeginTurn, repParams, ReplacementLayer.Other);
        if (list.isEmpty()) {
            return false;
        }
        return true;
    }

    /**
     * Helper function to get total prevention shield amount (limited to "prevent next N damage effects")
     * @param o Affected game entity object
     * @return total shield amount
     */
    public int getTotalPreventionShieldAmount(GameEntity o) {
        final List<ReplacementEffect> list = Lists.newArrayList();
        game.forEachCardInGame(new Visitor<Card>() {
            @Override
            public boolean visit(Card c) {
                for (final ReplacementEffect re : c.getReplacementEffects()) {
                    if (re.getMode() == ReplacementType.DamageDone
                            && re.getLayer() == ReplacementLayer.Other
                            && re.hasParam("PreventionEffect")
                            && re.zonesCheck(game.getZoneOf(c))
                            && re.getOverridingAbility() != null
                            && re.getOverridingAbility().getApi() == ApiType.ReplaceDamage
                            && re.matchesValidParam("ValidTarget", o)) {
                        list.add(re);
                    }
                }
                return true;
            }

        });

        int totalAmount = 0;
        for (ReplacementEffect re : list) {
            SpellAbility sa = re.getOverridingAbility();
            if (sa.hasParam("Amount")) {
                String varValue = sa.getParam("Amount");
                if (StringUtils.isNumeric(varValue)) {
                    totalAmount += Integer.parseInt(varValue);
                } else {
                    varValue = sa.getSVar(varValue);
                    if (varValue.startsWith("Number$")) {
                        totalAmount += Integer.parseInt(varValue.substring(7));
                    }
                }
            }
        }
        return totalAmount;
    }

    /**
     * Helper function to check if combat damage is prevented this turn (fog effect)
     * @return true if there is some resolved fog effect
     */
    public final boolean isPreventCombatDamageThisTurn() {
        // a fog effect can only be active from a zone in STATIC_ABILITIES_SOURCE_ZONES
        // (zonesCheck below rejects other zones), so don't scan libraries and hands
        for (final Card c : getReadOnlyCombatReplacementRuleSources()) {
            for (final ReplacementEffect re : c.getReplacementEffects()) {
                if (re.getMode() == ReplacementType.DamageDone
                        && re.getLayer() == ReplacementLayer.Other
                        && "True".equals(re.getParam("Prevent"))
                        && "True".equals(re.getParam("IsCombat"))
                        && !re.hasParam("ValidSource") && !re.hasParam("ValidTarget")
                        && re.zonesCheck(game.getZoneOf(c))) {
                    return true;
                }
            }
        }
        return false;
    }

    public boolean isReplacing() {
        return !hasRun.isEmpty();
    }
}
