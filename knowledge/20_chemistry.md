# Module 20: Chemistry, Acids, Alkalis and Energetics

> **STOP AND READ THIS FIRST.** Roman *nitrum* (Greek *nitron*), the stuff
> Egyptian embalmers pack into bodies, glassmakers melt into batches, and
> fullers scour wool with, is **sodium carbonate/bicarbonate (natron)**,
> scraped from dry lake beds, chiefly the Wadi Natrun in Egypt. It has no
> nitrogen chemistry and will never become potassium nitrate no matter how
> you heat, grind, or purify it. If your gunpowder or nitric acid plan
> starts with "buy nitrum from an Alexandrian merchant," the plan is dead.
> Potassium nitrate does not exist as a mined or traded good anywhere in the
> Roman world in 100 AD. You must grow it biologically in a nitre bed over
> one to two years, starting on day one. This confusion is the single most
> common failure mode in any "bootstrap Rome" plan. See `saltpetre_nitre_beds`.

This module covers apparatus, alkalis, mineral acids, the fuels and
solvents that come from destructive distillation, and the analytical
discipline that makes any of it reproducible. Only `electrolysis_chemistry`
needs electricity (Module 50); everything else runs on fire, ceramics,
glass, lead, and patience, using materials the Empire already has.

---

### lab_apparatus - Laboratory apparatus (*vasa chymica*)

**What it is / why you want it.** The kit that turns "boiling things in a
pot" into repeatable chemistry: retort, alembic head, receiver, sand bath,
water bath, luting compound, crucible tongs.

**Why you would never guess this.** The seals matter more than the
vessels. A hairline gap in a joint that looks solid cold can open the
moment it is heated, and it releases whatever corrosive or toxic vapour
you are making straight into the room. Getting the lute right is as
important as getting the vessel shape right.

**Prerequisites.** A kiln reaching stoneware heat (roughly 1000-1100 C,
orange on the canonical colour scale in 10_metallurgy.md, so roughly 900-1000 C, bellows-fed), glassblowing, a coppersmith, charcoal supply.
Cross-reference the pottery/kiln and glass modules for exact TECH_IDs.

**Roman-available inputs.** Fine potter's clay for retorts and crucibles;
blown glass, including Alexandria's near-colourless ware, for heads and
receivers; sheet copper, bronze, and lead worked by *aerarii* and
*plumbarii*; river sand for the sand bath; water for the *balneum Mariae*
(water bath), named for the Alexandrian writer Maria the Jewess, whose
dates are disputed (attributed, unverified) but whose tradition, per
Zosimos of Panopolis writing around 300 AD, already included a proto-
still, the *tribikos*: distillation apparatus is culturally normal in the
Greek East, not alien to this world. Luting clay: potter's clay with
chopped straw or hair, a little dung for fine texture, salt or egg white
as binder.

**Procedure.** Throw and fire a cucurbit and fitted alembic head
separately in stoneware, or blow both in glass to watch a reaction. Build
a sand bath (dry sand over charcoal, vessel nested in it) for slow even
heat, and a water bath capped at 100 C for anything that must not exceed
boiling. Pack lute thickly around every joint, air-dry a full day before
firing gently, then work up to full heat on a second session; never lute
and hard-fire the same day. Fit wrought-iron crucible tongs sized to your
standard crucible.

**How you know it worked.** No hissing or seepage at a hot, pressurised
joint. Distillate drips cleanly from the spout rather than running down
the outside. A day-old lute joint rings dull, not hollow, when tapped.

**Failure modes.** Fast heating cracks lute at the joint you most need
sealed. Too-sandy clay crumbles; too little sand and it shrinks and
splits. Glass shatters moved cold into a hot bath. Under-fired ceramic
weeps vapour through the wall itself, not just joints.

**Cost & labour.** ESTIMATED (basis: comparable to fine tableware plus a
glassblowing commission). A basic set: 3-5 potter-days, 1-2 glassblower-
days, 1 smith-day, plus your own supervision. Modest capital, a week to
ten days including drying and test-firing.

**Danger.** Burns from hot ceramic and glass. No social danger yet;
distillation reads as perfumery or medicine to a Roman observer.

**Confidence: HIGH** on ceramics, glass, and metalworking feasibility.
**MEDIUM** on the Maria the Jewess dating, which is traditional but
disputed.

---

### saltpetre_nitre_beds - Saltpetre nitre beds (no Roman name; this
material is not part of the Roman world in 100 AD)

**What it is / why you want it.** Potassium nitrate (KNO3): the oxidiser
in gunpowder, the raw material for nitric acid, and a reagent you need
repeatedly downstream. No accessible mineral deposit exists; you farm it.

**Why you would never guess this.** Beyond the nitrum confusion at the top
of this module: a mature bed gives you mostly **calcium nitrate**, not
potassium nitrate, because the bed is built on calcareous material for
bacterial reasons. Calcium nitrate is deliquescent and will not crystallise
cleanly. You must convert it with potash. Skipping that conversion is the
second most common way to "successfully" run a bed and still get nothing
usable.

**Prerequisites.** Manure, straw, urine, wood ash, old lime mortar or
chalky earth. A roofed, ventilated shed. `potash_and_soda` for conversion.

**Roman-available inputs.** Stable and barnyard manure; straw; old mortar
rubble or chalky earth for calcium (demolition sites are a free source);
urine, already commercially collected for fulling; wood ash, both mixed in
and separately leached to potash.

**Procedure.** Build a waist-high bed of alternating thin layers of
manure, straw, and calcareous rubble, porous throughout. Water with urine
periodically rather than plain water. Turn the whole bed with a fork
every four to six weeks; this is the single most important step, since
the nitrifying organisms (unknown to a Roman but the process you know as
ammonia to nitrite to nitrate) need oxygen and an unturned pile stalls.
Keep covered from rain, open to air. Mature 12-24 months; this is a
biological minimum, not forceable by more urine or heat, exactly why you
start this in year one for a year-three payoff. Leach the mature earth
through a straw-bottomed barrel with repeated water washes, collecting a
calcium-nitrate-rich liquor. Boil this liquor with a strong wood-ash
potash solution: `Ca(NO3)2 + K2CO3 -> CaCO3 (precipitates) + 2 KNO3
(stays dissolved)`. Filter hot, boil the filtrate near saturation, and
cool slowly; KNO3 crystallises as needles since its solubility drops
sharply with cooling, unlike common salt. Redissolve and recrystallise at
least once more for working purity.

**How you know it worked.** White to grey needle crystals, sharp cooling
taste (small controlled test only), and a pinch on a hot coal fizzes and
sparks distinctly, unlike plain salt's simple pop. Confirm with the flame
test in `analytical_chemistry` (faint lilac through blue glass).

**Failure modes.** Skipping conversion leaves hygroscopic calcium nitrate
that will not hold a charge. An unturned, anaerobic bed stalls and smells
of rot. Rain-soaked beds lose nitrate to runoff. Unrecrystallised product
burns unevenly.

