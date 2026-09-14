# Blind Prerequisite Audit — `point_contact_transistor`

Method: breadth-first from the goal node. For each node, only the `id` and `name` were
looked up first; prerequisites (3–10 of them) were guessed from the name and general
historical/technical knowledge *before* the node's actual `pre` list was read. Guesses
were then classified MATCHED / ELSEWHERE / MISSING against the actual list (after a
targeted search of the whole tree, not just this node, before calling anything MISSING).
Actual prerequisites not guessed were classified REASONABLE / QUESTIONABLE.

Processed 40 nodes (budget cap reached; queue was not empty).

## Summary table

| Metric | Count |
|---|---|
| Nodes processed | 40 |
| Total guesses made | 232 |
| Guesses MATCHED | 101 |
| Guesses classified ELSEWHERE (tree has it, not on this node) | 86 |
| Guesses classified MISSING (not found anywhere by targeted search) | 45 |
| Actual prerequisites not guessed — REASONABLE | 19 |
| Actual prerequisites not guessed — QUESTIONABLE | 1 |

Note on the 45 "MISSING" guesses: about 15 of these come from three root/axiom nodes
(`units_standards`, `arithmetic_positional`, `scientific_method`) that deliberately have
**zero** prerequisites by design (the tree's own notes say standing/institutions are not
a prerequisite for stating an idea, only for being *believed*). Those are not tree defects;
they are counted for completeness but excluded from the prioritized list below. The
substantive misses are concentrated in a handful of real items, listed after the node log.

---

## Node-by-node log

### 1. point_contact_transistor — "Point-contact transistor"
Guesses: (1) controlled-purity semiconductor crystal, (2) crystal-growth/purification
method, (3) controlled doping, (4) fine wire point-contact fabrication/positioning,
(5) solid-state/quantum theory of semiconductors, (6) precision low-current measurement,
(7) stable DC power supply, (8) vacuum-tube electronics as prior art, (9) precision
micromanipulation/metrology, (10) an institutional research lab.

Actual `pre` (7): `galena_detector`, `gp_whisker_forming`, `micrometer_gauges`,
`prc_lapping_plate`, `quantum_solidstate_theory`, `single_crystal`, `vacuum_tube`.
(`req_any`: alternate path `silicon_path` vs `single_crystal`, not treated as a hard dependency.)

- 1,2,3 → MATCHED (`single_crystal`)
- 4 → MATCHED (`gp_whisker_forming`)
- 5 → MATCHED (`quantum_solidstate_theory`)
- 6 → ELSEWHERE (galvanometer/voltmeter family, found later under `semiconductor_metrology`)
- 7 → ELSEWHERE (battery chain, found later under `daniell_cell`/`crude_cell`)
- 8 → MATCHED (`vacuum_tube`)
- 9 → MATCHED (`micrometer_gauges`, `prc_lapping_plate`)
- 10 → ELSEWHERE (`fin_research_institute` exists in the tree)

Actual not guessed: `galena_detector` — REASONABLE (the direct historical ancestor device).

### 2. galena_detector — "Galena cat's whisker point-contact rectifier"
Guesses: (1) galena mineral access, (2) fine wire, (3) battery+circuit, (4) radio/antenna
context, (5) concept of rectification, (6) audio indicator, (7) adjustable spring mount.

Actual `pre` (3): `crude_cell`, `drawplate_wire`, `lead_metallurgy`.

