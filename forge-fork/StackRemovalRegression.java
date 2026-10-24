import com.google.gson.*;
import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.phase.PhaseType;
import forge.game.spellability.*;
import forge.game.zone.ZoneType;
import java.nio.file.*;
import java.util.*;

/** Real Aftermath resolution and generic live/frozen removal controls. */
public class StackRemovalRegression extends AITest {
    static void require(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args) throws Exception {
        String mode=args[0];int expected=Integer.parseInt(args[1]);Path root=Path.of(args[2]);Files.createDirectories(root);
        StackRemovalRegression t=new StackRemovalRegression();t.initializeModel();forge.util.MyRandom.setRandom(new Random(40));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Stack removal fixture"));
        for(Player x:game.getPlayers())t.fillLibrary(x,10);
        Player p=game.getPlayers().get(0);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
        if(mode.startsWith("aftermath")){
            Card card=t.addCardToZone("Dusk // Dawn",p,ZoneType.Graveyard);
            for(int i=0;i<5;i++)t.addCardToZone("Plains",p,ZoneType.Battlefield);
            game.getAction().checkStaticAbilities();game.copyLastState();
            DurableEvidence.begin("stack-removal-aftermath");EngineEvidence.begin(game);
            var chosen=p.getController().chooseSpellAbilityToPlay();
            require(chosen!=null && chosen.size()==1 && chosen.get(0).getHostCard().getId()==card.getId(),"Aftermath not selected from graveyard");
            require(p.getController().playChosenSpellAbility(chosen.get(0)),"Aftermath real cast/payment failed");
            require(game.getStack().size()==1,"Wrong Aftermath stack size");
            if(mode.equals("aftermath-countered")){
                Player opponent=game.getPlayers().get(1);
                Card counter=t.addCardToZone("Counterspell",opponent,ZoneType.Hand);
                Card a=t.addCardToZone("Island",opponent,ZoneType.Battlefield),b=t.addCardToZone("Island",opponent,ZoneType.Battlefield);
                game.getAction().checkStaticAbilities();game.getPhaseHandler().setPriority(opponent);
                var response=opponent.getController().chooseSpellAbilityToPlay();
                require(response!=null && response.size()==1 && response.get(0).getHostCard().getId()==counter.getId(),"Counter response not selected");
                require(opponent.getController().playChosenSpellAbility(response.get(0)) && a.isTapped() && b.isTapped(),"Counter did not pay real UU");
                require(game.getStack().size()==2,"Counter response did not enter stack");
            }
            game.getStack().resolveStack();
            require(game.getStack().isEmpty() && p.getCardsIn(ZoneType.Exile).stream().anyMatch(c->c.getId()==card.getId()),"Aftermath did not leave stack for exile");
            require(p.getCardsIn(ZoneType.Battlefield).stream().filter(Card::isTapped).count()==5 && p.getManaPool().isEmpty(),"Aftermath cost not paid exactly");
        } else {
            Card ring=t.addCardToZone("Sol Ring",p,ZoneType.Hand),land=t.addCardToZone("Island",p,ZoneType.Battlefield);
            game.getAction().checkStaticAbilities();game.copyLastState();
            SpellAbility sa=ring.getSpellAbilities().stream().filter(SpellAbility::isSpell).findFirst().orElseThrow();sa.setActivatingPlayer(p);
            require(ComputerUtil.handlePlayingSpellAbility(p,sa,null),"Real control cast failed");
            SpellAbilityStackInstance instance=game.getStack().peek();
            if(mode.equals("frozen")){
                game.getStack().remove(instance);game.getStack().freezeStack(null);game.getStack().add(instance.getSpellAbility(),instance);
                var f=game.getStack().getClass().getDeclaredField("frozenStack");f.setAccessible(true);
                instance=(SpellAbilityStackInstance)((java.util.Stack<?>)f.get(game.getStack())).peek();
            }
            DurableEvidence.begin("stack-removal-"+mode);EngineEvidence.begin(game);
            game.getStack().remove(instance);game.getStack().remove(instance);
            if(mode.equals("frozen"))game.getStack().unfreezeStack();
            require(game.getStack().isEmpty() && land.isTapped() && p.getManaPool().isEmpty(),"Repeated removal changed payment or retained stack instance");
        }
        EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");result.addProperty("seed",40);
        DurableEvidence.finish(root.resolve("results"),40,"stack removal constructed fixture\n",result);
        Path tape=Path.of(System.getProperty("forge.audit.directory"),"referee-events.jsonl");int count=0;
        for(String line:Files.readAllLines(tape)){
            JsonObject row=JsonParser.parseString(line).getAsJsonObject();
            if(row.get("kind").getAsString().equals("engine_call") && row.get("hook").getAsString().startsWith("forge/game/Game.fireEvent(")){
                JsonObject event=row.getAsJsonArray("arguments").get(0).getAsJsonObject();
                if(event.get("record_type").getAsString().equals("GameEventSpellRemovedFromStack"))count++;
            }
        }
        require(count==expected,"Wrong removal notification count "+count+" expected "+expected);
        System.out.println("PASS mode="+mode+" removal_notifications="+count+"; actual payments/zones checked, not natural-game approval");System.exit(0);
    }
}
