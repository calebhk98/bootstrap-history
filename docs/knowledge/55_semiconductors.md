# Module 55: Vacuum, High Purity and Semiconductors

Two points matter more than any single recipe here.

First: **a galena cat's whisker rectifier is a working semiconductor device that needs no purification at all.** Mineral lead sulfide from any lead mine, a springy scrap of wire, and the crude copper-iron brine cell from `50_electricity.md` show a current that flows one way and not the other. No furnace, no vacuum, no theory. Build it within five years. It is the proof of concept that turns a two-century plan into a funded one, because it is real and testable now.

Second: **you carry the theory, and that is worth more than any apparatus.** Band structure, doping, majority and minority carriers, the p-n junction, minority carrier injection: the real world took roughly 1900 to 1947 and several Nobel prizes to work these out. You already know the answers. Write them down (`semiconductor_theory`) in your first decade, whether or not you live to see a working transistor. You will not get to teach this twice.

The rest of this module is the two-century machine connecting those two facts: pumps, tubes, radio, germanium, zone refining, crystal pulling. Read `50_electricity.md` first; every entry below assumes its batteries, dynamo, meters and insulated wire.

---

### vacuum_pumps - Pumps and gauges for empty space (*antlia pneumatica*)

**What it is / why you want it.** Removing air from a sealed vessel, needed for discharge tubes, vacuum tubes, and zone-refining atmospheres.

**Why you would never guess this.** That falling liquid drops, with no pistons or seals, can drag gas out of a closed space is not intuitive.

**Prerequisites.** Glassblowing, clear glass, mercury (Almadén, Spain), narrow glass tubing.

**Roman-available inputs.** Mercury, blown glass tube, leather and tallow for piston seals.

**Procedure.**
1. Piston pump: brass cylinder, leather-sealed piston, leather flap valves. Reaches roughly 10 torr single-barrel, near 1 torr double-barrel with good leather; leaks limit it.
2. Sprengel mercury drop pump (1865): mercury drips down a vertical capillary tube; each falling drop seals a slug of the tube, trapping and carrying out a plug of gas from a side-arm connected to the vessel. No pistons, no seals, only glass and gravity. Reaches roughly 0.001 torr with care, thousands of drops per run, a full day for a good vacuum.

**How you know it worked.** McLeod gauge: trap a known volume of the vacuum's gas in a graduated bulb, compress it with mercury into a small capillary volume; the compression ratio gives pressure directly, readable from about 10 torr down to 0.0001 torr. Build this early; it is your only real pressure instrument.

**Failure modes.** Piston: leather cracks, seal fails. Sprengel: mercury column breaks, capillary clogs, reservoir runs dry mid-run.

**Cost & labour.** Piston pump: ESTIMATED 20 artisan-days, 200-400 denarii. Sprengel: ESTIMATED 15 artisan-days glassblowing, 5-10 kg mercury, expect 3-5 rebuilds. MEASURED: Sprengel's own pump reached vacua adequate for early discharge tubes with this exact design.

**Danger.** Mercury vapour is a cumulative neurotoxin: ventilate, never heat the mercury, rotate workers off it. Imploding evacuated glass: use a wire-mesh or leather guard.

**Confidence: HIGH** on physics and design; MEDIUM on exact torr achievable with Roman-grade glass and mercury purity.

**Getters, finishing the vacuum after sealing.** Phosphorus getter: white phosphorus (Brand's process, evaporate urine to paste, char with sand and charcoal, distil in a covered retort at red heat, collect under water), ignited electrically inside the tube just before final seal-off, burns off residual oxygen and nitrogen. Pyrophoric and severely toxic, handle only under water. Barium getter: barium metal from molten-salt electrolysis of barium chloride (`50_electricity.md`'s dynamo), evaporated onto the sealed tube's glass wall by resistive heating, scavenges gas for the tube's life; ESTIMATED a multi-year metallurgical side-project of its own, defer it, phosphorus alone suffices early on.

---

### crookes_xray_electron - Discharge tubes, X-rays and the electron (*tubus vacuus electricus*)

**What it is / why you want it.** A sealed, evacuated tube with two electrodes and a high-voltage supply shows cathode rays, and at higher voltage, X-rays. Deflecting the beam in a magnetic field is how the electron's nature is demonstrated.

**Why you would never guess this.** Nothing here is conceptually hard once you know to look; you are building the instruments, not discovering the physics, so a 30-year 19th-century research programme compresses to an engineering exercise.

**Prerequisites.** `vacuum_pumps`, `50_electricity.md` (induction coil or stepped-up dynamo, roughly 10-50 kV), glass-metal seals (see `vacuum_tube`).

**Roman-available inputs.** Blown glass bulb, platinum or iron electrodes, copper coil wire.

