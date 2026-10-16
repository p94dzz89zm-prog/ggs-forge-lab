package forge.ai.ggs;

import com.google.gson.*;
import forge.ai.bridge.BridgeSnapshot;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Player-visible state plus public targets, combat assignments and mana. */
public final class PlannerSnapshot {
    private PlannerSnapshot() {}
    public static JsonObject forPlayer(Player viewer) {
        JsonObject out=BridgeSnapshot.forPlayer(viewer);
        JsonArray stack=new JsonArray();
        for(var item:viewer.getGame().getStack()) {
            SpellAbility sa=item.getSpellAbility();JsonObject entry=new JsonObject();
            entry.addProperty("host_id",sa.getHostCard().getId());
            if(sa.getActivatingPlayer()!=null)entry.addProperty("activating_player_id",sa.getActivatingPlayer().getId());
            entry.addProperty("api",String.valueOf(sa.getApi()));entry.addProperty("x_paid",sa.getXManaCostPaid());
            JsonArray cards=new JsonArray(),players=new JsonArray(),spells=new JsonArray();
            for(Card c:sa.getTargets().getTargetCards())cards.add(c.getId());
            for(Player p:sa.getTargets().getTargetPlayers())players.add(p.getId());
            for(SpellAbility target:sa.getTargets().getTargetSpells())spells.add(target.getHostCard().getId());
            entry.add("target_card_ids",cards);entry.add("target_player_ids",players);entry.add("target_spell_host_ids",spells);stack.add(entry);
        }
        out.add("public_stack_targets",stack);
        JsonObject combat=new JsonObject();var c=viewer.getGame().getCombat();
        if(c!=null) {
            combat.addProperty("attacking_player_id",c.getAttackingPlayer().getId());JsonArray attackers=new JsonArray();
            for(Card a:c.getAttackers()) {
                JsonObject row=new JsonObject();row.addProperty("attacker_id",a.getId());
                var defender=c.getDefenderByAttacker(a);if(defender!=null)row.addProperty("defender_id",defender.getId());
                row.addProperty("blocked",c.isBlocked(a));JsonArray blockers=new JsonArray();
                for(Card b:c.getBlockers(a))blockers.add(b.getId());row.add("blocker_ids",blockers);attackers.add(row);
            }
            combat.add("attackers",attackers);
        }
        out.add("public_combat",combat);JsonArray mana=new JsonArray();
        for(Player p:viewer.getGame().getPlayers()){JsonObject row=new JsonObject();row.addProperty("player_id",p.getId());row.addProperty("pool",p.getManaPool().toString());mana.add(row);}
        out.add("public_mana_pools",mana);return out;
    }
}
