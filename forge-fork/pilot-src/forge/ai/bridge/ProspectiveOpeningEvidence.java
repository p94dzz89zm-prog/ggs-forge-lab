package forge.ai.bridge;

import com.google.gson.*;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import java.nio.file.Path;
import java.util.*;

/** Private observational evidence only; never a pilot input or legality oracle. */
public final class ProspectiveOpeningEvidence {
    private record Call(String hook, Game game, Object receiver) {}
    private static final Map<Long, Call> calls = new LinkedHashMap<>();
    private static long next;
    private static boolean closed;
    private ProspectiveOpeningEvidence() {}
    private static Object field(Object obj, String name) {
        try { var f=obj.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(obj); }
        catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
    }
    private static int randomIndex() {
        try { var f=EngineEvidence.class.getDeclaredField("randomPosition"); f.setAccessible(true); return f.getInt(null); }
        catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
    }
    private static Game game(Object obj) {
        if (obj instanceof Player p) return p.getGame();
        if (obj instanceof PlayerController c) return c.getPlayer().getGame();
        return (Game)field(obj,"game");
    }
    private static void write(JsonObject row) {
        String file=System.getProperty("dragonmind.prospectiveOpening"); if(file==null)return;
        row.addProperty("format",1);row.addProperty("audience","offline_referee_only");
        row.addProperty("random_index",randomIndex());row.addProperty("rules_approved",false);
        try { DurableEvidence.append(Path.of(file),row); } catch(Exception e){throw new IllegalStateException("Opening evidence failed",e);}
    }
    private static JsonElement value(Object obj) {
        if(obj==null)return JsonNull.INSTANCE;
        if(obj instanceof Boolean b)return new JsonPrimitive(b);
        if(obj instanceof Number n)return new JsonPrimitive(n);
        if(obj instanceof Player p)return new JsonPrimitive(p.getId());
        if(obj instanceof Card c)return new JsonPrimitive(c.getId());
        if(obj instanceof Iterable<?> list){JsonArray out=new JsonArray();for(Object item:list)out.add(value(item));return out;}
        return new JsonPrimitive(obj.getClass().getName());
    }
    private static JsonObject state(Game game) {
        JsonObject out=new JsonObject();out.addProperty("game_type",game.getRules().getGameType().name());
        out.addProperty("age",String.valueOf(game.getAge()));JsonArray players=new JsonArray();
        for(Player p:game.getRegisteredPlayers()){
            JsonObject seat=new JsonObject();seat.addProperty("id",p.getId());seat.addProperty("life",p.getLife());
            for(ZoneType zone:ZoneType.values()){
                JsonArray cards=new JsonArray();for(Card c:p.getCardsIn(zone,false)){
                    JsonObject card=new JsonObject();card.addProperty("id",c.getId());card.addProperty("name",c.getName());
                    card.addProperty("owner",c.getOwner().getId());card.addProperty("commander",c.isCommander());
                    card.addProperty("immutable",c.isImmutable());card.addProperty("token",c.isToken());
                    card.addProperty("actual_zone",c.getZone()==null?null:c.getZone().getZoneType().name());cards.add(card);
                }seat.add(zone.name(),cards);
            }players.add(seat);
        }out.add("players",players);return out;
    }
    public static synchronized long enter(String hook,Object receiver,Object[] args){
        if(System.getProperty("dragonmind.prospectiveOpening")==null||closed)return 0;
        Game game=game(receiver);long id=++next;calls.put(id,new Call(hook,game,receiver));
        JsonObject row=new JsonObject();row.addProperty("kind","opening_call");row.addProperty("call_id",id);row.addProperty("hook",hook);
        row.add("state",state(game));
        if(receiver instanceof Player p)row.addProperty("player_id",p.getId());
        if(receiver instanceof PlayerController c)row.addProperty("player_id",c.getPlayer().getId());
        if(hook.equals("mulligans"))row.add("first_player_id",value(field(receiver,"firstPlayer")));
        JsonArray arguments=new JsonArray();for(Object arg:args)arguments.add(value(arg));row.add("arguments",arguments);
        write(row);return id;
    }
    public static synchronized void leave(long id,Object result){
        if(id==0)return;Call call=calls.remove(id);if(call==null)throw new IllegalStateException("Unknown opening call");
        JsonObject row=new JsonObject();row.addProperty("kind","opening_return");row.addProperty("call_id",id);
        row.addProperty("hook",call.hook);row.add("result",value(result));row.add("state",state(call.game));write(row);
    }
    public static synchronized void generated(Player player,Iterable<Card> cards){
        if(System.getProperty("dragonmind.prospectiveOpening")==null||closed)return;
        JsonObject row=new JsonObject();row.addProperty("kind","shuffle_generated");row.addProperty("player_id",player.getId());
        row.add("order",value(cards));write(row);
    }
    public static synchronized void random(int bits,int result){
        if(System.getProperty("dragonmind.prospectiveOpening")==null||closed)return;
        JsonObject row=new JsonObject();row.addProperty("kind","opening_random_bits");row.addProperty("bits",bits);row.addProperty("value",result);write(row);
    }
    public static synchronized void priorityEvent(Game game,Object event){
        if(System.getProperty("dragonmind.prospectiveOpening")==null||closed||!(event instanceof forge.game.event.GameEventPlayerPriority))return;
        JsonObject row=new JsonObject();row.addProperty("kind","opening_priority");row.add("state",state(game));
        var phase=game.getPhaseHandler();row.addProperty("turn",phase.getTurn());row.addProperty("phase",String.valueOf(phase.getPhase()));
        row.add("active_player",value(phase.getPlayerTurn()));row.add("priority_player",value(phase.getPriorityPlayer()));
        row.addProperty("stack_empty",game.getStack().isEmpty());row.addProperty("open_capture_calls",calls.size());write(row);closed=true;
    }
}