- 1 → MATCHED (`lead_metallurgy`, explicitly "secures your galena supply")
- 2 → MATCHED (`drawplate_wire`)
- 3 → MATCHED (`crude_cell`)
- 4 → ELSEWHERE (`com_antenna_ground` etc. exist, not wired here — and on reflection this
  isn't really a prerequisite of the rectifier itself, only of a later radio application)
- 5 → MISSING, but retracted on reflection: the node's own note says explicitly "No
  purification, no doping, no vacuum, no theory" — my guess was simply wrong here.
- 6 → ELSEWHERE (`com_morse_sounder` is a close analogue)
- 7 → MISSING (no dedicated node; minor)

### 3. gp_whisker_forming — "Point contact whisker forming"
Guesses: (1) semiconductor crystal to form against, (2) pulse/capacitor circuit,
(3) fine sharpened wire, (4) precision micromanipulator, (5) electrical monitoring during
forming, (6) prior point-contact rectifier knowledge, (7) etched/clean crystal surface.

Actual `pre` (2): `cap_tol_10um`, `daniell_cell`.

- 1 → ELSEWHERE (`single_crystal`, sibling under the parent goal, not re-listed here)
- 2 → ELSEWHERE (capacitor tech exists in the tree — `electrostatics`, `el2_capacitor_*` —
  but not wired here; `daniell_cell` supplies steady current, not obviously a pulse)
- 3 → ELSEWHERE (`drawplate_wire`, an ancestor)
- 4 → MATCHED (`cap_tol_10um`)
- 5 → ELSEWHERE (galvanometer family, seen later)
- 6 → ELSEWHERE (`galena_detector`, sibling)
- 7 → ELSEWHERE (`prc_lapping_plate`, sibling)

Actual not guessed: `daniell_cell` — REASONABLE (power source for the forming pulse).

### 4. micrometer_gauges — "Micrometer, verniers, gauge blocks, go/no-go gauges"
Guesses: (1) precision screw-cutting lathe, (2) hardened steel stock, (3) reference
length standard, (4) flat lapping technique, (5) general machine-tool metalworking,
(6) dividing engine/scale graduation, (7) hardenable tool steel.

Actual `pre` (2): `master_screw`, `precision_three_plate`.

- 1 → MATCHED (`master_screw`)
- 2 → ELSEWHERE (cast/tool-steel nodes exist, not listed here)
- 3 → ELSEWHERE (`cap_measure_len` exists elsewhere)
- 4 → MATCHED (`precision_three_plate`)
- 5 → ELSEWHERE
- 6 → ELSEWHERE (`mfg_dividing_engine` exists)
- 7 → ELSEWHERE

### 5. prc_lapping_plate — "Lapping with cast-iron plate and abrasive compound"
Guesses: (1) cast-iron foundry capability, (2) fine abrasive powder, (3) flat reference
surface, (4) oil/grease carrier, (5) grinding/polishing precursor, (6) rotary motion/bench,
(7) flatness verification.

Actual `pre` (2): `cap_tol_10um`, `precision_three_plate`.

- 1 → ELSEWHERE (`mat_cast_iron` exists)
- 2 → ELSEWHERE (`mat_emery` exists)
- 3 → MATCHED (`precision_three_plate`)
- 4 → MISSING (not modeled; minor)
- 5 → ELSEWHERE
- 6 → MATCHED (`cap_tol_10um`)
- 7 → ELSEWHERE (`prc_standard_meter_wavelength` exists)

### 6. quantum_solidstate_theory — "Band theory, doping, carriers, the p-n junction"
Guesses: (1) quantum mechanics/Schrödinger, (2) atomic theory, (3) statistical mechanics,
(4) crystallography, (5) X-ray diffraction, (6) electromagnetic theory, (7) advanced math,
(8) institutionalized research/publication system.

Actual `pre` (2): `atomic_theory`, `em_theory`.

This is a deliberate "carry the conclusions" shortcut node — the note says explicitly:
*"Historically this took from 1900 to 1947 and several Nobel prizes. You carry the
conclusions... The single largest time saving in the programme."*

- 1 → ELSEWHERE (`sc2_physics_wave_mechanics` exists in the tree, unused here)
- 2 → MATCHED (`atomic_theory`)
- 3 → ELSEWHERE (`sc2_physics_statistical_mechanics` exists, unused here)
- 4 → ELSEWHERE (no direct crystallography node but covered via X-ray diffraction nodes)
- 5 → ELSEWHERE (`in2_xray_diffraction_camera` / `mt2_xray_diffraction` exist, unused here)
- 6 → MATCHED (`em_theory`)
- 7 → ELSEWHERE (`calculus` exists, unused here)
- 8 → ELSEWHERE (`fin_research_institute` exists, unused here)

This node is the clearest example in the whole audit of the tree's "theory download"
device: a fully-built granular physics chain exists elsewhere in the tree but the
critical path to the goal explicitly bypasses it.

### 7. single_crystal — "Czochralski single crystal growth and controlled doping"
Guesses: (1) purified feedstock, (2) precise-temperature furnace, (3) controlled
atmosphere, (4) seed crystal, (5) precision pulling/rotating mechanism, (6) dopant
metering/analytical balance, (7) inert crucible material, (8) pyrometry.

Actual `pre` (8): `cap_measure_temp_hi`, `cap_tol_10um`, `gp_controlled_atmosphere_chamber`,
`gp_czochralski_puller`, `in2_xray_diffraction_camera`, `prc_gauge_blocks_johansson`,
`semiconductor_metrology`, `zone_refining`.

- 1 → MATCHED (`zone_refining`)
- 2 → MATCHED (`cap_measure_temp_hi`, `gp_czochralski_puller`)
- 3 → MATCHED (`gp_controlled_atmosphere_chamber`)
- 4 → MATCHED (`gp_czochralski_puller`)
- 5 → MATCHED (`gp_czochralski_puller`, `cap_tol_10um`)
- 6 → **MISSING** — the node's own note says *"Add the dopant to the melt in weighed
  traces; this is where the analytical balance earns its keep"* but no balance node
  (`balance_analytical` / `in2_analytical_balance`, both of which exist in the tree) is
  in the `pre` list.
- 7 → ELSEWHERE (`fused_quartz` exists, a sibling of `gp_controlled_atmosphere_chamber`)
- 8 → MATCHED (`cap_measure_temp_hi`)

Actual not guessed: `in2_xray_diffraction_camera`, `prc_gauge_blocks_johansson`,
`semiconductor_metrology` — all REASONABLE (grain-boundary check, metrology, carrier
verification).

### 8. vacuum_tube — "Diode, triode, and the first amplifier"
Guesses: (1) high-vacuum pump, (2) glassblowing, (3) heated filament/cathode,
(4) thermionic-emission theory, (5) metal-to-glass sealing, (6) grid electrode/wire mesh,
(7) DC power supply, (8) EM/circuit theory.

Actual `pre` (8): `cap_vac_1e6`, `copper_refining`, `diffusion_pump`, `discharge_xray`,
`gp_exhaust_pinchoff`, `gp_getter`, `gp_glass_metal_seal`, `in2_electron_source_cathode`.

- 1 → MATCHED (`cap_vac_1e6`, `diffusion_pump`)
- 2 → ELSEWHERE (general glassworking assumed ancestor)
- 3 → MATCHED (`in2_electron_source_cathode`)
- 4 → MATCHED (`discharge_xray`)
- 5 → MATCHED (`gp_glass_metal_seal`)
- 6 → **MISSING** — no node anywhere in the tree explicitly covers fabricating the
  triode's fine wire-mesh control grid, the element that turns a diode into an amplifier.
- 7 → ELSEWHERE (battery/dynamo chain)
- 8 → ELSEWHERE (`em_theory`, via `discharge_xray`)

Actual not guessed: `copper_refining`, `gp_exhaust_pinchoff`, `gp_getter` — all REASONABLE.

### 9. cap_tol_10um — "Tolerance 0.01 mm (slide rest, lead screw, micrometer)"
Guesses: (1) slide-rest lathe, (2) lead screw, (3) micrometer/caliper, (4) hardened tool
steel, (5) master length standard, (6) machinist craft tradition.

Actual `pre` (3): `cap_tol_100um`, `micrometer_gauges`, `screw_lathe`.

- 1,2 → MATCHED (`screw_lathe`)
- 3 → MATCHED (`micrometer_gauges`)
- 4 → ELSEWHERE
- 5 → ELSEWHERE (`cap_measure_len` exists)
- 6 → ELSEWHERE (`prc_apprentice_system` exists)

Actual not guessed: `cap_tol_100um` — REASONABLE (tiered tolerance progression).

### 10. daniell_cell — "Daniell cell and reliable current sources"
Guesses: (1) copper/zinc metal supply, (2) CuSO4/ZnSO4 salts, (3) porous
barrier/diaphragm, (4) voltaic-pile precursor, (5) ceramic/glass containers,
(6) electrochemical-series knowledge.

Actual `pre` (2): `sulfuric_retort`, `voltaic_pile`.

- 1 → ELSEWHERE (baseline metal supply)
- 2 → MATCHED (`sulfuric_retort`)
- 3 → MISSING (no porous-pot/diaphragm node found)
- 4 → MATCHED (`voltaic_pile`)
- 5 → ELSEWHERE (glass/lab-apparatus chain)
- 6 → MISSING (minor, folded into chemistry elsewhere, not found as distinct node)

### 11. master_screw — "The first accurate screw, and thread standards"
Guesses: (1) basic lathe, (2) hardened-steel cutting tool, (3) hand thread-accuracy
check, (4) consistent metal stock, (5) hand-filing/fitting skill, (6) standardized thread
convention.

Actual `pre` (3): `cap_tol_100um`, `cementation_steel`, `precision_three_plate`.

- 1 → MISSING, but retracted: the node's own note explicitly describes escaping the
  lathe bootstrap problem by *wrapping a strip around a cylinder* — no lathe needed. My
  guess was simply incorrect, not a tree gap.
- 2 → MATCHED (`cementation_steel`)
- 3 → MATCHED (`precision_three_plate`, the lapping-with-a-long-nut averaging method)
- 4 → ELSEWHERE
- 5 → MATCHED (`cap_tol_100um`)
- 6 → ELSEWHERE (`units_standards`, `opt_standards_laboratory` exist)

### 12. precision_three_plate — "True plane surfaces by the three-plate method"
Guesses: (1) three rough flat plate blanks, (2) abrasive/scraping compound, (3) hand
scraping skill, (4) visual flatness check, (5) metal casting/forging capability.

Actual `pre` (2): `case_hardening`, `units_standards`.

- 1 → ELSEWHERE (node's own note: "needs nothing any Iron-Age workshop does not already have")
- 2 → ELSEWHERE (`mat_emery` exists)
- 3 → ELSEWHERE
- 4 → MATCHED (self-referentially satisfied by the three-plate rotation method itself)
- 5 → ELSEWHERE

Actual not guessed: `case_hardening`, `units_standards` — both REASONABLE (durable
scraper/plate material; standardized length/temperature scale).

### 13. atomic_theory — "Atoms, elements, atomic weights, stoichiometry, the periodic table"
Guesses: (1) quantitative chemical analysis, (2) analytical balance, (3) gas-law
experiments, (4) isolation/characterization of pure elements, (5) comparative
tabulation method, (6) scientific community/publication.

Actual `pre` (2): `arithmetic_positional`, `scientific_method`.

Another "carry the conclusions" node: *"You can write the periodic table from memory
on day one... It only becomes operational once you have the analytical balance."*

- 1 → MISSING (elided by design)
- 2 → **MISSING** — explicitly named as operationally necessary in the node's own note,
  yet not in `pre`, and no downstream node reconnects it either.
- 3 → MISSING (elided by design)
- 4 → MISSING (elided by design)
- 5 → MATCHED (covered by the shortcut device itself)
- 6 → MATCHED (`scientific_method`)

Actual not guessed: `arithmetic_positional` — REASONABLE.

### 14. em_theory — "Electromagnetic theory"
Guesses: (1) electrostatics, (2) basic magnetism, (3) current/Ohm's law, (4) induction
(Faraday), (5) calculus, (6) Oersted-type electricity–magnetism link.

Actual `pre` (2): `calculus`, `newtonian_mechanics`.

Same shortcut pattern: *"Faraday's and Maxwell's conclusions handed to a school that can
already do calculus collapses a century into a decade."*

- 1 → ELSEWHERE (`sc2_physics_electrostatics`, `electrostatics` exist, unused here)
- 2 → ELSEWHERE (`sc2_physics_magnetostatics`, `sea_magnetic_compass` exist)
- 3 → ELSEWHERE (implied by broader `el2_*` electrical chain)
- 4 → MISSING (no clearly dedicated induction-experiment node found)
- 5 → MATCHED (`calculus`)
- 6 → MISSING (not found as a distinct node)

Actual not guessed: `newtonian_mechanics` — REASONABLE.

### 15. cap_measure_temp_hi — "High temperature (clay contraction and colour pyrometry)"
Guesses: (1) high-temp kiln/furnace, (2) reference clay cones, (3) empirical colour
chart, (4) ceramic know-how, (5) lower-tier thermometry.

Actual `pre` (2): `cap_heat_1300`, `cap_measure_temp`.

- 1 → MATCHED (`cap_heat_1300`)
- 2, 3 → MATCHED (embodied in this node's own described technique)
- 4 → ELSEWHERE
- 5 → MATCHED (`cap_measure_temp`)

### 16. gp_controlled_atmosphere_chamber — "Controlled atmosphere furnace chamber"
Guesses: (1) gas-tight enclosure, (2) inert/reducing gas supply, (3) gas flow/pressure
regulation, (4) high-temp furnace integration, (5) heat-resistant seals/gland,
(6) purge/evacuate before backfill.

Actual `pre` (3): `cap_gas_o2h2`, `cap_vac_1torr`, `fused_quartz`.

- 1 → MATCHED (`fused_quartz`)
- 2 → MATCHED (`cap_gas_o2h2`)
- 3 → ELSEWHERE
- 4 → ELSEWHERE (sibling furnace nodes)
- 5, 6 → MATCHED (`cap_vac_1torr`)

### 17. gp_czochralski_puller — "Seed-and-pull crystal grower"
Guesses: (1) motorized withdrawal mechanism, (2) rotation mechanism, (3) vertical
alignment/guide rails, (4) furnace temperature-gradient control, (5) vibration
isolation, (6) fine screw/gear drive.

Actual `pre` (2): `cap_tol_10um`, `motor_transformer_ac`.

- 1, 2, 6 → MATCHED (`motor_transformer_ac`, `cap_tol_10um`)
- 3 → MATCHED (`cap_tol_10um`)
- 4 → ELSEWHERE (sibling furnace/atmosphere nodes)
- 5 → **MISSING** (no vibration-isolation node found anywhere for precision crystal growth)

### 18. in2_xray_diffraction_camera — "X-ray diffraction camera: Bragg geometry"
Guesses: (1) X-ray source, (2) photographic film, (3) Bragg's-law theory,
(4) precision goniometer/rotation stage, (5) radiation shielding, (6) darkroom/film
development.

Actual `pre` (2): `discharge_xray`, `mirror_amalgam`.

- 1 → MATCHED (`discharge_xray`)
- 2 → ELSEWHERE (photography chain exists)
- 3 → ELSEWHERE (folded into the node's own description)
- 4 → **MISSING** — the node's own note explicitly says *"Requires collimated X-rays
  and precision rotation stage,"* but no such node is in `pre`.
- 5 → MISSING (minor, not modeled)
- 6 → ELSEWHERE

Actual not guessed: `mirror_amalgam` ("Tin-mercury amalgam plate mirrors") — **QUESTIONABLE**.
Ordinary X-ray diffraction cameras do not need front-surface visible-light mirrors; this
reads like a mismatched or placeholder dependency, possibly standing in for "precision
reflective-surface fabrication" generically, or a linking error, perhaps in place of the
missing goniometer/rotation-stage requirement noted above.

### 19. prc_gauge_blocks_johansson — "Gauge blocks and wringing with 0.5 micron accuracy"
Guesses: (1) hardened dimensionally-stable steel, (2) sub-micron flat lapped surfaces,
(3) master reference standard, (4) temperature-controlled environment,
(5) optical flatness/interferometry, (6) dust-free handling.

Actual `pre` (3): `cap_measure_light`, `cap_tol_10um`, `precision_three_plate`.

- 1 → ELSEWHERE
- 2 → MATCHED (`precision_three_plate`, `cap_tol_10um`)
- 3, 5 → MATCHED (`cap_measure_light`)
- 4 → MISSING (minor)
- 6 → MISSING (minor)

### 20. semiconductor_metrology — "Four-point probe, Hall effect, carrier measurement"
Guesses: (1) precision low-current source/measurement, (2) strong stable magnet,
(3) four fine probe contacts, (4) Hall-effect theory, (5) microvolt-level voltage
measurement, (6) repeatable non-damaging sample contact.

Actual `pre` (7): `cap_measure_elec`, `el2_potentiometer_method_measurement`,
`el2_valve_voltmeter_high_impedance`, `electromagnet`, `galvanometer`,
`quantum_solidstate_theory`, `vacuum_tube`.

- 1 → MATCHED (`galvanometer`, `el2_potentiometer_method_measurement`, `cap_measure_elec`)
- 2 → MATCHED (`electromagnet`)
- 3 → MISSING (no dedicated fine-probe-contact fabrication node found)
- 4 → MATCHED (`quantum_solidstate_theory`)
- 5 → MATCHED (`el2_valve_voltmeter_high_impedance`)
- 6 → MISSING (minor)

Actual not guessed: `vacuum_tube` — REASONABLE (underlies the valve voltmeter).

### 21. zone_refining — "Zone refining to one part in 1e9"
Guesses: (1) raw germanium feedstock, (2) movable induction/resistance heater,
(3) controlled atmosphere, (4) controlled-speed translation mechanism, (5) inert
boat/container, (6) purity-verification technique.

Actual `pre` (8): `arc_furnace_ferroalloys`, `cap_measure_temp_hi`, `cap_tol_10um`,
`el2_induction_heating_inductor_coupling`, `ge_reduction`, `gp_controlled_atmosphere_chamber`,
`motor_transformer_ac`, `semiconductor_metrology`.

- 1 → MATCHED (`ge_reduction`)
- 2 → MATCHED (`el2_induction_heating_inductor_coupling`)
- 3 → MATCHED (`gp_controlled_atmosphere_chamber`)
- 4 → MATCHED (`motor_transformer_ac`, `cap_tol_10um`)
- 5 → ELSEWHERE (`fused_quartz`)
- 6 → MATCHED (`semiconductor_metrology`)

Actual not guessed: `arc_furnace_ferroalloys` — REASONABLE (probably supplies furnace
refractory/electrode/heating-element materials); `cap_measure_temp_hi` — REASONABLE.

### 22. crude_cell — "Copper-iron brine cell"
Guesses: (1) copper/iron metal supply, (2) brine/salt, (3) non-conductive container,
(4) empirical dissimilar-metals-in-electrolyte knowledge.

Actual `pre` (2): `lead_metallurgy`, `workshop_first`.

- 1 → MATCHED, via `lead_metallurgy` (its own note explains it stands in for "a
  developed metal-mining/working tradition" — an initially odd-looking but, on
  investigation, reasonable link)
- 2 → MISSING (minor, assumed trivially available)
- 3 → MATCHED (`workshop_first`)
- 4 → ELSEWHERE / embedded in the node's own description

### 23. drawplate_wire — "The drawplate and drawn wire"
Guesses: (1) hardened steel plate, (2) ductile metal stock, (3) drawing bench/pulling
mechanism, (4) lubricant, (5) annealing furnace.

Actual `pre` (2): `case_hardening`, `workshop_first`.

- 1 → MATCHED (`case_hardening`)
- 2 → ELSEWHERE (baseline)
- 3 → MATCHED (`workshop_first`)
- 4, 5 → ELSEWHERE / embedded in description

### 24. lead_metallurgy — "Lead sheet, pipe, litharge and cupellation control"
Guesses: (1) lead-ore access, (2) smelting furnace, (3) cupellation hearth,
(4) metalworking tools, (5) workshop infrastructure.

Actual `pre` (1): `workshop_first`. (root-adjacent; note says "already done... wherever
there is a developed lead-mining tradition; Rome is the best-documented case")

- 1, 3 → MATCHED (embedded in the node's own note)
- 2, 4, 5 → MATCHED (`workshop_first`)

### 25. cap_vac_1e6 — "Very high vacuum, 1e-6 torr (diffusion pump plus getters)"
Guesses: (1) diffusion pump hardware, (2) rough backing pump, (3) chemical getter,
(4) vacuum gauge, (5) leak-tight construction.

Actual `pre` (3): `cap_power_electric`, `cap_tol_10um`, `cap_vac_1e3`.

- 1 → ELSEWHERE (the `diffusion_pump` node exists but, oddly, is not listed here despite
  this node's own name being "diffusion pump plus getters" — see note below)
- 2 → MATCHED (`cap_vac_1e3`, `cap_power_electric`)
- 3 → ELSEWHERE (`gp_getter` exists as a sibling elsewhere, not here)
- 4, 5 → ELSEWHERE

Actual not guessed: `cap_tol_10um` — REASONABLE. Minor structural note: this node's name
advertises "diffusion pump plus getters" but neither `diffusion_pump` nor `gp_getter` is
actually in its `pre` list — they're consumed as siblings by `vacuum_tube` instead. Not a
missing capability (the tree has both), just an internal naming/abstraction wrinkle.

### 26. copper_refining — "High-purity copper and insulated wire"
Guesses: (1) electrolytic refining, (2) raw copper feedstock, (3) insulating coating,
(4) wire-drawing technology, (5) DC power.

Actual `pre` (3): `cap_pure_4N`, `drawplate_wire`, `mat_copper`.

- 1 → MATCHED (`cap_pure_4N`)
- 2 → MATCHED (`mat_copper`)
- 3 → ELSEWHERE / embedded (silk, shellac, bitumen — in the node's own note)
- 4 → MATCHED (`drawplate_wire`)
- 5 → ELSEWHERE

### 27. diffusion_pump — "Rotary and mercury diffusion pumps"
Guesses: (1) rotary-vane pump stage, (2) mercury supply, (3) mercury heater,
(4) precision-machined parts, (5) vacuum piping.

Actual `pre` (4): `cap_vac_1torr`, `interchangeable_parts`, `motor_transformer_ac`, `vacuum_pumps`.

- 1 → MATCHED (`cap_vac_1torr`, `motor_transformer_ac`)
- 2 → MATCHED (`vacuum_pumps`)
- 3, 5 → ELSEWHERE / embedded
- 4 → MATCHED (`interchangeable_parts`)

### 28. discharge_xray — "Discharge tubes, cathode rays, X-rays, the electron"
Guesses: (1) rough-vacuum sealed glass tube, (2) high-voltage source, (3) sealed
electrodes, (4) photographic plates, (5) fluorescent screen material.

Actual `pre` (3): `dynamo`, `em_theory`, `vacuum_pumps`.

- 1 → MATCHED (`vacuum_pumps`)
- 2 → MATCHED (`dynamo`)
- 3 → ELSEWHERE
- 4 → ELSEWHERE (photography chain)
- 5 → MISSING (minor)

Actual not guessed: `em_theory` — REASONABLE.

### 29. gp_exhaust_pinchoff — "Exhaust and pinch-off technique"
Guesses: (1) glassworking torch, (2) vacuum-pump connection, (3) workable glass tubing,
(4) monitor vacuum level, (5) skilled glassblowing.

Actual `pre` (2): `cap_heat_2000`, `cap_vac_1e6`.

- 1 → MATCHED (`cap_heat_2000`)
- 2 → MATCHED (`cap_vac_1e6`)
- 3, 4, 5 → ELSEWHERE / embedded

### 30. gp_getter — "Chemical getter"
Guesses: (1) reactive-metal getter material, (2) induction-flash heating mechanism,
(3) chemical scavenging knowledge, (4) sealed vacuum envelope.

Actual `pre` (2): `el2_induction_heating_inductor_coupling`, `glass_clear`.

- 1, 3 → MATCHED / embedded in node's own description
- 2 → MATCHED (`el2_induction_heating_inductor_coupling`)
- 4 → MATCHED (`glass_clear`)

### 31. gp_glass_metal_seal — "Glass to metal vacuum seal"
Guesses: (1) thermal-expansion-matched alloy, (2) glassworking torch skill, (3) clean
surface preparation, (4) matched glass composition, (5) controlled cooling/annealing.

Actual `pre` (2): `cap_tol_100um`, `glass_clear`.

- 1 → MISSING (no dedicated node for the specific matched-expansion lead-in alloy,
  e.g. Dumet wire, even though the node's own note names platinum and nickel-iron
  explicitly)
- 2, 3, 5 → ELSEWHERE / embedded
- 4 → MATCHED (`glass_clear`)

Actual not guessed: `cap_tol_100um` — REASONABLE (fitting/checking the seal).

### 32. in2_electron_source_cathode — "Electron source: heated cathode"
Guesses: (1) filament material (tungsten), (2) low-voltage current source, (3) vacuum
environment, (4) thermionic-emission theory, (5) emission-enhancing oxide coating.

Actual `pre` (1): `discharge_xray`.

- 1 → **MISSING** — no node connects ductile tungsten filament wire (powder-metallurgy
  tungsten, hot-swaged and drawn — the historical Coolidge process) to this node, even
  though `mat_tungsten`, `mt2_tungsten_extraction`, and `met_powder_metallurgy` all exist
  elsewhere in the tree. Producing wire-drawable tungsten was itself a hard, dedicated
  materials-science problem, not a trivial consequence of "having tungsten metal."
- 2 → ELSEWHERE
- 3, 4 → MATCHED (`discharge_xray`)
- 5 → MISSING (minor refinement, not modeled)

### 33. cap_tol_100um — "Tolerance 0.1 mm (file, scraper, gauge)"
Guesses: (1) hardened files/scrapers, (2) gauge/template standard, (3) craftsman skill,
(4) adequate lighting, (5) cruder prior tolerance tier.

Actual `pre` (2): `cap_tol_1mm`, `precision_three_plate`.

- 1, 3, 5 → MATCHED (`cap_tol_1mm`)
- 2 → MATCHED (`precision_three_plate`)
- 4 → MISSING (minor, not modeled)

### 34. cementation_steel — "Blister steel by cementation"
Guesses: (1) wrought-iron bar stock, (2) charcoal carbon source, (3) sealed
chest/furnace, (4) sustained high temperature, (5) bloomery precursor.

Actual `pre` (3): `cap_heat_1100`, `case_hardening`, `refractory_fireclay`.

- 1, 2 → ELSEWHERE (baseline)
- 3 → MATCHED (`refractory_fireclay`, `cap_heat_1100`)
- 4 → MATCHED (`cap_heat_1100`)
- 5 → MATCHED (`case_hardening` — small-scale carburizing predates bulk cementation
  furnaces historically, so this ordering is right on reflection)

### 35. case_hardening — "Systematic case hardening, quenching and tempering"
Guesses: (1) iron/steel objects, (2) carbon-rich packing material, (3) furnace reaching
critical temperature, (4) quenching medium, (5) colour-based temperature judgment,
(6) blacksmithing tradition.

Actual `pre` (2): `units_standards`, `workshop_first`.

- 1–4, 6 → ELSEWHERE / embedded (node's own note: "smiths already do all of this... but
  inconsistently")
- 5 → MATCHED (`units_standards` — temper colours as a standardized index)

### 36. units_standards — "Define and publish standard length, mass, time and temperature"
Guesses: (1) central authority, (2) physical reference artifacts, (3) distribution
mechanism, (4) writing/numeracy, (5) economic buy-in.

Actual `pre` (0) — a deliberate root node.

All 5 guesses are technically MISSING from the `pre` list, but this is a designed axiom
("Do this before writing any other recipe down") not a tree defect — Rome's pre-existing
writing, authority, and bronze-casting are simply taken as given starting conditions.

### 37. arithmetic_positional — "Decimal positional notation, zero, negative numbers, decimal fractions"
Guesses: (1) writing system for numerals, (2) scribal/educational infrastructure,
(3) trade/accounting motive, (4) exposure to existing positional systems, (5) baseline literacy.

Actual `pre` (0) — deliberate root node ("Needs no standing... a nobody can do this").
Same treatment as node 36.

### 38. scientific_method — "Controlled experiment, hypothesis, replication, publication"
Guesses: (1) writing/record-keeping, (2) peer community, (3) publication distribution,
(4) patronage/funding, (5) cultural tolerance for questioning authority.

Actual `pre` (0) — deliberate root node, same "needs no standing" design as 36/37.
Institutional resistance (opposition from Aristotelian/Galenic authorities) is modeled
as narrative risk/traits on the node, not as a graph dependency.

### 39. calculus — "Differential and integral calculus"
Guesses: (1) algebraic notation, (2) decimal positional arithmetic, (3) geometric
foundations, (4) mathematical-rigor tradition, (5) physical motivating problems.

Actual `pre` (1): `geometry_analytic`.

- 1, 3 → MATCHED (`geometry_analytic`, "coordinate geometry and trigonometric tables")
- 2 → MISSING (minor — `arithmetic_positional` is a free root node elsewhere but not
  linked here)
- 4, 5 → ELSEWHERE / embedded (Archimedes' method of exhaustion, per the node's note)

### 40. newtonian_mechanics — "Newtonian mechanics and gravitation"
Guesses: (1) calculus, (2) astronomical observation data, (3) precision timekeeping,
(4) scientific-method tradition, (5) geometry/trigonometry.

Actual `pre` (1): `calculus`.

- 1 → MATCHED (`calculus`)
- 2 → MISSING (no astronomical-observation node linked, though astronomy nodes likely
  exist elsewhere in the tree — not confirmed by targeted search this round)
- 3 → MISSING (no pendulum-clock/timekeeping node linked)
- 4 → ELSEWHERE (`scientific_method` is a root node elsewhere, unused here)
- 5 → ELSEWHERE (via the `calculus` → `geometry_analytic` chain)

---

## Prioritized MISSING list (the actual product of this audit)

Ordered by how consequential the gap is to a faithful reconstruction of the path to the
point-contact transistor.

1. **Analytical balance is narratively required but graph-absent.** Two different nodes'
   own notes (`single_crystal`: *"this is where the analytical balance earns its keep two
   centuries later"*; `atomic_theory`: *"it only becomes operational once you have the
   analytical balance"*) call out the balance by name as a practical precondition, yet
   neither `balance_analytical` nor `in2_analytical_balance` (both exist in the tree) is
   wired into either node's `pre` list, or into `semiconductor_metrology`.
   **Fix:** add `balance_analytical` (or `in2_analytical_balance`) as an explicit
   prerequisite of `single_crystal` (for weighing dopant traces) and consider it for
   `atomic_theory`'s downstream "operational" nodes.

2. **The triode's control-grid fabrication is not modeled anywhere.** `vacuum_tube`
   covers cathode, vacuum, seals, exhaust, and getters, but nothing addresses making and
   positioning the fine wire-mesh grid that is the defining structural difference between
   a diode and a triode/amplifier.
   **Fix:** add a node (e.g. `gp_grid_electrode_winding`) depending on fine wire
   (`drawplate_wire`/`copper_refining`) and precision winding/mounting jigs
   (`cap_tol_10um`), and make it a prerequisite of `vacuum_tube`.

3. **Ductile tungsten filament wire is disconnected from the cathode node.**
   `in2_electron_source_cathode`'s only prerequisite is `discharge_xray`; nothing links
   it to `mat_tungsten`, `mt2_tungsten_extraction`, or `met_powder_metallurgy`, even
   though drawing tungsten into filament wire (historically the Coolidge process —
   powder-sinter an ingot, then hot-swage and draw) was itself a nontrivial, dedicated
   achievement distinct from simply possessing tungsten metal.
   **Fix:** add a `gp_ductile_tungsten_wire` node depending on `met_powder_metallurgy` +
   `mat_tungsten` + `drawplate_wire`-class drawing technique, and make it a prerequisite
   of `in2_electron_source_cathode`.

4. **The X-ray diffraction camera's own note names a requirement it doesn't list, and
   lists one that looks wrong.** `in2_xray_diffraction_camera`'s note says *"Requires
   collimated X-rays and precision rotation stage"* but no goniometer/rotation-stage node
   is in its `pre`; instead it lists `mirror_amalgam` ("tin-mercury amalgam plate
   mirrors"), which has no obvious role in X-ray diffraction.
   **Fix:** replace or supplement `mirror_amalgam` with a precision rotation-stage/
   goniometer node (built from `cap_tol_10um`-class precision mechanics), matching the
   node's own stated requirement.

5. **"Theory download" nodes bypass the tree's own granular physics/chemistry chain.**
   `quantum_solidstate_theory`, `atomic_theory`, and `em_theory` are explicit narrative
   shortcuts ("you carry the conclusions") with minimal prerequisites, while the tree
   separately contains a full bottom-up chain (`sc2_physics_wave_mechanics`,
   `sc2_physics_statistical_mechanics`, `sc2_physics_electrostatics`,
   `sc2_physics_magnetostatics`, `sc2_physics_maxwell_equations`,
   `mt2_xray_diffraction`/`in2_xray_diffraction_camera`) that is never connected to the
   goal's critical path. This is clearly a deliberate design choice (and is explained in
   each node's note), but a careful historian would flag it as the single largest
   compression in the whole tree — real 1900–1947 solid-state physics needed quantum
   statistics and X-ray crystallography as load-bearing inputs, not just "calculus plus
   prior theory."
   **Fix (if closer historical fidelity is wanted):** make `quantum_solidstate_theory`
   additionally depend on `sc2_physics_wave_mechanics`, `sc2_physics_statistical_mechanics`,
   and `mt2_xray_diffraction`; make `em_theory` depend on `sc2_physics_electrostatics` and
   `sc2_physics_magnetostatics`.

6. **No pulse/capacitor-discharge circuit for the transistor "forming" step.**
   `gp_whisker_forming` depends only on `cap_tol_10um` and `daniell_cell` (a steady,
   low-voltage source), but the node's own note describes "a brief surge of current" —
   closer to a capacitor discharge than a battery-and-switch. The tree has a substantial
   capacitor branch (`electrostatics`, `el2_capacitor_fixed_mica`,
   `el2_capacitor_fixed_paper`, `el2_capacitor_variable_air`,
   `el2_capacitor_electrolytic`) that is never connected here.
   **Fix:** add a capacitor-discharge node as an alternate/additional prerequisite of
   `gp_whisker_forming`.

7. **No vibration isolation for the Czochralski puller.** At the precision implied by
   `cap_tol_10um`-scale pulling mechanics, ordinary workshop/building vibration would
   disturb the melt meniscus and seed interface; no isolation mechanism (massive bench,
   spring/sand damping, etc.) is modeled anywhere near `gp_czochralski_puller`.
   **Fix:** add a vibration-isolation capability node as a prerequisite, or fold it into
   `prc_machine_frame_cast_iron` (already in the tree) and link that in.

8. **Lower-priority / minor items**, worth a pass but not urgent: a porous diaphragm for
   `daniell_cell`; a named matched-thermal-expansion sealing alloy (Dumet wire) rather
   than prose-only in `gp_glass_metal_seal`; temperature-controlled environment and
   dust-free handling for `prc_gauge_blocks_johansson`; radiation shielding anywhere near
   `discharge_xray`/`in2_xray_diffraction_camera`; a dedicated fine four-point-probe
   contact-fabrication node for `semiconductor_metrology`.
