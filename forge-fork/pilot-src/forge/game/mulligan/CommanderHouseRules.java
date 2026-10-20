package forge.game.mulligan;

import forge.game.Game;
import forge.game.GameType;
import forge.game.card.Card;
import forge.game.player.Player;
import java.util.*;

/** Opt-in variant, separate from official Commander; never a legality policy. */
public final class CommanderHouseRules {
    public static final String PROFILE="ggs-house-v1";
    private CommanderHouseRules(){}
    public static boolean requested(){
        String profile=System.getProperty("dragonmind.houseProfile");
        if(profile==null)return false;
        if(!PROFILE.equals(profile))throw new IllegalStateException("Unknown Commander house profile: "+profile);
        return true;
    }
    public static boolean enabled(Game game){
        if(!requested())return false;
        if(game.getRules().getGameType()!=GameType.Commander && !game.getRules().hasAppliedVariant(GameType.Commander))
            throw new IllegalStateException("GGS house profile requires Commander");
        return true;
    }
    public static int startingLife(int original){return requested()?40:original;}
    public static AbstractMulligan mulligan(AbstractMulligan original){
        return enabled(original.getPlayer().getGame())?new HouseMulligan(original.getPlayer()):original;
    }
    public static Iterable<Map.Entry<Card,Integer>> damageForLoss(Player player){
        // Keep actual combat damage/history available to all other consumers.
        // Only the commander-damage loss test is disabled under this variant.
        return enabled(player.getGame())?Collections.emptyList():player.getCommanderDamage();
    }
}
