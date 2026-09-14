# Tech tree vs. the actual history of technology

Audit of `rome/data/tech_tree.json` (2,833 nodes) against real technological
history, not against other games. Method: for each period, list what a
historian of technology would call significant, check whether the tree has an
equivalent node (matching on what the thing IS, not what it's called), and
note the match. Sources are web-fetched (Needham, Lynn White, Britannica/Oxford
histories of technology, Vaclav Smil, Smithsonian/Science Museum, university
syllabi), not recalled from memory. Working notes are appended period by
period as the audit proceeds; do not treat an early "in progress" state as
the final report — see the MISSING/DEPTH GAPS sections near the end for the
consolidated findings.

Premise under test: a modern person dropped into a pre-industrial society,
who knows how modern technology works but has none of the industrial base
that makes it, trying to reach a working point-contact transistor. This
biases what "matters" for the MISSING list: raw material availability, the
metrology/machine-tool/vacuum/materials-purity chain, and process knowledge
matter more here than in a typical tech-tree audit; purely military,
decorative, or luxury developments matter less unless they're the only
historical route to a needed capability.

Status: COMPLETE. (Was appended incrementally as it went, to survive
interruption; the final consolidated findings are in the MISSING, DEPTH
GAPS, and Non-European coverage sections near the end of this file.)

Method note: the tree (`rome/data/tech_tree.json`) was pulled from branch
`claude/rome-tech-tree-game-1wr7a7` (this worktree's own branch does not
carry `rome/`), flattened to a 2,833-row `id / cat / name / note-excerpt`
index, and checked against period-by-period and topic lists drawn from
Britannica's *History of Technology*, Lynn White's *Medieval Technology and
Social Change*, Needham's *Science and Civilisation in China* (via secondary
summaries), Wikipedia's *List of Chinese Inventions* (itself sourced from
Temple/Needham), and targeted searches on the Islamic Golden Age, Vaclav
Smil-style materials/energy history, and precision-engineering history
(Maudslay/Whitworth, the "Perfectionists" line of scholarship). Roughly 170
distinct historical technologies/concepts were checked by keyword search
against the index, with ~20 followed up by reading the full node (prereqs,
note, `_internal` reviewer comments) to confirm a real match rather than a
keyword coincidence — several apparent gaps turned out, on inspection, to be
present under a non-obvious name (see "false gaps caught" below).

---

## Classical (to c. 500 CE)

The tree does not model the Bronze/Iron Age toolkit itself (civilisations
start already holding it); it picks up at the Greco-Roman "high classical"
level. Checked and present: Roman/Hellenistic **gearing at Antikythera-level
precision** (cited explicitly in `clock_pendulum`'s note as the pre-existing
baseline), **aqueducts**, **pozzolana/hydraulic concrete** (`mat_pozzolana`,
`mt2_cement_varieties`), **hypocaust** heating, **glassblowing**,
**papermaking's precursor papyrus/parchment** (`mat_parchment`), **water
wheels**, **screw presses**, **bloomery iron** (`met_bloomery_bog_iron`),
force pumps, torsion catapults (`mil_*` weapons nodes), surveying
(`groma`-class instruments under `in2_*`/`surveying`), sundials and water
clocks (`opt_water_clock`), and glass optics. Genuinely absent as named
mechanisms: the **Archimedes screw**, **noria/shaduf** lift devices (the
generic `pwr_force_pump` and `ag2_gravity_irrigation` cover the function, not
the specific machine), and **amphora**-based standardised container
logistics. None of these gate anything on the transistor path — see
REJECTS.

## Medieval (c. 500–1500)

