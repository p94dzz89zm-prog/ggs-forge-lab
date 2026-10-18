package forge.ai.bridge;
/** Same seeded java.util.Random algorithm, with a private random-bit tape. */
public final class EvidenceRandom extends java.util.Random {
 public EvidenceRandom(long seed){super(seed);EngineEvidence.randomReset(seed);}
 @Override protected synchronized int next(int bits){return EngineEvidence.randomBits(bits,super.next(bits));}
}
