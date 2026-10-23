import forge.ai.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.mulligan.*;
import forge.game.player.*;
import forge.game.zone.ZoneType;
import java.lang.reflect.*;
import java.util.*;

/** Full perform(), actual policy factory and CR103.5-derived expectations. */
public final class MulliganServiceRegression extends AITest {
    static void require(boolean ok, String reason) { if (!ok) throw new AssertionError(reason); }
    static Set<Integer> ids(Player player) {
        Set<Integer> out = new HashSet<>();
        for (ZoneType zone : new ZoneType[]{ZoneType.Hand, ZoneType.Library})
            for (Card card : player.getCardsIn(zone)) require(out.add(card.getId()), "duplicate physical card");
        return out;
    }
    public static void main(String[] args) throws Exception {
        boolean house = args[0].equals("house"); int declines = args[0].equals("cap") ? 8 : house ? 3 : 2;
        require(CommanderHouseRules.requested() == house, "wrong explicit profile");
        MulliganServiceRegression t = new MulliganServiceRegression(); t.initializeModel();
        forge.util.MyRandom.setRandom(new Random(57)); t.initAndCreateGame();
        forge.StaticData.instance().setMulliganRule(forge.MulliganDefs.MulliganRule.London);
        List<RegisteredPlayer> seats = new ArrayList<>();
        for (int i = 0; i < 4; i++) seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i, null)));
        GameRules rules = new GameRules(GameType.Commander); rules.addAppliedVariant(GameType.Commander);
        Game game = new Game(seats, rules, new Match(rules, seats, "Full mulligan service"));
        game.setAge(GameStage.Mulligan);
        Map<Player, Set<Integer>> originals = new HashMap<>(); Map<Player, List<Integer>> bottoms = new HashMap<>();
        for (Player player : game.getPlayers()) { t.fillLibrary(player, 30); player.setLife(40, null); player.drawCards(7); originals.put(player, ids(player)); }
        Player first = game.getPlayers().get(2); MulliganService service = new MulliganService(first);
        Field selected = MulliganService.class.getDeclaredField("mulligans"); selected.setAccessible(true);
        Field count = AbstractMulligan.class.getDeclaredField("timesMulliganed"); count.setAccessible(true);
        int[] prompts = {0}, tucks = {0};
        for (Player player : game.getPlayers()) player.dangerouslySetController(new PlayerControllerAi(game, player, player.getLobbyPlayer()) {
            @Override public boolean mulliganKeepHand(Player start, int toBottom) {
                int round = prompts[0] / 4;
                require(round < 8, "zero-card hand was offered another mulligan");
                require(start == first && player == game.getPlayers().get((2 + prompts[0]) % 4), "starting-player turn order");
                try {
                    for (Object item : (List<?>) selected.get(service)) {
                        AbstractMulligan m = (AbstractMulligan) item;
                        require(count.getInt(m) == round, "redraw before all declarations: prompt="+prompts[0]);
                        require(!m.hasKept(), "keep before all declarations");
                        require(house ? m instanceof HouseMulligan : m instanceof LondonMulligan, "actual service policy selection");
                        int expected = house ? 7 : 7-Math.max(0, round-1);
                        require(m.getPlayer().getCardsIn(ZoneType.Hand).size() == expected, "CR103.5 hand size before decision");
                        require(ids(m.getPlayer()).equals(originals.get(m.getPlayer())), "physical card conservation");
                    }
                } catch (IllegalAccessException ex) { throw new RuntimeException(ex); }
                require(toBottom == (house ? 0 : Math.max(0, round-1)), "multiplayer first free accounting");
                System.out.println("DECLARE round="+round+" player="+player.getId()+" hand="+player.getCardsIn(ZoneType.Hand).size());
                prompts[0]++; return round >= declines;
            }
            @Override public CardCollectionView tuckCardsViaMulligan(CardCollectionView hand, int number) {
                require(!house && hand.size() == 7 && number >= 0 && number <= 7, "London draws seven before bottoming");
                CardCollection picked = new CardCollection(); List<Integer> pickedIds = new ArrayList<>();
                for (Card card : hand) if (picked.size() < number) { picked.add(card); pickedIds.add(card.getId()); }
                bottoms.put(player, pickedIds); tucks[0]++;
                System.out.println("BOTTOM player="+player.getId()+" count="+number);
                return picked;
            }
        });
        service.perform();
        require(prompts[0] == (house ? 12 : declines == 8 ? 32 : 12), "prompt count/cap");
        for (Object item : (List<?>) selected.get(service)) {
            AbstractMulligan m = (AbstractMulligan) item; Player player = m.getPlayer();
            require(count.getInt(m) == declines && m.hasKept() && !m.canMulligan(), "terminal mulligan state");
            require(player.getCardsIn(ZoneType.Hand).size() == (house ? 7 : 7-Math.max(0, declines-1)), "opening hand size");
            require(ids(player).equals(originals.get(player)), "final conservation");
            if (!house) {
                List<Integer> order = new ArrayList<>(); for (Card c : player.getCardsIn(ZoneType.Library)) order.add(c.getId());
                List<Integer> chosen = bottoms.get(player);
                require(order.subList(order.size()-chosen.size(),order.size()).equals(chosen), "chosen cards/order on library bottom");
            }
        }
        require(tucks[0] == (house ? 0 : 4*declines), "bottoming operations");
        game.setAge(GameStage.Play); Player victim=game.getPlayers().get(0), owner=game.getPlayers().get(1);
        Card commander=t.addCardToZone("Goro-Goro and Satoru",owner,ZoneType.Battlefield);commander.setCommander(true);owner.addCommander(commander);
        victim.addCommanderDamage(commander,21);require(victim.getCommanderDamage(commander)==21,"damage history retained");
        require(victim.checkLoseCondition()!=house,"commander-damage loss profile");
        if(house){victim.setLife(0,null);require(victim.checkLoseCondition(),"ordinary life loss retained");}
        System.out.println("PASS full mulligan service policy="+args[0]+" seed=57, rotated start, barrier, bottoming, conservation, cap and loss profile; not game certification");System.exit(0);
    }
}
