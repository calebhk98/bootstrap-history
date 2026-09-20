# Module 10: Metallurgy, Fuel and Refractories

This module is the load-bearing wall of the guide. Nothing electrical,
nothing precision-mechanical happens until you can reliably hold a
temperature, hold a shape, and produce a predictable alloy.

## The single-page metallurgy dependency chain

1. `refractory_fireclay` first, always. Every furnace, crucible, retort and
   condenser below needs a lining that survives its own temperature.
2. `charcoal_industrial` in parallel with (1). Woodland management has a
   multi-year lead time; start it now, it is the long pole in the tent.
3. `coal_and_coke`, optional accelerant once you know where outcrop coal is.
4. `bellows_water_blown`, the single highest-leverage mechanical upgrade.
   Nothing past bloomery iron happens without sustained air beyond arm power.
5. `blast_furnace_cast_iron`, needs (1) lining, (2) fuel, (4) blast.
6. `finery_forge`, needs (5)'s pig iron as feedstock.
7. `cementation_steel`, needs (6)'s bars, (1)'s sealed chest, (2)'s charcoal.
8. `crucible_steel`, needs (7)'s blister steel, (1)'s best crucibles, and
   ideally `high_temp_furnace` (13) for reliable full melting.
9. `case_hardening` and `quench_temper` run in parallel with (6)-(8).
   Romans already do crude versions; you need steel with real carbon
   content from (7) to temper usefully.
10. `copper_refining` and `wire_drawing`: the drawplate must be made from
    hardened, tempered tool steel, so this needs (9). Otherwise independent
    of the iron chain.
11. `zinc_metal`, critical path for the whole future electrical tree. Needs
    (1), (2) and (4) only, not cast iron, so it runs in parallel with (5)-(9).
12. `lead_silver_cupellation`, `tin_bronze_solder`, `mercury`,
    `antimony_arsenic_bismuth`: a parallel "minor metals" track, mostly
    refinements of practice Romans already have. Start alongside (1).
13. `high_temp_furnace` (regenerative preheat, then oxy-hydrogen) is the
    long-run heat ceiling that makes (8) reliable and gates (14).
14. `alloy_steels_ferroalloys` is the terminal, decades-out entry. It needs
    the full iron/steel chain, (13), and in its hardest form genuinely
    needs electricity, which needs (11) and (10). The module closes its own
    loop: better metallurgy needs electricity, and electricity needs
    metallurgy.

---

### refractory_fireclay - Furnace lining and crucible clay (*argilla refractaria*)

**What it is / why you want it.** A clay body that does not soften, crack or
fuse to slag at working temperature. Every furnace, crucible and retort in
this guide fails if the container fails first.

**Why you would never guess this.** Not all clay is the same clay. Ordinary
potter's clay (high iron, high flux) slumps well below forge heat; a good
refractory clay is low in iron and alkalis. You cannot tell which by
looking, only by firing a test piece past your intended use temperature.

**Prerequisites.** None. This is your first task in Rome.

**Roman-available inputs.** Pale grey or white clay, low in visible iron
staining (avoid red/orange beds, that is iron and will slag). Grog: old
fired pottery or kiln waste, crushed to sand/gravel size.

**Procedure.** Collect several clay samples from different beds, wedge
free of air. Add crushed grog to a test batch, roughly 20-40% by volume, to
cut shrinkage and cracking (ESTIMATED, modern refractory practice). Fire
test pieces alongside your real furnace load, using furnace colour as your
only thermometer: faint red ~500-550 °C, dull red ~600-700 °C, cherry red
~700-800 °C, bright cherry ~800-900 °C, orange ~900-1000 °C, yellow
~1000-1150 °C, dazzling white above roughly 1300 °C. NOTE: this scale is
strongly affected by ambient light and every smith reads it 100 °C or more
differently in daylight than in a dark shop, so judge colour in consistent
dim light and calibrate your own eye against a known melting point (silver
962 °C, copper 1085 °C) before trusting it. An earlier draft of this module
gave a scale 100-200 °C higher than this one and disagreed with Module 30;
the audit in 99_AUDIT.md caught it and this is the corrected version. Pull test pieces at intervals: a
good refractory clay stays matte and rigid, a bad one goes glossy, sags, or
bloats.

**How you know it worked.** Fired piece rings when tapped, holds a sharp
edge, shows no glaze or sag at target temperature plus a margin.

**Failure modes.** Glassy sweating or slumping: too much iron/flux, discard
that bed. Cracking on first fire: too little grog or too fast a ramp.

**Cost & labour.** 2-4 personal days scouting and testing beds. Roughly
200-400 kg wet clay per labourer-day (ESTIMATED). No cash cost if self-dug.

**Danger.** Minimal; standard fire burns.

**Confidence: HIGH.** Textbook ceramics; nothing here needs materials
Romans lack.

---

### charcoal_industrial - Charcoal at scale (*carbo*)

**What it is / why you want it.** Charcoal is the fuel of every furnace
below: hotter, cleaner-burning than wood, and itself a reducing agent.
Scaling from hearth to ironworks means scaling from bundled wood to managed
woodland and standing kilns.

**Why you would never guess this.** The bottleneck on Roman-era iron output
is not ore or usually labour, it is charcoal, and charcoal supply is a
forestry-management problem with a decade-long feedback loop, not a
fuel-gathering task you solve this season.

**Prerequisites.** None to produce; `refractory_fireclay` for anything you
build to burn it in.

**Roman-available inputs.** Coppice-able hardwood: oak, beech, hazel,
chestnut, ash. Romans already coppice for fuel and poles; this formalises
the rotation and scales the kiln.

**Procedure.** Stack arm-thick billets in a dome around a central flue,
cover with turf and earth, leave vent holes. Light the centre and close
down air as the burn establishes so wood chars rather than burns; a large
clamp runs roughly 3-6 days (MEASURED, traditional practice, variable with
size and weather). Yield is roughly 20-25% charcoal by dry wood weight,
i.e. very roughly 4-5 tonnes wood per tonne charcoal (MEASURED, historical
range, quoted figures span about 15-30% depending on wood, moisture and
skill). Cool fully before opening; reignition on early opening is the main
cause of lost yield.

**How you know it worked.** Charcoal is black through, light, rings
slightly, shows wood grain in cross-section. Browned-not-charred wood or
ash-cored pieces mean under- or over-burning.

**Failure modes.** Too much air: burns to ash. Too wet a cover: incomplete,
smoky, low-heat char. Early reopening: reignites, batch lost.

**Cost & labour.** 2-4 people per clamp, several days per cycle. Oak/chestnut
coppice for charcoal cordwood runs a 15-25 year rotation (MEASURED,
historical European practice); hazel poles a shorter 7-9 years. Woodland
must be set aside and managed years before the iron it will fuel.

**Danger.** CO from smouldering clamps in enclosed spaces; burns; collapse.
Socially, visible large-scale cutting draws land-rights and flooding
complaints; site clamps on land you control.

