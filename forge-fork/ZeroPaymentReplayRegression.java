import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.cost.*;
import forge.game.ability.AbilityFactory;
import forge.game.zone.ZoneType;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Zero-resource effect payment only. Never invokes AI mana selection. */
public class ZeroPaymentReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);
  ZeroPaymentReplayRegression test=new ZeroPaymentReplayRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
  GameRules rules=new GameRules(GameType.Constructed);Game game=new Game(seats,rules,new Match(rules,seats,"Zero effect cost"));Player p=game.getPlayers().get(0);
  Card host=test.addCardToZone("Island",p,ZoneType.Battlefield);var ability=AbilityFactory.getAbility("DB$ Draw | Cost$ 0 | Defined$ You | NumCards$ 1",host);ability.setActivatingPlayer(p);
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");row.addProperty("actor_id",p.getId());row.addProperty("decision_type","zero_effect_mana");row.addProperty("payment_choice","pay");row.addProperty("source_ability",host.getId()+":"+ability.getId());row.addProperty("ability_api",String.valueOf(ability.getApi()));JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);row.add("ability_parameters",params);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);
  System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  Cost cost=new Cost(mode.equals("nonzero")?"1":"0",true);
  if(mode.equals("nonmana"))ability.setPayCosts(new Cost("T",true));
  int life=p.getLife();int hands=p.getCardsIn(ZoneType.Hand).size();
  try {
   if(!p.getController().payManaCost(cost.getCostMana(),ability,null,null,true))throw new AssertionError("Zero payment declined");
   if(!mode.equals("valid"))throw new AssertionError("Unsupported payment accepted");
   if(p.getLife()!=life||!p.getManaPool().isEmpty()||host.isTapped()||!host.isInZone(ZoneType.Battlefield)||p.getCardsIn(ZoneType.Hand).size()!=hands||!ability.getPayingMana().isEmpty())throw new AssertionError("Zero payment moved resources");
   DecisionReplay.finish();System.out.println("PASS four-player zero effect payment: adjusted cost paid with no resource transfer or AI choice");
  }catch(IllegalStateException failure){
   if(mode.equals("valid")||!failure.getMessage().contains("resource-changing"))throw failure;
   if(host.isTapped()||p.getLife()!=life)throw new AssertionError("Rejected payment changed resources");
   try{DecisionReplay.finish();throw new AssertionError("Failed payment completed");}catch(IllegalStateException denied){if(!denied.getMessage().contains("failed decision"))throw denied;}
   System.out.println("PASS four-player "+mode+" payment rejected without resource transfer");
  }
  System.exit(0);
 }
}