**Procedure.**
1. Seal two electrodes into a bulb, evacuate to roughly 0.01-0.001 torr.
2. Apply high voltage: at low pressure a beam of cathode rays runs from the negative electrode, fluorescing where it hits glass.
3. A nearby magnet bends the beam, proving charged particles.
4. Where the beam strikes a target at higher voltage (tens of kV), X-rays emit, detectable by fogging a covered photographic plate.

**How you know it worked.** Visible beam deflection under a magnet; a covered photographic plate fogs when placed near the running tube.

**Failure modes.** Vacuum too poor: diffuse glow, no beam. Too good: discharge won't strike without much higher voltage. Electrode overheats, outgasses, ruins the run.

**Cost & labour.** ESTIMATED 10 artisan-days per tube, heavy glass wastage early on. Capital: as `vacuum_pumps` plus an induction coil, ESTIMATED 300-600 denarii.

**Danger.** Publish a blunt radiation warning BEFORE any public demonstration: unshielded X-rays burn, sterilize, and cause cancer with repeated exposure. Never place any body part in the beam. Seconds of exposure only, lead shielding above roughly 20 kV, never a daily performance.

**Confidence: HIGH** on physics; MEDIUM on exact thresholds with Roman-grade coils and glass.

---

### vacuum_tube - The diode and triode (*lampas electrica*)

**What it is / why you want it.** A heated filament in vacuum emits electrons; a positive plate collects them, one-way current, a diode. A fine grid between the two, at small voltage, controls a much larger plate current: an amplifier. This turns every weak signal in the empire into something usable.

**Why you would never guess this.** Obvious once you have the electron and a decent vacuum. The hard part is entirely mechanical: a wire through glass that survives repeated heating without cracking.

**Prerequisites.** `vacuum_pumps`, `crookes_xray_electron`, `50_electricity.md`, alloy-making for seal wire.

**Roman-available inputs.** Platinum wire (filament and seals, its expansion nearly matches soda-lime and lead glass, a real property); carbonized fiber as an Edison-style alternative filament; iron or nickel sheet for the plate; fine wire for the grid.

**Procedure.**
1. Filament between two lead-in wires, heated by a small current from `50_electricity.md` to dull red-orange, hot enough to emit, not so hot it burns out.
2. Plate: a metal sheet or cylinder facing the filament, on its own lead-in, held positive.
3. Triode: a fine wire grid between filament and plate, close to the filament, on its own lead-in.
4. Glass-to-metal seal, the hard problem: platinum works but is costly at scale. Cheaper long-run answer: a nickel-iron core (roughly 42% nickel, the rest iron, an alloy whose expansion nearly matches glass) clad in copper, drawn to fine wire, what later engineers called Dumet wire. Both metals are Roman-available; expect years of trial to match platinum's seal reliability.
5. Evacuate with the Sprengel pump, finish with a phosphorus getter, seal the exhaust tip closed under vacuum.

**How you know it worked.** Diode: current flows filament-to-plate only when the plate is positive, testable on the galvanometer. Triode: a small grid voltage swing produces a large plate-current swing, that ratio is your gain.

**Failure modes.** Seal cracks on heating (mismatched expansion), tube dies. Filament burns out. Grid too close: shorts. Under-gettered: residual gas glows blue, poor performance.

**Cost & labour.** ESTIMATED 15-30 artisan-days per working tube early on, most early attempts fail at the seal. Platinum ESTIMATED 50-100 denarii/gram; a mastered Dumet-equivalent alloy drops this to ordinary metal cost.

**Danger.** Plate supplies of hundreds of volts can kill; treat as live apparatus per `50_electricity.md`.

**Confidence: MEDIUM.** Physics and design HIGH; the Dumet alloy composition and platinum-glass match are real, MEASURED facts; Roman rebuild-cycle counts are ESTIMATED.

---

### radio_spark_to_valve - From spark transmitter to the crystal set and the valve radio (*telegraphia sine filo*)

**What it is / why you want it.** Signalling without wires: a spark radiates a burst each time its gap fires; a receiver (coherer, then crystal, then valve) detects it at distance.

**Why you would never guess this.** Not obvious a spark makes waves that travel and can be tuned; the receiver side is where the galena rectifier earns its keep beyond a curiosity.

**Prerequisites.** `50_electricity.md`, `galena_detector`, insulated copper wire, later `vacuum_tube`.

**Roman-available inputs.** Insulated copper wire, an induction coil, iron filings for a coherer, galena and phosphor bronze for the detector.