**Confidence: HIGH** on method (continuous practice, antiquity to 20th
century); **MEDIUM** on exact yield figures, never measured numerically by
Romans.

---

### coal_and_coke - Sea-coal and coking (*carbo fossilis*)

**What it is / why you want it.** Mineral coal, and coal converted to coke
(volatiles and much sulfur driven off), are fuels that don't consume
woodland. Coke additionally has the mechanical strength to hold its shape
under a tall furnace's charge weight, which charcoal cannot past a certain
furnace height.

**Why you would never guess this.** It isn't obvious a fuel needs to be
strong. Charcoal is friable; stack enough charge on it and lower layers
crush to dust, choking airflow. Coke's fused, cellular structure survives
being crushed by tonnes of charge above it, which is exactly what lets
furnaces grow taller and hotter.

**Prerequisites.** None chemically; `refractory_fireclay` for the coking
structure.

**Roman-available inputs.** Coal outcrops in Roman Britain: archaeologically
attested (coal residues at forts on Hadrian's Wall, in the Weald, at Bath).
Solinus records a perpetual "black stone" fire at Aquae Sulis, generally
read as coal (attributed, unverified as to exact wording/date). Expect none
of this in Italy itself; it must ship from Britain.

**Procedure.** Break coal to fist-sized lumps, stack and cover exactly as
a charcoal clamp with draft holes. Burn down, restricting air, roughly 2-3
days (ESTIMATED, analogy to charcoal-clamp timing); tars, water and much
sulfur burn off as smoke. Cool and break open: coke is grey, hard, porous,
lighter than raw coal, burns nearly smokeless.

**How you know it worked.** Coke rings like stone, does not blacken your
hand the way coal does, burns with a clean blue-edged flame rather than
coal's smoky yellow one.

**Failure modes.** Undercoked coal keeps sulfur/tar and will "hot-short"
iron on direct contact. Overcoked (too much air): burns to ash.

**Cost & labour.** Delivered cost dominated by shipping, not extraction.
Coking loses roughly a quarter to a third of raw coal's mass (ESTIMATED,
basis: typical bituminous coal volatile content, ~25-35% by weight).

**Danger.** Coking gas is toxic and flammable, do not lean over vents.
Sulfurous smoke is caustic. Socially unremarkable in Britain.

**Confidence: MEDIUM.** Roman coal use in Britain is real (HIGH); coking it
for iron smelting is a post-Roman technique (17th-18th century England)
introduced here (MEDIUM).

---

### bellows_water_blown - Water-driven double bellows and the trompe

**What it is / why you want it.** Replacing arm-powered bellows with a
water-wheel mechanism delivering continuous, high-volume air for hours
without fatigue. The single highest-leverage mechanical change in this
module: it is what turns a bloomery into a blast furnace.

**Why you would never guess this.** It looks like a labour convenience; it
is actually a scale-and-temperature unlock, since a bloomery's ceiling is
set by how steadily a human can blow air. You do not need a true crank,
unavailable until roughly the 3rd century (Hierapolis sawmill). Use cams
(lifting tappets) on the wheel's axle instead, each lifting a lever that
raises a bellows board then drops it, the same principle already used in
Han-dynasty water-powered trip hammers.

**Prerequisites.** A working water wheel (earlier module); leather/wood
bellows construction (already Roman). For the trompe: lead pipe and a
several-metre fall of water.

**Roman-available inputs.** Oak/ash timber, tanned ox-hide, iron fittings,
a water wheel (Vitruvius, *De Architectura* X). Lead pipe (*fistula
plumbea*) for the trompe.

**Procedure, cam bellows.** Build two bellows with weighted top boards side
by side. Mount offset cams on the wheel axle so one delivers while the
other refills. Feed both into a common wind-chest with a one-way leather
flap valve, smoothing pulses into a near-continuous blast.

**Procedure, trompe (no moving parts).** Run a pipe from a header cistern
down several metres into a closed barrel, with a ring of small air-inlet
holes near the top of the pipe. Falling water entrains air down with it;
inside the barrel the air separates, collects under pressure, and is drawn
off to the furnace while water drains continuously from the bottom.

**How you know it worked.** Furnace roar becomes continuous, not pulsing;
glow at the tuyere stays steady for hours instead of surging and dying.

**Failure modes.** Cams timed wrong: both bellows rise together, blast
stops. Trompe holes too large: mostly spray, weak entrainment. Too little
fall height: not enough pressure to matter.

**Cost & labour.** Cam rig: ESTIMATED 15-30 artisan-days once the wheel
exists; trompe: ESTIMATED 5-10 artisan-days. A bloomery needs on the rough
order of a cubic metre or two of air per minute (ESTIMATED, rough
combustion stoichiometry); a blast furnace needs several times that,
sustained for hours, beyond any human crew in shifts. Tune by observation,
there is no flow instrument.

**Danger.** Crush/pinch injuries near moving machinery; pressurised trompe
barrels can blow a bung.

**Confidence: HIGH** on mechanism and cam (non-crank) feasibility
(Han-dynasty water bellows attested 31 AD, Hou Han Shu); **MEDIUM** on the
trompe this early, best attested in medieval Pyrenean forges, though the
physics needs nothing Rome lacks.

---

### blast_furnace_cast_iron - The tall shaft furnace and cast iron

**What it is / why you want it.** A furnace tall enough, blown hard and
continuously enough to fully melt iron, producing liquid cast iron you can
tap and cast, or convert downstream to wrought iron and steel. This is the
single biggest technology gap between Rome at 100 AD and China at the same
date: Chinese foundries cast iron from roughly the 5th century BC and had
water-powered blast bellows by 31 AD, while the West has no true blast
furnace until roughly the 12th-13th century AD, a gap of about a
millennium.

**Why you would never guess this.** A bloomery smith reasonably believes
iron does not melt in a forge, because in his furnace it never does; iron
melts at 1538 °C. Iron loaded with carbon melts far lower: cast iron near
4.3% carbon has a eutectic point around 1147 °C, achievable. Height plus
continuous blast raises peak tuyere-zone temperature and gives the charge
long contact time with a carbon-monoxide-rich atmosphere as it descends,
so it absorbs carbon and arrives already low-melting.

**Prerequisites.** `refractory_fireclay`, `charcoal_industrial` (or
`coal_and_coke`), `bellows_water_blown`; iron ore, limestone.

**Roman-available inputs.** Iron ore (haematite/limonite, e.g. Noricum,
Britain, Spain), limestone (already used in Roman mortar), charcoal or coke.

**Procedure.**
1. Build a fireclay-lined shaft roughly a person's height or taller,
   tapered, with a tuyere near the base fed by the water-blown bellows.
2. Charge from the top in alternating ore, fuel, crushed-limestone layers,
   tuned by trial (limestone combines with ore's silica gangue into a
   fluid slag; too little clogs the furnace, too much wastes fuel heat).
