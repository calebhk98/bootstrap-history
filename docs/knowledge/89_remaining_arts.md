# Module 89: Remaining Arts and Sciences

## Introduction

This is the leftover bin: 202 nodes spanning mathematics, medicine, finance, instruments, manufacturing, control theory and operations research, military organisation, civil engineering theory, metallurgy, and nine semiconductor-path steps (`gp_` prefix), none of which fit a single domain module. Given a hard word budget, entries below use five merged fields (what/why, kernel, needs, check/failure, cost-danger-confidence) instead of the full nine-field template used elsewhere: a deliberate compression, not a lower standard of accuracy.

Mathematics is the highest-leverage claim here: it costs papyrus and teaching hours, nothing else, and everything below touching structural or electrical calculation rides on four kernels. Positional notation with a real zero (`60_mathematics_method.md#arithmetic_positional`) makes long multiplication and division a written procedure instead of an abacus trick; Roman numerals record a finished quantity but cannot calculate. The Fourier idea, that any periodic wave is a sum of pure sine waves at different frequencies, is the most useful tool for everything acoustic and electrical downstream. Determinants, matrices, and interpolation are the working tools of structural or electrical calculation. Probability and statistics turn measurement into knowledge, the foundation under insurance, the randomised trial, and quality control, reappearing below in institutional clothes (mortality tables, medical statistics, operational research).

Many entries are institutions, not recipes, so "Roman-available inputs" and "Danger" read thin for them; that is correct. For medicine, danger is stated honestly where real. For military entries, only the dependency chain is given, no tactical detail.

---

## Civil engineering theory

### civ_statics - Statics: forces and moments in balance

**What/why.** Every force and turning moment on a structure at rest sums to zero; solving that balance at each joint (method of joints) gives every internal member force before anything is built.
**Kernel.** Archimedes already has the lever; the leap is applying vector force-and-moment balance systematically, joint by joint, across a whole frame.
**Needs.** Arithmetic, scaled force diagrams. No new material.
**Check & failure.** Last joint solved balances using only forces already found; starting at a joint with 3+ unknowns is unsolvable directly.
**Cost, danger, confidence.** DERIVED: a day, paper only. No danger. Confidence: HIGH, textbook statics.
Also covers: civ_method_joints.

### civ_bending_moment - Bending moment, shear, neutral axis, elasticity, buckling

**What/why.** Integrating load along a beam gives shear, integrating shear gives bending moment, showing exactly where a beam fails first.
**Kernel.** A beam has a neutral axis, unstressed, at its centre depth, compression on one face, tension on the other, which is why an I-beam is efficient.
**Needs.** civ_statics, elementary calculus, Young's modulus and Poisson's ratio.
**Check & failure.** A test beam loaded to predicted moment shows predicted deflection and cracks where stress is calculated highest; ignoring buckling on a slender column is the common miss.
**Cost, danger, confidence.** DERIVED: days of calculation. A test beam can drop at failure, keep clear. Confidence: HIGH, textbook.
Also covers: civ_neutral_axis, civ_elasticity_theory, civ_euler_buckling.

### civ_materials_testing - Materials testing, safety factor, soil mechanics

**What/why.** Pulling real samples to failure gives the strength and stiffness numbers a calculation needs; multiplying design load by a safety factor (2 to 5) absorbs the gap between calculation and reality.
**Kernel.** Soil is the surprise: strength depends heavily on water content and confinement, and before Terzaghi's effective-stress theory, foundation depth was guesswork.
**Needs.** civ_statics, civ_bending_moment, a calibrated loading frame or lever press.
**Check & failure.** Structures built to tested numbers survive design load with the expected margin repeatedly; testing one sample as if it represents a whole batch is the common failure.
**Cost, danger, confidence.** DERIVED: a frame is one-time capital, weeks; each test after is hours. A press under load can whip a sample. Confidence: HIGH.
Also covers: civ_factor_safety, civ_soil_mechanics.

---

## Finance, trade, and civic institutions

See `96_finance.md` for money, banking, and corporate law; these are the surrounding civic machinery.

### fin_standard_weights - Standard weights, assay office, customs house

**What/why.** A state-held reference weight, a stamped hallmark assaying precious-metal fineness, and a border customs post together let strangers trade without personally verifying every item.
**Kernel.** All three fail together if the master reference itself drifts, so it must be sealed and never used for daily trade, only to check working copies.
**Needs.** A trusted mint or treasury to hold the master standard, literate inspectors.
**Check & failure.** Merchant weights checked against the master agree; corrupt inspectors under-assessing for a bribe is the recurring failure.
**Cost, danger, confidence.** DERIVED: one-time state cost, a few officials ongoing. Social danger only: counterfeiting is a state offence. Confidence: HIGH.
Also covers: fin_assay_office, fin_customs_house.

### fin_census - Census, survey, statistics office, mortality table

**What/why.** Continuous registration of births, deaths (with age), and land, plus a baseline territorial survey and a permanent statistics office, produces the population and death numbers tax and insurance need.
**Kernel.** The mortality table is the payoff: dividing deaths in an age band by the number alive at that age's start gives the annual probability of death.
**Needs.** Literate clerks, a standard record form, several years of consistent data before the table.
**Check & failure.** The table predicts next year's deaths in a band within a small margin; undercounting the poor or mobile population skews every downstream number.
**Cost, danger, confidence.** DERIVED: a permanent clerical office, tens of scribes per province. Social danger: populations distrust being counted. Confidence: HIGH mechanics.
Also covers: fin_survey_map, fin_statistical_office, fin_mortality_table.

### fin_government - Standing bureaucracy, post office, civil service exam

**What/why.** A permanent professional administrative staff, a mail office centralising and tracking correspondence, and a competitive written exam for appointment replace patronage staffing with something that scales past one patron's lifetime.
**Kernel.** The exam is cheap (paper, examiners) and attacks incompetent placement by birth or favour directly, with no new technology required.
**Needs.** Widespread literacy among candidates, a stable syllabus, elite willingness to accept merit appointment.
**Check & failure.** Administrative errors and corruption complaints fall over years relative to patronage offices; an exam testing memorised rhetoric rather than administrative skill selects the wrong trait.
**Cost, danger, confidence.** DERIVED: examiners and paper are cheap, the cost is political. Purely social danger. Confidence: MEDIUM, elite acceptance is a real gamble.
Also covers: fin_post_office, fin_civil_service_exam.

### fin_societas - Business organisation: partnership to joint stock, exchange, guilds, unions, totalisator

**What/why.** A ladder from societas (partnership, dies with the partners, unlimited liability) to a chartered joint-stock company that outlives its founders and caps each owner's loss at their stake.
**Kernel.** Perpetual, limited-liability existence is the genuinely new idea: it is what lets strangers pool capital for a venture too large for one family.
**Needs.** Reliable courts, literacy and accounting, a grading standard for the exchange.
**Check & failure.** Shares trade at a stable published price; a joint-stock company without real oversight becomes a fraud vehicle (worthless shares sold on false promise).
**Cost, danger, confidence.** DERIVED: a charter and ledger are cheap. Social danger: collegia already draw state suspicion. Confidence: MEDIUM.
Also covers: fin_joint_stock, fin_commodity_exchange, fin_collegium, fin_guild, fin_trade_union, fin_totalisator.

### fin_professional_exam - Professional licensing and patent office

