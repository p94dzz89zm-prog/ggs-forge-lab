import com.google.gson.*;
import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.Card;
import forge.game.cost.Cost;
import forge.game.keyword.*;
import forge.game.player.*;
import forge.game.phase.PhaseType;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.lang.reflect.Method;
import java.util.*;

/** Real optional additional costs and linked ETB copies; not a natural game. */
public class SquadKeywordRegression extends AITest {
    static void require(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args) throws Exception {
        int amount=Integer.parseInt(args[0]);boolean remove=Boolean.parseBoolean(args[1]);
        SquadKeywordRegression t=new SquadKeywordRegression();t.initializeModel();
        forge.util.MyRandom.setRandom(new Random(38));t.initAndCreateGame();
        List<RegisteredPlayer> seats=new ArrayList<>();
        for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Squad fixture"));
        for(Player x:game.getPlayers())t.fillLibrary(x,10);
        Player p=game.getPlayers().get(0);
        p.dangerouslySetController(new PlayerControllerAi(game,p,p.getLobbyPlayer()){
            @Override public int chooseNumberForKeywordCost(SpellAbility sa,Cost c,KeywordInterface k,String prompt,int max){
                require(k.getKeyword()==Keyword.SQUAD && amount<=max,"Unexpected additional-cost choice");return amount;
            }
        });
        game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
        Card card=t.addCardToZone("Endless Foot Assault",p,ZoneType.Hand);
        List<Card> lands=new ArrayList<>();for(int i=0;i<3+2*amount;i++)lands.add(t.addCardToZone("Plains",p,ZoneType.Battlefield));
        game.getAction().checkStaticAbilities();game.copyLastState();
        DurableEvidence.begin("squad-fixture-"+amount+"-"+remove);EngineEvidence.begin(game);
        KeywordInterface keyword=card.getKeywords(Keyword.SQUAD).iterator().next();
        Method encode=EngineEvidence.class.getDeclaredMethod("value",Object.class,int.class);encode.setAccessible(true);
        JsonObject value=(JsonObject)encode.invoke(null,keyword,0);
        require(value.get("keyword").getAsString().equals("SQUAD") && !value.has("unencoded"),"Keyword was not typed");
        require(value.getAsJsonObject("mana_cost").get("generic").getAsInt()==1,"Squad cost lost generic mana");
        System.out.println("ENCODED "+value);
        SpellAbility sa=card.getSpellAbilities().stream().filter(SpellAbility::isSpell).findFirst().orElseThrow();sa.setActivatingPlayer(p);
        require(ComputerUtil.handlePlayingSpellAbility(p,sa,null),"Squad cast failed");
        require(lands.stream().filter(Card::isTapped).count()==3+2*amount && p.getManaPool().isEmpty(),"Additional cost not paid exactly");
        System.out.println("SQUAD original-SA-count="+sa.getOptionalKeywordAmount(keyword));
        require(game.getStack().peekAbility().getOptionalKeywordAmount(Keyword.SQUAD)==amount,"Stack spell lost paid Squad count");
        game.getStack().resolveStack();game.getStack().addAllTriggeredAbilitiesToStack();
        Card current=p.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getId()==card.getId()).findFirst().orElseThrow();
        if(remove)game.getAction().moveToGraveyard(current,null);
        int resolved=0;while(!game.getStack().isEmpty()){
            require(++resolved<=10,"Squad token copies recursively triggered");game.getStack().resolveStack();game.getStack().addAllTriggeredAbilitiesToStack();
        }
        long copies=p.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getName().equals("Endless Foot Assault") && c.isToken()).count();
        require(copies==amount,"Wrong Squad token count after original removal="+remove+": "+copies);
        EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");result.addProperty("seed",38);
        DurableEvidence.finish(java.nio.file.Path.of(System.getProperty("forge.audit.directory")).getParent().resolve("results"),38,"Squad constructed fixture\n",result);
        System.out.println("PASS Squad amount="+amount+" original_removed="+remove+" copies="+copies+" exact mana payment and finite linked triggers");System.exit(0);
    }
}