3. Blow continuously; the descending charge is preheated countercurrent by
   rising hot gas, which is why height matters. Near the tuyere, reduction
   produces metallic iron that keeps absorbing carbon and melts.
4. Molten iron and slag pool at the base, slag floating on top. Tap slag
   through a higher notch; tap iron through a lower hole plugged with a
   clay "bott," broken open with an iron bar. Iron runs into sand mould
   channels: a main "sow" channel with branching "pig" moulds.
5. Recharge from the top continuously, tap at intervals; unlike a bloomery
   this is a continuous, not batch, process.

**How you know it worked.** Tapped metal flows like thick porridge, not a
half-solid mass. Cooled pig iron is hard, brittle, breaks with a
crystalline grey or white fracture (grey iron shows graphite flakes) and
shatters rather than bends cold.

**Failure modes.** Weak blast or short furnace reverts to bloomery
behaviour. Too little limestone clogs the tuyere with thick slag
("hanging"). Sulfur-rich fuel (raw coal) makes iron "hot short."

**Cost & labour.** First build: ESTIMATED several weeks of mason/smith
labour. Running cost historically very roughly 4-8 tonnes charcoal per
tonne pig iron (MEASURED, broad pre-industrial range); your own furnace's
ratio stays unknown until weighed.

**Danger.** Molten metal/slag is lethal on contact; water meeting it
causes steam explosions, keep charge bone dry. Socially, an operation this
visible draws landowner and likely imperial attention.

**Confidence: HIGH** on the phase-diagram chemistry and Chinese dating;
**MEDIUM** on exact fuel-consumption ratios for a first Roman attempt.

---

### finery_forge - Converting pig iron to wrought iron (*fining*)

**What it is / why you want it.** Pig iron is brittle and cannot be forged.
The finery (and later the puddling furnace) burns most of the carbon back
out under a strong blast, giving malleable, weldable wrought iron or,
stopped earlier, steel.

**Why you would never guess this.** It looks backwards: you worked hard to
put carbon in so it would melt, now you burn most of it back out. The
payoff is that liquefying, tapping and casting at scale first is far more
productive than a bloomery big enough for the same tonnage directly.

**Prerequisites.** `blast_furnace_cast_iron` for feedstock;
`bellows_water_blown` for the blast.

**Roman-available inputs.** Pig iron, charcoal, an open hearth with a
tuyere.

**Procedure.**
1. Reheat pig iron in an open hearth with a strong blast onto the metal
   surface, not just the fuel bed. Blast oxygen burns out carbon and
   silicon into the slag/gas; melting point rises as carbon falls, and the
   metal stiffens from liquid to a pasty mass well before it is pure iron.
2. Gather the pasty mass into a ball ("loop") with tongs, working it under
   the blast until uniformly stiff.
3. Hammer hard and repeatedly to squeeze out slag and consolidate into a
   bar, the same consolidation skill already used on bloomery blooms.
4. Optionally reheat in a second, cleaner hearth (the chafery) purely for
   forging heat, without further refining.

**How you know it worked.** Watch sparks: high-carbon iron throws long
branching star-bursts; as carbon burns out, sparks shorten toward wrought
iron's sparse orange ones. A fully fined bar shows a fibrous, grey,
slag-streaked fracture, not pig iron's crystalline break, and welds to
itself under the hammer at bright yellow heat.

**Failure modes.** Stopped too early: still brittle, won't weld. Too few
reheats: cracks working cold. Uneven blast: "wormy" inconsistent bar.

**Cost & labour.** ESTIMATED 1-2 skilled artisan-days per finery cycle, plus
a further day of chafery/hammering per bar, scaling with charge size.

**Danger.** Standard burn/molten-metal hazards; open-hearth blast throws
sparks further than a closed furnace.

**Confidence: MEDIUM-HIGH.** Fining pig iron is well-documented
medieval/early-modern practice, introduced here as new to Rome since Rome
has no pig iron of its own to fine.

*Later upgrade: the puddling furnace.* Once coal and a reverberatory
furnace exist (`high_temp_furnace`), pig iron can be fined without fuel
touching the metal, since coal's sulfur would otherwise contaminate it.
Fuel burns in a separate firebox; flame reflects off a low brick roof onto
the iron, hand-stirred ("puddled") as it "comes to nature" (historically
Henry Cort, 1784). The step that eventually frees iron refining from
charcoal/woodland. Confidence: MEDIUM.

---

### cementation_steel - Blister steel

**What it is / why you want it.** Packing wrought-iron bars in charcoal
inside a sealed chest and holding heat for days lets carbon diffuse in from
the surface, converting iron to steel without melting anything.

**Why you would never guess this.** Solid iron absorbing carbon from solid
charcoal over days, well below melting point, with nothing visibly mixing,
is not intuitive. The only external sign is small surface blisters, from
gas evolving as carbon penetrates, hence the name.

**Prerequisites.** `finery_forge` for bar stock; `refractory_fireclay` for
the chest; `charcoal_industrial`.

**Roman-available inputs.** Wrought iron bars, crushed charcoal, a
clay-luted stone or fireclay chest.

**Procedure.**
1. Pack bars in alternating layers with crushed charcoal, no bar touching
   another, inside the chest. Seal the lid with clay lute to exclude air;
   air would let the charcoal just burn, and would scale the iron's
   surface instead of carburising it.
2. Hold at roughly 950-1100 °C (bright orange-red, colour scale as above)
   continuously for several days, historically around 6-9 days for
   full-depth bars (MEASURED, historical English practice, varies with bar
   thickness and target depth). Cool the sealed chest fully before opening.

**How you know it worked.** Break a sample: good bars show surface
blisters and a coarse, bright, crystalline fracture, not wrought iron's
dull fibrous one. Field test: quench a red-hot cut-off; if it now files
hard or resists a scratch, it has taken carbon, plain wrought iron will not
harden this way.

**Failure modes.** Air leak: surface scales instead of carburising, patchy
result. Too short a hold: only a thin case, soft core. Penetration is
roughly a tenth of a millimetre of case depth per hour at temperature
(ESTIMATED, modern carburising rate-of-thumb), why full-depth conversion
needs days.

**Cost & labour.** ESTIMATED 6-9 days continuous furnace tending per batch
(many bars per chest, so a batch cost not per-bar); heavy charcoal draw.

**Danger.** Standard burn/fume hazards, plus the difficulty of holding
temperature safely overnight across many days.

**Confidence: MEDIUM-HIGH.** Chemistry is textbook and crude case-
carburising was already known in antiquity; the bar-scale sealed-chest
process described here is a later (17th century onward) refinement
introduced early. Time/temperature figures: MEDIUM, drawn from later
sources, not Roman ones.

---

### crucible_steel - Melted, homogeneous steel (*Huntsman process*)

**What it is / why you want it.** Fully melting blister steel in a small
closed crucible, rather than only hammer-folding it, gives an even,
slag-free ingot. This is the gate on any edge or tool needing reliable
hardness across its whole cross-section: razors, precision cutters,
springs, gauges.

