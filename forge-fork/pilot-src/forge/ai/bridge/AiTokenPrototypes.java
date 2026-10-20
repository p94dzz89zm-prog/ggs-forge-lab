package forge.ai.bridge;

import forge.game.Game;
import forge.game.card.Card;
import forge.game.card.CardFactory;
import forge.game.card.token.TokenInfo;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.item.IPaperCard;
import java.util.concurrent.atomic.AtomicLong;

/** Prediction objects have unique private IDs; live and hidden IDs stay untouched. */
public final class AiTokenPrototypes {
 private static final int FIRST_PREVIEW_ID=1_000_000_000;
 private static final ThreadLocal<Integer> depth=ThreadLocal.withInitial(()->0);
 private static final AtomicLong sequence=new AtomicLong();
 private AiTokenPrototypes(){}

 public static Card getPrototype(String script,SpellAbility ability,Player player){
  int previous=depth.get();depth.set(previous+1);
  try{return TokenInfo.getProtoType(script,ability,player);}
  finally{if(previous==0)depth.remove();else depth.set(previous);}
 }

 public static Card createCard(IPaperCard paper,Player player,Game game){
  if(depth.get()==0)return CardFactory.getCard(paper,player,game);
  long serial=sequence.getAndIncrement();
  // Negative IDs make Forge skip card characteristics. Reserve the upper
  // positive range instead; instrumented live/hidden allocators reject it.
  if(serial<0||serial>Integer.MAX_VALUE-(long)FIRST_PREVIEW_ID)
   throw new IllegalStateException("AI prototype identity space exhausted");
  int id=(int)(FIRST_PREVIEW_ID+serial);
  return CardFactory.getCard(paper,player,id,game);
 }

 public static void requireLiveIdRange(int id){
  if(id<=0||id>=FIRST_PREVIEW_ID)
   throw new IllegalStateException("Live/hidden card allocator exhausted its disjoint identity range");
 }
}
