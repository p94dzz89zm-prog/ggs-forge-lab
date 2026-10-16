package forge.ai.bridge;

import com.google.gson.*;
import forge.LobbyPlayer;
import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.ZoneType;
import forge.util.collect.FCollectionView;
import java.nio.file.*;
import java.util.*;

/** Assisted remote seat: external strategic choices, stock automatic mana/cost payment.
 * Unoverridden controller hooks remain stock AI; this is not a fully manual controller.
 */
public class PlayerControllerBridge extends PlayerControllerAi {
    private final BridgeChannel channel;
    private final boolean remote;
    public PlayerControllerBridge(Game game,Player player,LobbyPlayer lobby) {
        super(game,player,lobby);
        remote=player.getName().equals(System.getProperty("forge.bridge.player",""));
        channel=remote?new BridgeChannel(Path.of(System.getProperty("forge.bridge.directory","bridge"))):null;
    }
    private JsonObject request(String kind,JsonArray options) {
        JsonObject q=new JsonObject();q.addProperty("kind",kind);q.add("state",BridgeSnapshot.forPlayer(player));q.add("options",options);
        q.addProperty("assistance","Stock automatic mana, costs, mulligans, damage assignment and unoverridden hooks; use auto only explicitly.");
        return q;
    }
    private void audit(String kind,JsonObject detail) {
        String dir=System.getProperty("forge.audit.directory");if(dir==null)return;
        String selected=System.getProperty("forge.audit.player");if(selected!=null&&!selected.equals(player.getName()))return;
        JsonObject row=request(kind,new JsonArray());row.add("decision",detail);
        try {BridgeChannel.append(Path.of(dir, "seat-"+player.getId()+".jsonl"),row.toString());}
        catch(java.io.IOException e){throw new IllegalStateException("Audit write failed",e);}
    }
    private boolean auto(JsonObject r){return r.has("auto") && r.get("auto").getAsBoolean();}
    private JsonArray options(Collection<? extends GameEntity> choices) {
        JsonArray result=new JsonArray();int i=0;
        for(GameEntity e:choices){JsonObject o=BridgeSnapshot.entity(e,player);
            // An engine-issued search prompt permits the chooser to inspect its own library options.
            if(e instanceof Card c && c.getOwner()==player && c.isInZone(ZoneType.Library))o.addProperty("name",c.getName());
            o.addProperty("index",i++);result.add(o);}
        return result;
    }
    private int index(JsonObject r,int size,boolean optional){
        int i=r.get("index").getAsInt();if(i==-1 && optional)return i;
        if(i<0 || i>=size)throw new IllegalArgumentException("Choice index outside engine options");return i;
    }
    @Override public String chooseSomeType(String type,SpellAbility sa,Collection<String> valid,boolean optional){
        String chosen;
        if(remote){JsonArray os=new JsonArray();for(String s:valid)os.add(s);JsonObject q=request("type",os);q.addProperty("card",sa.getHostCard().getName());JsonObject r=channel.ask(q);
            chosen=auto(r)?super.chooseSomeType(type,sa,valid,optional):r.get("type").getAsString();
            if(!valid.contains(chosen))throw new IllegalArgumentException("Type not offered by engine");
        }else chosen=super.chooseSomeType(type,sa,valid,optional);
        JsonObject d=new JsonObject();d.addProperty("card",sa.getHostCard().getName());d.addProperty("chosen_type",chosen);audit("type",d);return chosen;
    }
    @Override public List<SpellAbility> chooseSpellAbilityToPlay(){
        if(!remote){List<SpellAbility> picked=super.chooseSpellAbilityToPlay();JsonObject d=new JsonObject();d.addProperty("action",picked==null?"pass":picked.toString());audit("priority",d);return picked;}
        CardCollection cards=new CardCollection(player.getCardsIn(ZoneType.Hand,ZoneType.Graveyard,ZoneType.Command));
        cards.addAll(getGame().getCardsIn(ZoneType.Battlefield));
        for(Card c:getGame().getCardsIn(ZoneType.Exile))if(!c.isFaceDown())cards.add(c);
        List<SpellAbility> available=new ArrayList<>();
        CardCollection lands=ComputerUtilAbility.getAvailableLandsToPlay(getGame(),player);
        if(lands!=null)for(Card c:lands) {
            if(c.isInZone(ZoneType.Library))continue;
            LandAbility land=new LandAbility(c,c.getCurrentState());land.setActivatingPlayer(player);if(land.canPlay())available.add(land);
        }
        for(SpellAbility sa:ComputerUtilAbility.getSpellAbilities(cards,player)) {
            sa.setActivatingPlayer(player);
            if(!sa.isManaAbility() && sa.canPlay())available.add(sa);
        }
        JsonArray os=new JsonArray();for(int i=0;i<available.size();i++){SpellAbility sa=available.get(i);JsonObject o=BridgeSnapshot.entity(sa.getHostCard(),player);o.addProperty("index",i);o.addProperty("description",sa.toString());o.addProperty("cost",String.valueOf(sa.getPayCosts()));os.add(o);}
        JsonObject q=request("priority",os);q.addProperty("options_are","Timing-eligible engine candidates; payment and targets are rechecked after selection.");
        JsonObject r=channel.ask(q);if(auto(r))return super.chooseSpellAbilityToPlay();
        int i=index(r,available.size(),true);if(i==-1)return null;
        SpellAbility selected=available.get(i);
        if(r.has("x")){int x=r.get("x").getAsInt();if(x<0)throw new IllegalArgumentException("Negative X");selected.setXManaCostPaid(x);}
        if(!selected.canPlay())throw new IllegalArgumentException("Ability timing changed");
        for(SpellAbility part=selected;part!=null;part=part.getSubAbility())if(part.usesTargeting() && !chooseTargetsFor(part))throw new IllegalArgumentException("Invalid targets");
        if(!selected.isLandAbility() && !ComputerUtilCost.canPayCost(selected,player,false))throw new IllegalArgumentException("Selected ability is not payable");
        return Collections.singletonList(selected);
    }
    @Override public boolean playChosenSpellAbility(SpellAbility sa){
        if(!remote)return super.playChosenSpellAbility(sa);
        if(sa.isLandAbility()){if(!sa.canPlay())return false;sa.resolve();return true;}
        // Unlike stock implementation, preserve the payment routine's actual success result.
        return ComputerUtil.handlePlayingSpellAbility(player,sa,null);
    }
    @Override public boolean chooseTargetsFor(SpellAbility sa){
        if(!remote)return super.chooseTargetsFor(sa);
        sa.resetTargets();
        List<GameEntity> candidates=sa.getTargetRestrictions().getAllCandidates(sa);
        JsonObject q=request("targets",options(candidates));q.addProperty("description",sa.toString());q.addProperty("min",sa.getMinTargets());q.addProperty("max",sa.getMaxTargets());
        JsonObject r=channel.ask(q);if(auto(r))return super.chooseTargetsFor(sa);
        Set<Integer> seen=new HashSet<>();
        for(JsonElement e:r.getAsJsonArray("indices")){int i=e.getAsInt();if(i<0||i>=candidates.size()||!seen.add(i))throw new IllegalArgumentException("Invalid target index");GameEntity target=candidates.get(i);if(!sa.canTarget(target))throw new IllegalArgumentException("Target no longer valid");sa.getTargets().add(target);}
        return sa.isTargetNumberValid();
    }
    @Override public <T extends GameEntity>T chooseSingleEntityForEffect(FCollectionView<T> choices,DelayedReveal reveal,SpellAbility sa,String title,boolean optional,Player target,Map<String,Object> params){
        if(!remote)return super.chooseSingleEntityForEffect(choices,reveal,sa,title,optional,target,params);
        if(reveal!=null)reveal(reveal);
        List<T> list=new ArrayList<>();for(T e:choices)list.add(e);
        JsonObject q=request("entity",options(list));q.addProperty("title",title);q.addProperty("optional",optional);
        JsonObject r=channel.ask(q);if(auto(r))return super.chooseSingleEntityForEffect(choices,null,sa,title,optional,target,params);
        int i=index(r,list.size(),optional);return i==-1?null:list.get(i);
    }
    @Override public CardCollectionView chooseCardsForEffect(CardCollectionView choices,SpellAbility sa,String title,int min,int max,boolean optional,Map<String,Object> params){
        if(!remote)return super.chooseCardsForEffect(choices,sa,title,min,max,optional,params);
        List<Card> list=new ArrayList<>();for(Card c:choices)list.add(c);
        JsonObject q=request("cards",options(list));q.addProperty("title",title);q.addProperty("min",min);q.addProperty("max",max);
        JsonObject r=channel.ask(q);if(auto(r))return super.chooseCardsForEffect(choices,sa,title,min,max,optional,params);
        CardCollection selected=new CardCollection();Set<Integer> seen=new HashSet<>();
        for(JsonElement e:r.getAsJsonArray("indices")){int i=e.getAsInt();if(i<0||i>=list.size()||!seen.add(i))throw new IllegalArgumentException("Invalid card index");selected.add(list.get(i));}
        if(selected.size()>max || (selected.size()<min && !(optional && selected.isEmpty())))throw new IllegalArgumentException("Wrong number of cards");return selected;
    }
    @Override public Card chooseSingleCardForZoneChange(ZoneType destination,List<ZoneType> origin,
            SpellAbility sa,CardCollection fetchList,DelayedReveal reveal,String prompt,boolean optional,Player decider){
        if(!remote)return super.chooseSingleCardForZoneChange(destination,origin,sa,fetchList,reveal,prompt,optional,decider);
        if(reveal!=null)reveal(reveal);
        List<Card> list=new ArrayList<>();for(Card card:fetchList)list.add(card);
        JsonObject q=request("entity",options(list));q.addProperty("title",prompt);q.addProperty("optional",optional);
        JsonObject r=channel.ask(q);
        if(auto(r))return super.chooseSingleCardForZoneChange(destination,origin,sa,fetchList,null,prompt,optional,decider);
        int i=index(r,list.size(),optional);return i==-1?null:list.get(i);
    }
    @Override public SpellAbility chooseSingleSpellForEffect(List<SpellAbility> spells,SpellAbility sa,
            String title,Map<String,Object> params){
        if(!remote)return super.chooseSingleSpellForEffect(spells,sa,title,params);
        JsonArray choices=new JsonArray();
        for(int i=0;i<spells.size();i++){
            JsonObject option=new JsonObject();option.addProperty("index",i);
            option.addProperty("name",spells.get(i).getDescription());choices.add(option);
        }
        JsonObject q=request("entity",choices);q.addProperty("title",title);q.addProperty("optional",false);
        JsonObject r=channel.ask(q);
        if(auto(r))return super.chooseSingleSpellForEffect(spells,sa,title,params);
        return spells.get(index(r,spells.size(),false));
    }
    @Override public boolean confirmAction(SpellAbility sa,PlayerActionConfirmMode mode,String message,List<String> opts,Card card,Map<String,Object> params){
        if(!remote)return super.confirmAction(sa,mode,message,opts,card,params);
        JsonObject q=request("confirm",new JsonArray());q.addProperty("message",message);JsonObject r=channel.ask(q);
        return auto(r)?super.confirmAction(sa,mode,message,opts,card,params):r.get("yes").getAsBoolean();
    }
    @Override public int chooseNumber(SpellAbility sa,String title,int min,int max){
        if(!remote)return super.chooseNumber(sa,title,min,max);
        JsonObject q=request("number",new JsonArray());q.addProperty("title",title);q.addProperty("min",min);q.addProperty("max",max);JsonObject r=channel.ask(q);
        int n=auto(r)?super.chooseNumber(sa,title,min,max):r.get("number").getAsInt();if(n<min||n>max)throw new IllegalArgumentException("Number outside bounds");return n;
    }
    @Override public void declareAttackers(Player attacker,Combat combat){
        if(!remote){super.declareAttackers(attacker,combat);return;}
        JsonArray os=new JsonArray();Map<String,Map.Entry<Card,GameEntity>> pairs=new HashMap<>();
        for(Card c:player.getCreaturesInPlay())for(GameEntity defender:combat.getDefenders())if(CombatUtil.canAttack(c,defender)){
            String key=c.getId()+":"+defender.getId();JsonObject o=new JsonObject();o.addProperty("key",key);o.add("attacker",BridgeSnapshot.entity(c,player));o.add("defender",BridgeSnapshot.entity(defender,player));os.add(o);pairs.put(key,Map.entry(c,defender));}
        JsonObject r=channel.ask(request("attack",os));if(auto(r)){super.declareAttackers(attacker,combat);return;}
        Set<Card> seen=new HashSet<>();for(JsonElement e:r.getAsJsonArray("pairs")){var pair=pairs.get(e.getAsString());if(pair==null||!seen.add(pair.getKey()))throw new IllegalArgumentException("Invalid attack");combat.addAttacker(pair.getKey(),pair.getValue());}
        if(!CombatUtil.validateAttackers(combat))throw new IllegalArgumentException("Attack violates engine constraints");
    }
    @Override public void declareBlockers(Player defender,Combat combat){
        if(!remote){super.declareBlockers(defender,combat);return;}
        JsonArray os=new JsonArray();Map<String,Map.Entry<Card,Card>> pairs=new HashMap<>();
        for(Card attacker:combat.getAttackers())for(Card blocker:player.getCreaturesInPlay())if(CombatUtil.canBlock(attacker,blocker,combat)){
            String key=attacker.getId()+":"+blocker.getId();JsonObject o=new JsonObject();o.addProperty("key",key);o.add("attacker",BridgeSnapshot.entity(attacker,player));o.add("blocker",BridgeSnapshot.entity(blocker,player));os.add(o);pairs.put(key,Map.entry(attacker,blocker));}
        JsonObject r=channel.ask(request("block",os));if(auto(r)){super.declareBlockers(defender,combat);return;}
        Set<String> seen=new HashSet<>();for(JsonElement e:r.getAsJsonArray("pairs")){String key=e.getAsString();var pair=pairs.get(key);if(pair==null||!seen.add(key))throw new IllegalArgumentException("Invalid block");combat.addBlocker(pair.getKey(),pair.getValue());}
        String error=CombatUtil.validateBlocks(combat,defender);if(error!=null)throw new IllegalArgumentException(error);
    }
}
