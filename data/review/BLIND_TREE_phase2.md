# Phase Two: Comparison of the blind reconstruction against the real tree

Method: read `point_contact_transistor`'s full ancestor closure via its `pre`
edges (146 nodes total, computed by BFS over `pre`), read every closure node's
name and prerequisites, and searched the full 2831-node tree freely for terms
implied by the phase-one capability list. `req_any` fields were inspected but
excluded from the closure count: several of their `options` keys point at raw
material identifiers (e.g. `mat_steel`, `linen_kg`) rather than tech-node ids,
so they read as alternative-material bookkeeping, not the prerequisite graph
proper.

Axioms per the task brief, noted once and not scored below: `units_standards`,
`arithmetic_positional`, `scientific_method` (founder's starting knowledge),
and `atomic_theory`, `em_theory`, `quantum_solidstate_theory` (compressed
physics chains).

---

## Part A: Phase-one capabilities vs. the real tree

| # | Capability (phase one) | Verdict | Real-tree node(s) |
|---|---|---|---|
| 1 | Controlled-purity germanium crystal | MATCHED | `germanium_extraction`, `ge_reduction`, `gecl4_purification`, `cap_pure_2N/4N/6N`, `zone_refining` |
| 2 | Single-crystal growth process | MATCHED | `single_crystal`, `gp_czochralski_puller` |
| 3 | High-temp furnace, controlled atmosphere | MATCHED | `high_temp_furnace`, `gp_controlled_atmosphere_chamber`, `cap_heat_*` ladder |
| 4 | Purity verification (resistivity/chemical) | MATCHED | `semiconductor_metrology`, `analytical_chemistry`, `balance_analytical` |
| 5 | Fine wire-drawing | MATCHED | `drawplate_wire` |
| 6 | Springy contact alloy (phosphor bronze / gold) | MISSING | no phosphor-bronze alloy node anywhere in the 2831-node tree; `mat_gold` exists but is referenced as a prerequisite by nothing, including `point_contact_transistor` itself, though `gold_g` is charged as a material cost |
| 7 | Precision screw adjustment / fine mechanical positioning | MATCHED | `master_screw`, `micrometer_gauges`, `screw_lathe`, `cap_tol_10um` |
| 8 | Magnifying optics / microscope for placing the whisker | MISSING | `microscope_compound` and `glass_bead_microscope` exist in the tree (used for biology/metallography) but neither is reachable from `point_contact_transistor`, `gp_whisker_forming`, or any semiconductor node |
| 9 | Galvanometer / small-current measurement | MATCHED | `galvanometer` |
| 10 | Precision resistor standards (manganin/constantan) | ELSEWHERE | `el2_standard_resistor_manganin`, `mt2_manganin_resistance` exist but are referenced by nothing at all in the whole tree, not just outside the goal closure |
| 11 | Stable low-voltage DC supply | MATCHED | `voltaic_pile`, `daniell_cell`, `crude_cell` |
| 12 | Empirical metal-semiconductor rectification | MATCHED | `galena_detector` |
| 13 | Natural semiconducting mineral (galena) | MATCHED | folded into `galena_detector` <- `lead_metallurgy`, elegantly the same ore as the lead chain |
| 14 | Early radio-frequency context | ELSEWHERE | a large radio subtree exists (`radio`, `com_crystal_set`, `if_coherer`, etc.) built on top of `galena_detector`, correctly *not* required going the other direction into the transistor; phase-one over-included this as motivation rather than a hard dependency |
| 15 | Chemical/electrolytic etch of the germanium surface | MISSING | goal closure has only mechanical lapping (`prc_lapping_plate`); `el2_electropolishing_etching_surface_finish` exists but is referenced by nothing anywhere |
| 16 | Industrial acid manufacture | MATCHED | `sulfuric_retort`, `nitric_acid`, `hydrochloric_acid`, `lead_chamber` |
| 17 | Vacuum pump technology | MATCHED | `vacuum_pumps`, `diffusion_pump`, `cap_vac_*` ladder |
| 18 | Heated filament / thermionic cathode | MATCHED | `in2_electron_source_cathode` |
| 19 | Glass-to-metal vacuum seal | MATCHED | `gp_glass_metal_seal` |
| 20 | Glassblowing / glass manufacture | MATCHED | `glass_labware`, `glass_clear`, `glass_borosilicate` |
| 21 | Precision machining (lathes, mills) | MATCHED | `screw_lathe`, `prc_milling_machine`, `boring_mill`, `prc_treadle_lathe_flywheel` |
| 22 | Hardened tool steel / cutting dies | MATCHED | `cementation_steel`, `crucible_steel`, `case_hardening`, `mat_bulk_steel` |
| 23 | Metal annealing / heat treatment | MATCHED | `case_hardening` |
| 24 | Electric motor technology | MATCHED | `motor_transformer_ac`, `dynamo`, `en_alternator`, `en_commutator` |
| 25 | Distillation apparatus / lab glassware | MATCHED | `glass_labware`, `lab_apparatus`, `sulfuric_retort`, `gecl4_purification` |
| 26 | Precise temperature control | MATCHED | `cap_measure_temp_hi`, `cap_measure_temp`, `thermometer` |
| 27 | Refractory furnace linings | MATCHED | `refractory_fireclay`, `mt2_silica_brick_refractory` |
| 28 | Inert/controlled gas atmosphere | MATCHED | `cap_gas_o2h2`, `gp_controlled_atmosphere_chamber` |
| 29 | Airtight seals and gaskets | MATCHED | `mat_leather` (via `cap_vac_1torr`), `gp_glass_metal_seal` |
| 30 | Basic circuit theory + insulated wire | MATCHED | `em_theory` axiom, `copper_refining` |
| 31 | Vacuum-tube amplifier as a whole | MATCHED | `vacuum_tube` — landed on the exact node |
| 32 | Rigid, vibration-free precision positioning fixture | MATCHED | `precision_three_plate`, `cap_tol_10um`, `gp_whisker_forming` |

**27 MATCHED, 2 ELSEWHERE, 3 MISSING** out of 32 phase-one capabilities.

---

## Part B: Reverse direction — closure nodes phase one never asked for

Grouped by theme (146 closure nodes total, minus the 6 axioms = 140 scored):

| Group | Representative nodes | Verdict | Why |
|---|---|---|---|
| Math/physics substrate under the axioms | `algebra_symbolic`, `geometry_analytic`, `calculus`, `newtonian_mechanics`, `thermodynamics_theory`, `discharge_xray`, `statistics_basic` | REASONABLE | phase one folded these into the `em_theory`/`quantum_solidstate_theory` axioms as instructed; the real tree just expands the same ground into separate nodes |
| Precision machine-tool bootstrap chain | `prc_treadle_lathe_flywheel`, `prc_slide_rest_simple`, `prc_change_gears_quadrant`, `screw_lathe`, `boring_mill`, `prc_milling_machine`, `prc_dividing_head`, `interchangeable_parts`, `prc_gauge_blocks_johansson`, `cap_tol_*` ladder | REASONABLE | phase one's "precision machining" and "fine mechanical adjustment" buckets cover the same ground at coarser grain |
| Ferrous metallurgy chain | `charcoal_industrial`, `bellows_water_blown`, `blast_furnace`, `finery_puddling`, `coal_coke`, `crucible_steel`, `cementation_steel`, `case_hardening`, `refractory_fireclay`, `mt2_silica_brick_refractory`, `mt2_basic_converter`, `mat_bulk_steel` | REASONABLE | coarser bucket in phase one ("hardened tool steel", "refractory materials") |
| Zinc / lead / mercury metallurgy | `zinc_metal`, `zinc_industry_scale`, `lead_metallurgy`, `mercury_supply` | REASONABLE | needed for germanium-as-zinc-byproduct (which phase one predicted by name alone) and for lead/mercury in the galena and vacuum-pump chains |
| Battery/electrochemistry detail | `crude_cell`, `daniell_cell`, `voltaic_pile`, `electroplating`, `electromagnet` | REASONABLE | phase one's single "battery" bucket covers this ground |
| Local power generation ladder | `crank_conrod`, `water_power_scale`, `steam_atmospheric`, `steam_watt`, `steam_high_pressure`, `cap_power_muscle/water/steam/electric` | REASONABLE | needed to eventually motorize machine tools and furnaces; phase one's "electric motor technology" bucket assumed this substrate without naming it |
| National electrical grid distribution | `power_grid`, `en_transformer`, `en_switchgear`, `en_transmission_line`, `en_substation`, `en_insulator`, `en_circuit_breaker`, `en_frequency_standardisation`, `pwr_high_voltage_transmission`, `arc_furnace_ferroalloys`, `cap_power_grid`, `cap_heat_3000` | QUESTIONABLE | this entire distribution buildout exists only to feed one electric arc furnace (`arc_furnace_ferroalloys`) on the path to `zone_refining`. Real electrometallurgical arc furnaces ran off local/on-site generation (`cap_power_electric`, already in the closure) without needing grid-scale transmission, substations, or frequency standardization. This reads as an existing over-specification in the tree, not a phase-one miss |
| Vacuum/glass/optical instrument chain | `barometer`, `vacuum_pumps`, `diffusion_pump`, `glass_clear`, `glass_borosilicate`, `fused_quartz`, `mirror_amalgam`, `telescope`, `lens_grinding`, `spectroscope`, `balance_analytical`, `thermometer` | REASONABLE | matches phase one's vacuum-tube and chemistry buckets; `spectroscope`/`telescope`/`mirror_amalgam` specifically support trace germanium detection and X-ray optics, a refinement phase one didn't itemize but agrees with on reflection |
| X-ray crystallography | `discharge_xray`, `in2_xray_diffraction_camera`, `in2_electron_source_cathode` | REASONABLE | confirms the grown boule really is single-crystal (Bragg geometry) — sound practice phase one didn't think to name |
| Narrative/setting nodes | `identity_cover`, `patron_local`, `workshop_first` | REASONABLE (setting-specific) | not derivable from the physics of a transistor at all, but sensible once you know the premise is a secret founder inside Roman society who needs cover, patronage, and an institutional base |

---

## Part C: Summary table

| Category | Count |
|---|---|
| Phase-one capabilities: MATCHED | 27 |
| Phase-one capabilities: ELSEWHERE | 2 |
| Phase-one capabilities: MISSING | 3 |
| Phase-one capabilities: total | 32 |
| Reverse-direction node groups: REASONABLE | 8 groups (~130 nodes) |
| Reverse-direction node groups: QUESTIONABLE | 1 group (~10 nodes: electrical grid distribution) |
| Goal closure size (via `pre`) | 146 nodes |
| Axioms noted, not scored | 6 |

---

## Part D: Prioritized MISSING list with marginal cost

Marginal cost = size of (closure of the proposed new node) minus (nodes already
in `point_contact_transistor`'s existing 146-node closure).

**1. HIGH — Optical magnification to place the whisker.** `gp_whisker_forming`'s
own note says the two points are set "a few hundredths of a millimetre apart";
nothing in its closure lets anyone see that gap. Add `microscope_compound` as a
new prerequisite of `gp_whisker_forming` (or of `point_contact_transistor`
directly). `microscope_compound` depends on `glass_bead_microscope`,
`precision_three_plate` (already in closure) and `telescope` (already in
closure); `glass_bead_microscope` depends only on `lens_grinding` (already in
closure). **Marginal cost: 2 nodes** (`glass_bead_microscope`,
`microscope_compound`).

**2. MEDIUM — Chemical/electrolytic surface etch, separate from mechanical
lapping.** The real 1947 process combined lapping with an electrolytic etch to
set the final rectifying surface; the tree's closure has only
`prc_lapping_plate`. Add `el2_electropolishing_etching_surface_finish` as a new
prerequisite of `gp_whisker_forming` alongside `prc_lapping_plate`. It depends
on `el2_electroplating_and_electrorefining`, which depends on `electroplating`
(already in closure). **Marginal cost: 2 nodes**
(`el2_electroplating_and_electrorefining`,
`el2_electropolishing_etching_surface_finish`).

**3. LOW — Contact-alloy sourcing wired in as real prerequisites instead of
bare material costs.** `gold_g` and `phosphor_bronze_g` are charged as material
costs on `point_contact_transistor`/`gp_whisker_forming` but neither traces to
a gating tech node. For gold: wire the existing orphan `mat_gold` in as a
prerequisite of `point_contact_transistor` (**marginal cost: 1 node**). For
phosphor bronze: add a new `phosphor_bronze_alloy` node as a prerequisite of
`gp_whisker_forming`, depending on `mat_copper` (already in closure) plus new
`mat_tin` (zero-prerequisite) and new `chm_phosphorus_extraction` (depends only
on `cap_heat_1300`, already in closure). **Marginal cost: 3 nodes**
(`phosphor_bronze_alloy`, `mat_tin`, `chm_phosphorus_extraction`). Combined
marginal cost for both halves of item 3: **4 nodes**.
