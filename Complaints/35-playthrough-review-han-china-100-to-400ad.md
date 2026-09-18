# Playthrough review: Han China, 100-400 AD

**Type:** Realism review, external
**Priority:** Reference document. Several items already have work in flight.
**Status:** Recorded at the stakeholder's request. NOTHING HERE HAS BEEN
ACTED ON, and nothing in it was investigated before writing - it is the
reviewer's account, kept as given, with project state noted where this
repository already knows something about a point.

The reviewer's own framing is worth keeping: the prose explanations should
NOT be stripped in favour of pure numbers, "because I'm supposed to reason
about the world, not just optimize numbers."

---

## 1. Interface: an agent-oriented compact mode

The single biggest improvement suggested. An explicit structured mode -
concise JSON or JSONL for `state`, `available`, `why` and so on - that
returns machine-readable state WITHOUT discarding the human-readable
explanation. The game accepts JSON input already, but its output is still
primarily prose and tables.

Explicitly NOT a request to remove the prose. Both, addressed to different
readers, from one command.

## 2. Historical omissions

**State monopolies (the Salt and Iron debate).** Han and Jin China ran
imperial monopolies - `yantie` - over iron casting, salt and liquor. A
private citizen operating blast furnaces, rolling mills and distillation
towers would have been nationalised by imperial tax commissioners.

*Project state:* this repository arrived at the same conclusion from the
opposite direction on the same day, and by measurement rather than by
history. `Complaints/32` records that once Ricardian rent was computed
properly, mercury still priced ~1,440x below book, and the leading
explanation is that Roman mercury was a STATE MONOPOLY capping output below
what Almaden could produce, forcing the margin onto a worse deposit. That is
the first case here where an institution sets a price no physical mechanism
can. The Chinese case is the same mechanism at larger scale.

**Geographic logistics and raw material transport.** Coking coal, zinc ore,
quartz and mercury are abstract capital purchases rather than physical
freight on canals and rivers. No need to secure mining concessions in
specific provinces.

*Project state:* `sim/world/transport.py` now derives freight cost per
tonne-km from animal metabolism and rolling resistance, and
`sim/world/deposits.py` gives minerals locations, grades and finite stocks.
Neither is wired into the engine. Coverage is not the same as being wired
in.

**Religious upheaval.** Between 100 and 400 AD China saw the arrival of
Buddhism and Daoist theocratic rebellion (the Way of the Five Pecks of
Rice). Buddhist monasteries became dominant landholders, mill owners and
pawnshops. Religion is absent entirely.

*Project state:* absent, and layered at 8 in
`ENDOGENOUS_COSTS_AND_DOMAINS.md`. The monastery point is sharper than
"religion is missing": it names religious institutions as ECONOMIC actors -
landlords, millers and lenders - which is a thing the actor model could
represent without a theory of belief.

**Active diplomacy and military command.** The player cannot raise a private
militia, bribe an invading warlord, or influence a campaign. Military
defence is a passive stat roll.

*Project state:* `sim/world/military_logistics.py` derives what an army
physically consumes and how far it can march from a supply base, standalone.
It does not decide anything. Command, bribery and militia-raising are
agency, which is a different and later thing.

## 3. Over-simplifications

**Instantaneous hiring pools.** With cash and household capacity, `hire
artisan 25` recruits 25 master craftsmen in one year. Recruiting 25 master
metalworkers in antiquity meant agents across provinces and guild networks.

*Project state:* shares a root with `Complaints/34` (skilled hours cannot be
bought at all). The model has no notion of how scarce a given skill is in a
given place at a given time. Fixing either without that notion will produce
an arbitrary number.

**No epidemics or demographic pyramids.** No birth rates, no infant
mortality, no pandemics on the scale of the Antonine plague or the
3rd-century plagues in northern China.

*Project state:* `sim/world/demography.py` has three age cohorts, nutrition
driving mortality and fertility, and crude rates falling out rather than
being set. Not wired in; `docs/architecture/WIRING_MILESTONE_4.md` is the
plan. Note CLAUDE.md 3.2: the baseline must NOT reliably reproduce a dated
event like the Antonine plague - if it does, that is evidence of cheating.
Plagues should be draws, not appointments.