**Cost & labour.** ESTIMATED throughout; confirm with a small test bed
before committing labour at scale. As an order-of-magnitude planning
figure only: comparable early modern nitre works, on beds of a few cubic
metres, are described as yielding on the order of a few hundred grams to
a few kilograms of purified saltpetre per cubic metre of mature earth per
leaching cycle (ESTIMATED, basis: general early modern nitre-works
accounts). Labour is light per visit but stretched over 12-24 months
before leaching, then a few skilled days per batch for boiling and
crystallising.

**Danger.** Low physical risk while growing. The boiling step involves hot
alkaline liquor, splash and fume hazard. The larger danger is social: see
`gunpowder`'s strategic analysis.

**Confidence: HIGH** on the biology and conversion chemistry, both
well-documented pre-industrial practice. **LOW** on any specific yield
figure, explicitly flagged ESTIMATED.

---

### potash_and_soda - Potash and soda ash (soda overlaps with Roman
*nitrum*/natron; potash has no Roman equivalent)

**What it is / why you want it.** Potash (potassium carbonate, from wood
ash) for the saltpetre conversion, soap, and later caustic potash; soda
(sodium carbonate, natron or plant ash) for glass and soap, and later
caustic soda.

**Why you would never guess this.** Obvious once you want it. The sharp
edge: Romans already have soda as natron but possess no refined potash
industry, even though the two alkalis look and behave almost identically.

**Prerequisites.** Hardwood ash, quicklime (already a mature Roman
industry via concrete and mortar).

**Roman-available inputs.** Hardwood ash from any fire; natron from Egypt;
ash of salt-marsh halophyte plants as a second soda source (Pliny
references plants burned for salt-adjacent substances, attributed,
unverified; the underlying ash-burning technique is ancient even though
the later Spanish "barilla" trade name is medieval); quicklime.

**Procedure.** Leach wood ash repeatedly through a straw-bottomed barrel,
boil the lye down to crude potash. Use natron directly, or burn and leach
salt-marsh plants for soda. To causticise either: dissolve in water, add
slaked lime in slight excess, boil: `K2CO3 + Ca(OH)2 -> 2 KOH + CaCO3` (or
the sodium equivalent). Filter off the chalky precipitate hot; boil the
filtrate down for caustic potash or caustic soda.

**How you know it worked.** Crude alkali fizzes with a drop of acid
(carbonate releasing CO2). Causticised alkali no longer fizzes and feels
markedly more slippery and corrosive.

**Failure modes.** Incomplete leaching wastes alkali in spent ash.
Under-boiled causticising leaves carbonate mixed in, weakening downstream
soap-making.

**Later industrial routes, for reference.** Leblanc (needs sulfuric acid
and coal): salt plus sulfuric acid gives salt-cake and HCl gas (see
`hydrochloric_acid`); salt-cake roasted with limestone and coal gives
soda ash, with foul calcium sulfide waste. Solvay (needs ammonia, brine,
limestone): ammonia from coal-gas liquor (see `destructive_distillation`)
reacted with brine and CO2 precipitates sodium bicarbonate directly,
ammonia recycled. Both are later upgrades, not starting requirements.

**Cost & labour.** ESTIMATED (basis: existing Roman ash-leaching and
lime-burning trades). Low capital, modest labour, limited mainly by ash
volume.

**Danger.** Caustic alkalis burn skin and eyes, more insidiously than
acids since pain is delayed while tissue fat saponifies; wash immediately
and copiously. No social danger.

**Confidence: HIGH.** Well-attested pre-modern chemistry, no anachronism
risk.

---

### sulfuric_acid_retort - Oil of vitriol by dry distillation
(*oleum vitrioli*)

**What it is / why you want it.** Sulfuric acid made by dry-distilling
green vitriol (ferrous sulfate), the Nordhausen-type route: low volume but
very high, even fuming, concentration, your first strong acid before the
higher-volume lead chamber comes online.

**Why you would never guess this.** You roast a mild crystalline salt
until it violently decomposes into acidic gases that recondense stronger
than anything you started with. Nothing about green vitriol looks like it
should yield concentrated acid.

**Prerequisites.** `lab_apparatus` with a stoneware retort surviving
several hundred degrees C and corrosive sulfur oxide vapour.

**Roman-available inputs.** Green vitriol (ferrous sulfate, forms where
pyrite weathers in damp air, common around mine waste); blue vitriol
(copper sulfate, from Cyprus mine drainage); both also concentrated from
naturally acidic mine waters, notably the Rio Tinto district of Hispania.
Dioscorides and Pliny both discuss vitriolic minerals (attributed,
unverified for exact chapter).

**Procedure.** Dry the crystals in open air. Pack into a stoneware retort
with a downward-sloping neck feeding a cooled, sealed receiver. Heat
strongly, past red heat, toward the hottest a bellows-fed fire sustains
(roughly 1000-1200 C hand-blown, more water-blown). The vitriol decomposes
approximately as `2 FeSO4 -> Fe2O3 + SO2 + SO3` (illustrative, not exact;
real decomposition is stepwise and mixed). The released gases condense in
the receiver, SO3 reacting avidly with any moisture present to give
concentrated, even fuming, acid. Store in glass or lead only.

**How you know it worked.** Dense, oily, colourless to straw liquid,
distinctly heavier than water, fumes visibly in humid air, chars a wood
splinter or cloth scrap black on contact.

**Failure modes.** Under-heating gives poor decomposition and low yield.
The retort is slowly consumed by any acid pooling inside while hot.
Cracking under thermal stress releases toxic SO2/SO3 into the room; run
outdoors or with heavy ventilation.

**Cost & labour.** ESTIMATED (basis: comparable to a metalworking smelt
of similar fuel intensity). Slow vitriol collection, a full attentive day
of high heat per batch, low yield per batch relative to labour; a
precious-reagent method, not bulk supply.

**Danger.** Severe respiratory irritation from SO2/SO3 fumes, worse if a
vessel cracks. The finished acid burns skin, eyes, cloth, and most metals
on contact. No particular social danger.

**Confidence: HIGH** on the chemistry, the real historical route to
sulfuric acid before lead chambers. **MEDIUM** on ancient source citations,
attributed but not chapter-verified.

---

### sulfuric_acid_bell - Oil of vitriol by the bell method

**What it is / why you want it.** Bench-scale predecessor to the lead
chamber: burn sulfur with a little saltpetre under a sealed bell over
water, and dilute sulfuric acid condenses. Your proof-of-concept before
building a full chamber.

**Why you would never guess this.** Burning sulfur alone gives only weak,
unstable sulfurous acid. The saltpetre's decomposition products catalyse
full oxidation to sulfur trioxide, the actual precursor of true sulfuric
acid, and without it no amount of burning sulfur gets you there.

**Prerequisites.** `saltpetre_nitre_beds` (a small amount), sulfur, a
glass bell jar or lead dome.

**Roman-available inputs.** Sulfur, native and volcanic, well attested
(Sicily and other volcanic regions), already used for fumigation and
medicine; purified saltpetre; a blown glass bell or beaten lead dome.