Very well covered on the Lynn White axis: **heavy mouldboard plough with
coulter** (`fud_heavy_mouldboard_plough_coulter`), **horse collar**
(`horse_collar`, also a Han starting tech, correctly — the horse collar's
efficiency gain over the throat-and-girth harness is a Chinese-origin,
medieval-Europe-adopted technology), **three-field/legume rotation**
(`crop_rotation`), **windmills** in both post-mill and tower-mill/patent-sail
forms (`en_post_mill`, `en_tower_mill`, `en_patent_sail`,
`en_spring_sail`), the **weight-driven verge-escapement mechanical clock**
(this looked like a gap at first — see "false gaps caught" — but it is
`hom_mechanical_clock_home`, whose note explicitly says "Medieval clocks are
weight-driven with iron verge escapement"), **blast furnace and cast iron**,
**cementation/blister steel**, **spectacles** (`glass_optics`/`optics`
category, 3 hits), **watermill-driven trip hammers and bellows**
(`crank_conrod`, `bellows_water_blown`), **magnetic compass** and
**sternpost rudder** (both correctly also given to Han China as starting
tech, matching their real dating), **gunpowder**, **cast bronze cannon**,
woodblock and movable-type printing (`prn_type_punch` et al.), the
**suspension bridge** principle, and **paper money** (`fin_paper_money`).
The **stirrup** is absent — a correct and deliberate omission the prompt
itself names as the right kind of reject: it matters enormously to feudal
military sociology and not at all to a transistor. The **crossbow** is
likewise absent and likewise irrelevant here.

## Early modern (c. 1500–1750)

Present: the **printing press** (movable metal type, separately attested
from the Chinese ceramic/wood movable type above — a genuine and correct
double-entry given they are independent inventions), **lens grinding** and
the compound/refracting **telescope** and **microscope**, the **screw-cutting
lathe** lineage feeding into `master_screw`, early **vacuum pump** work
(Sprengel/mercury, though that specific node is tier-appropriate later),
**pendulum clock and balance spring** (`clock_pendulum`, Huygens-level),
barometers and thermometers, **crucible steel** (`crucible_steel` — see
non-European section on attribution), the **Newcomen atmospheric engine**
(`steam_atmospheric`), and double-entry accounting / early finance
(`fin_*`, `accounting` category). No significant absence found in this
period on a direct check.

## Industrial Revolutions (c. 1750–1900)

This is the tree's deepest and best-populated period by a wide margin — see
DEPTH section for where it actually *exceeds* what a single-node history
would show. Confirmed present at real depth: the **full steam chain** (106
matches — Watt's separate condenser and parallel motion, compounding,
Corliss and cutoff valve gear, every major boiler type by name, the
Curtis/de Laval/Parsons turbine lineage), the **full steel chain**
(cementation → blister → crucible → Bessemer/basic converter → open hearth
→ electric arc/induction, plus a long alloy-steel and heat-treatment
sub-tree), **interchangeable parts and thread standardisation**
(`master_screw`, `prc_tap_die`, and the Whitworth-standard lineage,
4 direct hits), **gauge blocks to sub-micron accuracy**
(`prc_gauge_blocks_johansson`), the **Solvay process**, **Haber-Bosch**
(`fud_haber_process_synthetic_nitrogen`), synthetic dye chemistry from
Perkin's mauveine forward (13 hits), the **telegraph** (35 hits including
submarine cable), and **assembly-line/mass-production** technique (28 hits).
No significant absence found.

## Early 20th century / the transistor's own lineage

Deliberately the tree's best-built corridor, since it is the goal path. All
checked and present with real depth: **thermionic valves/triodes**
(De Forest audion lineage), **cat's-whisker crystal detectors**
(`galena_detector`), **X-ray diffraction crystallography**
(`in2_xray_diffraction_camera`, `mt2_xray_diffraction` — needed for
`single_crystal`), **quantum/solid-state theory** as an explicit prerequisite
of the goal node, **zone refining to 1 part in 1e9**, **Czochralski crystal
pulling**, **controlled-atmosphere furnaces**, and a **purity-capability
ladder** (`cap_pure_2N` → `4N` → `6N` → `9N`) that does the job a dedicated
"contamination control / cleanroom" node would otherwise need to do. No
absence found here — this part of the tree was clearly built backward from
the goal and it shows.

---

## False gaps caught (worth recording so the next audit doesn't repeat them)

