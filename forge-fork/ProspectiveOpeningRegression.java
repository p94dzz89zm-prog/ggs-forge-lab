import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.Card;
import forge.game.mulligan.*;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import forge.deck.Deck;
import java.lang.reflect.Method;
import java.nio.file.*;
import java.util.*;
import com.google.gson.*;

/** Capture integration only: duplicate-card fixture decks are not legal decks. */
public final class ProspectiveOpeningRegression extends AITest {
    public static void main(String[] args)throws Exception{
        ProspectiveOpeningRegression t=new ProspectiveOpeningRegression();t.initializeModel();t.initAndCreateGame();
        forge.StaticData.instance().setMulliganRule(forge.MulliganDefs.MulliganRule.London);
        forge.util.MyRandom.setRandom(new EvidenceRandom(58));
        List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("fixture"+i,null)));
        GameRules rules=new GameRules(GameType.Commander);rules.addAppliedVariant(GameType.Commander);
        Game game=new Game(seats,rules,new Match(rules,seats,"Opening instrumentation fixture"));
        String[] names={"Goro-Goro and Satoru","Ezio Auditore da Firenze","Frodo, Adventurous Hobbit","Leonardo, the Balance"};int seat=0;
        for(Player player:game.getPlayers()){
            t.fillLibrary(player,99);player.setLife(40,null);player.setStartingLife(40);
            Card c=t.addCardToZone(names[seat++],player,ZoneType.Command);c.setCommander(true);player.addCommander(c);
        }
        game.setAge(GameStage.Mulligan);DurableEvidence.begin("stage58-opening-fixture-"+args[0]);EngineEvidence.begin(game);
        Method choose=GameAction.class.getDeclaredMethod("determineFirstTurnPlayer",GameOutcome.class);choose.setAccessible(true);
        Player first=(Player)choose.invoke(game.getAction(),new Object[]{null});
        for(Player player:game.getPlayers())player.shuffle(null);
        for(Player player:game.getPlayers())player.drawCards(7);
        new MulliganService(first).perform();
        EngineEvidence.finish();
        JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");result.addProperty("fixture_only",true);result.addProperty("rules_approved",false);
        Path output=Path.of(System.getProperty("dragonmind.resultDirectory"));Files.createDirectories(output);
        DurableEvidence.finish(output,58,"OPENING_CAPTURE_FIXTURE_COMPLETE\n",result);
        System.out.println("OPENING_CAPTURE_FIXTURE_COMPLETE policy="+args[0]+"; illegal duplicate-card fixture, no game approval");System.exit(0);
    }
}