**Procedure.** Set a shallow dish of water under the bell's footprint. Mix
a small quantity of saltpetre with a larger quantity of sulfur (starting
ratio to refine by experiment; no verified period figure survives to cite
here). Ignite on a small suspended dish just above the water, lower the
bell, and seal its rim in a water trough. Let it burn out fully sealed.
The saltpetre's nitrogen oxides cycle repeatedly: NO2 oxidises SO2 to SO3
while reducing to NO, and NO is reoxidised by remaining oxygen back to
NO2, a real catalytic cycle that processes far more sulfur than the
saltpetre's own mass suggests. The SO3 dissolves into the water as dilute
sulfuric acid; repeat burns over the same water to concentrate further.

**How you know it worked.** The water turns sour and heavier, chars a
splinter faintly after many repeated burns, and loses the sharp sulfurous
smell of a simple SO2 solution.

**Failure modes.** Too little saltpetre gives mostly weak sulfurous acid.
A poorly sealed bell lets reactive gases escape into the room, a real
inhalation hazard.

**Cost & labour.** ESTIMATED (basis: minor bench materials). Cheap in
apparatus, expensive in the saltpetre it consumes; best used for
demonstration and small batches until `lead_chamber` is running.

**Danger.** Nitrogen oxide gases are a serious, delayed respiratory
hazard (see the kill-list below); sulfur dioxide is a strong immediate
irritant. Run outdoors or with excellent ventilation, never enclosed.

**Confidence: MEDIUM.** The nitrogen-oxide mechanism is textbook (HIGH).
The bench-scale ratios and handling are ESTIMATED/attributed from general
pre-industrial descriptions, not a verified period recipe.

---

### lead_chamber - The lead chamber process

**What it is / why you want it.** Industrial-scale version of the bell
method: burn sulfur and a little saltpetre continuously inside a
lead-lined chamber with a water mist inside, and collect dilute sulfuric
acid in bulk, feeding soap, textile, metal, and every acid entry below.

**Why you would never guess this.** Lead specifically, because sulfuric
acid forms a protective, insoluble lead sulfate skin that shields it from
further attack, while iron, bronze, and copper corrode progressively and
ceramic cannot be built airtight at this scale. And the chamber needs a
controlled air feed, not a sealed one, since the nitrogen-oxide cycle
needs fresh oxygen to keep recycling.

**Prerequisites.** `saltpetre_nitre_beds`, sulfur, substantial lead sheet
and *plumbarii* skill (already mature via Roman pipe-making), a large
enclosed structure.

**Roman-available inputs.** Sulfur and saltpetre as above; lead, abundant
from Britain and Hispania.

**Procedure.** Line a room-sized chamber entirely in lead, seams folded
and cold-worked. Fit a water trough or mist arrangement, a controlled air
inlet, and a flue. Burn sulfur with a small proportion of saltpetre
continuously (exact firing arrangement to refine by trial; no verified
period figure survives to cite). SO2, oxidised via the nitrogen-oxide
cycle described above, converts progressively to SO3, which combines with
chamber water vapour into an acid mist that settles into the trough. Run
continuously, restocking sulfur and a trickle of fresh saltpetre, since
nitrogen escapes with the exhaust and must be topped up.

**How you know it worked.** Collected liquid is sour, heavier than water,
chars paper faintly, but noticeably weaker than the retort-distilled
product: this is bulk-grade acid by design.

**Failure modes.** Insufficient air stalls the cycle, giving weak
sulfurous acid. Excess saltpetre wastes hard-won nitrate. A lead seam
failure leaks corrosive mist. Lead exposed to acid too long eventually
corrodes past its sulfate skin, especially at seams, so the chamber has a
finite life and needs inspection.

**Later refinements: Gay-Lussac and Glover towers.** A Gay-Lussac tower
absorbs the nitrogen oxides that would otherwise escape up the flue into a
stream of concentrated sulfuric acid, forming "nitrous vitriol" pumped
back into the chamber to release its nitrogen again, sharply cutting
saltpetre use per unit of acid. A Glover tower, before the chamber, uses
the hot sulfur-burning gas to help denitrate the returning nitrous vitriol
and pre-concentrate the finished acid. Both need acid-resistant ceramic or
lead packing and are worth attempting only once the basic chamber runs
reliably.

**Cost & labour.** ESTIMATED (basis: a substantial lead-plumbing
commission plus ongoing fuel and reagent use). Significant upfront capital
in lead and skilled labour; modest ongoing tending; sulfur is cheap,
saltpetre is the real long-run cost given its year-plus maturation time.

**Danger.** The same nitrogen-oxide and SO2 inhalation hazards as the bell
method, at larger sustained scale; never enter the chamber while firing.
Socially, a large acid-producing lead structure draws questions from
neighbours and authority; a plausible cover story (dyeing, metal refining,
tanning) is worth arranging in advance.

**Confidence: MEDIUM.** The chemistry (nitrogen-oxide catalysis, lead's
self-passivation) is HIGH and matches the real historical process closely.
Roman-era construction specifics and achievable scale are ESTIMATED, a
starting point to refine, not a verified recipe.

---

### nitric_acid - Nitric acid, *aqua fortis*

**What it is / why you want it.** Made from saltpetre and oil of vitriol;
dissolves most metals, makes other nitrates, etches metal now, and much
later feeds explosives and semiconductor etching (Module 50+).

**Why you would never guess this.** Obvious once you have both reagents;
this is a direct displacement, not a hidden trick. The one catch: the
product must be distilled off as vapour and recondensed, since a simple
mix mostly gives a solid double-salt, not free acid.

**Prerequisites.** `saltpetre_nitre_beds`, `sulfuric_acid_retort` or
`lead_chamber` acid, `lab_apparatus` with a glass or stoneware retort
(glass resists nitric acid vapour well, unlike hydrofluoric).

**Roman-available inputs.** Purified saltpetre; oil of vitriol, the
retort-distilled version preferred here for a cleaner reaction.

**Procedure.** Mix dry saltpetre with concentrated sulfuric acid in a
retort. At moderate heat with roughly equal proportions: `KNO3 + H2SO4 ->
KHSO4 + HNO3`; with excess acid and stronger heat, `2 KNO3 + H2SO4 ->
K2SO4 + 2 HNO3`. Heat gently in the sand bath, well below a full boil,
since the vapour comes off early. Distil into a cooled glass receiver;
the product often comes over pale yellow to reddish brown from dissolved
nitrogen dioxide, normal, and what fuming nitric acid looks like.
Continue until the retort residue thickens and stops giving vapour,
leaving a useful potassium sulfate/bisulfate residue.

**How you know it worked.** Clear to yellow-tinged liquid, denser than
water, stains skin yellow (the xanthoproteic reaction, distinctive to
nitric acid), dissolves copper with brown fumes and a blue-green solution,
chars organic matter.

**Failure modes.** Too little acid or too low heat leaves nitrate locked
in the solid double-salt. Overheating decomposes product into escaping
brown NO2 gas, lowering yield and creating a real inhalation hazard.

**Cost & labour.** ESTIMATED (basis: comparable retort-distillation
labour to the sulfuric acid retort). A day of watched distillation per
batch; the real cost driver is the saltpetre consumed.

**Danger.** Severe skin and eye burns; brown distillation fumes are toxic
nitrogen oxides needing the same ventilation discipline as the lead
chamber. Dissolves most metals; store only in glass or acid-resistant
stoneware.

**Confidence: HIGH.** Standard acid-base displacement, no anachronism
risk once saltpetre and sulfuric acid exist.

