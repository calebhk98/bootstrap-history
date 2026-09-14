# Module 70: Medicine, Public Health and Biology

Two events are fixed on your calendar regardless of what you plan: the
Antonine Plague (165-180 AD) and the Plague of Cyprian (249-262 AD). Each
kills a large fraction of the Empire's population and everything built on
top of it. A furnace can be rebuilt in a season; a dead school of trained
scholars cannot. Nothing else in this document matters if the people who
know it die of dysentery or smallpox before they teach a second
generation. Read this module alongside `school_founded`, not after it.

Entries are ordered roughly by how soon you need them: sanitation before
germ theory before variolation before anything clever.

---

### sanitation_antisepsis - Boiled water, handwashing, wound irrigation, quarantine (*aqua fervens*, *manus lotae*, no single Roman term covers the practice)

**What it is / why you want it.** Habits that cost nothing but labour and
argument, and save more lives than every machine in this document. In
order of lives saved per hour spent persuading people: (1) handwashing
before touching a wound, birth, or food, (2) boiling drinking and
irrigation water, (3) isolating the visibly sick, (4) never reusing a
dressing, burning soiled ones rather than washing and reissuing them, (5)
flaming instruments before cutting, (6) removing standing waste from
where people sleep and eat.

**Why you would never guess this.** You would guess the abstract fine; the
trap is assuming existing Roman infrastructure already does it. It mostly
does not, and in one case actively works against you (below).

**Prerequisites.** `distillation_alcohol` (20_chemistry.md#distillation_fractional)
for a cheap disinfecting spirit; otherwise none beyond argument and
authority.

**Roman-available inputs.** Aqueduct water (Frontinus, *De Aquaeductu*).
Wine, cheap and mildly antiseptic even undistilled. Linen for dressings,
already produced at scale. Bronze/iron surgical tools, already excellent
(see `surgery_practice`).

**Procedure.** Boil water to a full rolling boil for a few minutes, cool
covered, not open. Wash hands in hot water then wine or spirit before any
wound, birth, or dressing change, and after touching a corpse or a
previous dressing. Set aside a separate room for fever/cough/rash cases,
with its own vessel and attendant. Burn used dressings; if cloth is too
scarce, boil at a full rolling boil, never reuse a suppurating dressing on
a clean wound. Pass blades through flame until faintly glowing, cool in
clean air, not cloth. Route latrine and kitchen waste downhill and
downstream of any well or food store.

**How you know it worked.** Compare two similar patient groups, treated
and untreated, over a season: fouled, swollen wounds ("laudable pus" under
Galenic doctrine, wrongly read as healthy) versus clean closure; sick-room
isolation versus no isolation, tracking secondary household cases. The gap
is visible within one campaign or birthing season.

**Failure modes.** Boiled water poured back into a dirty vessel undoes the
point. A curtain instead of a separate airspace does little. Treating this
as a one-time order rather than a standing, checked practice; old habits
reassert within weeks.

**Cost & labour.** ESTIMATED (basis: prices.json wage rates, labourer
0.075 den/hr, scholar 0.4 den/hr). Roughly 300 personal hours to design
and train the first cohort; ongoing labour near 900 labourer-hours/year
per large household or valetudinarium; capital roughly 400 denarii,
upkeep roughly 300 denarii/year; no calendar floor, effective immediately.
Highest return per denarii in this document.

**Danger.** Physical: minor burns. Social: implies established physicians'
"laudable pus" doctrine is wrong. Sell it first to the army, which already
runs valetudinaria, has a results-tracking officer class, and follows
standing orders.

**On the existing infrastructure, honestly.** *Aqueducts*: genuinely
helpful when the flowing water is used for drinking, cooking, and
flushing rather than left standing. *Public latrines*: mixed. Removing
waste into a sewer (the Cloaca Maxima) is a real gain over none, but
communal multi-seat latrines used one shared sponge on a stick (a
*tersorium*), rinsed in one shared bucket and passed person to person, a
textbook fecal-oral transmission device you should replace early, even
though it will look like you are removing something civilised. (A modern
study of Roman latrine sediments found no improvement in parasite loads
over pre-Roman levels, MEDIUM confidence, exact figures unverified, but
consistent with this mechanism.) *Public baths*: net negative for
infectious disease however socially valuable, since large volumes of warm
water are shared by sick and well alike and changed infrequently; push for
more frequent changes and separate hours for the visibly unwell rather
than trying to close them.

**Confidence: HIGH.** The mechanism is textbook; the infrastructure
description is well attested in Frontinus and Vitruvius and
archaeologically. The *tersorium* parasite-load claim is MEDIUM, resting
on a modern inference rather than a Roman measurement.

---

### germ_theory - Germ theory of disease (no Roman term; the closest existing idea is Varro's *semina morbi*, "seeds of disease")

**What it is / why you want it.** Demonstrating, not merely asserting,
that specific invisible living agents cause specific diseases and spread
by specific routes, against the dominant model of disease as an imbalance
of the four humours. Without this, no one accepts sanitation, quarantine,
or variolation as more than superstition.

**Why you would never guess this.** Rome already has a half-built
conceptual slot for it: Varro speculated in writing that marshes breed
"certain minute creatures, invisible to the eye... that enter the body
through mouth and nose and cause disease" (*De Re Rustica* 1.12.2,
attributed, unverified for exact wording, but a standard citation in
histories of epidemiology). Anchor your demonstration to that existing
idea rather than presenting germ theory as a foreign import.