**Procedure.**
1. Spark transmitter: an induction coil charges a capacitor (foil-and-mica or Leyden jar) across a spark gap wired to antenna and earth; each spark radiates a damped burst.
2. Coherer (earliest receiver): a glass tube of loose iron filings between two electrodes, drops to low resistance when radio energy hits it, must be tapped to reset after each pulse.
3. Crystal set: antenna and earth, a tuned coil (copper wire on a wood or cardboard former with a sliding or tapped selector) and capacitor in series with the galena detector (`galena_detector`), feeding a high-impedance earpiece.
4. Earpiece, the hard part: a small horseshoe magnet (lodestone, or an electromagnet from `50_electricity.md`), soft iron pole pieces wound with roughly 1,000-3,000 turns of fine insulated wire, positioned 0.2-0.5 mm from a thin iron diaphragm (roughly 0.1-0.2 mm sheet). The many turns give the thousand-ohm-plus impedance a weak crystal-detected current needs to move the diaphragm audibly.
5. Once `vacuum_tube` exists: replace spark and coherer with a valve oscillator and amplifier, continuous waves, far greater range, enough power to drive a real speaker instead of a delicate earpiece.

**How you know it worked.** A click or tone in the earpiece, or coherer deflection, coincident with a distant known spark.

**Failure modes.** Detuned coil: no signal. Poor earth: weak reception. Earpiece gap wrong: no sound, or diaphragm sticks.

**Cost & labour.** ESTIMATED 40-80 artisan-hours per receiving station. MEASURED historical spark-set range: tens of kilometres; ESTIMATED comparable or less here.

**Danger.** Social: instantaneous cross-province messages will read as sorcery; manage the reveal under direct imperial patronage to avoid a charge of magic.

**Confidence: MEDIUM.** Coherers and spark sets are well-attested; Roman-achievable ranges and wire gauges are ESTIMATED.

---

### galena_detector - The cat's whisker rectifier (*plumbago fulminans*, informal)

**What it is / why you want it.** A sharp metal point on a natural galena (lead sulfide, PbS) crystal conducts far better one way than the other. This is your no-cost entry point to real semiconductor rectification: no smelting, no doping, no vacuum, no theory.

**Why you would never guess this.** That raw, unrefined mineral touched by bent wire shows any electrical asymmetry was found essentially by accident (Braun, 1874), decades before anyone understood why.

**Prerequisites.** Mining access, `50_electricity.md`'s crude brine cell and galvanometer for demonstration only.

**Roman-available inputs.** Galena (lead ore, mined across the Empire, Britain, Spain, Sardinia). Fine springy wire: phosphor bronze best, else spring bronze, brass, or hard-drawn iron. Lead or tin for a mounting cup.

**Procedure.**
1. Select a piece with a clean, bright, metallic cleavage face, not weathered or dull. Galena cleaves along cubic planes: a gentle knife tap along a crack splits it into flat shiny faces.
2. Mount the crystal in a cup of molten lead or lead-tin alloy poured around its base, giving a low-resistance connection to the bulk.
3. Mount fine springy wire on a pivoted arm with a fine adjustment screw, letting the tip move across the face under light, consistent spring pressure, just enough for contact.
4. Hunt for a sensitive spot: touch different points, testing each for rectification. Sensitive spots are crystal defects or inclusions found only by touch and test, expect dozens of tries.
5. To demonstrate: wire the whisker contact in series with the brine cell and galvanometer. Note the deflection, reverse the cell's polarity, note it again. At a sensitive spot the reversed reading should be a tenth or less of the first. That asymmetry, from a battery a child could build, is the proof of concept.

**How you know it worked.** Galvanometer deflection several to tens of times larger one polarity than the other, at the same contact point.

**Failure modes.** Oxidized face: little or no asymmetry. Whisker too hard: crystal fractures. Vibration: whisker shifts off its sensitive spot, a known lifelong nuisance of this device.

**Cost & labour.** ESTIMATED 2-4 hours to build the mount, half a day of spot-hunting per usable detector. Materials under 20 denarii.

**Danger.** Lead exposure from raw galena and molten mounting alloy: wash hands, ventilate, keep children off raw galena dust. Present it honestly as a curiosity, not magic.

**Confidence: HIGH.** Real, MEASURED 19th-century technology (Braun, 1874), needing no purification, doping, or vacuum. The most certain entry in this module.

---

### semiconductor_theory - What to write down before you can test any of it (*doctrina de semiconductoribus*)

**What it is / why you want it.** The framework turning "some stones rectify" into deliberate engineering. Costs a scribe and paper, nothing else; the largest single time-saving in the whole programme, since the real world took roughly 1900-1947 to work it out.

**Why you would never guess this.** You would not guess it, you already know it. The task is transcription and preservation, not discovery.

**Prerequisites.** Literacy, a durable medium, multiple redundant copies in different archives.

**Roman-available inputs.** Papyrus, wax tablets, parchment codices, trusted scribes.