---

### hydrochloric_acid - Spirit of salt, muriatic acid

**What it is / why you want it.** Made from common salt and oil of
vitriol; useful for metal cleaning and dye mordanting on its own, and
essential toward aqua regia and the Leblanc salt-cake byproduct.

**Why you would never guess this.** Obvious once you want it. The useful
catch: the reaction runs in two stages at two different temperatures, and
only the hotter second stage gives the valuable salt-cake byproduct rather
than a half-reacted mush.

**Prerequisites.** `sulfuric_acid_retort` or `lead_chamber` acid, common
salt, `lab_apparatus`.

**Roman-available inputs.** Sea or rock salt, already produced at
industrial scale (Ostia and elsewhere); sulfuric acid from either route
above.

**Procedure.** Mix salt with concentrated sulfuric acid in a retort. At
moderate heat, the first stage: `NaCl + H2SO4 -> NaHSO4 + HCl` (gas). For
a more complete reaction and the salt-cake byproduct, heat further, near
red heat: `NaHSO4 + NaCl -> Na2SO4 (salt-cake) + HCl`, which needs
noticeably more heat than the first stage and is where most attempts stop
short. Pass the escaping gas into a receiver of cold water, where it
dissolves readily.

**How you know it worked.** The gas is sharp, choking, fumes visibly in
humid air even before touching water. The acid is clear, fumes gently when
opened, fizzes vigorously with a pinch of chalk or lime.

**Failure modes.** Stopping heat early leaves only the first stage,
lower yield, no usable salt-cake. Escaped gas is lost product and an
immediate respiratory irritant.

**By-products and downstream use.** The salt-cake left in the retort
feeds the Leblanc soda process in `potash_and_soda`. Three parts of this
acid mixed fresh with one part nitric acid gives aqua regia, dissolving
gold and platinum via free chlorine and nitrosyl chloride generated in
situ, metals neither acid touches alone. This matters for gold refining
now and for ultra-clean glassware washing in later fine chemical and
semiconductor work.

**Cost & labour.** ESTIMATED (basis: comparable to the nitric acid entry
but cheaper, since salt is far less precious than saltpetre).

**Danger.** Gas and mist severely irritate lungs, eyes, and skin; the
acid burns, generally less catastrophically than sulfuric or hydrofluoric.
Aqua regia must be mixed immediately before use, never stored, since it
decomposes and builds dangerous pressure sealed.

**Confidence: HIGH.** Standard chemistry, clear period-feasible inputs.

---

### hydrofluoric_acid - Hydrofluoric acid (no established Roman name;
fluorspar is not identified as a distinct mineral by Roman mineralogists)

**What it is / why you want it.** Dissolves glass; used for etching now
and, far downstream, unavoidable for purifying silicon and germanium
(Module 50+). Made from fluorspar (calcium fluoride) and sulfuric acid.

**Why you would never guess this.** Fluorspar has no Roman economic
identity; it occurs naturally across Gaul, Germany, and Britain as an
attractive, colourful, cubic-crystal, soft mineral, and a modern eye that
knows cubic cleavage and knife-scratchable softness is your only
realistic way to find it. (Some historians debate whether Pliny's prized
imported "murrhine ware" might be worked fluorspar; genuinely disputed,
LOW confidence, not a sourcing plan.) Prospect and identify your own
deposit.

**Prerequisites.** `sulfuric_acid_retort` (wants strong acid); identified
fluorspar; a lead or wax-lined vessel, since this acid actively destroys
glass and ceramic linings.

**Roman-available inputs.** Fluorspar, located by physical properties
(cubic habit, softer than quartz, purple/green/yellow banding);
concentrated sulfuric acid.

**Procedure.** Crush fluorspar coarsely. Mix with concentrated sulfuric
acid in a lead retort, never glass or stoneware, or a beeswax-lined vessel
for small work. Heat gently: `CaF2 + H2SO4 -> CaSO4 + 2 HF`. Condense the
gas in a cooled lead or wax-lined receiver with a little water. Note that
anhydrous liquid HF boils at about 19.5 C, near ordinary ambient
temperature, so working with the aqueous solution is your realistic
product, not pure anhydrous acid, which would simply boil away without
refrigeration you do not have.

**How you know it worked.** It etches glass on contact within minutes via
`SiO2 + 4 HF -> SiF4 + 2 H2O`; no other Roman-accessible substance does
this at ordinary temperature.

**Failure modes.** Glass or ceramic vessels are destroyed by the product
they are making, ruining the batch. Thin or pitted lead vessels can fail.

**Cost & labour.** ESTIMATED (basis: comparable small-batch retort
labour). Materials are cheap once fluorspar is found; the real cost is
finding a deposit and the extreme handling discipline required.

**Danger. Read this even if nothing else.** This is the most dangerous
substance in the module, worse than its acid strength suggests, because
of how it kills. Contact often causes little or no immediate pain, so a
real exposure is easy to miss. The fluoride ion penetrates skin and binds
calcium and magnesium in underlying tissue and, absorbed in enough
quantity, throughout the body including bone, causing damage that
continues for hours and can trigger fatal cardiac arrhythmia from a
modest-looking exposure well after the person feels fine. The standard
modern treatment, calcium gluconate applied immediately, does not exist
for you and cannot be improvised. Treat every exposure as a medical
emergency with no reliable treatment available. The only real strategy is
prevention: full skin and eye covering always, never breathe the vapour,
work outdoors with strong airflow, dedicated vessels touching nothing
else, and stop work immediately at any splash, washing with running water
for a long time.

**Confidence: HIGH** on the chemistry. **LOW** on the murrhine-ware
aside, explicitly disputed background only.

---

### gunpowder - Gunpowder (*pulvis pyrius*, a later coinage; no Roman
term exists)

**What it is / why you want it.** A mechanical mixture of potassium
nitrate, charcoal, and sulfur that burns explosively fast once properly
prepared. Arguably the highest-impact item in this module, for reasons
beyond chemistry.

**Why you would never guess this.** Two layers. First, the roughly 75/15/10
percent by mass ratio of saltpetre, charcoal, and sulfur is what history
settled on after centuries of trial, not something you would derive from
first principles. Second, and this is the part almost everyone
underestimates: simply mixing the right ratio gives weak, unreliable
"serpentine" powder. The real gate technology is **wet-milling and
corning**, without which the right recipe still gives you no working
weapon.

**Prerequisites.** `saltpetre_nitre_beds` (the actual bottleneck),
charcoal burning, sulfur.

**Roman-available inputs.** Purified, recrystallised saltpetre (~75
percent); charcoal (~15 percent), ideally burned specifically from young
willow or alder shoots at controlled low charring temperature rather than
general hardwood fuel charcoal, giving a more porous, more reactive
product; sulfur (~10 percent), native or volcanic.

**Procedure.** Grind each ingredient separately, fine. Combine in ratio
and dry-mix only briefly; this alone is serpentine powder, not the
finished product. **Wet-mill**: moisten the combined powder with water or
weak spirits into a stiff paste and grind it for a sustained period, in an
edge-runner mill or extended mortar work, forcing intimate, near-particle
contact between oxidiser and fuel that dry mixing never achieves; this is
the actual mechanism behind why corned powder outperforms serpentine
powder. **Corn it**: press the wet mill-cake into dense cakes, partially
dry, break into granules, sieve by size, finish drying. Granulation
controls burn surface area and physically locks the ingredients together
so they cannot segregate. Store dry.

