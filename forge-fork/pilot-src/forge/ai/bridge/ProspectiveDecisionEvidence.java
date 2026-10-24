package forge.ai.bridge;
import com.google.gson.*;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import java.nio.file.Path;
import java.util.*;

/** Offline observation of offered choices; enumeration completeness is unproved. */
public final class ProspectiveDecisionEvidence {
    private static Game live;private static long next;
    private static final Map<Long,PlayerController> calls=new HashMap<>();
    private ProspectiveDecisionEvidence(){}
    private static JsonElement describe(Object value){
        try{var method=EngineEvidence.class.getDeclaredMethod("value",Object.class,int.class);method.setAccessible(true);return (JsonElement)method.invoke(null,value,0);}
        catch(ReflectiveOperationException e){throw new IllegalStateException(e);}
    }
    private static void write(JsonObject row){
        row.addProperty("format",1);row.addProperty("audience","offline_referee_only");row.addProperty("rules_approved",false);
        try{DurableEvidence.append(Path.of(System.getProperty("dragonmind.legalChoices")),row);}catch(Exception e){throw new IllegalStateException(e);}
    }
    public static synchronized long enter(String hook,PlayerController controller,Object[] arguments){
        if(System.getProperty("dragonmind.legalChoices")==null)return 0;
        Player actor=controller.getPlayer();Game game=actor.getGame();if(live==null)live=game;if(game!=live)return 0;
        long id=++next;calls.put(id,controller);JsonObject row=new JsonObject();row.addProperty("kind","decision_offer");row.addProperty("decision_id",id);row.addProperty("hook",hook);row.addProperty("actor",actor.getId());
        var phase=game.getPhaseHandler();row.addProperty("turn",phase.getTurn());row.addProperty("phase",String.valueOf(phase.getPhase()));row.addProperty("priority",phase.getPriorityPlayer()==null?null:phase.getPriorityPlayer().getId());row.addProperty("active",phase.getPlayerTurn()==null?null:phase.getPlayerTurn().getId());
        row.add("offered_arguments",describe(arguments));row.add("mana_pool",describe(actor.getManaPool()));
        JsonArray publicPlayers=new JsonArray();for(Player p:game.getPlayers()){
            JsonObject seat=new JsonObject();seat.addProperty("id",p.getId());seat.addProperty("life",p.getLife());seat.addProperty("hand_count",p.getCardsIn(ZoneType.Hand).size());seat.addProperty("library_count",p.getCardsIn(ZoneType.Library).size());
            JsonArray visible=new JsonArray();for(ZoneType z:new ZoneType[]{ZoneType.Hand,ZoneType.Battlefield,ZoneType.Command,ZoneType.Graveyard,ZoneType.Exile})for(Card c:p.getCardsIn(z)){
                boolean permitted=c.isFaceDown()?c.getView().canFaceDownBeShownTo(actor.getView()):c.getView().canBeShownTo(actor.getView());
                // Conservative information projection: opponent hand identities
                // require independent reveal-entitlement tracking before inclusion.
                if(z==ZoneType.Hand&&p!=actor)permitted=false;
                if(permitted){JsonObject card=new JsonObject();card.addProperty("id",c.getId());card.addProperty("name",c.getName());card.addProperty("zone",z.name());card.addProperty("tapped",c.isTapped());visible.add(card);}
            }seat.add("actor_visible_cards",visible);publicPlayers.add(seat);
        }row.add("actor_information",publicPlayers);row.addProperty("enumeration_scope","Actual native choice arguments only; full legal-action enumeration and independent legality remain unproved");write(row);return id;
    }
    public static synchronized void leave(long id,Object result){
        if(id==0)return;if(calls.remove(id)==null)throw new IllegalStateException("Unknown captured decision");
        JsonObject row=new JsonObject();row.addProperty("kind","decision_return");row.addProperty("decision_id",id);row.add("chosen_result",describe(result));write(row);
    }
}
