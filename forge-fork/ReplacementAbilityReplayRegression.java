import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import forge.game.cost.*;
import forge.game.replacement.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Exact selected replacement-object linkage, not parameter-only aliases. */
public class ReplacementAbilityReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());ReplacementAbilityReplayRegression test=new ReplacementAbilityReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"ETB identity"));Player p=game.getPlayers().get(0);for(Player seat:game.getPlayers())test.fillLibrary(seat,10);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
  Card card=test.addCardToZone("Hidden Hideout",p,ZoneType.Hand);ReplacementEffect effect=card.getReplacementEffects().stream().filter(e->e.getClass().getName().endsWith("ReplaceMoved")).findFirst().orElseThrow();
  JsonObject identity=new JsonObject();identity.addProperty("trait_type",effect.getClass().getName());identity.addProperty("source_card_id",card.getId());JsonObject effectParams=new JsonObject();effect.getMapParams().forEach(effectParams::addProperty);identity.add("parameters",effectParams);
  JsonObject selection=new JsonObject();selection.addProperty("kind","decision");selection.addProperty("index",0);selection.addProperty("actor_id",p.getId());selection.addProperty("hook","forge/ai/PlayerControllerAi.chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;");selection.addProperty("decision_type","replacement_choice");JsonArray offered=new JsonArray();offered.add(identity);selection.add("available_effects",offered);selection.add("selected_effect",identity);
  boolean missing=mode.equals("missing"),wrong=mode.equals("wrong-instance");
  JsonObject payment=new JsonObject();payment.addProperty("kind","decision");payment.addProperty("index",missing?0:1);payment.addProperty("actor_id",p.getId());payment.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");payment.addProperty("decision_type","zero_effect_mana");payment.addProperty("source_ability",card.getId()+":900000");payment.addProperty("ability_api","Tap");payment.add("ability_parameters",JsonParser.parseString("{DB:Tap,ETB:True,Defined:Self}"));payment.addProperty("payment_choice","pay");
  payment.getAsJsonObject("ability_parameters").addProperty("ETB","True");
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,(missing?"":selection+"\n")+payment+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":"+(missing?1:2)+"}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());DurableEvidence.begin("replacement-fixture");EngineEvidence.begin(game);
  try{
   if(missing||wrong){
    if(wrong)p.getController().chooseSingleReplacementEffect(List.of(effect));
    var fake=effect.ensureAbility().copy();fake.setActivatingPlayer(p);fake.setReplacementEffect(effect);fake.setReplacingObject(forge.game.ability.AbilityKey.Card,card);effect.setHasRun(true);
    p.getController().payManaCost(fake.getPayCosts().getCostPartByType(CostPartMana.class),fake,null,null,true);throw new AssertionError("Unproven replacement instance accepted");
   }
   Card entered=p.playLand(card,null);if(entered==null||!entered.isInZone(ZoneType.Battlefield)||!entered.isTapped()||entered.getOwner()!=p||entered.getController()!=p||!game.getStack().isEmpty())throw new AssertionError("Native entered-tapped land result differs");
   DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",108);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),108,"fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS selected exact replacement instance pays actual zero cost; native Hidden Hideout enters tapped");
  }catch(IllegalStateException error){if(!(missing||wrong)||!error.getMessage().contains("no exact selected replacement instance"))throw error;if(!card.isInZone(ZoneType.Hand)||card.isTapped()||!p.getManaPool().isEmpty())throw new AssertionError("Rejected replacement mutated land/resources");System.out.println("PASS "+mode+" replacement rejected despite matching source/parameters");}
  System.exit(0);
 }
}
