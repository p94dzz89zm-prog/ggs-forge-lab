package forge.ai.ggs;

/** Bounded strategy profiles chosen by the external experience learner.
 * No legality, target eligibility, engine preservation or payment guard changes.
 */
public enum AdaptiveStrategy {
 BALANCED(90,6,4,4), ENGINE(120,6,4,5), ECONOMY(75,10,6,5);
 public final int dragonBonus, manaPenalty, replayPenalty, openingLandThreshold;
 AdaptiveStrategy(int dragon,int mana,int replay,int lands) {
  dragonBonus=dragon;manaPenalty=mana;replayPenalty=replay;openingLandThreshold=lands;
 }
 public static AdaptiveStrategy current() {
  return valueOf(System.getProperty("dragonmind.strategyProfile","BALANCED"));
 }
}
