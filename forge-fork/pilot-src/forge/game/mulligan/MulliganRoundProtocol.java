package forge.game.mulligan;

import java.util.ArrayList;
import java.util.List;

/** CR 103.5: finish the round's declarations before changing any hand. */
public final class MulliganRoundProtocol {
    private MulliganRoundProtocol() {}

    public static void run(MulliganService service) {
        while (true) {
            List<AbstractMulligan> participants = new ArrayList<>();
            List<Boolean> keeps = new ArrayList<>();
            boolean allKept = true;
            for (AbstractMulligan mulligan : service.mulligans) {
                if (mulligan.hasKept()) continue;
                boolean keep = !mulligan.canMulligan() ||
                    mulligan.getPlayer().getController().mulliganKeepHand(
                        service.firstPlayer, mulligan.tuckCardsDuringMulligan());
                if (service.game.isGameOver()) return;
                participants.add(mulligan);
                keeps.add(keep);
                allKept &= keep;
            }
            for (int i = 0; i < participants.size(); i++) {
                if (keeps.get(i)) participants.get(i).keep();
                else participants.get(i).mulligan();
            }
            if (allKept) return;
        }
    }
}