## 4. Where realism broke down

**Currency debasement.** 100-400 AD China saw severe monetary chaos - Dong
Zhuo melting imperial statues, the Three Kingdoms issuing debased coin. In
the game a cash coin's buying power is perfectly uniform across three
centuries.

*Project state:* nothing. Note that the price solver's numeraire is one hour
of unskilled labour, not a coin, so the machinery for "the coin moved and
the labour did not" is closer than it looks.

**The aggregate demand problem.** Who buys 1.2 million cash/year of
precision machine parts, high-voltage substations and lead-chamber sulfuric
acid in 4th-century agrarian China?

*THE STAKEHOLDER PUSHES BACK ON THIS ONE, and it is recorded as a
disagreement rather than a finding:* "if you have been making computers, you
are creating the demand by it existing." That is a real argument - an
industrial base is its own customer, and intermediate goods are bought by
the next process rather than by peasants.

*Project state, which bears on the disagreement:* there is no demand model
at all. That is the shared root of `Complaints/29` (joint production cannot
be priced from the cost side; the answer is in demand) and `Complaints/32`
(every price is currently pure labour content). Whichever way the argument
goes, the model cannot currently represent EITHER position, and the
reviewer's question and the stakeholder's rebuttal would both be answerable
once it can.

## 5. Where realism strained

**The physical weight of bronze coinage.** A treasury of 26.7 million cash
by 390 AD. Chinese `qian` were physical bronze coins on cords; 26.7 million
of them weigh roughly 80-100 tonnes, needing vaults and guards.

This is a good check precisely because it is arithmetic rather than
judgement, and the project already has the pieces: coin mass is physical,
`sim/world/transport.py` prices moving mass, and storage and guarding are
costs an actor should bear. A treasury that weighs nothing is a hardcoded
outcome in the sense of CLAUDE.md 3.1.

## 6. Where real life would make it impossible

**The tacit supply chain and the purity trap.** A semiconductor needs
germanium at one part per billion. In the 4th century there is no mass
spectrometer, no NMR, no gas chromatograph: a 5 ppm boron contaminant in
the quartz crucible kills the crystal and NOTHING TELLS YOU WHY.
Historically this took tens of thousands of interacting chemical and
instrument firms.

The sharp form of this is not "purity is hard", it is **you cannot measure
what you cannot measure**. A tech tree that lets you attempt a node you have
no instrument to diagnose should model the failure as uninformative - you
lose the batch and learn nothing - rather than as a cost. That is a
mechanism this project does not have and could.

**The societal and political immune response.** Han, Three Kingdoms, Jin and
Sixteen Kingdoms China was run by Confucian scholar-officials and
aristocratic military clans, where mechanical devices were dismissed as
`qiji yiqiao` - clever contrivances of no moral value. More lethally, a
private citizen with 26 million cash, municipal electrical grids, chemical
works and thousands of organised artisans would be branded a rebel or a
sorcerer. Cao Cao, Sima Yi or a Jin prince would have executed the founder,
confiscated the workshops into the state iron monopoly, and drafted the
machinists into building siege engines.

This is the same mechanism as item 2's state monopoly and is the most
consequential item in the review. The founder currently accumulates
unlimited wealth and industrial capacity with no political consequence. Per
CLAUDE.md 3.3 it must NOT become a scripted "the emperor seizes your
workshops at year N" event: it has to fall out of an actor with its own
interests noticing a rival concentration of power. That makes it a politics
and institutions problem, layered at 6, and it is the strongest argument yet
for why those layers matter to THIS scenario rather than being scenery.

---

## For whoever picks this up

Four of these have modules built and unwired (transport, deposits,
demography, military logistics), one is corroborated by this project's own
measurement (state monopolies, via mercury), one is an explicit stakeholder
disagreement to be settled by building the thing that could answer it
(aggregate demand), and two are new mechanisms nobody here had thought of:
uninformative failure when you have no instrument, and the physical mass of
money.

Do not treat this list as a work queue in order. The items are not
independent, and several would be answered at once by demand and by
institutions.