**Why you would never guess this.** Folded ("shear") blister steel looks
good enough; it is a real improvement over plain wrought iron. But folding
cannot fully homogenise carbon or remove every slag streak, and slag
inclusions are exactly what makes a fine edge tear instead of cut. Full
melting is the only fix, and steel's high melting point makes that a
serious furnace problem, not a recipe problem.

**Prerequisites.** `cementation_steel`; `refractory_fireclay` for crucibles
surviving full melt heat; ideally `high_temp_furnace`.

**Roman-available inputs.** Blister steel pieces; heavily grogged fireclay
crucibles (historical Huntsman crucibles were clay-graphite, but graphite
as a deliberately sourced material is not established as Roman-available,
so expect shorter crucible life); powdered glass as a protective flux.

**Procedure.**
1. Make small (few-kilogram), thick-walled, pre-fired, heavily grogged
   crucibles. Load broken blister steel with a pinch of powdered glass on
   top and lid loosely.
2. Set in the strongest-blast furnace available, aiming comfortably above
   steel's melting range (roughly 1370-1500 °C by carbon content;
   industrial practice wants nearer 1600 °C for pouring superheat), at or
   beyond plain water-blown charcoal heat's ceiling, so treat success as
   depending on `high_temp_furnace`. Hold until fully liquid (clear,
   mobile glass flux, no solid lumps when probed).
3. Lift with long tongs, pour fast into a preheated mould; a hand crucible
   cools quickly.

**How you know it worked.** Cooled ingot breaks with a fine, even, silvery
crystalline fracture, no layering or slag streaks, unlike folded steel's
visible lamination.

**Failure modes.** Furnace short of temperature: charge stays a sticky
solid and never truly pours. Crucible failure loses the melt, a real risk
given available materials; expect high early scrap rates.

**Cost & labour.** High: ESTIMATED several crucibles consumed per success
early on; skilled, small-batch, high-attrition.

**Danger.** Handling a molten crucible by hand tongs is a severe
burn/spill risk; a cracking crucible can spray molten steel.

**Confidence: MEDIUM.** Chemistry and payoff are textbook, the process
(Huntsman, 1740s) well documented; **LOW-MEDIUM** on whether graphite-free
crucibles survive repeated full steel melts, the entry's real open
question.

---

### case_hardening - Surface-hardening a finished tool (*ferrum indurare*)

**What it is / why you want it.** Carburising only a finished object's
outer skin gives a hard, wear-resistant surface over a tough core, ideal
for edges, gears, armour plates.

**Why you would never guess this.** Obvious once you want a hard edge and
tough back on one piece. Romans already pack finished tools in charcoal,
bone, horn or leather and reheat to harden the surface, real attested
practice. What they lack is any way to know how deep or uniform the
carbon has gone, so results vary tool to tool.

**Prerequisites.** `cementation_steel` (same chemistry, applied locally); a
finished wrought-iron blank.

**Roman-available inputs.** Charcoal, bone/horn scraps (a real added carbon
and nitrogen source), leather off-cuts, clay for luting a simple pack.

**Procedure.** Pack the working area in crushed charcoal (bone/horn mixed
in if available) inside a small clay-luted pot. Heat to the same
950-1100 °C range as cementation, but for minutes to a few hours rather
than days, since only a thin case is needed (ESTIMATED, same
tenth-millimetre-per-hour guide). Quench directly from the pack while hot
(see `quench_temper`).

**How you know it worked.** A file skates off the hardened surface but
still bites the unpacked tang. Grinding the edge throws fine, dense sparks
rather than wrought iron's sparse dull ones.

**Failure modes.** Case too thin: wears through fast. Uneven pack contact:
patchy hardness, cracking in spots. This unevenness, not the basic idea, is
what Roman practice already suffers from.

**Cost & labour.** ESTIMATED a few hours to a day per batch, far cheaper
than full bar cementation since only finished pieces are treated.

**Danger.** Standard forge burn hazards.

**Confidence: HIGH** that Romans already did some form of this; **MEDIUM**
on precise depth/time figures, never recorded by ancient smiths.

---

### quench_temper - Controlled hardening and tempering (*temperare*)

**What it is / why you want it.** Quenching hardens carbon steel;
tempering, a controlled reheat after, trades some hardness for toughness so
the piece doesn't shatter. Romans already quench and temper by feel; the
improvement is a repeatable visible reference for the tempering step.

**Why you would never guess this.** That quenching alone leaves steel
brittle is discoverable by trial and error, and Romans plainly knew it.
Not obvious without being told: a thin, transparent oxide film forms on
bright polished steel as it is gently reheated, and its colour is a
repeatable function of temperature, a thermometer made from the workpiece
itself.

**Prerequisites.** A steel object with real carbon content (from
`cementation_steel` or `case_hardening`), already quenched.

**Roman-available inputs.** Water or oil for quenching (both already used);
a file or stone to polish a small bright patch; a bed of embers for a
gentle, controlled reheat.

**Procedure.**
1. Heat the shaped piece uniformly to bright cherry-orange (~800-900 °C)
   and quench fully in water (fast, harsher, more crack risk on thin
   sections) or oil (slower, gentler).
2. File or grind a small patch bright, then reheat gently and evenly,
   watching it pass through a repeatable colour sequence: pale straw
   around 230 °C, brown around 255 °C, purple around 280 °C, blue around
   300 °C (standard textbook values; real steels vary roughly ±10-20 °C by
   alloy content, treat as reliable targets, not exact constants). Quench
   the instant the desired colour appears to lock in that temper.
3. Match colour to purpose by trial: pale straw for the hardest edges
   (razors, engraving tools, scrapers); brown for punches, chisels, axes;
   purple for screwdrivers and light springs; blue for swords and heavier
   springs needing more give (ESTIMATED, blacksmithing rule-of-thumb).

**How you know it worked.** A tempered edge holds up under normal use and
does not snap when moderately flexed, where a merely quenched edge chips
or shatters almost immediately.

**Failure modes.** Skipped tempering: shatters in use. Overshoot past blue
into grey: too soft, loses the hardness quenched in, exactly the
inconsistency Roman "by feel" tempering could not previously fix.

**Cost & labour.** Minutes per piece once the target colour is known;
negligible material cost.

**Danger.** Standard burn hazards; quenching produces steam and spatter,
keep your face clear.

**Confidence: HIGH** on the physics and on the colour values given
(consistent with standard published temper charts, minor source-to-source
variation of order 10-20 °C expected); **HIGH** that Romans already
quenched/tempered by feel inconsistently, a reasonable inference, not a
cited ancient description of the colour method itself.

---

### zinc_metal - Distilling metallic zinc (*per descensum*)

**What it is / why you want it.** Metallic zinc you can hold, not just zinc
fumed into copper to make brass. This is the single most important item in
this module: metallic zinc is the practical gate on the voltaic pile, and
the pile gates the entire electrical technology tree.