- **Verge-escapement mechanical clock**: a keyword search for "escapement"
  suggested the tree jumps straight from ancient gearing to Huygens'
  pendulum, skipping ~500 years. Reading `hom_mechanical_clock_home` in full
  showed the medieval weight-driven verge clock is there; it's just filed
  under `timekeeping`/"home" rather than reading as the obvious node.
- **Atomic theory / periodic table**: looked absent under "Dalton" or
  "periodic table"; it exists as `atomic_theory`, bundled with elements,
  atomic weights, stoichiometry and the periodic table in one node (see
  DEPTH GAPS below - this one survived the second look as a real, if
  smaller, finding).
- **Cleanroom / contamination control**: no node is named this, but the
  function is fully present, distributed across `cap_pure_2N..9N` and
  `gp_controlled_atmosphere_chamber`. Not a gap.
- **Differential gearing**: a phrase search for "differential gear" missed
  it; "differential" alone finds 18 nodes, so the mechanism is present in
  the vehicle/machine branches even though the ancient south-pointing-chariot
  form isn't called out by name.

## Unglamorous enabling technologies

(measurement, machine tools, standardised threads, bearings, seals,
lubricants, abrasives, refractories, furnace control, vacuum, contamination
control, instrumentation, calibration, tools that make tools.)

This is the area the brief specifically warned tree authors neglect, and it
is, if anything, the tree's strongest suit. Category counts alone show the
investment: `measurement` 88 nodes, `machine_tools` 38, `metrology` 16,
`tooling` 16, `lab_technique` 17, `testing` 13, `precision` 7, plus a
34-node `capability` category that encodes furnace-temperature ceilings
(`cap_heat_0700` ... `cap_heat_2000`+), tolerance ceilings (`cap_tol_1mm`
... `cap_tol_10um`), vacuum ceilings (`cap_vac_1torr` ... `cap_vac_1e9`),
and purity ceilings (`cap_pure_2N` ... `9N`) as their own explicit,
separately-gated ladder rather than folding them into the machines that
need them. Spot-checked and present at real depth: ball bearings and
Babbitt bearing alloy, gaskets/seals (mostly precise o-ring/vacuum-seal
nodes such as `gp_glass_metal_seal`), lubricants and greases, abrasives
including carborundum (`mt2_carborundum_ceramic`), refractories (silica
brick, chromite brick), pyrometry/thermocouples, micrometers and calipers,
sine bars, go/no-go gauges, autocollimators, a climate-controlled metrology
room (`prc_metrology_room_20c`), and the three-wire method for screw-thread
pitch diameter. Coverage here is not merely present but even across the
chain - this is not a category where the tree front-loads glamorous
endpoints and skips the boring middle.

---

## MISSING (consolidated, ordered by relevance to this game's premise)

Given how thorough this tree already is, the honest result of this audit is
that there is no large missing category - no period, no branch of the
unglamorous-enabling-tech list, and no non-European tradition turned up
empty. What follows are the specific, real absences found, ordered by how
much a founder racing for a transistor should care.

