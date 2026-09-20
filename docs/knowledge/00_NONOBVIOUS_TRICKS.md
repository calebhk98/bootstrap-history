# 00 - The Non-Obvious Tricks Index

*The single most important file in this guide.*

A competent modern adult knows roughly what a microscope, a battery and a steam
engine **are**. Almost nobody knows the **specific physical trick** that makes
each one buildable with pre-industrial means. That gap is what kills bootstrap
plans: you know the destination and not the door.

This file is the list of doors. Each entry states the trick in one paragraph,
what it saves you, and where the full recipe lives.

Format: **TRICK - the kernel.** *(Saves: X)* → `module#anchor`

---

## Tier 0 - Free. Do these in the first year. They cost hours, not denarii.

**1. A single glass bead is a 200x microscope.**
Not a compound microscope. One tiny sphere. Draw a glass fibre in a flame, melt
its tip into a bead 1-2 mm across, mount it in a pinhole between two metal
plates, put the specimen on a needle right behind it, and hold the whole plate
against your eyeball in bright light. Magnification is roughly 250 mm divided by
the focal length, and a sphere's focal length is roughly its radius times
n/(2(n-1)), which for ordinary glass is about the radius. A 1 mm bead therefore
gives on the order of 250x. Van Leeuwenhoek beat every compound microscope in
Europe with this for fifty years. **Rome can do this in a week and see bacteria.**
*(Saves: ~200 years of optics, and it is the observational basis for germ theory)*
→ `30_glass_optics.md#glass_bead_microscope`

**2. Three plates, rubbed in rotation, make a true plane out of nothing.**
Two surfaces lapped together converge on a matched sphere-and-socket, not a
plane. **Three** surfaces, lapped A-B, B-C, then A-C, repeatedly, can only
converge on flat, because a sphere cannot mate with itself in all three
pairings. From one true plane you derive the straightedge, the square, the
gauge, the master screw, the lead screw, the micrometer, the bored cylinder,
and thence every machine. This needs iron, abrasive and patience, all of which
Rome has in abundance. **Every dimension of precision engineering descends from
this one trick and it requires no pre-existing reference standard.**
*(Saves: the entire measurement bootstrap problem)*
→ `40_power_precision.md#precision_three_plate`

**3. Roman *nitrum* is NOT saltpetre.** It is sodium carbonate (natron). There
is no potassium nitrate anywhere in the Roman economy. You must farm it in
nitre beds: dung, straw, wood ash, lime and urine, layered, kept damp and
turned, for 12-24 months. Then leach with water and boil the leachate with
wood-ash potash so that calcium nitrate is converted to potassium nitrate,
which is what actually works in powder. **Start the beds in your first month.
They are the longest lead-time item in the entire tree and everything in
energetic and nitrogen chemistry waits on them.**
*(Saves: 2 years of dead-end searching, which is what happens to everyone who
assumes nitrum is nitre)*
→ `20_chemistry.md#saltpetre_nitre_beds`

**4. Zinc escapes up the chimney because it boils below its own reduction
temperature.** Calamine plus charcoal reduces to zinc at around 1000 C, but zinc
boils at 907 C, so the metal leaves as vapour and immediately re-oxidises in the
furnace mouth. That is exactly why Rome makes brass by cementation without ever
seeing the metal. The fix is a **sealed retort with a downward condenser**
(distillation *per descensum*, the Indian Zawar method). **Zinc is the hidden
gate on the voltaic pile and therefore on the entire electrical age.**
*(Saves: the discovery that your electrical programme is blocked, in year 30)*
→ `10_metallurgy.md#zinc_metal`

