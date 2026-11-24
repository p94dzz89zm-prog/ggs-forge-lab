package forge.ai.validation;

import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/** Called synchronously only from the pinned controller's native declaration window. */
public final class IndependentOpening {
    private static final BufferedReader replies = new BufferedReader(
            new InputStreamReader(System.in, StandardCharsets.UTF_8));
    private static final int[] revisions = new int[4];
    private static final boolean[] kept = new boolean[4];
    private IndependentOpening() {}

    public static synchronized boolean wantMulligan(Player actor, int count) {
        int seat = actor.getId();
        if (!Boolean.getBoolean("dragonmind.openingFixture")
                || !"ggs-house-v1".equals(System.getProperty("dragonmind.houseProfile"))
                || !"".equals(System.getProperty("forge.ai.ggsPilotPlayer",""))
                || seat < 0 || seat > 3 || kept[seat] || revisions[seat] >= 3
                || actor.getCardsIn(ZoneType.Hand).size() != 7 || !actor.canMulligan())
            throw new IllegalStateException("Outside native house declaration window");
        int lands = 0, early = 0;
        for (Card card : actor.getCardsIn(ZoneType.Hand)) {
            if (SharedOpening.landOption(card)) lands++;
            else if (SharedOpening.earlySpell(card)) early++;
        }
        boolean cheap = false;
        for (Card card : actor.getCardsIn(ZoneType.Command))
            if (card.isCommander() && SharedOpening.earlySpell(card)) cheap = true;
        System.out.printf("DM_OFFER {\"game\":\"opening\",\"seat\":%d,\"revision\":%d,"
                + "\"actions\":[\"keep\",\"redraw\"],\"observation\":"
                + "{\"lands\":%d,\"early\":%d,\"cheap_commander\":%b}}%n",
                seat, revisions[seat], lands, early, cheap);
        System.out.flush();
        String prefix = "opening " + seat + " " + revisions[seat] + " ";
        try {
            String answer = replies.readLine();
            if (!(prefix+"keep").equals(answer) && !(prefix+"redraw").equals(answer))
                throw new IllegalArgumentException("Stale or unoffered pilot reply");
            revisions[seat]++;
            kept[seat] = answer.equals(prefix+"keep");
            return !kept[seat];
        } catch (java.io.IOException e) {
            throw new IllegalStateException("Pilot pipe failed", e);
        }
    }
}
