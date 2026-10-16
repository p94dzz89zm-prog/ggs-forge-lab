# March and blocked trample

A constructed combat exposed a losing target choice at 2 life. Balefire Dragon
blocked Typhoid Rats while Memnite blocked Colossal Dreadmaw. With only enough
mana for X=1, the incumbent phased Balefire. After actual payment and resolution,
five trample damage reduced the pilot to -3. Phasing Dreadmaw preserves 2 life.

The additional public-state forecast considers ordinary blocked trample during
the blockers step. It subtracts the engine's blocker shielding forecast and
uses the existing damage/prevention prediction. The previous empty-stack lethal
priority can then rank this threat ahead of preserving a valuable blocker.
This addition excludes infect and first/double-strike attackers or blockers.
Other combat mechanics and complicated stacks remain outside its tested scope.
No card definition, cost, timing restriction or resolution rule is changed.

MarchTrampleRegression contains eight boundary positions under three bounded
profiles: lethal spillover, different bodies/blockers, a third player's combat,
no trample, an untargetable threat, nonlethal damage and unavailable blue mana.
These are 24 correlated profile/boundary checks, not 24 independent games.
Legal blocks and engine damage orders are initialized before actual payment and
combat. CounterRescuePaymentRegression separately executes both counterspell
choices at three life totals, verifying payment, resolution and combat.

An initial trample probe omitted damage-assignment ordering and dealt six rather
than five player damage. That fixture error was corrected before accepting the
reproduction. The failed attempt remains private diagnostic evidence; it is not
a natural-game rules finding. Never change card rules to repair a fixture.

build_march_trample.py overlays only FireworkPilotPolicy.class on the pinned
recovered counter-rescue executable. It preserves earlier combined-lethal,
haste and March corrections. Keep raw games, hands, audits and model state
private. Whole-game learning still requires evidence-bound all-seat review;
these scoped checks do not establish general strength or error-free play.
