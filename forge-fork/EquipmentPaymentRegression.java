import forge.ai.*;
import forge.ai.validation.RulesValidationController;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.player.*;
import forge.game.phase.PhaseType;
import forge.game.zone.ZoneType;
import java.util.*;

/** Minimal real-payment probe; constructed fixture, never complete-game approval. */
public class EquipmentPaymentRegression extends AITest {
    static void require(boolean value,String text){if(!value)throw new AssertionError(text);}
    public static void main(String[] args) throws Exception {
        boolean reserve=Boolean.parseBoolean(args[0]);
        EquipmentPaymentRegression t=new EquipmentPaymentRegression();t.initializeModel();
        forge.util.MyRandom.setRandom(new Random(37));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"Equipment payment probe"));
        for(Player x:game.getPlayers())t.fillLibrary(x,10);
        Player p=game.getPlayers().get(0);
        game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
        Card equipment=t.addCardToZone("Foot Chopper",p,ZoneType.Battlefield);
        Card creature=t.addCardToZone("Grizzly Bears",p,ZoneType.Battlefield);
        Card a=t.addCardToZone("Island",p,ZoneType.Battlefield),b=t.addCardToZone("Island",p,ZoneType.Battlefield);
        game.getAction().checkStaticAbilities();game.copyLastState();
        if(reserve)for(Card land:List.of(a,b))AiCardMemory.rememberCard(p,land,AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);
        var choice=p.getController().chooseSpellAbilityToPlay();
        System.out.println("PROBE reserved="+reserve+" choice="+choice);
        if(reserve){
            require(choice==null && !a.isTapped() && !b.isTapped() && p.getManaPool().isEmpty() && game.getStack().isEmpty(),"Reserved source preflight mutated state or selected an unpayable ability");
            System.out.println("PASS strategic reservation prevents preflight; no illegal activation");System.exit(0);
        }
        require(choice!=null && choice.size()==1 && choice.get(0).getHostCard()==equipment,"No equipment candidate");
        require(!a.isTapped() && !b.isTapped() && p.getManaPool().isEmpty(),"Preflight mutated resources");
        boolean played=p.getController().playChosenSpellAbility(choice.get(0));
        System.out.println("PROBE played="+played+" tapped="+a.isTapped()+","+b.isTapped()+" stack="+game.getStack().size()+" pool="+p.getManaPool());
        if(!reserve){
            require(played && a.isTapped() && b.isTapped() && p.getManaPool().isEmpty() && game.getStack().size()==1,"Legal equip failed real generic payment");
            game.getStack().resolveStack();require(equipment.getEquipping()==creature,"Equip failed attachment");
        } else {
            require(!played && !a.isTapped() && !b.isTapped() && p.getManaPool().isEmpty() && game.getStack().isEmpty(),"Reservation refusal changed resources or entered stack");
        }
        System.out.println("PASS equipment payment probe; scope excludes natural-game approval");System.exit(0);
    }
}
