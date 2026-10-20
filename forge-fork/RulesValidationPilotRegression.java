import com.google.gson.JsonObject;
import forge.ai.*;
import forge.ai.bridge.*;
import forge.ai.validation.RulesValidationController;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.phase.PhaseType;
import forge.game.zone.ZoneType;
import java.nio.file.*;
import java.util.*;

/** Four-player native controller integration. Deliberately constructed, not a game. */
public class RulesValidationPilotRegression extends AITest {
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        String mode=args[0];Path out=Path.of(args[1]);Files.createDirectories(out);
        RulesValidationPilotRegression t=new RulesValidationPilotRegression();t.initializeModel();
        forge.util.MyRandom.setRandom(new Random(17));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"Validation pilot constructed fixture"));
        for(Player p:game.getPlayers())t.fillLibrary(p,10);
        Player p=game.getPlayers().get(0),opponent=game.getPlayers().get(1);
        if(mode.equals("off")){
            require(!(p.getController() instanceof RulesValidationController),"Default-off changed controller");
            System.out.println("PASS validation pilot default-off controller preserved");System.exit(0);
        }
        require(game.getPlayers().stream().allMatch(x->x.getController() instanceof RulesValidationController),"Factory did not install four validation controllers");
        game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
        Card ring=t.addCardToZone("Sol Ring",p,ZoneType.Hand);
        Card island=t.addCardToZone("Island",p,ZoneType.Battlefield);
        Card expensive=t.addCardToZone("Ulamog, the Infinite Gyre",p,ZoneType.Hand);
        Card hidden=t.addCardToZone("Colossification",opponent,ZoneType.Hand);
        game.getAction().checkStaticAbilities();game.copyLastState();
        DurableEvidence.begin("native-validation-fixture");EngineEvidence.begin(game);
        require(!p.getController().playChosenSpellAbility(null),"Null action was not refused");
        var chosen=p.getController().chooseSpellAbilityToPlay();
        require(chosen!=null && chosen.size()==1 && chosen.get(0).getHostCard()==ring,"Pilot failed payable spell selection");
        require(!island.isTapped() && ring.isInZone(ZoneType.Hand),"Selection spent resources");
        game.getPhaseHandler().setPriority(opponent);
        require(!p.getController().playChosenSpellAbility(chosen.get(0)) && !island.isTapped(),"Wrong-priority execution transferred resources");
        game.getPhaseHandler().setPriority(p);
        require(p.getController().playChosenSpellAbility(chosen.get(0)),"Actual engine cast/payment failed");
        require(island.isTapped() && p.getManaPool().isEmpty() && game.getStack().size()==1,"Wrong paid stack transition");
        require(!p.getController().playChosenSpellAbility(chosen.get(0)),"Consumed selection executed twice");
        game.getStack().resolveStack();
        require(p.getCardsIn(ZoneType.Battlefield).stream().anyMatch(c->c.getId()==ring.getId() && c.getName().equals("Sol Ring")),"Paid spell did not resolve to current battlefield identity: "+p.getCardsIn(ZoneType.Battlefield));

        Card mountain=t.addCardToZone("Mountain",p,ZoneType.Battlefield);
        Card bolt=t.addCardToZone("Lightning Bolt",p,ZoneType.Hand);
        Card elf=t.addCardToZone("Llanowar Elves",opponent,ZoneType.Battlefield);
        game.getAction().checkStaticAbilities();game.copyLastState();
        chosen=p.getController().chooseSpellAbilityToPlay();
        require(chosen!=null && chosen.size()==1 && chosen.get(0).getHostCard()==bolt,"Pilot failed targeted removal preflight");
        require(p.getController().playChosenSpellAbility(chosen.get(0)) && mountain.isTapped(),"Targeted spell did not pay real red mana");
        game.getStack().resolveStack();game.getAction().checkStateEffects(true);
        require(p.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getId()==bolt.getId()),"Instant did not resolve to graveyard");
        require(opponent.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getId()==elf.getId()),"Native removal did not destroy selected 1/1 through SBA");
        require(expensive.isInZone(ZoneType.Hand) && hidden.isInZone(ZoneType.Hand),"Unaffordable/private-zone card moved");
        EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");result.addProperty("seed",17);
        DurableEvidence.finish(out.resolve("results"),17,"native validation fixture\n",result);
        System.out.println("PASS four validation controllers: deterministic selection, actual mana payment, wrong-priority refusal, consumed-selection refusal, stack resolution, targeted removal and SBA");
        System.out.println("SCOPE constructed four-player fixture; no natural game, terminal approval or training");System.exit(0);
    }
}
