package forge.ai.ggs;

/** Externally explored tactical weights. Legality and preservation guards remain
 * outside the tunable score. Missing overrides reproduce the archived policy.
 */
public record DecisionWeights(int damage, int hitPercent, int dragon, int mana,
                              int replay, int bodyDivisor) {
    private static int parameter(String key, int fallback, int min, int max) {
        String value = System.getProperty("dragonmind.weight." + key);
        if (value == null) return fallback;
        int parsed = Integer.parseInt(value);
        if (parsed < min || parsed > max) throw new IllegalArgumentException("Weight outside safe search range: " + key);
        return parsed;
    }
    public static DecisionWeights current() {
        AdaptiveStrategy s = AdaptiveStrategy.current();
        return new DecisionWeights(parameter("damage",10,4,20), parameter("hitPercent",100,25,200),
            parameter("dragon",s.dragonBonus,0,180), parameter("mana",s.manaPenalty,0,16),
            parameter("replay",s.replayPenalty,0,16), parameter("bodyDivisor",8,4,16));
    }
}
