import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Recorded mana-source/spending decisions execute an actual cast and resolution. */
public class BasicManaReplayRegression extends AITest {
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);BasicManaReplayRegression test=new BasicManaReplayRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Constructed);Game game=new Game(seats,rules,new Match(rules,seats,"Recorded basic mana"));Player p=game.getPlayers().get(0);for(Player x:game.getPlayers())test.fillLibrary(x,10);
  game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Sol Ring",p,ZoneType.Hand);Card island=test.addCardToZone("Island",p,ZoneType.Battlefield);var spell=card.getFirstSpellAbility();spell.setActivatingPlayer(p);var mana=island.getManaAbilities().get(0);
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");row.addProperty("decision_type","basic_land_mana");row.addProperty("component","{1}");row.addProperty("source_ability",card.getId()+":"+spell.getId());row.addProperty("ability_api","PermanentNoncreature");
  JsonArray operations=new JsonArray();JsonObject activation=new JsonObject();activation.addProperty("op","activate_basic");activation.addProperty("card_id",island.getId());activation.addProperty("card_name","Island");JsonObject params=new JsonObject();mana.getMapParams().forEach(params::addProperty);activation.add("parameters",params);operations.add(activation);
  JsonObject spend=new JsonObject();spend.addProperty("op","spend");JsonObject unit=new JsonObject();unit.addProperty("source_card_id",island.getId());unit.addProperty("color",mode.equals("wrong-color")?"G":"U");unit.addProperty("snow",false);unit.addProperty("restricted",false);spend.add("mana",unit);operations.add(spend);row.add("operations",operations);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  if(mode.equals("tapped"))island.setTapped(true);
  try{
   if(!ComputerUtil.handlePlayingSpellAbility(p,spell,null))throw new AssertionError("Actual cast failed");
   if(!mode.equals("valid"))throw new AssertionError("Invalid payment accepted");
   var stacked=game.getStack().peekAbility();
   if(!island.isTapped()||!p.getManaPool().isEmpty()||stacked.getPayingMana().size()!=1||stacked.getPayingMana().get(0).getSourceCard().getId()!=island.getId())throw new AssertionError("Actual resource chain differs: tapped="+island.isTapped()+" pool="+p.getManaPool().totalMana()+" stackedPayments="+stacked.getPayingMana().size()+" originalPayments="+spell.getPayingMana().size());
   game.getStack().resolveStack();if(p.getCardsIn(ZoneType.Battlefield).stream().noneMatch(c->c.getName().equals("Sol Ring")))throw new AssertionError("Paid spell did not resolve");DecisionReplay.finish();System.out.println("PASS four-player recorded Island activation and blue mana spend cast and resolved Sol Ring");
  }catch(IllegalStateException failure){
   if(mode.equals("valid"))throw failure;String fragment=mode.equals("tapped")?"Unavailable basic":"selected basic mana";if(!failure.getMessage().contains(fragment))throw failure;
   if(!mode.equals("tapped")&&island.isTapped())throw new AssertionError("Invalid payment tapped source");if(!p.getManaPool().isEmpty())throw new AssertionError("Invalid payment produced mana");
   System.out.println("PASS four-player "+mode+" payment rejected before resource transfer");
  }
  System.exit(0);
 }
}