**5. Galena straight out of a lead mine is a working semiconductor.**
A cleaved crystal of lead sulfide touched with a fine springy wire is a
point-contact rectifier. It needs no purification, no doping, no vacuum, no
theory, and no good battery. **Rome can build a working semiconductor diode within about five years of
arrival**, which is what the tech tree's serial floor for `galena_detector`
actually works out to. You do not need the voltaic pile for it: a crude copper
and iron cell in brine gives half a volt, which is plenty to bias a crystal and
move a compass needle. It is
also the detector for the first radio receiver and the cheapest possible
demonstration that rectification is real, which is the seed of everything in
Module 50.
*(Saves: nothing on the critical path, but it is the proof-of-concept that
justifies the whole 200-year programme to a sceptical patron)*
→ `55_semiconductors.md#galena_detector`

**6. Zero, positional notation and symbolic algebra cost you nothing.**
Roman numerals make multiplication a specialist skill. You carry decimal
positional notation, zero, negative numbers, decimal fractions, the equals sign,
algebraic symbolism, logarithms and calculus in your head. Teaching them costs
teaching hours and multiplies the productivity of every future person in your
programme. **Highest return-on-hours item in this entire document.** Publish
under a "recovered from Indian and Chaldean sources" frame.
*(Saves: incalculable; treat as a permanent multiplier on all research)*
→ `60_mathematics_method.md`

**7. Boiling water, washing hands and quarantine.**
No apparatus. Costs an argument, not a denarius. Will save more Roman lives than
every machine here combined, and, selfishly, it is what keeps your workshop
staffed through the Antonine Plague of 165 AD.
*(Saves: your institution)*
→ `70_medicine_biology.md`

**8. Smallpox variolation.** Scratch material from a mild pustule into the skin.
Attested in practice long before Jenner, mortality roughly 1-2% versus roughly
30% for natural smallpox. **[B]** You know the Antonine Plague is coming in 165 AD.
→ `70_medicine_biology.md`

**9. The worm condenser is the invention, not the still.**
Alexandrian alchemists already have alembics. What they lack is a long coiled
tube immersed in a tub of cold running water. That one part is the difference
between a trickle of weak distillate and industrial fractionation. Everything
from perfume to alcohol to nitric acid to petrochemistry runs through it.
→ `20_chemistry.md#distillation_fractional`

**10. The drawplate.** A hardened plate with a graded row of tapered holes.
Anneal, lubricate with tallow, pull the wire through progressively smaller
holes. Rome makes wire by cutting strip and swaging it, which is slow and gives
short lengths. You will need tens of kilometres of round copper wire for a
single dynamo. Make the drawplate in year one.
→ `10_metallurgy.md#wire_drawing`

**11. Corning gunpowder.** Dry-mixed powder is nearly useless; the components
separate in transport and it burns slowly. Wet the mix into a cake, press it,
break it into grains, and sieve. Corned powder is several times more powerful.
The 75/15/10 ratio is worthless without this step. *(Also: read the political
warning before you build any of it.)*
→ `20_chemistry.md#gunpowder`

**12. Publish, print and disperse.**
Rag paper plus a screw press plus movable type is cheap and within ten years'
reach. Rome already has the screw press. Hundreds of dispersed copies of your
corpus are the only thing that survives the Third Century Crisis. The Library of
Alexandria's lesson is that **single copies burn**.
→ `80_information_printing.md`

---

## Tier 1 - Cheap, and they unblock whole branches

**13. Charcoal-fired air is the limit, so blow harder, not hotter.**
A hand bellows tops out around 1200 C. A water-wheel-driven double-acting
bellows on a tall shaft furnace with a limestone flux takes you past 1300 C and
into **liquid cast iron**, which Rome has never seen and China has had for five
centuries. This single change turns Rome's bloomery iron industry into a
foundry industry.
→ `10_metallurgy.md#blast_furnace_cast_iron`

**14. Green vitriol, roasted in a retort, gives you sulfuric acid.**
Iron sulfate is lying in heaps at every pyrite mine as a weathering product.
Dry-distil it and you get sulfur trioxide and water, which condense as oil of
vitriol. Sulfuric acid then makes nitric acid (with saltpetre) and hydrochloric
acid (with salt), and those three make everything else.
→ `20_chemistry.md#sulfuric_acid_retort`

