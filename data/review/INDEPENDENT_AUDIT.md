# Independent audit of 70 sampled nodes

## Verdict

The sample is uneven. About half the 70 nodes are sound in isolation: their listed prerequisites, materials and costs are internally consistent with what the note itself describes, and I found nothing wrong with them. The other half fail at least one test, and the errors cluster into two families rather than being randomly scattered. The single dominant error is a **capability prerequisite that does not match the physics or chemistry of the thing being built** - most often a heat rung (`cap_heat_1300`, `cap_heat_1600`) or a tolerance rung (`cap_tol_100um`) bolted onto a node whose own note describes a room-temperature chemical reaction, a paperwork/theory exercise, or an institutional programme with no machining in it at all. Eight nodes in the sample carry an explicit `[AUDIT: ... inferred by rome/sim/treetool.py repair, not stated by the author]` tag, and every one of the eight that I checked (`chm_gelignite`, `civ_dam_arch`, `com_binary_arithmetic`, `lnd_steering_geometry`, `mercury_supply`, `plague_preparedness`, `sea_charts_navigation`, `tex_mercerisation`) turned out to be wrong - a 100% failure rate on the auto-repaired capability floors in this sample. That is the single most actionable finding in this audit: the repair script's heuristic for inferring capability floors is not trustworthy and everything it touched should be reviewed by a human, not just in this sample but tree-wide. The second-largest class is missing chemical reagents and materials that the node's own note names but the prerequisite list omits - nitric acid for nitration (twice, in two different nodes, once wrongly and once rightly needed elsewhere), formaldehyde for Bakelite, soda ash for synthetic detergent, calcite instead of glass for a Nicol prism, a photoemissive alkali metal for a photocell. A smaller but real class is backwards or category-confused prerequisites (mercury needing vacuum technology that mercury itself is what makes possible; a stirrup needing a horse collar) and two outright tier inversions (a tier-2 node depending on a tier-3 node; a tier-1 node depending on a technology, blast-furnace cast iron, that is a major independent metallurgical leap).

## Findings

### chm_aniline (severity: HIGH)
- **Test failed:** Missing prerequisite; wrong prerequisite
- **Finding:** The note says "oleum nitrates benzene to nitrobenzene" - nitration of benzene requires nitric acid (mixed with sulfuric acid/oleum), and no nitric-acid technology is listed. Meanwhile `industrial_gases` (bulk O2/H2) is listed but the note's own reduction step uses iron powder in dilute acid (Béchamp reduction), not catalytic hydrogenation, so the hydrogen gas prerequisite is not actually used by the process described.
- **Fix:** Add `nitric_acid` as a prerequisite. Drop or justify `industrial_gases`; it is not used by the Béchamp route the note describes.

### chm_bakelite (severity: HIGH)
- **Test failed:** Missing prerequisite
- **Finding:** The note states plainly that "phenol and formaldehyde condense" to form the resin, but only `chm_phenol` is listed. Formaldehyde (`mat_formaldehyde`, tier 4 - meaning it is not free, it needs its own production chain) is completely absent from both `pre` and `mat`.
- **Fix:** Add the technology that yields `mat_formaldehyde` (methanol oxidation from destructive distillation) as a prerequisite, and add `mat_formaldehyde` to materials.

### chm_detergent_synthetic (severity: HIGH)
- **Test failed:** Missing prerequisite
- **Finding:** The note says the sulfonic acid "is neutralised with soda ash" and the process is sulfonation of cracked alkenes. Neither a soda-ash source nor a sulfuric-acid source is listed as a prerequisite or a material, even though comparable nodes in this same sample (e.g. `met_galvanizing`) do list `sulfuric_acid_kg` explicitly when it is used.
- **Fix:** Add `soda_leblanc` as a prerequisite, and add `sulfuric_acid_kg` to materials (or a sulfuric-acid source tech such as `lead_chamber`) for the sulfonation step.

