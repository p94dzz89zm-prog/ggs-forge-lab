package forge.game.mulligan;

import forge.game.player.Player;

/** Explicit GGS house rule: at most three complete reshuffles, always seven. */
public final class HouseMulligan extends AbstractMulligan {
    public HouseMulligan(Player player){super(player,false);}
    @Override public boolean canMulligan(){return !kept && timesMulliganed<3 && player.canMulligan();}
    @Override public int handSizeAfterNextMulligan(){return 7;}
    @Override public void mulligan(){
        if(!canMulligan())throw new IllegalStateException("House mulligan unavailable");
        super.mulligan();
    }
    @Override public int tuckCardsDuringMulligan(){return 0;}
}
