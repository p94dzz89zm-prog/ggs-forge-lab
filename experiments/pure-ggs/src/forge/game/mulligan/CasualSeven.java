package forge.game.mulligan;
import forge.game.Game;
import forge.game.card.*;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
/** Explicit experimental house rule; no card/rules/combat/AI changes. */
public final class CasualSeven {
 public static boolean dysfunctional(CardCollectionView hand) {
  int lands=0;boolean sol=false;
  for(Card c:hand){if(c.hasPlayableLandFace())lands++;if(c.getName().equals("Sol Ring"))sol=true;}
  return lands==0 || lands>=6 || (lands==1&&!sol);
 }
 public static void perform(Game game) {
  for(Player p:game.getPlayers()){
   int reshuffles=0;
   while(true){
    CardCollection hand=new CardCollection(p.getCardsIn(ZoneType.Hand));
    if(hand.size()!=7)throw new IllegalStateException("Casual opening hand must contain seven cards");
    boolean redo=dysfunctional(hand);
    System.out.println("DragonMind CasualSeven: player="+p.getName()+" reshuffles="+reshuffles+" redraw="+redo+" hand="+hand);
    if(!redo)break;
    if(reshuffles>=20)throw new IllegalStateException("CasualSeven redraw cap reached");
    for(Card c:hand)game.getAction().moveToLibrary(c,null);
    p.shuffle(null);p.drawCards(7);p.onMulliganned();reshuffles++;
   }
  }
 }
}
