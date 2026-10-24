package forge.ai.bridge;
/** Same seeded java.util.Random algorithm, with a private random-bit tape. */
public final class EvidenceRandom extends java.util.Random {
 public EvidenceRandom(long seed){super(seed);EngineEvidence.randomReset(seed);}
 @Override protected synchronized int next(int bits){if(Boolean.getBoolean("forge.evidence.traceRandom")){System.err.println("DRAGONMIND_RANDOM_ORIGIN bits="+bits);for(StackTraceElement frame:Thread.currentThread().getStackTrace())System.err.println("  "+frame);}return EngineEvidence.randomBits(bits,DecisionReplay.engineRandom(bits,super.next(bits)));}
}
