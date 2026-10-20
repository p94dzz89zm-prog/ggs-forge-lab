package forge.ai.bridge;

import com.google.gson.*;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbilityStackInstance;
import forge.game.zone.ZoneType;

/** Conservative player view: never exports library order or opponents' hands. */
public final class BridgeSnapshot {
    private BridgeSnapshot() {}
    public static JsonObject entity(GameEntity entity, Player viewer) {
        JsonObject out=new JsonObject(); out.addProperty("id",entity.getId());
        if(entity instanceof Card c) {
            boolean privateZone=c.isInZone(ZoneType.Library) || (c.isInZone(ZoneType.Hand) && c.getOwner()!=viewer);
            boolean hidden=privateZone || (c.isFaceDown() && c.getController()!=viewer);
            out.addProperty("name",hidden ? "Face-down card" : c.getName());
            out.addProperty("face_down",c.isFaceDown());
            boolean controlled=c.isInZone(ZoneType.Battlefield)||c.isInZone(ZoneType.Stack);
            out.addProperty("controller_id",controlled?c.getController().getId():c.getOwner().getId());
            out.addProperty("controller_basis",controlled?"actual_controller":"owner_outside_battlefield_or_stack");
            out.addProperty("owner_id",c.getOwner().getId());
            out.addProperty("zone",String.valueOf(c.getZone()==null ? null : c.getZone().getZoneType()));
            out.addProperty("token",c.isToken());
            out.addProperty("tapped",c.isTapped());
            if(!hidden) { out.addProperty("type",c.getType().toString());out.addProperty("mana_cost",c.getManaCost().toString()); }
            // Printed characteristics of an opponent's face-down card remain hidden.
            if(!privateZone) {out.addProperty("power",c.getNetPower());out.addProperty("toughness",c.getNetToughness());out.addProperty("summoning_sick",c.hasSickness());}
            if(!privateZone) {
                JsonObject counters=new JsonObject();
                for(var counter:c.getCounters().entrySet())counters.addProperty(counter.getElement().getName(),counter.getCount());
                out.add("counters",counters);out.addProperty("marked_damage",c.getDamage());
            }
            if(!hidden) {
                JsonArray chosen=new JsonArray();if(c.getChosenColors()!=null)for(String color:c.getChosenColors())chosen.add(color);
                out.add("chosen_colors",chosen);
                out.addProperty("commander",c.isCommander());
                out.addProperty("entered_this_turn",c.enteredThisTurn());
                // Formatting live abilities may inspect modal targets before an activating player exists.
                // Snapshot current-face Oracle text without evaluating those live ability descriptions.
                out.addProperty("rules_text",c.getOracleText());
                out.addProperty("rules_text_kind","oracle_current_face");
                out.addProperty("phased_out",c.isPhasedOut());
                JsonArray keywords=new JsonArray();
                for(var keyword:c.getKeywords())keywords.add(keyword.getOriginal());
                out.add("keywords",keywords);
                if(c.getAttachedTo()!=null)out.addProperty("attached_to",c.getAttachedTo().getId());
                JsonArray attached=new JsonArray();
                for(Card attachment:c.getAttachedCards())attached.add(attachment.getId());
                out.add("attachments",attached);
            }
        } else { out.addProperty("name",entity.getName()); }
        return out;
    }
    public static JsonObject forPlayer(Player viewer) {
        Game game=viewer.getGame(); JsonObject out=new JsonObject();
        out.addProperty("viewer_id",viewer.getId());out.addProperty("viewer",viewer.getName());
        out.addProperty("turn",game.getPhaseHandler().getTurn());
        out.addProperty("phase",String.valueOf(game.getPhaseHandler().getPhase()));
        if(game.getPhaseHandler().getPlayerTurn()!=null)out.addProperty("active_player_id",game.getPhaseHandler().getPlayerTurn().getId());
        JsonArray players=new JsonArray();
        for(Player p:game.getPlayers()) {
            JsonObject po=new JsonObject();po.addProperty("id",p.getId());po.addProperty("name",p.getName());po.addProperty("life",p.getLife());
            JsonObject commanderDamage=new JsonObject(),commanderCasts=new JsonObject();
            for(var entry:p.getCommanderDamage())commanderDamage.addProperty(String.valueOf(entry.getKey().getId()),entry.getValue());
            for(Card commander:p.getCommanders())commanderCasts.addProperty(String.valueOf(commander.getId()),p.getCommanderCast(commander));
            po.add("commander_damage",commanderDamage);po.add("commander_casts",commanderCasts);
            po.addProperty("hand_count",p.getCardsIn(ZoneType.Hand).size());po.addProperty("library_count",p.getCardsIn(ZoneType.Library).size());
            for(ZoneType z:new ZoneType[]{ZoneType.Battlefield,ZoneType.Graveyard,ZoneType.Command}) {
                JsonArray cs=new JsonArray();for(Card c:p.getCardsIn(z,false))cs.add(entity(c,viewer));po.add(z.name().toLowerCase(),cs);
            }
            JsonArray exile=new JsonArray();
            for(Card c:p.getCardsIn(ZoneType.Exile)) {
                if(c.isFaceDown()) {JsonObject unknown=new JsonObject();unknown.addProperty("id",c.getId());unknown.addProperty("name","Face-down exiled card");unknown.addProperty("owner_id",c.getOwner().getId());unknown.addProperty("controller_id",c.getController().getId());unknown.addProperty("zone","Exile");exile.add(unknown);}
                else exile.add(entity(c,viewer));
            }
            po.add("exile",exile);
            if(p==viewer) {JsonArray hand=new JsonArray();for(Card c:p.getCardsIn(ZoneType.Hand))hand.add(entity(c,viewer));po.add("hand",hand);}
            players.add(po);
        }
        out.add("players",players);
        JsonArray stack=new JsonArray();
        for(SpellAbilityStackInstance instance:game.getStack()) {
            var sa=instance.getSpellAbility();JsonObject so=entity(sa.getHostCard(),viewer);
            if(!sa.getHostCard().isFaceDown())so.addProperty("description",sa.toString());stack.add(so);
        }
        out.add("stack",stack);
        var combat=game.getCombat();
        if(combat!=null) {
            JsonArray attackers=new JsonArray();
            for(Card attacker:combat.getAttackers()) {
                JsonObject relation=new JsonObject();relation.addProperty("attacker_id",attacker.getId());
                GameEntity defender=combat.getDefenderByAttacker(attacker);
                if(defender!=null) {
                    relation.addProperty("defender_id",defender.getId());
                    relation.addProperty("defender_kind",defender instanceof Player ? "player" : "card");
                }
                relation.addProperty("blocked",combat.isBlocked(attacker));
                relation.addProperty("unblocked",combat.isUnblocked(attacker));
                JsonArray blockers=new JsonArray();for(Card blocker:combat.getBlockers(attacker))blockers.add(blocker.getId());
                relation.add("blocker_ids",blockers);attackers.add(relation);
            }
            JsonObject publicCombat=new JsonObject();publicCombat.add("attackers",attackers);out.add("combat",publicCombat);
        }
        return out;
    }
}