**Why you would never guess this.** This is the trap that kept the ancient
Mediterranean making brass for centuries without ever isolating zinc.
Carbothermic reduction of zinc oxide starts around 950-1000+ °C, but
metallic zinc boils at only 907 °C: reduction only gets going once zinc is
already past its own boiling point, so the instant it forms it is vapour,
not solid metal in your crucible. In an ordinary open or upward-venting
furnace, that vapour either alloys straight into copper right where it
forms (exactly how cementation brass-making works, copper is the trap) or,
uncaptured, drifts into the air and instantly reoxidises to white zinc
oxide fume, long recognised as "philosopher's wool" without anyone
connecting it to a metal. The fix is not a hotter fire but different
geometry: distil the vapour DOWNWARD into a cool, sealed collection point
instead of letting it rise. This "distillation per descensum" is the real
historical method, clearly attested at Zawar, Rajasthan.

**Prerequisites.** `refractory_fireclay`, `charcoal_industrial`,
`bellows_water_blown` (need to comfortably clear ~1000 °C and hold it for
the whole run).

**Roman-available inputs.** Calamine (smithsonite or hemimorphite,
recognised and used as *cadmia* for brass-making, e.g. Cyprus, Campania),
charcoal, a fireclay retort and separate condensing chamber, clay lute for
every joint.

**Procedure.** Roast/calcine the ore first to drive off carbonate/water
and concentrate the zinc content, then crush and mix with charcoal. Pack
into a sealed fireclay retort with a narrow spout leading DOWNWARD into a
separate, cooler collection vessel, the reverse of a normal upward still,
since zinc vapour is dense and falls back through a hot upward path and
reburns. Lute every joint airtight. Heat the charge comfortably above
1000 °C while keeping the downward chamber cooler than the vapour path (it
need not be cold, only cooler). Vapour travels down, sealed from air,
condensing to liquid (zinc melts at 419.5 °C) then solid as it cools. Cool
fully before breaking the seal.

**How you know it worked.** A bluish-white, moderately soft metal,
noticeably less dense than lead, unlike tin it does not "cry" (crackle)
when bent. Only white powder in the collection chamber means air reached
the vapour, that is oxide, not metal; redo the seal.

**Failure modes.** Air leak in the vapour path (most likely failure):
reoxidises to white powder in transit. Condensing chamber too hot: zinc
stays vapour and escapes. Furnace too cool: reduction barely proceeds.

**Cost & labour.** ESTIMATED several days per batch (roasting, packing, a
sustained above-1000 °C hold, full cooldown), high fuel use; expensive,
skilled, small-batch in early iterations.

**Danger.** Zinc oxide fume from a failed seal causes "metal fume fever,"
a real, usually self-limiting but unpleasant illness, still called "brass
founders' ague" in modern foundries. Ensure ventilation and do not breathe
over an opened retort.

**Forward note: germanium.** Zinc ores commonly carry trace germanium and
indium; in the later real zinc industry germanium is recovered from
smelter flue dust, not mined directly. Once zinc smelting runs at scale,
stockpile and label flue dust by ore source on the chance a batch is
germanium-rich. Long-range and speculative, unverifiable without assay.

**Why this gates the electrical age.** A voltaic pile needs two metals with
a large reactivity gap, joined by a brine/acid electrolyte, so one
reliably corrodes and drives current. Zinc-copper is the historical answer:
zinc sits well above copper (and iron) in reactivity, is cheap and
workable, and can be produced by a purely thermal process, unlike the truly
reactive alkali metals, which need electrolysis, itself needing
electricity first. Zinc is the one practical "first battery metal"
reachable without already having electricity.

**Confidence: HIGH** on the core chemistry (boiling point below reduction
temperature and the resulting reoxidation trap); **HIGH** that Romans made
brass without ever isolating zinc metal; **MEDIUM** on the per descensum
method's dating (best attested at Zawar, possibly centuries after 100 AD);
**LOW** on the germanium byproduct note, explicitly speculative.

---

### lead_silver_cupellation - Refining silver from lead ore (*cupellatio*)

**What it is / why you want it.** Most Roman silver comes mixed with lead
(argentiferous galena). Cupellation melts the lead under an air blast on a
porous hearth; the lead oxidises away as litharge, leaving pure silver.
Romans already do this at large scale.

**Why you would never guess this.** Obvious once you know silver and lead
co-occur; the clever part, already discovered in antiquity, is that air
blown across molten lead selectively oxidises the lead (silver is far less
reactive here), and the oxide is absorbed into the hearth or skims off,
leaving bright silver with a visible "flash" the instant the last lead
clears.

**Prerequisites.** Basic galena smelting to argentiferous lead (already
Roman practice).

**Roman-available inputs.** Galena (Rio Tinto, Cartagena, the Mendips,
Sardinia); bone ash or marl for the porous cupel hearth (archaeologically
attested at Roman mining sites).

**Procedure.** Smelt galena with charcoal to argentiferous lead (standard
practice), then melt it in a shallow bone-ash or marl-lined hearth. Blow
air steadily across the surface, not through it: lead oxidises to litharge
(PbO), absorbed by the hearth or skimmed, continuously exposing fresh lead.
Continue until the dull, scummy surface suddenly clears to a bright mirror
flash, silver, an attested Roman assay/refining endpoint.

**How you know it worked.** The flash itself is the test. The bead is soft,
bright white, takes almost no further scum once flashed.

**Failure modes.** Stopped too early: still lead-contaminated, dull.
Overblown past the flash: risk of mechanical silver loss in fume/spatter.

**Improvements worth making.** Continuous stronger air from
`bellows_water_blown`; collect and re-smelt litharge (PbO plus charcoal
back to lead) rather than discard it, closing the loop with chemistry
Romans already use elsewhere.

**Byproducts worth keeping.** Litharge (*spuma argenti*, Pliny NH XXXIII) as
a flux in glassmaking and glazes. Red lead (*minium*, classical sources
sometimes confuse this name with cinnabar/vermilion, be careful which is
meant) as further flux/pigment. White lead (*cerussa*), already made via
the Roman stack process (lead strips over vinegar fumes in dung heaps for
weeks, Pliny NH XXXIV, Vitruvius), a useful pigment.

**Cost & labour.** Already a mature industry; hours to a day per batch
depending on hearth size.

**Danger.** Severe: lead fume/dust are cumulative neurotoxins, already
endemic among Roman metalworkers ("saturnism"). Improve ventilation and
hygiene rather than simply scaling exposure.

**Confidence: HIGH.** Roman cupellation, the litharge/red-lead/white-lead
materials and Pliny's descriptions are all well attested; the flash
endpoint is standard, textbook chemistry.

---

### copper_refining - Fire-refining copper (*aes*)

**What it is / why you want it.** Smelted copper carries dissolved oxide
that makes it brittle. Fire-refining ("poling") removes it, giving tough,
drawable copper.

