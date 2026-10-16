package forge.ai.bridge;

import com.google.gson.JsonObject;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.nio.file.Path;

/** Offline audit stream; never a source of information for the remote seat. */
public final class BridgeAudit {
    private BridgeAudit() {}
    public static void evaluation(Player player,SpellAbility ability,String decision) {
        String dir=System.getProperty("forge.audit.directory");if(dir==null)return;
        String selected=System.getProperty("forge.audit.player");if(selected!=null&&!selected.equals(player.getName()))return;
        JsonObject row=new JsonObject();row.addProperty("kind","ai_evaluation");
        row.addProperty("offline_private",true);row.addProperty("ability",ability.toString());row.addProperty("decision",decision);
        row.addProperty("card_id",ability.getHostCard().getId());row.addProperty("card",ability.getHostCard().getName());row.addProperty("is_ninjutsu",ability.isNinjutsu());
        // Full state is recorded at priority selection, not for every candidate:
        // duplicating snapshots in the timed evaluator would distort its budget.
        row.addProperty("player_id",player.getId());row.addProperty("turn",player.getGame().getPhaseHandler().getTurn());
        row.addProperty("phase",String.valueOf(player.getGame().getPhaseHandler().getPhase()));
        try {BridgeChannel.append(Path.of(dir,"evaluation-seat-"+player.getId()+".jsonl"),row.toString());}
        catch(java.io.IOException e){throw new IllegalStateException("Decision audit failure",e);}
    }
}
