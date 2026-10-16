package forge.ai.ggs;

import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.util.MyRandom;
import java.util.Random;

/** Per-thread branch scope. No branch may consume the live game's RNG. */
public final class PlannerContext implements AutoCloseable {
    private static final ThreadLocal<Integer> DEPTH = ThreadLocal.withInitial(() -> 0);
    public static final String UNKNOWN = "DragonMind Unknown Card";
    private final Random previousRandom;
    private final int previousDepth;
    private PlannerContext(long seed) {
        previousDepth=DEPTH.get();previousRandom=MyRandom.getRandom();
        DEPTH.set(previousDepth+1);MyRandom.setRandom(new Random(seed));
    }
    public static PlannerContext enter(long seed) { return new PlannerContext(seed); }
    public static boolean active() { return DEPTH.get()>0; }
    public static boolean hidden(Card card,Player viewer) {
        return active() && (card.isInZone(ZoneType.Library)
            || card.isInZone(ZoneType.Hand) && (viewer==null || !viewer.getCardsIn(ZoneType.Hand).contains(card))
            || card.isInZone(ZoneType.Exile) && card.isFaceDown());
    }
    @Override public void close() {MyRandom.setRandom(previousRandom);DEPTH.set(previousDepth);}
}