**Procedure, what to write.**
1. Band structure: a filled valence band and an empty conduction band, separated by a gap. Whether a material conducts depends on that gap's size. Germanium's gap is roughly 0.67 eV, silicon's roughly 1.1 eV; carry these as given facts, to confirm once instruments exist.
2. Intrinsic (pure) material conducts weakly; deliberately doping it with controlled trace impurities changes conduction by orders of magnitude, on purpose.
3. Donors and acceptors: atoms with one extra outer electron (phosphorus, arsenic, antimony) donate a spare electron, giving n-type material, majority carriers electrons. Atoms with one fewer (boron, aluminum, gallium, indium) accept one, leaving a mobile "hole", giving p-type material, majority carriers holes.
4. Majority and minority carriers: each type has a small population of the opposite carrier always present. Devices are built on what happens to that minority population.
5. The p-n junction: where n-type meets p-type, a depletion region forms with a built-in field, passing current easily one way (forward bias), blocking it the other (reverse bias), a rectifier by design, the same asymmetry the galena crystal shows by accident.
6. Minority carrier injection: forward-bias a junction hard, and it injects minority carriers into the neighbouring region in large numbers, which then diffuse before recombining.
7. Transistor action: a second junction close enough (within the diffusion range, a fraction of a millimetre in germanium) collects those diffusing carriers before recombination. A small change at the first junction controls a much larger current at the second: amplification.

**How you know it worked.** Untestable until `galena_detector`, `semiconductor_metrology` and workable germanium exist, possibly decades later. Expected, acceptable.

**Failure modes.** Loss: fire, damp, a careless copyist. Commission at least three independent copies in different cities.

**Cost & labour.** ESTIMATED 2-6 months of writing and diagrams, under 100 denarii total copying cost. The cheapest entry in this module.

**Danger.** None physical. Socially, unproven claims about invisible "carriers" will read as fantasy; keep this a sealed technical archive, not a public claim, so it does not undermine credibility on what you can demonstrate now.

**Confidence: HIGH.** Settled 20th-century physics; the only real risk is faithful transcription across centuries.

---

### germanium_sourcing - Finding germanium at all (*plumbum cinereum*, informal)

**What it is / why you want it.** Germanium is the practical bootstrap semiconductor, lower melting point and simpler chemistry than silicon, but it essentially never occurs as its own workable ore anywhere reachable.

**Why you would never guess this.** At roughly 1.6 parts per million of the crust (ESTIMATED, Winkler-era figure) it seems findable, but it is dispersed, not concentrated: there is no germanium mine to seek, you must go through someone else's ore.

**Prerequisites.** Zinc smelting or sulfide-ore roasting, or coal-ash access; later `zone_refining` and `single_crystal_growth`.

**Roman-available inputs.**
1. Sphalerite (ZnS) concentrates: germanium substitutes for zinc at roughly tens to a few hundred ppm, ESTIMATED, higher in some Spanish and Balkan zinc districts.
2. Zinc-roasting flue dust, the best realistic source: germanium volatilizes and concentrates there, historically roughly 0.1-2% by weight, ESTIMATED, far richer than raw ore. Any Roman zinc or brass-cementation operation produces it.
3. Certain coal ashes: some seams carry germanium up to several hundred ppm to over 1% in ash, ESTIMATED, location-specific, worth testing.
4. Argyrodite (Ag8GeS6), roughly 6-7% germanium, MEASURED, the mineral where germanium was first identified (Winkler, Freiberg, Saxony, 1886). Freiberg lies in free Germania, trade-reachable via the amber road and Germanic contacts, with real diplomatic friction.
5. Germanite, roughly 1-8% germanium, MEASURED, at Tsumeb, Namibia. Effectively unreachable, no Roman route runs near sub-Saharan south-west Africa; note it, do not plan around it.

**Procedure, separation chemistry.**
1. Roast the flue dust or concentrate to oxides and chlorides.
2. Treat with concentrated hydrochloric acid: germanium converts to germanium tetrachloride, GeCl4, boiling at roughly 86°C.
3. Fractionally distil: GeCl4 separates easily from zinc chloride (bp roughly 732°C) and iron chloride, but needs roughly 10-20 redistillation passes to separate from its one close interferent, arsenic trichloride (bp roughly 130°C). Same still-and-column technique as distilling any other liquid.
4. Hydrolyze the purified GeCl4 with water, precipitating germanium dioxide, GeO2, and recoverable hydrochloric acid.
5. Reduce the GeO2 with hydrogen at roughly 650°C, yielding grey metallic germanium sponge.

**Why the chloride is the door.** Germanium metal and its oxide are solids with no easy purification path, you cannot fractionate a powder. The tetrachloride is a volatile liquid you can fractionally distil exactly like separating brandy from wash, again and again, until arsenic and everything else is reduced to a trace. This one property is what makes germanium tractable at all.

