import forge.ai.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import java.lang.reflect.Method;
import java.util.*;

/** Native SBA/trigger/stack boundary; no recorded decisions or model fitting. */
public class StateReadinessRegression extends AITest {
    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        StateReadinessRegression t = new StateReadinessRegression();
        t.initializeModel(); t.initAndCreateGame();
        List<RegisteredPlayer> seats = new ArrayList<>();
        for (int i = 0; i < 4; i++) seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat" + i, null)));
        GameRules rules = new GameRules(GameType.Commander);
        Game game = new Game(seats, rules, new Match(rules, seats, "SBA readiness fixture"));
        for (Player seat : game.getPlayers()) t.fillLibrary(seat, 10);
        game.setAge(GameStage.Play);
        Player p = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, p, false);
        game.getPhaseHandler().setPriority(p);
        Card bear = t.addCardToZone("Grizzly Bears", p, ZoneType.Battlefield);
        Card myr = t.addCardToZone("Darksteel Myr", p, ZoneType.Battlefield);
        Card zero = t.addCardToZone("Darksteel Myr", p, ZoneType.Battlefield);
        Card dissenter = t.addCardToZone("Doomed Dissenter", p, ZoneType.Battlefield);
        zero.setBaseToughness(0); // Explicit synthetic current-characteristic fixture.
        game.getAction().checkStaticAbilities();
        game.getTriggerHandler().resetActiveTriggers();
        bear.setDamage(2); myr.setDamage(1); dissenter.setDamage(1);
        game.copyLastState(); // Match the native action boundary's LTB history.
        require(game.getStack().isEmpty(), "Fixture must begin with an empty stack");
        require(bear.getNetToughness() == 2 && myr.getNetToughness() == 1 && zero.getNetToughness() == 0,
                "Fixture characteristics differ");
        require(myr.hasKeyword("Indestructible") && zero.hasKeyword("Indestructible"), "Missing indestructible control");

        // Invoke the same native readiness routine used before controller priority.
        Method ready = PhaseHandler.class.getDeclaredMethod("checkStateBasedEffects");
        ready.setAccessible(true);
        require(Boolean.FALSE.equals(ready.invoke(game.getPhaseHandler())), "Unexpected game termination");
        require(bear.isInZone(ZoneType.Graveyard), "Lethal damage survived SBA");
        require(myr.isInZone(ZoneType.Battlefield) && myr.getDamage() == 1, "Indestructible lethal-damage control failed");
        require(zero.isInZone(ZoneType.Graveyard), "Zero toughness incorrectly treated as destruction");
        require(dissenter.isInZone(ZoneType.Graveyard), "Death-trigger source survived lethal damage");
        require(game.getStack().size() == 1, "Death trigger not staged before priority boundary; stack=" + game.getStack().size());
        require(p.getCardsIn(ZoneType.Battlefield).stream().noneMatch(Card::isToken), "Death trigger resolved prematurely");
        require(Boolean.FALSE.equals(ready.invoke(game.getPhaseHandler())) && game.getStack().size() == 1,
                "Readiness duplicated or resolved a pending trigger");
        game.getStack().resolveStack();
        var tokens = p.getCardsIn(ZoneType.Battlefield).stream().filter(Card::isToken).toList();
        require(tokens.size() == 1 && tokens.get(0).getNetPower() == 2 && tokens.get(0).getNetToughness() == 2,
                "Death trigger did not natively create exactly one 2/2 token");
        require(tokens.get(0).getOwner() == p && tokens.get(0).getController() == p && game.getStack().isEmpty(),
                "Resolved token ownership/controller or stack differs");
        require(Boolean.FALSE.equals(ready.invoke(game.getPhaseHandler())) && game.getStack().isEmpty(),
                "Post-resolution readiness not stable");
        System.out.println("PASS StateReadinessRegression: lethal damage, indestructible, zero toughness, death trigger staging, deferred resolution, token ownership, stable readiness");
        System.out.println("SCOPE native constructed four-player fixture; no complete game or independent global priority approval");
        System.exit(0);
    }
}