**15. Lead is the only material that survives hot sulfuric acid.**
Which is why the industrial process is called the *lead chamber* process. Rome
has more cheap lead than it knows what to do with.
→ `20_chemistry.md#lead_chamber`

**16. Manganese dioxide is glassmaker's soap.** Rome already knows this. What
Rome does not know is *why*, or how to control the dose. Understanding it as a
redox couple lets you make deliberately water-clear glass to a specification
instead of by luck, which is the precondition for lenses.
→ `30_glass_optics.md#glass_clear_cristallo`

**17. Tuscany's fumaroles emit boric acid.** Larderello. If this is workable,
you get borosilicate glassware, which does not crack when you heat it, which is
the difference between a laboratory and a pile of broken retorts. Verify on
arrival. **[C]**
→ `30_glass_optics.md#glass_borosilicate`

**18. A mercury barometer is also a vacuum.** The empty space above the mercury
column is the first hard vacuum any human has ever had, and it is free. Rome
mines mercury at Almadén.
→ `30_glass_optics.md#thermometer`

**19. The Sprengel pump: high vacuum with no machining at all.**
Drops of mercury falling down a narrow glass tube each trap a slug of gas and
carry it out. No pistons, no seals, no tolerances. It reaches pressures good
enough for incandescent lamps and discharge tubes, using nothing but glass
tubing and mercury. **This is the single cheapest route from "Rome" to "vacuum
physics" and it skips the entire precision-machining prerequisite.**
→ `55_semiconductors.md#vacuum_pumps`

**20. Fixed points make thermometry, and thermometry makes chemistry
reproducible.** Melting ice and boiling water. Without a repeatable temperature
scale, no recipe in this guide can be transmitted to anyone who is not standing
next to you.
→ `30_glass_optics.md#thermometer`

**21. The analytical balance is the instrument that turns alchemy into
chemistry.** One milligram resolution, agate knife edges, a draught shield.
Without it, nothing is quantitative and nothing is reproducible.
→ `30_glass_optics.md#balance_analytical`

**22. The spectroscope tells you what something is made of, from its light
alone.** A prism, a slit and a small telescope. It is the cheapest analytical
instrument with the highest information yield, and it is how you will later
verify that your germanium is actually germanium.
→ `30_glass_optics.md#spectroscope`

**23. A tangent galvanometer defines electrical units from geometry alone.**
A coil of known radius and turn count, a compass needle at its centre, and the
Earth's field. You get absolute current measurement with no calibrated
instrument to start from. This solves the electrical metrology bootstrap.
→ `50_electricity.md#galvanometer`

**24. Self-excitation solves the dynamo chicken-and-egg.** You need a magnetic
field to generate current, and an electromagnet needs current. Residual
magnetism in the iron core is enough to start it, and it builds up. Nobody
guesses this; everybody assumes you need permanent magnets.
→ `50_electricity.md#dynamo_motor`

**25. You have no rubber. Insulate with silk, oiled linen and shellac.**
There is no natural rubber and no gutta percha in the Old World until the
Americas open. Wire insulation is a genuine blocker and the answers are silk
wrapping, linseed-oil varnish, shellac imported via the Indian trade, and
bitumen for cables.
→ `50_electricity.md#wire_insulation`

**26. Wilkinson's boring mill, not the idea of steam, is what gates the steam
engine.** Newcomen and Watt both had the concept long before anyone could bore
a cylinder round and straight enough to hold a piston. Precision precedes power.
→ `40_power_precision.md#boring_mill`

**27. The flywheel is what makes an intermittent machine useful,** and the
crank-and-connecting-rod is what converts rotation to reciprocation. Rome has
neither at scale and both are one afternoon's work for a carpenter.
→ `40_power_precision.md#crank_connecting_rod`

---

## Tier 2 - The endgame kernels

