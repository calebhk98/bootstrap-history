# Material gating audit: can you buy it, or must you make it

The rubber bug (`ac69bfb`, `e88a822`): a node can consume a material nothing
in its own prerequisite ancestry can produce, and the game will still sell it
at a flat book price. Before that fix you could buy rubber in Rome 100AD off
the shelf. This audit checks the other 161 material keys for the same bug.

## Method

For every material key consumed anywhere in `tech_tree.json` (162 keys, one
- `monochromatic_light_kg` - consumed only at quantity 0, so it was scanned
but has no real consumer to gate), every node that consumes it was found,
and a cycle-safe walk of that consumer's full ancestry - both `pre` and
`req_any` (skipping `req_any` options that name a material rather than a
node, per `substitution_quality`'s own "a purchasable commodity" handling)
- was checked for a node that plausibly produces the material.

"Produces" has no field in the schema; there is no `output` key. It was
inferred by hand, node by node, mostly from the `mat_*` id convention (a
`mat_aluminium`, `mat_copper`, `mat_wrought_iron`, ... node exists for most
raw materials) plus named process nodes elsewhere (`blast_furnace`,
`chm_contact_sulfuric`, `distillation_alcohol`, `tex_wool`, ...). 93 of the
162 materials have such a node somewhere in the tree; 69 have none at all.

**Having a `mat_*` (or other) production node does NOT by itself mean a
consumer needs it in its ancestry.** The task's own examples make this
explicit: iron and copper both have real production nodes (`mat_wrought_iron`
needs a bloomery or blast furnace; `mat_copper` needs `blast_furnace` and
heat) with genuine prerequisite chains, and it is still correct for a
consumer of `iron_bar_kg` or `copper_kg` to have neither in its ancestry,
because a Roman blacksmith or a Han ironmonger had already solved smelting
two thousand years before any of these civilisations' start dates - the
material was a mature, buyable trade good, whether or not *you* personally
know how to smelt it. A first, naive pass that gated every material on the
mere existence of a `mat_*` node produced absurd results (**213 of 246**
brass consumers "ungated", **292 of 590** iron-bar consumers "ungated",
**253 of 330** cast-iron consumers "ungated") precisely because it was
demanding the wrong thing: personal production of a Bronze Age commodity.

The real question, and the one this report answers material by material, is
narrower: **did this material exist as a purchasable commodity ANYWHERE ON
EARTH, at the era its consumer sits in?** For iron, copper, wool, silk, gold,
paper, porcelain (regionally), soap, dyed cloth - yes, someone, somewhere,
already knew how to make it, so the tree is right to let you buy it without
personally re-deriving the craft. For electrolytic aluminium, refined
petroleum, vulcanised rubber, industrial sulfuric acid, isolated chromium,
nickel, tungsten, molybdenum, platinum, selenium, zinc metal, porcelain (for
a Roman consumer specifically), aniline/synthetic routes, Bayer alumina,
calcium carbide, cryolite, celluloid - no. In every one of those cases *this
tech tree's own frontier* is the first place on Earth that process exists;
nobody else could have sold it to you either, so the consumer genuinely
needs the production node in its own ancestry.

A cycle-safe visited-set walk was necessary and not optional: the tree is
acyclic on `pre` alone but genuinely cyclic once `req_any` counts (the
existing example elsewhere in this tree, `junction_transistor -> silicon_path
-> point_contact_transistor -> junction_transistor`, is real; an assumed-DAG
walk gets OOM-killed).

## Numbers

| | |
|---|---|
| Material keys scanned | 162 |
| Materials with a real production node somewhere in the tree | 93 |
| Materials judged genuinely purchasable despite having a node (Bronze-Age-or-older crafts, trade goods) | 69 |
| Materials with no production node at all, judged correctly ungated (raw/natural/agricultural) | 69 |
| Materials with a genuine gap, fixed | 24 |
| Consumer nodes fixed (new `req_any` prerequisite group added) | 84 |
| Materials found to need a production node that does not exist yet (not added) | 3 flagged prominently, a few more noted in passing |

The task's own worked examples reported "7 of 18" aluminium consumers,
"2 of 7" petroleum consumers and "1 of 23" rubber consumers ungated. This
audit's full `pre`+`req_any` walk found **4 of 18**, **1 of 7** and **1 of
23** respectively - see "Why my numbers differ from the brief" below; the
three extra "gaps" in each case turn out to already be gated, once `req_any`
is followed correctly.

---

## Fixed: 24 materials, 84 consumer nodes

Each fix adds a new `req_any` group to the consumer node, naming the real
production route(s) - never removing or narrowing any existing route, so a
player is not forced down one path. `pre` was left alone throughout; nothing
here could create a cycle in `closure()` (which is `pre`-only and stays a
DAG) - see the cycle-safety note near the end.

| Material | Production route(s) required | Consumers fixed |
|---|---|---|
| `aluminium_kg` | `mat_aluminium` | `air_monoplane_structure`, `mil_bomber_aircraft`, `mil_dive_bomber`, `mil_fighter_aircraft` |
| `aluminum_oxide_kg` | `ch2_process_bayer` | `prc_lapping_plate` |
| `ammonia_kg` | `mat_ammonia` / `chm_haber_bosch` / `chm_solvay_process` | `ag2_urea` |
| `bleach_kg` | `mat_chlorine` / `chm_bleaching_powder` | `tx2_discharge_printing` |
| `calcium_carbide_kg` | `chm_alkali_waste` | `met_acetylene_supply` |
| `celluloid_kg` | `mat_celluloid` | `mt2_laminated_glass_safety` |
| `chromium_kg` | `mat_chromium` | `met_hardenability_alloys`, `prc_gauge_blocks_johansson` |
| `cryolite_kg` | `mat_cryolite` | `electrolysis_industrial` |
| `graphite_kg` (partial - see note) | `mat_graphite_pure` | `ge_reduction`, `silicon_path`, `single_crystal`, `zone_refining` |
| `manganese_kg` | `mat_manganese` | `chm_weldon_process`, `mat_bulk_steel`, `met_hardenability_alloys` |
| `molybdenum_kg` | `mt2_molybdenum_extraction` | `el2_beam_tetrode_output_tube` |
| `nickel_kg` (one exception - see note) | `mat_nickel` | `com_radar_magnetron`, `com_vacuum_tube_pentode`, `com_vacuum_tube_tetrode`, `gp_glass_metal_seal`, `if_cathode_ray_tube`, `lnd_diesel_cycle`, `lnd_otto_cycle_four_stroke`, `met_hardenability_alloys`, `met_powder_metallurgy`, `vacuum_tube` |
| `petroleum_refined_kg` | `mat_petroleum_refined` | `tx2_polyester` |
| `phosphorus_red_kg` | `chm_phosphorus_extraction` | `gp_getter` |
| `platinum_g` | `mat_platinum_bulk` | `chm_catalyst_concept`, `chm_contact_sulfuric`, `chm_ostwald_ammonia_oxidation`, `discharge_xray`, `gp_glass_metal_seal`, `opt_bolometer`, `prc_standard_meter_wavelength`, `pwr_fuel_cell`, `tl_spark_plug` |
| `porcelain_kg` | `mat_porcelain` | `el2_capacitor_variable_air`, `el2_potentiometer`, `en_insulator`, `en_rocket_motor`, `en_substation`, `en_transmission_line`, `gp_controlled_atmosphere_chamber`, `pwr_high_voltage_transmission` |
| `quartz_tube_kg` | `fused_quartz` | `sea_sonar` |
| `rubber_tubing_kg` | `mat_rubber_coagulated` / `mat_synthetic_rubber` | `med_sphygmomanometer` |
| `selenium_kg` | `pwr_selenium_metal` | `el2_photodiode_photocell_selenium`, `el2_rectifier_metal_layer` |
| `steam_kg` | `steam_atmospheric` / `steam_watt` / `cap_power_steam` / `steam_high_pressure` | `chm_activated_carbon` |
| `sulfuric_acid_kg` | `lead_chamber` / `chm_contact_sulfuric` | `cap_gas_o2h2`, `com_integrated_circuit`, `com_photolithography`, `electroplating`, `fud_beet_sugar_processing`, `fud_superphosphate_fertilizer`, `hydrochloric_acid`, `hydrofluoric_acid`, `med_insulin`, `met_electro_refining`, `met_galvanizing`, `met_metallography`, `met_tin_plate`, `mfg_anodising`, `nitric_acid`, `pwr_fuel_cell`, `pwr_selenium_metal`, `tex_chlorine_bleaching`, `tex_rayon_viscose` |
| `tungsten_kg` | `mat_tungsten` | `md2_fluoroscopy`, `md2_xray_plate`, `met_powder_metallurgy`, `mfg_hss_development`, `mfg_mushet_steel`, `mfg_stellite_tool`, `mt2_elinvar_alloy`, `opt_electron_microscope` |
| `wood_pulp_kg` | `prn_wood_pulp` | `tex_rayon_viscose` |
| `zinc_kg` | `mat_zinc` / `zinc_metal` / `zinc_industry_scale` | `cap_gas_o2h2`, `if_photoengraving` |

**Why these and not others with a book price**: every material above is a
specific invented industrial process with no real-world precedent before
that invention - electrolytic aluminium (1886), the Bayer process (1888),
synthetic ammonia routes, the Leblanc calcium-carbide byproduct, celluloid
(1862), isolated chromium/nickel/molybdenum/tungsten/selenium (all 1780s-
1820s discoveries, industrial-scale extraction much later), mined cryolite
(Greenland, 1854 industrially), fused quartz (1880s), refined petroleum
fractions (1850s+), workable platinum (refining solved ~1780s), true
porcelain (a closely-held Chinese/Islamic-world secret, not a Roman trade
good), the lead-chamber/contact processes for industrial-strength sulfuric
acid, cheap wood-pulp paper (1840s+), and metallic zinc by retort (a real
achievement, but a 9th-12th century Indian/Chinese one, not something Rome,
the Norse, or the pre-1500 Mexica could buy). No civilisation this side of
the tree's own frontier had these on offer.

**graphite_kg (partial fix, not material-wide)**: this key is used both for
ordinary lump graphite (pencils, brush contacts - genuinely ancient/natural,
correctly ungated) and for Acheson-process ultra-pure graphite (semiconductor
crucibles). Rather than gate the whole material - which would have forced
`gp_carbon_brushes` (tier 1) through a tier-5 purity chain it doesn't need -
only the four tier-5 consumers that are actually growing single-crystal
silicon/germanium (`ge_reduction`, `silicon_path`, `single_crystal`,
`zone_refining` - three of these sit on the critical path to the goal
itself) were gated on `mat_graphite_pure`. `gp_carbon_brushes` and
`prc_die_sinker` are left buying ordinary graphite, correctly.

**nickel_kg (one deliberate exception): `electroplating`**. `electroplating`
consumes nickel but sits *upstream* of `mat_nickel` itself
(`mat_nickel -> cap_pure_4N -> electroplating`), so gating it on nickel would
have made `electroplating` permanently unbuildable - a real regression, not
a fix. The generic electroplating technique doesn't specifically require
nickel either (silver, copper and gold plating are electroplating too), so
this is left as a documented, judged-legitimate gap rather than "fixed". A
future nickel-specific plating node would be the right place to add this
gate; none exists yet.

---

## Judged legitimate: 69 materials with a production node, left ungated

These all have a `mat_*`/process node somewhere in the tree (so a first,
structural pass flagged gaps for them, in some cases the great majority of
their consumers), but the material itself was a real, buyable commodity
across the whole span of eras these consumers sit in - a market for it
existed independent of the player's own progress, the same way iron and
copper do.

- **Ancient/Bronze-Age metals and alloys**, tradeable without personally
  knowing metallurgy: `copper_kg`, `copper_wire_kg` (wire-drawing is
  Bronze-Age jewellery technique), `iron_bar_kg`, `iron_bloom_kg`,
  `cast_iron_kg` (China cast iron from ~500 BC), `brass_kg`, `bronze_kg`,
  `gold_g`/`gold_kg`, `silver_kg`, `tin_kg`, `lead_kg` (already ungated, no
  producer node exists), `steel_plate_kg`, `tool_steel_kg`, `wire_drawn_kg`
  (crucible/Wootz/Noric/Damascus steel was a real, traded ancient/medieval
  commodity, matching `steel_noric_kg`'s own already-legitimate status).
- **Ancient minerals**, mined and traded: `alum_kg` (Roman/Egyptian alum
  trade), `asbestos_kg` (Pliny's "asbestos napkins"), `blue_vitriol_kg` /
  `green_vitriol_kg` (natural chalcanthite, known to ancient/medieval
  alchemists), `calamine_kg` (the ore Romans cemented into brass), `emery_kg`
  (Naxos emery, a named ancient Greek/Roman abrasive), `galena_kg` (raw lead
  ore), `natron_kg` (Egyptian trade good since ~1500 BC), `pyrolusite_kg`
  (Roman "glassmakers' soap", used to decolorize glass in antiquity),
  `sulfur_kg` (already ungated - no node exists; volcanic sulfur was mined
  since antiquity, e.g. Sicily).
- **Ancient/medieval organic and craft goods**: `beeswax_kg`/`wax_kg`,
  `tallow_kg`, `felt_kg` (Central Asian nomadic felt predates Rome by
  millennia), `leather_kg`, `linen_kg`, `silk_kg` (Silk Road, expensive but
  real - Pliny complains about gold flowing east for it), `shellac_kg`
  (Indian/SE Asian lac trade, ancient), `soap_kg` (Levantine hard-soap
  tradition and Gallic soap both pre-date these tiers), `dye_kg` (madder,
  woad, murex/Tyrian purple, indigo - all ancient trade dyes; the material
  key's one gapped consumer, cloth printing, doesn't require the *synthetic*
  aniline route), `essential_oil_kg` (ancient perfume industry - pressing/
  enfleurage, not only distillation), `ethanol_kg` (its only gapped
  consumers - insulin/penicillin extraction, metallography - are all tier
  3-4, by which point distilled alcohol is safely assumed to exist
  somewhere), `carbon_kg` (soot/lampblack, trivial since fire existed),
  `ceramic_kg` (pottery predates writing), `canvas_kg`/`cloth_kg`/
  `cloth_bag_kg`/`fabric_kg`/`cotton_fabric_kg` (weaving is Neolithic;
  finished cloth was a dominant ancient trade good), `cotton_fabric_kg`
  (as above), `papyrus_sheet` (Egyptian state export good - a scribe buys
  scrolls, doesn't need to own the swamp), `parchment_sheet` (bought from a
  parchment-maker/tanner), `paper_kg` (72% of its consumers were already
  ungated; once invented anywhere it became a widely-traded commodity, and
  every gapped consumer sits at a tier where that trade plausibly reaches
  them), `brick_1000` (fired brick since ~3500 BC, Roman *opus latericium*
  was everywhere), `concrete_reinforced_kg` and `phosphor_bronze_g` (0 real
  gaps; listed for completeness).
- **Acids/chemicals with a real pre-industrial trade**: `acetic_acid_kg`
  (vinegar, trivially ancient - 0 gaps), `acetylene_kg` (0 gaps),
  `formaldehyde_kg`/`nitrocellulose_kg`/`nitroglycerin_kg`/`bitumen_kg`
  (0 gaps as-is; `mat_bitumen` itself has no prerequisites - Mesopotamian
  bitumen seeps are Herodotus-era, purely a flavour node not a gate),
  `hydrochloric_acid_kg`/`nitric_acid_kg` (0 gaps; both were medieval
  alchemical products by the tiers that use them), `coal_tar_kg` (0 gaps).
- **Gases and elements with no true gap in practice**: `hydrogen_m3`,
  `oxygen_m3`, `germanium_g` (0 gaps - its handful of consumers already
  chain through `germanium_extraction`/`ge_reduction`/`gecl4_purification`),
  `nitre_kg` (0 gaps - nitre beds are a real, if late-medieval, composting
  technique already gating everything that needs it).

---

## Judged legitimate: 69 materials with no production node at all

No `mat_*` or process node exists anywhere in the tree for these, and none
should: every one is either a natural resource available basically anywhere
(clay, sand, gravel, stone in its various forms, timber, firewood, water,
chalk, limestone, dolomite, calcite, gypsum-adjacent minerals, kieselguhr,
fluorspar, agate, cinnabar - the ore itself, copper ore, iron ore, bauxite),
an agricultural/pastoral product (wheat, milk, manure, wine, wool - matching
the brief's own example, cotton as raw fibre, hemp fibre, flax/linen-rag,
bristles, horsehair, bone, bone ash, fat, cork, oak bark, rose petals), a
trivial byproduct of fire or basic husbandry (wood ash, firewood, gelatin,
agar), or a basic ancient/early craft with no meaningful barrier to entry
(felt-adjacent thread-spinning, ink - carbon ink and iron-gall ink both
predate these eras -, paint, varnish, dolomite/lodestone as found minerals,
mineral pigments, salt, flue dust as a smelting byproduct). Also in this
bucket: `iron_sheet_kg` and `steel_noric_kg` (Noric steel was a real,
famous Roman-era Alpine export - "ferrum Noricum" - so buying steel without
personally running a Noric forge is exactly the iron/copper case), land
itself (`iugerum_land`, bought or rented, not manufactured), and
`slave_skilled` (a market good in every one of these societies' own
economies, priced with a skill premium - not a manufacturing gap in the
sense this audit is about).

A few of these are debatable and were resolved on low stakes rather than
strong conviction (documented so a future pass can revisit them):
`antimony_kg` (known since antiquity as kohl/stibium; its low-tier
consumers - `printing_press` tier 1, type-metal alloys tier 2 - line up
with when antimony trade is well attested), `boric_acid_kg` (borax was a
real Tibet-to-Mediterranean trade good for millennia; its one consumer,
borosilicate glass, is tier 3), `chrome_salts_kg` (its single consumer,
`tex_chrome_tanning`, already lists `mat_chromium` as a hard `pre`, so it
rides along for free), `bismuth_kg` (Agricola documents European bismuth
mining from 1546; its consumers - thermoelectric couples, tier 3 - are
comfortably later), `argon_or_h2_m3` (the "or" in the key's own name already
offers the hydrogen route, which is separately gated).

---

## Needs a production node that does not exist yet (not added)

Three materials have **no production node anywhere in the tree**, are used
by consumers that sit at the deep end of the tech tree (tier 4-5, one of
them the goal node itself), and have no real pre-industrial or even
pre-20th-century commercial existence - these are genuine holes, not
judgment calls, and are reported rather than patched with an invented node,
per the brief's instruction:

- **`indium_g`** - consumed by `com_logic_gate`, `com_semiconductor_diode`,
  and **`junction_transistor` itself** (200 g). Indium was isolated in 1863
  and had no industrial extraction process before the 20th century. The
  win-condition node's own material list has no route to this material
  anywhere in the tree.
- **`caesium_g`** - consumed by `opt_photocell` (tier 3, on the road to
  photoelectric detection). Isolated 1860, no pre-industrial precedent.
- **`barium_kg`** - consumed by `vacuum_tube` (tier 5, barium getter in the
  envelope). Isolated 1808, no pre-industrial precedent.

Adding real production chains for these (indium and barium are typically
byproducts of zinc/lead smelting; caesium from pollucite ore) would be a
legitimate fix, but each is a genuine research/worldbuilding decision (which
ore, which by-product stream, what era) rather than a mechanical one, so it
was left for a future pass rather than invented here. Given `junction_
transistor` needs indium directly, this is the single most consequential
finding in this audit and worth prioritising.

---

## Notes on method

**Why my numbers differ from the brief's worked examples.** The brief
reported "7 of 18" aluminium consumers, "2 of 7" petroleum consumers and
"1 of 23" rubber consumers as ungated (verified before this audit started).
Redone with the full `pre`+`req_any` walk this instruction set requires,
the true counts are 4, 1 and 1. In every one of the "extra" cases the
consumer already reaches the production node through a `req_any` group -
sometimes a real substitution (`el2_microphone_condenser_electrostatic`'s
diaphragm can be aluminium *or* mylar), sometimes a single-option group that
is really a disguised hard requirement (`el2_meter_energy_kWh_meter`'s rotor
has exactly one listed option, `mat_aluminium`, so it already cannot be
built without it). A `pre`-only walk - which is what `closure()` uses
elsewhere in this engine, deliberately, because `closure()` must stay a DAG
- would undercount in the other direction and call all three of those
already-gated nodes bugs. The brief's own numbers look like they came from
a similar `pre`-only pass; this audit's full walk is more accurate to what a
player can actually do, and is the algorithm the brief itself specifies.

**Cycle safety.** The walk carries a visited set and is provably terminating
on a graph of 2,833 nodes (confirmed: full analysis runs in well under a
second). Two real cycles were caught and handled: `mat_nickel`'s own
ancestry passes through `electroplating` (via `cap_pure_4N`), and
`chm_contact_sulfuric`'s ancestry passes through `electroplating`,
`hydrochloric_acid` and `nitric_acid` (same route). The nickel case is the
one documented exception above. The sulfuric-acid case did not need an
exception, because `sulfuric_acid_kg`'s `req_any` offers **two** routes
(`lead_chamber` *or* `chm_contact_sulfuric`) and `lead_chamber`'s own
ancestry is clean of all three - so `electroplating`, `hydrochloric_acid`
and `nitric_acid` can all still be built, via the lead-chamber route,
without circularity.

**No developer-facing prose was added to player-visible fields.** Every new
`req_any` group carries only a `group` slug and `options` (existing node
ids); no `note` field was touched, so nothing described in the "shipped
`[AUDIT: ...]` in the win condition text" incident recurs here. The one
`_internal` field seen in this codebase (`mat_aluminium`'s own reviewer
note) is precedent for keeping any commentary out of player-facing text;
this audit's own reasoning lives here and in code comments only.

**Regression coverage.** `rome/sim/test_regressions.py` now pins all 24
fixed materials (23 material-wide, plus the 4 pinned `graphite_kg`
consumers, plus the one documented `nickel_kg`/`electroplating` exception)
with a cycle-safe `pre`+`req_any` walk, run as an ordinary (non-slow) check
- the whole audit computes in well under a second, nowhere near the ~3s
slow-check threshold. `python3 rome/sim/simulator.py validate` and the full
814-check-turned-817-check regression suite both pass clean after every fix
in this report.