**How you know it worked.** A small measured pinch, ignited in the open,
flashes and burns almost instantly with a sharp report and little clinging
residue, mostly fine ash. Slow fizzling or a caked unburned residue
signals bad ratio, poor grinding, or failed corning.

**Failure modes.** Dry-mixed serpentine powder segregates in handling
(the three ingredients differ in density and particle size) and absorbs
moisture readily, both faults fixed only by proper milling and corning,
not better dry mixing. Impure saltpetre burns sluggishly regardless of
milling quality.

**Cost & labour.** ESTIMATED, bottlenecked entirely by the saltpetre
supply; charcoal and sulfur are cheap and fast by comparison. A sustained
day or more of milling and corning per batch is a reasonable planning
assumption, small next to the one-to-two-year saltpetre cost.

**Danger, physical.** Fire and dust-explosion risk during grinding,
worse with sparking metal tools against stone; grind wet specifically to
suppress this, and keep open flame away from the milling area entirely.
Finished powder is an explosive, store away from heat in modest
quantities.

**Danger, social and strategic.** Gunpowder is very likely the single
technology that most changes your political position, in both directions
at once. Demonstrated, it is enormous leverage for patronage or protection
with whoever you show it to first, and that choice of audience matters
enormously. But it cannot be hidden once shown: the corning insight is
straightforward for any competent observer to reproduce, so secrecy
protects nothing after a first demonstration. The realistic range runs
from forced state service under close control, the likely better case,
through execution as a suspected sorcerer, to kidnap by a rival faction
seeking the knowledge. Treat every demonstration as an irreversible,
high-stakes political act: choose your first audience deliberately,
minimise who ever sees the corning step, and think through Roman
authority's likely reaction before anyone outside your control sees it
work.

**Confidence: HIGH** on the chemistry and corning mechanism. **MEDIUM**
on the exact ratio, the well-known historical figure but one that
Roman-era raw material variability (charcoal quality, saltpetre purity)
may require adjusting in practice.

---

### distillation_fractional - Fractional distillation and the worm still

**What it is / why you want it.** Concentrating ethanol out of wine into a
genuine distilled spirit, something this world does not yet have, plus the
general technique for separating liquids by boiling point.

**Why you would never guess this.** The boiling is obvious once you have
wine and a still head. The actual invention that makes distillation
practical, rather than a slow trickle, is the worm condenser: a long
coiled tube submerged in continuously cool water, giving far more cooling
surface than a simple air-cooled head ever can.

**Prerequisites.** `lab_apparatus`, a coppersmith able to coil a long
tube, wine.

**Roman-available inputs.** Wine, abundant across the Empire; copper or
tin-lined copper for the worm; quicklime for the azeotrope-breaking step.

**Procedure.** Fit the still with a delivery tube leading to a coiled
"worm," submerged in a continuously refreshed tub of cool water large
enough not to heat up during a run. Heat wine gently, well below a hard
boil, since ethanol (boils ~78 C) comes off before the water does.
Redistil repeatedly, discarding the early "foreshot" and late "tail" each
time, concentrating progressively toward, but never past, a fixed
azeotrope around 95.6 percent by weight (about 97.2 percent by volume,
boiling ~78.2 C), where vapour and liquid share the same composition and
ordinary distillation cannot go further. To exceed it, add quicklime to
the ~95 percent spirit: `CaO + H2O -> Ca(OH)2`; the resulting hydroxide,
insoluble in alcohol, drops out as a solid rather than diluting the
mixture, and redistilling gives anhydrous alcohol above the residue. For
harder separations (destructive-distillation products, below), build a
vertical column fitted with plates carrying small domed "bubble caps"
over holes, forcing rising vapour to bubble through a descending liquid
pool on each plate, each acting as one more re-vaporisation/re-
condensation step.

**How you know it worked.** Distilled spirit reliably ignites a small
measured sample with a pale blue flame and no residue; wine itself will
not sustain a flame.

**Failure modes.** An air-cooled head without a worm gives slow, weak
condensation. Heating too hard carries water over with the ethanol.
Skipping fractional redistillation gives weak, low-proof spirit regardless
of apparatus quality.

**Cost & labour.** ESTIMATED (basis: comparable to a substantial cauldron
commission). A worm-fitted still is a meaningful one-time coppersmith
investment; running it afterward is cheap and routine.

**Danger.** Alcohol vapour is flammable and, distilled over an open fire
as it necessarily is, poses a real fire risk; ventilate well and separate
the flame from the collection vessel as far as practical. No social danger
beyond the obvious demand a genuinely intoxicating spirit will create.

**Confidence: HIGH.** Standard physical chemistry; azeotrope figures and
the quicklime-drying method are solid textbook facts with no anachronism
risk once a still exists.

---

### destructive_distillation - Destructive distillation of wood and coal

**What it is / why you want it.** Heating wood or coal in an air-starved
sealed vessel breaks it into useful fractions instead of just heat and
ash: from wood, methanol, acetic acid, tar, and charcoal; from coal, coke,
coal gas, coal tar, and ammonia liquor. Coal tar is the gateway to dyes,
phenol, and eventually plastics.

**Why you would never guess this.** Starving the fire of air, the
opposite of what normally makes a fire hotter or more productive, is
exactly what preserves these fractions instead of destroying them all as
smoke and ash.

**Prerequisites.** `lab_apparatus` scaled to a sealed retort or oven; for
coal, access to it, a real but geographically distant resource (Roman
Britain already mines and burns "sea coal," historically attested, though
shipping it to an Italy-based operation is a genuine logistics problem).

**Roman-available inputs.** Wood, effectively unlimited; coal, from
British deposits.

**Procedure.** For wood: load split wood into a sealed retort with a
single outlet to a cooled receiver. Heat the outside only, never letting
air reach the wood. The escaping vapour condenses into a watery, sharp
pyroligneous liquor (methanol and acetic acid together) with a denser tar
layer separating out. What remains solid is charcoal, more thoroughly
carbonised than open-fire charcoal since none burned to ash. Separate the
liquor's fractions by fractional distillation: methanol comes off first
at lower temperature, leaving acetic acid behind. For coal (coking): load
coal into the same style of sealed retort or oven and heat strongly and
sustained without air reaching it. Collect an ammonia-bearing watery
condensate, a thick black coal tar, and an uncondensed flammable gas
(hydrogen, methane, carbon monoxide) pipeable for light or heat. What
remains solid is coke, harder and hotter-burning than raw coal or
charcoal.

**Uses.** Methanol: solvent and fuel, more toxic than ethanol, never
confuse the two. Pyroligneous acetic acid: stronger than wine vinegar,
feeds `organic_reagents_first_tier`. Wood tar: waterproofing, alongside
pine pitch Romans already use. Coke: hotter metallurgical fuel for later
high-temperature work. Coal gas: lighting and heating fuel. Coal tar:
banked for chemistry beyond this module, the raw material for later dyes,
phenol/carbolic acid antiseptic, and eventually plastics feedstock.
Ammonia liquor: nitrogen source for the Solvay process.