**28. Zone refining: a travelling molten band sweeps impurities to one end.**
Most impurities are more soluble in liquid than in solid, so a narrow molten
zone dragged repeatedly along an ingot carries them along with it. Repeat and
you reach purities of one part in ten billion, which is otherwise unreachable by
any chemical method. **This is the specific trick that makes semiconductors
possible at all**, and it needs only a tube furnace, a quartz or graphite boat,
an inert atmosphere and a way to move a heater slowly.
→ `55_semiconductors.md#zone_refining`

**29. Germanium tetrachloride boils at about 86 C.** That is the door.
Germanium is a nightmare to purify as a metal or an oxide and trivially easy as
a volatile chloride you can fractionally distil like brandy. Convert oxide to
chloride, distil it many times, hydrolyse back to the oxide, reduce with
hydrogen. Chemical purity first, then zone refining for the last few orders of
magnitude.
→ `55_semiconductors.md#germanium_sourcing`

**30. Germanium hides in zinc smelter flue dust and in coal ash.**
It is 1.6 ppm in the crust and essentially never occurs as its own ore in
reachable quantity. The realistic route is: build a zinc industry, then collect
the dust from the flues. **This is the second reason zinc metal is on the
critical path.**
→ `55_semiconductors.md#germanium_sourcing`

**31. You already know the answer to solid state physics.**
Band structure, doping, majority and minority carriers, the p-n junction and
minority carrier injection took forty years and several Nobel prizes to work
out. You carry the conclusions. This is the largest single time saving in the
whole programme, worth more than any tool, and it costs nothing but the
teaching. **Write it down in the first decade, before you can possibly test it,
because you may not live to teach it twice.**
→ `55_semiconductors.md#semiconductor_theory`

**32. Germanium before silicon.** Silicon is everywhere and germanium is rare,
and germanium is still the right first target: it melts at 938 C rather than
1414 C, its chloride distils at a convenient temperature, and its oxide is water
soluble, which makes separation easy. History did germanium first for exactly
these reasons and a bootstrap should too.
→ `55_semiconductors.md#silicon_path`

**33. Photography is not a luxury, it is an instrument.**
It is how you record spectra, measure star positions, image metal
microstructure, and eventually expose a photolithographic mask. Silver halides
on glass. Get it early and it pays for itself in data.
→ `30_glass_optics.md#camera_obscura_photography`

---

## Anti-tricks: things that look like shortcuts and probably are not

**This section is advice, not law, and the simulator does not enforce any of
it.** Every strategy file is just an ordering, `play` mode lets you start
anything whose prerequisites are met, and nothing here is blocked. If you think
chasing the steam engine in year three is right, do it and see. The model exists
to be argued with, and the list below is a prediction I could be wrong about,
not a rule.

With that said, here is what I expect to go badly and why:

- **Do not chase the steam engine early.** It is gated on boring, on boiler
  plate, and on cheap coal. Water power is abundant in Italy and Gaul and gets
  you the same shaft horsepower for a fraction of the prerequisite tree. Steam
  matters when you need power where there is no river.
- **Do not chase electricity before zinc and drawn insulated copper wire.**
  You will build a beautiful apparatus that produces nothing.
- **Do not chase aluminium.** It needs an electrical industry and cryolite.
- **Do not chase the Haber process.** 200 atmospheres and a catalyst. Nitre beds
  and, much later, the electric arc process are your nitrogen routes.
- **Do not chase antibiotics.** Penicillin needs deep-tank fermentation and
  chromatography. Antisepsis, clean water and sanitation deliver most of the
  mortality benefit for a thousandth of the effort.
- **Do not chase the internal combustion engine before petroleum refining and
  precision.** Bitumen and naphtha seeps exist in Mesopotamia, but the whole
  chain is longer than the electrical one.
- **Do not build a compound microscope before you have made a bead microscope.**
  A bad compound instrument is worse than a good single lens, which is precisely
  why van Leeuwenhoek won.
- **Do not release gunpowder casually.** Read `03_SOCIAL_POLITICS.md` first.
  It is the one item in this document with a serious chance of making the
  Third Century Crisis worse and destroying the whole programme.