**How you know it worked.** GeO2 precipitate is white and gelatinous; reduced germanium is dull grey-black, brittle, with modest conductivity on the galvanometer, well below a true metal.

**Failure modes.** Incomplete distillation leaves arsenic, poisoning later devices. Under-reduction leaves oxide mixed with metal, high-resistance lumps.

**Cost & labour.** ESTIMATED 200-400 artisan-hours per distillation batch for adequate purity. Yield from flue dust: ESTIMATED single-digit grams per large batch, a precious-metal-scale operation.

**Danger.** Hydrochloric acid and chlorine fumes are severely corrosive: work outdoors or in a well-ventilated shed. Arsenic trichloride, the main contaminant, is a lethal poison: bury residues away from water sources.

**Confidence: MEDIUM.** Chemistry (route, boiling points, reduction temperature) HIGH, MEASURED; Roman-era ore and dust concentrations ESTIMATED by analogy to later industrial sources.

---

### zone_refining - Pfann's travelling molten zone (*purgatio per zonam*, informal)

**What it is / why you want it.** A narrow molten band moved slowly along a germanium bar sweeps impurities to one end. Repeated passes reach purity no chemical method achieves. Without this, chemically purified germanium (`germanium_sourcing`) is still not clean enough for a working transistor.

**Why you would never guess this.** Most impurities dissolve more readily in molten germanium than solid germanium, so a freezing zone rejects impurity forward into the still-molten region ahead, concentrating it rather than spreading it evenly. Pfann worked this out in 1952, after the transistor already existed.

**Prerequisites.** `germanium_sourcing`, `vacuum_pumps` or an inert/hydrogen atmosphere, high-purity graphite or fused quartz vessels.

**Roman-available inputs.** Reduced germanium sponge. Fused quartz tube or high-purity graphite boat (from ash-poor charcoal). Hydrogen gas from an acid-metal generator.

**Procedure.**
1. Melt germanium (938°C) into a bar in a graphite or quartz boat.
2. Seal the boat in a quartz tube, evacuated or flushed with dry hydrogen, so the molten surface does not oxidize.
3. Heat only a narrow band, roughly 1-2 cm wide, to melting with a localized furnace or induction coil, leaving the rest solid.
4. Move that zone along the bar, ESTIMATED 5-20 cm/hour, by moving the heater or drawing the boat through it.
5. Impurities, having a segregation coefficient below one, stay preferentially in the liquid and are swept along toward one end.
6. Repeat the same-direction pass ESTIMATED 10-30 times, then cut off and discard the impurity-rich end.

**How you know it worked.** Resistivity, measured with `semiconductor_metrology`'s four-point probe along the bar, rises sharply toward the clean end after successive passes.

**Failure modes.** Ordinary clay or ceramic boats leach silicon or aluminum into the melt, defeating the purpose. Zone too fast: poor segregation. Air leak: surface oxidizes, ruining that pass.

**Cost & labour.** ESTIMATED days of continuous furnace-operator time per multi-pass run, plus quartz or graphite vessels that themselves require a mature ceramics or glass programme.

**Why no chemical method suffices.** Chemical purification gets you to roughly what a chemist can measure. Zone refining, historically, reached about one impurity atom in ten billion, MEASURED, far beyond any wet chemistry. This is not polish, it is the step that makes a working device possible; skip it and stray impurities act as uncontrolled, unwanted dopant.

**Danger.** Standard furnace burn and fire risk. Hydrogen atmosphere is explosive mixed with air: purge thoroughly, no open flame near the generator.

**Confidence: HIGH** on principle and MEASURED historical purity; MEDIUM on Roman-achievable pass counts and rates.

---

### single_crystal_growth - Pulling a single crystal from the melt (*cristallus tractus*, informal)

**What it is / why you want it.** Growing zone-refined germanium as one continuous crystal lattice, rather than many small randomly oriented grains, is what makes a working transistor possible, not chemical purity alone.

**Why you would never guess this.** Invisible internal grain boundaries destroy device function even in chemically perfect material, undetectable by ordinary chemical assay.

**Prerequisites.** `zone_refining`, `semiconductor_metrology`, precise weighing, a controlled pulling and rotation rig.

**Roman-available inputs.** Zone-refined germanium, a small oriented seed crystal (kept from earlier bars), weighed dopants (phosphorus, arsenic or antimony for n-type; boron, aluminum, or indium for p-type), a graphite or quartz crucible.

