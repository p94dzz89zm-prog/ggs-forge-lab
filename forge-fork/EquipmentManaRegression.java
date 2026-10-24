import com.google.gson.JsonObject;
import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.phase.PhaseType;
import forge.game.zone.ZoneType;
import java.nio.file.*;
import java.util.*;

/** Constructed four-seat mana/attachment controls, not a complete Commander game. */
public class EquipmentManaRegression extends AITest {
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        boolean remove=args[0].equals("remove-target");Path out=Path.of(args[1]);
        EquipmentManaRegression t=new EquipmentManaRegression();t.initializeModel();
        forge.util.MyRandom.setRandom(new Random(39));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"Equipment mana controls"));
        for(Player x:game.getPlayers())t.fillLibrary(x,10);
        Player p=game.getPlayers().get(0),other=game.getPlayers().get(1);
        game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
        Card equipment=t.addCardToZone("Skullclamp",p,ZoneType.Battlefield);
        Card creature=t.addCardToZone("Grizzly Bears",p,ZoneType.Battlefield);
        Card enemy=t.addCardToZone("Grizzly Bears",other,ZoneType.Battlefield);
        Card ring=t.addCardToZone("Sol Ring",p,ZoneType.Battlefield);
        game.getAction().checkStaticAbilities();game.copyLastState();
        DurableEvidence.begin("equipment-mana-"+args[0]);EngineEvidence.begin(game);
        var choice=p.getController().chooseSpellAbilityToPlay();
        require(choice!=null && choice.size()==1 && choice.get(0).getHostCard()==equipment,"Missing equip candidate");
        var ability=choice.get(0);
        require(!ability.canTarget(enemy),"Equip targeted opponent's creature");
        require(ability.getPayCosts().toString().equals("{1}"),"Unexpected equip cost");
        require(!ring.isTapped() && p.getManaPool().isEmpty(),"Selection spent mana");
        game.getPhaseHandler().devModeSet(PhaseType.COMBAT_BEGIN,p,false);
        require(!ability.canPlay(),"Sorcery-speed equip offered during combat");
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);
        require(p.getController().playChosenSpellAbility(ability),"Sol Ring failed equip payment");
        require(ring.isTapped() && p.getManaPool().totalMana()==1 && game.getStack().size()==1,"Sol Ring must generate two, spend one, retain one on stack");
        if(remove)game.getAction().moveToGraveyard(creature,null);
        game.getStack().resolveStack();game.getAction().checkStateEffects(true);
        require(p.getManaPool().totalMana()==1,"Resolution incorrectly cleared remaining mana");
        if(remove)require(equipment.getEquipping()==null && creature.isInZone(ZoneType.Graveyard),"Illegal target attached or left graveyard");
        else require(equipment.getEquipping()==creature && creature.getNetPower()==3 && creature.getNetToughness()==1,"Skullclamp attachment/continuous characteristics incorrect");
        require(equipment.isInZone(ZoneType.Battlefield),"Equipment changed zone");
        require(p.getManaPool().clearPool(false).size()==1 && p.getManaPool().isEmpty(),"Ordinary phase-end mana clearing failed");
        EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");
        result.addProperty("complete_game_approved",false);
        DurableEvidence.finish(out.resolve("results"),39,"equipment mana controls\n",result);
        System.out.println("PASS equipment mana controls: "+args[0]+"; constructed fixture only");System.exit(0);
    }
}
