import forge.ai.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.mulligan.*;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import java.lang.reflect.Field;
import java.util.*;

/** Native variant integration; no natural-game certification. */
public class HouseRulesRegression extends AITest {
    static void require(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args) throws Exception {
        boolean enabled=Boolean.parseBoolean(args[0]);
        require(CommanderHouseRules.requested()==enabled,"Wrong opt-in profile");
        HouseRulesRegression t=new HouseRulesRegression();t.initializeModel();forge.util.MyRandom.setRandom(new Random(39));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        for(RegisteredPlayer r:seats){r.setStartingLife(17);require(r.getStartingLife()==(enabled?40:17),"Starting life not enforced/default changed");}
        GameRules rules=new GameRules(GameType.Commander);rules.addAppliedVariant(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"House rules fixture"));
        for(Player p:game.getPlayers()){t.fillLibrary(p,30);p.setLife(40,null);p.setStartingLife(seats.get(0).getStartingLife());}
        Player p=game.getPlayers().get(0),opponent=game.getPlayers().get(1);
        game.setAge(GameStage.Mulligan);p.drawCards(7);
        if(enabled){
            AbstractMulligan m=CommanderHouseRules.mulligan(new LondonMulligan(p,true));
            require(m instanceof HouseMulligan,"Factory did not replace London mulligan");
            int total=p.getCardsIn(ZoneType.Library).size()+p.getCardsIn(ZoneType.Hand).size();
            for(int i=0;i<3;i++){
                require(m.canMulligan() && m.handSizeAfterNextMulligan()==7,"Free redraw unavailable");m.mulligan();
                require(p.getCardsIn(ZoneType.Hand).size()==7 && p.getCardsIn(ZoneType.Library).size()==total-7 && m.tuckCardsDuringMulligan()==0,"Reshuffle lost cards or imposed London tuck");
            }
            require(!m.canMulligan(),"Fourth redraw allowed");
            try{m.mulligan();throw new AssertionError("Fourth redraw executed");}catch(IllegalStateException expected){}
            m.keep();require(m.hasKept() && !m.canMulligan(),"Keep did not close mulligan");
            // The actual service must select this profile regardless of the stock preference.
            for(Player x:game.getPlayers())if(x!=p)x.drawCards(7);
            for(Player x:game.getPlayers())x.dangerouslySetController(new PlayerControllerAi(game,x,x.getLobbyPlayer()){
                @Override public boolean mulliganKeepHand(Player first,int cards){return false;}
            });
            MulliganService service=new MulliganService(p);service.perform();
            Field selected=MulliganService.class.getDeclaredField("mulligans");selected.setAccessible(true);
            Field times=AbstractMulligan.class.getDeclaredField("timesMulliganed");times.setAccessible(true);
            for(Object chosen:(List<?>)selected.get(service)){
                require(chosen instanceof HouseMulligan,"Native service bypassed house policy");
                AbstractMulligan actual=(AbstractMulligan)chosen;
                require(times.getInt(actual)==3 && actual.hasKept() && actual.getPlayer().getCardsIn(ZoneType.Hand).size()==7,"Native service did not cap forced decline at three free sevens");
            }
        }
        game.setAge(GameStage.Play);
        Card commander=t.addCardToZone("Goro-Goro and Satoru",opponent,ZoneType.Battlefield);commander.setCommander(true);opponent.addCommander(commander);
        p.addCommanderDamage(commander,21);
        require(p.getCommanderDamage(commander)==21,"House profile erased actual combat history");
        boolean lost=p.checkLoseCondition();
        require(lost!=enabled && p.hasLost()!=enabled,"Commander damage loss profile incorrect");
        if(enabled){p.setLife(0,null);require(p.checkLoseCondition() && p.hasLost(),"House profile disabled ordinary life loss");}
        System.out.println("PASS house profile="+enabled+" registered life, three full seven-card reshuffles, no fourth/tuck, retained damage history, commander/life loss controls");System.exit(0);
    }
}