**Why you would never guess this.** Copper that looks solid and shiny can
still be full of dissolved oxide that only fails later under the hammer or
drawplate; you cannot see the problem, only feel it fail.

**Prerequisites.** Basic copper smelting from ore (already Roman practice,
e.g. Cyprus, Rio Tinto).

**Roman-available inputs.** Smelted copper, green (unseasoned) wood poles,
a shallow melting hearth.

**Procedure.** Melt copper under a light charcoal cover. Thrust a green
wood pole beneath the surface and churn; steam and volatiles from the wood
chemically reduce dissolved oxide back to metal. Dip and quickly cool a
small sample and break it: a properly refined ("tough pitch") sample shows
a smooth, dense fracture with no porosity, under-refined copper is rough or
"wormy." Repeat poling until samples consistently break clean.

**How you know it worked.** The sample-break test itself; this technique
is still referenced today as "tough pitch copper."

**Failure modes.** Under-poled: brittle, porous, cracks under hammer or
drawplate. Over-poled: can pick up gas and embrittle differently, treat the
sample-break test as your only real check either way.

**Cost & labour.** ESTIMATED a few hours per melt, several sample-breaks
per session, cheap in materials.

**Danger.** Green wood in a melt spits hot metal violently, stand back, use
a long pole.

**Confidence: MEDIUM.** Chemistry is textbook; poling as a named technique
is well documented later (medieval onward), Roman use specifically is not
confirmed, treated here as an introduced refinement.

---

### wire_drawing - The drawplate

**What it is / why you want it.** Pulling wire through progressively
smaller holes in a hardened plate, instead of cutting and hammering strip
round by hand, is far faster and gives uniform, longer wire. Copper wire is
a prerequisite for every electrical device this guide will ever describe.

**Why you would never guess this.** Romans make wire by cutting thin
strips from sheet and rolling or hammering them round, a slow, inconsistent
process giving short, uneven lengths. The drawplate, a small hardened plate
with graded round holes, is a cheap, disproportionate win: once you have
one good plate, wire-making becomes pulling, not shaping.

**Prerequisites.** `quench_temper` (and `cementation_steel`), the plate
itself must be hardened tool steel or it deforms within a few pulls.
`copper_refining` for feedstock.

**Roman-available inputs.** A small hardened steel plate, tallow or
beeswax as lubricant, refined copper rod, pliers/tongs, ideally a simple
draw-bench (fixed plate plus windlass or lever).

**Procedure.**
1. Cast or hammer copper into a rough rod, tapered at one end. Drill or
   punch a graded series of round holes in the hardened plate.
2. Coat the rod with tallow, feed the tip through the largest hole, grip
   and pull the full length through. Move to the next smaller hole, repeat.
3. Anneal (reheat, cool slowly) between passes, roughly every 20-30%
   diameter reduction (ESTIMATED, standard rule-of-thumb for ductile
   metals), since drawing work-hardens copper and it cracks if pulled too
   far unsoftened. Continue drawing and annealing to target diameter.

**How you know it worked.** Wire is uniform in diameter along its full
length and bends smoothly without kinking, unlike visibly uneven,
often-faceted hand-hammered strip.

**Failure modes.** Skipped anneals snap the wire mid-pull. Too big a jump
between holes causes necking, breakage, or an enlarged die hole. A soft
drawplate goes out of round within a few pulls.

**Cost & labour.** ESTIMATED a few days of skilled toolmaking for a good
graded plate, one-time cost; drawing itself is then fast, ESTIMATED metres
per hour versus a small fraction of that by hand.

**Danger.** A snapping wire under draw-bench tension can whip back, keep
clear of the line of pull.

**Confidence: HIGH.** The drawplate is a well-documented medieval European
innovation (roughly 13th-14th century, sometimes noted earlier in the
Islamic world); Roman wire cut/swaged from strip is attested from
surviving wirework. One of the best "cheap, obvious in hindsight" items in
this module.

---

### tin_bronze_solder - Solders and fluxes

**What it is / why you want it.** Joining metal without melting the whole
piece: soft solder (tin-lead) for lower-strength joins, hard
solder/brazing (copper-zinc or copper-silver filler) for stronger joints at
higher temperature. Flux keeps the joint clean so filler wets and bonds.

**Why you would never guess this.** The trap is flux sourcing. Borax, the
standard modern brazing flux, is NOT reliably available in 100 AD: it comes
from Tibetan/Central Asian deposits and only reaches the Mediterranean via
later trade (well documented from roughly the 8th century onward, common in
Europe by the 13th). The same caution applies to true ammonium chloride
("sal ammoniac"); Pliny does describe a salt from the region of the Ammon
oracle (NH XXXI), but whether it is chemically identical to true ammonium
chloride is disputed (attributed, unverified), so don't rely on it either.

**Prerequisites.** Tin (Cornwall) and lead for soft solder; copper and
brass or copper-silver for hard solder.

**Roman-available inputs.** Tin, lead (Pliny NH XXXIV names
*argentarium*, tin-lead solder used by silversmiths), pine/fir resin (mild
flux), natron (weaker but genuine flux/cleaning agent, Wadi Natrun, already
correctly identified elsewhere as sodium carbonate, not saltpetre).

**Procedure, soft solder.** Alloy roughly equal parts tin and lead
(ESTIMATED starting ratio, exact Roman proportions undocumented; more tin
lowers melting point, more lead is cheaper). Clean joint surfaces bright,
coat with resin flux. Heat the joint, not the solder directly, until it
melts solder on contact; feed it in to wick by capillary action and cool
undisturbed.

**Procedure, hard solder/brazing.** Use brass or copper-silver filler.
Clean surfaces and dust with natron flux (weaker than borax, clean more
thoroughly beforehand to compensate). Heat the joint to dull-bright red and
apply filler, which should flow into a clean, hot gap by capillary action.

**How you know it worked.** Filler wets thinly and evenly along the whole
seam, not beaded, and holds real load without separating.

**Failure modes.** Dirty surfaces or insufficient flux: beads up, weak
joint. Overheated: flux burns off before filler flows.

**Cost & labour.** Cheap and fast per joint, minutes; tin is the real
expense.

**Danger.** Same lead-exposure caution as `lead_silver_cupellation`.

**Confidence: HIGH** that Romans used tin-lead solder (Pliny explicit);
**HIGH** that borax/true ammonium chloride are unreliable in 100 AD
(well-documented trade timing); **MEDIUM** on resin/natron effectiveness
specifically, weaker and less consistent than borax.

---

### mercury - Retorting cinnabar (*hydrargyrum*)

**What it is / why you want it.** Metallic mercury, already a genuine
imperially-controlled Roman product. Future importance: vacuum technology
(pumps, barometers) and mirror-silvering, both far downstream, worth
securing supply chains for now.