**What/why.** A competence exam before licence to practice protects the public from unqualified practitioners; a patent office examining inventions for novelty and granting a temporary monopoly in exchange for a full written disclosure.
**Kernel.** Without patent protection, secrecy is the rational choice for an inventor, so the state is deliberately buying disclosure with an enforced temporary monopoly, a bargain.
**Needs.** fin_civil_service_exam-grade testing machinery, literate technical examiners, enforceable courts.
**Check & failure.** Licensed practitioners show fewer malpractice complaints than unlicensed; licensing captured by the trade itself becomes a barrier to entry instead of a quality floor.
**Cost, danger, confidence.** DERIVED: examiners and an archive, modest cost. Social danger: excluded practitioners resent it. Confidence: MEDIUM, English patent law (1624) proves the model.
Also covers: fin_patent_office.

### fin_university - Academic and research institutions

**What/why.** A university, an endowed chair (capital whose income pays a scholar indefinitely), a learned society, a research institute freed from teaching duty, and a public museum together give scholarship a durable home.
**Kernel.** The endowment converts a one-time gift into a perpetual salary, exactly the way a joint-stock charter converts one-time investment into a perpetual company.
**Needs.** A perpetual-fund mechanism, students or scholars, buildings.
**Check & failure.** The chair, society, or museum still functions a generation after its founder's death, funded from the endowment alone; badly invested capital starves it over decades.
**Cost, danger, confidence.** DERIVED: capital scale varies, the mechanism is legal drafting only. No danger. Confidence: HIGH, Roman endowment precedent exists.
Also covers: fin_endowed_chair, fin_learned_society, fin_research_institute, fin_museum.

---

## Agricultural knowledge

### fud_agricultural_treatises - Written treatises and soil testing

**What/why.** Writing down crop rotation, fertiliser rates, and machinery designs spreads best practice beyond one estate's oral tradition; simple field tests turn fertiliser choice into a fitted response.
**Kernel.** Obvious that writing helps; less obvious that useful soil tests need no laboratory at all, only consistent observation.
**Needs.** Literacy, an existing body of practical farming knowledge (`75_agriculture_food.md`).
**Check & failure.** A farmer following the treatise on similar soil gets a comparable yield gain.
**Cost, danger, confidence.** DERIVED: writing materials and time only. No danger. Confidence: HIGH, Columella and Cato already write treatises.
Also covers: fud_soil_composition_analysis.

---

## The gp_ path: wound coil to point-contact transistor

Each entry is a narrow, specific failure mode between "we have electricity" and "we have a transistor." See `55_semiconductors.md` for the full path.

### gp_magnet_wire_enamelled - Enamelled magnet wire

**What/why.** Wire thin enough and reliably insulated enough to pack thousands of turns into a compact dynamo or transformer coil; without it, no compact coil.
**Kernel.** Silk-wrapped or oiled-linen wire, the natural output of existing wire and textile skill, is fine for one long telegraph wire but far too fat for thousands.
**Needs.** Fine drawn copper wire, a thin-drying hard varnish (cooked linseed oil varnish reformulated thinner).
**Check & failure.** Tightly wound turns show no continuity between neighbours and the coat does not crack on a tight bend.
**Cost, danger, confidence.** ESTIMATED (basis: fine wire-drawing labour): a drawer and dipping assistant. Varnish fumes need ventilation. Confidence: MEDIUM, formulation needs testing.

### gp_glass_metal_seal - Glass to metal vacuum seal

**What/why.** A current lead-in wire through a sealed glass tube wall must survive repeated heating and cooling without cracking the seal; this is what lets a vacuum tube carry current at all.
**Kernel.** This looks like glassblowing and is really a coefficient-matching problem: mismatched thermal expansion between glass and wire cracks the seal on the first heat cycle. Platinum tracks soda-lime glass closely.
**Needs.** Glass furnace with local controlled reheating, platinum wire (via long-distance trade, mat_platinum_bulk).
**Check & failure.** A sample cycled hot-cold several times shows no crack under magnification and holds vacuum over days.
**Cost, danger, confidence.** ESTIMATED (basis: platinum cost dominates): an hour of glasswork per seal. Furnace burns; platinum invites theft. Confidence: MEDIUM, glass's expansion curve untested.

### gp_getter - Chemical getter

**What/why.** After sealing, gas continues to seep out of a tube's internal metal parts for weeks, ruining the vacuum; a getter, a pellet of barium or magnesium flashed inside the sealed tube, absorbs it.
**Kernel.** The pump only gets you started; it cannot run on a sealed tube. A freshly flashed metal film is chemically hungry for oxygen and nitrogen and keeps absorbing it for months.
**Needs.** gp_exhaust_pinchoff sequence, magnesium metal (more reachable than barium at this level).
**Check & failure.** The flashed film stays bright and mirror-like; a film turning dull over days means the getter has already absorbed all it can.
**Cost, danger, confidence.** ESTIMATED (basis: small quantity of metal): low cost. Magnesium ignites in air, store under oil. Confidence: MEDIUM, isolating pure metal is nontrivial.

### gp_exhaust_pinchoff - Exhaust and pinch-off technique

**What/why.** The final sealing step: pump the assembled tube down, bake it, flash the getter, then pinch the connecting glass tail shut permanently while still under vacuum.
**Kernel.** Baking under vacuum, to drive adsorbed gas out of the internal metal parts, must happen before the getter flashes.
**Needs.** gp_getter, gp_glass_metal_seal, a vacuum pump, even heating for the bake.
**Check & failure.** The pinched tail shows a clean, fully closed seal with no pinhole; the tube holds vacuum for weeks after. Pinching before the bake-and-pump cycle traps gas permanently.
**Cost, danger, confidence.** ESTIMATED (basis: culminating step): tens of minutes per tube. Open flame near vacuum, standard risk. Confidence: MEDIUM.

### gp_carbon_brushes - Carbon and graphite brush contacts

**What/why.** A soft carbon block, spring-pressed against a rotating commutator or slip ring, carries current across a moving contact without the welding and gouging metal brushes cause.
**Kernel.** A metal-on-metal sliding contact under current spark-welds microscopically then tears free, gouging both surfaces; carbon is soft enough to wear itself down instead.
**Needs.** Reasonably pure charcoal or lamp-black carbon, compacted and baked into a block.
**Check & failure.** The commutator stays smooth and bright over weeks with even brush wear; too little spring pressure sparks, too much increases wear.
**Cost, danger, confidence.** ESTIMATED (basis: simple shaping): a day per set. Carbon dust is a minor irritant. Confidence: HIGH, well understood engineering.

### gp_laminated_core - Laminated iron core

**What/why.** Slicing a dynamo or transformer core into thin, insulated sheets instead of leaving it solid cuts the heat a changing magnetic field otherwise induces directly in the iron.
**Kernel.** A solid core has eddy currents induced in it, circulating in large loops and wasting energy as heat; thinly sliced insulated sheets confine each loop to one sheet.
**Needs.** Thin sheet iron (rolled or hammered), thin insulating varnish between sheets (gp_magnet_wire_enamelled chemistry).
**Check & failure.** A laminated core stays measurably cooler and delivers more usable output than a solid core of the same size.
**Cost, danger, confidence.** ESTIMATED (basis: sheet-metal skill plus coating): moderate labour, offset by reduced heat loss. Sharp edges. Confidence: HIGH, textbook.