**How you know it worked.** Wood distillation: a sharp watery liquid
separates from a denser tar layer, dense black charcoal left solid.
Coking: a hard, silvery-grey, porous residue that rings and burns
differently from raw coal, alongside tar and a strong ammoniacal liquid.

**Failure modes.** Any air leak burns the contents instead of pyrolysing
them, destroying the fractions. Under-heating leaves the process
incomplete with poor separation.

**Cost & labour.** ESTIMATED (basis: comparable to substantial charcoal-
burning or smelting work). Wood route is cheap in material, moderate in
labour and vessel wear; coal coking is limited less by process labour
than by shipping coal from Britain, a real cost to weigh before committing
to this route early.

**Danger.** Methanol is toxic if ingested and must be stored separately
from drinking alcohol. Coal gas contains carbon monoxide and is dangerous
if it accumulates in an enclosed space. Coal tar is an ongoing low-grade
toxic and irritant exposure with repeated handling; cover skin and
ventilate as routine practice.

**Confidence: HIGH** on the wood process. **MEDIUM** on the coal route
specifically for 100 AD, chemically identical but dependent on the
attested but distant Romano-British coal trade.

---

### organic_reagents_first_tier - First-tier organic reagents

**What it is / why you want it.** A working shortlist, in realistic order
of reachability: soap, ethanol, glacial acetic acid, ether, acetone,
oxalic acid, and chloroform.

**Why you would never guess this.** Obvious once you want each item
individually; the non-obvious part is the ordering, since several look
"easy" but depend on acids or gases not yet built, while one of the most
useful, soap, needs no acid at all and can be your first organic product.

**Prerequisites.** Varies per item: `potash_and_soda` for soap;
`distillation_fractional` and `destructive_distillation` for acetic acid
and ethanol; `sulfuric_acid_retort` or `lead_chamber` for ether and
acetone; `hydrochloric_acid` plus a chlorine source for chloroform.

**Roman-available inputs.** Olive oil or tallow and causticised alkali
for soap; wine for ethanol; wood ash or lime, plus pyroligneous acid or
vinegar, for the acetate salts behind acetic acid and acetone; sulfuric
acid for ether; nitric acid or wood-sorrel-family plants (already Roman
flora) for oxalic acid; pyrolusite (MnO2) and hydrochloric acid for the
chlorine chain behind chloroform.

**Procedure, in realistic order.** (1) **Soap**, first and easiest: fat
boiled with causticised alkali until saponified, no acid needed. Per the
anachronism rules, Gallic *sapo* is a scented hair pomade, not true
saponified cleansing soap; a proper causticised-alkali soap for washing
is a genuine new product here. (2) **Ethanol**, via a worm still and
wine. (3) **Glacial acetic acid**: convert pyroligneous acid or vinegar
into a solid metal acetate (boil with wood ash or lime), then distil that
acetate with concentrated sulfuric acid, which displaces concentrated
acetic acid vapour. (4) **Diethyl ether**: heat ethanol with concentrated
sulfuric acid at controlled moderate temperature (too hot gives flammable
ethylene instead), `2 C2H5OH -(H2SO4, heat)-> (C2H5)2O + H2O`, feeding
more ethanol as ether distils off; historically the "sweet oil of
vitriol" method (attributed, unverified for exact period text). (5)
**Acetone**, a byproduct fraction from dry distillation of the same metal
acetate, heated alone. (6) **Oxalic acid**: oxidise sugar or starch with
strong nitric acid, or extract from wood-sorrel-family plants by boiling,
precipitating with lime, then releasing the acid with a stronger acid.
(7) **Chloroform**, the most distant item: chlorine gas first (`MnO2 + 4
HCl -> MnCl2 + Cl2 + 2 H2O`, Roman-feasible since pyrolusite is already
known), absorbed into slaked lime for bleaching powder, then reacted with
ethanol or acetone in a haloform reaction.

**How you know it worked.** Soap lathers and cleans rather than
separating back into fat and alkali. Ethanol burns with a pale blue
flame. Glacial acetic acid smells and stings sharply and freezes near
16.6 C if cooled, unlike ordinary vinegar. Ether is intensely volatile
and smells sweet. Oxalic acid crystals dissolve rust stains on contact.

**Failure modes.** Impure or under-causticised alkali fails to saponify
fat cleanly. Ether overheated during preparation gives ethylene gas
instead. Oxalic acid extraction from plants gives low, variable yield
compared to the nitric acid route.

**Cost & labour.** ESTIMATED throughout, scaling with each item's
prerequisite acid or gas; soap and ethanol are cheap and fast, ether and
acetone moderate, oxalic acid and chloroform the most demanding.

**Danger.** Ether is extremely flammable, vapour heavier than air and
able to travel to a distant flame. Methanol-contaminated wood spirit is
toxic if mistaken for drinking ethanol. Chloroform's precursor chlorine
and bleaching-powder chemistry carries real respiratory hazards.

**Confidence: HIGH** on soap, ethanol, ether, and acetic acid. **MEDIUM**
on chloroform's period feasibility, which stacks several uncertain
prerequisite processes.

---

### analytical_chemistry - Analytical chemistry and the assay bench

**What it is / why you want it.** Weighing precisely (gravimetric
analysis), determining acid or alkali strength by titration, identifying
elements by flame colour, and assaying ores with a blowpipe. Without this,
nothing in this module is reproducible.

**Why you would never guess this.** It is easy to treat analysis as a
refinement to add later. It is in fact the opposite: every acid strength
and yield claim in this whole module is meaningless from batch to batch
without a way to measure and compare. This is not optional polish, it is
the feedback loop that turns "I did something like the recipe" into "I
know what I made," and belongs early, alongside `lab_apparatus`.

**Prerequisites.** A skilled metalworker for fine balance construction,
plant material for indicators, `lab_apparatus` for volumetric glassware.

**Roman-available inputs.** Fine balance construction builds on existing
skill: Roman mints and jewellers already weigh coin and gems to a
meaningful tolerance, so a knife-edge beam balance extends existing craft
rather than inventing from nothing. Plant indicators: red cabbage juice,
boiled from shredded leaves, and lichen-derived purple dye (orchil),
already an antique dyestuff (Pliny references a purple-yielding
plant/lichen dye under names such as *fucus*, attributed, unverified);
using either for pH is a repurposing insight your modern knowledge
supplies, not a Roman dyer's idea. Cobalt-blue glass as a flame-test
filter. Charcoal blocks and a mouth-blown blowpipe.