### chm_gelignite (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1300` (sustained 1300 C blast-furnace-grade heat) was auto-inferred and attached to this node, but gelignite manufacture as the note itself describes it - dissolving nitrocellulose in nitroglycerin with acetone or diethyl phthalate - is a room-temperature compounding operation. No heat capability of this kind is used anywhere in the process.
- **Fix:** Remove `cap_heat_1300`. If any capability floor is wanted here it would be a solvent-handling/ventilation one, not a heat rung.

### com_analytical_engine (severity: HIGH)
- **Test failed:** Missing prerequisite
- **Finding:** The note explicitly says the machine "was never built (same tolerance problems as the Difference Engine)" - yet no tolerance capability or `interchangeable_parts` appears anywhere in `pre`. A machine with thousands of precision gears and rods cannot be built by "same tolerance problems" hand-waving with zero tolerance prerequisite listed, especially when the much simpler `com_comptometer` in this same sample correctly lists `interchangeable_parts`.
- **Fix:** Add `cap_tol_100um` at minimum (arguably `interchangeable_parts`, matching `com_comptometer`'s own convention).

### com_binary_arithmetic (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1600` (regenerative-preheat furnace heat) was auto-inferred onto a node whose labour is 250 scholar-hours, whose material is 40 sheets of parchment, and whose content is purely the abstract number system and its arithmetic rules. There is no furnace, metal, or heat process anywhere in this node.
- **Fix:** Remove `cap_heat_1600` entirely. It has no bearing on a paperwork/theory node.

### hom_stove_enclosed (severity: HIGH)
- **Test failed:** Missing prerequisite; factually wrong implication
- **Finding:** The material list includes `cast_iron_kg: 40`, but this is tier 1 (the earliest tier) and no cast-iron or blast-furnace technology is listed as a prerequisite anywhere. Cast iron requires reducing ore in a blast furnace at sustained high heat; it is not something a hand-blown-charcoal-level tier-1 economy has "just lying around." This is exactly the kind of error the brief calls out: implicitly giving Rome cast iron in the West without earning it.
- **Fix:** Add `blast_furnace` as a prerequisite (matching how `met_cupola_furnace` correctly cites it elsewhere in this sample), or substitute `mat_wrought_iron` for the cast-iron sheet/box construction if the tier really is meant to be that early.

### hot_air_balloon (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** The listed prerequisites are `rag_paper` and `distillation_alcohol`, but the node's own note says "Linen sized with oil is the envelope; Rome has excellent sailcloth" - no paper appears anywhere in the materials (`linen_kg`, `olive_oil_kg`, `firewood_kg` only) or in the described construction, and the heat source is a wood fire (`firewood_kg: 8000`), not an alcohol burner. Neither prerequisite is actually used by the recipe as written.
- **Fix:** Remove `rag_paper` and `distillation_alcohol`. Neither is load-bearing for an oiled-linen, wood-fire-heated balloon; if anything is needed it is a textile-sizing/waterproofing craft note, which is already tier-0 (`mat_olive_oil`, `mat_linen`).

### lnd_stirrup (severity: HIGH)
- **Test failed:** Wrong prerequisite; missing prerequisite
- **Finding:** `horse_collar` (rigid padded collar, whippletree, nailed horseshoe) is listed as a prerequisite, but the stirrup and the horse collar are historically and functionally unrelated - one is a draft-harness efficiency device for pulling loads, the other is a mounted-rider balance device. A stirrup is a metal loop hung from a saddle strap; what it actually needs and does not have listed is a proper riding saddle.
- **Fix:** Remove `horse_collar`. Add a saddle-construction prerequisite (if one exists elsewhere in the tree); `mat_wrought_iron` (already listed) and `mat_leather`/saddle craft are the real inputs.

### med_aspirin (severity: HIGH)
- **Test failed:** Factually wrong note; wrong prerequisite; missing prerequisite
- **Finding:** Aspirin is made by acetylating salicylic acid with acetic anhydride (or acetyl chloride) - not by any reaction involving nitric acid. Nitration of salicylic acid does not produce acetylsalicylic acid; it produces nitro-substituted aromatic compounds. `nitric_acid` is simply the wrong reagent for this synthesis, and no acetylating agent (acetic anhydride) is listed at all.
- **Fix:** Replace `nitric_acid` with a prerequisite that yields acetic anhydride (acetic acid distillation/anhydride formation). `nitric_acid` should be removed from this node.

### mercury_supply (severity: HIGH)
- **Test failed:** Wrong prerequisite; backwards causal direction
- **Finding:** `cap_vac_1torr` (rough vacuum, piston pump) was auto-inferred as a prerequisite for extracting mercury from cinnabar, but the note itself describes simple retort roasting of cinnabar with condensation of the vapour - an atmospheric-pressure thermal process needing no vacuum equipment at all. Worse, the causal order is backwards: the tree's own vocabulary and this node's note both note that mercury is what *enables* the first hard vacuum (barometers, Sprengel pumps), not the other way around.
- **Fix:** Remove `cap_vac_1torr`. If a heat capability is wanted, `cap_heat_0700` or `cap_heat_1100` (roasting/retort temperatures) is the right family, not a vacuum rung.

### opt_nicol_prism (severity: HIGH)
- **Test failed:** Missing/wrong material
- **Finding:** The note correctly describes a Nicol prism as cut from "Calcite (Iceland spar) crystal," but the material listed is `glass_raw_kg: 0.8`. Glass is not birefringent in the way calcite is and cannot be substituted for it; the material listed contradicts the note's own physics.
- **Fix:** Replace `glass_raw_kg` with a calcite/Iceland-spar material line (not currently in the shared vocabulary materials table - this itself is a gap worth flagging to the vocabulary maintainers).

### plague_preparedness (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_tol_100um` (0.1 mm machining tolerance) was auto-inferred onto a public-health institution node - quarantine, clean water, sanitation, variolation. Nothing in this programme involves precision machining; its labour is 2500 scholar-hours and 6000 labourer-hours, and its materials list is empty.
- **Fix:** Remove `cap_tol_100um`. It has no bearing on a quarantine/sanitation programme.

### prc_lathe_faceplate (severity: HIGH)
- **Test failed:** Missing prerequisite
- **Finding:** A faceplate is a fixture that "bolts to spindle nose" of a lathe, per the node's own note - but no lathe (`screw_lathe` or any earlier lathe technology) is listed as a prerequisite anywhere. The entire premise of the device presupposes a working lathe already exists. `crank_conrod` is listed instead, which has no obvious connection to a cast-iron mounting plate; separately, crank-and-connecting-rod mechanisms are not well attested in Rome before roughly the 3rd century AD (the Hierapolis sawmill relief), which is worth checking against whatever calendar floor tier 1 represents in the full tree.
- **Fix:** Add a base lathe technology (e.g. `screw_lathe`, or whatever earlier lathe node exists in the full tree) as a prerequisite. Reconsider whether `crank_conrod` belongs here at all.

### prc_lead_screw_error_cam (severity: HIGH)
- **Test failed:** Wrong tier
- **Finding:** This node is tier 2, but one of its listed prerequisites, `prc_profile_projector`, is tier 3 in this very sample. A node cannot require a strictly more advanced technology than itself; the tier assignment is inverted.
- **Fix:** Either raise `prc_lead_screw_error_cam` to tier 3 (matching `prc_profile_projector`), or replace `prc_profile_projector` with a tier-appropriate measurement prerequisite.

### sea_charts_navigation (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_tol_100um` (0.1 mm machining tolerance) was auto-inferred onto a cartography node whose labour is scholar and scribe hours and whose material is parchment. Drawing and compiling navigation charts by pen and compass rose involves no precision machining.
- **Fix:** Remove `cap_tol_100um`.

### tex_mercerisation (severity: HIGH)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1300` was auto-inferred onto a process the note itself describes as treating cotton with sodium hydroxide "under tension" - mercerisation is done cold or barely warm; it needs no sustained 1300 C heat of any kind.
- **Fix:** Remove `cap_heat_1300`.

### air_pitot_tube (severity: MEDIUM)
- **Test failed:** Wrong tier
- **Finding:** This is tier 1, but its only prerequisite is `barometer` ("Mercury barometer, and the first hard vacuum"). Elsewhere in this same sample, `mercury_supply` - the node that secures the mercury a barometer needs - is tier 2. A tier-1 node should not depend on a technology whose own input chain sits at tier 2.
- **Fix:** Either raise `air_pitot_tube` to tier 2, or confirm `barometer`'s tier independently is genuinely achievable at tier 1 (unlikely given the mercury dependency).

### air_rotary_engine (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** A WWI-era rotary aero engine spins the entire cylinder block at high RPM and depends on tight dynamic balance to avoid tearing itself apart; the listed `cap_tol_100um` (0.1 mm) is the same tolerance rung already used for the much less demanding stationary `lnd_otto_cycle_four_stroke`. `lnd_spark_plug`, a far simpler part, already requires `cap_tol_10um` in this sample.
- **Fix:** Add `cap_tol_10um`.

### chm_cyanamide_fixation (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** The note describes making calcium carbide "by arc furnace" - which is exactly what `arc_furnace_ferroalloys` ("Electric arc furnace, carbides and ferroalloys") covers in the shared vocabulary, yet it is not listed; only the generic `cap_heat_3000` capability rung is cited.
- **Fix:** Add `arc_furnace_ferroalloys` as a prerequisite.

### civ_dam_arch (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1300` was auto-inferred, but the only material this node consumes is `lime_kg: 80` - lime burning runs at roughly 900-1000 C, well within `cap_heat_1100`. Nothing in an arch dam's construction (masonry, mortar, geometry) calls for blast-furnace-grade heat.
- **Fix:** Remove `cap_heat_1300`, or replace with `cap_heat_1100` if a heat floor is wanted at all.

### fud_hay_making_storage (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** `crop_rotation` ("Legume rotation, heavy plough, marling, selective breeding") is listed as a prerequisite for hay-making, but cutting and dry-storing grass is an ancient, independent practice (the Latin *foenum* predates any of the medieval agricultural-revolution package this prerequisite represents) and does not depend on rotation schemes, heavy ploughs, or selective breeding.
- **Fix:** Remove `crop_rotation`. Hay-making needs cutting tools (already tier 0) and dry storage, which is what this node's own materials (`timber_m3: 5` for a barn) already cover.

### fud_soil_composition_analysis (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** The note describes testing "soil pH, organic matter, and nutrient content via chemical analysis" - genuine quantitative chemical testing - but the only prerequisite is `fud_agricultural_treatises` (written knowledge codification). The shared vocabulary has `analytical_chemistry` ("Gravimetric and volumetric analysis") for exactly this kind of work, and it is not cited.
- **Fix:** Add `analytical_chemistry` as a prerequisite.

### lnd_steering_geometry (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1300` was auto-inferred onto what the note itself describes as pure kinematic linkage design ("this geometry is counterintuitive but essential"). Ackermann steering geometry is a layout problem, not a metallurgical one; the forged linkage arms it produces need at most `cap_heat_1100` to make, and arguably a tolerance capability matters more than a heat one for correct turning angles.
- **Fix:** Remove `cap_heat_1300`; if anything, add `cap_tol_1mm` or `cap_tol_100um` for the linkage geometry itself.

### med_autoclave (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** This node's `cap_heat_1300` was author-specified (not tool-inferred), but the note describes an autoclave operating at "120 C for 15 minutes." Sustained 1300 C blast-furnace heat has nothing to do with sterilizing at 120 C; if any heat capability belongs here it is for forging the pressure vessel's steel, which is already covered transitively by the listed `steam_high_pressure` -> `bessemer_openhearth` chain.
- **Fix:** Remove `cap_heat_1300` as a direct prerequisite of this node; it is redundant with what `steam_high_pressure` already implies.

### met_cupola_furnace (severity: MEDIUM)
- **Test failed:** Wrong tier
- **Finding:** This node is tier 1 (the earliest tier) yet requires `blast_furnace` ("Tall shaft blast furnace and cast iron") as a prerequisite - a major, non-trivial metallurgical leap in its own right, not something that belongs at the very start of the tree alongside basic hand crafts.
- **Fix:** Raise `met_cupola_furnace` to at least the same tier as `blast_furnace`, or later.

### met_galvanizing (severity: MEDIUM)
- **Test failed:** Wrong prerequisite; redundant prerequisite
- **Finding:** Two issues. First, `pre` lists both `mat_zinc` (a materials-table id, "Zinc metal") and `zinc_metal` (the actual technology, "Zinc metal by downward distillation") - these name the same underlying capability twice under two different id namespaces. Second, `cap_heat_1300` is far more heat than a zinc dip bath needs: zinc melts at 420 C and a galvanizing bath runs around 450-460 C, well inside `cap_heat_0700`.
- **Fix:** Drop `mat_zinc` from `pre` (it is already covered by `zinc_metal`). Replace `cap_heat_1300` with `cap_heat_0700`.

### met_roasting_calcining (severity: MEDIUM)
- **Test failed:** Internally inconsistent note
- **Finding:** The note ends "Needs a scholar to understand stoichiometry or roasters waste half their ore," but the labour list is `furnaceman: 150, labourer: 100` - zero scholar hours, and no theory prerequisite is listed either. The note asserts a requirement the node's own fields do not provide.
- **Fix:** Either add scholar hours and a chemistry-theory prerequisite, or remove the stoichiometry claim from the note - ancient roasters worked by empirical craft knowledge, not formal stoichiometry (a term that postdates Richter, 1792, and is anachronistic for a tier-1 node).

### opt_photocell (severity: MEDIUM)
- **Test failed:** Missing material
- **Finding:** The note says "Cesium or other photoemissive surface in vacuum emits electrons when light strikes," but no alkali-metal material appears in `mat` (only `copper_kg: 0.5`). Elsewhere in this sample, exotic/rare inputs are tracked explicitly when used (e.g. `com_semiconductor_diode` lists `germanium_g`, `indium_g`, `gold_g`) - this node breaks that convention.
- **Fix:** Add a cesium or alkali-metal material line to `mat`.

### opt_pyrometer_radiation (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** The note says radiation "focuses... onto bolometer or photocell," but neither `opt_photocell` nor any bolometer technology is listed as a prerequisite - only the abstract `cap_measure_elec` and `thermodynamics_theory`.
- **Fix:** Add `opt_photocell` as a prerequisite (or a bolometer-equivalent if one exists elsewhere in the tree).

### opt_stroboscope (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** `photography` is listed as a prerequisite, but the note describes the device purely as a visual RPM instrument - "rotating disk or electric lamp flash synchronized to object rotation... measuring RPM directly" - with no camera or film involved anywhere. The mechanical rotating-disk stroboscope (Plateau/Stampfer, 1832) long predates photography and needs neither photographic technology nor, for the disk variant, electric power.
- **Fix:** Remove `photography`. Keep `cap_power_electric` only if the intended variant is specifically the electric-flash version.

### prc_broach_machine (severity: MEDIUM)
- **Test failed:** Wrong tier of capability listed
- **Finding:** The note states the machine "Requires 0.05mm tooth accuracy," but the listed capability is `cap_tol_100um` (0.1 mm) - a capability that by definition does not guarantee 0.05 mm precision. The note's own number falls below what the cited prerequisite can deliver.
- **Fix:** Cite `cap_tol_10um` (0.01 mm) instead, which comfortably covers the stated 0.05 mm need.

### prc_honing_machine (severity: MEDIUM)
- **Test failed:** Wrong tier of capability listed
- **Finding:** The note claims the process "Produces 0.5 micron finish," but the listed capability is `cap_tol_10um` (10 micron) - twenty times coarser than the claimed output.
- **Fix:** Cite `cap_tol_1um` (1 micron, "lapping, grinding, optical flats") instead of `cap_tol_10um`.

### pwr_selenium_metal (severity: MEDIUM)
- **Test failed:** Wrong prerequisite
- **Finding:** `cap_heat_1300` is author-specified here, but the note describes "roasting and selective reduction" of a trace element from copper ore, which is a low-temperature roasting operation (typically 500-700 C), not a blast-furnace-grade process.
- **Fix:** Replace `cap_heat_1300` with `cap_heat_0700` or `cap_heat_1100`.

### sea_steam_turbine (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** A steam turbine depends on tight blade-to-casing clearances to avoid excessive leakage and rubbing at high rotational speed. The listed `cap_tol_100um` (0.1 mm) is the same rung used elsewhere in this sample for much less demanding stationary engine work; the much simpler `prc_cylindrical_grinder` and `prc_honing_machine` in this same sample both require `cap_tol_10um` for comparable rotating-machinery fits.
- **Fix:** Add `cap_tol_10um`.

### spectroscope (severity: MEDIUM)
- **Test failed:** Missing prerequisite
- **Finding:** The node is named "Prism and grating spectroscope," but ruling a diffraction grating (thousands of precisely equal, evenly spaced parallel lines) is a much harder precision-manufacturing problem than grinding a prism, historically requiring specialized ruling engines (Rowland, 1880s). No tolerance capability is listed at all.
- **Fix:** Add `cap_tol_10um` at minimum (arguably `cap_tol_1um`) if the grating variant is meant to be covered by this node.

### med_gram_stain_culture (severity: LOW)
- **Test failed:** Missing material
- **Finding:** The note describes "Petri's shallow agar dishes" for bacterial culture, but no culture-medium material (agar, or an earlier gelatin-based alternative) appears in `mat`, only glass and dye.
- **Fix:** Add an agar or gelatin material line to `mat`.

## Nodes I checked and found sound

air_aerodrome, air_dirigible_engine_mount, air_wing_warping, chm_filter_press, civ_method_joints, com_amplitude_modulation, com_comptometer, com_semiconductor_diode, com_superheterodyne_receiver, freedman_staff, fud_distillation_spirits, lnd_otto_cycle_four_stroke, lnd_spark_plug, lnd_truck, met_drawn_tube, met_open_hearth_furnace, met_wire_rod_rolling, opt_abbe_resolution_theory, opt_plano_convex_lens, opt_standards_laboratory, prc_autocollimator, prc_cylindrical_grinder, prc_profile_projector, prn_composing_stick, prn_woodblock_carving, pwr_rotary_drilling, pwr_trompe, sea_backstaff, sea_log_line, sea_skeleton_first, steam_high_pressure, tex_chlorine_bleaching, tex_spinning_jenny

## Systematic patterns

1. **Auto-repaired capability floors are unreliable.** Eight nodes in this sample carry the `[AUDIT: capability prerequisite(s) ... inferred by rome/sim/treetool.py repair, not stated by the author]` tag, and all eight, on inspection, cited a capability that does not match the physics of the node: a heat rung on a room-temperature chemical process (`chm_gelignite`, `tex_mercerisation`), a heat rung on a pure paperwork/theory node (`com_binary_arithmetic`), a heat rung on a masonry/geometry node that does not need it (`civ_dam_arch`, `lnd_steering_geometry`), a vacuum rung on an atmospheric-pressure thermal process with the causality backwards (`mercury_supply`), and a machining-tolerance rung on institutional/paperwork nodes with no machining at all (`plague_preparedness`, `sea_charts_navigation`). Given a 100% failure rate on the sample checked, every auto-repaired capability floor tree-wide should be treated as unverified and reviewed by hand, not treated as a defensible floor as the notes themselves currently ask the reader to do.
2. **Author-specified heat rungs also skew high.** Two nodes not flagged by the repair tool (`med_autoclave`, `pwr_selenium_metal`) independently cite `cap_heat_1300` for processes that run at a few hundred degrees. This suggests the authors themselves, not just the repair script, have a tendency to reach for `cap_heat_1300` as a generic "this is an industrial process" marker rather than matching the rung to the actual operating temperature.
3. **Notes assert requirements the prerequisite list does not provide.** `com_analytical_engine` blames its historical failure on "tolerance problems" but lists no tolerance capability; `met_roasting_calcining` says it "needs a scholar" but allocates zero scholar hours and no theory prerequisite; `prc_broach_machine` and `prc_honing_machine` both state a precision figure in their own note that is finer than the capability rung actually cited. These are self-contradictions checkable from the node's own text, independent of any outside knowledge, and worth a mechanical pass (grep every note for a numeric tolerance and diff it against the cited `cap_tol_*` rung).
4. **Reagents named in the note but absent from the prerequisite/material list**, specifically for named-reaction chemistry nodes: nitric acid (`chm_aniline`, `med_aspirin`), formaldehyde (`chm_bakelite`), soda ash (`chm_detergent_synthetic`), the correct raw material itself (calcite vs. glass in `opt_nicol_prism`). This looks like a pattern of writing an accurate descriptive note and then not tracing every named reagent back into the prerequisite/material fields.

## What I could not assess

- The full 1,179-node tree was not available, only this 70-node sample plus the shared vocabulary. Several findings above (e.g. `com_analytical_engine`'s missing tolerance capability, `prc_lathe_faceplate`'s missing lathe) assume the gap is real at the node level; it is possible, though I judge it unlikely given the instruction to judge each node in isolation, that an un-sampled sibling node supplies the missing piece through a different mechanism I cannot see.
- I do not know exactly what the `tier` field's absolute calendar meaning is (I inferred ordering only from tier-to-tier comparisons within the sample), nor what `yrs` measures precisely (development duration vs. calendar floor) - `steam_high_pressure`'s note suggests `yrs` sometimes encodes calendar diffusion time rather than build time, which I could not verify against other nodes.
- None of the 70 sampled nodes touch natural rubber, gutta percha, quinine, or New World crops, so I could not check how the tree handles those specific historically-flagged materials.
- I could not verify the tiers of prerequisite technologies named but not themselves included in the sample (`barometer`, `blast_furnace`, `com_difference_engine`, `crank_conrod`, and others) beyond what the shared vocabulary's plain-text descriptions imply; tier-inversion findings that depend on those (`air_pitot_tube`, `met_cupola_furnace`) are argued from the vocabulary's descriptions and from other sampled nodes' tiers, not from a direct reading of the un-sampled node's own tier field.
- Cost and hour magnitudes (test 4) were largely unremarkable in this sample once the capability/material errors above are set aside; I did not find a clean factor-of-five-or-more cost outlier that was not already explained by a capability or material mismatch, so no separate "wrong cost" findings are listed. This may reflect real soundness in costing, or it may reflect that I lack a reliable outside reference for what a Roman-to-modern tech tree should charge in its abstracted currency and hour units.

---

# RESOLUTION (added by the project author after reading this audit)

## The headline finding was accepted in full

> "Eight nodes in the sample carry an explicit `[AUDIT: ... inferred by
> rome/sim/treetool.py repair]` tag, and every one of the eight turned out to be
> wrong: a 100% failure rate on the auto-repaired capability floors."

That is correct and it is the most useful thing in this document. My repair
script inferred capability prerequisites by matching keywords against each
node's prose. Keyword matching over prose cannot infer physics. It attached a
1300 C blast furnace rung to a room-temperature gelignite compounding step, a
1600 C furnace to a pure paperwork node about binary arithmetic, and a vacuum
rung to mercury extraction, which is backwards, because mercury is what makes
vacuum technology possible.

**Actions taken:**

1. **All 112 auto-inferred capability edges have been reverted tree-wide**, not
   just the eight in the sample. If the sampled error rate was 100%, the
   population error rate is not something to argue about.
2. **Capability inference is now OFF BY DEFAULT** in `treetool.py repair`. It
   survives only behind an explicit `--infer-caps` flag whose help text says
   what it did. The default behaviour is now to COUNT the gaps and leave them
   visible.
3. Every node that lost an inferred edge now carries this in its note:
   *"This node does not declare the capability rung it needs. An automated pass
   once inferred one, and an independent review found that EVERY inferred rung it
   sampled was wrong, so all of them were reverted. The gap is left visible on
   purpose: a missing prerequisite you can see beats a wrong one you cannot."*
4. The 318 nodes with a genuine capability gap were then handed to five
   reviewers to assign **by judgement, one node at a time**, with the specific
   failure modes above written into their brief as things not to repeat.
5. The project's own audit score fell from 98.0 to **93.1** when the false edges
   were removed. That drop is the honest number and it is recorded as such.

## Every specific finding, and what was done

| Node | Finding | Action |
|---|---|---|
| `chm_aniline` | nitration needs nitric acid, not listed; `industrial_gases` not used by the Bechamp route | added `nitric_acid`, removed `industrial_gases` |
| `chm_bakelite` | formaldehyde named in the note, absent from prerequisites and materials | added `mat_formaldehyde` and 200 kg of formaldehyde |
| `chm_detergent_synthetic` | sulfonation and neutralisation reagents both missing | added `soda_leblanc` and sulfuric acid |
| `chm_gelignite` | 1300 C rung on a room-temperature compounding step | reverted |
| `com_analytical_engine` | note says Babbage failed on tolerance; node declared no tolerance rung | added `interchangeable_parts` and `cap_tol_100um` |
| `com_binary_arithmetic` | 1600 C furnace rung on a paperwork node | reverted |
| `hom_stove_enclosed` | 40 kg of cast iron at tier 1, with no blast furnace | raised to tier 2, added `blast_furnace` and `mat_cast_iron` |
| `hot_air_balloon` | paper and distilled spirits listed, neither load-bearing | both removed |
| `lnd_stirrup` | depended on the horse collar, an unrelated draught technology | removed; added the saddle, which was the real missing input |
| `med_aspirin` | acetylation needs acetic anhydride, not nitric acid | nitric acid removed, wood distillation added |
| `mercury_supply` | vacuum rung, which reverses the dependency | reverted |
| `opt_nicol_prism` | built from glass; a Nicol prism is cleaved calcite and glass cannot substitute | material changed to calcite, which was also added to the price list |
| `plague_preparedness` | 0.1 mm tolerance rung on a quarantine programme | reverted |
| `prc_lathe_faceplate` | listed no lathe at all | added the treadle lathe |
| `prc_lead_screw_error_cam` | tier 2 depending on a tier 3 instrument | raised to tier 3 |
| `sea_charts_navigation`, `tex_mercerisation`, `civ_dam_arch`, `lnd_steering_geometry` | inferred rungs, all wrong | reverted; `lnd_steering_geometry` given `cap_tol_100um`, which is the right one |
| `air_pitot_tube` | tier below its barometer dependency | raised to tier 2 |
| `air_rotary_engine`, `sea_steam_turbine`, `spectroscope` | no tolerance rung declared | `cap_tol_10um` added to each |
| `chm_cyanamide_fixation` | cyanamide runs through calcium carbide, which needs the arc furnace | added `arc_furnace_ferroalloys` |
| `fud_hay_making_storage` | depended on crop rotation, which is unrelated | removed |
| `fud_soil_composition_analysis` | quantitative analysis with no analytical chemistry | added `analytical_chemistry` |
| `med_autoclave` | heat rung redundant with high pressure steam | removed |
| `met_cupola_furnace` | tier 1 depending on the blast furnace | raised to tier 2 |
| `met_galvanizing` | blast furnace rung for a 450 C zinc bath; zinc listed twice | corrected to `cap_heat_0700`, duplicate removed |
| `met_roasting_calcining` | "stoichiometry" is anachronistic for tier 1 (Richter is 1792) | reworded to empirical craft proportion |
| `opt_photocell` | photoemissive surface with no alkali metal | caesium added, and priced |
| `opt_pyrometer_radiation` | needed a detector | `opt_photocell` added |
| `opt_stroboscope` | depended on photography; a mechanical stroboscope is a slotted disc | removed |
| `prc_broach_machine` | cited 0.1 mm for a stated 0.05 mm need | corrected to `cap_tol_10um` |
| `prc_honing_machine` | cited 0.01 mm; honing works to a micron | corrected to `cap_tol_1um` |
| `pwr_selenium_metal` | blast furnace rung for a low-temperature process | corrected to `cap_heat_1100` |
| `med_gram_stain_culture` | culture with no medium | agar added, and priced |

Every fixed node carries `[FIXED after independent audit: ...]` in its note.

## What this audit did not cover

70 of 1,176 nodes, about 6%. If the error rate in the sample holds across the
tree, roughly 600 nodes have at least one defect and roughly 280 have a serious
one. **Assume that is true.** This audit is a measurement of the error rate, not
a repair of the tree.