### gp_controlled_atmosphere_chamber - Controlled atmosphere furnace chamber

**What/why.** A sealed fused-quartz vessel that lets germanium be melted without exposing it to ordinary air, since molten germanium absorbs oxygen and nitrogen within seconds and ruins its own purity.
**Kernel.** The obvious approach, an open crucible the way bronze or iron is melted, destroys the one property (extreme purity) the whole semiconductor path depends on.
**Needs.** Fused quartz vessel-making (advanced glasswork, a real stretch beyond attested Roman skill).
**Check & failure.** A test melt held liquid under the atmosphere for the full pull time shows none of the discolouration or gas-pit defects an air-exposed melt.
**Cost, danger, confidence.** ESTIMATED (basis: hardest entry here): a serious capital project. Furnace burns; a cracked vessel is serious. Confidence: LOW, extrapolation beyond attested craft.

### gp_czochralski_puller - Seed-and-pull crystal grower

**What/why.** A mechanism lowers an oriented seed crystal to touch a molten germanium surface, then slowly withdraws it while rotating, so the melt freezes onto the seed one layer at a time.
**Kernel.** Seed orientation sets which crystal direction grows, rotation rate keeps the melt symmetric around the growing crystal, and pull rate sets diameter directly.
**Needs.** gp_controlled_atmosphere_chamber, an oriented single-crystal seed, precise steady mechanical control of rotation and withdrawal speed.
**Check & failure.** The pulled crystal is a single continuous rod, uniform in diameter, cleaving along consistent planes; uneven rotation gives an off-centre crystal.
**Cost, danger, confidence.** ESTIMATED (basis: an unattended-pull operator): high skilled labour. Furnace heat only. Confidence: LOW, purity and atmosphere control unproven at Roman level.

### gp_whisker_forming - Point contact whisker forming

**What/why.** Two springy phosphor bronze points are set onto a polished germanium surface a few hundredths of a millimetre apart, then a brief current surge is deliberately passed through them.
**Kernel.** The forming pulse is the actual invention: touching two points to germanium alone gives a weak contact.
**Needs.** gp_czochralski_puller-grown single-crystal germanium polished clean, phosphor bronze wire shaped into fine springy points.
**Check & failure.** The formed contact passes current far more easily one direction than the other.
**Cost, danger, confidence.** ESTIMATED (basis: fine assembly and testing): many attempts per success. Low danger. Confidence: LOW, reproduces real 1947 trial and error.

---

## Scientific instruments

### in2_analytical_balance - Precision balances: equal-arm, torsion, quartz microbalance

**What/why.** An equal-arm balance with a sliding rider reads fractional weights; a torsion balance twists a fine fibre instead of a pivot, detecting forces too small for any pivot.
**Kernel.** The torsion balance's trick is removing the pivot entirely: a fibre twists through countless tiny increments with no friction floor.
**Needs.** Sharp hard pivot and rigid beam (equal-arm); fine uniform silk or glass fibre (torsion).
**Check & failure.** Repeated weighings of the same object agree within stated sensitivity; a dull pivot or a fibre twisted many times already both introduce error.
**Cost, danger, confidence.** DERIVED: days per balance. No danger. Confidence: HIGH equal-arm/torsion, MEDIUM quartz.
Also covers: in2_torsion_balance, in2_microbalance_quartz.

### in2_bourdon_pressure_gauge - Pressure and vacuum gauges

**What/why.** A curved Bourdon tube straightens slightly under pressure, driving a pointer, to very high pressures; an evacuated bellows (aneroid) flexes with outside pressure, portable.
**Kernel.** The McLeod gauge's trick is compression: trap a known gas volume, squeeze it down by a known ratio, and the pressure rises into a readable range.
**Needs.** Thin-walled bronze or steel tube (Bourdon), thin bronze sheet (bellows).
**Check & failure.** Readings against a known reference pressure agree within tolerance; Bourdon and aneroid gauges show hysteresis, correctable by calibration.
**Cost, danger, confidence.** DERIVED: days per gauge. Mercury is toxic, ventilate. Confidence: HIGH, well documented instruments.
Also covers: in2_aneroid_capsule, in2_mercury_barometer, in2_mcleod_vacuum_gauge.

### in2_pitot_tube - Flow measurement: pitot, venturi, orifice