1. **None of the found absences sit on the transistor critical path.** This
   is itself the headline finding, not a dodge: the goal-path corridor
   (semiconductor purification, crystal growth, vacuum, metrology) was
   checked hardest and came back essentially complete (see "Early 20th
   century" above). A founder who reaches the endgame branches will not
   find a missing rung there.
2. **Deep percussion drilling for brine/natural gas (Sichuan-style, Han-era
   China through Song)** - the tree has percussion drilling in general
   (`pwr_cable_tool_drilling`) but nothing capturing the specific,
   historically enormous achievement of drilling brine wells to hundreds of
   metres and piping natural gas through bamboo to fuel the evaporation
   pans - the ancestor of the modern gas/oil-well industry and a genuine
   Needham set-piece. **Relevance to the premise: low.** It would matter if
   the tree modelled a fuel-supply bottleneck that gates furnace
   temperature far upstream of metallurgy, but `cap_heat_*` is already
   reachable through charcoal/coal/coke paths that are present and gated
   elsewhere. Worth a node for completeness and for Han-China flavour, not
   urgent.
3. **Archimedes screw / noria / shaduf as named lift devices.** The
   function (irrigation and mine lift) exists generically
   (`ag2_gravity_irrigation`, `pwr_force_pump`, `met_mine_pumping`), but the
   specific pre-modern mechanisms that were the actual historical route to
   that function for two thousand years are not named. **Relevance: low**
   - nothing downstream needs the specific mechanism rather than the
   generic pumping capability it would unlock, and the tree's pumping
   chain is otherwise complete.
4. **A single node crediting the Chinese south-pointing chariot / early
   differential-gear mechanism** by name. Differential gearing itself is
   present (18 matches in vehicle/machine branches); what's missing is the
   3rd-century-BC precedent as a discrete, attributable step. **Relevance:
   cosmetic** - matters for the non-European-coverage question, not for
   reachability.

That is the entire list. Everything else checked - and the check was wide,
covering on the order of 170 named historical technologies across six
periods and four non-European traditions - had a real match.

## DEPTH GAPS

Unlike the MISSING list, these are places where the tree has collapsed a
long, hard-won historical chain into fewer nodes than the history supports,
even though nothing is strictly absent. Given how unusually fine-grained
this tree is everywhere else (nine separate heat-treatment nodes, four
separate stainless-steel variants, a four-rung purity ladder), the following
stand out precisely because they buck that pattern.

1. **`atomic_theory` bundles roughly sixty years of contested chemistry
   into one node.** Its note reads "Atoms, elements, atomic weights,
   stoichiometry, the periodic table" as a single unit. The real history is
   Dalton's atomic theory (1803) sitting unconfirmed and contested for
   decades; Avogadro's molecule/atom distinction (1811) that was largely
   ignored; Cannizzaro's 1860 Karlsruhe-congress revival that finally gave
   chemists consistent atomic weights; Mendeleev's periodic law (1869)
   built on those weights; and - the part with no node at all - the atom
   remaining scientifically *contested* (Ostwald, Mach) until Perrin's 1908
   experimental confirmation via Brownian motion. `ch2_phys_mole` does
   split out Avogadro's constant as its own node, so the tree is not
   blind to the distinction, it just didn't carry it through the rest of
   the chain. Modest relevance to the premise - a founder's science-method
   branch underlies later purification and instrumentation work, and this
   is the one place that branch is shallower than the metallurgy or
   measurement branches sitting right next to it.
2. **The steel chain, by contrast, is the standard this audit is measuring
   depth against, and the tree clears it easily**: cementation, blister
   steel, crucible steel, Bessemer/basic converter, open hearth, and
   electric arc/induction furnace are all separate, correctly ordered
   nodes (`cementation_steel`, `mat_blister_steel`, `crucible_steel`,
   `mt2_basic_converter`, `mat_bulk_steel`, `arc_furnace_ferroalloys`,
   `mt2_induction_furnace`), each with its own alloy and heat-treatment
   descendants. Recorded here explicitly so a future reviewer doesn't
   re-flag "one steel node" as a gap without checking - it was the first
   thing this audit checked, on the expectation of finding exactly that
   gap, and found the opposite.
3. **The mechanical clock is likewise not a depth gap**, despite reading
   like one on a keyword search (see "false gaps caught") - ancient
   gearing, medieval verge escapement, and pendulum/balance-spring
   refinement are three separate, correctly staged nodes.

## Non-European coverage

The specific worry the brief raises - a tree written from a European
standpoint, thin on Chinese, Indian, Islamic and Mesoamerican material -
does not hold up under this check. Findings:

- **China (Needham's territory) is the best-covered non-European
  tradition**, and it is woven into the tree at both the node level and
  the civilisation level. The Han China starting kit (`han_china_100ad.json`)
  correctly grants cast iron, paper, the horse collar, the seed drill, the
  heavy mouldboard plough, the sternpost rudder and the magnetic compass as
  already in hand circa 100 CE - each of those datings checks out against
  the sources used here, and the accompanying blurb ("roughly a thousand
  years of head start... on metallurgy and agriculture") is not an
  exaggeration relative to Europe's timeline for the same technologies.
  Individually verified present elsewhere in the tree: papermaking,
  woodblock and movable-type printing, gunpowder and cast bronze cannon,
  cast iron and the blast furnace, water-powered double-acting bellows,
  the chain drive, paper currency, porcelain and bone china, coke fuel,
  and the escapement-bearing mechanical clock. The two Chinese-specific
  items not separately credited are noted above (deep brine/gas drilling,
  south-pointing-chariot differential) and both are attribution nuances,
  not functional gaps.
- **India's largest single contribution - the decimal positional number
  system with zero and negative numbers, underlying all subsequent
  quantitative science - is explicitly modelled** as `arithmetic_positional`
  ("Decimal positional notation, zero, negative numbers, decimal
  fractions"), with `sc2_notation_zero` and `sc2_notation_positional` as
  supporting nodes and `fin_arabic_numerals` capturing its commercial
  adoption. Wootz/crucible steel (a genuinely Indian/Central Asian
  invention, independently rediscovered by Huntsman in Sheffield in the
  1740s) is present as `crucible_steel`, but the node does not distinguish
  the two origins - a minor attribution point, not a coverage gap, since
  the process itself is correctly modelled. Mordant dyeing
  (`tex_mordanting`, `tex_dye_madder`), core to the Indian textile trade
  that dominated world commerce into the 18th century, is present.
- **The Islamic Golden Age's most load-bearing contributions - distillation,
  the paper mill scaled up with hydropower, and the windmill's westward
  transmission - all resolve to present nodes** (the `distill`-family
  nodes; papermaking as above; the wind-prime branch). The crankshaft
  (attributed to the Banu Musa brothers/al-Jazari) is present generically
  (`crank_conrod`) without the regional attribution, again an attribution
  point rather than a gap.
- **Mesoamerica (the Mexica civilisation) is handled structurally, not just
  by omission-avoidance**: `mexica_1500.json`'s starting kit and notes
  correctly encode the actually distinctive facts of Mesoamerican
  technology - chinampa agriculture outyielding contemporary European
  farming per hectare (`fud_chinampa`), obsidian blades sharper than steel
  but brittle (`mat_obsidian_blade`), and, most importantly, the absence
  of draught animals, the wheel in practical use, and iron, which the
  civilisation notes correctly identify as removing "the plough, the cart,
  the mill and the horse collar in one stroke." That is a real and correct
  reading of why Mesoamerican technology took the path it did, not a
  Eurocentric flattening of it. Lime plaster/stucco resolves to the
  generic `mat_lime` plus `cn_mortar` nodes rather than a
  Mesoamerica-specific node, which is defensible since the chemistry is
  identical to Roman lime mortar.
- **The Norse civilisation file and tree both correctly represent
  clinker-built shipbuilding and bloomery/pattern-welded iron** as the two
  genuinely distinctive Norse technical traditions; runic writing and
  named ship types (knarr, longship) are absent but are cultural/flavour
  rather than functional, on a par with the stirrup rejection above.

## REJECTS (things that matter historically but not to this premise)

Brief, as instructed - these were checked, found absent, and judged not to
matter to a founder racing for a transistor:

- **The stirrup** (explicitly named in the brief as the right kind of
  reject) - absent, and rightly so.
- **The crossbow** - absent; a military technology with no bearing on the
  industrial-materials path.
- **Acupuncture, dental amalgam** - absent; real Chinese/medical firsts,
  irrelevant to a transistor.
- **Runic writing, named Norse ship classes (knarr/longship), stockfish
  preservation** - absent; flavour/logistics detail with no technical
  dependency chain running through them.
- **Amphora-based container standardisation** - absent; a real Roman
  logistics technology, but the tree's general trade/logistics abstraction
  doesn't need the specific vessel modelled.
- **Quipu/khipu record-keeping** - absent, and correctly out of scope since
  it is Andean (Inca), not Mesoamerican, and the tree's four non-Roman
  civilisations don't include an Andean one.

---

Status: COMPLETE.