**Procedure, Czochralski method (1916, applied to germanium circa 1948-1950).**
1. Melt zone-refined germanium at 938°C in the protected atmosphere used for zone refining.
2. Add a precisely weighed dopant trace, targeting parts-per-million, requiring an analytical-grade balance.
3. Touch a small oriented seed crystal to the melt surface.
4. Withdraw it slowly, ESTIMATED 1-10 mm/minute, rotating a few to tens of rpm to average furnace temperature asymmetry.
5. Germanium freezes onto the seed in the same orientation, growing a single doped boule.

**How you know it worked.** A good boule has a smooth, unbroken lustrous surface. Sliced and probed with the four-point probe, it gives smoothly varying resistivity; a poor pull gives erratic, patchy readings.

**Why grain boundaries are fatal, not just undesirable.** A boundary between differently oriented grains is dense with broken bonds that trap and instantly recombine minority carriers, the carriers a transistor depends on surviving long enough to diffuse across a junction (`semiconductor_theory`). Carrier lifetime near a boundary can crash from microseconds to nanoseconds. This holds regardless of chemical purity: polycrystalline germanium, however many zone-refining passes, will never make a working transistor.

**Failure modes.** Pulling too fast: multiple grains or facets grow. Unstable temperature: boule necks or breaks. Dopant weighed wrong: found only at the metrology step.

**Cost & labour.** ESTIMATED weeks of operator time per successful pull, low early success rate, treat a dozen or more boules as development losses.

**Danger.** As `zone_refining`. Dopant handling: arsenic and its compounds are toxic, handle as any poison.

**Confidence: MEDIUM.** Method and grain-boundary physics HIGH, MEASURED; Roman pull rates and yields ESTIMATED.

---

### semiconductor_metrology - Measuring what you have made (*mensura resistentiae*, informal)

**What it is / why you want it.** The four-point probe and the Hall effect give resistivity, carrier type, and carrier concentration. Without these, purification and doping are blind; with them, every pass and pull becomes a measured, converging process.

**Why you would never guess this.** Using four contacts instead of two, specifically to cancel out the probe tips' own unknown contact resistance, is a non-obvious circuit trick; two contacts alone give a reading dominated by the contacts, not the material.

**Prerequisites.** `50_electricity.md` (precision galvanometer, stable current source), a small magnet, fine probe wire.

**Roman-available inputs.** Four fine, evenly spaced phosphor bronze probe tips on an insulating mount; a small horseshoe magnet (lodestone or electromagnet).

**Procedure, four-point probe.**
1. Press four collinear, evenly spaced tips (spacing s) onto the polished sample.
2. Force a known small current I through the two outer tips.
3. Measure voltage V across the two inner tips.
4. For a large sample, resistivity is roughly rho = 2 pi s V/I; smaller samples need a geometric correction found by comparing a sample of known resistivity.

**Procedure, Hall effect.**
1. Pass a steady current through a thin, regular sample.
2. Apply a magnetic field perpendicular to that current.
3. Measure the small transverse Hall voltage.
4. Its sign gives carrier type (electrons or holes); its magnitude, with known current, field, and thickness, gives carrier concentration.

**How you know it worked.** Reproducible readings on the same sample; a correctly doped, zone-refined sample matches the resistivity and type targeted when the dopant was weighed in.

**Failure modes.** Oxidized or uneven probe contact: noisy readings. Sample too small relative to spacing without the correction factor: systematic error.

**Cost & labour.** ESTIMATED a few days of instrument-maker time once `50_electricity.md`'s meters exist, cheap relative to what it saves.

**Why this closes the loop.** Every prior step (distillation passes, zone-refining passes, dopant weighing) is blind without a number coming back. Measured resistivity and carrier type turn purification from an act of faith into an engineering process that converges instead of guessing.

**Danger.** Minor, standard electrical handling.

**Confidence: HIGH.** Well-established, MEASURED techniques; achievable precision with Roman-grade meters and magnets is MEDIUM.

---

### point_contact_transistor - The first transistor (*punctum amplificans*, informal)

**What it is / why you want it.** Two fine metal points, pressed onto n-type germanium a fraction of a millimetre apart, give real gain: a small current at one point controls a much larger current at the other.

**Why you would never guess this.** Bardeen and Brattain found this in 1947 while investigating a different, failed design; even with the theory in hand the working geometry is not obvious. Having `semiconductor_theory` written in advance saves the most here: you already know to look for exactly this.

**Prerequisites.** `single_crystal_growth` (n-type germanium, ESTIMATED doped with arsenic or antimony), `semiconductor_metrology`, fine phosphor bronze wire, `50_electricity.md`.

**Roman-available inputs.** N-type single-crystal germanium slab, roughly 1 cm x 1 cm x a few mm (MEASURED, as the original device). Two phosphor bronze point contacts on an insulating wedge, spaced roughly 0.05 mm, achieved historically by razor-splitting a single foil contact into two; the same technique should work with fine bronze foil.

