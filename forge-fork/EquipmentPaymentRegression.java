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
        boolean late=args[0].equals("late-reservation") || args[0].equals("late-main2");
        AiCardMemory.MemorySet reservation=args[0].equals("late-main2")
            ? AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_MAIN2
            : AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL;
        EquipmentPaymentRegression t=new EquipmentPaymentRegression();t.initializeModel();
        if(args[0].equals("late-main2"))AiProfileUtil.loadAllProfiles("res/ai");
        forge.util.MyRandom.setRandom(new Random(37));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++){
            LobbyPlayerAi lobby=new LobbyPlayerAi("seat"+i,null);
            if(args[0].equals("late-main2"))lobby.setAiProfile("Default");
            seats.add(new RegisteredPlayer(new Deck()).setPlayer(lobby));
        }
        GameRules rules=new GameRules(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"Equipment payment probe"));
        for(Player x:game.getPlayers())t.fillLibrary(x,10);
        Player p=game.getPlayers().get(0);
        if(args[0].equals("late-main2"))require(((PlayerControllerAi)p.getController()).getAi().getIntProperty(AiProps.RESERVE_MANA_FOR_MAIN2_CHANCE)==100,"Historical Default reservation profile not loaded");
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
        if(late)for(Card land:List.of(a,b))AiCardMemory.rememberCard(p,land,reservation);
        boolean played=p.getController().playChosenSpellAbility(choice.get(0));
        System.out.println("PROBE played="+played+" tapped="+a.isTapped()+","+b.isTapped()+" stack="+game.getStack().size()+" pool="+p.getManaPool());
        if(late){
            require(!played && !a.isTapped() && !b.isTapped() && p.getManaPool().isEmpty() && game.getStack().isEmpty(),"Stale payment plan mutated state");
            require(!choice.get(0).isSkip(),"Stale payment plan entered payment and poisoned the ability with skip");
            AiCardMemory.clearMemorySet(p,reservation);
            var retry=p.getController().chooseSpellAbilityToPlay();
            require(retry!=null && retry.get(0).getHostCard()==equipment && p.getController().playChosenSpellAbility(retry.get(0)),"Refused selection could not be selected and paid after reservation release");
            game.getStack().resolveStack();require(equipment.getEquipping()==creature,"Retry failed attachment");
        } else if(!reserve){
            require(played && a.isTapped() && b.isTapped() && p.getManaPool().isEmpty() && game.getStack().size()==1,"Legal equip failed real generic payment");
            game.getStack().resolveStack();require(equipment.getEquipping()==creature,"Equip failed attachment");
        } else {
            require(!played && !a.isTapped() && !b.isTapped() && p.getManaPool().isEmpty() && game.getStack().isEmpty(),"Reservation refusal changed resources or entered stack");
        }
        System.out.println("PASS equipment payment probe; scope excludes natural-game approval");System.exit(0);
    }
}