**Prerequisites.** `glass_bead_microscope` (30_glass_optics.md#glass_bead_microscope),
`glass_lab_ware` for sealed and swan-neck flasks.

**Roman-available inputs.** Clear blown glass, already mature Roman craft.
Meat or vegetable broth. Pond water for first microscope samples. A
skilled glassblower to draw a long curved neck, well within existing
lamp-working skill.

**Procedure.** Three independent demonstrations, kept independent so no
single objection dismisses all three. (1) **Bead microscope**: a single
polished glass bead mounted so a sample sits a hair's breadth from its
focus (30_glass_optics.md#glass_bead_microscope). Pond water shows small
shape-shifting bodies (protozoa) and, at the resolution limit, faint
moving rods (large bacteria). This alone proves nothing about disease. (2)
**Boiled vs unboiled, sealed vs open broth**: unboiled broth spoils
regardless of sealing; boiled and sealed stays clear far longer than
boiled and open. Strongest version: a swan-neck flask, boiled broth
inside, neck open to air but bent in a low S-curve. Air passes freely but
dust settles in the bend and never reaches the broth, which stays clear
indefinitely; wipe the bend's inside and let the washings run down, and it
clouds within days. This shows clear air alone does not spoil broth, but
settled airborne matter does, directly contradicting spontaneous
generation. (3) **Treated vs untreated wounds**: assign similar wounds by
simple alternation to the `sanitation_antisepsis` regimen or standard
Galenic practice, record fever, suppuration, and death over a month.

**How you know it worked.** The broth test is self-demonstrating over two
weeks of side-by-side observation. The wound comparison needs several
dozen wounds per arm, counts recorded before treatment begins.

**Failure modes.** A cracked "sealed" flask gives a false negative.
Uneven wound cohorts (worst cases bunched in one arm by chance) blur the
result. Expect Galenists to reinterpret results inside humoral vocabulary
rather than abandon it after one demonstration.

**Cost & labour.** Per rome/data/tech_tree.json node `germ_theory`
(confidence C there): roughly 350 personal hours, 1500 scholar-hours over
two years, capital ~250 denarii, upkeep ~150 denarii/year. Cheap; the
expense is in years and status, not denarii.

**Danger.** Minimal physical risk. Real social risk: telling wealthy,
connected physicians their training rests on a wrong premise, in public.
Do the broth demonstration under a patron, for primed witnesses, not as a
street spectacle.

**Confidence: HIGH** on the physics and biology (the swan-neck experiment
is Pasteur's, needing only Roman glassblowing skill). **MEDIUM** on the
exact Varro wording.

---

### variolation - Smallpox inoculation (no Roman term; propose *insitio variolae*, "grafting of the pox")

**What it is / why you want it.** Deliberately giving a small, controlled
dose of smallpox through the skin, producing a mild localised case and
lasting immunity, instead of risking a severe naturally-acquired case.
The single most important entry here if the Antonine Plague is smallpox;
worthless if it is not.

**Why you would never guess this.** It looks reckless. The non-obvious
part is that dose and route matter enormously, and that this was worked
out empirically, long before any Western scientific medicine, by the
simple observation that survivors of a mild pox never catch it again.

**Prerequisites.** `germ_theory` (to defend it against Galenic objection),
`sanitation_antisepsis` (for the inoculation site and isolation of the
inoculee).

**Roman-available inputs.** No special material beyond an active mild
smallpox case and a clean blade; a technique, not an import.

**Procedure.** (1) Take material only from a **mild** case (modest,
scattered pustules, never a confluent or haemorrhagic case, which
inoculates severity along with immunity). (2) Take clear or slightly
turbid fluid from an unbroken pustule around day 8-10 of eruption, a
smaller and better-controlled dose than thick mature pus. (3) Make a
small superficial scratch, not a deep cut, on the outer upper arm, and
work in a minimal amount of material. (4) Isolate the inoculee for the
full resulting illness, as any smallpox case. (5) Keep the chain going
arm-to-arm from one inoculee's pustule to the next, rather than returning
repeatedly to severe natural cases, to keep severity consistent.

**How you know it worked.** A small local pustule develops within one to
two weeks, with mild fever, then resolves; subsequent deliberate exposure
to an active natural case produces no reaction.

**Dose problem, plainly.** This kills a real minority of recipients, since
it is a live dose of a genuinely lethal disease with no precise way to
titrate it here. Best available data (18th-century inoculation
programmes, MEASURED from those, not from any Roman source) put
variolation case-fatality around 1-2 in 100, against roughly 20-30 in 100
for natural smallpox in the same records. The ratio is solid; the exact
percentages are ESTIMATED for your context, since outcome depends on
inoculator skill, patient nutrition, and circulating strain.

**On priority.** Long predates Jenner (1796): practised in China (nasal
insufflation of powdered scabs, origin uncertain, 10th-16th century in
different accounts, attributed, unverified) and in West Africa (brought to
English-speaking attention by an enslaved West African man's account to a
Boston minister, early 18th century, attributed, unverified). It has no
single inventor.

**On the Antonine Plague specifically.** You know it arrives around 165
AD; you do not know for certain what it is. What survives of Galen's
account (attributed, unverified for exact passage) describes fever and a
pustular or dark rash, consistent with smallpox but also with measles, and
modern historians genuinely disagree. Do not build your survival plan on
variolation alone: if the disease is measles, smallpox material does
nothing, and no equivalent pre-modern measles inoculation exists. Build
`quarantine_publichealth` and `sanitation_antisepsis` as your primary,
pathogen-agnostic defence, and validate variolation in the decades before
165 AD against whatever pox or rash disease you can actually observe,
distinguishing smallpox (deep, umbilicated pustules on face and limbs)
from measles (fine rash from the hairline down, preceded by small white
mouth spots, a genuine and teachable sign).

**Failure modes.** Material from a severe case, or too much of it,
produces a severe inoculated case. A dirty blade transmits an unrelated
disease. Failing to isolate the inoculee turns a controlled demonstration
into an outbreak.

**Cost & labour.** ESTIMATED, low material cost; the real cost is years of
small-scale, low-stakes trial before inoculating anyone politically
important (see "How not to be executed for this").

**Danger.** Physical: a real, non-trivial chance of killing the recipient,
smaller than natural infection but not zero, and this must be disclosed.
Social: a visible death in a prominent family is the single most dangerous
event in this module.

**Confidence: MEDIUM.** Mechanism and mortality comparison are solid
(18th-century record). **LOW** on whether the Antonine Plague is even
smallpox, flagged explicitly, not to be papered over.

---

### vaccination_cowpox - Vaccination from cowpox (*variolae vaccinae*, "pox of the cow")

**What it is / why you want it.** The safer successor to variolation:
cowpox material instead of live smallpox, removing most of variolation's
~1-in-100 death risk.

**Why you would never guess this.** Not obvious from first principles; it
comes from the folk observation that dairy workers who caught cowpox from
their animals never seemed to catch smallpox afterward.

**Prerequisites.** `variolation`, `germ_theory`, ongoing surveillance under
`veterinary_and_agriculture_link`.

**Roman-available inputs.** Cattle and dairying, universal (Columella
writes on it at length). No new material beyond finding a genuine cowpox
outbreak.

**Procedure.** Maintain standing surveillance of dairy herds and milkers
for pustular lesions, since cowpox is sporadic. On a confirmed case (mild
local pustules, little systemic illness, unlike smallpox), take fresh
pustule material and inoculate by the same arm-scratch method as
variolation. Maintain the chain by arm-to-arm transfer, since natural
outbreaks are too rare to be the sole source. Once confidence is high,
confirm protection by challenging a small number of consenting,
informed volunteers with variolation material and observing no reaction,
as in the historical 1796 test.

**How you know it worked.** A mild local pustule develops and little
else; a subsequent variolation challenge produces no reaction.

**What this needs beyond variolation.** Reliable identification of true
cowpox against other, non-protective cattle skin conditions (takes
practice and false starts), a continuously maintained living-material
chain since cowpox does not keep as dried material the way smallpox does,
and eventual willingness to run the confirmatory challenge test.

**Failure modes.** Mistaking an unrelated lesion for cowpox gives a false,
unprotective inoculation wrongly trusted. Losing the chain (no fresh case,
no surviving inoculee) forces a new hunt.

**Cost & labour.** ESTIMATED, similar order to variolation, plus ongoing
veterinary inspection labour, a few hundred labourer-hours/year across a
modest number of estates.

**Danger.** Physical risk much lower than variolation, not zero. Social
risk lower, since there are fewer visible deaths to explain.

**Confidence: MEDIUM.** Biology is solid and historically proven (Jenner,
1796). Capped at MEDIUM because finding a confirmed Roman-era cowpox
outbreak on demand has no knowable timeline; you may wait years.

---

### quarantine_publichealth - Quarantine, clean water, sewage separation and food inspection (*custodia*, *cura aquarum*, no single Roman term covers the whole programme)

**What it is / why you want it.** The pathogen-agnostic layer: isolation
of the sick, cordons, contact tracing in a pre-statistical society,
protected water, separated sewage, inspected food, backed by enough
political authority to enforce any of it.

**Why you would never guess this.** The mechanism is intuitive once you
believe in contagion; the hard part is political, fitting requests into
categories of authority that already exist rather than inventing new ones.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`, `school_founded`
(explicitly required in rome/data/tech_tree.json node
`plague_preparedness`).

**Roman-available inputs.** Existing civic machinery to extend, not
invent: aediles (market inspection), the curator aquarum (water supply),
local collegia (membership registries doubling as reporting networks),
funeral colleges and undertakers (an informal mortality register),
midwives (a birth register).

**Procedure, isolation and tracing.** Set isolation by the disease's own
observed course: for smallpox, roughly 10-14 days incubation before
symptoms, then 3-4 weeks of active infectiousness until scabs fall away,
a full case-isolation window near six weeks; watch known contacts for the
shorter 10-14 day incubation window before clearing them. (Do not import
the later, unrelated "forty days" maritime quarantine convention as though
derived from this disease's biology; it was not.) Trace contacts through
household heads and collegium officials naming who a newly sick person
lived and worked with, and move those named into watched status. Use a
physical cordon around an afflicted household, ship, or quarter, food and
water passed in, no one passed out, enforced by whatever armed authority
the local magistrate controls.

**Procedure, water and sewage.** Confirm no latrine or sewer outflow sits
upstream of, or drains toward, a well or aqueduct intake. Where night
soil fertilises market gardens (a real Roman practice), insist on a long
composting period before it touches food crops. Keep drinking cisterns
covered and cleaned on a fixed schedule.

**Procedure, food inspection.** Extend the aediles' existing market
authority explicitly to spoiled meat and fish (a real risk in a
garum-producing economy) and contaminated grain, with a sense-based
standard: no strong off-odour, no mould, no discoloured or slimy flesh.

**How you actually get a magistrate to act.** Do not present this as new
medicine; present it as protecting a mandate the magistrate already holds
and is already judged on. Get results first where outcomes are already
tracked, the legion again, and bring that endorsement to a civilian
magistrate afterward. Secure a patron of real standing before approaching
any magistrate who does not already know you; an unknown foreigner asking
to cordon part of a town otherwise reads as a threat to public order.

**How you know it worked.** Fewer new cases outside a cordon than inside;
fewer illnesses among traced-and-watched contacts than an untraced
comparison group, visible within one outbreak.

**Failure modes.** An unenforced cordon is a suggestion. Contact tracing
through collegium officials misses districts with no collegium coverage,
usually the poorest and most crowded. Food inspection without a clear
standard degenerates into arbitrary enforcement or bribery.

**Cost & labour.** Per rome/data/tech_tree.json node
`plague_preparedness` (confidence C there, explicitly flagged as "the
highest expected-value defensive investment in the game"): roughly 700
personal hours, 2500 scholar-hours, 6000 labourer-hours over four years,
capital ~6000 denarii, upkeep ~2000 denarii/year.

**Danger.** More political than physical: cordoning a town quarter or
declaring food contaminated threatens vested interests (landlords, grain
merchants, sometimes a magistrate's own business). Act only with a
patron's written authority behind you.

**Confidence: MEDIUM.** The public health mechanisms are well understood.
The isolation-period numbers are DERIVED from smallpox's own known course,
only as reliable as the assumption the coming epidemic follows it (see
the uncertainty flagged under `variolation`).

---

### anaesthesia_analgesia - Pain relief and anaesthesia (*sedatio doloris*)

**What is genuinely available now.** Opium poppy (*papaver*, already
cultivated, in Dioscorides): reliable sedation and pain relief, but the
effective and fatal dose are close, overdose kills by suppressing
breathing, repeated use causes dependence. Mandrake (*mandragora*) and
henbane (*hyoscyamus*), both in Dioscorides: real tropane-alkaloid
sedation, but potency varies wildly by plant and season, and the margin
between sedation and a fatal or delirium-inducing dose is narrow and
unpredictable; historical "soporific sponge" mixtures of these with opium
gave inconsistent, sometimes dangerous results, not reliable
unconsciousness. Wine and alcohol dull pain only mildly, impair
cooperation, provoke vomiting, and thin the blood, worsening bleeding.
None of these, alone or combined, reliably produces the still, unconscious
state true surgical anaesthesia requires.

**What follows, and what it needs.** Diethyl ether and chloroform are true
general anaesthetics (first surgical use 1846 and 1847 historically).
Ether needs ethanol (`distillation_alcohol`) heated with concentrated
sulfuric acid under controlled, moderate heat (20_chemistry.md#organic_reagents_first_tier;
overheating gives flammable ethylene instead). Chloroform needs a chlorine
source (pyrolusite plus hydrochloric acid) absorbed into slaked lime, then
reacted with ethanol or acetone in a haloform reaction (same
cross-reference). Both are downstream of a working acid industry, not
available alongside the plant-based options above.

**Why surgery without anaesthesia is limited to about two minutes.** A
conscious patient in severe pain can hold still and avoid unmanageable
shock only briefly, on the order of a couple of minutes for major cutting
(the fastest pre-anaesthesia surgeons, historically, trained specifically
for speed within this window; attributed, unverified for an exact figure,
consistent with the period's surgical literature). This bounds what is
possible: fast amputation, yes; sustained internal or exploratory surgery
on a conscious patient, essentially no.

**How you know it worked.** Plant preparations: drowsy, less pain, still
rousable, breathing even; slowed or irregular breathing means overdose,
stop immediately, keep the patient upright and stimulated. Ether or
chloroform: smooth loss of consciousness, no response to a pinch, steady
breathing, reversible within minutes of removing the vapour.

**Failure modes.** Overdose with the plant route is the most common,
best-documented danger. Ether vapour, heavier than air, can travel along
a floor to a distant flame. Chloroform is not flammable but has a
narrower margin to sudden cardiac arrest, historically documented.

**Cost & labour.** ESTIMATED. Plant route nearly free, with dosing risk
learned by careful titration on consenting volunteers first. Ether and
chloroform inherit the full cost of `organic_reagents_first_tier` in
20_chemistry.md.

**Danger.** Overdose death (plants), fire (ether), sudden cardiac events
(chloroform). Socially, an insensible patient is indistinguishable to an
onlooker from death or possession; use only with primed witnesses.

**Confidence: HIGH** on plant pharmacology and its dangers. **HIGH** on
ether/chloroform chemistry, textbook. **MEDIUM** on the "two minutes"
figure, a rough historical characterisation.

---

### surgery_practice - Surgical practice (*chirurgia*)

**What Rome already does well.** Cataract couching, displacing a clouded
lens with a fine needle to restore rough vision (Celsus, *De Medicina*,
book 7, HIGH confidence this operation is described there). Trepanation,
attested archaeologically by healed skull bone around the opening, meaning
patients regularly survived it. Amputation, survivable given the
two-minute constraint above. A genuinely impressive instrument kit,
scalpels, forceps, bone levers, specula, cautery irons in bronze and iron
(the House of the Surgeon at Pompeii finds are the best-known example).

**Why you would never guess this.** The trap runs the other way, assuming
Roman surgery is primitive and needs replacing. It needs three specific
corrections on an already solid base.

**Prerequisites.** `sanitation_antisepsis`, `germ_theory`,
`anaesthesia_analgesia` for longer procedures.

**Roman-available inputs.** The existing instrument kit, unchanged.
Boiled and dried gut or flax fibre for ligature thread.

**Procedure, three upgrades.** (1) **Ligature over cautery.** Roman
surgeons already tie off vessels (Celsus describes it), but cautery
dominates because an untreated ligature thread is itself an infection
source, making cautery's crude sterilising side-effect seem safer. Once
`sanitation_antisepsis` exists, boiled, wine-soaked ligature thread
removes that downside; ligature preserves tissue cautery destroys and
causes far less pain and scarring. (2) **Better haemostasis before
tying**: grip the bleeding vessel with forceps under direct sight before
tying, a technique refinement using the existing kit. (3)
**Post-operative care under the antisepsis regime**: clean dressings
changed not reused, fever read as a warning sign rather than healthy
draining, adequate food and fluids during recovery.

**How you know it worked.** Compare post-operative infection and death
between ligature-plus-antisepsis and cautery-plus-old-practice on
comparable wounds, the same controlled-comparison method as `germ_theory`.

**Failure modes.** A ligature tied with dirty thread in an unclean wound
reintroduces the exact risk cautery accidentally avoided; the upgrade
only works as a package with sanitation. Trained cautery habits reassert
under time pressure unless practised deliberately.

**Cost & labour.** ESTIMATED, low material cost (existing kit, cheap
ligature thread); the cost is retraining time for surgeons already
skilled in cautery.

**Danger.** Ordinary surgical risk, reduced not increased by these
changes. Socially easier than `germ_theory`, a smaller claim, easily won
on visible results.

**Confidence: HIGH.** Roman surgical competence and instrument kit are
well attested; the upgrades are textbook with a well-understood mechanism.

---

### pharmacology_first_tier - First-tier pharmacology: willow, foxglove, and opium, and why quinine is out of reach

**Willow bark to aspirin.** (1) **Decoction**: boil willow bark (*salix*,
common across the Empire) in water; real pain and fever relief, no
chemistry needed, use for pain attributed to earlier Greek tradition
(attributed, unverified exact Dioscorides citation but consistent with
his general coverage). (2) **Salicylic acid**: extract salicin from
concentrated bark (or meadowsweet) by repeated boiling and evaporation,
then oxidise it using `analytical_chemistry` and
`organic_reagents_first_tier` methods; stronger and more reliable than
raw decoction, but harsh on the stomach at effective doses. (3)
**Aspirin (acetylsalicylic acid)**: react salicylic acid with acetic
anhydride, itself a further downstream product of the acetic acid
chemistry in `organic_reagents_first_tier`; gentler on the stomach at an
equally effective dose, a genuine improvement, not just a new name. Flag
the acetic anhydride step as the hardest of the three.

**Digitalis, and its narrow window.** Foxglove (no Roman name, Greek and
Roman pharmacology never identified it, though the plant grows within
imperial territory) contains cardiac glycosides that genuinely strengthen
a failing heartbeat, historically the basis of a real treatment for
dropsy. The effective and toxic doses sit close together, a
well-established modern pharmacological fact, and the drug accumulates
with repeated dosing, so a dose safe yesterday can turn toxic after
several days. Toxicity signs: nausea, a yellow-green tinge or haloes
around lights (a specific, teachable warning), dangerous rhythm
disturbance. Use only with `analytical_chemistry`'s balance to weigh
dried, powdered leaf precisely, start at the smallest plausible dose,
watch the pulse every time.

**Opium standardisation.** Raw opium varies substantially in potency by
source and age. Fix: dissolve a carefully weighed quantity of dried opium
into a fixed volume of distilled spirit (`distillation_alcohol`) to make
a standard tincture, so a given volume always delivers a known dose.

**Why quinine is out of reach.** Quinine comes from cinchona bark, native
only to the Andes. Per the hard rule on New World materials, there is no
Old World substitute; malaria remains pharmacologically unsolvable here.
The only lever is prevention: draining or oiling standing water against
mosquito breeding, fine netting where affordable, both imperfect.

**How you know it worked.** Willow/salicylic acid/aspirin: fever and pain
measurably ease within an hour or two; aspirin gives the same relief with
less stomach complaint across a cohort. Digitalis: pulse becomes stronger
and more regular at a correctly titrated dose; any toxicity sign at any
dose means stop and recheck, never increase.

**Failure modes.** Poorly dried acetic anhydride gives a weak or
contaminated aspirin. Digitalis dosed by rough handfuls rather than
weighed powder is the single most dangerous mistake in this module and
will kill patients. Opium tincture from old, damp opium gives a
weaker-than-labelled dose, tempting a dangerous overcorrection when a
fresher batch is later used at the same volume.

**Cost & labour.** ESTIMATED. Willow decoction nearly free; salicylic
acid and aspirin inherit the organic chemistry chain's cost; digitalis is
cheap in material but requires the analytical balance, not optional here.

**Danger.** Digitalis is the standout danger in this module outside
surgery: a small error is fatal, and early toxicity can be mistaken for
worsening illness, tempting a dose increase that is exactly backwards.
Treat it as a poison that is also a medicine.

**Confidence: HIGH** throughout: the organic chemistry, digitalis's
pharmacology and narrow window, and quinine's total unavailability are
all well established.

---

### nutrition_deficiency - Deficiency diseases and their cheap fixes

**Scurvy** (vitamin C deficiency; present as "gum and joint wasting cured
by fresh green food"). Rome's ordinary diet, with regular vegetables and
fruit including citron (already known), makes population-wide scurvy
unlikely in settled populations. Real risk on long voyages or in besieged
garrisons cut off from fresh food, a well-attested later seafaring
pattern, no Roman-specific incidence figure available. Fix: any regular
fresh vegetable or fruit ration; fermented cabbage keeps its vitamin
content far longer than fresh produce for long voyages.

**Rickets** (vitamin D deficiency, too little sunlight; present as "bowed,
weakened bones in children kept from the sun"). Plausible in dense
Roman insula housing with narrow, sun-starved streets, with some
suggestive bioarchaeological evidence in less sunny provinces such as
Britain, but scale is uncertain, flagged attributed/unverified. Fix:
regular sunlight for children, fatty fish where available.

**Beriberi** (thiamine deficiency, from over-refined grain). Historically
tied to populations relying on heavily polished rice; unlikely to be a
major Roman problem given a wheat and barley staple, generally
stone-milled and retaining more of the grain than later industrial
rice-polishing. Flagged as probably not significant, with real
uncertainty.

**Iodine deficiency and goitre** (visible neck swelling from a starved
thyroid). Genuinely and directly attested in antiquity, particularly
inland and mountainous regions far from seafood, such as parts of the
Alps; ancient physicians describe and treat such swellings. Fix: seafood,
sea salt, or seaweed for inland populations, cheap and reliable once the
link is understood.

**How you know it worked.** Scurvy: gum bleeding and joint pain resolve
within days to weeks of fresh food restored. Rickets: slower, watch for
fewer new cases in sun-exposed cohorts over months rather than fast
reversal. Goitre: swelling recedes over weeks to months on regular iodine
intake.

**Failure modes.** Treating any vague "poor diet" complaint as one of
these without checking the specific presentation misapplies the fix.
Reworking milling practice against beriberi risk is very likely wasted
effort given the uncertainty above.

**Cost & labour.** ESTIMATED, low throughout: observation-and-diet
corrections, not manufactured treatments.

**Danger.** Minimal directly; the main risk is misdiagnosis against a
germ-caused illness, delaying the correct response.

**Confidence: MEDIUM** on scurvy's risk pattern and fix (mechanism solid,
Roman incidence uncertain). **LOW** on rickets' Roman-era scale. **LOW**,
leaning "probably not applicable," on beriberi. **HIGH** on iodine
deficiency and goitre, both the antiquity attestation and the fix.

---

### microscopy_biology - Microscopy and the beginnings of biology

**What it is / why you want it.** What the bead microscope shows the
first time you use it, and the research programme it opens, independent
of the germ-theory demonstration above.

**Why you would never guess this.** A small glass bead, indistinguishable
from jewellery, resolves a genuinely new tier of the world; this was,
historically, discovered by one amateur with exactly this equipment and
no institutional backing (Antonie van Leeuwenhoek, 17th century,
attributed, well documented, cited only as proof the equipment level
suffices, not as a Roman event).

**Prerequisites.** `glass_bead_microscope`.

**Roman-available inputs.** Pond and ditch water, blood (from any wound
or routine bloodletting), semen, thin cork or plant-stem slices, all
freely available.

**Procedure, easiest first.** (1) **Cork or plant stem**, sliced thin:
shows a regular honeycomb of walled compartments, cell walls, the easiest
first observation, subject dead and motionless. (2) **Blood**, thinly
smeared: disc-shaped bodies filling the field, red blood cells. (3)
**Pond water**, especially stood a few days: moving, shape-changing
bodies, protozoa. (4) **Semen**, fresh, thinly mounted: large numbers of
small bodies with active whip-tails, motile, striking. (5)
**Bacteria, at the limit**: in putrefying matter or dental scrapings,
faint moving rods visible at the edge of a good bead's resolution, the
hardest of the five and needing a patient, practised eye.

**How you know it worked.** Each category has a distinct, describable
appearance; reliable, repeated identification by a trained observer on
fresh samples confirms both instrument and technique.

**The research programme that follows.** Compare healthy versus diseased
tissue or fluid side by side; classify moving bodies by size, shape, and
movement; run transfer experiments, introducing sick material into a
healthy subject and watching whether the same appearance and illness
follow, the direct experimental bridge to `germ_theory`. Longer term,
this motivates `microscope_compound`
(30_glass_optics.md#microscope_compound), a much later item resolving
finer structure than any single bead.

**Failure modes.** A dirty or poorly ground bead gives a useless blur
mistaken for "nothing to see." Overclaiming fine structure at the
resolution limit damages credibility; be conservative about what you
actually saw.

**Cost & labour.** ESTIMATED, low: the instrument is costed under
`glass_bead_microscope` in 30_glass_optics.md; ongoing cost here is only
observer time.

**Danger.** Minimal. Main risk is social overreach, claiming more
certainty from a hazy image than a hostile Galenist audience will accept.

**Confidence: HIGH.** Simple single-lens microscopy at this level is
extremely well documented (Leeuwenhoek's surviving letters and
specimens), and every observation above is genuine and repeatable at
these magnifications.

---

### antibiotics_note - Antibiotics: why they are not the priority

**Penicillin.** Needs, in rough order: a mould that yields usefully (the
original strain was a poor producer), a deliberate strain-hunting
programme for a substantially higher-yield strain, further improvement by
mutation and selection, large aerated deep-tank fermentation rather than
shallow surface culture, an industrial-scale nutrient medium, and
chromatographic or solvent-extraction purification into a stable, dosable
product. Every step needs infrastructure and microbiological
understanding far beyond this module's reach before either plague
arrives; a very late item in the overall programme.

**Sulfonamides.** Come out of the coal-tar synthetic dye industry
(historically, Prontosil, from azo dye research in the 1930s), needing a
mature `destructive_distillation` of coal for tar, isolation of aniline
compounds, and diazotization/azo-coupling chemistry on top. A real
prerequisite chain, later than the willow-bark chemistry in
`pharmacology_first_tier` but well earlier than penicillin's fermentation
demands.

**The bottom line.** Sanitation, clean water, and isolation deliver most
of the achievable mortality reduction for a small fraction of either
antibiotic class's effort; a strategic characterisation, not a measured
ratio, but not a controversial direction. Do not delay
`sanitation_antisepsis` or `quarantine_publichealth` to chase antibiotics.
Sulfonamides are a reasonable mid-programme goal once coal-tar chemistry
exists for other reasons; penicillin is a long-term aspiration, not a
plague-preparedness item.

**Cost & labour.** ESTIMATED; penicillin's cost is out of scope here
since its prerequisite chain (fermentation, strain selection,
chromatography) is not yet specified anywhere in this document.

**Danger.** None from this decision itself; the danger is opportunity
cost, chasing this too early at the expense of the cheap interventions
above.

**Confidence: HIGH.** The historical difficulty and sequencing of
penicillin versus sulfonamides is well documented, and the direction of
the sanitation comparison is not controversial in the history of public
health.

---

### obstetrics_maternal - Obstetric handwashing and maternal mortality (building on Soranus of Ephesus's existing gynaecological tradition)

**What it is / why you want it.** One nearly free habit, already implied
by `germ_theory`: clean hands specifically before any internal
examination or delivery, which historically produced a dramatic fall in
deaths from childbed fever.

**Why you would never guess this.** The historical discovery (Ignaz
Semmelweis, Vienna, 1847) came from a grim observation: doctors moving
directly from autopsies to labouring women had far higher death rates
than midwives who never touched a cadaver. The mechanism, invisible
material carried on unwashed hands, is exactly `germ_theory`'s mechanism
applied to childbirth, historically one of the largest preventable causes
of death for young women.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`.

**Roman-available inputs.** Water, wine, eventually distilled spirit, no
new material.

**Procedure.** Anyone about to examine or assist a labouring woman
internally washes hands thoroughly in hot water then wine or spirit
immediately beforehand, especially after handling a wound, corpse, or
other sick patient; instruments cleaned the same way as under
`sanitation_antisepsis`.

**How you know it worked.** Compare maternal fever and death rates
between attendants who follow this and those who do not, across a large
enough number of births, the same controlled-comparison method used
throughout.

**On the scale of the benefit, honestly.** Semmelweis's own ward saw
maternal mortality fall from commonly cited figures around 18 in 100
births to roughly 1-2 in 100, MEASURED from that specific 19th-century
hospital record, not a Roman number, and his high starting figure was
driven by a teaching hospital's frequent autopsy-to-delivery traffic, a
pattern less exactly replicated in Roman domestic midwifery. Expect a
real, probably large reduction here too, since the underlying mechanism
is the same, but treat the specific percentage as ESTIMATED for your
context, not a number to promise a patron in advance.

**Failure modes.** Washing once at the start of a shift rather than before
each new patient misses the point, the risk is in each transfer event.
Midwives who already avoid the dead may see little benefit from this
framing and need a different comparison (between labouring patients, or
after soiled linens) to see the value.

**Cost & labour.** ESTIMATED, effectively free: water, wine or spirit,
and the habit itself.

**Danger.** Minimal physically. Socially delicate, implying an
experienced midwife's existing practice contributed to deaths; present as
an addition, let the comparison data make the case.

**Confidence: HIGH** on mechanism and qualitative result (extremely well
documented). **MEDIUM** on the exact historical percentages, which vary
between sources and are a 19th-century Viennese figure, not a Roman one.

---

### veterinary_and_agriculture_link - Animal disease, draught power, and food supply

**What it is / why you want it.** The same germ theory, sanitation, and
isolation principles applied to livestock, because draught power (oxen,
mules, horses) and much of the food supply (dairy, meat) depend on herd
health; an epizootic cripples agriculture and transport as thoroughly as
a human epidemic cripples population.

**Why you would never guess this.** Easy to treat this module as entirely
about humans; in an economy where nearly all cartage, ploughing, and
milling power comes from animals, a herd-wide outbreak is a transport and
food crisis of the same character, just less visible to a physician
focused only on people.

**Prerequisites.** `germ_theory`, `sanitation_antisepsis`; builds on
existing Roman veterinary knowledge (Columella, *De Re Rustica*, a real
and citable authority).

**Roman-available inputs.** Existing husbandry practice per Columella;
the same clean water, isolation, and wound care principles as the
human-focused entries, applied to a stable or byre.

**Procedure.** Do not share water troughs or feed between sick and
healthy animals; isolate the sick. Clean working-animal wounds (harness
sores, plough injuries) the way human wounds are cleaned, not left to
fester. Maintain standing surveillance of dairy herds for pustular udder
lesions, serving both herd protection and the `vaccination_cowpox` search.
Keep separate tools and attendants between sick and healthy groups where
practical, to avoid carrying infection the way a human attendant would.

**How you know it worked.** Fewer working animals lost or lamed to
untreated wound infection over a season; fewer secondary herd cases after
isolating a first sick animal, compared to an unisolated herd.

**Failure modes.** Treating animal husbandry as entirely separate from
the human-health programme, so attendants move freely between sick
animals and human patients without the handwashing discipline
established elsewhere, reintroduces the transmission risk the rest of the
module removes.

**Cost & labour.** ESTIMATED, low: mostly labourer time for basic
separation and cleaning, at the same wage-rate basis used throughout
(labourer 0.075 den/hr).

**Danger.** Minimal directly. The strategic risk of ignoring this entry
is losing draught animals to a preventable epizootic at the same moment a
human epidemic strains your labour force, a compounding crisis.

**Confidence: HIGH** on the mechanism and Columella's citability.
**MEDIUM** on how readily herdsmen accept isolation that reduces a sick
animal's short-term economic use without a demonstrated track record.

---

## The plague timetable

**165-180 AD, the Antonine Plague.** From 100 AD you have roughly
sixty-five years. This module's own dependency chain, per
rome/data/tech_tree.json, runs `school_founded` (a stated four-year
floor) before `germ_theory` (a further two years, itself gated on
`glass_bead_microscope`) before `plague_preparedness` (a further four
years). Summed naively, DERIVED from the tree's own `yrs` fields, that is
a floor near a decade, before counting the time to found the school or
train its staff. The practical implication: start the whole chain,
school founding included, within your first decade in-country, or you
race an unfinished programme against an epidemic. Use the remaining
decades for two things: field-testing variolation against whatever pox or
measles-like cases actually appear in the interim, since you will not
know for certain whether the Antonine Plague is smallpox or measles until
you can observe its actual presentation; and, more important given that
uncertainty, extending `quarantine_publichealth` and
`sanitation_antisepsis` as broadly as your influence reaches, since these
work regardless of the pathogen. Do not wait for certainty before
building the pathogen-agnostic layer.

**249-262 AD, the Plague of Cyprian.** From 165 AD you have roughly eighty
more years, and you personally will almost certainly not be alive to
manage it if you arrived as an adult in 100 AD; this must be a
transmitted institution by 249 AD, not personal knowledge, which is
exactly why `school_founded` and durable written tradition matter as much
as any single technique. This plague's identity is, if anything, less
certain than the first; ancient accounts are fragmentary and modern
historians offer several candidates without consensus, and no confident
attribution is offered here beyond flagging that uncertainty. Spend the
eighty-year gap widening the reach of the first plague's institutions
rather than inventing new ones: train more physicians and magistrates,
embed the practice in already-trusted bodies (legions, healing temples
such as those of Asclepius/Aesculapius, professional collegia) so it
survives leadership change, and budget seriously for the real bottleneck
that Rome has no printing and no paper, so every copy of a protocol is a
scribe's labour on papyrus or parchment; a protocol in one copy in one
city is not actually institutionalised.

---

## How not to be executed for this

Physicians already occupy a recognised, often Greek or freedman social
slot in Rome, and later imperial law recognises certain immunities from
civic burdens for practising physicians alongside teachers and
philosophers (attributed, unverified for an exact citation, but broadly
consistent with the standard picture of the profession's legal standing).
That status is an asset, and also exactly what makes reliably curing
people where established physicians fail dangerous: unusual success is a
recognised route to an accusation of poisoning or sorcery (*veneficium*),
not merely professional envy. Tactics:

1. **Operate under a powerful patron before you need one.** A foreign
physician with no patron performing strange, effective treatments reads
as a threat; the same person as a senator's or governor's client
physician reads as known and vouched-for. Secure this before your first
controversial demonstration.

2. **Speak in existing vocabulary while changing the content.** Describe
`germ_theory`'s invisible agents using Varro's own phrase, "seeds of
disease" (*semina morbi*), completing an existing Roman intellectual
thread rather than importing foreign ideas.

3. **Never claim, or appear to claim, perfect success.** Let some
patients die visibly and openly. A physician who loses patients is a
physician; one who never does is, uncomfortably fast, a suspected
poisoner, especially if a rival's patient dies while yours thrive. Keep
your failure rate visible.

4. **Control the venue for anything uncanny.** A moving speck under a
bead microscope, a patient rendered insensible by ether, a deliberate
mild dose of a lethal disease, all read to an unprimed crowd as
*maleficium*. Demonstrate first privately, for briefed witnesses who
already trust you, and go public only with a track record they can vouch
for.

5. **Get licensed through existing structures, and stay inside them.** A
recognised collegium membership gives an institutional face and a body
that can vouch for you if accused.

6. **De-risk dangerous demonstrations on low-political-consequence
volunteers first.** This is how the historical 18th-century inoculation
programmes actually de-risked variolation, testing condemned prisoners
under royal permission before extending it to a royal family (attributed,
the actual sequence in the Lady Mary Wortley Montagu/Caroline of Ansbach
era, an English precedent, not Roman, cited only as sound strategy).
Build your Roman track record on informed, consenting volunteers of
modest standing before inoculating, operating on, or anaesthetising
anyone politically important. A single dramatic public failure involving
someone well connected is the most dangerous event in this module.

---

## Sources and confidence

**High confidence, primary sources you can build on.** Celsus, *De
Medicina*, for Roman surgical technique, instruments, cataract couching,
and vessel ligation. Dioscorides, for willow, opium poppy, mandrake, and
henbane, all genuine entries in his surviving materia medica. Frontinus,
*De Aquaeductu*, for the water supply under `sanitation_antisepsis`.
Columella, *De Re Rustica*, for existing husbandry underlying
`veterinary_and_agriculture_link`. Soranus of Ephesus, a genuine,
roughly contemporary (Trajanic/Hadrianic-era) gynaecological source to
build `obstetrics_maternal` on, though specific passages are not cited
here. Galen's dominance of the profession, and humoral theory as the
obstacle `germ_theory` must overcome, are well attested, though specific
claims about what Galen wrote of the Antonine Plague itself are flagged
below.

**Flagged, lower confidence, or attributed-and-unverified.** Varro's
exact wording on invisible disease-causing creatures (*De Re Rustica*
1.12.2), the general concept a standard citation, precise Latin
unverified here. The precise identity of both the Antonine Plague and the
Plague of Cyprian, genuinely disputed among modern historians, flagged
explicitly wherever it matters for planning. The variolation and
Semmelweis mortality percentages, real historical figures from documented
programmes, but from later centuries and different societies, transposed
here as the best available evidence rather than Roman measurements. The
exact legal citation for physicians' civic immunities, the general fact
well established, the precise juristic passage unverified. Roman-era
incidence of rickets and beriberi, flagged LOW and MEDIUM respectively
under `nutrition_deficiency`, genuine uncertainty. Any cost, labour, or
calendar figure not drawn directly from rome/data/tech_tree.json is
marked ESTIMATED against the wage-rate basis in rome/data/prices.json and
should be read as a shape, not a guarantee.