**Procedure.**
1. Confirm the slab is single-crystal, n-type, with `semiconductor_metrology`.
2. Mount two point contacts on the wedge, spaced ESTIMATED 0.03-0.1 mm.
3. Forming pulse: a brief high-current pulse through one contact locally converts the germanium beneath it, believed to create a thin p-type region, making that contact a small junction against the n-type bulk.
4. Bias the formed "emitter" contact forward, the nearby "collector" contact reverse, both against the n-type "base".
5. Forward bias injects minority carriers (holes) into the base; the close collector gathers most of them before they recombine.

**How you know it worked.** A small signal at the emitter produces a much larger one at the collector, on the galvanometer or an earpiece. MEASURED historical performance: roughly 18 dB power gain (factor of order 20-100), voltage gain of order 100, December 1947.

**Failure modes.** Points too far apart: no gain. Forming pulse too weak: no junction. Too strong: destroys the contact. Mechanical shock: points are jarred off their sensitive configuration, echoing `galena_detector`'s fragility, the reason the industry moved on to `junction_transistor`.

**Cost & labour.** ESTIMATED weeks of trial per working device even with all prerequisites in hand; Bardeen and Brattain's own team spent roughly a year reaching this point. `semiconductor_theory` should compress, not eliminate, this.

**Danger.** Ordinary low-voltage handling only.

**Confidence: HIGH** on physics and MEASURED historical figures (Bardeen, Brattain, Shockley, Bell Labs, 16 December 1947). MEDIUM on how long Roman hands, without micromanipulators, take to reach the needed spacing and forming control.

---

### junction_transistor - Grown and alloy junctions (*iunctio amplificans*, informal)

**What it is / why you want it.** Building junctions directly into the crystal, first grown, then alloyed, replaces fragile hand-positioned points with a rugged, reproducible, manufacturable device.

**Why you would never guess this.** A natural refinement once `point_contact_transistor` works and `semiconductor_theory` says what matters is the junction, not specifically two sharp points.

**Prerequisites.** `point_contact_transistor`, `single_crystal_growth`, `semiconductor_metrology`.

**Roman-available inputs.** N-type germanium melt or crystal, indium (p-type, alloy junctions), n- and p-type dopants in sequence (grown junctions).

**Procedure, grown junction (Teal and Sparks, 1950).**
1. Start a Czochralski pull with n-type dopant in the melt.
2. Mid-pull, add excess p-type dopant, switching the freezing crystal's type.
3. Add n-type dopant again later, switching back.
4. The boule has two junctions at known positions, sliced out afterward.

**Procedure, alloy junction (1951).**
1. Take a thin n-type wafer.
2. Place an indium pellet on each face.
3. Briefly melt the indium into the surface on each side, recrystallizing thin p-type regions as it cools, giving p-n-p with two junctions.

**Why this is far more manufacturable.** No point has to be hand-positioned to a fraction of a millimetre and held against vibration. Junction depth and spacing are set by pull timing or pellet size and melt duration, both more controllable and repeatable, giving higher yield and more consistent gain, which is why this became the standard commercial form.

**How you know it worked.** As `point_contact_transistor`: measurable gain between outer regions controlled by the middle region.

**Failure modes.** Grown junction: dopant switch not sharp, weak gain. Alloy junction: indium pellet overheated or too large, shorts the two junctions.

**Cost & labour.** ESTIMATED comparable to or less than `point_contact_transistor` once `single_crystal_growth` is established, with much higher yield.

**Danger.** As prior entries; indium is comparatively mild, handle with standard metal-handling care.

**Confidence: HIGH.** MEASURED historical devices (Teal and Sparks 1950, alloy junction 1951), straightforward extensions of prerequisite techniques.

---

### silicon_path - The alternative substrate, and why to defer it (*silex amplificans*, informal)

**What it is / why you want it.** Silicon eventually replaced germanium industrially, for good reasons, but is the wrong first target for a Roman-era bootstrap.

**Why you would never guess this.** It looks backward to choose the rarer material first; the reason is that Roman-era furnace and crucible technology struggles far more with silicon than germanium.

**Prerequisites.** Same chain as germanium, plus better refractory crucible chemistry.

**Roman-available inputs.** Silicon, roughly 27% of the crust, present in essentially all sand and clay: no sourcing problem, unlike `germanium_sourcing`.

