import com.google.gson.*;
import forge.ai.AiCardMemory;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.nio.file.*;
import java.util.*;

/** Offline diagnostic side channel; never changes mana, decisions or referee rows. */
public final class ReservationProbe {
    private static JsonObject context(Player p){
        JsonObject r=new JsonObject();r.addProperty("turn",p.getGame().getPhaseHandler().getTurn());
        r.addProperty("phase",String.valueOf(p.getGame().getPhaseHandler().getPhase()));
        r.addProperty("player_id",p.getId());r.addProperty("pool",p.getManaPool().totalMana());
        JsonObject memories=new JsonObject();
        for(var set:AiCardMemory.MemorySet.values()){
            JsonArray a=new JsonArray();var cards=AiCardMemory.getMemorySet(p,set);
            if(cards!=null)cards.stream().sorted(Comparator.comparingInt(Card::getId)).forEach(c->a.add(c.getId()));
            memories.add(set.name(),a);
        }
        r.add("memory",memories);return r;
    }
    private static boolean enabled(Player p){return System.getProperty("dragonmind.reservationProbe")!=null && p.getId()==1 && p.getGame().getPhaseHandler().getTurn()==34;}
    private static synchronized void write(JsonObject r){
        try{Files.writeString(Path.of(System.getProperty("dragonmind.reservationProbe")),r.toString()+"\n",StandardOpenOption.CREATE,StandardOpenOption.APPEND);}
        catch(Exception e){throw new IllegalStateException("Diagnostic side-channel write failed",e);}
    }
    public static void reserved(boolean result,Player p,Card c){
        if(!enabled(p))return;JsonObject r=context(p);r.addProperty("kind","reservation_return");
        r.addProperty("source_id",c.getId());r.addProperty("source_name",c.getName());r.addProperty("reserved",result);write(r);
    }
    public static void paid(Object result,Player p,SpellAbility a){
        if(!enabled(p)||!a.getHostCard().getName().equals("Foot Chopper"))return;
        JsonObject r=context(p);r.addProperty("kind","mana_plan_return");r.addProperty("ability_id",a.getId());
        r.addProperty("source_id",a.getHostCard().getId());r.addProperty("plan_found",result!=null);r.addProperty("skip",a.isSkip());write(r);
    }
}