**Procedure.** Build a beam balance with a hardened knife-edge pivot and
symmetric pans, calibrated against reference weights made by repeated
halving and cross-checking. ESTIMATED (basis: fine coinage/jewellery
craftsmanship): a well-made balance likely resolves on the order of one
part in a thousand to one part in ten thousand of its load, a few
milligrams on a ten-gram sample; confirm against your own instrument.
For gravimetric analysis, convert a sample into a form of known
composition (precipitate, or dry/ignite to constant mass) and weigh it
against the original. For titration, add a solution of known
concentration gradually to a measured volume of unknown, watching a plant
indicator (red cabbage juice, red/pink in acid, green/blue in alkali) for
the colour-change point; the volume needed gives the unknown's strength.
For flame tests, dip a clean iron wire in a sample and hold it in a clean
flame: sodium gives intense yellow, potassium a faint lilac usually
masked by sodium and best viewed through cobalt-blue glass, copper
blue-green; this is your main check that a saltpetre batch is genuinely
potassium-based. For blowpipe assay, direct a hot flame onto a mineral
fragment on a charcoal block with borax or soda flux and read the
resulting bead's colour and any separated metal, a real field-assay
method standard well into a much later era.

**How you know it worked.** A trustworthy balance gives the same reading
on repeated weighings and correctly detects a small added test weight. A
trustworthy titration gives closely agreeing results on repeated runs of
the same sample.

**Failure modes.** A dull or uneven pivot gives inconsistent readings that
look precise but are not, worse than no measurement since it creates false
confidence. Indicators degrade with age and should be checked fresh
against a known acid and alkali before trusting a result.

**Cost & labour.** ESTIMATED (basis: comparable to a fine jeweller's/mint-
adjacent commission). A well-made balance is a real, one-time investment
worth prioritising early since every other entry depends on measuring its
output.

**Danger.** Minimal directly; the serious risk is skipping this entry,
since every acid-strength and dosage figure elsewhere becomes an
unverifiable guess without it.

**Confidence: HIGH** on the general methods, all real, well-attested
pre-modern techniques. **LOW** on the specific balance resolution figure,
explicitly flagged ESTIMATED.

---

### electrolysis_chemistry - Electrolytic chemistry

**What it is / why you want it.** Once electricity exists (Module 50),
passing current through solutions or molten salts unlocks chlorine and
caustic soda together, metallic sodium, metallic aluminium, and hydrogen
and oxygen from water.

**Why you would never guess this.** This entry has no earlier place in
your technology arc regardless of how badly you want its products: it is
entirely gated on reliable electricity, and there is no period-plausible
chemical shortcut to metallic aluminium at all, which is exactly why
aluminium historically remained a precious-metal-priced curiosity until
electrolysis existed.

**Prerequisites.** Module 50 (electricity generation) is a hard
prerequisite for this entire entry; nothing below is reachable by any
method covered in this guide until it exists.

**Roman-available inputs.** Brine (sea salt dissolved in water), alumina
(extractable from clay or bauxite-type ore), cryolite (a rarer imported
mineral flux), and plain water are all otherwise Roman-reachable; the
only missing ingredient is a source of direct electric current.

**Procedure.** Chlor-alkali: electrolyse brine, `2 NaCl + 2 H2O -> Cl2 +
H2 + 2 NaOH`, a far cleaner route to both than the chemical methods used
earlier in this module. Sodium metal: electrolyse molten NaOH, which is what Davy actually did in
1807. Electrolysing molten sodium chloride is the Downs process and is a
20th-century industrial development needing a much higher cell temperature and
a calcium chloride flux; do not plan around it.
the original historical route to isolated sodium. Aluminium: electrolyse
alumina dissolved in molten cryolite, more electricity-hungry than the
rest, a later, more ambitious target. Hydrogen and oxygen: `2 H2O -> 2 H2
+ O2`, achievable even with a small primitive battery, the simplest
application and a clean alternative to the chemical routes in
`industrial_gases`.

**How you know it worked.** Gas bubbles visibly at each electrode;
chlorine's sharp smell and hydrogen's light "pop" on ignition confirm
which is which, the same tests used in `industrial_gases`.

**Failure modes.** Weak or inconsistent current gives slow, unreliable
gas evolution and poor metal deposition; electrode material that reacts
with the electrolyte (most metals besides the specialised ones actually
used industrially) contaminates or destroys itself over a run.

**Cost & labour.** Deferred entirely to Module 50 and whatever generation
capacity exists at the time; not estimable in isolation from that
module's own figures.

**Danger.** Chlorine gas at the anode is a serious inhalation hazard
(see the kill-list below); molten electrolytes for sodium and aluminium
work are severe burn and fire hazards. All deferred in scale to Module
50's own safety picture.

**Confidence: HIGH** on the chemistry itself, textbook and certain,
conditional entirely on the electrical prerequisite being met.

---

### industrial_gases - Industrial gases: oxygen and hydrogen without
electricity

**What it is / why you want it.** Producing oxygen and hydrogen by
chemical means, before electrolysis exists, primarily to feed an
oxy-hydrogen torch capable of temperatures beyond ordinary charcoal and
bellows, needed for working fused quartz on the road to precision glass
and electronics.

**Why you would never guess this.** A hydrogen flame in pure oxygen
reaches far higher temperature than any bellows-fed charcoal fire,
because it is not burdened with heating a large volume of inert
atmospheric nitrogen the way an ordinary air-fed fire is; not intuitive
from everyday experience of fire.

**Prerequisites.** For oxygen: mercury (Roman-available, Almaden, Spain)
or a chlorate source needing prior chlorine chemistry. For hydrogen: iron
and an acid.

**Roman-available inputs.** Mercury; potassium chlorate (later-tier, needs
chlorine first); iron; sulfuric or hydrochloric acid.

**Procedure.** For oxygen, mercuric oxide route: heat mercury gently in
open air over a sustained period to form red mercuric oxide (a real,
historically attested method), then heat the oxide more strongly in a
retort, `2 HgO -> 2 Hg + O2`, condensing and recovering the mercury vapour
rather than releasing it, both for value and because it is a serious
poison. Chlorate route: heat potassium chlorate with a small, reusable
amount of manganese dioxide as catalyst, `2 KClO3 -> 2 KCl + 3 O2`, at a
lower temperature than chlorate alone needs; treat as a later refinement
once chlorine production is routine, since it needs chlorate first. Plain
MnO2 heated alone releases oxygen at very high temperature but
inefficiently. For hydrogen: add iron filings or scrap to dilute sulfuric
or hydrochloric acid in a vessel fitted with a gas-collection tube: `Fe +
2 HCl -> FeCl2 + H2`, releasing gas steadily while acid and metal remain.
Zinc would react faster, but clean metallic zinc is genuinely difficult
for Romans (they know zinc-bearing calamine ore for cementation brass but
not a clean route to the isolated metal); iron is the practical choice
and works perfectly well.

**Why it matters.** An oxy-hydrogen or oxy-fuel torch reaches a flame
markedly hotter than a bellows-fed charcoal fire (roughly 1200 C
hand-blown, toward 1500 C water-blown, per the general rule elsewhere in
this guide), enough to work fused quartz, whose softening point sits well
above ordinary furnace reach, a genuine gate technology toward vacuum
tubes and quartz components in Module 50 and beyond.

**How you know it worked.** Oxygen relights a glowing, not flaming, wood
splinter near the outlet. Hydrogen gives a light "pop" when a small
sample is ignited near an open flame, distinct from oxygen's relighting.

**Failure modes.** Overheating the mercury route risks losing mercury
vapour into the room instead of condensing it. Weak acid or poor iron
gives slow, low-yield hydrogen.