**Honest comparison.**
1. Melting point: germanium 938°C, within reach of a water-blown charcoal furnace (roughly 1200°C hand-blown, 1500°C water-blown). Silicon melts at 1414°C, near the top of what such a furnace sustains reliably for the hours a pull requires.
2. Crucible chemistry: molten silicon attacks ordinary fused quartz far more aggressively than germanium does; a crucible surviving repeated melts without contaminating the batch is a harder materials problem.
3. Purification route: trichlorosilane, SiHCl3 (hydrogen chloride gas over heated silicon at roughly 300°C, boiling at roughly 32°C), fractionally distilled, then hydrogen-reduced at high temperature (the Siemens process). Workable, but an extra gas-handling and reduction step beyond germanium's chain.
4. Payoff: silicon's larger bandgap (roughly 1.1 eV vs germanium's roughly 0.67 eV) gives higher-temperature-tolerant devices, a real advantage for a mature industry, irrelevant to proving the concept.

**Recommendation.** Build germanium first. Lower melting point is an easier furnace problem at Roman maturity, its chemistry is precedented and simpler, and it is the historically proven first path (1947-1951). Attempt silicon only once germanium-programme furnace, crucible, and vacuum infrastructure is mature, likely decades after the first working germanium transistor.

**How you know it worked.** As `point_contact_transistor` and `junction_transistor`, on silicon instead.

**Failure modes.** Crucible contamination from silicon's aggressive high-temperature chemistry, the dominant added failure mode.

**Cost & labour.** ESTIMATED comparable per-step labour to germanium, but materially higher furnace and crucible development cost.

**Danger.** Trichlorosilane and hydrogen chloride: severely corrosive and toxic, identical precautions to `germanium_sourcing`'s chlorine chemistry.

**Confidence: MEDIUM.** Chemistry and figures HIGH, MEASURED. Which path is genuinely faster for a Roman programme specifically is ESTIMATED reasoning, since history never ran this choice under these constraints.

---

## The endgame dependency chain

1. `50_electricity.md`: batteries, dynamo, insulated wire, meters.
2. `semiconductor_theory`, written in the first decade, costs almost nothing, saves the most.
3. `galena_detector`, built within roughly five years, the proof that funds everything after.
4. Glassblowing and clear glass, matured to blow sealed, evacuated envelopes.
5. `vacuum_pumps`, piston then Sprengel, plus McLeod gauge and phosphorus getters.
6. `crookes_xray_electron`: discharge tubes as instrument-building, not discovery.
7. `vacuum_tube`: diode, then triode, needing the Dumet-equivalent alloy seal, the hardest metallurgical sub-problem in the chain.
8. `radio_spark_to_valve`: funding, prestige, and a proving ground for tuned circuits and amplifiers reused later.
9. `germanium_sourcing`: flue dust or argyrodite located and traded for, GeCl4 distillation mastered.
10. `zone_refining`: quartz or graphite vessel-making, atmosphere control, dozens of patient passes.
11. `single_crystal_growth`: precision pulling rig, weighed dopants, an analytical balance.
12. `semiconductor_metrology`: four-point probe and Hall apparatus, without which steps 9-11 are blind.
13. `point_contact_transistor`, then `junction_transistor`.
14. Optionally, decades later, `silicon_path`.

**How many trained people, ESTIMATED.** Not a handful of hands: a standing, multi-generational technical establishment. Reckon roughly 150-300 skilled specialists sustained at any time: miners and ore-sorters, glassblowers, ceramicists (fused quartz, refractories), metallurgists and alloy-smiths, acid and chlorine chemists, furnace operators, instrument makers, precision mechanics, and scribes maintaining the theory archive. Comparable in scale to a legion's engineering corps or an imperial mint, concentrated in two or three workshops under continuous patronage, with apprenticeship chains spanning the roughly two-century gap between `semiconductor_theory` (year 1-10) and `junction_transistor` (a century or more later at Roman-era development speed).

---

## Sources and confidence

MEASURED figures (Sprengel pump and McLeod gauge, Crookes/Röntgen/Thomson tube work, Bell Labs' 16 December 1947 point-contact transistor and its gain, Teal and Sparks' 1950 grown junction, the 1951 alloy junction, Pfann's 1952 zone refining and its purity, Czochralski's 1916 method, argyrodite's 1886 discovery and germanium content, germanium and silicon melting points and bandgaps, GeCl4 and SiHCl3 boiling points) come from standard solid-state physics references (in the spirit of Sze) and standard transistor histories (in the spirit of Riordan and Hoddeson). HIGH confidence.

ESTIMATED figures (Roman-achievable vacuum levels, artisan-hours, germanium concentrations in Roman-reachable ores and dusts, pass counts and pull rates with hand-built apparatus, workforce size) are reasoned extrapolations from the measured base cases, adjusted down for cruder tooling, flagged throughout. Treat each as a planning assumption, correctable by `semiconductor_metrology`'s actual readings once built, not a fact to build irreversible decisions on.

Overall confidence: MEDIUM. The science is HIGH and settled; the Roman-era engineering path is a reasoned, unverified extrapolation.
