package forge.ai.bridge;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.io.*;
import java.security.*;
import java.util.*;

/** Private diagnostic snapshots. Default off. Never a pilot observation. */
public final class ReadinessTrace {
 private static Game live;
 private static BufferedWriter writer;
 private static Path path;
 private static long sequence;
 public static synchronized void begin(Game game){
  String target=System.getProperty("dragonmind.readinessTrace");if(target==null)return;
  if(live==game)return;
  if(live!=null)throw new IllegalStateException("Overlapping readiness games");
  try{path=Path.of(target);writer=Files.newBufferedWriter(path,StandardOpenOption.CREATE_NEW);live=game;sequence=0;event(game,"trace_begin",false);}
  catch(IOException e){throw new IllegalStateException("Cannot open readiness evidence",e);}
 }
 public static synchronized void event(Game game,String kind,boolean result){
  if(live!=game||writer==null)return; // Exclude hypothetical clones.
  JsonObject row=new JsonObject();row.addProperty("format",1);row.addProperty("audience","offline_referee_only");row.addProperty("sequence",++sequence);row.addProperty("kind",kind);row.addProperty("result",result);
  var phase=game.getPhaseHandler();row.addProperty("turn",phase.getTurn());row.addProperty("phase",String.valueOf(phase.getPhase()));row.addProperty("priority",phase.getPriorityPlayer()==null?null:phase.getPriorityPlayer().getId());
  JsonArray players=new JsonArray();
  for(Player p:game.getRegisteredPlayers()){
   JsonObject s=new JsonObject();s.addProperty("id",p.getId());s.addProperty("life",p.getLife());s.addProperty("poison",p.getPoisonCounters());s.addProperty("active",game.getPlayers().contains(p));s.addProperty("lost",p.hasLost());
   s.addProperty("hand_count",p.getCardsIn(ZoneType.Hand).size());s.addProperty("library_count",p.getCardsIn(ZoneType.Library).size());
   JsonArray cards=new JsonArray();for(Card c:p.getCardsIn(ZoneType.Battlefield)){
    JsonObject card=new JsonObject();card.addProperty("id",c.getId());card.addProperty("owner",c.getOwner().getId());card.addProperty("controller",c.getController().getId());card.addProperty("creature",c.isCreature());card.addProperty("power",c.getNetPower());card.addProperty("toughness",c.getNetToughness());card.addProperty("damage",c.getDamage());card.addProperty("phased_out",c.isPhasedOut());card.addProperty("indestructible",c.hasKeyword("Indestructible"));cards.add(card);
   }s.add("battlefield",cards);players.add(s);
  }row.add("players",players);
  JsonArray stack=new JsonArray();for(var instance:game.getStack()){
   JsonObject s=new JsonObject();s.addProperty("instance",instance.getId());s.addProperty("ability",instance.getSpellAbility().getId());s.addProperty("source",instance.getSpellAbility().getHostCard().getId());stack.add(s);
  }row.add("stack",stack);
  row.addProperty("snapshot_scope","Partial public-state diagnostic; no full layers, targets, pending-trigger inventory or hidden-zone identities");
  try{writer.write(row.toString());writer.newLine();writer.flush();}catch(IOException e){throw new IllegalStateException("Cannot write readiness evidence",e);}
 }
 public static synchronized void finish(Game game){
  if(live!=game||writer==null)return;
  event(game,"trace_complete",false);
  try{
   writer.close();writer=null;MessageDigest hash=MessageDigest.getInstance("SHA-256");
   try(InputStream in=Files.newInputStream(path)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)hash.update(b,0,n);}
   JsonObject receipt=new JsonObject();receipt.addProperty("records",sequence);receipt.addProperty("bytes",Files.size(path));receipt.addProperty("sha256",HexFormat.of().formatHex(hash.digest()));receipt.addProperty("rules_approved",false);
   Files.writeString(Path.of(path+".receipt.json"),receipt.toString(),StandardOpenOption.CREATE_NEW);live=null;
  }catch(Exception e){throw new IllegalStateException("Cannot seal readiness evidence",e);}
 }
}