**Cost & labour.** ESTIMATED (basis: comparable small-batch retort work).
Modest materials cost; the mercury route is limited by how much repeated
mercury exposure you are willing to risk, the hydrogen route is cheap once
any acid exists.

**Danger.** Mercury vapour is a serious cumulative neurological poison
with no dramatic immediate symptom; always heat mercury or its oxide
outdoors or with strong ventilation. Hydrogen and oxygen together, or
hydrogen alone in enclosed air, are a real explosion risk if allowed to
mix and accumulate before ignition.

**Confidence: HIGH.** Both routes are real, historically attested methods
(the mercuric oxide route is literally how oxygen was first isolated) with
straightforward, certain chemistry.

---

## Acid strength reference

Realistic concentrations by route, since acid is not just acid. Figures
below are standard textbook/historical characteristics of each named
process, not Roman-era measurements, since Romans have no concentration
instrument of their own, only the observable tests given in each entry.

- **Sulfuric acid, dry distillation (`sulfuric_acid_retort`,
  Nordhausen-type):** very high, approaching or exceeding 100 percent
  equivalent with free dissolved SO3 ("fuming"), MEASURED as a
  characteristic of this real historical process, batch purity varying
  with vitriol quality and distillation care.
- **Sulfuric acid, lead chamber ("chamber acid," `lead_chamber`):**
  roughly 35-40 percent by weight as collected, MEASURED as the general
  character of historical chamber acid. Boiling down in lead pans
  concentrates it further, limited by the pan itself; a Glover tower can
  push it toward the high 70s percent.
- **Nitric acid (`nitric_acid`):** a maximum-boiling azeotrope with water
  at roughly 68 percent by weight, boiling around 121 C, MEASURED as a
  standard physical constant. Excess concentrated sulfuric acid as
  dehydrating agent during distillation can push the product past this,
  toward fuming, above roughly 86 percent, red-brown from dissolved NO2.
- **Hydrochloric acid (`hydrochloric_acid`):** a hard ceiling at ordinary
  room temperature of roughly 38-40 percent by weight; past that, water
  cannot hold more dissolved HCl gas and it bubbles back out, MEASURED as
  a physical constant, not a limitation of care. Colder absorption water
  pushes slightly higher.
- **Hydrofluoric acid (`hydrofluoric_acid`):** realistically a moderate-
  strength aqueous solution (tens of percent by weight, ESTIMATED, basis:
  practical limits of lead/wax vessel collection at Roman-achievable
  temperatures). Anhydrous liquid HF boils at about 19.5 C, near ordinary
  ambient temperature, making it impractical to hold without
  refrigeration you do not have; the aqueous form is your realistic
  product and remains extremely hazardous at any concentration.

---

## What will kill you in your own laboratory

Ordered by how likely each hazard is to actually get you, not by how
dramatic it sounds.

1. **Carbon monoxide from enclosed charcoal and coal fires.** The most
   likely killer, simply because it is the most constant exposure: nearly
   every entry here runs on charcoal or coal heat, Roman workshops already
   normalise indoor braziers, and CO is odourless with no warning before
   it incapacitates. Any enclosed retort room or drying shed needs real,
   deliberate airflow, especially overnight with a smouldering fire.
2. **Chronic lead and mercury exposure.** Central to this module's acid
   and oxygen work; both cause cumulative, insidious poisoning from
   repeated small exposures that feel like nothing and add up over
   months. Wash hands and face after every session; never eat or drink
   near active lead or mercury work.
3. **Nitrogen oxide gas from lead chamber, bell, and nitric acid work.**
   Dangerous because immediate symptoms (mild throat irritation, a slight
   cough) feel minor while serious lung injury develops silently over the
   following twelve to twenty-four hours. Anyone exposed should rest and
   be watched closely for a full day afterward, even feeling fine.
4. **Sulfur dioxide and sulfuric acid mist.** Frequent, accompanying
   nearly every sulfuric acid process, but more self-limiting than
   nitrogen oxides: strong irritation drives people out before serious
   harm in most cases, though repeated exposure still damages lungs and
   splashes burn.
5. **Chlorine gas**, once you are producing it. Immediately and
   powerfully self-warning at low concentration, which limits surprise
   exposures, but a real concentrated dose in an enclosed space is
   genuinely lethal.
6. **Fire and dust explosion from gunpowder milling, and solvent fires
   from ether and concentrated ethanol.** Less frequent with real
   discipline (wet-milling to suppress spark risk, keeping flame and
   vapour apart), but fast-moving and catastrophic when it happens.
7. **Hydrofluoric acid.** The rarest exposure here, but per-incident the
   most dangerous substance in the module: painless initial contact,
   delayed systemic damage, no available period antidote.
8. **Contaminant metals in vitriol and ore sources**, most notably
   arsenic, sometimes occurring alongside pyrite and other sulfide
   minerals. ESTIMATED risk, since exact ore purity varies by site and is
   unknown here; a background possibility for sustained work from a
   single mineral source, not a specific quantified danger.

---

## Sources and confidence

**Ancient sources a Roman scholar could actually consult**, cited where
reasonably confident and flagged where not: Pliny the Elder's *Naturalis
Historia* (commonly Book 31 on salts, Book 33-34 on metals and mineral
pigments including vitriol-adjacent substances, Book 36 on stones,
including the murrhine-ware discussion in `hydrofluoric_acid`; exact
book/chapter numbers for the specific vitriol and nitrum passages are
attributed, unverified, and should be checked before citing with
confidence). Dioscorides's *De Materia Medica* for vitriol-type minerals
and natron, attributed, unverified for precise passage. Vitruvius's *De
Architectura* for lead-working practice underlying `lab_apparatus` and
`lead_chamber`. Zosimos of Panopolis and the Alexandrian alchemical
tradition (Maria the Jewess among its earliest named figures) for the
cultural plausibility of proto-distillation apparatus, with the caveat
that Zosimos writes after your 100 AD arrival point and is not himself a
period-contemporary source for you.

**Modern chemical and industrial-history knowledge deliberately
retrojected**, the entire premise of this module: the lead chamber
process, the Leblanc and Solvay soda processes, the Nordhausen vitriol
route to sulfuric acid, nitre-bed cultivation, gunpowder corning,
fractional distillation and the ethanol azeotrope, destructive
distillation, and standard gravimetric/volumetric analysis are all
well-documented pre-modern and early-industrial chemistry with a solid
textbook basis. The chemistry is not in serious doubt. What is genuinely
uncertain, and flagged throughout as ESTIMATED, is exactly how fast, at
what yield, and at what quality a single modern person working with
Roman-era artisan labour and materials in 100 AD can run each process,
since no controlled trial of that exact situation exists to cite. Treat
every ESTIMATED figure as a planning assumption to test at small scale,
not a promised result.

**Overall module confidence: MEDIUM-HIGH.** The chemistry throughout is
textbook and essentially certain. The Roman-era material availability
claims are well grounded against this guide's hard rules, with the
saltpetre/nitrum distinction the load-bearing correction the whole module
depends on. The weakest links are the specific yield, timing, and labour
figures for nitre beds and gunpowder milling, both flagged ESTIMATED, and
the coal-logistics assumptions in `destructive_distillation`.