**Why you would never guess this.** Obvious once you want it; unlike zinc,
mercury is comparatively easy, its boiling point (356.7 °C) is far below
the roasting temperature needed to break down cinnabar, so ordinary
condensation works fine. No boils-above-its-own-reduction-temperature trap.
This is exactly why mercury was isolated in antiquity while zinc was not.

**Prerequisites.** A retort and condenser; `refractory_fireclay` improves
durability.

**Roman-available inputs.** Cinnabar (mercury sulfide), mined at Sisapo
(near modern Almaden, Spain) under imperial monopoly, described at length
by Pliny (NH XXXIII), including the danger to workers and the use of
condemned/enslaved labour because of it.

**Procedure.**
1. Roast crushed cinnabar in a closed or near-closed retort: HgS plus
   oxygen yields mercury vapour and sulfur dioxide.
2. Lead vapour through a cooled pipe; mercury condenses readily past
   356.7 °C, collecting as liquid metal.
3. Store the collected liquid in sealed glass or ceramic vessels (already
   Roman-available glassware).

**How you know it worked.** Liquid, silvery, very dense, beads into round
droplets, stays liquid until roughly -39 °C.

**Failure modes.** Incomplete roasting: unreacted cinnabar left, still red,
easy to spot and re-roast. Leaky condenser: vapour escapes as fume, both
yield loss and serious inhalation hazard.

**Cost & labour.** Already a mature, state-controlled industry at Sisapo;
expect it to stay administratively restricted rather than freely scalable.

**Danger.** Severe and cumulative neurotoxin, already recognised by Romans
(Pliny). Never heat mercury or amalgams unventilated; never ingest.
Socially, this is an imperial monopoly resource, unauthorised operations
will draw serious attention.

**Later payoffs.** Vacuum pumps/barometers (mercury's density and low
vapour pressure make it the working fluid for early vacuum technology,
itself a prerequisite for vacuum tubes far downstream); mirror-silvering
(tin-foil-mercury amalgam on glass, far better than polished bronze/silver
*specula*, though the amalgam process is itself toxic).

**Confidence: HIGH.** Roman mercury mining at Sisapo, Pliny's account, and
the retort chemistry are all well attested and textbook respectively.

---

### antimony_arsenic_bismuth - Minor metals worth knowing about

**What it is / why you want it.** Three metals of very different near-term
usefulness, worth flagging together to know what's worth stockpiling now
versus what genuinely isn't available yet.

**Why you would never guess this.** Knowing which of these is worth any
effort now (none, urgently) versus which ore is worth quietly setting
aside for later.

**Prerequisites.** None; basic mining/roasting already Roman practice.

**Roman-available inputs.** Stibnite (antimony sulfide, cosmetic kohl,
Pliny NH XXXIII); orpiment and realgar (arsenic sulfides, pigments; Pliny
discusses auripigmentum and sandaraca in NH 33, and the painters' pigments
systematically in NH 35, so cite 33 and 35 rather than 33-34). Bismuth: no confirmed Roman-available source at all.

**Procedure.** Antimony: stibnite is reducible to metal by roasting and
carbon reduction, similar to lead, though Roman use stays at the
sulfide-cosmetic stage; metallic antimony is brittle and useless alone,
its value is later, hardening lead alloys (type-metal, bearing metal).
Arsenic: orpiment/realgar were anciently alloyed into copper in some
pre-tin-bronze traditions, not standard Roman practice by 100 AD; later
use (lead-alloy hardening, far downstream semiconductor doping) is only a
long-range flag. Bismuth: historically confused with lead, tin and
antimony until the 18th century (Geoffroy, 1753), with no good evidence of
Roman recognition; melts around 271 °C, useful only much later for
fusible alloys. For now, simply stockpile stibnite, orpiment and realgar
ore rather than discard tailings; nothing here needs smelting yet.

**How you know it worked.** Not applicable; no near-term smelting attempt
is recommended.

**Failure modes.** Not applicable at this tier.

**Cost & labour.** Negligible beyond ore already being mined for cosmetic
and pigment use.

**Danger.** All three toxic, arsenic and antimony especially; handle with
the same care already applied by Roman pigment/cosmetic workers.

**Confidence: HIGH** on Roman availability and use of stibnite, orpiment,
realgar (Pliny explicit); **LOW** on near-term value in smelting to metal
now; **LOW** on bismuth being recognised as distinct at all in 100 AD.

---

### high_temp_furnace - Pushing past 1500 °C

**What it is / why you want it.** A ladder of methods to reach higher
sustained temperature, each a ceiling on which of the above entries
(especially `crucible_steel` and `alloy_steels_ferroalloys`) actually work.

**Why you would never guess this.** "Build a bigger fire" stops working
past a point: plain charcoal with strong forced air tops out short of
cleanly melting steel, let alone platinum or reducing silica. Each further
rung is a different trick, not more fuel.

**Prerequisites.** `bellows_water_blown` for rung 2; `refractory_fireclay`
throughout; `zinc_metal` and `wire_drawing` for rung 5.

**Roman-available inputs.** Charcoal or coke; firebrick for rung 3;
pyrolusite (MnO2, Roman-available) as one oxygen source for rung 4.

**Procedure, rungs in order of difficulty and temperature.**
1. Hand bellows, charcoal: roughly 1150-1250 °C. Good for bronze, wrought
   iron, glass, and comfortably covers `cementation_steel`'s 950-1100 °C.
2. Water-blown bellows or trompe (`bellows_water_blown`): roughly
   1400-1500 °C. Enough for cast iron, marginal for `crucible_steel`'s
   ~1600 °C target.
3. Regenerative preheat (Siemens principle, circa 1856): waste exhaust
   passes through a firebrick checkerwork that absorbs its heat, then
   incoming air is drawn through that hot brick instead of entering cold, a
   twin chamber swapping roles every 20-30 minutes. Preheated air (up to
   roughly 1000 °C) raises achievable flame temperature substantially,
   historically enabling steelmaking around 1600-1700 °C (Siemens-Martin),
   needing only better brickwork, nothing chemically new.
4. Oxy-hydrogen blowpipe: pure hydrogen burned in pure oxygen, historically
   used from the early 19th century to melt platinum (1768 °C), practically
   reaching on the order of 2000 °C. Needs its own gas chains: hydrogen
   from acid plus metal, oxygen from strongly heated pyrolusite (MnO2,
   Roman-available) or red mercury oxide, plus safe storage and a burner
   that mixes without detonating. Distant and high-payoff, not near-term.
5. Electric arc (much later): effectively unlimited within your
   refractories' limits, gated on a reliable electrical supply, itself
   gated on `zinc_metal` and `wire_drawing`. Closes the loop: this furnace
   ladder eventually needs the electrical tree it makes possible.

**How you know it worked.** Use the colour scale from `refractory_fireclay`
as your gauge; cross-check against hard references, platinum visibly
melting confirms step 4, cast iron flowing freely confirms step 2.

