import forge.ai.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.mulligan.*;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import java.lang.reflect.*;
import java.util.*;

/** Actual native round method, with independently observed declaration barrier. */
public final class MulliganRoundRegression extends AITest {
    static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        boolean house = args[0].equals("house");
        MulliganRoundRegression t = new MulliganRoundRegression();
        t.initializeModel(); forge.util.MyRandom.setRandom(new Random(56)); t.initAndCreateGame();
        List<RegisteredPlayer> seats = new ArrayList<>();
        for (int i = 0; i < 4; i++) seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat" + i, null)));
        GameRules rules = new GameRules(GameType.Commander); rules.addAppliedVariant(GameType.Commander);
        Game game = new Game(seats, rules, new Match(rules, seats, "Mulligan round regression"));
        game.setAge(GameStage.Mulligan);
        List<AbstractMulligan> policies = new ArrayList<>();
        Field count = AbstractMulligan.class.getDeclaredField("timesMulliganed"); count.setAccessible(true);
        int[] prompts = {0}; int rounds = house ? 3 : 1;
        for (Player player : game.getPlayers()) {
            t.fillLibrary(player, 30); player.setLife(40, null); player.drawCards(7);
            policies.add(house ? new HouseMulligan(player) : new LondonMulligan(player, true));
        }
        Player first = game.getPlayers().get(0);
        for (Player player : game.getPlayers()) player.dangerouslySetController(new PlayerControllerAi(game, player, player.getLobbyPlayer()) {
            @Override public boolean mulliganKeepHand(Player start, int tuck) {
                int round = prompts[0] / 4;
                try {
                    for (AbstractMulligan m : policies) {
                        require(count.getInt(m) == round, "hand changed before all round declarations: prompt=" + prompts[0]);
                        require(!m.hasKept(), "keep applied before all round declarations");
                    }
                } catch (IllegalAccessException ex) { throw new RuntimeException(ex); }
                require(start == first && tuck == 0, "unexpected first player or free-round tuck");
                System.out.println("DECLARE round=" + round + " player=" + player.getId());
                prompts[0]++;
                return round >= rounds;
            }
        });
        MulliganService service = new MulliganService(first);
        Field selected = MulliganService.class.getDeclaredField("mulligans"); selected.setAccessible(true); selected.set(service, policies);
        Method run = MulliganService.class.getDeclaredMethod("runPlayerMulligans"); run.setAccessible(true);
        try { run.invoke(service); } catch (InvocationTargetException ex) { throw new RuntimeException(ex.getCause()); }
        require(prompts[0] == (house ? 12 : 8), "wrong number of policy prompts");
        for (AbstractMulligan m : policies) {
            require(count.getInt(m) == rounds && m.hasKept(), "wrong terminal mulligan state");
            require(m.getPlayer().getCardsIn(ZoneType.Hand).size() == 7, "free redraw hand size");
            require(m.getPlayer().getCardsIn(ZoneType.Library).size() == 23, "card conservation");
        }
        System.out.println("PASS native round declarations, policy=" + args[0] + ", seed=56; scoped fixture only");
        System.exit(0);
    }
}