**What/why.** A pitot tube compares total against static pressure for local velocity; a venturi narrows then widens, its throat pressure drop giving flow rate with good pressure recovery.
**Kernel.** The three trade cost against accuracy and lost energy in a predictable order: orifice cheapest and crudest, venturi smoother and costlier.
**Needs.** sc2_physics_hydrodynamics (Bernoulli's relation), a manometer or Bourdon gauge sensitive enough for the pressure differences.
**Check & failure.** Computed flow rate matches a timed known-volume fill; an orifice coefficient taken from a table rather than calibrated for the installation gives systematic error.
**Cost, danger, confidence.** DERIVED: fabrication days, calibration hours. No unusual danger. Confidence: HIGH, textbook.
Also covers: in2_venturi_flow_meter, in2_orifice_flow_meter.

### in2_thermocouple - Temperature measurement: thermocouple, RTD, gas thermometry

**What/why.** A thermocouple (two dissimilar metals joined, generating voltage from temperature difference) reaches 1600 C with platinum-rhodium pairs; a platinum resistance thermometer is more accurate but slower.
**Kernel.** Gas thermometry defines an absolute scale directly from the gas law rather than by comparison to another thermometer.
**Needs.** Platinum (thermocouple, RTD), a rigid sealed vessel and precise pressure gauge (gas thermometry).
**Check & failure.** The calibrated instrument repeatedly reads known reference points (ice, boiling water) correctly; an unaccounted reference-junction temperature or lead resistance introduces a fixed offset error.
**Cost, danger, confidence.** DERIVED: days per instrument. High-temperature calibration work. Confidence: HIGH, standard instrumentation.
Also covers: in2_resistance_thermometer_RTD, in2_gas_thermometry_absolute.

### in2_quartz_resonator_frequency - Frequency standards: quartz, tuning fork, hairspring

**What/why.** A precisely cut quartz crystal vibrates at a stable frequency (better than 1 part per million yearly, temperature-controlled); a tuning fork is a cruder mechanical equivalent (about 1 in 1,000).
**Kernel.** Quartz's piezoelectric effect, squeezing generates a voltage and a voltage flexes it back, lets it oscillate electrically at its own mechanical frequency with almost no external disturbance.
**Needs.** Precisely cut oriented quartz plus basic electrical drive (`55_semiconductors.md`).
**Check & failure.** Two independently made units run side by side drift apart less than stated tolerance; a poorly oriented quartz cut is far more temperature-sensitive.
**Cost, danger, confidence.** DERIVED: days per unit. No danger. Confidence: MEDIUM, quartz needs later electronics.
Also covers: in2_tuning_fork_oscillator, in2_balance_spring_watch.

### in2_optical_comparator - Optical length measurement: comparator and travelling microscope

**What/why.** An optical comparator projects a magnified shadow of a part onto a screen for fast contact-free comparison (10 to 100x); a travelling microscope pairs magnification with a precise micrometer screw stage.
**Kernel.** Neither the screw nor the eye alone is precise enough; combined, the microscope makes a small screw movement visually obvious, resolving finer than either could alone.
**Needs.** Precision ground lenses (`30_glass_optics.md`), a precisely cut micrometer screw.
**Check & failure.** Repeated measurements of a known-length standard agree within the instrument's resolution; backlash in a worn screw introduces error unless always turned the same direction.
**Cost, danger, confidence.** DERIVED: days. No danger. Confidence: HIGH, extends Roman lens grinding and screw cutting.
Also covers: in2_travelling_microscope.

---

## Materials wrongly flagged as unobtainable

### mat_natural_rubber - Distant materials that are reachable, not exotic

**What/why.** Seven materials the gap analysis flagged as apparent blockers are reachable via routes Rome already sails or trades, just farther along them (`data/world/geography.json`).
**Kernel.** The trap is assuming "not Mediterranean" means "unobtainable": rubber (African vines) sits down a coast Rome already sails.
**Needs.** Existing long-distance trade routes; ocean crossings specifically for quinine and platinum.
**Check & failure.** The material arrives at a cost consistent with other long-distance goods of similar bulk.
**Cost, danger, confidence.** DERIVED: existing trade infrastructure for most; quinine and crops need real expedition investment. Ordinary trade risk. Confidence: HIGH routes, MEDIUM transplantation.
Also covers: mat_gutta_percha, mat_quinine, mat_cryolite, mat_platinum_bulk, mat_chile_nitrate, mat_newworld_crops.

---

## Medicine: physiology, heredity, clinical method

Be careful here: several entries are knowledge rather than procedure, and several method entries carry real ethical weight.

### md2_circulation - Core physiology: circulation, digestion, respiration, kidney, nerves, hormones, immunity

**What/why.** Blood circulates in a closed loop through capillaries too fine to see, reused not remade; digestion is chemical as well as mechanical; lungs exchange gases across a thin barrier.
**Kernel.** Circulation is the sharpest correction: the intuitive picture (blood made fresh, consumed, not reused) is wrong.
**Needs.** md2_cadaver_dissection for structure, careful repeated observation of living animals.
**Check & failure.** The circulation model correctly predicts that tying off a vein pools blood on the far side from the heart.
**Cost, danger, confidence.** DERIVED: teaching time only. No danger from the knowledge itself. Confidence: HIGH, settled physiology.
Also covers: md2_digestion, md2_gas_exchange, md2_kidney, md2_nervous_system, md2_endocrine_system, md2_immunity.

### md2_cell_theory - Cell theory and heredity: chromosomes, genes, DNA, Mendelian ratios

**What/why.** Living organisation is cellular throughout, not fibrous or humoral; chromosomes are visible structures at division carrying genes, the active units of inheritance.
**Kernel.** The ratios are the sharp surprise: breeding a black and a white animal to grey suggests blending.
**Needs.** A microscope (`30_glass_optics.md`) for cells and chromosomes.
**Check & failure.** Counted offspring ratios match predicted patterns within chance's expected deviation; too few offspring counted makes chance look like a real pattern break.
**Cost, danger, confidence.** DERIVED: a garden plot, several seasons. No danger. Confidence: HIGH observable parts, MEDIUM DNA as the molecule.
Also covers: md2_chromosome, md2_gene, md2_dna, md2_mendelian_inheritance.

### md2_case_series - Clinical study design: case series to randomised controlled trial

**What/why.** A ladder of rigour: a case series describes a pattern with no control group; a case-control study compares affected against unaffected backward, fast but recall-biased; a cohort study follows a group forward.
**Kernel and the real ethical weight.** Randomisation is counter-intuitive: withholding a believed-effective treatment by coin flip feels wrong, but it is what eliminates selection bias. A placebo is unacceptable once a proven treatment exists.
**Needs.** md2_medical_statistics, md2_case_record, a large enough patient population.
**Check & failure.** The observed group difference exceeds what chance alone would produce this often; an unblinded trial lets physician enthusiasm bias who is judged "improved."
**Cost, danger, confidence.** DERIVED: many patients, years of follow-up. Real ethical weight withholding treatment from a control arm. Confidence: HIGH logic, MEDIUM Roman-era ethics.
Also covers: md2_case_control_study, md2_cohort_study, md2_randomised_controlled_trial, md2_blinding, md2_placebo.

### md2_medical_statistics - Medical statistics and vital registration

**What/why.** Applies probability and averaging (fin_census, fin_mortality_table) specifically to medicine: hypothesis testing (is a difference larger than chance alone would produce), confidence intervals, and a legal vital registration system recording cause of death.
**Kernel.** The denominator problem is the trap: a death count means nothing without knowing how many were at risk in the first place, which requires whole-population registration.
**Needs.** fin_census and fin_mortality_table machinery, a legal requirement for physician-assigned cause of death.
**Check & failure.** Rates computed from registration data are stable year to year and show a real change after a known intervention.
**Cost, danger, confidence.** DERIVED: extends existing census apparatus. Social resistance to reporting cause of death. Confidence: HIGH, direct application.
Also covers: md2_mortality_table, md2_vital_registration.

### md2_case_record - Medical practice institutions: case records, journals, licensing, nursing, pharmacopoeia

**What/why.** A standardised case record lets a second physician continue care; a medical journal establishes priority and spreads findings; licensing (built on fin_professional_exam) excludes untrained practitioners; professional nursing sets formal training standards.
**Kernel.** The pharmacopoeia's legal force is the sharp point: without it, the same drug name can mean wildly different actual strengths from different apothecaries.
**Needs.** fin_professional_exam for licensing, printing or copying capacity, a nursing training curriculum.
**Check & failure.** A case record lets an unfamiliar physician correctly continue care; a pharmacopoeia preparation from two apothecaries produces the same effect at the same dose.
**Cost, danger, confidence.** DERIVED: administrative infrastructure, comparable to other credentialing. A wrong mandated dose propagates everywhere. Confidence: MEDIUM, real risk without modern pharmacology.
Also covers: md2_medical_journal, md2_medical_licensing, md2_nursing_profession, md2_pharmacopoeia.

### md2_agar_media - Laboratory and anatomical method: agar culture, microbiology, bioassay, drug standardisation, cadaver dissection

**What/why.** Agar (red seaweed) is a solid culture medium that neither melts at body heat nor gets digested by growing bacteria, unlike gelatin; microbiology culture identifies organisms by colony and stain.
**Kernel.** Agar's advantage is counter-intuitive: gelatin looks like the obvious solid medium, but it melts at exactly the temperature you need and the organisms digest it as food.
**Needs.** Red seaweed source, a microscope, a maintained test-animal colony (bioassay), legal cadaver access.
**Check & failure.** Agar plates stay solid with distinct colonies for days; a bioassay's potency units predict clinical effect consistently across batches.
**Cost, danger, confidence.** DERIVED: modest cost, animal bioassay costlier. Real danger: lab pathogens, cadaver disease risk, Roman custom around the dead. Confidence: HIGH technique.
Also covers: md2_microbiology_culture, md2_bioassay, md2_drug_standardisation, md2_cadaver_dissection.

---

## Metallurgy: testing and structure analysis

### met_tensile_test - Mechanical testing: tensile, hardness, fatigue

**What/why.** A tensile test pulls a gripped specimen apart, plotting load against elongation for yield and ultimate strength; a hardness test presses a hardened indenter under known load.
**Kernel.** Fatigue is counter-intuitive: a part passing a static pull test comfortably can still fail suddenly from repeated loading at much lower stress.
**Needs.** civ_materials_testing's loading frame extended for cyclic load, a hardened or diamond indenter.
**Check & failure.** Tensile results on same-batch samples agree closely; hardness correlates with independently known tensile strength; a single sample taken as batch-representative.
**Cost, danger, confidence.** DERIVED: a testing machine is real capital, tests after are hours. A breaking specimen can whip. Confidence: HIGH, standard methods.
Also covers: met_hardness_test, met_fatigue_testing.

### met_metallography - Metal structure analysis: metallography, phase diagrams, spectroscopy

**What/why.** Metallography polishes a section mirror-smooth, etches with dilute acid to reveal grain boundaries and phases, examined under a microscope.
**Kernel.** The phase diagram converts a temperature into a prediction: heat a known steel to a specific temperature and the diagram says in advance which phases result.
**Needs.** met_tensile_test and met_hardness_test to correlate structure against real properties.
**Check & failure.** Observed microstructure correctly predicts independently measured hardness and toughness on the same batch; over-polishing smears the surface, over-etching dissolves fine detail.
**Cost, danger, confidence.** DERIVED: polishing is cheap, microscope/spectroscope are shared capital. Acids need care. Confidence: HIGH, non-exotic metallurgy.
Also covers: met_phase_diagram_knowledge, met_spectroscopic_assay.

### met_mannesmann_piercing - Mannesmann piercing for seamless tube

**What/why.** Two conical rolls, rotating toward each other around a heated round bar, pierce through its centre and push material outward into a tube, no weld seam.
**Kernel.** It sounds impossible, pinching a bar between rollers should squash it flat, but the hot bar is plastic not rigid.
**Needs.** A powered rolling mill with precisely aligned conical rolls.
**Check & failure.** The tube shows a continuous seamless wall in cross-section after etching, consistent thickness around the circumference; uneven bar heating pierces off-centre.
**Cost, danger, confidence.** DERIVED: substantial mill capital, ongoing crew. Crush and burn risk. Confidence: MEDIUM, needs a real powered mill.

---

## Manufacturing systems

### mfg_drawing_office - Engineering drawing and documentation

**What/why.** A drawing office as the single source of truth, using orthographic projection (standard top, front, side views with no ambiguity), consistent dimensioning, a bill of materials exploded from the drawing.
**Kernel.** Orthographic projection's value is non-obvious: a perspective drawing looks more natural, but three flat undistorted views let an operator read exact numbers directly with no interpretation.
**Needs.** Literate trained draftsmen, a consistently taught convention.
**Check & failure.** A part made from the drawing alone by someone who never saw the designer fits correctly first time.
**Cost, danger, confidence.** DERIVED: three draftsmen support 200 workers. No danger; under-staffing is the risk. Confidence: HIGH, a convention system, not new tech.
Also covers: mfg_blueprint, mfg_orthographic, mfg_dimensioning, mfg_bill_materials, mfg_change_order.

### mfg_production_schedule - Production planning and control

**What/why.** A production schedule balances demand, inventory, and capacity, revised regularly; an inventory reorder point accounts for lead time and usage rate.
**Kernel.** Quality department separation is the sharp point: it looks like duplication, but a production department grading its own work has an obvious incentive to pass borderline.
**Needs.** mfg_drawing_office specifications to inspect against, arithmetic for reorder points.
**Check & failure.** Stockouts and excess inventory both become rare; defect rates found independently fall over quarters.
**Cost, danger, confidence.** DERIVED: organisational overhead, a handful of staff per department. No danger. Confidence: HIGH, well-documented organisational science.
Also covers: mfg_inventory_mgmt, mfg_quality_dept, mfg_maintenance, mfg_tool_room.

### mfg_time_study - Scientific management: time study, work study, standard hour, piece rate, assembly line

**What/why.** Time study averages observed cycles, with fatigue allowances, into a standard hour of expected output; work study redesigns the task to remove unnecessary motion, typically a 20 to 40 percent gain.
**Kernel.** The assembly line's constraint is counter-intuitive: its speed is set entirely by the single slowest station, not by an average or the fastest.
**Needs.** mfg_drawing_office standardisation, a consistent short-interval timer, complete part standardisation for the line.
**Check & failure.** Measured output rises toward the new standard without a rise in defects; a piece rate without separate quality monitoring rewards speed over quality.
**Cost, danger, confidence.** DERIVED: modest study overhead, the line is the major capital cost. Piece-rate disputes are real. Confidence: HIGH, documented industrial engineering.
Also covers: mfg_work_study, mfg_standard_hour, mfg_piece_rate, mfg_assembly_line.

### mfg_queueing_theory - Operations research: queueing theory, linear programming and the simplex method, Gantt charts, the critical path method

**What/why.** Erlang's queueing theory (1909) sizes a telephone exchange, or any server against random arrivals, to a stated grade of service instead of a guess; Dantzig's simplex method (1947) finds the best allocation of scarce resources under linear constraints instead of leaving it to argument; the Gantt chart (Gantt, c.1910-15, after Adamiecki 1896) and the critical path method (Kelley and Walker 1957, the Navy's PERT 1958) turn a project's task list into a picture that names which delay actually costs the whole schedule a day.
**Kernel.** The simplex method's non-obvious step is geometric, not algebraic: the optimum of a linear objective under linear constraints is always at a CORNER of the feasible region, so a search only ever needs to hop between adjacent corners, never scan the interior. The critical path's non-obvious step is that slack is not evenly spread: most tasks in a real project can slip for free, and only one chain through the network cannot.
**Needs.** mfg_production_schedule and a functioning telephone exchange or comparable server system to size (queueing); statistics_basic and matrix algebra (simplex); mfg_production_schedule again (Gantt, critical path).
**Check & failure.** A sized exchange or stockroom hits its stated blocking or stockout rate under real traffic; a scheduled project's actual finish date tracks the critical path's predicted date, and slipping a non-critical task provably does not move it. Queueing and LP formulas mis-set when arrivals are not actually random (rush hours, batch orders) or constraints are not actually linear; a Gantt chart hides the network of dependencies a critical path chart makes explicit, so a Gantt-only shop still gets blindsided by which delay mattered.
**Cost, danger, confidence.** DERIVED: a handful of scholars and engineers, no special apparatus beyond paper and, for simplex on a large problem, a room of human computers before machine computation exists. No physical danger; the social risk is a plan that looks more certain than the arrival data underneath it actually is. Confidence: HIGH, textbook operations research with named originators and dates.
Also covers: mfg_linear_programming_simplex, mfg_gantt_chart, mfg_critical_path_method.

---

## Control theory: stability and the process controller

Maxwell's centrifugal-governor paper opens a body of theory the tree's mechanical governors and feedback amplifiers had been running on without: a proof that a closed loop can be built correctly and still be unstable, purely as a property of its own equations, plus the designed three-term controller that this theory makes it safe to tune aggressively. See `40_power_precision.md` for the flyball governor itself and `50_electricity.md` for the feedback amplifier; this section is the mathematics that tells you, in advance, whether either one will hunt or hold.

### ctl_governor_stability_theory - Stability theory: Maxwell's governor equations, Routh and Hurwitz criteria, Nyquist, Bode, root locus

**What/why.** Maxwell (1868) writes the governor's own linearised differential equation and shows its characteristic equation's roots decide stability. Routh (1877) and, independently, Hurwitz (1895, answering Stodola's turbine problem) give algebraic tests on that equation's coefficients that answer stable-or-not with no root ever solved for. Nyquist (1932) and Bode (early 1940s) extend the same question to feedback amplifiers, graphically, with a numeric safety margin. Evans's root locus (1948) plots how the closed loop's poles move as gain is turned up, so a designer can pick a gain by eye.
**Kernel.** The scandal is that stability is NOT a craftsmanship question. A governor or amplifier built to the same drawing, with the same care, is stable or unstable purely as a property of the numbers in its own loop equation; more gain, or a longer feedback delay, can turn a rock-steady loop into one that oscillates without warning, for reasons no amount of fine machining fixes.
**Needs.** en_centrifugal_governor or el2_negative_feedback_stability_gain as the physical loop being analysed; calculus for Maxwell; polynomial algebra for Routh; determinants for Hurwitz; complex numbers for Nyquist and root locus; logarithms for Bode.
**Check & failure.** A loop predicted stable by the criterion runs without hunting under a step change in load; a loop predicted unstable, run anyway, hunts or oscillates exactly as predicted. Applying any of these tests to a loop whose real delay or nonlinearity was not modelled gives a false stable verdict, the single most common failure of the whole approach.
**Cost, danger, confidence.** DERIVED: a scholar's or engineer's desk time, no apparatus. No physical danger from the mathematics itself; the danger it prevents is downstream, in the plant that would otherwise have been tuned by trial and error against a real hazard. Confidence: HIGH, textbook control theory with named originators and dates.
Also covers: ctl_routh_criterion, ctl_hurwitz_criterion.

### ctl_nyquist_stability_criterion - Nyquist criterion, Bode plot and margins, root locus

**What/why.** Nyquist's 1932 criterion counts encirclements of one point by a plotted curve to answer whether a closed feedback loop is stable; Bode's log-magnitude and phase plots make the same test readable at a glance and reduce the safety margin to two design numbers; Evans's root locus (1948) shows graphically where the closed loop's poles move as gain increases.
**Kernel.** All three replace "solve the equation and check" with "read a picture", which matters because the loops worth building, telephone repeater amplifiers with hundreds of stages, are far too high an order to solve by hand every time a component value changes.
**Needs.** ctl_governor_stability_theory's algebraic criteria as the thing these graphical methods are a faster read of; el2_negative_feedback_stability_gain as the amplifier this was built to tame; complex numbers; logarithms for Bode specifically.
**Check & failure.** A loop redesigned to a target gain and phase margin from a Bode plot survives production tolerances that a marginally-stable design does not; reading a Nyquist plot with the wrong sense of encirclement, an easy mistake, predicts the opposite of the true answer.
**Cost, danger, confidence.** DERIVED: desk time and graph paper, no apparatus. Confidence: HIGH.
Also covers: ctl_bode_plot_margins, ctl_root_locus.

### ctl_minorsky_pid_law - The designed process controller: three-term (PID) control, the pneumatic controller, Ziegler-Nichols tuning

**What/why.** Minorsky (1922), watching a helmsman steer the battleship USS New Mexico, formalises correction proportional to present error, to the error's rate of change, and to its accumulated past, as the first explicit three-term (proportional-integral-derivative) control law. Instrument makers, Foxboro's Stabilog (1931) foremost, build that law into a compressed-air relay that positions a valve directly from a bellows reading a process deviation, no electricity required on the plant floor. Ziegler and Nichols (1942, Taylor Instrument Companies) give two short empirical recipes for setting the three gains from a step test or a single sustained oscillation, without ever writing down the process's own differential equation.
**Kernel.** The three-term law is the answer to a specific failure the tree's tension around zone_refining and similar processes turns on: a mechanical governor holds ONE variable near ONE setpoint by direct linkage, but a furnace, distillation column or autoclave has a variable that drifts on its OWN thermal or chemical time lag, too slow for a flyball's centrifugal response and too varied for one fixed linkage ratio. The integral and derivative terms are what let a controller chase a slow, laggy process without either leaving a permanent offset (proportional alone) or overreacting to noise (derivative alone).
**Needs.** ctl_governor_stability_theory (a three-term loop can still be tuned into instability, and the same stability tests apply); newtonian_mechanics for Minorsky's own derivation; cap_power_steam or cap_power_electric for the compressed-air or electrical supply the pneumatic relay runs on; a pressure or temperature sensing element (opt_bourdon_gauge, thermometer, in2_thermocouple) to read the process.
**Check & failure.** A process held under the controller shows a bounded, damped return to setpoint after a disturbance rather than a permanent offset or a growing oscillation; a controller tuned too aggressively (integral or derivative gain too high) hunts continuously, visibly worse than manual control, which is exactly the failure Ziegler-Nichols's rules are built to avoid.
**Cost, danger, confidence.** DERIVED: engineer and machinist hours to build the pneumatic relay itself, modest capital next to the furnace or column it regulates. No new physical danger beyond the process it controls; the risk it exists to reduce is losing that process to drift. Confidence: HIGH, textbook process control with named originators and dates.
Also covers: ctl_pneumatic_process_controller, ctl_ziegler_nichols_tuning.

---

## Military organisation

State the dependency chain only; see `97_military.md` for the full account.

### mil_general_staff - Professional military planning: general staff and war college

**What/why.** A permanent peacetime cadre of professional planners handles campaign strategy, logistics, and mobilisation continuously; a war college formally teaches military science, producing shared professional doctrine.
**Kernel.** This only works as a standing peacetime institution; planning invented from scratch after war is declared is already too late for this scale of mobilisation.
**Needs.** fin_government-grade bureaucratic capacity, a literate officer corps, sc2_institution_curriculum-style formal teaching.
**Check & failure.** Peacetime mobilisation plans execute close to schedule when needed; a general staff without real authority becomes a paper exercise ignored in the field.
**Cost, danger, confidence.** DERIVED: standing officer salary, small relative to the army. An independent officer class is a power centre. Confidence: HIGH.
Also covers: mil_war_college.

### mil_conscription_reserve - Mass mobilisation: conscription, railways, logistics, arsenal manufacture

**What/why.** Conscription and a trained reserve turn a small army into a much larger force within weeks (European armies grew from about 2 million to 15 million within months in 1914).
**Kernel.** None of the four work alone: conscription without railways cannot reach the front in time, railways without logistics discipline arrive with no supplies waiting.
**Needs.** fin_government-grade administration for registration, a coordinated rail network.
**Check & failure.** A mobilisation exercise moves the reserve to its assigned position on schedule, fully equipped.
**Cost, danger, confidence.** DERIVED: whole-economy scale. This mobilisation speed is itself a strategic risk to neighbours. Confidence: MEDIUM, depends on infrastructure not assumed built.
Also covers: mil_railway_mobilisation, mil_logistics_discipline, mil_arsenal_manufacturing, mil_ammunition_standardisation.

### mil_cryptanalysis - Signals intelligence, cryptanalysis, operational research

**What/why.** Signals intelligence intercepts enemy radio, using direction-finding and traffic analysis to reveal movements without reading content; cryptanalysis is the harder step of breaking the cipher itself.
**Kernel.** All three depend on the enemy already using radio in the first place; before that, there is no traffic to intercept and no cipher to break.
**Needs.** Enemy radio use (not yet true at Roman technology level).
**Check & failure.** Analysed traffic correctly predicts enemy movements, verified against events; acting on partial signals with excess confidence, or failing to disguise a broken cipher.
**Cost, danger, confidence.** DERIVED: a dedicated corps, bounded wartime cost. Over-trusting broken intelligence is the main risk. Confidence: MEDIUM, depends on radio technology not provided.
Also covers: mil_signals_intelligence, mil_operational_research.

---

## Shop-floor training and knowledge transfer

### prc_apprentice_system - Apprentice system and toolroom institution

**What/why.** A boy apprenticed around age twelve, bound roughly seven years, learns tacit skill (feel for a scraper, reading a dial indicator) under direct supervision, knowledge that cannot be written down.
**Kernel.** mfg_drawing_office specifies what a part should be, precisely; it cannot specify how to physically achieve that precision by hand, a gap only direct extended supervision closes.
**Needs.** Master craftsmen willing to take apprentices, an equipped toolroom space.
**Check & failure.** A trained apprentice working independently matches the master's precision, judged by met_hardness_test and civ_materials_testing measurement, not by eye.
**Cost, danger, confidence.** DERIVED: one master trains a handful over years; a toolroom supports fifty machines. Apprentices are bound labour, a real constraint. Confidence: HIGH.
Also covers: prc_toolroom_institution.

---

## Libraries, archives, and publishing

### prn_library_archive - Library, archive, cataloguing, indexing, copyright economics

**What/why.** A library or archive preserves texts beyond any one owner's lifetime; a cataloguing system turns a pile of scrolls into a searchable resource; an index or concordance gives a complete word-location list.
**Kernel.** Copyright's timing is the surprise: it barely makes sense before printing exists, since hand-copying a whole scroll is already so slow that unauthorised copies pose little threat.
**Needs.** A building with fire, damp, and theft protection, literate cataloguers.
**Check & failure.** An unfamiliar reader locates a specific passage in minutes using catalogue and index.
**Cost, danger, confidence.** DERIVED: cataloguing scales with collection size, the building is the larger cost. Fire is the dominant danger, Alexandria the caution. Confidence: HIGH.
Also covers: prn_cataloguing_system, prn_index_concordance, prn_copyright_economics.

---

## Science as institution

### sc2_institution_journal - Scientific publication: journal, learned society, citation, peer review

**What/why.** A periodical journal (Philosophical Transactions, 1665) establishes priority and lets distant researchers learn from each other; a learned society (Royal Society 1660) creates community and authority.
**Kernel.** Anonymity is the counter-intuitive design choice: an anonymous referee can honestly flag a colleague's or rival's flawed work without it becoming personal.
**Needs.** Printing capacity or a well-organised scribal circulation network.
**Check & failure.** Priority disputes become rare, since the journal date settles them; a journal without real review becomes a vehicle for weak or fraudulent work.
**Cost, danger, confidence.** DERIVED: printing cost plus unpaid reviewer time. Publication exposes work to criticism. Confidence: HIGH, documented from the 1660s.
Also covers: sc2_institution_learned_society, sc2_institution_citation, sc2_institution_referee.

### sc2_institution_curriculum - Academic teaching institutions: curriculum, textbook, examination, doctorate

**What/why.** A deliberately ordered curriculum (arithmetic before algebra, geometry before calculus) organises teaching coherently; a textbook (Euclid's Elements, already old in 100 AD) distills a field into one reference; written examination standardises assessment.
**Kernel.** The doctorate's originality requirement is the hard part to institutionalise: certifying learned material is straightforward, certifying genuine novelty requires expert judges who know the field's frontier.
**Needs.** sc2_institution_journal to establish what counts as "already known," fin_university's institutional home.
**Check & failure.** Students passing each stage can perform the next stage's material without re-teaching; a curriculum ordered by tradition rather than real prerequisite leaves students memorising.
**Cost, danger, confidence.** DERIVED: textbook writing is slow, teaching cost is ordinary. Institutions resist curriculum change. Confidence: HIGH, Euclid proves the core idea works.
Also covers: sc2_institution_textbook, sc2_institution_examination, sc2_institution_doctorate.

### sc2_institution_funded_programme - Research funding and management

**What/why.** A funded research programme, money for research with no immediate product owed, becomes essential once research grows too expensive for private means; patent disclosure forces a choice between secrecy and monopoly.
**Kernel.** A research group looks like ordinary apprenticeship, but junior members are simultaneously being trained and actively producing original work under the director's credit.
**Needs.** fin_endowed_chair or a state programme for funding, sc2_institution_journal for publishing output.
**Check & failure.** The group produces a steady stream of published, cited work over years; funding tied too tightly to short-term deliverables loses the research freedom that made the model valuable.
**Cost, danger, confidence.** DERIVED: funding varies, the pattern itself costs only salaries. Credit disputes are a real friction. Confidence: MEDIUM, depends on institutions above existing.
Also covers: sc2_institution_patent_disclosure, sc2_institution_research_group.

---

## The scientific method as institution

### sc2_method_hypothesis - Hypothesis, controlled experiment, lab notebook, replication, peer criticism, negative results

**What/why.** Six linked habits are the real machinery of empirical science: an explicit falsifiable hypothesis stated in advance; a controlled experiment isolating one variable; a dated lab notebook recording what was actually done.
**Kernel.** Negative results go most against instinct: a null finding disappoints everyone, yet a well-designed experiment that found nothing saves everyone else the time of independently repeating.
**Needs.** sc2_institution_journal for publication, basic probability (from this module's mathematics kernel).
**Check & failure.** An independent researcher following only the published method and notebook obtains a comparable result.
**Cost, danger, confidence.** DERIVED: notebook materials negligible, real cost is sustained culture. Risk is talking about habits without practising them. Confidence: HIGH logic.
Also covers: sc2_method_controlled_experiment, sc2_method_lab_notebook, sc2_method_negative_result, sc2_method_peer_criticism, sc2_method_replication.

---

## Physics: a compressed survey

Full derivations belong in `60_mathematics_method.md`; this states what each result is, its non-obvious kernel, and where it plugs into the tech tree.

### sc2_physics_newtons_laws - Classical mechanics: Newton's laws, kinematics, momentum, energy, work, gravitation

**What/why.** Newton's three laws (Principia, 1687), kinematics (position, velocity, acceleration related by calculus), momentum conservation, kinetic and potential energy, work and power.
**Kernel.** Gravitation's unification is the sharp insight: a falling apple and an orbiting planet look unrelated.
**Needs.** Arithmetic and basic calculus, this module's mathematics kernel.
**Check & failure.** Predicted trajectories and collision outcomes match careful measurement; solving every problem from force alone, rather than momentum or energy, is often needlessly hard.
**Cost, danger, confidence.** DERIVED: teaching time and simple apparatus. No unusual danger. Confidence: HIGH, the most solid physics here.
Also covers: sc2_physics_kinematics, sc2_physics_momentum, sc2_physics_energy, sc2_physics_work_power, sc2_physics_gravitation.

### sc2_physics_fluid_statics - Fluid mechanics: statics, Bernoulli, viscosity, Reynolds number

**What/why.** Fluid statics and buoyancy (Archimedes, Hero) explain floating and sinking; Bernoulli's equation (1738) shows faster-moving fluid has lower pressure; viscosity (Stokes, 1851) measures internal friction.
**Kernel.** The Reynolds number's scale-independence is the surprise: a small model and a full-size ship show the same flow pattern if this one combined number matches.
**Needs.** sc2_physics_newtons_laws, basic calculus for Bernoulli's derivation.
**Check & failure.** A scaled model with matched Reynolds number shows the same flow character as the full-size design.
**Cost, danger, confidence.** DERIVED: water tank models, simple timing. No unusual danger. Confidence: HIGH, textbook.
Also covers: sc2_physics_hydrodynamics, sc2_physics_viscosity, sc2_physics_reynolds_number.

### sc2_physics_elasticity - Elasticity, wave motion, acoustics, aerodynamic lift

**What/why.** Hooke's spring law is the structural-engineering foundation; the wave equation describes vibration mechanically; acoustics applies that to sound; aerodynamic lift explains how a wing generates lift.
**Kernel.** This is where the Fourier idea from the introduction earns its keep: any complex vibration is really a sum of simple sine waves at different frequencies.
**Needs.** sc2_physics_newtons_laws, calculus, the Fourier decomposition idea (`60_mathematics_method.md`).
**Check & failure.** A structure's calculated elastic deflection matches measurement; loading past the elastic limit invalidates Hooke's proportionality, a common design error if not tested first (civ_materials_testing).
**Cost, danger, confidence.** DERIVED: simple apparatus; a wind tunnel is a real capital project. No unusual danger. Confidence: HIGH; MEDIUM on rigorous lift theory.
Also covers: sc2_physics_wave_motion, sc2_physics_acoustics, sc2_physics_aerodynamic_lift.

### sc2_physics_electrostatics - Electromagnetism: electrostatics, magnetostatics, Maxwell's equations, EM waves, spectrum

**What/why.** Coulomb's law (1785) quantifies charge force with the electric field as the organising concept; magnetostatics (Ampere, Gauss) does the same for magnets and current loops; Maxwell's equations (1861-1862) unify both.
**Kernel.** Light being an electromagnetic wave is the startling unification: sight and static electricity look unrelated, and accepting they are the same phenomenon required real theoretical courage.
**Needs.** `50_electricity.md`'s practical electrical foundation, calculus for Maxwell's equations.
**Check & failure.** A predicted electromagnetic wave is detected at a distance with no wire connection, the direct experimental link to light.
**Cost, danger, confidence.** DERIVED: mostly apparatus costed in `50_electricity.md`. Shock risk from spark-gap demos. Confidence: HIGH, textbook.
Also covers: sc2_physics_magnetostatics, sc2_physics_maxwell_equations, sc2_physics_em_wave, sc2_physics_spectrum.

### sc2_physics_geometric_optics - Optics: geometric rays, diffraction, speed of light

**What/why.** Geometric optics (Fermat's least-time principle) lets mirrors and lenses be designed by ray tracing; diffraction (Fraunhofer, 1819-1823) explains how a fine slit grating splits light by wavelength; the speed of light is a fundamental constant.
**Kernel.** Fermat's principle sounds like it attributes intention to light ("chooses the fastest path"), when it is really a mathematical consequence of wave behaviour.
**Needs.** `30_glass_optics.md`'s lens and mirror grinding skill.
**Check & failure.** Ray-traced predictions for a lens or mirror match where the real image forms.
**Cost, danger, confidence.** DERIVED: shared with `30_glass_optics.md` cost, plus grating-ruling skill. No unusual danger. Confidence: HIGH; MEDIUM on an accurate speed-of-light measurement.
Also covers: sc2_physics_diffraction, sc2_physics_speed_of_light.

### sc2_physics_kinetic_theory - Kinetic theory and statistical mechanics

**What/why.** Kinetic theory (Clausius, Maxwell, Boltzmann) explains pressure and temperature as the statistical result of huge numbers of molecular collisions; the Boltzmann distribution shows molecular speeds, electron energies.
**Kernel.** The blackbody problem is the sharpest lesson here: a theory working perfectly everywhere else can fail completely in one specific regime.
**Needs.** sc2_physics_newtons_laws applied statistically to huge particle numbers, basic probability from this module's mathematics kernel.
**Check & failure.** Measured gas behaviour under controlled heating matches kinetic theory quantitatively; reaction rates at different temperatures fall on a straight line the Arrhenius way.
**Cost, danger, confidence.** DERIVED: shared with the in2 instrument cluster. No unusual danger. Confidence: HIGH theory; MEDIUM full statistical mechanics and blackbody measurement.
Also covers: sc2_physics_boltzmann_distribution, sc2_physics_statistical_mechanics, sc2_physics_blackbody_radiation.

### sc2_physics_quantum_photon - Quantum and nuclear physics: photon, photoelectric effect, uncertainty, wave mechanics, nucleus, neutron, fission

**What/why.** Planck's 1900 quantum hypothesis, extended by Einstein (1905) to the photoelectric effect (frequency, not intensity, ejects electrons, confirmed by Millikan in 1916), the Heisenberg uncertainty principle (1927, a fundamental limit), and Rutherford's nucleus and the neutron, together sketch modern quantum and nuclear physics, ending in fission.
**Kernel and why it sits at the far end of this survey.** The photoelectric effect is the sharpest surprise here: a brighter light at the same colour knocks out exactly as many electrons, no more energetic, while only changing colour (frequency) changes their energy, a result that seemed absurd until Millikan's decade-long measurement confirmed it.
**Needs.** sc2_physics_electrostatics and sc2_physics_kinetic_theory as the classical foundation this overturns.
**Check & failure.** Historically: Millikan's measurements confirmed the photoelectric prediction precisely, Rutherford's scattering pattern confirmed a small dense nucleus. Treating this cluster as achievable at the same level as the rest of this module is the biggest mistake a reader could make.
**Cost, danger, confidence.** ESTIMATED (basis: real programme needed national infrastructure): the most distant entry here, for completeness. Fission carries catastrophic danger. Confidence: HIGH history.
Also covers: sc2_physics_photoelectric_effect, sc2_physics_uncertainty_principle, sc2_physics_wave_mechanics, sc2_physics_nucleus_discovery, sc2_physics_neutron_discovery, sc2_physics_nuclear_fission.

---

## Sources and confidence

Mathematics and classical physics (statics through optics) are HIGH throughout: settled, textbook material where the open question is teaching sequence, not correctness. The gp_ semiconductor cluster is deliberately MEDIUM to LOW: principles are documented, but steps like fused-quartz vessel-making and gas purification at the needed purity are real extrapolations beyond attested Roman craft, flagged per entry. Medical entries are HIGH where directly observable, MEDIUM where they need sustained institutions (registration, trial ethics) to deliver value. Institutional entries (finance, academic, military, publishing) are HIGH on mechanism, MEDIUM on Roman social adoption, a real historical gamble, not a technical certainty. The quantum/nuclear physics cluster is HIGH on history, explicitly LOW on near-term relevance.

## Where to go next

- [`60_mathematics_method.md`](60_mathematics_method.md) - the full teaching sequence for positional notation, calculus, and the mathematics this module assumes throughout.
- [`55_semiconductors.md`](55_semiconductors.md) - the complete semiconductor path the nine `gp_` nodes above are individual steps within.
- [`70_medicine_biology.md`](70_medicine_biology.md) - the wider medical and biological programme the `md2_` cluster supplements.
- [`96_finance.md`](96_finance.md) - money, banking, and corporate law, the platform the `fin_` institutional cluster is built on.
- [`97_military.md`](97_military.md) - the full military-technology programme the `mil_` organisational cluster depends on.