**Failure modes.** Assuming a bigger fire alone clears step 3 or beyond;
each rung is a different mechanism.

**Cost & labour.** Step 3 is a masonry project comparable in scale to the
blast furnace itself. Step 4 needs an entirely separate gas-chemistry
supply chain before the furnace part is even relevant.

**Danger.** Step 4: hydrogen-oxygen mixtures are a severe detonation hazard
if premixed before ignition, treat gas handling here as seriously as
anything in this guide.

**Confidence: HIGH** on the colour scale and regenerative preheat (well
documented, Siemens process); **MEDIUM** on exact oxy-hydrogen flame
temperature (practical figures commonly cluster near 2000 °C, higher
theoretical values quoted depending on stoichiometry, treat 2000 °C as
conservative); **LOW** on near-term Roman buildability of step 4's full
chain.

---

### alloy_steels_ferroalloys - Ferromanganese, ferrosilicon, tungsten and chrome steels

**What it is / why you want it.** The terminal, most advanced entry: alloys
giving steel special properties far beyond plain carbon steel. Included so
you know what exists and what ore to stockpile, not as a near-term recipe.

**Why you would never guess this.** Some of these are gated on electricity,
not on ore availability; ore is arguably already sitting in Roman-worked
ground in several cases, the missing piece is furnace temperature.

**Prerequisites.** The full iron/steel chain, `high_temp_furnace`; the
hardest items additionally need a working electrical supply
(`zinc_metal`, `wire_drawing`, and further downstream technology).

**Roman-available inputs.** Pyrolusite (MnO2, already Roman-available, used
e.g. as a glass decolouriser) for ferromanganese; ordinary silica sand for
ferrosilicon, universally available. Tungsten (as wolframite, a waste
mineral in tin-mining gangue, e.g. Cornwall) and chromium (chromite,
possibly present in Anatolian ophiolite belts, unverified) are not
recognised or worked as distinct materials by Rome at all.

**Procedure.** Ferromanganese: smelt pyrolusite alongside iron ore under
strongly reducing, high-temperature conditions (the blast-furnace-and-
beyond end of the furnace ladder); manganese ties up sulfur as manganese
sulfide, far less damaging than iron sulfide, reducing hot-shortness and
improving hardenability; ore is not the constraint here, furnace control
is. Ferrosilicon: reducing silica with carbon needs real industrial
temperatures above roughly 2000 °C, historically requiring electric arc
furnaces (late 19th century), gated on `high_temp_furnace`'s hardest
rungs. Tungsten and chromium steels: tungsten was not isolated until 1783
(the Elhuyar brothers), chromium not until 1797 (Vauquelin); both metals
(tungsten melts at 3422 °C) genuinely require electric-arc-era technology
to work with at all, no charcoal-and-bellows or regenerative-furnace path
reaches tungsten's melting point. For now, simply set aside unusually
heavy, dark waste mineral from tin workings rather than discard it,
resource-banking for a far later tier.

**How you know it worked.** Not testable at this tier; there is no
near-term attempt to compare against. Revisit once `high_temp_furnace`
step 4 or 5 and a real electrical supply both exist.

**Failure modes.** Attempting ferrosilicon or tungsten/chromium alloying
without electric-arc-level heat simply fails to reduce the ore at all, no
partial result, the charge stays unreacted rock and metal.

**Cost & labour.** Not meaningfully estimable this far ahead; treat this
whole entry as a resource-and-priority note, not a costed recipe.

**Danger.** None beyond ordinary furnace/ore-handling hazards at this
stage, since no actual smelting attempt is recommended yet.

**Confidence: MEDIUM** on ferromanganese/ferrosilicon chemistry and gating
(textbook); **LOW** on tungsten/chromium ore availability or recognition in
the Roman world specifically, reasoned inference about mineral
associations, not a confirmed archaeological claim.

---

## Sources and confidence

**Textbook chemistry/physics (HIGH, era-independent):** blackbody glow
colour vs. temperature; the iron-carbon phase diagram (cast iron's ~1147 °C
eutectic vs. pure iron's 1538 °C melting point); carbon diffusion during
cementation; temper colours (230/255/280/300 °C, standard published
values, ±10-20 °C source variation); zinc's melting (419.5 °C) and boiling
(907 °C) points and the reduction-vs-boiling trap; mercury's boiling
(356.7 °C) point; the reactivity-series logic behind zinc-copper cells;
platinum (1768 °C) and tungsten (3422 °C) melting points; the Siemens
regenerative principle.

**Historically attested Roman practice (HIGH-MEDIUM, cited where
possible):** cupellation and its "brightening" endpoint, litharge/red
lead/white lead (Pliny NH XXXIII-XXXIV; Vitruvius); mercury mining and
retorting at Sisapo/Almaden (Pliny NH XXXIII); brass by cementation with
calamine; stibnite, orpiment, realgar as cosmetics/pigments (Pliny NH
XXXIII-XXXIV); tin-lead solder, *argentarium* (Pliny NH XXXIV); coal use
in Roman Britain (archaeologically attested; Solinus's Bath account is
attributed, unverified); water wheels (Vitruvius X); Roman wire
cut/swaged from strip, not drawn.

**Cross-civilisation comparisons (HIGH):** Chinese cast iron from roughly
the 5th century BC and water-powered blast bellows by 31 AD (Hou Han Shu,
biography of Du Shi); European blast furnaces not before roughly the
12th-13th century AD; Indian (Zawar) zinc distillation per descensum,
dating debated, generally well after 100 AD.

**Later historical processes introduced ahead of their real-world timeline
(MEDIUM on mechanism, NOT claimed as Roman practice):** bar-scale
cementation/blister steel (17th century onward); Huntsman crucible steel
(1740s); finery/chafery and puddling (Henry Cort, 1784); the drawplate
(medieval, roughly 13th-14th century); coking coal for iron (17th-18th
century England); copper poling; the trompe (early-modern Pyrenean
forges); Siemens regenerative furnace (1856); oxy-hydrogen blowpipe
(early 19th century).

**My own extrapolation, flagged ESTIMATED/DERIVED in place:** charcoal
yield and charcoal-to-iron ratios; coppicing rotation lengths;
bellows/furnace air-volume reasoning (order-of-magnitude only); wire
anneal frequency; temper-colour application assignments; that borax and
true ammonium chloride are unavailable in 100 AD; the wolframite-in-tin-ore
and Anatolian-chromite notes; the germanium-from-zinc-residue note, the
single most speculative claim here, flagged LOW throughout.

**Anachronism checks applied throughout:** no crank (bellows use cams,
consistent with the crank not appearing before the Hierapolis sawmill,
3rd century AD); no graphite crucibles (fireclay-and-grog only); no New
World or costly Far-Eastern-only materials (borax excluded); natron always
sodium carbonate, never saltpetre; cast iron, coke, the blast furnace,
crucible steel and free zinc metal are framed throughout as new
technology this module introduces, not pre-existing Roman capability.
