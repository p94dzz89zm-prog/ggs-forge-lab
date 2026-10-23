package forge.game.mulligan;

/** CR103.5/103.5c: no further mulligan after an opening hand of zero. */
public final class LondonMulliganLimit {
    private LondonMulliganLimit() {}
    public static boolean canMulligan(LondonMulligan mulligan) {
        return !mulligan.hasKept() &&
            mulligan.tuckCardsDuringMulligan() < mulligan.player.getMaxHandSize();
    }
}
