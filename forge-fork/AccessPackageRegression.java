import forge.ai.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Actual Forge cost/effect/blocking checks, not a replacement simulator. */
public class AccessPackageRegression extends AITest {
 int checks;
 void pass(String label) { checks++; System.out.println("PASS "+label); }
 AiController pilot(Player p) {return ((PlayerControllerAi)p.getController()).getAi();}
 void enabled(Player p, boolean on) {if(on)System.setProperty("forge.ai.ggsPilotPlayer",p.getName());else System.clearProperty("forge.ai.ggsPilotPlayer");}
 SpellAbility effect(Card c,Player p) {SpellAbility s=c.getSpellAbilities().stream().filter(a->a.getApi()==ApiType.Effect).findFirst().orElseThrow();s.setActivatingPlayer(p);return s;}
 void ready(Game g) {for(Player p:g.getPlayers())fillLibrary(p,10);g.getAction().checkStateEffects(true);}
 void attack(Game g,Player ai,Player opp,Card body,boolean fresh) {
  g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);
  body.setSickness(false);body.setTurnInZone(g.getPhaseHandler().getTurn()-(fresh?0:1));
  Combat c=new Combat(ai);c.addAttacker(body,opp);g.getPhaseHandler().setCombat(c);
 }
 void activation(String name,boolean on,boolean mana,boolean fresh,boolean open,boolean commander,boolean late,int oppMana) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enabled(ai,on);
  if(commander)addCard("Goro-Goro and Satoru",ai).setCommander(true);
  Card host=addCard(name,ai);
  Card body=name.equals("Gingerbrute")?host:addCard(open?"Changeling Outcast":name.startsWith("Higure")?"Thousand-Faced Shadow":"Runeclaw Bear",ai);
  Card blocker=addCard(name.startsWith("Higure")?"Birds of Paradise":"Runeclaw Bear",opp);
  if(mana){addCard("Mountain",ai);addCard("Island",ai);}else if(name.equals("War Cadence"))addCard("Mountain",ai);
  for(int i=0;i<oppMana;i++)addCard("Island",opp);
  ready(g);attack(g,ai,opp,body,fresh);
  if(late)g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  SpellAbility s=effect(host,ai);
  boolean expected=on&&mana&&fresh&&!open&&commander&&!late&&oppMana==0;
  boolean play=pilot(ai).canPlaySa(s).willingToPlay();
  Assert.assertEquals(play,expected,name+" on="+on+" mana="+mana+" fresh="+fresh+" open="+open+" commander="+commander+" late="+late+" oppMana="+oppMana);
  if(play){
   if(name.startsWith("Higure"))Assert.assertTrue(s.getTargets().contains(body));
   if(name.equals("War Cadence"))Assert.assertEquals(s.getXManaCostPaid().intValue(),1);
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,s,null),"actual cost payment "+name);
   g.getStack().resolveStack();
   if(name.equals("War Cadence")){
    new AiBlockController(opp,false).assignBlockersForCombat(g.getCombat());
    Assert.assertTrue(g.getCombat().getBlockers(body).isEmpty(),"paid Cadence denies actual block");
   }else Assert.assertFalse(CombatUtil.canBlock(body,blocker),"effect grants actual access");
   Assert.assertFalse(pilot(ai).canPlaySa(s).willingToPlay(),"no repeat activation");
  }
  pass(name+" guard/resolution "+on+"/"+mana+"/"+fresh+"/"+open+"/"+commander+"/"+late+"/"+oppMana);
 }
 void passive(){
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enabled(ai,true);
  Card atsu=addCard("Tetsuko Umezawa, Fugitive",ai),kari=addCard("Kari Zev, Skyship Raider",ai),ragavan=addToken("ragavan",ai),bear=addCard("Runeclaw Bear",opp);
  ready(g);Assert.assertFalse(CombatUtil.canBlock(kari,bear));Assert.assertFalse(CombatUtil.canBlock(ragavan,bear));pass("Atsu opens Kari and actual Ragavan token");
  g.getAction().moveToGraveyard(atsu,null);g.getAction().checkStateEffects(true);Assert.assertTrue(CombatUtil.canBlock(kari,bear));pass("Atsu removal restores blocking");
  Card cover=addCard("Cover of Darkness",ai);cover.setChosenType("Goblin");Card own=addCard("Goro-Goro and Satoru",ai),enemy=addCard("Goblin Piker",opp),black=addCard("Royal Assassin",opp),artifact=addCard("Gingerbrute",opp),ownBear=addCard("Runeclaw Bear",ai);g.getAction().checkStateEffects(true);
  Assert.assertTrue(own.hasKeyword(forge.game.keyword.Keyword.FEAR));Assert.assertTrue(enemy.hasKeyword(forge.game.keyword.Keyword.FEAR));Assert.assertFalse(CombatUtil.canBlock(own,bear));Assert.assertTrue(CombatUtil.canBlock(own,black));Assert.assertTrue(CombatUtil.canBlock(own,artifact));Assert.assertFalse(CombatUtil.canBlock(enemy,ownBear));pass("Cover is global and preserves black/artifact exceptions");
  Card outcast=addCard("Changeling Outcast",ai),bird=addCard("Birds of Paradise",opp),phoenix=addCard("Phoenix Chick",ai),dauthi=addCard("Dauthi Voidwalker",ai),otherShadow=addCard("Dauthi Voidwalker",opp);g.getAction().checkStateEffects(true);
  Assert.assertFalse(CombatUtil.canBlock(outcast,bear));Assert.assertFalse(CombatUtil.canBlock(outcast,bird));Assert.assertFalse(CombatUtil.canBlock(phoenix,bear));Assert.assertTrue(CombatUtil.canBlock(phoenix,bird));Assert.assertFalse(CombatUtil.canBlock(dauthi,bear));Assert.assertTrue(CombatUtil.canBlock(dauthi,otherShadow));pass("natural unblockable, flying and shadow");
  SpellAbility h=effect(addCard("Higure, the Still Wind",ai),ai);Card rogue=addCard("Tetsuko Umezawa, Fugitive",ai);Assert.assertFalse(h.canTarget(rogue));Assert.assertFalse(h.canTarget(own));Assert.assertTrue(h.canTarget(outcast));pass("Higure targets Ninjas/changelings, not Atsu or GGS");
 }
 void publicManaAndDefender(){
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),defender=g.getPlayers().get(0),other=g.getPlayers().get(2);enabled(ai,true);
  addCard("Goro-Goro and Satoru",ai);Card cadence=addCard("War Cadence",ai),body=addCard("Runeclaw Bear",ai);addCard("Runeclaw Bear",defender);
  addCard("Mountain",ai);addCard("Island",ai);addCard("Island",ai);addCard("Island",defender);
  for(int i=0;i<6;i++)addCard("Island",other);other.setLife(80,null);
  ready(g);attack(g,ai,defender,body,true);SpellAbility s=effect(cadence,ai);
  Assert.assertTrue(pilot(ai).canPlaySa(s).willingToPlay());Assert.assertEquals(s.getXManaCostPaid().intValue(),2);
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,s,null));g.getStack().resolveStack();
  new AiBlockController(defender,false).assignBlockersForCombat(g.getCombat());Assert.assertTrue(g.getCombat().getBlockers(body).isEmpty());pass("Cadence pays X=2 against actual defender, ignoring unrelated opponent's mana");
  g=initAndCreateGame();ai=g.getPlayers().get(1);defender=g.getPlayers().get(0);enabled(ai,true);addCard("Goro-Goro and Satoru",ai);body=addCard("Gingerbrute",ai);addCard("Phoenix Chick",defender);addCard("Island",ai);
  ready(g);attack(g,ai,defender,body,true);s=effect(body,ai);Assert.assertFalse(pilot(ai).canPlaySa(s).willingToPlay());pass("Gingerbrute does not buy evasion against a haste blocker");
 }
 public static void main(String[]args){
  AccessPackageRegression t=new AccessPackageRegression();t.initializeModel();t.passive();t.publicManaAndDefender();
  for(String name:List.of("Higure, the Still Wind","War Cadence","Gingerbrute")){
   t.activation(name,true,true,true,false,true,false,0);
   t.activation(name,false,true,true,false,true,false,0);
   t.activation(name,true,false,true,false,true,false,0);
   t.activation(name,true,true,false,false,true,false,0);
   if(!name.equals("Gingerbrute"))t.activation(name,true,true,true,true,true,false,0);
   t.activation(name,true,true,true,false,false,false,0);
   t.activation(name,true,true,true,false,true,true,0);
   if(name.equals("War Cadence"))t.activation(name,true,true,true,false,true,false,1);
  }
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
