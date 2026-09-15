# Tech-tree opening review — combined report

> [!IMPORTANT]
> ## Suggestions — highest-priority fixes
> **Design constraint:** keep the technology tree **scenario/country agnostic**. Do not hard-link ordinary technology nodes to Rome, Han, England, the Mexica, Japan, Mars, etc. A scenario should simply load an historically appropriate starting state into the same universal graph.
>
> 1. **Make scenario starts explicit data, not inferred from a universal “ancient baseline.”** Each scenario should declare the exact tech/capability/material nodes it begins with. The current shared ambient/tier-0 inheritance silently gives culturally and geographically specific Old World technologies to unrelated starts; that is the main source of the Mexica/Han/Norse errors. This becomes even more important for Paleolithic, Mars, early America, Japan, Australia, and future starts.
> 2. **Keep prerequisites physical and causal rather than chronological or country-based.** A technology invented in 1750 can be immediately attemptable in 100 AD if a modern founder knows it and all necessary materials, tooling, labor skills, biological stock, and institutions already exist. Gate things because they require something real—not because history had not reached the calendar date yet.
> 3. **Do not use `tier 0` as “every society starts with this.”** Tier/depth and starting ownership are different concepts. A very basic technology can still be absent in a particular place (wheel transport, ironworking, writing, domesticated draft animals), while a sophisticated local technology can already be present.
> 4. **Split capabilities that bundle independent facts.** The clearest example is `cap_power_muscle` combining human and animal power. A Mars castaway may have humans but no oxen; the Mexica had human muscle but no large draft-animal economy. Similar bundled nodes (`crank_conrod`, horse collar + whippletree + horseshoe, etc.) should be split when one component can realistically exist without the others.
> 5. **Separate “knowledge of a process” from prerequisites that cannot be supplied by knowledge.** Biological stock, geographically restricted materials, specialist tooling, and institutional ecosystems must still gate projects. Knowing sericulture does not create silkworm eggs; knowing watch-case construction does not create a watchmaking industry.
> 6. **Audit scenario grants for internal contradictions automatically.** If a start owns bloomery iron, bronze casting, and glassmaking, but its maximum heat capability says 700 °C, flag it. If a briefing says “no iron/no practical wheel” while the loaded state includes wrought iron and iron-tyred spoked wheels, flag it. A validator could catch a large fraction of the problems found in these reviews.
> 7. **Prefer universal process names over civilization names where possible.** A Roman-specific artifact such as a groma can stay Roman, but a generic function such as right-angle surveying should have culture-neutral underlying capabilities. A Han or Mexica start should not inherit a Roman device merely because it fulfills a similar function.
> 8. **Treat traded/imported material access carefully.** A start may possess silk, paper, obsidian, or other goods without possessing the production technology. Model the dependency so access to the material does not automatically imply local manufacture, and local process knowledge does not magically imply access to the raw input.
> 9. **Descriptions should teach the technology from zero.** Every node should answer: *What is it? How does it work? What inputs does it require? Why is it useful or difficult?* Avoid descriptions that are just specialist vocabulary or that assume the player already knows terms such as retting, selvedge, seigniorage, or radical notation.
> 10. **Fix factual errors and over-bundled historical claims before fine-tuning prices.** Examples found in these audits include the 50/50 Pb-Sn “eutectic,” the 100 AD Pantheon-dome wording, the Han navigational compass, England's pendulum clock in 1300, and several compound nodes that grant centuries of mechanical development in one step.
>
> **Recommended scalable implementation:** scenario files contain only starting-state data (known node IDs, available resources/materials, capability values, population/institution facts, geography/environment, etc.). The tech graph remains one universal causal graph. Adding “pre-caveman,” Mars, Civil-War America, Australia, Japan, or another start then means authoring a new initial-state file and validating it against the same graph—not forking the graph or adding country checks.

## Reading note

This combined document preserves the three original reviews below. The **strict realism audits supersede any earlier recommendation motivated by reducing menu size or making the opening easier to choose from**. A large number of immediately available projects is not itself a problem if the starting state and causal prerequisites are realistic.

---

# Appendix — Initial Rome player-POV review

# Rome 100 AD opening tech-tree review — player-POV log

## Session setup
Fresh default Roman game: Trajanic Rome, 100 AD; fog of war ON; poor scholar (400 denarii); immortal founder; transistor goal; standard 500-year horizon. I used the CLI exactly as a player first (`state`, `available`, `why`) and only then checked the tree data to audit all 209 opening choices consistently.

## Opening verdict
The game starts Rome with **139 granted technologies** and **209 immediately startable projects**. The number 139 is not intrinsically too high for a 2,849-node tree. The problem is classification: dozens of basic ancient practices remain in the “research this” pool even though Rome already demonstrably had them. I would **increase** the granted set by roughly 40–60 mundane craft/institution nodes, while simultaneously **removing or gating** roughly 25–40 later/ecosystem-dependent projects from the immediate pool. That would make the opening narrower and more historically legible without making Rome technologically stronger in a silly way.

The 400-denarius default also creates a useful distinction: 209 are mechanically startable, but many are not financeable. That is fine. What is not fine is when a project is technically startable despite requiring an ecosystem the prerequisites do not represent (watch case before watches; modern academic institutions before an institution base; cultivated silk as if silkworm stock is locally available).

## Starting grants (139)
Most of the grants are sensible: Roman roads, concrete/arches, aqueducts, market/contract institutions, writing media, basic medicine, ships, weaving and common materials are exactly the sort of ambient capability a newcomer should inherit rather than reinvent. I would keep the count in this ballpark, but fix these specific problems:

- **Roman concrete dome** is dated by its own note to the Pantheon in 126 AD, yet the scenario begins in 100 AD. Rome certainly had domes, but the node as written overclaims the mature Pantheon capability by ~26 years. Rename/scale it to “Roman concrete dome, early” or stop granting the Pantheon-grade version.
- **Geared mechanical transmission** claims involute/cycloidal tooth flanks. The Antikythera mechanism proves sophisticated gearing, not those later optimized tooth profiles. Keep the grant, fix the description.
- **Legal protection for physicians** is too categorical as a universal technical baseline; if it represents a specific legal privilege, it should be scenario/institution-specific and sourced carefully.
- Several grants are really **available materials/trade goods** rather than technology (silk, cotton, asbestos, mercury, etc.). That is mechanically understandable, but the UI should label them as “available supply/material” so players do not read 139 as 139 inventions Rome mastered.
- The bigger omission is mundane practice: flax/hemp processing, retting, heddles, selvedges, scouring, common dye staging, basic leather finishing, earthenware, hot riveting, investment casting, ordinary oil pressing, etc. Those appearing as founder projects makes Rome look oddly ignorant of its own workshops.

## All 209 immediately startable projects
Legend: **MOVE TO START** = Rome should already know this; **KEEP STARTABLE** = plausible thing a modern knower could attempt immediately; **QUESTIONABLE** = plausible idea but prerequisites/cost framing need work; **GATE HARDER** = should not be immediately startable because a missing enabling technology, institution, supply chain, or mature industry is doing too much hidden work.

| # | Project | Cost shown | Founder h | Floor y | Risk | Verdict | Description quality |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 5 | 30 | 0.10 | 0% | KEEP STARTABLE | Good: mostly self-explanatory |
| 2 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 6 | 30 | 0 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 3 | **Yarn count standardisation** (`tx2_count_standard`) | 6 | 40 | 0 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 4 | **Retting of flax and hemp fibres** (`tx2_retting`) | 6 | 30 | 0 | 15% | MOVE TO START | Weak: assumes terminology / too terse |
| 5 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 6 | 30 | 0 | 15% | MOVE TO START | Weak: assumes terminology / too terse |
| 6 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 7.5 | 40 | 0 | 15% | MOVE TO START | Weak: assumes terminology / too terse |
| 7 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 9 | 40 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 8 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 9 | 40 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 9 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 9 | 40 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 10 | **Twist insertion control** (`tx2_twist_insertion`) | 9 | 50 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 11 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 9 | 50 | 0.20 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 12 | **Bone setting** (`med_bone_setting`) | 9.3 | 0 | 0.50 | 10% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 13 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 9.5 | 40 | 0.10 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 14 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 9.5 | 40 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 15 | **Beam: warp holder and tension** (`tx2_beam`) | 9.9 | 40 | 0.20 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 16 | **Contract of employment** (`fin_employment_contract`) | 10 | 60 | 1 | 5% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 17 | **Button: horn material** (`tx2_button_horn`) | 10 | 40 | 0.10 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 18 | **Button: bone material** (`tx2_button_bone`) | 10.1 | 40 | 0.10 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 19 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 10.5 | 50 | 0 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 20 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 10.5 | 50 | 0 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 21 | **Mohair: angora goat fibre** (`tx2_mohair`) | 10.5 | 50 | 0 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 22 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 10.5 | 50 | 0 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 23 | **Button: shell material** (`tx2_button_shell`) | 11.5 | 50 | 0.15 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 24 | **Pin: sewing fastener** (`tx2_pin`) | 11.8 | 40 | 0.10 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 25 | **Amputation and prosthetics** (`med_amputation`) | 12.3 | 0 | 0 | 30% | MOVE TO START | Good: mostly self-explanatory |
| 26 | **Comb: hair grooming tool** (`tx2_comb`) | 13 | 50 | 0.20 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 27 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 14 | 60 | 0.30 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 28 | **Currying: leather finish dressing** (`tx2_currying`) | 15 | 60 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 29 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 16 | 80 | 1 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 30 | **Splitting: leather layering** (`tx2_splitting`) | 16 | 70 | 0.30 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 31 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 16.6 | 50 | 0.50 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 32 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 18 | 100 | 2 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 33 | **Obstetric practice** (`med_obstetric_practice`) | 18.8 | 0 | 0 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 34 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 19.8 | 50 | 0.20 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 35 | **Trademark and mark of quality** (`fin_trademark`) | 20 | 80 | 1 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 36 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 21 | 60 | 0.25 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 37 | **Safety pin** (`hom_safety_pin`) | 24.1 | 40 | 0.25 | 2% | QUESTIONABLE | Good: mostly self-explanatory |
| 38 | **Seigniorage and debasement** (`fin_seigniorage`) | 25 | 80 | 0.20 | 10% | MOVE TO START | Weak: assumes terminology / too terse |
| 39 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 27.9 | 70 | 0.30 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 40 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 28.6 | 50 | 0.20 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 41 | **Usury law and interest regulation** (`fin_usury_law`) | 30 | 100 | 1 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 42 | **Corset: rigid body support garment** (`tx2_corset`) | 30 | 100 | 0.50 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 43 | **Toothbrush** (`hom_toothbrush`) | 30.3 | 60 | 0.25 | 2% | QUESTIONABLE | Good: mostly self-explanatory |
| 44 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 31 | 60 | 0.20 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 45 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 37.5 | 80 | 1 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 46 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 40 | 120 | 1 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 47 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 40.4 | 80 | 0.50 | 15% | QUESTIONABLE | Good: mostly self-explanatory |
| 48 | **Tariff and import duty** (`fin_tariff`) | 47.5 | 100 | 2 | 10% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 49 | **Log line for speed** (`sea_log_line`) | 49.6 | 30 | 0.10 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 50 | **Monopoly and exclusive grant** (`fin_monopoly`) | 51.1 | 80 | 1 | 15% | QUESTIONABLE | Good: mostly self-explanatory |
| 51 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 53.5 | 100 | 2 | 20% | MOVE TO START | Weak: assumes terminology / too terse |
| 52 | **Cartel and market sharing agreement** (`fin_cartel`) | 53.8 | 100 | 1 | 20% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 53 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 55 | 80 | 0.30 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 54 | **Block printing: carved design application** (`tx2_printing_block`) | 55.1 | 100 | 0.50 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 55 | **Peat extraction and burning** (`pwr_peat`) | 57.4 | 100 | 0.50 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 56 | **Mortgage and real estate credit** (`fin_mortgage`) | 57.5 | 120 | 1 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 57 | **Patent and exclusive right** (`fin_patent`) | 61.8 | 140 | 2 | 20% | QUESTIONABLE | Good: mostly self-explanatory |
| 58 | **Guild and monopoly craft** (`fin_guild`) | 68.8 | 100 | 1 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 59 | **Hand ginning cotton** (`tex_hand_ginning`) | 69.9 | 30 | 0.20 | 6% | MOVE TO START | Good: mostly self-explanatory |
| 60 | **Bill of exchange** (`fin_bill_exchange`) | 70 | 150 | 2 | 15% | KEEP STARTABLE | Good: mostly self-explanatory |
| 61 | **Codebook for optical signal tower** (`com_optical_codebook`) | 71.4 | 100 | 0.25 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 62 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 74.4 | 20 | 0.30 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 63 | **Toys and dolls** (`hom_toys_dolls`) | 75.5 | 60 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 64 | **Straightedge and reference straightness** (`prc_straightedge`) | 81.8 | 30 | 0.20 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 65 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 83 | 50 | 0.50 | 2% | QUESTIONABLE | Good: mostly self-explanatory |
| 66 | **Doll: articulated child plaything** (`tx2_doll`) | 83.5 | 80 | 1 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 67 | **Compass for navigation** (`air_compass_magnetic`) | 87.7 | 30 | 0.10 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 68 | **Trade union and workers collegium** (`fin_trade_union`) | 88.1 | 120 | 2 | 30% | QUESTIONABLE | Good: mostly self-explanatory |
| 69 | **Wheelbarrow** (`lnd_wheelbarrow`) | 89 | 30 | 0.50 | 5% | KEEP STARTABLE | Good: mostly self-explanatory |
| 70 | **Umbrella** (`hom_umbrella`) | 89.7 | 80 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 71 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 97.7 | 35 | 0.15 | 5% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 72 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 102 | 100 | 0.50 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 73 | **Triangulated truss frame** (`civ_truss_triangulated`) | 108.4 | 120 | 0.50 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 74 | **Needle: sewing implement** (`tx2_needle`) | 111.8 | 40 | 0.10 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 75 | **Lodestone knowledge** (`sea_lodestone`) | 112.2 | 20 | 0.20 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 76 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 113.8 | 50 | 0.15 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 77 | **Carding: opening and aligning fibres** (`tx2_carding`) | 115.9 | 60 | 0.20 | 15% | MOVE TO START | Good: mostly self-explanatory |
| 78 | **Guano** (`ag2_guano`) | 119 | 30 | 0 | 8% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 79 | **Marling** (`ag2_marling`) | 119.4 | 25 | 0.15 | 2% | QUESTIONABLE | Weak: assumes terminology / too terse |
| 80 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 124.9 | 60 | 0.50 | 3% | QUESTIONABLE | Good: mostly self-explanatory |
| 81 | **Mordanting dyes with alum** (`tex_mordanting`) | 129.3 | 40 | 0.30 | 8% | MOVE TO START | Weak: assumes terminology / too terse |
| 82 | **Stone polishing and smoothing** (`cn_stone_polish`) | 137.8 | 30 | 0.15 | 5% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 83 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 142 | 80 | 0.40 | 5% | GATE HARDER | Good: mostly self-explanatory |
| 84 | **Liming** (`ag2_liming`) | 149.6 | 30 | 0.20 | 3% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 85 | **Hopping** (`ag2_hopping`) | 150 | 40 | 0.15 | 4% | QUESTIONABLE | Weak: assumes terminology / too terse |
| 86 | **Kite** (`air_kite_basic`) | 157.8 | 20 | 0.10 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 87 | **Composting** (`ag2_composting`) | 159.4 | 40 | 0.20 | 5% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 88 | **Potash** (`ag2_potash`) | 159.4 | 40 | 0.20 | 5% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 89 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 169.2 | 80 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 90 | **Sluice gate for water control** (`civ_gate_sluice`) | 183 | 100 | 0.60 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 91 | **Indigo dyeing** (`tex_indigo`) | 187.8 | 60 | 0.40 | 10% | KEEP STARTABLE | Good: mostly self-explanatory |
| 92 | **Reefing sails** (`tr_reefing`) | 200.4 | 50 | 0.30 | 8% | MOVE TO START | Good: mostly self-explanatory |
| 93 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 202.8 | 40 | 0.50 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 94 | **Production schedule** (`mfg_production_schedule`) | 204 | 130 | 0.50 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 95 | **Wooden waggonway** (`tr_wooden_waggonway`) | 204.9 | 40 | 2 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 96 | **Flux** (`mfg_flux`) | 209 | 60 | 0.15 | 7% | MOVE TO START | Good: mostly self-explanatory |
| 97 | **Obsidian blade knapping** (`mat_obsidian_blade`) | 210 | 40 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 98 | **Vector control** (`md2_vector_control`) | 210.8 | 100 | 2 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 99 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 216.8 | 40 | 0 | 0% | QUESTIONABLE | Good: mostly self-explanatory |
| 100 | **Enamelling** (`mfg_enamelling`) | 216.8 | 120 | 0.30 | 14% | MOVE TO START | Good: mostly self-explanatory |
| 101 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 217.5 | 150 | 1 | 10% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 102 | **Plaster cast immobilization** (`md2_plaster_cast`) | 218 | 100 | 1 | 15% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 103 | **Adhesive bonding** (`mfg_adhesive_bond`) | 219.5 | 140 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 104 | **Japanning** (`mfg_japanning`) | 219.5 | 110 | 0.25 | 9% | QUESTIONABLE | Weak: assumes terminology / too terse |
| 105 | **Hot riveting** (`mfg_hot_riveting`) | 220 | 80 | 0.20 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 106 | **Casting mould** (`mfg_mould`) | 222.5 | 120 | 0.30 | 12% | MOVE TO START | Good: mostly self-explanatory |
| 107 | **Cold riveting** (`mfg_cold_riveting`) | 223 | 100 | 0.20 | 9% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 108 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 223.4 | 30 | 1 | 5% | GATE HARDER | Good: mostly self-explanatory |
| 109 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 223.5 | 110 | 0.80 | 8% | GATE HARDER | Good: mostly self-explanatory |
| 110 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 224.4 | 80 | 0.80 | 11% | KEEP STARTABLE | Good: mostly self-explanatory |
| 111 | **Painting** (`mfg_painting`) | 225 | 80 | 0.20 | 8% | MOVE TO START | Good: mostly self-explanatory |
| 112 | **Horizontal loom** (`tex_horizontal_loom`) | 225.8 | 80 | 0.50 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 113 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 230 | 350 | 2 | 20% | KEEP STARTABLE | Good: mostly self-explanatory |
| 114 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 230 | 60 | 0.50 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 115 | **Block and tackle pulley** (`tr_block_tackle`) | 230.2 | 40 | 0.30 | 2% | MOVE TO START | Good: mostly self-explanatory |
| 116 | **Hay making and dry storage** (`fud_hay_making_storage`) | 235 | 100 | 1 | 20% | MOVE TO START | Good: mostly self-explanatory |
| 117 | **Post and lintel structure** (`cn_post_lintel`) | 235.6 | 25 | 0.40 | 5% | MOVE TO START | Good: mostly self-explanatory |
| 118 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 236 | 100 | 4 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 119 | **Soft soldering** (`mfg_soft_solder`) | 236.4 | 80 | 0.20 | 8% | MOVE TO START | Good: mostly self-explanatory |
| 120 | **Malting** (`ag2_malting`) | 240 | 60 | 0.30 | 8% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 121 | **Oil pressing** (`ag2_oil_pressing`) | 241.6 | 60 | 0.30 | 8% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 122 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 258 | 150 | 8 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 123 | **Funded research programme** (`sc2_institution_funded_programme`) | 258 | 120 | 5 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 124 | **Referee and peer review** (`sc2_institution_referee`) | 258 | 100 | 8 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 125 | **Research group and principal investigator** (`sc2_institution_research_group`) | 258 | 100 | 5 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 126 | **Hypothesis and prediction** (`sc2_method_hypothesis`) | 258 | 90 | 8 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 127 | **Negative result and null finding** (`sc2_method_negative_result`) | 258 | 90 | 20 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 128 | **Replication and repeatability** (`sc2_method_replication`) | 258 | 80 | 10 | 15% | KEEP STARTABLE | Good: mostly self-explanatory |
| 129 | **Positional notation and place value** (`sc2_notation_positional`) | 258 | 0 | 0 | 15% | KEEP STARTABLE | Good: mostly self-explanatory |
| 130 | **Probability axioms and conditional probability** (`sc2_probability_axioms`) | 258 | 100 | 4 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 131 | **Semaphore signal** (`tr_semaphore_signal`) | 259.3 | 40 | 2 | 6% | QUESTIONABLE | Good: mostly self-explanatory |
| 132 | **Hopper wagon for bulk minerals** (`tr_hopper_wagon`) | 266.1 | 50 | 1 | 6% | GATE HARDER | Good: mostly self-explanatory |
| 133 | **The decimal point convention** (`sc2_notation_decimal_point`) | 268.3 | 20 | 2 | 15% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 134 | **Signal flags for maritime communication** (`com_signal_flags`) | 269.6 | 40 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 135 | **Quill pen** (`if_quill`) | 271.2 | 15 | 0.05 | 3% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 136 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 271.5 | 120 | 1 | 8% | QUESTIONABLE | Good: mostly self-explanatory |
| 137 | **Coal seam and mining** (`pwr_coal_seam`) | 272.8 | 150 | 1 | 25% | QUESTIONABLE | Good: mostly self-explanatory |
| 138 | **Root symbols and radical notation** (`sc2_notation_roots`) | 278.6 | 40 | 3 | 15% | GATE HARDER | Weak: assumes terminology / too terse |
| 139 | **Town planning and street layout** (`civ_town_planning`) | 278.8 | 180 | 1 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 140 | **Pyrethrum** (`ag2_pyrethrum`) | 280 | 70 | 0.30 | 12% | QUESTIONABLE | Weak: assumes terminology / too terse |
| 141 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 280 | 70 | 0.50 | 10% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 142 | **Exponent notation** (`sc2_notation_exponents`) | 281.2 | 45 | 2 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 143 | **Sprung mattress** (`hom_sprung_mattress`) | 285.5 | 120 | 1 | 8% | GATE HARDER | Good: mostly self-explanatory |
| 144 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 294 | 120 | 5 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 145 | **Momentum and impulse** (`sc2_physics_momentum`) | 296.7 | 80 | 3 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 146 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 299.3 | 80 | 5 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 147 | **Kinematics: position, velocity, acceleration** (`sc2_physics_kinematics`) | 301.9 | 90 | 2 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 148 | **Newton's law of universal gravitation** (`sc2_physics_gravitation`) | 304.4 | 100 | 5 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 149 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 309 | 40 | 0 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 150 | **Cross-staff for latitude** (`sea_cross_staff`) | 310.7 | 80 | 0.25 | 12% | QUESTIONABLE | Good: mostly self-explanatory |
| 151 | **Manometer (pressure measurement)** (`opt_manometer`) | 315.9 | 60 | 0.10 | 5% | KEEP STARTABLE | Good: mostly self-explanatory |
| 152 | **Mirror: reflective glass surface** (`tx2_mirror`) | 316 | 70 | 0.30 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 153 | **Bilge pump** (`tr_bilge_pump`) | 329.2 | 50 | 0.30 | 4% | MOVE TO START | Good: mostly self-explanatory |
| 154 | **Investment casting and lost wax** (`met_investment_casting`) | 329.8 | 100 | 0.80 | 8% | MOVE TO START | Good: mostly self-explanatory |
| 155 | **Anemometer (wind speed)** (`opt_anemometer`) | 337.2 | 60 | 0.25 | 8% | KEEP STARTABLE | Good: mostly self-explanatory |
| 156 | **Pile driving by drop hammer** (`cn_pile_driving`) | 347.9 | 40 | 0.80 | 8% | QUESTIONABLE | Good: mostly self-explanatory |
| 157 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 363 | 120 | 1 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 158 | **Papyrus** (`mat_papyrus`) | 402.5 | 20 | 0 | 0% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 159 | **Examination and credentialing** (`sc2_institution_examination`) | 412.8 | 80 | 8 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |
| 160 | **Sternpost rudder** (`sea_sternpost_rudder`) | 427.4 | 120 | 0.50 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 161 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 444 | 300 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 162 | **Paved street and sidewalk** (`civ_street_paved`) | 491.7 | 80 | 0.80 | 8% | KEEP STARTABLE | Good: mostly self-explanatory |
| 163 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 531 | 50 | 0.50 | 7% | QUESTIONABLE | Adequate: identifies it, but thin on mechanism/context |
| 164 | **Parchment** (`mat_parchment`) | 536.6 | 30 | 0 | 0% | KEEP STARTABLE | Adequate: identifies it, but thin on mechanism/context |
| 165 | **Drawing office** (`mfg_drawing_office`) | 541.8 | 150 | 0.50 | 11% | QUESTIONABLE | Good: mostly self-explanatory |
| 166 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 580 | 100 | 0.50 | 0% | MOVE TO START | Good: mostly self-explanatory |
| 167 | **Six months of listening before you act** (`arrival_orientation`) | 600 | 900 | 0.50 | 2% | QUESTIONABLE | Good: mostly self-explanatory |
| 168 | **Lateen sail** (`tr_lateen_sail`) | 629 | 80 | 0.50 | 2% | QUESTIONABLE | Good: mostly self-explanatory |
| 169 | **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | 709.4 | 200 | 1 | 10% | QUESTIONABLE | Weak: assumes terminology / too terse |
| 170 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 710.5 | 40 | 0.20 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 171 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 715 | 60 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 172 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 718 | 70 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 173 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 721 | 80 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 174 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 733 | 70 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 175 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 760 | 60 | 0.40 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 176 | **Separate foul and storm sewers** (`civ_sewer_separate`) | 765 | 120 | 1 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 177 | **Cylindrical silos for bulk grain storage** (`fud_grain_storage_silos`) | 830.4 | 200 | 1 | 10% | KEEP STARTABLE | Good: mostly self-explanatory |
| 178 | **Coach** (`lnd_coach`) | 837.7 | 200 | 2 | 20% | GATE HARDER | Good: mostly self-explanatory |
| 179 | **Silver soldering** (`mfg_silver_solder`) | 856.1 | 100 | 0.25 | 10% | QUESTIONABLE | Good: mostly self-explanatory |
| 180 | **Square rig sails** (`tr_square_rig`) | 935 | 40 | 0.60 | 4% | GATE HARDER | Good: mostly self-explanatory |
| 181 | **Skeleton-first hull construction** (`sea_skeleton_first`) | 967.7 | 250 | 1 | 22% | GATE HARDER | Weak: assumes terminology / too terse |
| 182 | **Diving bell** (`sea_diving_bell`) | 968.5 | 120 | 0.40 | 20% | QUESTIONABLE | Good: mostly self-explanatory |
| 183 | **Pawnshop and secured loan** (`fin_pawnshop`) | 1,025 | 60 | 0.30 | 10% | MOVE TO START | Good: mostly self-explanatory |
| 184 | **Decimal positional notation, zero, negative numbers, decimal fractions** (`arithmetic_positional`) | 1,032 | 450 | 1 | 10% | KEEP STARTABLE | Good: mostly self-explanatory |
| 185 | **Bottle: glass container** (`tx2_bottle`) | 1,132 | 60 | 0.30 | 15% | MOVE TO START | Adequate: identifies it, but thin on mechanism/context |
| 186 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 1,138 | 120 | 0.50 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 187 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 1,203 | 80 | 1 | 15% | KEEP STARTABLE | Good: mostly self-explanatory |
| 188 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | 1,210 | 100 | 1 | 15% | KEEP STARTABLE | Good: mostly self-explanatory |
| 189 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | 1,258 | 100 | 1 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 190 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,445 | 0 | 0 | 0% | QUESTIONABLE | Good: mostly self-explanatory |
| 191 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 1,470 | 200 | 8 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 192 | **Establish a respectable cover identity** (`identity_cover`) | 1,580 | 500 | 0.50 | 5% | QUESTIONABLE | Good: mostly self-explanatory |
| 193 | **Trading post and remote store** (`fin_trading_post`) | 1,662 | 100 | 1 | 15% | QUESTIONABLE | Good: mostly self-explanatory |
| 194 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 1,883* | 110 | 0.80 | 10% | GATE HARDER | Weak: assumes terminology / too terse |
| 195 | **Ferry and toll crossing** (`fin_ferry`) | 1,916* | 100 | 1 | 12% | MOVE TO START | Good: mostly self-explanatory |
| 196 | **Organized whaling industry for oil and meat** (`fud_whaling_industry`) | 2,070* | 300 | 1 | 30% | GATE HARDER | Good: mostly self-explanatory |
| 197 | **Lottery and state gambling** (`fin_lottery`) | 2,080* | 150 | 2 | 10% | GATE HARDER | Good: mostly self-explanatory |
| 198 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 2,112* | 100 | 1 | 25% | GATE HARDER | Good: mostly self-explanatory |
| 199 | **Census and population enumeration** (`fin_census`) | 2,532* | 200 | 2 | 15% | MOVE TO START | Good: mostly self-explanatory |
| 200 | **Inn and coaching house** (`fin_inn`) | 3,538* | 100 | 1.5 | 12% | MOVE TO START | Good: mostly self-explanatory |
| 201 | **Marine insurance** (`fin_marine_insurance`) | 4,105* | 200 | 2 | 25% | QUESTIONABLE | Good: mostly self-explanatory |
| 202 | **Postal service as paid business** (`fin_postal_service`) | 4,362* | 180 | 2 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 203 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 4,713* | 100 | 0.50 | 8% | QUESTIONABLE | Good: mostly self-explanatory |
| 204 | **Racecourse and pari-mutuel betting** (`fin_racecourse`) | 5,332* | 130 | 2 | 18% | GATE HARDER | Weak: assumes terminology / too terse |
| 205 | **Hotel and commercial lodging** (`fin_hotel`) | 5,824* | 120 | 2 | 15% | GATE HARDER | Good: mostly self-explanatory |
| 206 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 6,296* | 80 | 0.50 | 9% | MOVE TO START | Weak: assumes terminology / too terse |
| 207 | **Theatre as business** (`fin_theatre_business`) | 8,848* | 150 | 3 | 20% | GATE HARDER | Good: mostly self-explanatory |
| 208 | **Plantation and large estate agriculture** (`fin_plantation`) | 10,831* | 200 | 3 | 20% | GATE HARDER | Good: mostly self-explanatory |
| 209 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 17,415* | 80 | 0.30 | 15% | GATE HARDER | Adequate: identifies it, but thin on mechanism/context |

## Pricing / labour / time / prerequisite findings
Across the opening, the *shape* of prices is usually better than the exact numbers: tiny household/textile tricks are cheap, institutions and businesses are expensive, and the founder-hour burden is often modest compared with hired labour. That is a good model for the premise. But exact values are visibly synthetic and should not be defended too literally—the tree itself says they are calibrated estimates.

- **Zero-year projects** are overused. A 0-year floor can make sense for “the insight exists,” but many craft practices still require setup, trials, teaching, and adoption. Use a small nonzero floor (0.05–0.25 y) more consistently unless it is genuinely just recognizing an existing practice.
- **Staff prerequisites are inconsistent.** Many textile nodes require 1 artisan even when they are ordinary baseline craft; meanwhile some large institutional/legal changes can be initiated by the founder with no standing staff. Separate “can formulate” from “can implement at social scale.”
- **Prerequisites are too literal/material in places and too shallow industrially.** Having lead+tin is enough to expose “type metal,” but type metal matters because of repeatable precision casting and printing-type requirements. A watch case has no watchmaking prerequisite at all. Those are clear graph errors, not balance taste.
- **Finance/institution techs** often need standing, legal reach, or a client network more than a few hundred denarii. Their costs may be okay as project cash, but prerequisite/standing gates should carry more of the realism burden.
- **Descriptions are uneven.** Core hand-authored nodes such as scientific method and arithmetic are excellent: they explain mechanism, historical resistance, and why the player should care. Many deep-tree imported nodes are one sentence (“X does Y”) and assume the player already knows terms such as retting, selvedge, marling, seigniorage, radical notation, or skeleton-first construction. For a game whose pleasure is learning the chain, that is not enough.

## Highest-priority opening fixes
1. Grant Rome the obviously ancient everyday craft nodes now sitting in the research pool. This is the single biggest historical/UX improvement.
2. Add ecosystem prerequisites to obvious orphans: watch case, type metal, cultivated silk, modern research-degree structures, sprung mattress, mature postal/hotel/racecourse businesses, and several later transport/naval forms.
3. Rewrite terse descriptions so every node answers three questions without outside knowledge: **what is it, how does it work, why does it matter here?**
4. Audit “0 years” and institution staffing. The current opening sometimes makes a tiny craft and a society-wide convention look mechanically too similar.
5. Keep the broad 139-ish starting knowledge budget. Cutting it would make the player re-research even more things Rome plainly knew. The right move is **more baseline grants but fewer immediate frontier choices**, not simply more or less technology overall.

---

# Appendix — Rome 100 AD strict realism audit

# Rome 100 AD opening — strict realism audit

**Scope:** every one of the **139 granted nodes** and every one of the **209 projects startable at game start**, judged for historical/technical realism rather than menu size or convenience. The protagonist is treated as the briefing defines them: a competent modern adult with modern knowledge, Latin/Greek, no magical supply chain, and only Roman-era materials/institutions initially available. Therefore “invented historically in 1750” is **not** by itself a reason to gate a project; missing physical materials, tools, people, institutions, or biological stock *is*.

## Executive findings

- **The 139-grant count is not too high.** The set is mostly sensible, but it mixes technologies with resources/trade access and contains several scope/date problems. More importantly, it omits many mundane Roman crafts that then appear as “research.”

- **Rome should start with a higher heat capability.** It is granted glass, bronze/wrought iron and glass windows but only `cap_heat_0700`. The tree’s own `cap_heat_1100` text says 1100 °C is already reached wherever bloomery iron, bronze casting and glass melting are practised. That is an internal realism contradiction.

- **Immediate availability should be judged by dependency, not invention date.** Wheelbarrows, lightning conductors, quill pens, lateen-sail trials, cross-staffs and even Newtonian ideas can reasonably be attempted by a modern knower using Roman inputs. They need not be hidden merely to reproduce Earth’s historical chronology.

- **The real bad openings are missing ecosystems:** cultivated silk without silkworm/mulberry stock; watch cases without watches; type metal without antimony/typecasting/printing; spectacle frames without lenses; railway ballast/hopper wagons without a railway; paper tools/paperclips without paper/wire; modern academic credentials without an academic institution.

- **A large block should simply be granted to Rome:** census, latifundia/plantations, inns, bottles, lost-wax casting, hot riveting, oil pressing, block-and-tackle, post-and-lintel building, bone setting, obstetrics, ancient textile preparation/dyeing, mine timbering, etc. Their positive “research” cost/time is therefore a classification error more than a balance error.

- **Descriptions are strongest in the hand-authored core and weaker in many deep-branch glossary nodes.** Good descriptions explain the object/process, why it works, and what is historically/socially hard. Weak ones merely define jargon or cite a later date without telling the player what they would actually do.

## Part I — all 139 granted Roman nodes

For granted nodes the simulator charges no opening research cost, so the parameter question is mostly whether the capability belongs in the inherited state and whether the description accurately scopes it. Material nodes are assessed as **access/availability**, not as Roman invention.

| # | Granted node | Verdict | Description | Realism note |
|---:|---|---|---|---|
| 1 | **Sustained 700 C (pottery kiln)** (`cap_heat_0700`) | FIX START SET | Good/adequate | This rung is too low as Rome’s highest granted heat capability. The tree’s own `cap_heat_1100` note says 1100 °C was already reached wherever bloomery iron, bronze casting and glass melting were practised—all of which Rome has. Grant 1100 °C (or redefine the capability semantics). |
| 2 | **Muscle and animal power** (`cap_power_muscle`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 3 | **Tolerance 1 mm (skilled hand craft)** (`cap_tol_1mm`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 4 | **Amphitheatre with tiered seating** (`civ_amphitheatre`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 5 | **Roman aqueduct with inverted siphons** (`civ_aqueduct_roman`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 6 | **Roman masonry arch** (`civ_arch_roman`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 7 | **Roman fired brick and tile** (`civ_brick_tile`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 8 | **Chorobates: Roman water levelling rod** (`civ_chorobates`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 9 | **Roman concrete dome** (`civ_dome_roman`) | TOO EARLY / OVERSTATED | Needs revision | Domes are Roman, but the description defines the node by the 43.3 m Pantheon dome completed c. 126 AD, 26 years after start. Grant an early Roman concrete-dome capability; reserve Pantheon-scale mastery for later. |
| 10 | **Glass panes for windows** (`civ_glass_windows`) | CORRECT | Good/adequate | Window glass is archaeologically attested in the early imperial period; grant is sound. |
| 11 | **Insula: Roman apartment block** (`civ_insula`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 12 | **Wrought iron working and riveting** (`civ_iron_wrought`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 13 | **Marble veneer and ashlar facing** (`civ_marble_facing`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 14 | **Roman paved road with surveying** (`civ_road_paved`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 15 | **Roman sewer with gravity flow** (`civ_sewer_roman`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 16 | **Groma: Roman X-staff surveying tool** (`civ_surveying_groma`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 17 | **Barrel vault** (`civ_vault_barrel`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 18 | **Annona grain dole and administration** (`fin_annona`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 19 | **Deposit bankers (argentarii)** (`fin_argentarii`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 20 | **Auction and competitive bidding** (`fin_auction`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 21 | **Coined money** (`fin_coined_money`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 22 | **Professional associations (collegia)** (`fin_collegium`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 23 | **Contract law and enforcement** (`fin_contract_law`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 24 | **Standing bureaucracy** (`fin_government`) | BROAD BUT OK | Good/adequate | Rome certainly has a permanent state administration, but “standing bureaucracy” sounds more modern and centralized than Trajanic administration really was. Keep, tighten wording. |
| 25 | **Maritime loan at high interest** (`fin_maritime_loan`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 26 | **Permanent market and market law** (`fin_market`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 27 | **Partnership (societas)** (`fin_societas`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 28 | **Tax farming and revenue contracts** (`fin_tax_farming`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 29 | **Testament and inheritance law** (`fin_testament`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 30 | **Wage and labour payment** (`fin_wage`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 31 | **Board games, dice games, and pieces** (`hom_board_games`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 32 | **Beeswax candle** (`hom_candle_beeswax`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 33 | **Tallow candle** (`hom_candle_tallow`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 34 | **Roman cosmetics** (`hom_cosmetics_roman`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 35 | **Flush latrine with running water** (`hom_flush_latrine_simple`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 36 | **Wooden furniture** (`hom_furniture_wooden`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 37 | **Hypocaust underfloor heating** (`hom_hypocaust`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 38 | **Lead and ceramic plumbing** (`hom_lead_plumbing`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 39 | **Locks and keys** (`hom_locks_keys`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 40 | **Mirror, polished bronze** (`hom_mirror_bronze_polished`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 41 | **Musical instruments** (`hom_musical_instruments`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 42 | **Oil lamp, simple** (`hom_oil_lamp_simple`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 43 | **Perfume by enfleurage** (`hom_perfume_enfleurage`) | RENAME / VERIFY PROCESS | Needs revision | Roman perfumery is unquestionable, but the specifically named `enfleurage` process is more associated with later perfumery. Grant ancient maceration/infusion perfumery unless the cold-fat technique is specifically sourced. |
| 44 | **Public bath (thermae)** (`hom_public_bath`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 45 | **Pivoting front axle** (`lnd_axle_pivot_front`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 46 | **Bridge** (`lnd_bridge`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 47 | **Cursus publicus courier service** (`lnd_cursus_publicus`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 48 | **Four-wheeled cart** (`lnd_four_wheel_cart`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 49 | **Harness of throat and girth type** (`lnd_harness_throat_girth`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 50 | **Horse saddle (basic)** (`lnd_horse_saddle_basic`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 51 | **Litter** (`lnd_litter`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 52 | **Milestone** (`lnd_milestone`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 53 | **Mule transport** (`lnd_mule_transport`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 54 | **Ox transport** (`lnd_ox_transport`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 55 | **Paved trunk road network** (`lnd_paved_road_network`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 56 | **Two-wheeled cart** (`lnd_two_wheel_cart`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 57 | **Iron tyre (tire)** (`lnd_tyre_iron`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 58 | **Spoked wheel** (`lnd_wheel_spoked`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 59 | **Alum** (`mat_alum`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 60 | **Asbestos** (`mat_asbestos`) | CORRECT AS MATERIAL KNOWLEDGE | Good/adequate | Asbestos was known in antiquity. Treat this as material availability/knowledge, not proof of a large Roman asbestos industry. |
| 61 | **Beeswax** (`mat_beeswax`) | CORRECT AS ACCESS | Thin | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 62 | **Bitumen and naphtha seeps** (`mat_bitumen`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 63 | **Brass (by cementation)** (`mat_brass`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 64 | **Bronze** (`mat_bronze`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 65 | **Calamine (zinc carbonate/silicate ore)** (`mat_calamine`) | CORRECT AS ACCESS | Thin | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 66 | **Carbon black and lampblack** (`mat_carbon_black`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 67 | **Charcoal** (`mat_charcoal`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 68 | **Emery (Naxos)** (`mat_emery`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 69 | **Galena (lead sulfide)** (`mat_galena`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 70 | **Soda-lime glass** (`mat_glass_soda`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 71 | **Gold** (`mat_gold`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 72 | **Gypsum plaster** (`mat_gypsum`) | CORRECT AS ACCESS | Thin | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 73 | **Lead** (`mat_lead`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 74 | **Leather** (`mat_leather`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 75 | **Quicklime and slaked lime** (`mat_lime`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 76 | **Linen** (`mat_linen`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 77 | **Mercury** (`mat_mercury`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 78 | **Natron (sodium carbonate)** (`mat_natron`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 79 | **Olive oil** (`mat_olive_oil`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 80 | **Pyrolusite (manganese dioxide)** (`mat_pyrolusite`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 81 | **Salt** (`mat_salt`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 82 | **Shellac (traded)** (`mat_shellac`) | ACCESS PLAUSIBLE, EVIDENCE WEAK | Good/adequate | Indian Ocean trade makes import conceivable, but shellac specifically is much less securely evidenced as a Roman commodity than silk/pepper/cotton. Treat as rare reachability rather than ambient stock. |
| 83 | **Silk (traded)** (`mat_silk`) | CORRECT AS TRADE ACCESS | Good/adequate | Finished silk reached Rome by long-distance trade; this does not imply Roman sericulture. Good distinction if `tx2_silk_fibre` remains separately gated. |
| 84 | **Silver** (`mat_silver`) | CORRECT AS ACCESS | Thin | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 85 | **Sulfur** (`mat_sulfur`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 86 | **Tallow** (`mat_tallow`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 87 | **Tin** (`mat_tin`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 88 | **Vitriols (iron and copper sulfates)** (`mat_vitriols`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 89 | **Wrought iron (bloomery)** (`mat_wrought_iron`) | CORRECT AS ACCESS | Good/adequate | Reasonable as a material known/obtainable somewhere in Roman reach; UI should present resource access separately from invented technology. |
| 90 | **Cataract couching** (`med_cataract_couching`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 91 | **Legal protection for physicians** (`med_legal_physician`) | RENAME / SCOPE | Needs revision | Physicians did receive privileges in Roman law (citizenship/tax/public-service exemptions in various periods), but “legal protection” is too vague/universal. Name the specific privilege being granted. |
| 92 | **Opium and mandrake tinctures** (`med_opium_mandrake`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 93 | **Good surgical instrument kit** (`med_surgical_kit_good`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 94 | **Trepanation** (`med_trepanation`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 95 | **Wound suturing** (`med_wound_suturing`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 96 | **Burning glass** (`opt_burning_glass`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 97 | **Dioptra (sighting tube)** (`opt_dioptra`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 98 | **Geared mechanical transmission** (`opt_geared_mechanisms`) | DESC FIX | Needs revision | Sophisticated ancient gearing is real (Antikythera is decisive), so the grant is right. Remove/qualify claims about later optimized involute/cycloidal tooth profiles if present in the detailed text. |
| 99 | **Groma (surveying cross)** (`opt_groma`) | CORRECT | Assumes term | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 100 | **Polished metal mirror** (`opt_metal_mirror_polished`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 101 | **Steelyard balance** (`opt_steelyards`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 102 | **Sundial** (`opt_sundial`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 103 | **Water clock (clepsydra)** (`opt_water_clock`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 104 | **Water-filled globe as magnifier** (`opt_water_globe_magnifier`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 105 | **Carbon ink** (`prn_carbon_ink`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 106 | **Codex binding** (`prn_codex_bound`) | CORRECT, EMERGING | Thin | The codex is attested by Martial in the late 1st century AD. Correct at 100 AD, but it should be an emerging minority book form rather than the dominant default. |
| 107 | **Library and archive** (`prn_library_archive`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 108 | **Mosaic and fresco** (`prn_mosaic_fresco`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 109 | **Papyrus sheets** (`prn_papyrus_sheets`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 110 | **Parchment sheets** (`prn_parchment_sheets`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 111 | **Scribal copying** (`prn_scribal_copying`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 112 | **Sculpture** (`prn_sculpture`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 113 | **Seals and stamps** (`prn_seals_stamps`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 114 | **Theatre and pantomime** (`prn_theatre_pantomime`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 115 | **Wax tablets** (`prn_wax_tablets`) | CORRECT | Thin | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 116 | **Animal-driven treadmill** (`pwr_animal_treadmill`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 117 | **Force pump** (`pwr_force_pump`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 118 | **Screw press** (`pwr_screw_press_power`) | CORRECT, DIFFUSION CAVEAT | Good/adequate | Screw presses existed by the late 1st c. BC/1st c. AD, but archaeological diffusion was uneven. Correct as available know-how, not necessarily universal practice. |
| 119 | **Anchor** (`sea_anchor`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 120 | **Coastal pilotage** (`sea_coastal_pilotage`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 121 | **Large merchant sailing ships** (`sea_merchant_ships_large`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 122 | **Monsoon route to India** (`sea_monsoon_route`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 123 | **Mortise-and-tenon hull construction** (`sea_mortise_tenon`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 124 | **Pharos lighthouse** (`sea_pharos_lighthouse`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 125 | **Sounding lines** (`sea_sounding_lines`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 126 | **Spritsail** (`sea_spritsail`) | CORRECT, MARGINAL | Assumes term | Ancient iconography supports spritsails from roughly the 2nd c. BC onward. Correct to know, but it was marginal compared with the square rig. |
| 127 | **Square sail with brails** (`sea_square_sail`) | CORRECT | Assumes term | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 128 | **Steering oars** (`sea_steering_oars`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 129 | **Cotton by trade** (`tex_cotton_trade`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 130 | **Drop spindle** (`tex_drop_spindle`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 131 | **Dyeing with madder root** (`tex_dye_madder`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 132 | **Murex purple dyeing** (`tex_dye_murex`) | CORRECT | Assumes term | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 133 | **Dyeing with woad** (`tex_dye_woad`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 134 | **Felting** (`tex_felting`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 135 | **Sailcloth** (`tex_sailcloth`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 136 | **Silk by trade** (`tex_silk_trade`) | CORRECT | Thin | Rome’s elite silk consumption and eastern trade are well established. This should not unlock cultivation without live biological stock. |
| 137 | **Two-beam loom** (`tex_two_beam_loom`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 138 | **Warp-weighted loom** (`tex_warp_weighted_loom`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |
| 139 | **Wool fiber** (`tex_wool`) | CORRECT | Good/adequate | Plausible Roman knowledge/capability by 100 AD; no material realism objection found in this opening audit. |

### Starting-set changes I would make before touching gameplay balance

1. Grant or otherwise represent **~1100 °C furnace capability** at start, because the existing Roman materials/industries already imply it.
2. Replace the Pantheon-defined dome grant with an **early Roman concrete dome/vault capability**, leaving Pantheon-scale execution as a later achievement if desired.
3. Keep ancient gearing, but fix the tooth-profile overclaim.
4. Tighten vague institutional/material labels (`med_legal_physician`, shellac access, perfume process).
5. Move the clearly ancient omissions identified in Part II into the Roman inherited set (or merge duplicate ontology nodes).

## Part II — all 209 projects startable at 100 AD

Verdicts: **ALREADY ROMAN** = should be inherited; **PLAUSIBLE NOW** = a modern founder can realistically begin it with starting inputs; **STARTABLE, FIX MODEL** = the founder can begin the idea/prototype, but scope/prerequisites/cost model need revision; **MISSING GATE** = a physical/resource/institutional dependency is absent, so it should not currently be startable.

| # | Project | Live cost | Founder h | Hired labour | Floor y | Prereqs now | Verdict | Parameter check | Realism / description note |
|---:|---|---:|---:|---|---:|---|---|---|---|
| 1 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 5 | 30 | — | 0.10 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. The technique is trivial, but the description is specifically about erasing pencil marks while the opening has no pencil/graphite-writing prerequisite. Either generalise it to abrasive erasing of charcoal/leadpoint or gate it behind the writing medium. |
| 2 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 6 | 30 | 40h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 3 | **Yarn count standardisation** (`tx2_count_standard`) | 6 | 40 | 40h artisan | 0 | — | **PLAUSIBLE NOW** | Startable, but a zero calendar floor is aggressive; allow prototyping quickly while adoption/training takes time. | Adequate. A formal yarn-count standard is a plausible founder introduction; Rome had yarn grading but not this modern length-per-weight standard. It should key off a defined measurement system, not float prereq-free. |
| 4 | **Retting of flax and hemp fibres** (`tx2_retting`) | 6 | 30 | 40h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 5 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 6 | 30 | 40h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 6 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 7.5 | 40 | 50h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 7 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 9 | 40 | 60h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 8 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 9 | 40 | 60h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 9 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 9 | 40 | 60h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 10 | **Twist insertion control** (`tx2_twist_insertion`) | 9 | 50 | 60h artisan | 0 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Ancient spinners already controlled twist by feel. The modern quantified part (turns per unit length / twist multiplier) needs standards. Split tacit craft from measured specification. |
| 11 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 9 | 50 | 60h artisan | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 12 | **Bone setting** (`med_bone_setting`) | 9.3 | 0 | 50h artisan | 0.50 | med_surgical_kit_good | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 13 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 9.5 | 40 | 50h artisan | 0.10 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 14 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 9.5 | 40 | 50h artisan | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 15 | **Beam: warp holder and tension** (`tx2_beam`) | 9.9 | 40 | 60h carpenter | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 16 | **Contract of employment** (`fin_employment_contract`) | 10 | 60 | 50h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 17 | **Button: horn material** (`tx2_button_horn`) | 10 | 40 | 60h artisan | 0.10 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Horn buttons are physically easy to make now, but the node note itself places routine production in the medieval period. Startable is fine; do not treat it as something Rome already used as a common fastening system. |
| 18 | **Button: bone material** (`tx2_button_bone`) | 10.1 | 40 | 60h artisan | 0.10 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Same issue as horn buttons: technically immediate, historically not a normal Roman closure. The project is an introduction/fashion adoption, not an invention needing advanced machinery. |
| 19 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 10.5 | 50 | 70h artisan | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Cannot be conjured from Roman workshops. Cashmere requires the relevant goat populations/fibre supply from Inner/Central Asia and a trade/breeding route. |
| 20 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 10.5 | 50 | 70h artisan | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Jute is a South Asian crop/resource problem before it is a fibre-processing problem. Require seed/plant access and a suitable cultivation region. |
| 21 | **Mohair: angora goat fibre** (`tx2_mohair`) | 10.5 | 50 | 70h artisan | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. The named Angora-goat fibre depends on a specific animal population/breed and supply chain. A generic “fine goat undercoat” project could be startable; this named material should not be. |
| 22 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 10.5 | 50 | 70h artisan | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Ramie likewise needs the Asian plant and propagation stock. The technical processing is simple compared with getting the crop. |
| 23 | **Button: shell material** (`tx2_button_shell`) | 11.5 | 50 | 70h artisan | 0.15 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 24 | **Pin: sewing fastener** (`tx2_pin`) | 11.8 | 40 | 60h smith | 0.10 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Pins and dress pins existed in antiquity. If this node specifically means drawn-wire headed pins, say so and require wire drawing; otherwise Rome should simply have it. |
| 25 | **Amputation and prosthetics** (`med_amputation`) | 12.3 | 0 | 50h artisan | 0 | med_surgical_kit_good | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Amputation and crude prostheses are ancient. The Roman “Capua leg” predates the scenario by centuries. This should be inherited knowledge, though outcomes remain awful. |
| 26 | **Comb: hair grooming tool** (`tx2_comb`) | 13 | 50 | 80h artisan | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 27 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 14 | 60 | 80h carpenter | 0.30 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 28 | **Currying: leather finish dressing** (`tx2_currying`) | 15 | 60 | 100h artisan | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 29 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 16 | 80 | 80h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Formal apprenticeship contracts are attested in the Roman world (especially documentary papyri). The exact later guild-indentured form is medieval, but the underlying node is too broad to justify research. |
| 30 | **Splitting: leather layering** (`tx2_splitting`) | 16 | 70 | 100h artisan | 0.30 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 31 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 16.6 | 50 | 70h smith | 0.50 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A paperclip is not hard conceptually, but reliable cheap springy drawn wire and abundant paper are the actual prerequisites. Neither appears in this node. |
| 32 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 18 | 100 | 120h artisan | 2 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Mass sizing is startable as an idea, but it depends on a measurement standard plus systematic anthropometry and pattern production. The current prereq-free form is too detached from those enablers. |
| 33 | **Obstetric practice** (`med_obstetric_practice`) | 18.8 | 0 | 100h artisan | 0 | mat_linen | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 34 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 19.8 | 50 | 60h smith | 0.20 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 35 | **Trademark and mark of quality** (`fin_trademark`) | 20 | 80 | 100h scribe | 1 | fin_contract_law | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Maker marks are ancient; a centrally registered, enforceable trademark right is not. Keep startable as a legal reform, but require/charge for registry and enforcement rather than treating the mark itself as the invention. |
| 36 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 21 | 60 | 80h carpenter | 0.25 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 37 | **Safety pin** (`hom_safety_pin`) | 24.1 | 40 | 50h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. The Hunt-style one-piece safety pin needs suitable wire and controlled spring geometry. Wrought iron + 1 mm tolerance alone is a weak prerequisite set. |
| 38 | **Seigniorage and debasement** (`fin_seigniorage`) | 25 | 80 | 100h merchant | 0.20 | fin_coined_money | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 39 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 27.9 | 70 | 40h carpenter, 80h smith | 0.30 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A flyer belongs to the spinning-wheel/frame lineage. It should not be an isolated prereq-free metal shape. |
| 40 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 28.6 | 50 | 70h smith | 0.20 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. The modern drawing pin is mostly a sheet/wire/pin-making and paper-office ecosystem item. Gate it to those capabilities. |
| 41 | **Usury law and interest regulation** (`fin_usury_law`) | 30 | 100 | 150h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 42 | **Corset: rigid body support garment** (`tx2_corset`) | 30 | 100 | 200h artisan | 0.50 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 43 | **Toothbrush** (`hom_toothbrush`) | 30.3 | 60 | 100h artisan | 0.25 | cap_tol_1mm | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. A bristle toothbrush is technologically buildable immediately even though the familiar format is much later; Rome already has chew-sticks/tooth powders. Description correctly distinguishes those. |
| 44 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 31 | 60 | 100h artisan | 0.20 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A spectacle frame without optical lenses/spectacles is nonsense. Add the lens/spectacle prerequisite. |
| 45 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 37.5 | 80 | 150h merchant | 1 | fin_market | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 46 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 40 | 120 | 200h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Rome already had insolvency procedures (for example cessio bonorum and creditor seizure regimes). If the intended node is modern discharge/reorganisation, rename it and explain the difference. |
| 47 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 40.4 | 80 | 100h labourer | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. This is better modelled as a discoverable resource/deposit than as a technology. Prospecting can start immediately; oil-shale retorting should be separate. |
| 48 | **Tariff and import duty** (`fin_tariff`) | 47.5 | 100 | 150h merchant, 50h scribe | 2 | fin_tax_farming | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 49 | **Log line for speed** (`sea_log_line`) | 49.6 | 30 | 50h artisan | 0.10 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A log line is easy ropework, but useful speed measurement needs a reproducible time interval. Require a portable timing method or explicitly bundle one. |
| 50 | **Monopoly and exclusive grant** (`fin_monopoly`) | 51.1 | 80 | 150h merchant, 50h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 51 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 53.5 | 100 | 50h master, 150h merchant | 2 | fin_coined_money | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. Rome already operated multiple coin metals and official exchange/tariff relationships. A strict modern bimetallic standard would be a reform, but the present description is broader than that. |
| 52 | **Cartel and market sharing agreement** (`fin_cartel`) | 53.8 | 100 | 200h merchant | 1 | fin_contract_law | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 53 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 55 | 80 | 120h artisan | 0.30 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Pattern grading logically follows a sizing system and pattern-cutting practice. It should not be startable before its own conceptual parent. |
| 54 | **Block printing: carved design application** (`tx2_printing_block`) | 55.1 | 100 | 200h artisan, 80h engraver | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 55 | **Peat extraction and burning** (`pwr_peat`) | 57.4 | 100 | 200h labourer | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 56 | **Mortgage and real estate credit** (`fin_mortgage`) | 57.5 | 120 | 150h merchant, 100h scribe | 1 | fin_contract_law | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 57 | **Patent and exclusive right** (`fin_patent`) | 61.8 | 140 | 150h merchant, 100h scribe | 2 | fin_contract_law | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A patent is politically/institutionally feasible from day one only as a proposal. Completion should depend on state recognition/enforcement; the physical inventor cannot create a patent right by himself. |
| 58 | **Guild and monopoly craft** (`fin_guild`) | 68.8 | 100 | 200h master | 1 | fin_collegium | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 59 | **Hand ginning cotton** (`tex_hand_ginning`) | 69.9 | 30 | 200h labourer | 0.20 | tex_cotton_trade | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 60 | **Bill of exchange** (`fin_bill_exchange`) | 70 | 150 | 200h merchant, 100h scribe | 2 | fin_contract_law | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Bills of exchange are institutionally plausible with Roman literacy, banking and contract law. The hard part is acceptance by a merchant network, so adoption time matters more than founder craft hours. |
| 61 | **Codebook for optical signal tower** (`com_optical_codebook`) | 71.4 | 100 | 200h scribe | 0.25 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. A codebook can be written at once, but “for optical signal tower” should require or be paired with an actual signalling station/tower system. |
| 62 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 74.4 | 20 | 400h labourer | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 63 | **Toys and dolls** (`hom_toys_dolls`) | 75.5 | 60 | 60h artisan, 80h carpenter | 0.50 | cap_tol_1mm | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 64 | **Straightedge and reference straightness** (`prc_straightedge`) | 81.8 | 30 | 80h artisan, 60h smith | 0.20 | cap_tol_1mm | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 65 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 83 | 50 | 80h carpenter | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 66 | **Doll: articulated child plaything** (`tx2_doll`) | 83.5 | 80 | 150h artisan | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 67 | **Compass for navigation** (`air_compass_magnetic`) | 87.7 | 30 | 50h artisan | 0.10 | mat_silk, mat_wrought_iron | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. The navigation compass should at minimum require lodestone/magnetisation knowledge; `sea_lodestone` is simultaneously startable, so the graph currently lets the child start before the parent. |
| 68 | **Trade union and workers collegium** (`fin_trade_union`) | 88.1 | 120 | 100h master, 200h merchant | 2 | fin_collegium | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A bargaining union is not just another collegium in Trajanic Rome. Associations were politically sensitive and sometimes prohibited. The project needs a much stronger political-risk/institution requirement than an ordinary contract reform. |
| 69 | **Wheelbarrow** (`lnd_wheelbarrow`) | 89 | 30 | 80h carpenter, 30h smith | 0.50 | lnd_wheel_spoked | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. A wheelbarrow is an excellent example of something historically absent in Rome but realistically introducible immediately by a modern founder using existing wheel/carpentry skills. |
| 70 | **Umbrella** (`hom_umbrella`) | 89.7 | 80 | 60h artisan, 100h carpenter | 0.50 | cap_tol_1mm | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 71 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 97.7 | 35 | 80h mason | 0.15 | mat_gypsum | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 72 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 102 | 100 | 200h labourer | 0.50 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 73 | **Triangulated truss frame** (`civ_truss_triangulated`) | 108.4 | 120 | 200h artisan, 300h carpenter | 0.50 | civ_arch_roman | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Triangulated timber framing is physically well within Roman capability. If the node means explicit truss analysis rather than simply building triangles, the description should say so. |
| 74 | **Needle: sewing implement** (`tx2_needle`) | 111.8 | 40 | 60h smith | 0.10 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 75 | **Lodestone knowledge** (`sea_lodestone`) | 112.2 | 20 | 80h scholar | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 76 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 113.8 | 50 | 60h smith | 0.15 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 77 | **Carding: opening and aligning fibres** (`tx2_carding`) | 115.9 | 60 | 150h artisan | 0.20 | cap_tol_1mm, tex_wool | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 78 | **Guano** (`ag2_guano`) | 119 | 30 | 80h merchant | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. “Guano” as a high-grade fertilizer is mainly a geographic commodity. Mediterranean bird manure exists, but the famous concentrated deposits are not locally available; add a source/access condition. |
| 79 | **Marling** (`ag2_marling`) | 119.4 | 25 | 60h labourer | 0.15 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 80 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 124.9 | 60 | 100h artisan, 80h plumber | 0.50 | hom_flush_latrine_simple | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A water-seal trap is simple enough for Roman plumbing and can be introduced immediately. The project is realistic; the description should stress the need to keep the seal wet and ventilate drains. |
| 81 | **Mordanting dyes with alum** (`tex_mordanting`) | 129.3 | 40 | 100h artisan | 0.30 | mat_alum, tex_dye_madder | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 82 | **Stone polishing and smoothing** (`cn_stone_polish`) | 137.8 | 30 | 80h mason | 0.15 | cap_tol_1mm | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 83 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 142 | 80 | 150h smith | 0.40 | mat_wrought_iron | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A lightning conductor is historically 18th century but physically startable now by a modern knower: iron/copper conductor plus a good earth. It does not need the player to rediscover electrostatics first. It does need a credible continuous conductor and grounding detail. |
| 84 | **Liming** (`ag2_liming`) | 149.6 | 30 | 80h labourer | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 85 | **Hopping** (`ag2_hopping`) | 150 | 40 | — | 0.15 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Weak. Hopped beer is gated first by hops and a brewing tradition. A “hopping” process with no hop-plant/resource requirement is incomplete. |
| 86 | **Kite** (`air_kite_basic`) | 157.8 | 20 | 40h artisan | 0.10 | mat_linen, mat_silk | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 87 | **Composting** (`ag2_composting`) | 159.4 | 40 | 100h labourer | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 88 | **Potash** (`ag2_potash`) | 159.4 | 40 | 100h labourer | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 89 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 169.2 | 80 | 80h artisan, 100h plumber | 0.50 | hom_flush_latrine_simple | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. This is the application of the immediately preceding water-trap idea to a flushing fixture. Make that prerequisite explicit rather than allowing both independently. |
| 90 | **Sluice gate for water control** (`civ_gate_sluice`) | 183 | 100 | 250h carpenter, 100h smith | 0.60 | civ_arch_roman | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 91 | **Indigo dyeing** (`tex_indigo`) | 187.8 | 60 | 140h artisan | 0.40 | mat_natron, tex_dye_woad | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Indigo/indicum was known through Indian trade, and the reduction-vat chemistry overlaps woad dyeing. Treating the dye process as totally unknown to Rome is hard to justify. |
| 92 | **Reefing sails** (`tr_reefing`) | 200.4 | 50 | 300h sailor | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Ancient Mediterranean square sails used brails and other methods to reduce/handle sail area. A generic “reefing” node is too broad to be post-Roman unless it means a specific later reef-point system. |
| 93 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 202.8 | 40 | 100h carpenter, 60h smith | 0.50 | lnd_wheel_spoked | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 94 | **Production schedule** (`mfg_production_schedule`) | 204 | 130 | — | 0.50 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 95 | **Wooden waggonway** (`tr_wooden_waggonway`) | 204.9 | 40 | 200h carpenter | 2 | cap_power_muscle | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 96 | **Flux** (`mfg_flux`) | 209 | 60 | 60h artisan | 0.15 | —; any: {"group": "flux", "options": {"mat_borax": 1.0, "mat_rosin": 0.85, "mat_salt": 0.6}} | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 97 | **Obsidian blade knapping** (`mat_obsidian_blade`) | 210 | 40 | 600h artisan | 0.50 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 98 | **Vector control** (`md2_vector_control`) | 210.8 | 100 | 120h scholar | 2 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Breeding-site destruction and identifying mosquitoes/fleas/lice are startable modern public-health knowledge. The note wrongly bundles later chemical insecticides and resistance management; split those. |
| 99 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 216.8 | 40 | 100h artisan | 0 | mat_linen | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Linen masks are plausible; cloth “surgical gloves” are much less convincing and can become contaminated. This should be tied to hand washing/asepsis/sterilisation and worded as barrier technique, not as a rubber-glove substitute with equivalent effect. |
| 100 | **Enamelling** (`mfg_enamelling`) | 216.8 | 120 | 140h furnaceman | 0.30 | cap_heat_0700, mat_glass_soda | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Vitreous enamelling predates Rome by centuries and was used in Roman/Celtic metalwork. This should not be a new technology. |
| 101 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 217.5 | 150 | 200h artisan, 250h smith | 1 | cap_tol_1mm, mat_brass | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A wire mould and deckle is specifically a papermaking tool. Requiring brass but not paper pulp/papermaking reverses the dependency. |
| 102 | **Plaster cast immobilization** (`md2_plaster_cast`) | 218 | 100 | 120h artisan | 1 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Plaster immobilisation is a realistic founder introduction with local gypsum, but it should require bone-setting knowledge and padding/splint practice. |
| 103 | **Adhesive bonding** (`mfg_adhesive_bond`) | 219.5 | 140 | 120h artisan | 0.30 | mat_bitumen; any: {"group": "adhesive", "options": {"mat_bitumen": 1.0, "mat_gums_resins": 0.7, "mat_shellac": 0.8}} | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Adhesive bonding is prehistoric/ancient technology. If this node means formal engineering joint design with bitumen, rename it; the generic title belongs in the starting set. |
| 104 | **Japanning** (`mfg_japanning`) | 219.5 | 110 | 130h artisan | 0.25 | mat_shellac | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Weak. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 105 | **Hot riveting** (`mfg_hot_riveting`) | 220 | 80 | 100h artisan | 0.20 | mat_wrought_iron | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Hot riveting is already inside Roman wrought-iron practice; the civilization even starts with a “wrought iron working and riveting” node, making this a direct duplicate. |
| 106 | **Casting mould** (`mfg_mould`) | 222.5 | 120 | 150h artisan | 0.30 | —; any: {"group": "pattern", "options": {"mfg_pattern_metal": 0.9, "mfg_pattern_wood": 1.0}} | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Casting moulds are ancient; the note specifically describes later flask sand-casting. Rename to “green-sand flask moulding” and add metal-casting prerequisites, or grant generic mould-making. |
| 107 | **Cold riveting** (`mfg_cold_riveting`) | 223 | 100 | 120h artisan | 0.20 | mat_wrought_iron | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 108 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 223.4 | 30 | 150h carpenter, 400h labourer | 1 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. Sleepers and ballast are a railway/waggonway subtechnology. They should require rails/track before they can be a meaningful project. |
| 109 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 223.5 | 110 | 300h labourer | 0.80 | cap_tol_1mm | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. Industrial ore-pelletising presupposes a stream of fine ore, crushing/grinding and a furnace that benefits from controlled burden permeability. A 1 mm tolerance capability is irrelevant as its main gate. |
| 110 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 224.4 | 80 | 300h carpenter | 0.80 | cap_power_muscle | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Mine timbering is ancient and certainly within Roman mining practice. Later formal design standards can be a separate improvement. |
| 111 | **Painting** (`mfg_painting`) | 225 | 80 | 100h artisan | 0.20 | —; any: {"group": "paint", "options": {"enamel": 1.0, "lacquer": 0.9, "oil_paint": 1.0}} | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 112 | **Horizontal loom** (`tex_horizontal_loom`) | 225.8 | 80 | 100h artisan, 200h carpenter | 0.50 | cap_tol_1mm, tex_two_beam_loom | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 113 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 230 | 350 | 500h scribe | 2 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Good opening node. A modern founder can immediately begin teaching controlled comparison, hypothesis, replication and written reporting. The two-year floor is defensible as social/institutional adoption rather than “discovery”. |
| 114 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 230 | 60 | 200h potter | 0.50 | cap_heat_0700 | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The note itself calls terracotta ancient. Rome should not research low-fired earthenware in 100 AD. |
| 115 | **Block and tackle pulley** (`tr_block_tackle`) | 230.2 | 40 | 150h carpenter, 50h smith | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Compound pulley/block-and-tackle systems were known in the Greco-Roman world and used in cranes. Grant it. |
| 116 | **Hay making and dry storage** (`fud_hay_making_storage`) | 235 | 100 | 300h labourer | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 117 | **Post and lintel structure** (`cn_post_lintel`) | 235.6 | 25 | 50h carpenter, 100h mason | 0.40 | cap_tol_1mm | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 118 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 236 | 100 | 180h scribe | 4 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. The founder can write Newton’s laws on day one, so historical date is not a gate. But the node claims quantitative engineering transformation; that usefulness needs units, algebra/geometry and kinematics. Split “state the laws” from “operational Newtonian mechanics” or add educational dependencies. |
| 119 | **Soft soldering** (`mfg_soft_solder`) | 236.4 | 80 | 100h artisan | 0.20 | mat_lead | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 120 | **Malting** (`ag2_malting`) | 240 | 60 | — | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 121 | **Oil pressing** (`ag2_oil_pressing`) | 241.6 | 60 | — | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Oil pressing is a major Roman industry; screw/lever press technology is already present in the scenario. This is a clear starting-knowledge omission. |
| 122 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 258 | 150 | — | 8 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. A doctorate is an institutional credential, not a book the founder can write. It needs a university/school, examination authority, faculty and a credential-recognition system. |
| 123 | **Funded research programme** (`sc2_institution_funded_programme`) | 258 | 120 | — | 5 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. A funded programme can in principle begin under patronage, but a durable research programme requires an institution, trained staff and accounting. Prereq-free is too generous even if the founder can personally fund a project. |
| 124 | **Referee and peer review** (`sc2_institution_referee`) | 258 | 100 | — | 8 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. Peer review requires multiple competent peers plus a publication/communication venue. It should follow a research community, not be a solo founder project. |
| 125 | **Research group and principal investigator** (`sc2_institution_research_group`) | 258 | 100 | — | 5 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A research group and PI literally require trained researchers and an institution. Add staff/school prerequisites. |
| 126 | **Hypothesis and prediction** (`sc2_method_hypothesis`) | 258 | 90 | — | 8 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 127 | **Negative result and null finding** (`sc2_method_negative_result`) | 258 | 90 | — | 20 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. The norm “record null results” is teachable immediately, but it only makes sense as part of a scientific-method/reporting practice. Add that conceptual parent. |
| 128 | **Replication and repeatability** (`sc2_method_replication`) | 258 | 80 | — | 10 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Same for replication: startable as a norm, but completion should depend on an experimental programme and multiple practitioners. |
| 129 | **Positional notation and place value** (`sc2_notation_positional`) | 258 | 0 | — | 0 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Place value is teachable immediately. The tree should reconcile this node with `arithmetic_positional`, which later bundles decimal positional notation, zero, negative numbers and decimal fractions; right now the two overlap awkwardly. |
| 130 | **Probability axioms and conditional probability** (`sc2_probability_axioms`) | 258 | 100 | — | 4 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Formal conditional probability is not useful in a mathematical vacuum. Require at least arithmetic/fractions and preferably algebraic notation; the founder may know it, but students cannot absorb axioms without the language. |
| 131 | **Semaphore signal** (`tr_semaphore_signal`) | 259.3 | 40 | 100h carpenter, 100h smith | 2 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Semaphore is buildable with Roman carpentry, but a useful system needs stations, line-of-sight surveying and a code. Prototype-now is realistic; network adoption should be a larger project. |
| 132 | **Hopper wagon for bulk minerals** (`tr_hopper_wagon`) | 266.1 | 50 | 250h carpenter, 100h smith | 1 | —; any: {"group": "structural_casting", "options": {"mat_bronze": 0.7, "mat_bulk_steel": 0.9, "mat_cast_iron": 1.0, "mat_wrought_iron": 0.8}} | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. A hopper wagon presupposes a rail/waggonway and bulk-loading/unloading workflow. Gate it to those. |
| 133 | **The decimal point convention** (`sc2_notation_decimal_point`) | 268.3 | 20 | 40h scribe | 2 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. The decimal point is a notation convention and can be introduced early, but it only has meaning after positional decimal notation. Add that parent. |
| 134 | **Signal flags for maritime communication** (`com_signal_flags`) | 269.6 | 40 | 60h artisan | 0.50 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 135 | **Quill pen** (`if_quill`) | 271.2 | 15 | 40h scribe | 0.05 | cap_tol_1mm | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 136 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 271.5 | 120 | 80h carpenter, 200h mason | 1 | cap_heat_0700 | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 137 | **Coal seam and mining** (`pwr_coal_seam`) | 272.8 | 150 | 300h labourer, 400h miner | 1 | cap_tol_1mm | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Coal was actually used in Roman Britain and other local contexts. If “coal seam and mining” means recognising/exploiting coal, the empire should at least have regional access/knowledge; if it means systematic deep coal mining, rename it. |
| 138 | **Root symbols and radical notation** (`sc2_notation_roots`) | 278.6 | 40 | 80h scribe | 3 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Weak. Radical notation is merely a symbol, but it represents an established square-root operation. Require the mathematical concept/algebra rather than allowing an isolated glyph project. |
| 139 | **Town planning and street layout** (`civ_town_planning`) | 278.8 | 180 | 300h scholar | 1 | civ_surveying_groma | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 140 | **Pyrethrum** (`ag2_pyrethrum`) | 280 | 70 | — | 0.30 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Weak. Pyrethrum is first a botanical-resource issue. Require access to the appropriate Chrysanthemum/Tanacetum material before an insecticide programme. |
| 141 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 280 | 70 | — | 0.50 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Romans stored and transported snow/ice for elite consumption. “Ice trade” may be more organised than the evidence, but basic ice/snow refrigeration should already be known. |
| 142 | **Exponent notation** (`sc2_notation_exponents`) | 281.2 | 45 | 90h scribe | 2 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. Exponent notation can be coined immediately, but only after there is something like symbolic algebra/powers to notate. Add that dependency. |
| 143 | **Sprung mattress** (`hom_sprung_mattress`) | 285.5 | 120 | 150h artisan, 100h carpenter | 1 | cap_tol_1mm, mat_wrought_iron | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. A sprung mattress is a wire/spring-manufacturing product. Rome’s wrought iron and 1 mm hand tolerance do not supply repeatable coil springs or cheap drawn wire. |
| 144 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 294 | 120 | — | 5 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 145 | **Momentum and impulse** (`sc2_physics_momentum`) | 296.7 | 80 | 150h scribe | 3 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Momentum/impulse is transferable knowledge, but quantitative use depends on units, arithmetic/algebra and reliable time/distance measurement. The project can start as teaching, but the node is too independent. |
| 146 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 299.3 | 80 | 160h scribe | 5 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Ancient authors cite authorities, but modern bibliographic reference depends on stable editions/copies and conventions. Keep startable as a documentation reform; do not describe it as if page-level modern citation can exist before standard texts/printing. |
| 147 | **Kinematics: position, velocity, acceleration** (`sc2_physics_kinematics`) | 301.9 | 90 | 170h scribe | 2 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Kinematics is not blocked by 17th-century history, but its useful equations need algebra, units and measurement. Add those educational/measurement dependencies. |
| 148 | **Newton's law of universal gravitation** (`sc2_physics_gravitation`) | 304.4 | 100 | 180h scribe | 5 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. The founder knows universal gravitation, but teaching/testing an inverse-square quantitative law requires mathematics and astronomical measurement. Prereq-free completion is unrealistic even if day-one note-taking is not. |
| 149 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 309 | 40 | 60h artisan | 0 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Finished silk is traded to Rome; sericulture is not. Cultivation requires live silkworm eggs/stock, mulberry cultivation and closely guarded production knowledge from East Asia. Hard gate. |
| 150 | **Cross-staff for latitude** (`sea_cross_staff`) | 310.7 | 80 | 150h artisan, 100h scholar | 0.25 | cap_tol_1mm | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. A cross-staff is very simple and can be introduced immediately; Roman geometry/surveying is enough to fabricate it. Calibration and safe/accurate use are the real work. |
| 151 | **Manometer (pressure measurement)** (`opt_manometer`) | 315.9 | 60 | 60h artisan, 80h glassblower | 0.10 | cap_tol_1mm | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. A crude liquid-column manometer is physically feasible with Roman glass/ceramic tubing and scales. Startable is realistic, though the node should specify how the U-tube is made/sealed. |
| 152 | **Mirror: reflective glass surface** (`tx2_mirror`) | 316 | 70 | 100h artisan | 0.30 | mat_glass_soda | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Glass mirrors are startable only if the reflective backing process/material is specified. Rome has glass and lead/tin/silver, so this is not a historical-date problem; it is a missing process/material prerequisite problem. |
| 153 | **Bilge pump** (`tr_bilge_pump`) | 329.2 | 50 | 150h carpenter, 100h smith | 0.30 | cap_power_muscle | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Roman ships already used pumps in some contexts and the civilization starts with a force pump. A generic bilge-pump node should probably be inherited or explicitly be a shipboard adaptation of that pump. |
| 154 | **Investment casting and lost wax** (`met_investment_casting`) | 329.8 | 100 | 140h artisan | 0.80 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 155 | **Anemometer (wind speed)** (`opt_anemometer`) | 337.2 | 60 | 100h artisan, 40h carpenter, 60h smith | 0.25 | cap_tol_1mm | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 156 | **Pile driving by drop hammer** (`cn_pile_driving`) | 347.9 | 40 | 150h labourer | 0.80 | cap_power_muscle | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Roman engineers drove piles for bridges and harbour works. Drop-hammer pile driving should be starting knowledge. |
| 157 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 363 | 120 | 200h artisan | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 158 | **Papyrus** (`mat_papyrus`) | 402.5 | 20 | 60h scribe | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Papyrus sheets are already granted. A separate startable `mat_papyrus` node is a direct ontology/prerequisite inconsistency. |
| 159 | **Examination and credentialing** (`sc2_institution_examination`) | 412.8 | 80 | — | 8 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. Credentialing/examination requires a school, curriculum, examiners and social recognition. It should follow those institutions. |
| 160 | **Sternpost rudder** (`sea_sternpost_rudder`) | 427.4 | 120 | 200h carpenter, 100h smith | 0.50 | cap_tol_1mm, sea_steering_oars | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. A sternpost rudder is not just a rudder bolted onto a Roman shell-first hull. It fits better after frame/skeleton-first construction and stern structure capable of taking the loads. |
| 161 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 444 | 300 | 200h carpenter, 400h smith | 0.50 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Excellent opening project for this premise. The founder can define standards immediately; material master artefacts and adoption are what cost time. |
| 162 | **Paved street and sidewalk** (`civ_street_paved`) | 491.7 | 80 | 400h labourer, 300h mason | 0.80 | civ_road_paved | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 163 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 531 | 50 | 100h mason | 0.50 | —; any: {"group": "damp_proof", "options": {"mat_bitumen": 1.0, "mat_lead": 0.7}} | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Adequate. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 164 | **Parchment** (`mat_parchment`) | 536.6 | 30 | 80h scribe | 0 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Parchment sheets are already granted. Like papyrus, this separate material node should already be satisfied or merged. |
| 165 | **Drawing office** (`mfg_drawing_office`) | 541.8 | 150 | 200h scribe | 0.50 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 166 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 580 | 100 | 200h scholar | 0.50 | mat_olive_oil | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Dioscorides’ *De materia medica* was written in the first century AD. In a 100 AD Roman start, “herbal pharmacy (Dioscorides)” is contemporary inherited knowledge, not a future technology. |
| 167 | **Six months of listening before you act** (`arrival_orientation`) | 600 | 900 | — | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 168 | **Lateen sail** (`tr_lateen_sail`) | 629 | 80 | — | 0.50 | sea_square_sail | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. The lateen/settee family appears in Late Antiquity in the Mediterranean, but a modern founder could rig and test one using existing Roman sailcloth, spars and ships. Immediate experimentation is realistic. |
| 169 | **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | 709.4 | 200 | 900h artisan, 700h smith | 1 | tex_wool; any: {"group": "organic_material", "options": {"mat_leather": 1.0, "tex_wool": 0.6}} | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Weak. The bundle is the problem: rigid padded collar, whippletree and nailed horseshoe have different histories and engineering functions. All are physically introducible with Roman leather/iron, but they should be separate nodes with animal-testing/adoption costs. |
| 170 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 710.5 | 40 | 60h artisan | 0.20 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 171 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 715 | 60 | 100h artisan | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 172 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 718 | 70 | 120h artisan | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 173 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 721 | 80 | 140h artisan | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 174 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 733 | 70 | 120h artisan | 0.30 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Adequate. Resist dyeing is ancient globally and technically simple. Even if not common in Rome, it is realistically startable; the note should identify the resist medium and process rather than merely name the category. |
| 175 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 760 | 60 | 80h artisan | 0.40 | mat_alum | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 176 | **Separate foul and storm sewers** (`civ_sewer_separate`) | 765 | 120 | 800h labourer | 1 | civ_sewer_roman | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A separate storm/foul network is conceptually startable because Rome already has sewers, but city-scale completion is an enormous civil project. Ensure cost/time represent a pilot standard versus rebuilding a city; current title sounds system-wide. |
| 177 | **Cylindrical silos for bulk grain storage** (`fud_grain_storage_silos`) | 830.4 | 200 | 150h carpenter, 300h mason | 1 | civ_arch_roman | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Tall cylindrical grain silos are possible, but the note overstates the physics: grain pressure does not by itself exclude insects/rodents. Aeration, moisture and wall loads are the hard issues. Structural and grain-handling requirements are under-modeled. |
| 178 | **Coach** (`lnd_coach`) | 837.7 | 200 | 150h artisan, 400h carpenter, 200h smith | 2 | lnd_four_wheel_cart, lnd_harness_throat_girth, mat_wrought_iron | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 179 | **Silver soldering** (`mfg_silver_solder`) | 856.1 | 100 | 120h smith | 0.25 | cap_heat_0700, mat_silver | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Hard/silver soldering was within ancient precious-metal craft, but the note demands a 0.1 mm joint gap while the civilization only grants a 1 mm tolerance capability. Either grant the craft as tacit skill or require finer fit for the specified modern process control. |
| 180 | **Square rig sails** (`tr_square_rig`) | 935 | 40 | — | 0.60 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 181 | **Skeleton-first hull construction** (`sea_skeleton_first`) | 967.7 | 250 | 200h artisan, 600h carpenter | 1 | cap_tol_1mm, sea_mortise_tenon | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Weak. Frame/skeleton-first construction is a genuine major shipbuilding transition. A modern founder can begin trials with Roman shipwrights, so startable is plausible, but cost/time should reflect full-scale hull experiments and conservative craft resistance. |
| 182 | **Diving bell** (`sea_diving_bell`) | 968.5 | 120 | 300h carpenter, 100h smith | 0.40 | sea_anchor | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 183 | **Pawnshop and secured loan** (`fin_pawnshop`) | 1,025 | 60 | 100h merchant | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 184 | **Decimal positional notation, zero, negative numbers, decimal fractions** (`arithmetic_positional`) | 1,032 | 450 | 2500h scribe | 1 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Core knowledge-transfer node and legitimately startable immediately. The content is broad—zero, negatives and decimal fractions are distinct ideas—so adoption time should represent teaching and institutional uptake, not discovery. |
| 185 | **Bottle: glass container** (`tx2_bottle`) | 1,132 | 60 | 100h glassblower | 0.30 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Adequate. Roman glassblowers made bottles in enormous numbers. This should unquestionably be inherited. |
| 186 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 1,138 | 120 | 200h artisan | 0.50 | mat_beeswax, mat_linen, mat_silk | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A Montgolfier-type hot-air balloon is physically possible with preindustrial materials, so historical date alone does not gate it. The node is rightly expensive, but it should explicitly account for envelope mass/area, rope/tether strength, fireproofing and a heat source; “beeswax-sealed linen” may be too heavy for a man-lifting envelope without careful numbers. |
| 187 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 1,203 | 80 | 100h artisan | 1 | mat_asbestos | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Asbestos textiles were described in antiquity. Whether all literary claims are reliable, spinning asbestos is not a modern technology Rome needs to discover from scratch. |
| 188 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | 1,210 | 100 | 2500h furnaceman, 2000h labourer | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 189 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | 1,258 | 100 | 3000h carpenter | 1 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Ancient Mediterranean ships could make some progress to windward; square rigs were not literally “useless” upwind. Deep keel improves lateral resistance, but the binary description is historically/nautically wrong. Treat as an improvement, not invention of controlled navigation. |
| 190 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,445 | 0 | — | 0 | mat_lead | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The note itself says Rome had used lead sheathing for decades. That is a smoking gun: it belongs in the granted set. |
| 191 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 1,470 | 200 | 400h scholar, 200h scribe | 8 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The node cites Euclid (c. 300 BC) as its own precedent. Codified instructional texts plainly predate 100 AD; grant the generic capability and reserve later mass textbooks for printing-era nodes. |
| 192 | **Establish a respectable cover identity** (`identity_cover`) | 1,580 | 500 | 400h scribe | 0.50 | — | **PLAUSIBLE NOW** | Broadly plausible for an introduction/prototype; no obvious hard prerequisite missing. | Good. Historically later or uncommon in Rome, but physically/institutionally reasonable for a modern knower to prototype or introduce immediately with Roman inputs. |
| 193 | **Trading post and remote store** (`fin_trading_post`) | 1,662 | 100 | 150h merchant | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 194 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 1,883* | 110 | 300h furnaceman | 0.80 | mat_lead, mat_tin | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Weak. Type metal requires antimony—missing from the listed material prerequisites—and is useless without punches/matrices/typecasting/printing. Lead + tin alone cannot produce the described alloy. |
| 195 | **Ferry and toll crossing** (`fin_ferry`) | 1,916* | 100 | 100h carpenter, 150h merchant | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 196 | **Organized whaling industry for oil and meat** (`fud_whaling_industry`) | 2,070* | 300 | 200h artisan, 400h sailor | 1 | sea_merchant_ships_large | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Good. An “organised whaling industry” requires specialised hunting boats, harpoons, rendering logistics and whale grounds. Large merchant ships alone are nowhere near sufficient. |
| 197 | **Lottery and state gambling** (`fin_lottery`) | 2,080* | 150 | 200h merchant, 150h scribe | 2 | — | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Romans used lottery-like distributions and lots; a revenue-raising public lottery can be introduced immediately. If the node means the latter, make the institutional distinction clear. |
| 198 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 2,112* | 100 | 150h merchant | 1 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The generic capability/practice predates 100 AD in the Roman/Mediterranean world; description is acceptable unless it implies a later industrial version. |
| 199 | **Census and population enumeration** (`fin_census`) | 2,532* | 200 | 200h merchant, 300h scribe | 2 | fin_government | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. The Roman state literally used the census as a core fiscal/civic institution. This is one of the clearest starting-tech omissions in the whole opening set. |
| 200 | **Inn and coaching house** (`fin_inn`) | 3,538* | 100 | 150h merchant | 1.5 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Roman inns, taverns and roadside lodging are ubiquitous. This should be inherited. |
| 201 | **Marine insurance** (`fin_marine_insurance`) | 4,105* | 200 | 300h merchant, 150h scribe | 2 | fin_maritime_loan | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. True insurance is later than Roman bottomry, but the founder can realistically introduce a premium-for-indemnity contract using existing bankers, maritime loans and contract law. Adoption/underwriting practice is the work, not invention of a physical technology. |
| 202 | **Postal service as paid business** (`fin_postal_service`) | 4,362* | 180 | 200h carpenter, 250h merchant | 2 | fin_contract_law | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. No historical-date gate is needed, but the current node bundles later practice, lacks a logical parent, or overstates what the starting inputs can accomplish. |
| 203 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 4,713* | 100 | 250h smith | 0.50 | cap_heat_0700, mat_lead, mat_tin | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. Basic lead-tin soldering is ancient, but the note contains a chemistry error: 50/50 Pb-Sn is not the 183 °C eutectic; the eutectic is about 61.9% tin / 38.1% lead. Split ancient soldering from later composition optimisation and correct the number. |
| 204 | **Racecourse and pari-mutuel betting** (`fin_racecourse`) | 5,332* | 130 | 200h carpenter, 200h merchant | 2 | civ_amphitheatre, fin_argentarii | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Weak. A pooled pari-mutuel system is later, but it is easy to introduce in a Roman racing culture. The prerequisite should be a circus/race venue, not an amphitheatre; those are different building types. |
| 205 | **Hotel and commercial lodging** (`fin_hotel`) | 5,824* | 120 | 150h carpenter, 200h merchant | 2 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Commercial lodging already exists as Roman inns/mansiones/cauponae. If “hotel” means a larger modern service institution, define the distinguishing features; otherwise it is a duplicate. |
| 206 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 6,296* | 80 | 300h master | 0.50 | mat_mercury | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Weak. Mercury’s affinity for gold was known in antiquity and Roman authors describe mercury handling. Basic gold amalgamation should be inherited; the later patio process for low-grade silver ore is a separate technology. |
| 207 | **Theatre as business** (`fin_theatre_business`) | 8,848* | 150 | 300h carpenter, 200h merchant | 3 | civ_amphitheatre | **STARTABLE, FIX MODEL** | Can begin now, but prerequisites/scope are incomplete; retune cost/time only after that fix. | Good. A commercial ticket-selling theatre is institutionally possible, but Roman theatrical economics often ran through patronage/public provision. Startable as a business-model reform; `civ_amphitheatre` is the wrong venue prerequisite for theatre. |
| 208 | **Plantation and large estate agriculture** (`fin_plantation`) | 10,831* | 200 | 300h merchant | 3 | — | **ALREADY ROMAN** | Research price/labour/time should be 0 because the capability belongs in the inherited state. | Good. Latifundia and large slave-worked commercial estates are quintessentially Roman. This absolutely belongs in the starting institutional/economic state. |
| 209 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 17,415* | 80 | 60h engraver, 120h smith | 0.30 | — | **MISSING GATE** | Do not tune price yet: prerequisite/resource graph is wrong, so current cost/labour/time are not meaningful. | Adequate. A watch case has no purpose without a portable watch and the precision watchmaking chain. This is the cleanest example of a child node exposed before its parent ecosystem. |

## Counts from the strict pass

- **ALREADY ROMAN: 89**

- **PLAUSIBLE NOW: 29**

- **STARTABLE, FIX MODEL: 56**

- **MISSING GATE: 35**


These counts are descriptive, not a target. If fixing the starting set exposes more legitimate projects, that is fine. The tree should follow reality rather than be pruned to a preferred opening-menu size.

## Highest-confidence concrete fixes

- Grant `cap_heat_1100` (or reconcile its semantics with Rome’s already-granted iron/bronze/glass industries).
- Grant/merge obvious Roman practices: `fin_census`, `fin_plantation`, `fin_inn`/generic lodging, `tx2_bottle`, `met_investment_casting`, `mfg_hot_riveting`, `ag2_oil_pressing`, `tr_block_tackle`, `cn_post_lintel`, `med_bone_setting`, `med_obstetric_practice`, the basic textile prep/dyeing nodes, `mt2_timbering_safety`, `sea_lead_sheathing`, and generic textbook/codified instruction.
- Add hard gates for sericulture, watch cases, type metal, spectacle frames, papermaking mould/deckle, railway-specific components, and crop/animal resources such as jute/ramie/cashmere/mohair/pyrethrum/hops.
- Correct `mt2_solder_lead_tin`: **50/50 Pb-Sn is not the 183 °C eutectic**; the eutectic is about 61.9% Sn / 38.1% Pb.
- Split bundled nodes whose components have different prerequisites (`horse_collar`; “vector control”; parts of the science-notation chain).
- Fix venue/domain mismatches: pari-mutuel horse racing wants a **circus/racecourse**, not an amphitheatre; theatre business wants a theatre, not an amphitheatre.

## Description standard I recommend

Every node should answer four things in plain language: **(1) what it is, (2) how it physically/institutionally works, (3) what prerequisite makes it possible here, and (4) what the founder must actually do to introduce it.** Avoid entries that only define specialist vocabulary (“selvedge”, “marling”, “seigniorage”, “radical notation”, “skeleton-first”) without enough explanation for a non-specialist player.

## Evidence notes used to resolve disputed cases

- Roman cataract couching is directly described by Celsus and is well attested in histories of ancient ophthalmology.
- Martial, late 1st century AD, is standard evidence for literary codices, so codex binding at a 100 AD start is plausible but still emerging.
- Archaeological work places Roman window glass in the early imperial period.
- Ancient Mediterranean iconography supports spritsails from roughly the 2nd century BC onward, though as a marginal rig.
- Screw presses existed by the late 1st century BC / 1st century AD, but diffusion was uneven.
- The lightning conductor is an 18th-century historical invention, yet this scenario’s protagonist already knows the principle; its relevant dependencies are conductor continuity, grounding and installation, not rediscovering Franklin.
- The modern bristle toothbrush is much later than Rome; ancient tooth-cleaning sticks are much older. That makes a bristle brush a plausible founder introduction, not inherited Roman practice.



---

# Appendix — Other civilizations strict realism audit

# Other civilizations — opening realism audit

This follows the same standard as the Rome audit: **historical/technical realism, not menu size**. A later invention can be immediately researchable if a modern founder could actually build/introduce it from local inputs; a project is wrong only when the society should already have it, or when the graph skips a real material/tool/institution/geographic prerequisite.

## Cross-civilization finding: the ambient layer is not civilization-neutral

The engine auto-grants a large tier-0/ambient package to every civilization. That package is heavily Roman/Mediterranean in content. This is a minor wording problem for Han or medieval England, a substantial distortion for Viking Scandinavia, and **catastrophic for the Mexica start**. The Mexica briefing explicitly says “no iron, no wheel in practical use,” yet the live opening grants wrought-iron working, iron tyres, spoked wheels, glass windows, lead plumbing and coined money. This is an internal contradiction visible without any external historical argument.

| Civilization | Year | Live granted | Live startable | Clear bad inherited grants flagged | Suspicious/mis-scoped inherited grants |
|---|---:|---:|---:|---:|---:|
| The Later Han Empire | 100 | 133 | 257 | 15 | 8 |
| Scandinavia in the Viking age | 900 | 125 | 233 | 23 | 10 |
| England under Edward I | 1300 | 130 | 272 | 9 | 6 |
| The Mexica Triple Alliance | 1500 | 114 | 211 | 54 | 27 |

# The Later Han Empire (100)

## Explicit civilization seeds

| Seed | Verdict | Note |
|---|---|---|
| **Tall shaft blast furnace and cast iron** (`blast_furnace`) | GOOD | Cast iron and blast-furnace production are genuine major Han advantages. |
| **Cast iron** (`mat_cast_iron`) | GOOD | Correct material capability. |
| **Sustained 1300 C (water-blown continuous blast)** (`cap_heat_1300`) | GOOD / APPROXIMATE | A continuous blast furnace implies temperatures in this class; exact capability wording is coarse but defensible. |
| **Rag paper from linen** (`rag_paper`) | OVERSTATED | Paper belongs in the Han start, but this node describes a mature rag-pulp process with a water-driven stamper. Early Han paper predates Cai Lun, but this exact industrial recipe is too developed for 100 AD. |
| **Rag paper** (`mat_paper`) | GOOD | Paper existed in China before the traditional 105 AD Cai Lun date; access is defensible. |
| **Crank, connecting rod, flywheel, cam and trip hammer** (`crank_conrod`) | BUNDLED TOO FAR | The node bundles crank, connecting rod, flywheel, cam and trip hammer as one inherited package. Han water machinery supports some linkage sophistication, not this entire later mechanical toolkit. |
| **Water-driven double-acting bellows** (`bellows_water_blown`) | GOOD | Du Shi is traditionally credited with water-powered blast bellows in 31 AD; appropriate. |
| **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | TOO EARLY / OVERBUNDLED | Han harness improved substantially, but the fully rigid padded horse collar plus whippletree plus nailed horseshoe is a later bundle. |
| **Mechanical seed drill** (`fud_seed_drill`) | GOOD | Multi-tube seed-drill technology is plausibly Han and belongs in the start. |
| **Heavy mouldboard plough with coulter (regional)** (`fud_heavy_mouldboard_plough_coulter`) | GOOD / REGIONAL WORDING | Advanced iron ploughs and mouldboard-like ploughing are appropriate; the node wording is Euro-regional and should be localized. |
| **Sternpost rudder** (`sea_sternpost_rudder`) | SCOPE FIX | Chinese stern-mounted axial rudders are plausible by this period, but the description is a later European-style sternpost/gudgeon/tiller package. Rename to the actual Han form. |
| **Magnetic compass** (`sea_magnetic_compass`) | TOO EARLY AS NAVIGATION | Han knowledge of lodestone/direction is plausible; a pivoted navigational compass card for open-sea navigation is not a 100 AD inherited capability. |

## Inherited/granted opening state — all nodes

| # | Granted node | Realism flag | Description |
|---:|---|---|---|
| 1 | **Water-driven double-acting bellows** (`bellows_water_blown`) | GOOD | Adequate/good |
| 2 | **Tall shaft blast furnace and cast iron** (`blast_furnace`) | GOOD | Adequate/good |
| 3 | **Sustained 700 C (pottery kiln)** (`cap_heat_0700`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 4 | **Sustained 1300 C (water-blown continuous blast)** (`cap_heat_1300`) | GOOD / APPROXIMATE | Adequate/good |
| 5 | **Muscle and animal power** (`cap_power_muscle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 6 | **Tolerance 1 mm (skilled hand craft)** (`cap_tol_1mm`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 7 | **Glass panes for windows** (`civ_glass_windows`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 8 | **Wrought iron working and riveting** (`civ_iron_wrought`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 9 | **Marble veneer and ashlar facing** (`civ_marble_facing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 10 | **Crank, connecting rod, flywheel, cam and trip hammer** (`crank_conrod`) | BUNDLED TOO FAR | Adequate/good |
| 11 | **Auction and competitive bidding** (`fin_auction`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 12 | **Coined money** (`fin_coined_money`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 13 | **Contract law and enforcement** (`fin_contract_law`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 14 | **Standing bureaucracy** (`fin_government`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 15 | **Maritime loan at high interest** (`fin_maritime_loan`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 16 | **Permanent market and market law** (`fin_market`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 17 | **Tax farming and revenue contracts** (`fin_tax_farming`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 18 | **Testament and inheritance law** (`fin_testament`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 19 | **Wage and labour payment** (`fin_wage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 20 | **Heavy mouldboard plough with coulter (regional)** (`fud_heavy_mouldboard_plough_coulter`) | GOOD / REGIONAL WORDING | Adequate/good |
| 21 | **Mechanical seed drill** (`fud_seed_drill`) | GOOD | Adequate/good |
| 22 | **Board games, dice games, and pieces** (`hom_board_games`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 23 | **Beeswax candle** (`hom_candle_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 24 | **Tallow candle** (`hom_candle_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 25 | **Flush latrine with running water** (`hom_flush_latrine_simple`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 26 | **Wooden furniture** (`hom_furniture_wooden`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 27 | **Hypocaust underfloor heating** (`hom_hypocaust`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 28 | **Lead and ceramic plumbing** (`hom_lead_plumbing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 29 | **Locks and keys** (`hom_locks_keys`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 30 | **Mirror, polished bronze** (`hom_mirror_bronze_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 31 | **Musical instruments** (`hom_musical_instruments`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 32 | **Oil lamp, simple** (`hom_oil_lamp_simple`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 33 | **Perfume by enfleurage** (`hom_perfume_enfleurage`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 34 | **Public bath (thermae)** (`hom_public_bath`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 35 | **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | TOO EARLY / OVERBUNDLED | Adequate/good |
| 36 | **Pivoting front axle** (`lnd_axle_pivot_front`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 37 | **Bridge** (`lnd_bridge`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 38 | **Four-wheeled cart** (`lnd_four_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 39 | **Harness of throat and girth type** (`lnd_harness_throat_girth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 40 | **Horse saddle (basic)** (`lnd_horse_saddle_basic`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 41 | **Litter** (`lnd_litter`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 42 | **Milestone** (`lnd_milestone`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 43 | **Mule transport** (`lnd_mule_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 44 | **Ox transport** (`lnd_ox_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 45 | **Paved trunk road network** (`lnd_paved_road_network`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 46 | **Two-wheeled cart** (`lnd_two_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 47 | **Iron tyre (tire)** (`lnd_tyre_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 48 | **Spoked wheel** (`lnd_wheel_spoked`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 49 | **Alum** (`mat_alum`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 50 | **Asbestos** (`mat_asbestos`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 51 | **Beeswax** (`mat_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 52 | **Bitumen and naphtha seeps** (`mat_bitumen`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 53 | **Brass (by cementation)** (`mat_brass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 54 | **Bronze** (`mat_bronze`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 55 | **Calamine (zinc carbonate/silicate ore)** (`mat_calamine`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 56 | **Carbon black and lampblack** (`mat_carbon_black`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 57 | **Cast iron** (`mat_cast_iron`) | GOOD | Adequate/good |
| 58 | **Charcoal** (`mat_charcoal`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 59 | **Emery (Naxos)** (`mat_emery`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 60 | **Galena (lead sulfide)** (`mat_galena`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 61 | **Soda-lime glass** (`mat_glass_soda`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 62 | **Gold** (`mat_gold`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 63 | **Gypsum plaster** (`mat_gypsum`) | NO OBVIOUS HARD CONFLICT | Thin |
| 64 | **Lead** (`mat_lead`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 65 | **Leather** (`mat_leather`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 66 | **Quicklime and slaked lime** (`mat_lime`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 67 | **Linen** (`mat_linen`) | NO OBVIOUS HARD CONFLICT | Assumes term |
| 68 | **Mercury** (`mat_mercury`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 69 | **Natron (sodium carbonate)** (`mat_natron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 70 | **Olive oil** (`mat_olive_oil`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 71 | **Rag paper** (`mat_paper`) | GOOD | Adequate/good |
| 72 | **Pyrolusite (manganese dioxide)** (`mat_pyrolusite`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 73 | **Salt** (`mat_salt`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 74 | **Shellac (traded)** (`mat_shellac`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 75 | **Silk (traded)** (`mat_silk`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 76 | **Silver** (`mat_silver`) | NO OBVIOUS HARD CONFLICT | Thin |
| 77 | **Sulfur** (`mat_sulfur`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 78 | **Tallow** (`mat_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 79 | **Tin** (`mat_tin`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 80 | **Vitriols (iron and copper sulfates)** (`mat_vitriols`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 81 | **Wrought iron (bloomery)** (`mat_wrought_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 82 | **Cataract couching** (`med_cataract_couching`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 83 | **Legal protection for physicians** (`med_legal_physician`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 84 | **Opium and mandrake tinctures** (`med_opium_mandrake`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 85 | **Good surgical instrument kit** (`med_surgical_kit_good`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 86 | **Trepanation** (`med_trepanation`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 87 | **Wound suturing** (`med_wound_suturing`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 88 | **Burning glass** (`opt_burning_glass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 89 | **Dioptra (sighting tube)** (`opt_dioptra`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 90 | **Geared mechanical transmission** (`opt_geared_mechanisms`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 91 | **Groma (surveying cross)** (`opt_groma`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 92 | **Polished metal mirror** (`opt_metal_mirror_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 93 | **Steelyard balance** (`opt_steelyards`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 94 | **Sundial** (`opt_sundial`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 95 | **Water clock (clepsydra)** (`opt_water_clock`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 96 | **Water-filled globe as magnifier** (`opt_water_globe_magnifier`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 97 | **Carbon ink** (`prn_carbon_ink`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 98 | **Codex binding** (`prn_codex_bound`) | NO OBVIOUS HARD CONFLICT | Thin |
| 99 | **Library and archive** (`prn_library_archive`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 100 | **Mosaic and fresco** (`prn_mosaic_fresco`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 101 | **Papyrus sheets** (`prn_papyrus_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 102 | **Parchment sheets** (`prn_parchment_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 103 | **Scribal copying** (`prn_scribal_copying`) | NO OBVIOUS HARD CONFLICT | Thin |
| 104 | **Sculpture** (`prn_sculpture`) | NO OBVIOUS HARD CONFLICT | Thin |
| 105 | **Seals and stamps** (`prn_seals_stamps`) | NO OBVIOUS HARD CONFLICT | Thin |
| 106 | **Theatre and pantomime** (`prn_theatre_pantomime`) | WRONG / FOREIGN / ANACHRONISTIC | Thin |
| 107 | **Wax tablets** (`prn_wax_tablets`) | NO OBVIOUS HARD CONFLICT | Thin |
| 108 | **Animal-driven treadmill** (`pwr_animal_treadmill`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 109 | **Force pump** (`pwr_force_pump`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 110 | **Screw press** (`pwr_screw_press_power`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 111 | **Rag paper from linen** (`rag_paper`) | OVERSTATED | Adequate/good |
| 112 | **Anchor** (`sea_anchor`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 113 | **Coastal pilotage** (`sea_coastal_pilotage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 114 | **Magnetic compass** (`sea_magnetic_compass`) | TOO EARLY AS NAVIGATION | Adequate/good |
| 115 | **Large merchant sailing ships** (`sea_merchant_ships_large`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 116 | **Monsoon route to India** (`sea_monsoon_route`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 117 | **Mortise-and-tenon hull construction** (`sea_mortise_tenon`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 118 | **Sounding lines** (`sea_sounding_lines`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 119 | **Spritsail** (`sea_spritsail`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 120 | **Square sail with brails** (`sea_square_sail`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 121 | **Steering oars** (`sea_steering_oars`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 122 | **Sternpost rudder** (`sea_sternpost_rudder`) | SCOPE FIX | Adequate/good |
| 123 | **Cotton by trade** (`tex_cotton_trade`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 124 | **Drop spindle** (`tex_drop_spindle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 125 | **Dyeing with madder root** (`tex_dye_madder`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 126 | **Murex purple dyeing** (`tex_dye_murex`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 127 | **Dyeing with woad** (`tex_dye_woad`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 128 | **Felting** (`tex_felting`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 129 | **Sailcloth** (`tex_sailcloth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 130 | **Silk by trade** (`tex_silk_trade`) | NO OBVIOUS HARD CONFLICT | Thin |
| 131 | **Two-beam loom** (`tex_two_beam_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 132 | **Warp-weighted loom** (`tex_warp_weighted_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 133 | **Wool fiber** (`tex_wool`) | NO OBVIOUS HARD CONFLICT | Adequate/good |

## Immediately startable opening projects — all nodes

`BASELINE CONTAMINATED` means the project is startable because at least one of its direct prerequisites is an inherited node flagged above as wrong/foreign/anachronistic. `GENERIC MISSING GATE` carries over a dependency defect already identified in the Rome audit and is not a judgment that the civilization is “too advanced.”

| # | Project | Cost | Founder h | Hired labour | Floor y | Prereqs | Realism flag | Description |
|---:|---|---:|---:|---|---:|---|---|---|
| 1 | **Chaff cutter** (`ag2_chaff_cutter`) | 166.1 | 50 | 140h smith | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 2 | **Composting** (`ag2_composting`) | 140.6 | 40 | 100h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 3 | **Contour ploughing** (`ag2_contour_ploughing`) | 210.0 | 70 | — | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 4 | **Coulter** (`ag2_coulter`) | 151.1 | 40 | 120h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Thin |
| 5 | **Cultivator** (`ag2_cultivator`) | 252.0 | 70 | 220h smith | 0.35 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 6 | **Grafting** (`ag2_grafting`) | 157.5 | 50 | — | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 7 | **Guano** (`ag2_guano`) | 120.7 | 30 | 80h merchant | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 8 | **Harrow** (`ag2_harrow`) | 138.1 | 45 | 100h smith | 0.25 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 9 | **Hopping** (`ag2_hopping`) | 112.5 | 40 | — | 0.15 | — | GENERIC MISSING GATE | Adequate/good |
| 10 | **Layering** (`ag2_layering`) | 118.1 | 40 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 11 | **Liming** (`ag2_liming`) | 132.0 | 30 | 80h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 12 | **Malting** (`ag2_malting`) | 180.0 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 13 | **Marling** (`ag2_marling`) | 105.4 | 25 | 60h labourer | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 14 | **Oil pressing** (`ag2_oil_pressing`) | 181.2 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 15 | **Potash** (`ag2_potash`) | 140.6 | 40 | 100h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 16 | **Pyrethrum** (`ag2_pyrethrum`) | 210.0 | 70 | — | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 17 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 241.5 | 70 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 18 | **Roller** (`ag2_roller`) | 161.4 | 40 | 80h smith | 0.25 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 19 | **Root cutter** (`ag2_root_cutter`) | 225.0 | 60 | 180h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 20 | **Subsoiler** (`ag2_subsoiler`) | 218.6 | 55 | 180h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 21 | **Tedder** (`ag2_tedder`) | 240.1 | 65 | 200h smith | 0.35 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 22 | **Compass for navigation** (`air_compass_magnetic`) | 66.2 | 30 | 50h artisan | 0.1 | mat_silk, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 23 | **Kite** (`air_kite_basic`) | 118.4 | 20 | 40h artisan | 0.1 | mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 24 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 1,003.8 | 120 | 200h artisan | 0.5 | mat_beeswax, mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 25 | **Decimal positional notation, zero, negative numbers, decimal fractions** (`arithmetic_positional`) | 360.0 | 450 | 2500h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 26 | **Six months of listening before you act** (`arrival_orientation`) | 543.4 | 900 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 27 | **White phosphorus extraction from bone ash** (`chm_phosphorus_extraction`) | 1,668.0 | 120 | 150h furnaceman | 0.5 | cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 28 | **Roman masonry arch** (`civ_arch_roman`) | 276.9 | 60 | 120h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 29 | **Roman fired brick and tile** (`civ_brick_tile`) | 158.4 | 40 | 80h potter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 30 | **Chorobates: Roman water levelling rod** (`civ_chorobates`) | 98.3 | 25 | 30h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 31 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 107.9 | 80 | 150h smith | 0.4 | mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 32 | **Groma: Roman X-staff surveying tool** (`civ_surveying_groma`) | 81.3 | 20 | 20h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 33 | **Block and tackle with rope** (`cn_block_tackle_hoist`) | 204.9 | 30 | 60h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 34 | **Treadwheel crane** (`cn_crane_treadwheel`) | 412.3 | 55 | 100h carpenter, 80h labourer | 0.7 | cap_power_muscle, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 35 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 398.2 | 50 | 100h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 36 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 122.1 | 35 | 80h mason | 0.15 | mat_gypsum | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 37 | **Pile driving by drop hammer** (`cn_pile_driving`) | 340.4 | 40 | 150h labourer | 0.8 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 38 | **Post and lintel structure** (`cn_post_lintel`) | 176.8 | 25 | 50h carpenter, 100h mason | 0.4 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 39 | **Stone quarrying with wedge** (`cn_quarrying_wedge`) | 89.8 | 20 | 100h labourer | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 40 | **Timber scaffolding system** (`cn_scaffolding`) | 488.6 | 50 | 120h carpenter | 0.6 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 41 | **Soil compaction by roller** (`cn_soil_compaction`) | 717.6 | 70 | 120h labourer | 1 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 42 | **Stone polishing and smoothing** (`cn_stone_polish`) | 103.4 | 30 | 80h mason | 0.15 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 43 | **Codebook for optical signal tower** (`com_optical_codebook`) | 31.5 | 100 | 200h scribe | 0.25 | — | GENERIC MISSING GATE | Adequate/good |
| 44 | **Signal flags for maritime communication** (`com_signal_flags`) | 101.1 | 40 | 60h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 45 | **Horse gin** (`en_horse_gin`) | 63.1 | 30 | 150h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 46 | **Spring motor (large clockwork)** (`en_spring_motor`) | 7.9 | 80 | — | 0.8 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 47 | **Treadwheel** (`en_treadwheel`) | 30.3 | 20 | 100h carpenter | 0.2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 48 | **Annona grain dole and administration** (`fin_annona`) | 3,788.8 | 600 | 200h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 49 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 14.5 | 80 | 80h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 50 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 35.2 | 80 | 150h merchant | 1 | fin_market | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 51 | **Deposit bankers (argentarii)** (`fin_argentarii`) | 1,369.3 | 150 | 60h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 52 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 36.2 | 120 | 200h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 53 | **Bill of exchange** (`fin_bill_exchange`) | 63.4 | 150 | 200h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 54 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 48.5 | 100 | 50h master, 150h merchant | 2 | fin_coined_money | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 55 | **Census and population enumeration** (`fin_census`) | 1,091.9 | 200 | 200h merchant, 300h scribe | 2 | fin_government | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 56 | **Professional associations (collegia)** (`fin_collegium`) | 822.3 | 120 | 40h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 57 | **Contract of employment** (`fin_employment_contract`) | 9.1 | 60 | 50h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 58 | **Ferry and toll crossing** (`fin_ferry`) | 1,943.6 | 100 | 100h carpenter, 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 59 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 1,867.6 | 100 | 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 60 | **Hotel and commercial lodging** (`fin_hotel`) | 5,331.9 | 120 | 150h carpenter, 200h merchant | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 61 | **Inn and coaching house** (`fin_inn`) | 3,238.6 | 100 | 150h merchant | 1.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 62 | **Lottery and state gambling** (`fin_lottery`) | 1,883.7 | 150 | 200h merchant, 150h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 63 | **Marine insurance** (`fin_marine_insurance`) | 3,717.6 | 200 | 300h merchant, 150h scribe | 2 | fin_maritime_loan | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 64 | **Mortgage and real estate credit** (`fin_mortgage`) | 52.1 | 120 | 150h merchant, 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 65 | **Pawnshop and secured loan** (`fin_pawnshop`) | 928.3 | 60 | 100h merchant | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 66 | **Plantation and large estate agriculture** (`fin_plantation`) | 9,898.5 | 200 | 300h merchant | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 67 | **Postal service as paid business** (`fin_postal_service`) | 4,609.6 | 180 | 200h carpenter, 250h merchant | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 68 | **Seigniorage and debasement** (`fin_seigniorage`) | 22.6 | 80 | 100h merchant | 0.2 | fin_coined_money | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 69 | **Partnership (societas)** (`fin_societas`) | 275.3 | 40 | 20h scribe | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 70 | **Tariff and import duty** (`fin_tariff`) | 43.0 | 100 | 150h merchant, 50h scribe | 2 | fin_tax_farming | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 71 | **Trademark and mark of quality** (`fin_trademark`) | 18.1 | 80 | 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 72 | **Trading post and remote store** (`fin_trading_post`) | 1,559.1 | 100 | 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 73 | **Usury law and interest regulation** (`fin_usury_law`) | 27.2 | 100 | 150h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 74 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 272.2 | 120 | 200h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 75 | **Hay making and dry storage** (`fud_hay_making_storage`) | 141.0 | 100 | 300h labourer | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 76 | **Mechanical grain reaper** (`fud_mechanical_reaper`) | 570.1 | 300 | 200h carpenter, 150h smith | 1 | cap_tol_1mm, horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 77 | **Organized whaling industry for oil and meat** (`fud_whaling_industry`) | 1,552.5 | 300 | 200h artisan, 400h sailor | 1 | sea_merchant_ships_large | GENERIC MISSING GATE | Adequate/good |
| 78 | **Button with eyelet** (`hom_button`) | 24.3 | 40 | 60h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 79 | **Roman cosmetics** (`hom_cosmetics_roman`) | 60.0 | 20 | — | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 80 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 3.8 | 30 | — | 0.1 | — | GENERIC MISSING GATE | Adequate/good |
| 81 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 203.6 | 120 | 80h carpenter, 200h mason | 1 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 82 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 149.2 | 80 | 80h artisan, 100h plumber | 0.5 | hom_flush_latrine_simple | GENERIC MISSING GATE | Adequate/good |
| 83 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 110.2 | 60 | 100h artisan, 80h plumber | 0.5 | hom_flush_latrine_simple | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 84 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 62.3 | 50 | 80h carpenter | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 85 | **Safety pin** (`hom_safety_pin`) | 18.3 | 40 | 50h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 86 | **Sprung mattress** (`hom_sprung_mattress`) | 215.6 | 120 | 150h artisan, 100h carpenter | 1 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 87 | **Toothbrush** (`hom_toothbrush`) | 22.7 | 60 | 100h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 88 | **Toys and dolls** (`hom_toys_dolls`) | 56.6 | 60 | 60h artisan, 80h carpenter | 0.5 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 89 | **Umbrella** (`hom_umbrella`) | 67.6 | 80 | 60h artisan, 100h carpenter | 0.5 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 90 | **Establish a respectable cover identity** (`identity_cover`) | 1,430.9 | 500 | 400h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 91 | **Carbon paper** (`if_carbon_paper`) | 376.3 | 70 | 200h artisan | 1 | mat_carbon_black, mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 92 | **Quill pen** (`if_quill`) | 94.6 | 15 | 40h scribe | 0.05 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Thin |
| 93 | **Coach** (`lnd_coach`) | 855.9 | 200 | 150h artisan, 400h carpenter, 200h smith | 2 | lnd_four_wheel_cart, lnd_harness_throat_girth, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 94 | **Cursus publicus courier service** (`lnd_cursus_publicus`) | 0.0 | 0 | — | 0 | lnd_horse_saddle_basic, lnd_paved_road_network | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 95 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 208.1 | 40 | 100h carpenter, 60h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 96 | **Wheelbarrow** (`lnd_wheelbarrow`) | 91.3 | 30 | 80h carpenter, 30h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 97 | **Obsidian blade knapping** (`mat_obsidian_blade`) | 190.2 | 40 | 600h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 98 | **Papyrus** (`mat_papyrus`) | 140.4 | 20 | 60h scribe | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 99 | **Parchment** (`mat_parchment`) | 187.2 | 30 | 80h scribe | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 100 | **Plaster cast immobilization** (`md2_plaster_cast`) | 163.5 | 100 | 120h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 101 | **Vector control** (`md2_vector_control`) | 186.0 | 100 | 120h scholar | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 102 | **Amputation and prosthetics** (`med_amputation`) | 9.3 | 0 | 50h artisan | 0 | med_surgical_kit_good | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 103 | **Bone setting** (`med_bone_setting`) | 7.0 | 0 | 50h artisan | 0.5 | med_surgical_kit_good | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 104 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 435.0 | 100 | 200h scholar | 0.5 | mat_olive_oil | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 105 | **Obstetric practice** (`med_obstetric_practice`) | 14.1 | 0 | 100h artisan | 0 | mat_linen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 106 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 162.6 | 40 | 100h artisan | 0 | mat_linen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 107 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | 747.2 | 100 | 2500h furnaceman, 2000h labourer | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 108 | **Green sand molding for casting** (`met_green_sand_mold`) | 210.6 | 80 | 120h artisan, 100h labourer | 1 | cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 109 | **Investment casting and lost wax** (`met_investment_casting`) | 160.8 | 100 | 140h artisan | 0.8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 110 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 66.4 | 20 | 400h labourer | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 111 | **Adhesive bonding** (`mfg_adhesive_bond`) | 164.6 | 140 | 120h artisan | 0.3 | mat_bitumen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 112 | **Cold riveting** (`mfg_cold_riveting`) | 169.5 | 100 | 120h artisan | 0.2 | mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 113 | **Drawing office** (`mfg_drawing_office`) | 189.0 | 150 | 200h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 114 | **Enamelling** (`mfg_enamelling`) | 162.6 | 120 | 140h furnaceman | 0.3 | cap_heat_0700, mat_glass_soda | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 115 | **Flux** (`mfg_flux`) | 156.8 | 60 | 60h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 116 | **Hot riveting** (`mfg_hot_riveting`) | 167.2 | 80 | 100h artisan | 0.2 | mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 117 | **Japanning** (`mfg_japanning`) | 164.6 | 110 | 130h artisan | 0.25 | mat_shellac | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 118 | **Casting mould** (`mfg_mould`) | 166.9 | 120 | 150h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 119 | **Painting** (`mfg_painting`) | 168.8 | 80 | 100h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 120 | **Production schedule** (`mfg_production_schedule`) | 90.0 | 130 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 121 | **Silver soldering** (`mfg_silver_solder`) | 642.1 | 100 | 120h smith | 0.25 | cap_heat_0700, mat_silver | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 122 | **Soft soldering** (`mfg_soft_solder`) | 177.3 | 80 | 100h artisan | 0.2 | mat_lead | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 123 | **Tumbling** (`mfg_tumbling`) | 189.6 | 110 | 100h artisan | 0.3 | mat_cast_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 124 | **Bomb, general purpose** (`mil_bomb_general_purpose`) | 46.6 | 70 | 85h artisan, 70h smith | 0.5 | mat_cast_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 125 | **Naval mine** (`mil_naval_mine`) | 34.4 | 70 | 80h artisan, 60h smith | 0.5 | mat_cast_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 126 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 4,722.0 | 80 | 300h master | 0.5 | mat_mercury | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 127 | **Basic Bessemer converter for steel from iron-ore matte** (`mt2_basic_converter`) | 200.3 | 160 | 500h furnaceman | 1.5 | blast_furnace, cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 128 | **Cement varieties: Portland and alternatives for construction** (`mt2_cement_varieties`) | 198.0 | 160 | 400h furnaceman | 1.2 | cap_heat_1300, mat_lime | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 129 | **Copper converter: blowing air through molten matte** (`mt2_copper_converter`) | 198.4 | 180 | 500h furnaceman | 1.5 | bellows_water_blown, cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 130 | **Copper smelting in reverberatory furnace** (`mt2_copper_reverberatory`) | 186.0 | 120 | 350h furnaceman | 1 | bellows_water_blown, cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 131 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 203.3 | 60 | 200h potter | 0.5 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 132 | **Glass fiber: fine filaments for insulation and reinforcement** (`mt2_glass_fibre_insulation`) | 294.0 | 220 | 600h glassblower | 1.5 | cap_heat_1300, cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 133 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 167.6 | 110 | 300h labourer | 0.8 | cap_tol_1mm | GENERIC MISSING GATE | Adequate/good |
| 134 | **Silica brick: high-silica refractory for blast furnaces** (`mt2_silica_brick_refractory`) | 204.8 | 110 | 300h mason | 0.8 | cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 135 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 3,119.1 | 100 | 250h smith | 0.5 | cap_heat_0700, mat_lead, mat_tin | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 136 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 198.0 | 80 | 300h carpenter | 0.8 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 137 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 913.9 | 110 | 300h furnaceman | 0.8 | mat_lead, mat_tin | GENERIC MISSING GATE | Adequate/good |
| 138 | **White cast iron: hard but brittle, iron carbide dominant** (`mt2_white_cast_iron`) | 392.5 | 110 | 320h furnaceman | 0.8 | blast_furnace, cap_heat_1300 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 139 | **Anemometer (wind speed)** (`opt_anemometer`) | 254.0 | 60 | 100h artisan, 40h carpenter, 60h smith | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 140 | **Manometer (pressure measurement)** (`opt_manometer`) | 236.9 | 60 | 60h artisan, 80h glassblower | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 141 | **Mandrel and self-centering chuck** (`prc_mandrel_chuck`) | 119.6 | 60 | 80h artisan, 120h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 142 | **Pantograph and copying mechanism for die sinking** (`prc_pantograph_copying`) | 315.6 | 80 | 180h artisan, 100h smith | 0.5 | cap_tol_1mm, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 143 | **Straightedge and reference straightness** (`prc_straightedge`) | 62.2 | 30 | 80h artisan, 60h smith | 0.2 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 144 | **Tailstock and dead centre** (`prc_tailstock_deadcentre`) | 124.9 | 50 | 100h artisan, 60h smith | 0.2 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 145 | **Treadle lathe with flywheel** (`prc_treadle_lathe_flywheel`) | 181.3 | 80 | 200h carpenter, 100h smith | 0.5 | cap_power_muscle, cap_tol_1mm, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 146 | **Hand papermaking** (`prn_hand_papermaking`) | 47.6 | 80 | 300h artisan | 1 | rag_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 147 | **Surface sizing** (`prn_sizing_surface`) | 20.7 | 50 | 100h artisan | 0.3 | mat_alum, rag_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 148 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 82.2 | 150 | 200h artisan, 250h smith | 1 | cap_tol_1mm, mat_brass | GENERIC MISSING GATE | Adequate/good |
| 149 | **Coal seam and mining** (`pwr_coal_seam`) | 240.8 | 150 | 300h labourer, 400h miner | 1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 150 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 35.6 | 80 | 100h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 151 | **Peat extraction and burning** (`pwr_peat`) | 50.6 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 152 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 90.0 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 153 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 104.4 | 80 | 160h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 154 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 90.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 155 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 90.0 | 150 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 156 | **Examination and credentialing** (`sc2_institution_examination`) | 144.0 | 80 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 157 | **Funded research programme** (`sc2_institution_funded_programme`) | 90.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 158 | **Referee and peer review** (`sc2_institution_referee`) | 90.0 | 100 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 159 | **Research group and principal investigator** (`sc2_institution_research_group`) | 90.0 | 100 | — | 5 | — | GENERIC MISSING GATE | Adequate/good |
| 160 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 450.0 | 200 | 400h scholar, 200h scribe | 8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 161 | **Hypothesis and prediction** (`sc2_method_hypothesis`) | 90.0 | 90 | — | 8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 162 | **Negative result and null finding** (`sc2_method_negative_result`) | 90.0 | 90 | — | 20 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 163 | **Replication and repeatability** (`sc2_method_replication`) | 90.0 | 80 | — | 10 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 164 | **The decimal point convention** (`sc2_notation_decimal_point`) | 93.6 | 20 | 40h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 165 | **Exponent notation** (`sc2_notation_exponents`) | 98.1 | 45 | 90h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 166 | **Positional notation and place value** (`sc2_notation_positional`) | 90.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 167 | **Root symbols and radical notation** (`sc2_notation_roots`) | 97.2 | 40 | 80h scribe | 3 | — | GENERIC MISSING GATE | Adequate/good |
| 168 | **Newton's law of universal gravitation** (`sc2_physics_gravitation`) | 106.2 | 100 | 180h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 169 | **Kinematics: position, velocity, acceleration** (`sc2_physics_kinematics`) | 105.3 | 90 | 170h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 170 | **Momentum and impulse** (`sc2_physics_momentum`) | 103.5 | 80 | 150h scribe | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 171 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 177.0 | 100 | 180h scribe | 4 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 172 | **Probability axioms and conditional probability** (`sc2_probability_axioms`) | 90.0 | 100 | — | 4 | — | GENERIC MISSING GATE | Adequate/good |
| 173 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 157.5 | 350 | 500h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 174 | **Navigation charts** (`sea_charts_navigation`) | 724.5 | 200 | 400h scholar, 300h scribe | 0.5 | sea_magnetic_compass | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 175 | **Cross-staff for latitude** (`sea_cross_staff`) | 315.2 | 80 | 150h artisan, 100h scholar | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 176 | **Diving bell** (`sea_diving_bell`) | 736.1 | 120 | 300h carpenter, 100h smith | 0.4 | sea_anchor | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 177 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | 1,276.5 | 100 | 3000h carpenter | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 178 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,466.2 | 0 | — | 0 | mat_lead | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 179 | **Lodestone knowledge** (`sea_lodestone`) | 113.8 | 20 | 80h scholar | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 180 | **Log line for speed** (`sea_log_line`) | 50.4 | 30 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 181 | **Pharos lighthouse** (`sea_pharos_lighthouse`) | 0.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 182 | **Skeleton-first hull construction** (`sea_skeleton_first`) | 982.0 | 250 | 200h artisan, 600h carpenter | 1 | cap_tol_1mm, sea_mortise_tenon | BASELINE CONTAMINATED | Adequate/good |
| 183 | **Traverse board** (`sea_traverse_board`) | 107.8 | 40 | 60h artisan, 40h scholar | 0.15 | sea_magnetic_compass | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 184 | **Hand ginning cotton** (`tex_hand_ginning`) | 61.7 | 30 | 200h labourer | 0.2 | tex_cotton_trade | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 185 | **Horizontal loom** (`tex_horizontal_loom`) | 201.4 | 80 | 100h artisan, 200h carpenter | 0.5 | cap_tol_1mm, tex_two_beam_loom | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 186 | **Indigo dyeing** (`tex_indigo`) | 165.7 | 60 | 140h artisan | 0.4 | mat_natron, tex_dye_woad | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 187 | **Mordanting dyes with alum** (`tex_mordanting`) | 114.1 | 40 | 100h artisan | 0.3 | mat_alum, tex_dye_madder | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 188 | **Stirrup with foot loop** (`tl_stirrup`) | 231.7 | 60 | 50h artisan, 150h smith | 0.2 | mat_leather, lnd_horse_saddle_basic, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 189 | **Bilge pump** (`tr_bilge_pump`) | 283.4 | 50 | 150h carpenter, 100h smith | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 190 | **Block and tackle pulley** (`tr_block_tackle`) | 198.6 | 40 | 150h carpenter, 50h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 191 | **Hopper wagon for bulk minerals** (`tr_hopper_wagon`) | 229.8 | 50 | 250h carpenter, 100h smith | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 192 | **Lateen sail** (`tr_lateen_sail`) | 555.0 | 80 | — | 0.5 | sea_square_sail | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 193 | **Reefing sails** (`tr_reefing`) | 172.5 | 50 | 300h sailor | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 194 | **Block rigging and rope lashing** (`tr_rigging_block_lashing`) | 157.5 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 195 | **Semaphore signal** (`tr_semaphore_signal`) | 115.0 | 40 | 100h carpenter, 100h smith | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 196 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 192.3 | 30 | 150h carpenter, 400h labourer | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 197 | **Square rig sails** (`tr_square_rig`) | 825.0 | 40 | — | 0.6 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 198 | **Wooden waggonway** (`tr_wooden_waggonway`) | 176.4 | 40 | 200h carpenter | 2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 199 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 570.0 | 60 | 80h artisan | 0.4 | mat_alum | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 200 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 1,061.2 | 80 | 100h artisan | 1 | mat_asbestos | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 201 | **Beam: warp holder and tension** (`tx2_beam`) | 7.4 | 40 | 60h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 202 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 4.5 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 203 | **Bottle: glass container** (`tx2_bottle`) | 849.0 | 60 | 100h glassblower | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 204 | **Button: bone material** (`tx2_button_bone`) | 7.6 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 205 | **Button: horn material** (`tx2_button_horn`) | 7.5 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 206 | **Button: shell material** (`tx2_button_shell`) | 8.6 | 50 | 70h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 207 | **Cardboard box: folded laminate container** (`tx2_cardboard_box`) | 149.3 | 70 | 120h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 208 | **Carding: opening and aligning fibres** (`tx2_carding`) | 102.7 | 60 | 150h artisan | 0.2 | cap_tol_1mm, tex_wool | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 209 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 7.9 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 210 | **Comb: hair grooming tool** (`tx2_comb`) | 9.8 | 50 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 211 | **Corset: rigid body support garment** (`tx2_corset`) | 22.5 | 100 | 200h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 212 | **Cotton gin: separation of seed from fibre** (`tx2_cotton_ginning`) | 25.1 | 120 | 80h carpenter, 60h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 213 | **Yarn count standardisation** (`tx2_count_standard`) | 4.5 | 40 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 214 | **Currying: leather finish dressing** (`tx2_currying`) | 11.2 | 60 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 215 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 10.5 | 60 | 80h carpenter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 216 | **Doll: articulated child plaything** (`tx2_doll`) | 62.7 | 80 | 150h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 217 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 21.5 | 50 | 70h smith | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 218 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 536.2 | 60 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 219 | **Dyeing in garment: finished good colouration** (`tx2_dyeing_garment`) | 570.1 | 90 | 160h artisan | 1 | tex_dye_madder | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 220 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 540.8 | 80 | 140h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 221 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 538.5 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 222 | **Envelope: paper folded container** (`tx2_envelope_gummed`) | 56.3 | 60 | 100h artisan | 0.3 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 223 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 86.5 | 50 | 60h smith | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 224 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 6.8 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 225 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 21.0 | 70 | 40h carpenter, 80h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 226 | **Fulling: cloth densification** (`tx2_fulling`) | 560.8 | 60 | 80h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 227 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 7.2 | 40 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 228 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 6.8 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 229 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 15.1 | 50 | 60h smith | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 230 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 7.9 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 231 | **Mirror: reflective glass surface** (`tx2_mirror`) | 237.0 | 70 | 100h artisan | 0.3 | mat_glass_soda | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 232 | **Mohair: angora goat fibre** (`tx2_mohair`) | 7.9 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 233 | **Needle: sewing implement** (`tx2_needle`) | 85.0 | 40 | 60h smith | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 234 | **Paper bag: folded container** (`tx2_paper_bag`) | 83.3 | 60 | 100h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 235 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 12.6 | 50 | 70h smith | 0.5 | — | GENERIC MISSING GATE | Adequate/good |
| 236 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 41.3 | 80 | 120h artisan | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 237 | **Pin: sewing fastener** (`tx2_pin`) | 9.0 | 40 | 60h smith | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 238 | **Postcard: prepaid correspondence** (`tx2_postcard`) | 35.3 | 70 | 100h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 239 | **Block printing: carved design application** (`tx2_printing_block`) | 41.3 | 100 | 200h artisan, 80h engraver | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 240 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 7.9 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 241 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 549.8 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 242 | **Retting of flax and hemp fibres** (`tx2_retting`) | 4.5 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Assumes term |
| 243 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 6.8 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 244 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 532.9 | 40 | 60h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 245 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 5.6 | 40 | 50h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Assumes term |
| 246 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 4.5 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 247 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 231.8 | 40 | 60h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 248 | **Singeing: flame removal of nap** (`tx2_singeing`) | 875.8 | 60 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 249 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 13.5 | 100 | 120h artisan | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 250 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 23.2 | 60 | 100h artisan | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 251 | **Splitting: leather layering** (`tx2_splitting`) | 12.0 | 70 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 252 | **Twist insertion control** (`tx2_twist_insertion`) | 6.8 | 50 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 253 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 6.8 | 50 | 60h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 254 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 15.8 | 60 | 80h carpenter | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 255 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 13,060.9 | 80 | 60h engraver, 120h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 256 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 7.1 | 40 | 50h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 257 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 402.1 | 300 | 200h carpenter, 400h smith | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |

### Opening-project triage counts

- **PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK: 222**
- **GENERIC MISSING GATE: 34**
- **BASELINE CONTAMINATED: 1**

### Highest-confidence fixes

- Remove the navigational magnetic compass from inherited knowledge; keep lodestone/directional knowledge and let the player develop a practical compass.
- Split `crank_conrod`; do not grant flywheel/cam/trip-hammer as a single Han package.
- Replace Roman/Mediterranean ambient institutions, medicine, writing media and ship forms with Chinese equivalents where appropriate rather than deleting the underlying capability.
- Localize descriptions: a Chinese plough, rudder, bureaucracy or medical capability should not be explained through Roman/European hardware.

# Scandinavia in the Viking age (900)

## Explicit civilization seeds

| Seed | Verdict | Note |
|---|---|---|
| **Clinker-built hull** (`sea_clinker_hull`) | GOOD | Core Viking-age shipbuilding capability. |
| **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | GOOD | Deep keel and effective windward sailing fit Viking-age Scandinavian seafaring. |
| **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | GOOD | Bog-iron bloomery production is appropriate. |
| **Open ocean navigation out of sight of land** (`exp_openocean_navigation`) | GOOD | By 900 Scandinavians were making open-ocean voyages to Iceland and across the North Atlantic. |

## Inherited/granted opening state — all nodes

| # | Granted node | Realism flag | Description |
|---:|---|---|---|
| 1 | **Sustained 700 C (pottery kiln)** (`cap_heat_0700`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 2 | **Muscle and animal power** (`cap_power_muscle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 3 | **Tolerance 1 mm (skilled hand craft)** (`cap_tol_1mm`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 4 | **Glass panes for windows** (`civ_glass_windows`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 5 | **Wrought iron working and riveting** (`civ_iron_wrought`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 6 | **Marble veneer and ashlar facing** (`civ_marble_facing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 7 | **Open ocean navigation out of sight of land** (`exp_openocean_navigation`) | GOOD | Adequate/good |
| 8 | **Auction and competitive bidding** (`fin_auction`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 9 | **Coined money** (`fin_coined_money`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 10 | **Contract law and enforcement** (`fin_contract_law`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 11 | **Standing bureaucracy** (`fin_government`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 12 | **Maritime loan at high interest** (`fin_maritime_loan`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 13 | **Permanent market and market law** (`fin_market`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 14 | **Tax farming and revenue contracts** (`fin_tax_farming`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 15 | **Testament and inheritance law** (`fin_testament`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 16 | **Wage and labour payment** (`fin_wage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 17 | **Board games, dice games, and pieces** (`hom_board_games`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 18 | **Beeswax candle** (`hom_candle_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 19 | **Tallow candle** (`hom_candle_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 20 | **Flush latrine with running water** (`hom_flush_latrine_simple`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 21 | **Wooden furniture** (`hom_furniture_wooden`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 22 | **Hypocaust underfloor heating** (`hom_hypocaust`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 23 | **Lead and ceramic plumbing** (`hom_lead_plumbing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 24 | **Locks and keys** (`hom_locks_keys`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 25 | **Mirror, polished bronze** (`hom_mirror_bronze_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 26 | **Musical instruments** (`hom_musical_instruments`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 27 | **Oil lamp, simple** (`hom_oil_lamp_simple`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 28 | **Perfume by enfleurage** (`hom_perfume_enfleurage`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 29 | **Public bath (thermae)** (`hom_public_bath`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 30 | **Pivoting front axle** (`lnd_axle_pivot_front`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 31 | **Bridge** (`lnd_bridge`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 32 | **Four-wheeled cart** (`lnd_four_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 33 | **Harness of throat and girth type** (`lnd_harness_throat_girth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 34 | **Horse saddle (basic)** (`lnd_horse_saddle_basic`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 35 | **Litter** (`lnd_litter`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 36 | **Milestone** (`lnd_milestone`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 37 | **Mule transport** (`lnd_mule_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 38 | **Ox transport** (`lnd_ox_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 39 | **Paved trunk road network** (`lnd_paved_road_network`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 40 | **Two-wheeled cart** (`lnd_two_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 41 | **Iron tyre (tire)** (`lnd_tyre_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 42 | **Spoked wheel** (`lnd_wheel_spoked`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 43 | **Alum** (`mat_alum`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 44 | **Asbestos** (`mat_asbestos`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 45 | **Beeswax** (`mat_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 46 | **Bitumen and naphtha seeps** (`mat_bitumen`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 47 | **Brass (by cementation)** (`mat_brass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 48 | **Bronze** (`mat_bronze`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 49 | **Calamine (zinc carbonate/silicate ore)** (`mat_calamine`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 50 | **Carbon black and lampblack** (`mat_carbon_black`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 51 | **Charcoal** (`mat_charcoal`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 52 | **Emery (Naxos)** (`mat_emery`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 53 | **Galena (lead sulfide)** (`mat_galena`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 54 | **Soda-lime glass** (`mat_glass_soda`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 55 | **Gold** (`mat_gold`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 56 | **Gypsum plaster** (`mat_gypsum`) | NO OBVIOUS HARD CONFLICT | Thin |
| 57 | **Lead** (`mat_lead`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 58 | **Leather** (`mat_leather`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 59 | **Quicklime and slaked lime** (`mat_lime`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 60 | **Linen** (`mat_linen`) | NO OBVIOUS HARD CONFLICT | Assumes term |
| 61 | **Mercury** (`mat_mercury`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 62 | **Natron (sodium carbonate)** (`mat_natron`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 63 | **Olive oil** (`mat_olive_oil`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 64 | **Pyrolusite (manganese dioxide)** (`mat_pyrolusite`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 65 | **Salt** (`mat_salt`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 66 | **Shellac (traded)** (`mat_shellac`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 67 | **Silk (traded)** (`mat_silk`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 68 | **Silver** (`mat_silver`) | NO OBVIOUS HARD CONFLICT | Thin |
| 69 | **Sulfur** (`mat_sulfur`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 70 | **Tallow** (`mat_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 71 | **Tin** (`mat_tin`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 72 | **Vitriols (iron and copper sulfates)** (`mat_vitriols`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 73 | **Wrought iron (bloomery)** (`mat_wrought_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 74 | **Cataract couching** (`med_cataract_couching`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 75 | **Legal protection for physicians** (`med_legal_physician`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 76 | **Opium and mandrake tinctures** (`med_opium_mandrake`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 77 | **Good surgical instrument kit** (`med_surgical_kit_good`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 78 | **Trepanation** (`med_trepanation`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 79 | **Wound suturing** (`med_wound_suturing`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 80 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | GOOD | Adequate/good |
| 81 | **Burning glass** (`opt_burning_glass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 82 | **Dioptra (sighting tube)** (`opt_dioptra`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 83 | **Geared mechanical transmission** (`opt_geared_mechanisms`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 84 | **Groma (surveying cross)** (`opt_groma`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 85 | **Polished metal mirror** (`opt_metal_mirror_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 86 | **Steelyard balance** (`opt_steelyards`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 87 | **Sundial** (`opt_sundial`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 88 | **Water clock (clepsydra)** (`opt_water_clock`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 89 | **Water-filled globe as magnifier** (`opt_water_globe_magnifier`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 90 | **Carbon ink** (`prn_carbon_ink`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 91 | **Codex binding** (`prn_codex_bound`) | MIS-SCOPED / VERIFY LOCAL FORM | Thin |
| 92 | **Library and archive** (`prn_library_archive`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 93 | **Mosaic and fresco** (`prn_mosaic_fresco`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 94 | **Papyrus sheets** (`prn_papyrus_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 95 | **Parchment sheets** (`prn_parchment_sheets`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 96 | **Scribal copying** (`prn_scribal_copying`) | NO OBVIOUS HARD CONFLICT | Thin |
| 97 | **Sculpture** (`prn_sculpture`) | NO OBVIOUS HARD CONFLICT | Thin |
| 98 | **Seals and stamps** (`prn_seals_stamps`) | NO OBVIOUS HARD CONFLICT | Thin |
| 99 | **Theatre and pantomime** (`prn_theatre_pantomime`) | WRONG / FOREIGN / ANACHRONISTIC | Thin |
| 100 | **Wax tablets** (`prn_wax_tablets`) | NO OBVIOUS HARD CONFLICT | Thin |
| 101 | **Animal-driven treadmill** (`pwr_animal_treadmill`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 102 | **Force pump** (`pwr_force_pump`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 103 | **Screw press** (`pwr_screw_press_power`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 104 | **Anchor** (`sea_anchor`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 105 | **Clinker-built hull** (`sea_clinker_hull`) | GOOD | Adequate/good |
| 106 | **Coastal pilotage** (`sea_coastal_pilotage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 107 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | GOOD | Adequate/good |
| 108 | **Large merchant sailing ships** (`sea_merchant_ships_large`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 109 | **Monsoon route to India** (`sea_monsoon_route`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 110 | **Mortise-and-tenon hull construction** (`sea_mortise_tenon`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 111 | **Sounding lines** (`sea_sounding_lines`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 112 | **Spritsail** (`sea_spritsail`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 113 | **Square sail with brails** (`sea_square_sail`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 114 | **Steering oars** (`sea_steering_oars`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 115 | **Cotton by trade** (`tex_cotton_trade`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 116 | **Drop spindle** (`tex_drop_spindle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 117 | **Dyeing with madder root** (`tex_dye_madder`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 118 | **Murex purple dyeing** (`tex_dye_murex`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 119 | **Dyeing with woad** (`tex_dye_woad`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 120 | **Felting** (`tex_felting`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 121 | **Sailcloth** (`tex_sailcloth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 122 | **Silk by trade** (`tex_silk_trade`) | NO OBVIOUS HARD CONFLICT | Thin |
| 123 | **Two-beam loom** (`tex_two_beam_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 124 | **Warp-weighted loom** (`tex_warp_weighted_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 125 | **Wool fiber** (`tex_wool`) | NO OBVIOUS HARD CONFLICT | Adequate/good |

## Immediately startable opening projects — all nodes

`BASELINE CONTAMINATED` means the project is startable because at least one of its direct prerequisites is an inherited node flagged above as wrong/foreign/anachronistic. `GENERIC MISSING GATE` carries over a dependency defect already identified in the Rome audit and is not a judgment that the civilization is “too advanced.”

| # | Project | Cost | Founder h | Hired labour | Floor y | Prereqs | Realism flag | Description |
|---:|---|---:|---:|---|---:|---|---|---|
| 1 | **Chaff cutter** (`ag2_chaff_cutter`) | 364.3 | 50 | 140h smith | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 2 | **Composting** (`ag2_composting`) | 472.5 | 40 | 100h labourer | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 3 | **Grafting** (`ag2_grafting`) | 280.0 | 50 | — | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 4 | **Guano** (`ag2_guano`) | 388.1 | 30 | 80h merchant | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 5 | **Hopping** (`ag2_hopping`) | 210.0 | 40 | — | 0.15 | — | GENERIC MISSING GATE | Adequate/good |
| 6 | **Layering** (`ag2_layering`) | 210.0 | 40 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 7 | **Liming** (`ag2_liming`) | 443.5 | 30 | 80h labourer | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 8 | **Malting** (`ag2_malting`) | 336.0 | 60 | — | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 9 | **Marling** (`ag2_marling`) | 354.1 | 25 | 60h labourer | 0.15 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 10 | **Oil pressing** (`ag2_oil_pressing`) | 338.2 | 60 | — | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 11 | **Potash** (`ag2_potash`) | 472.5 | 40 | 100h labourer | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 12 | **Pyrethrum** (`ag2_pyrethrum`) | 392.0 | 70 | — | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 13 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 431.2 | 70 | — | 0.5 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 14 | **Compass for navigation** (`air_compass_magnetic`) | 122.8 | 30 | 50h artisan | 0.1 | mat_silk, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 15 | **Kite** (`air_kite_basic`) | 220.9 | 20 | 40h artisan | 0.1 | mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 16 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 3,372.8 | 120 | 200h artisan | 0.5 | mat_beeswax, mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 17 | **Decimal positional notation, zero, negative numbers, decimal fractions** (`arithmetic_positional`) | 1,120.0 | 450 | 2500h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 18 | **Six months of listening before you act** (`arrival_orientation`) | 924.0 | 900 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 19 | **Roman masonry arch** (`civ_arch_roman`) | 1,017.8 | 60 | 120h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 20 | **Roman fired brick and tile** (`civ_brick_tile`) | 295.7 | 40 | 80h potter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 21 | **Chorobates: Roman water levelling rod** (`civ_chorobates`) | 174.7 | 25 | 30h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 22 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 198.8 | 80 | 150h smith | 0.4 | mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 23 | **Groma: Roman X-staff surveying tool** (`civ_surveying_groma`) | 144.5 | 20 | 20h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 24 | **Block and tackle with rope** (`cn_block_tackle_hoist`) | 364.3 | 30 | 60h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 25 | **Treadwheel crane** (`cn_crane_treadwheel`) | 733.0 | 55 | 100h carpenter, 80h labourer | 0.7 | cap_power_muscle, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 26 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 743.4 | 50 | 100h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 27 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 501.4 | 35 | 80h mason | 0.15 | mat_gypsum | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 28 | **Pile driving by drop hammer** (`cn_pile_driving`) | 1,395.3 | 40 | 150h labourer | 0.8 | cap_power_muscle | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 29 | **Post and lintel structure** (`cn_post_lintel`) | 329.8 | 25 | 50h carpenter, 100h mason | 0.4 | cap_tol_1mm | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 30 | **Stone quarrying with wedge** (`cn_quarrying_wedge`) | 157.5 | 20 | 100h labourer | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 31 | **Timber scaffolding system** (`cn_scaffolding`) | 868.6 | 50 | 120h carpenter | 0.6 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 32 | **Soil compaction by roller** (`cn_soil_compaction`) | 2,391.3 | 70 | 120h labourer | 1 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 33 | **Stone polishing and smoothing** (`cn_stone_polish`) | 192.9 | 30 | 80h mason | 0.15 | cap_tol_1mm | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 34 | **Codebook for optical signal tower** (`com_optical_codebook`) | 176.4 | 100 | 200h scribe | 0.25 | — | GENERIC MISSING GATE | Adequate/good |
| 35 | **Signal flags for maritime communication** (`com_signal_flags`) | 314.5 | 40 | 60h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 36 | **Horse gin** (`en_horse_gin`) | 110.6 | 30 | 150h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 37 | **Spring motor (large clockwork)** (`en_spring_motor`) | 14.0 | 80 | — | 0.8 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 38 | **Treadwheel** (`en_treadwheel`) | 53.2 | 20 | 100h carpenter | 0.2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 39 | **Annona grain dole and administration** (`fin_annona`) | 6,371.6 | 600 | 200h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 40 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 24.6 | 80 | 80h scribe | 1 | fin_contract_law | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 41 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 59.1 | 80 | 150h merchant | 1 | fin_market | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 42 | **Deposit bankers (argentarii)** (`fin_argentarii`) | 2,328.5 | 150 | 60h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 43 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 61.6 | 120 | 200h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 44 | **Bill of exchange** (`fin_bill_exchange`) | 107.8 | 150 | 200h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 45 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 82.4 | 100 | 50h master, 150h merchant | 2 | fin_coined_money | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 46 | **Cartel and market sharing agreement** (`fin_cartel`) | 78.9 | 100 | 200h merchant | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 47 | **Census and population enumeration** (`fin_census`) | 3,249.4 | 200 | 200h merchant, 300h scribe | 2 | fin_government | BASELINE CONTAMINATED | Adequate/good |
| 48 | **Professional associations (collegia)** (`fin_collegium`) | 1,398.3 | 120 | 40h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 49 | **Contract of employment** (`fin_employment_contract`) | 15.4 | 60 | 50h scribe | 1 | fin_contract_law | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 50 | **Ferry and toll crossing** (`fin_ferry`) | 6,246.7 | 100 | 100h carpenter, 150h merchant | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 51 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 3,253.3 | 100 | 150h merchant | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 52 | **Hotel and commercial lodging** (`fin_hotel`) | 9,185.2 | 120 | 150h carpenter, 200h merchant | 2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 53 | **Inn and coaching house** (`fin_inn`) | 5,579.1 | 100 | 150h merchant | 1.5 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 54 | **Lottery and state gambling** (`fin_lottery`) | 3,203.2 | 150 | 200h merchant, 150h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 55 | **Marine insurance** (`fin_marine_insurance`) | 6,321.7 | 200 | 300h merchant, 150h scribe | 2 | fin_maritime_loan | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 56 | **Monopoly and exclusive grant** (`fin_monopoly`) | 73.2 | 80 | 150h merchant, 50h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 57 | **Mortgage and real estate credit** (`fin_mortgage`) | 88.6 | 120 | 150h merchant, 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 58 | **Patent and exclusive right** (`fin_patent`) | 88.6 | 140 | 150h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 59 | **Pawnshop and secured loan** (`fin_pawnshop`) | 1,578.5 | 60 | 100h merchant | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 60 | **Plantation and large estate agriculture** (`fin_plantation`) | 15,889.6 | 200 | 300h merchant | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 61 | **Postal service as paid business** (`fin_postal_service`) | 15,976.2 | 180 | 200h carpenter, 250h merchant | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 62 | **Seigniorage and debasement** (`fin_seigniorage`) | 38.5 | 80 | 100h merchant | 0.2 | fin_coined_money | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 63 | **Partnership (societas)** (`fin_societas`) | 468.2 | 40 | 20h scribe | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 64 | **Tariff and import duty** (`fin_tariff`) | 73.2 | 100 | 150h merchant, 50h scribe | 2 | fin_tax_farming | BASELINE CONTAMINATED | Adequate/good |
| 65 | **Trademark and mark of quality** (`fin_trademark`) | 30.8 | 80 | 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 66 | **Trading post and remote store** (`fin_trading_post`) | 2,622.0 | 100 | 150h merchant | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 67 | **Usury law and interest regulation** (`fin_usury_law`) | 46.2 | 100 | 150h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 68 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 510.7 | 120 | 200h artisan | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 69 | **Hay making and dry storage** (`fud_hay_making_storage`) | 329.0 | 100 | 300h labourer | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 70 | **Organized whaling industry for oil and meat** (`fud_whaling_industry`) | 2,898.0 | 300 | 200h artisan, 400h sailor | 1 | sea_merchant_ships_large | GENERIC MISSING GATE | Adequate/good |
| 71 | **Button with eyelet** (`hom_button`) | 44.2 | 40 | 60h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 72 | **Carpet sweeper** (`hom_carpet_sweeper`) | 215.7 | 100 | 120h artisan, 80h carpenter | 0.75 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 73 | **Roman cosmetics** (`hom_cosmetics_roman`) | 112.0 | 20 | — | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 74 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 7.0 | 30 | — | 0.1 | — | GENERIC MISSING GATE | Adequate/good |
| 75 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 380.0 | 120 | 80h carpenter, 200h mason | 1 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 76 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 501.5 | 80 | 80h artisan, 100h plumber | 0.5 | hom_flush_latrine_simple | BASELINE CONTAMINATED | Adequate/good |
| 77 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 370.2 | 60 | 100h artisan, 80h plumber | 0.5 | hom_flush_latrine_simple | BASELINE CONTAMINATED | Adequate/good |
| 78 | **Mangle and wringer** (`hom_mangle_wringer`) | 285.4 | 100 | 120h artisan, 80h carpenter | 0.75 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 79 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 116.3 | 50 | 80h carpenter | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 80 | **Safety pin** (`hom_safety_pin`) | 33.7 | 40 | 50h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 81 | **Sprung mattress** (`hom_sprung_mattress`) | 399.7 | 120 | 150h artisan, 100h carpenter | 1 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 82 | **Toothbrush** (`hom_toothbrush`) | 42.4 | 60 | 100h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 83 | **Toys and dolls** (`hom_toys_dolls`) | 105.6 | 60 | 60h artisan, 80h carpenter | 0.5 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 84 | **Umbrella** (`hom_umbrella`) | 125.6 | 80 | 60h artisan, 100h carpenter | 0.5 | cap_tol_1mm | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 85 | **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | 2,103.2 | 200 | 900h artisan, 700h smith | 1 | tex_wool | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 86 | **Establish a respectable cover identity** (`identity_cover`) | 2,433.2 | 500 | 400h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 87 | **Quill pen** (`if_quill`) | 294.3 | 15 | 40h scribe | 0.05 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Thin |
| 88 | **Coach** (`lnd_coach`) | 2,731.8 | 200 | 150h artisan, 400h carpenter, 200h smith | 2 | lnd_four_wheel_cart, lnd_harness_throat_girth, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 89 | **Cursus publicus courier service** (`lnd_cursus_publicus`) | 0.0 | 0 | — | 0 | lnd_horse_saddle_basic, lnd_paved_road_network | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 90 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 661.3 | 40 | 100h carpenter, 60h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 91 | **Wheelbarrow** (`lnd_wheelbarrow`) | 290.2 | 30 | 80h carpenter, 30h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 92 | **Obsidian blade knapping** (`mat_obsidian_blade`) | 323.4 | 40 | 600h artisan | 0.5 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 93 | **Papyrus** (`mat_papyrus`) | 436.8 | 20 | 60h scribe | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 94 | **Parchment** (`mat_parchment`) | 582.4 | 30 | 80h scribe | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 95 | **Plaster cast immobilization** (`md2_plaster_cast`) | 305.2 | 100 | 120h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 96 | **Vector control** (`md2_vector_control`) | 625.0 | 100 | 120h scholar | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 97 | **Amputation and prosthetics** (`med_amputation`) | 17.3 | 0 | 50h artisan | 0 | med_surgical_kit_good | BASELINE CONTAMINATED | Adequate/good |
| 98 | **Bone setting** (`med_bone_setting`) | 13.0 | 0 | 50h artisan | 0.5 | med_surgical_kit_good | BASELINE CONTAMINATED | Adequate/good |
| 99 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 812.0 | 100 | 200h scholar | 0.5 | mat_olive_oil | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 100 | **Obstetric practice** (`med_obstetric_practice`) | 26.2 | 0 | 100h artisan | 0 | mat_linen | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 101 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 303.5 | 40 | 100h artisan | 0 | mat_linen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 102 | **Investment casting and lost wax** (`met_investment_casting`) | 461.7 | 100 | 140h artisan | 0.8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 103 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 220.5 | 20 | 400h labourer | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 104 | **Adhesive bonding** (`mfg_adhesive_bond`) | 307.3 | 140 | 120h artisan | 0.3 | mat_bitumen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 105 | **Cold riveting** (`mfg_cold_riveting`) | 312.2 | 100 | 120h artisan | 0.2 | mat_wrought_iron | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 106 | **Drawing office** (`mfg_drawing_office`) | 588.0 | 150 | 200h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 107 | **Enamelling** (`mfg_enamelling`) | 303.5 | 120 | 140h furnaceman | 0.3 | cap_heat_0700, mat_glass_soda | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 108 | **Flux** (`mfg_flux`) | 292.6 | 60 | 60h artisan | 0.15 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 109 | **Hot riveting** (`mfg_hot_riveting`) | 308.0 | 80 | 100h artisan | 0.2 | mat_wrought_iron | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 110 | **Japanning** (`mfg_japanning`) | 307.3 | 110 | 130h artisan | 0.25 | mat_shellac | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 111 | **Casting mould** (`mfg_mould`) | 311.5 | 120 | 150h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 112 | **Painting** (`mfg_painting`) | 315.0 | 80 | 100h artisan | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 113 | **Production schedule** (`mfg_production_schedule`) | 504.0 | 130 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 114 | **Silver soldering** (`mfg_silver_solder`) | 1,198.5 | 100 | 120h smith | 0.25 | cap_heat_0700, mat_silver | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 115 | **Soft soldering** (`mfg_soft_solder`) | 331.0 | 80 | 100h artisan | 0.2 | mat_lead | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 116 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 8,814.4 | 80 | 300h master | 0.5 | mat_mercury | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 117 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 354.2 | 60 | 200h potter | 0.5 | cap_heat_0700 | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 118 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 312.9 | 110 | 300h labourer | 0.8 | cap_tol_1mm | GENERIC MISSING GATE | Adequate/good |
| 119 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 8,092.6 | 100 | 250h smith | 0.5 | cap_heat_0700, mat_lead, mat_tin | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 120 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 665.3 | 80 | 300h carpenter | 0.8 | cap_power_muscle | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 121 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 2,694.1 | 110 | 300h furnaceman | 0.8 | mat_lead, mat_tin | GENERIC MISSING GATE | Adequate/good |
| 122 | **Anemometer (wind speed)** (`opt_anemometer`) | 472.1 | 60 | 100h artisan, 40h carpenter, 60h smith | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 123 | **Manometer (pressure measurement)** (`opt_manometer`) | 442.2 | 60 | 60h artisan, 80h glassblower | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 124 | **Mandrel and self-centering chuck** (`prc_mandrel_chuck`) | 209.8 | 60 | 80h artisan, 120h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 125 | **Straightedge and reference straightness** (`prc_straightedge`) | 114.5 | 30 | 80h artisan, 60h smith | 0.2 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 126 | **Tailstock and dead centre** (`prc_tailstock_deadcentre`) | 219.2 | 50 | 100h artisan, 60h smith | 0.2 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 127 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 304.5 | 150 | 200h artisan, 250h smith | 1 | cap_tol_1mm, mat_brass | GENERIC MISSING GATE | Adequate/good |
| 128 | **Coal seam and mining** (`pwr_coal_seam`) | 808.9 | 150 | 300h labourer, 400h miner | 1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 129 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 119.7 | 80 | 100h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 130 | **Peat extraction and burning** (`pwr_peat`) | 170.1 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 131 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 302.4 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 132 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 324.8 | 80 | 160h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 133 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 280.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 134 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 280.0 | 150 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 135 | **Examination and credentialing** (`sc2_institution_examination`) | 448.0 | 80 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 136 | **Funded research programme** (`sc2_institution_funded_programme`) | 280.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 137 | **Referee and peer review** (`sc2_institution_referee`) | 280.0 | 100 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 138 | **Research group and principal investigator** (`sc2_institution_research_group`) | 280.0 | 100 | — | 5 | — | GENERIC MISSING GATE | Adequate/good |
| 139 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 1,400.0 | 200 | 400h scholar, 200h scribe | 8 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 140 | **Hypothesis and prediction** (`sc2_method_hypothesis`) | 280.0 | 90 | — | 8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 141 | **Negative result and null finding** (`sc2_method_negative_result`) | 280.0 | 90 | — | 20 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 142 | **Replication and repeatability** (`sc2_method_replication`) | 280.0 | 80 | — | 10 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 143 | **The decimal point convention** (`sc2_notation_decimal_point`) | 291.2 | 20 | 40h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 144 | **Exponent notation** (`sc2_notation_exponents`) | 305.2 | 45 | 90h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 145 | **Positional notation and place value** (`sc2_notation_positional`) | 280.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 146 | **Root symbols and radical notation** (`sc2_notation_roots`) | 302.4 | 40 | 80h scribe | 3 | — | GENERIC MISSING GATE | Adequate/good |
| 147 | **Newton's law of universal gravitation** (`sc2_physics_gravitation`) | 330.4 | 100 | 180h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 148 | **Kinematics: position, velocity, acceleration** (`sc2_physics_kinematics`) | 327.6 | 90 | 170h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 149 | **Momentum and impulse** (`sc2_physics_momentum`) | 322.0 | 80 | 150h scribe | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 150 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 330.4 | 100 | 180h scribe | 4 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 151 | **Probability axioms and conditional probability** (`sc2_probability_axioms`) | 280.0 | 100 | — | 4 | — | GENERIC MISSING GATE | Adequate/good |
| 152 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 280.0 | 350 | 500h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 153 | **Cross-staff for latitude** (`sea_cross_staff`) | 424.9 | 80 | 150h artisan, 100h scholar | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 154 | **Diving bell** (`sea_diving_bell`) | 1,355.9 | 120 | 300h carpenter, 100h smith | 0.4 | sea_anchor | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 155 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,693.9 | 0 | — | 0 | mat_lead | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 156 | **Lodestone knowledge** (`sea_lodestone`) | 153.4 | 20 | 80h scholar | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 157 | **Log line for speed** (`sea_log_line`) | 67.9 | 30 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 158 | **Pharos lighthouse** (`sea_pharos_lighthouse`) | 0.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 159 | **Skeleton-first hull construction** (`sea_skeleton_first`) | 1,134.4 | 250 | 200h artisan, 600h carpenter | 1 | cap_tol_1mm, sea_mortise_tenon | BASELINE CONTAMINATED | Adequate/good |
| 160 | **Sternpost rudder** (`sea_sternpost_rudder`) | 501.1 | 120 | 200h carpenter, 100h smith | 0.5 | cap_tol_1mm, sea_steering_oars | GENERIC MISSING GATE | Adequate/good |
| 161 | **Field bleaching with sun** (`tex_field_bleaching`) | 342.7 | 50 | 300h labourer | 2 | mat_linen, tex_sailcloth | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 162 | **Hand ginning cotton** (`tex_hand_ginning`) | 100.1 | 30 | 200h labourer | 0.2 | tex_cotton_trade | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 163 | **Horizontal loom** (`tex_horizontal_loom`) | 323.4 | 80 | 100h artisan, 200h carpenter | 0.5 | cap_tol_1mm, tex_two_beam_loom | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 164 | **Indigo dyeing** (`tex_indigo`) | 269.4 | 60 | 140h artisan | 0.4 | mat_natron, tex_dye_woad | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 165 | **Mordanting dyes with alum** (`tex_mordanting`) | 185.3 | 40 | 100h artisan | 0.3 | mat_alum, tex_dye_madder | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 166 | **Vegetable tanning of leather** (`tex_vegetable_tanning`) | 1,329.6 | 100 | 250h artisan, 200h labourer | 1.2 | mat_leather | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 167 | **Stirrup with foot loop** (`tl_stirrup`) | 408.7 | 60 | 50h artisan, 150h smith | 0.2 | mat_leather, lnd_horse_saddle_basic, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 168 | **Bilge pump** (`tr_bilge_pump`) | 398.2 | 50 | 150h carpenter, 100h smith | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 169 | **Block and tackle pulley** (`tr_block_tackle`) | 278.5 | 40 | 150h carpenter, 50h smith | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 170 | **Hopper wagon for bulk minerals** (`tr_hopper_wagon`) | 769.6 | 50 | 250h carpenter, 100h smith | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 171 | **Lateen sail** (`tr_lateen_sail`) | 780.0 | 80 | — | 0.5 | sea_square_sail | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 172 | **Reefing sails** (`tr_reefing`) | 242.4 | 50 | 300h sailor | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 173 | **Block rigging and rope lashing** (`tr_rigging_block_lashing`) | 182.0 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 174 | **Semaphore signal** (`tr_semaphore_signal`) | 640.7 | 40 | 100h carpenter, 100h smith | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 175 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 646.1 | 30 | 150h carpenter, 400h labourer | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 176 | **Square rig sails** (`tr_square_rig`) | 1,159.5 | 40 | — | 0.6 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 177 | **Wooden waggonway** (`tr_wooden_waggonway`) | 592.7 | 40 | 200h carpenter | 2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 178 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 1,064.0 | 60 | 80h artisan | 0.4 | mat_alum | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 179 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 3,565.8 | 80 | 100h artisan | 1 | mat_asbestos | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 180 | **Beam: warp holder and tension** (`tx2_beam`) | 13.9 | 40 | 60h carpenter | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 181 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 8.4 | 30 | 40h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 182 | **Bottle: glass container** (`tx2_bottle`) | 1,584.8 | 60 | 100h glassblower | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 183 | **Button: bone material** (`tx2_button_bone`) | 14.1 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 184 | **Button: horn material** (`tx2_button_horn`) | 14.0 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 185 | **Button: shell material** (`tx2_button_shell`) | 16.1 | 50 | 70h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 186 | **Carding: opening and aligning fibres** (`tx2_carding`) | 166.0 | 60 | 150h artisan | 0.2 | cap_tol_1mm, tex_wool | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 187 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 14.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 188 | **Comb: hair grooming tool** (`tx2_comb`) | 18.2 | 50 | 80h artisan | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 189 | **Corset: rigid body support garment** (`tx2_corset`) | 42.0 | 100 | 200h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 190 | **Cotton gin: separation of seed from fibre** (`tx2_cotton_ginning`) | 44.5 | 120 | 80h carpenter, 60h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 191 | **Yarn count standardisation** (`tx2_count_standard`) | 8.4 | 40 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 192 | **Currying: leather finish dressing** (`tx2_currying`) | 21.0 | 60 | 100h artisan | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 193 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 19.7 | 60 | 80h carpenter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 194 | **Doll: articulated child plaything** (`tx2_doll`) | 117.0 | 80 | 150h artisan | 1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 195 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 40.0 | 50 | 70h smith | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 196 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 1,001.0 | 60 | 100h artisan | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 197 | **Dyeing in garment: finished good colouration** (`tx2_dyeing_garment`) | 1,013.6 | 90 | 160h artisan | 1 | tex_dye_madder | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 198 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 1,009.4 | 80 | 140h artisan | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 199 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 1,005.2 | 70 | 120h artisan | 0.3 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 200 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 159.3 | 50 | 60h smith | 0.15 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 201 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 12.6 | 40 | 60h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 202 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 39.0 | 70 | 40h carpenter, 80h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 203 | **Fulling: cloth densification** (`tx2_fulling`) | 1,004.2 | 60 | 80h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 204 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 13.3 | 40 | 50h artisan | 0.1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 205 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 12.6 | 40 | 60h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 206 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 27.7 | 50 | 60h smith | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 207 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 14.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 208 | **Mirror: reflective glass surface** (`tx2_mirror`) | 442.4 | 70 | 100h artisan | 0.3 | mat_glass_soda | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 209 | **Mohair: angora goat fibre** (`tx2_mohair`) | 14.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 210 | **Needle: sewing implement** (`tx2_needle`) | 156.5 | 40 | 60h smith | 0.1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 211 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 23.2 | 50 | 70h smith | 0.5 | — | GENERIC MISSING GATE | Adequate/good |
| 212 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 77.0 | 80 | 120h artisan | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 213 | **Pin: sewing fastener** (`tx2_pin`) | 16.5 | 40 | 60h smith | 0.1 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 214 | **Press stud: snap fastener** (`tx2_press_stud`) | 144.8 | 80 | 100h smith | 1 | mat_brass | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 215 | **Block printing: carved design application** (`tx2_printing_block`) | 77.2 | 100 | 200h artisan, 80h engraver | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 216 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 14.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 217 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 1,026.2 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 218 | **Retting of flax and hemp fibres** (`tx2_retting`) | 8.4 | 30 | 40h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Assumes term |
| 219 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 12.6 | 40 | 60h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 220 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 994.7 | 40 | 60h artisan | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 221 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 10.5 | 40 | 50h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Assumes term |
| 222 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 8.4 | 30 | 40h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 223 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 432.6 | 40 | 60h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 224 | **Singeing: flame removal of nap** (`tx2_singeing`) | 1,556.9 | 60 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 225 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 25.2 | 100 | 120h artisan | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 226 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 43.4 | 60 | 100h artisan | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 227 | **Splitting: leather layering** (`tx2_splitting`) | 22.4 | 70 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 228 | **Twist insertion control** (`tx2_twist_insertion`) | 12.6 | 50 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 229 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 12.6 | 50 | 60h artisan | 0.2 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 230 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 29.3 | 60 | 80h carpenter | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 231 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 24,380.4 | 80 | 60h engraver, 120h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 232 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 13.3 | 40 | 50h artisan | 0 | — | CHECK: LIKELY ALREADY KNOWN/AVAILABLE | Adequate/good |
| 233 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 683.8 | 300 | 200h carpenter, 400h smith | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |

### Opening-project triage counts

- **PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK: 125**
- **CHECK: LIKELY ALREADY KNOWN/AVAILABLE: 67**
- **GENERIC MISSING GATE: 34**
- **BASELINE CONTAMINATED: 7**

### Highest-confidence fixes

- Keep the four explicit Norse seeds; they are the cleanest explicit package after the Mexica five.
- Remove Roman urban infrastructure/medicine as ambient inheritance: hypocaust, lead plumbing, public bath, groma/dioptra, papyrus, etc.
- Treat far-distance luxuries such as silk/shellac/natron as trade access only if the geography model can actually justify their route; do not grant them as generic local stock.
- A “standing bureaucracy” and Roman-style tax farming are especially poor fits for the start description “no state to speak of.”

# England under Edward I (1300)

## Explicit civilization seeds

| Seed | Verdict | Note |
|---|---|---|
| **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | GOOD | Appropriate medieval traction technology. |
| **Crank, connecting rod, flywheel, cam and trip hammer** (`crank_conrod`) | BUNDLED TOO FAR | Cranks are plausible; a complete crank + connecting rod + flywheel + cam + trip-hammer package is too broad for an inherited 1300 capability. |
| **Overshot wheels, millponds, leats, line shafting** (`water_power_scale`) | MOSTLY GOOD, SCOPE FIX | Large watermills, millponds and leats are appropriate; generalized line-shaft industrial power transmission is overstated. |
| **Water power, tens of kW on one shaft** (`cap_power_water`) | GOOD | Tens of kilowatts at substantial mills is defensible. |
| **Rag paper from linen** (`rag_paper`) | WRONG AS DOMESTIC PROCESS | Paper was available in England, but English papermaking production is later. Grant imported paper access, not this production recipe. |
| **Rag paper** (`mat_paper`) | GOOD AS ACCESS | Imported paper is appropriate. |
| **Pendulum clock and later the balance spring** (`clock_pendulum`) | WRONG BY CENTURIES | Mechanical clocks are emerging around this period; the pendulum clock is seventeenth century. Split mechanical escapement clock from pendulum clock. |
| **Sternpost rudder** (`sea_sternpost_rudder`) | GOOD | Appropriate by 1300 in northern European shipping. |

## Inherited/granted opening state — all nodes

| # | Granted node | Realism flag | Description |
|---:|---|---|---|
| 1 | **Sustained 700 C (pottery kiln)** (`cap_heat_0700`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 2 | **Muscle and animal power** (`cap_power_muscle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 3 | **Water power, tens of kW on one shaft** (`cap_power_water`) | GOOD | Adequate/good |
| 4 | **Tolerance 1 mm (skilled hand craft)** (`cap_tol_1mm`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 5 | **Glass panes for windows** (`civ_glass_windows`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 6 | **Wrought iron working and riveting** (`civ_iron_wrought`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 7 | **Marble veneer and ashlar facing** (`civ_marble_facing`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 8 | **Pendulum clock and later the balance spring** (`clock_pendulum`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 9 | **Crank, connecting rod, flywheel, cam and trip hammer** (`crank_conrod`) | BUNDLED TOO FAR | Adequate/good |
| 10 | **Auction and competitive bidding** (`fin_auction`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 11 | **Coined money** (`fin_coined_money`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 12 | **Contract law and enforcement** (`fin_contract_law`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 13 | **Standing bureaucracy** (`fin_government`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 14 | **Maritime loan at high interest** (`fin_maritime_loan`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 15 | **Permanent market and market law** (`fin_market`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 16 | **Tax farming and revenue contracts** (`fin_tax_farming`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 17 | **Testament and inheritance law** (`fin_testament`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 18 | **Wage and labour payment** (`fin_wage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 19 | **Board games, dice games, and pieces** (`hom_board_games`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 20 | **Beeswax candle** (`hom_candle_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 21 | **Tallow candle** (`hom_candle_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 22 | **Flush latrine with running water** (`hom_flush_latrine_simple`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 23 | **Wooden furniture** (`hom_furniture_wooden`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 24 | **Hypocaust underfloor heating** (`hom_hypocaust`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 25 | **Lead and ceramic plumbing** (`hom_lead_plumbing`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 26 | **Locks and keys** (`hom_locks_keys`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 27 | **Mirror, polished bronze** (`hom_mirror_bronze_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 28 | **Musical instruments** (`hom_musical_instruments`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 29 | **Oil lamp, simple** (`hom_oil_lamp_simple`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 30 | **Perfume by enfleurage** (`hom_perfume_enfleurage`) | NO OBVIOUS HARD CONFLICT | Assumes term |
| 31 | **Public bath (thermae)** (`hom_public_bath`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 32 | **Rigid padded horse collar, whippletree, nailed horseshoe** (`horse_collar`) | GOOD | Adequate/good |
| 33 | **Pivoting front axle** (`lnd_axle_pivot_front`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 34 | **Bridge** (`lnd_bridge`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 35 | **Four-wheeled cart** (`lnd_four_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 36 | **Harness of throat and girth type** (`lnd_harness_throat_girth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 37 | **Horse saddle (basic)** (`lnd_horse_saddle_basic`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 38 | **Litter** (`lnd_litter`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 39 | **Milestone** (`lnd_milestone`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 40 | **Mule transport** (`lnd_mule_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 41 | **Ox transport** (`lnd_ox_transport`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 42 | **Paved trunk road network** (`lnd_paved_road_network`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 43 | **Two-wheeled cart** (`lnd_two_wheel_cart`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 44 | **Iron tyre (tire)** (`lnd_tyre_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 45 | **Spoked wheel** (`lnd_wheel_spoked`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 46 | **Alum** (`mat_alum`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 47 | **Asbestos** (`mat_asbestos`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 48 | **Beeswax** (`mat_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 49 | **Bitumen and naphtha seeps** (`mat_bitumen`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 50 | **Brass (by cementation)** (`mat_brass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 51 | **Bronze** (`mat_bronze`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 52 | **Calamine (zinc carbonate/silicate ore)** (`mat_calamine`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 53 | **Carbon black and lampblack** (`mat_carbon_black`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 54 | **Charcoal** (`mat_charcoal`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 55 | **Emery (Naxos)** (`mat_emery`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 56 | **Galena (lead sulfide)** (`mat_galena`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 57 | **Soda-lime glass** (`mat_glass_soda`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 58 | **Gold** (`mat_gold`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 59 | **Gypsum plaster** (`mat_gypsum`) | NO OBVIOUS HARD CONFLICT | Thin |
| 60 | **Lead** (`mat_lead`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 61 | **Leather** (`mat_leather`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 62 | **Quicklime and slaked lime** (`mat_lime`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 63 | **Linen** (`mat_linen`) | NO OBVIOUS HARD CONFLICT | Assumes term |
| 64 | **Mercury** (`mat_mercury`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 65 | **Natron (sodium carbonate)** (`mat_natron`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 66 | **Olive oil** (`mat_olive_oil`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 67 | **Rag paper** (`mat_paper`) | GOOD AS ACCESS | Adequate/good |
| 68 | **Pyrolusite (manganese dioxide)** (`mat_pyrolusite`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 69 | **Salt** (`mat_salt`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 70 | **Shellac (traded)** (`mat_shellac`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 71 | **Silk (traded)** (`mat_silk`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 72 | **Silver** (`mat_silver`) | NO OBVIOUS HARD CONFLICT | Thin |
| 73 | **Sulfur** (`mat_sulfur`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 74 | **Tallow** (`mat_tallow`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 75 | **Tin** (`mat_tin`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 76 | **Vitriols (iron and copper sulfates)** (`mat_vitriols`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 77 | **Wrought iron (bloomery)** (`mat_wrought_iron`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 78 | **Cataract couching** (`med_cataract_couching`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 79 | **Legal protection for physicians** (`med_legal_physician`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 80 | **Opium and mandrake tinctures** (`med_opium_mandrake`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 81 | **Good surgical instrument kit** (`med_surgical_kit_good`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 82 | **Trepanation** (`med_trepanation`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 83 | **Wound suturing** (`med_wound_suturing`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 84 | **Burning glass** (`opt_burning_glass`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 85 | **Dioptra (sighting tube)** (`opt_dioptra`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 86 | **Geared mechanical transmission** (`opt_geared_mechanisms`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 87 | **Groma (surveying cross)** (`opt_groma`) | MIS-SCOPED / VERIFY LOCAL FORM | Assumes term |
| 88 | **Polished metal mirror** (`opt_metal_mirror_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 89 | **Steelyard balance** (`opt_steelyards`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 90 | **Sundial** (`opt_sundial`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 91 | **Water clock (clepsydra)** (`opt_water_clock`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 92 | **Water-filled globe as magnifier** (`opt_water_globe_magnifier`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 93 | **Carbon ink** (`prn_carbon_ink`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 94 | **Codex binding** (`prn_codex_bound`) | NO OBVIOUS HARD CONFLICT | Thin |
| 95 | **Library and archive** (`prn_library_archive`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 96 | **Mosaic and fresco** (`prn_mosaic_fresco`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 97 | **Papyrus sheets** (`prn_papyrus_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 98 | **Parchment sheets** (`prn_parchment_sheets`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 99 | **Scribal copying** (`prn_scribal_copying`) | NO OBVIOUS HARD CONFLICT | Thin |
| 100 | **Sculpture** (`prn_sculpture`) | NO OBVIOUS HARD CONFLICT | Thin |
| 101 | **Seals and stamps** (`prn_seals_stamps`) | NO OBVIOUS HARD CONFLICT | Thin |
| 102 | **Theatre and pantomime** (`prn_theatre_pantomime`) | NO OBVIOUS HARD CONFLICT | Thin |
| 103 | **Wax tablets** (`prn_wax_tablets`) | NO OBVIOUS HARD CONFLICT | Thin |
| 104 | **Animal-driven treadmill** (`pwr_animal_treadmill`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 105 | **Force pump** (`pwr_force_pump`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 106 | **Screw press** (`pwr_screw_press_power`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 107 | **Sails on ships** (`pwr_ship_sail`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 108 | **Rag paper from linen** (`rag_paper`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 109 | **Anchor** (`sea_anchor`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 110 | **Coastal pilotage** (`sea_coastal_pilotage`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 111 | **Large merchant sailing ships** (`sea_merchant_ships_large`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 112 | **Monsoon route to India** (`sea_monsoon_route`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 113 | **Mortise-and-tenon hull construction** (`sea_mortise_tenon`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 114 | **Sounding lines** (`sea_sounding_lines`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 115 | **Spritsail** (`sea_spritsail`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 116 | **Square sail with brails** (`sea_square_sail`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 117 | **Steering oars** (`sea_steering_oars`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 118 | **Sternpost rudder** (`sea_sternpost_rudder`) | GOOD | Adequate/good |
| 119 | **Cotton by trade** (`tex_cotton_trade`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 120 | **Drop spindle** (`tex_drop_spindle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 121 | **Dyeing with madder root** (`tex_dye_madder`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 122 | **Murex purple dyeing** (`tex_dye_murex`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 123 | **Dyeing with woad** (`tex_dye_woad`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 124 | **Felting** (`tex_felting`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 125 | **Sailcloth** (`tex_sailcloth`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 126 | **Silk by trade** (`tex_silk_trade`) | NO OBVIOUS HARD CONFLICT | Thin |
| 127 | **Two-beam loom** (`tex_two_beam_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 128 | **Warp-weighted loom** (`tex_warp_weighted_loom`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 129 | **Wool fiber** (`tex_wool`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 130 | **Overshot wheels, millponds, leats, line shafting** (`water_power_scale`) | MOSTLY GOOD, SCOPE FIX | Adequate/good |

## Immediately startable opening projects — all nodes

`BASELINE CONTAMINATED` means the project is startable because at least one of its direct prerequisites is an inherited node flagged above as wrong/foreign/anachronistic. `GENERIC MISSING GATE` carries over a dependency defect already identified in the Rome audit and is not a judgment that the civilization is “too advanced.”

| # | Project | Cost | Founder h | Hired labour | Floor y | Prereqs | Realism flag | Description |
|---:|---|---:|---:|---|---:|---|---|---|
| 1 | **Chaff cutter** (`ag2_chaff_cutter`) | 314.8 | 50 | 140h smith | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 2 | **Composting** (`ag2_composting`) | 206.3 | 40 | 100h labourer | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 3 | **Contour ploughing** (`ag2_contour_ploughing`) | 308.0 | 70 | — | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 4 | **Coulter** (`ag2_coulter`) | 286.3 | 40 | 120h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Thin |
| 5 | **Cultivator** (`ag2_cultivator`) | 477.5 | 70 | 220h smith | 0.35 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 6 | **Grafting** (`ag2_grafting`) | 242.0 | 50 | — | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 7 | **Guano** (`ag2_guano`) | 130.9 | 30 | 80h merchant | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 8 | **Harrow** (`ag2_harrow`) | 264.3 | 45 | 100h smith | 0.25 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 9 | **Hopping** (`ag2_hopping`) | 165.0 | 40 | — | 0.15 | — | GENERIC MISSING GATE | Adequate/good |
| 10 | **Layering** (`ag2_layering`) | 181.5 | 40 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 11 | **Liming** (`ag2_liming`) | 193.6 | 30 | 80h labourer | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 12 | **Malting** (`ag2_malting`) | 264.0 | 60 | — | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 13 | **Marling** (`ag2_marling`) | 154.6 | 25 | 60h labourer | 0.15 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 14 | **Oil pressing** (`ag2_oil_pressing`) | 265.8 | 60 | — | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 15 | **Potash** (`ag2_potash`) | 206.3 | 40 | 100h labourer | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 16 | **Pyrethrum** (`ag2_pyrethrum`) | 308.0 | 70 | — | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 17 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 261.8 | 70 | — | 0.5 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 18 | **Roller** (`ag2_roller`) | 308.6 | 40 | 80h smith | 0.25 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 19 | **Root cutter** (`ag2_root_cutter`) | 426.4 | 60 | 180h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 20 | **Subsoiler** (`ag2_subsoiler`) | 414.3 | 55 | 180h smith | 0.3 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 21 | **Tedder** (`ag2_tedder`) | 455.0 | 65 | 200h smith | 0.35 | horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 22 | **Compass for navigation** (`air_compass_magnetic`) | 96.5 | 30 | 50h artisan | 0.1 | mat_silk, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 23 | **Kite** (`air_kite_basic`) | 173.6 | 20 | 40h artisan | 0.1 | mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 24 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 1,472.2 | 120 | 200h artisan | 0.5 | mat_beeswax, mat_linen, mat_silk | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 25 | **Decimal positional notation, zero, negative numbers, decimal fractions** (`arithmetic_positional`) | 968.0 | 450 | 2500h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 26 | **Six months of listening before you act** (`arrival_orientation`) | 561.0 | 900 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 27 | **Time to the second (pendulum)** (`cap_measure_time_s`) | 0.0 | 0 | — | 0 | clock_pendulum | BASELINE CONTAMINATED | Thin |
| 28 | **Roman masonry arch** (`civ_arch_roman`) | 365.5 | 60 | 120h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 29 | **Roman fired brick and tile** (`civ_brick_tile`) | 232.3 | 40 | 80h potter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 30 | **Chorobates: Roman water levelling rod** (`civ_chorobates`) | 151.0 | 25 | 30h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 31 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 156.2 | 80 | 150h smith | 0.4 | mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 32 | **Groma: Roman X-staff surveying tool** (`civ_surveying_groma`) | 124.9 | 20 | 20h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 33 | **Block and tackle with rope** (`cn_block_tackle_hoist`) | 314.9 | 30 | 60h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 34 | **Treadwheel crane** (`cn_crane_treadwheel`) | 633.6 | 55 | 100h carpenter, 80h labourer | 0.7 | cap_power_muscle, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 35 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 584.1 | 50 | 100h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 36 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 179.1 | 35 | 80h mason | 0.15 | mat_gypsum | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 37 | **Pile driving by drop hammer** (`cn_pile_driving`) | 498.1 | 40 | 150h labourer | 0.8 | cap_power_muscle | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 38 | **Post and lintel structure** (`cn_post_lintel`) | 259.2 | 25 | 50h carpenter, 100h mason | 0.4 | cap_tol_1mm | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 39 | **Stone quarrying with wedge** (`cn_quarrying_wedge`) | 136.1 | 20 | 100h labourer | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 40 | **Timber scaffolding system** (`cn_scaffolding`) | 750.7 | 50 | 120h carpenter | 0.6 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 41 | **Soil compaction by roller** (`cn_soil_compaction`) | 1,087.8 | 70 | 120h labourer | 1 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 42 | **Stone polishing and smoothing** (`cn_stone_polish`) | 151.6 | 30 | 80h mason | 0.15 | cap_tol_1mm | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 43 | **Codebook for optical signal tower** (`com_optical_codebook`) | 77.0 | 100 | 200h scribe | 0.25 | — | GENERIC MISSING GATE | Adequate/good |
| 44 | **Signal flags for maritime communication** (`com_signal_flags`) | 247.1 | 40 | 60h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 45 | **Horse gin** (`en_horse_gin`) | 95.6 | 30 | 150h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 46 | **Peat extraction and drying** (`en_peat_fuel`) | 284.9 | 70 | 322h miner | 1 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 47 | **Penstock and flume** (`en_penstock`) | 188.0 | 50 | 200h carpenter, 368h mason | 2 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 48 | **Spring motor (large clockwork)** (`en_spring_motor`) | 12.1 | 80 | — | 0.8 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 49 | **Treadwheel** (`en_treadwheel`) | 46.0 | 20 | 100h carpenter | 0.2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 50 | **Annona grain dole and administration** (`fin_annona`) | 3,627.0 | 600 | 200h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 51 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 15.0 | 80 | 80h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 52 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 33.7 | 80 | 150h merchant | 1 | fin_market | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 53 | **Deposit bankers (argentarii)** (`fin_argentarii`) | 1,413.7 | 150 | 60h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 54 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 37.4 | 120 | 200h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 55 | **Bill of exchange** (`fin_bill_exchange`) | 65.5 | 150 | 200h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 56 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 50.0 | 100 | 50h master, 150h merchant | 2 | fin_coined_money | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 57 | **Cartel and market sharing agreement** (`fin_cartel`) | 44.9 | 100 | 200h merchant | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 58 | **Census and population enumeration** (`fin_census`) | 1,972.8 | 200 | 200h merchant, 300h scribe | 2 | fin_government | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 59 | **Professional associations (collegia)** (`fin_collegium`) | 849.0 | 120 | 40h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 60 | **Contract of employment** (`fin_employment_contract`) | 9.3 | 60 | 50h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 61 | **Ferry and toll crossing** (`fin_ferry`) | 2,107.0 | 100 | 100h carpenter, 150h merchant | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 62 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 1,975.2 | 100 | 150h merchant | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 63 | **Hotel and commercial lodging** (`fin_hotel`) | 5,228.6 | 120 | 150h carpenter, 200h merchant | 2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 64 | **Inn and coaching house** (`fin_inn`) | 3,175.9 | 100 | 150h merchant | 1.5 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 65 | **Lottery and state gambling** (`fin_lottery`) | 1,944.8 | 150 | 200h merchant, 150h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 66 | **Marine insurance** (`fin_marine_insurance`) | 3,838.2 | 200 | 300h merchant, 150h scribe | 2 | fin_maritime_loan | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 67 | **Monopoly and exclusive grant** (`fin_monopoly`) | 44.4 | 80 | 150h merchant, 50h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 68 | **Mortgage and real estate credit** (`fin_mortgage`) | 53.8 | 120 | 150h merchant, 100h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 69 | **Patent and exclusive right** (`fin_patent`) | 53.8 | 140 | 150h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 70 | **Pawnshop and secured loan** (`fin_pawnshop`) | 958.4 | 60 | 100h merchant | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 71 | **Plantation and large estate agriculture** (`fin_plantation`) | 9,045.1 | 200 | 300h merchant | 3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 72 | **Postal service as paid business** (`fin_postal_service`) | 4,997.1 | 180 | 200h carpenter, 250h merchant | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 73 | **Seigniorage and debasement** (`fin_seigniorage`) | 23.4 | 80 | 100h merchant | 0.2 | fin_coined_money | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 74 | **Partnership (societas)** (`fin_societas`) | 284.2 | 40 | 20h scribe | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 75 | **Tariff and import duty** (`fin_tariff`) | 44.4 | 100 | 150h merchant, 50h scribe | 2 | fin_tax_farming | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 76 | **Trademark and mark of quality** (`fin_trademark`) | 18.7 | 80 | 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 77 | **Trading post and remote store** (`fin_trading_post`) | 1,492.5 | 100 | 150h merchant | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 78 | **Usury law and interest regulation** (`fin_usury_law`) | 28.1 | 100 | 150h scribe | 1 | fin_contract_law | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 79 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 399.3 | 120 | 200h artisan | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 80 | **Hay making and dry storage** (`fud_hay_making_storage`) | 219.7 | 100 | 300h labourer | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 81 | **Heavy mouldboard plough with coulter (regional)** (`fud_heavy_mouldboard_plough_coulter`) | 465.2 | 200 | 150h carpenter, 200h smith | 1 | cap_tol_1mm, horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 82 | **Mechanical grain reaper** (`fud_mechanical_reaper`) | 878.0 | 300 | 200h carpenter, 150h smith | 1 | cap_tol_1mm, horse_collar | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 83 | **Organized whaling industry for oil and meat** (`fud_whaling_industry`) | 2,277.0 | 300 | 200h artisan, 400h sailor | 1 | sea_merchant_ships_large | GENERIC MISSING GATE | Adequate/good |
| 84 | **Button with eyelet** (`hom_button`) | 37.3 | 40 | 60h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 85 | **Roman cosmetics** (`hom_cosmetics_roman`) | 88.0 | 20 | — | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 86 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 5.5 | 30 | — | 0.1 | — | GENERIC MISSING GATE | Adequate/good |
| 87 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 298.6 | 120 | 80h carpenter, 200h mason | 1 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 88 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 218.9 | 80 | 80h artisan, 100h plumber | 0.5 | hom_flush_latrine_simple | GENERIC MISSING GATE | Adequate/good |
| 89 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 161.6 | 60 | 100h artisan, 80h plumber | 0.5 | hom_flush_latrine_simple | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 90 | **Mangle and wringer** (`hom_mangle_wringer`) | 150.7 | 100 | 120h artisan, 80h carpenter | 0.75 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 91 | **Mechanical clock for home** (`hom_mechanical_clock_home`) | 1,072.0 | 180 | 200h artisan, 100h carpenter, 250h master | 1.5 | cap_tol_1mm, crank_conrod, water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 92 | **Metronome** (`hom_metronome`) | 215.2 | 110 | 100h artisan, 160h master | 0.75 | cap_tol_1mm, clock_pendulum | BASELINE CONTAMINATED | Adequate/good |
| 93 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 91.4 | 50 | 80h carpenter | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 94 | **Safety pin** (`hom_safety_pin`) | 26.5 | 40 | 50h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 95 | **Sewing machine, hand-crank** (`hom_sewing_machine_hand`) | 316.8 | 180 | 200h artisan, 200h master, 100h smith | 1 | cap_tol_1mm, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 96 | **Sprung mattress** (`hom_sprung_mattress`) | 314.1 | 120 | 150h artisan, 100h carpenter | 1 | cap_tol_1mm, mat_wrought_iron | GENERIC MISSING GATE | Adequate/good |
| 97 | **Toothbrush** (`hom_toothbrush`) | 33.3 | 60 | 100h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 98 | **Toys and dolls** (`hom_toys_dolls`) | 83.0 | 60 | 60h artisan, 80h carpenter | 0.5 | cap_tol_1mm | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 99 | **Umbrella** (`hom_umbrella`) | 98.7 | 80 | 60h artisan, 100h carpenter | 0.5 | cap_tol_1mm | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 100 | **Washing machine, hand-powered** (`hom_washing_machine_hand`) | 194.8 | 140 | 160h artisan, 100h carpenter | 1 | cap_tol_1mm, water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 101 | **Establish a respectable cover identity** (`identity_cover`) | 1,477.3 | 500 | 400h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 102 | **Quill pen** (`if_quill`) | 254.3 | 15 | 40h scribe | 0.05 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Thin |
| 103 | **Coach** (`lnd_coach`) | 921.4 | 200 | 150h artisan, 400h carpenter, 200h smith | 2 | lnd_four_wheel_cart, lnd_harness_throat_girth, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 104 | **Cursus publicus courier service** (`lnd_cursus_publicus`) | 0.0 | 0 | — | 0 | lnd_horse_saddle_basic, lnd_paved_road_network | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 105 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 223.0 | 40 | 100h carpenter, 60h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 106 | **Wheelbarrow** (`lnd_wheelbarrow`) | 97.9 | 30 | 80h carpenter, 30h smith | 0.5 | lnd_wheel_spoked | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 107 | **Obsidian blade knapping** (`mat_obsidian_blade`) | 196.4 | 40 | 600h artisan | 0.5 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 108 | **Papyrus** (`mat_papyrus`) | 377.5 | 20 | 60h scribe | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 109 | **Parchment** (`mat_parchment`) | 503.4 | 30 | 80h scribe | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 110 | **Plaster cast immobilization** (`md2_plaster_cast`) | 239.8 | 100 | 120h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 111 | **Vector control** (`md2_vector_control`) | 272.8 | 100 | 120h scholar | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 112 | **Amputation and prosthetics** (`med_amputation`) | 13.6 | 0 | 50h artisan | 0 | med_surgical_kit_good | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 113 | **Bone setting** (`med_bone_setting`) | 10.2 | 0 | 50h artisan | 0.5 | med_surgical_kit_good | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 114 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 638.0 | 100 | 200h scholar | 0.5 | mat_olive_oil | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 115 | **Obstetric practice** (`med_obstetric_practice`) | 20.6 | 0 | 100h artisan | 0 | mat_linen | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 116 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 238.5 | 40 | 100h artisan | 0 | mat_linen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 117 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | 1,565.5 | 100 | 2500h furnaceman, 2000h labourer | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 118 | **Investment casting and lost wax** (`met_investment_casting`) | 362.8 | 100 | 140h artisan | 0.8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 119 | **Mine pumping systems** (`met_mine_pumping`) | 2,648.8 | 180 | 50h artisan, 200h carpenter, 150h smith | 2.5 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 120 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 96.3 | 20 | 400h labourer | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 121 | **Safety lamps and mine ventilation** (`met_safety_lamps_ventilation`) | 1,086.4 | 140 | 100h artisan, 200h miner | 1.8 | cap_heat_0700, cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 122 | **Trip hammer and water-driven forge hammer** (`met_trip_hammer`) | 795.2 | 80 | 80h carpenter, 120h smith | 1.2 | cap_power_water, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 123 | **Water-powered ore stamp mill** (`met_water_ore_stamp`) | 678.2 | 120 | 50h artisan, 200h carpenter, 100h smith | 1.5 | cap_power_water, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 124 | **Adhesive bonding** (`mfg_adhesive_bond`) | 241.5 | 140 | 120h artisan | 0.3 | mat_bitumen | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 125 | **Cold riveting** (`mfg_cold_riveting`) | 245.3 | 100 | 120h artisan | 0.2 | mat_wrought_iron | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 126 | **Drawing office** (`mfg_drawing_office`) | 508.2 | 150 | 200h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 127 | **Enamelling** (`mfg_enamelling`) | 190.8 | 120 | 140h furnaceman | 0.3 | cap_heat_0700, mat_glass_soda | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 128 | **Flux** (`mfg_flux`) | 229.9 | 60 | 60h artisan | 0.15 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 129 | **Hot riveting** (`mfg_hot_riveting`) | 242.0 | 80 | 100h artisan | 0.2 | mat_wrought_iron | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 130 | **Japanning** (`mfg_japanning`) | 193.2 | 110 | 130h artisan | 0.25 | mat_shellac | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 131 | **Casting mould** (`mfg_mould`) | 244.8 | 120 | 150h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 132 | **Painting** (`mfg_painting`) | 198.0 | 80 | 100h artisan | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 133 | **Production schedule** (`mfg_production_schedule`) | 220.0 | 130 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 134 | **Silver soldering** (`mfg_silver_solder`) | 941.7 | 100 | 120h smith | 0.25 | cap_heat_0700, mat_silver | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 135 | **Soft soldering** (`mfg_soft_solder`) | 260.1 | 80 | 100h artisan | 0.2 | mat_lead | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 136 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 6,925.6 | 80 | 300h master | 0.5 | mat_mercury | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 137 | **Drifting: horizontal tunneling along ore seams** (`mt2_drifting_horizontal`) | 264.6 | 110 | 450h miner | 1.5 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 138 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 215.1 | 60 | 200h potter | 0.5 | cap_heat_0700 | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 139 | **Hydraulic mining: washing ore and overburden with water pressure** (`mt2_hydraulic_mining`) | 244.8 | 120 | 300h labourer | 1.2 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 140 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 245.9 | 110 | 300h labourer | 0.8 | cap_tol_1mm | GENERIC MISSING GATE | Adequate/good |
| 141 | **Shaft sinking: deep vertical access to ore bodies** (`mt2_shaft_sinking_mining`) | 269.5 | 120 | 500h miner | 2 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 142 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 6,099.5 | 100 | 250h smith | 0.5 | cap_heat_0700, mat_lead, mat_tin | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 143 | **Stoping: extracting ore in upward progression from access drifts** (`mt2_stoping_ore_extraction`) | 259.6 | 100 | 400h miner | 1 | cap_power_water | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 144 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 290.4 | 80 | 300h carpenter | 0.8 | cap_power_muscle | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 145 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 2,030.6 | 110 | 300h furnaceman | 0.8 | mat_lead, mat_tin | GENERIC MISSING GATE | Adequate/good |
| 146 | **Anemometer (wind speed)** (`opt_anemometer`) | 370.9 | 60 | 100h artisan, 40h carpenter, 60h smith | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 147 | **Manometer (pressure measurement)** (`opt_manometer`) | 347.4 | 60 | 60h artisan, 80h glassblower | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 148 | **Mandrel and self-centering chuck** (`prc_mandrel_chuck`) | 181.3 | 60 | 80h artisan, 120h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 149 | **Pantograph and copying mechanism for die sinking** (`prc_pantograph_copying`) | 478.6 | 80 | 180h artisan, 100h smith | 0.5 | cap_tol_1mm, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 150 | **Straightedge and reference straightness** (`prc_straightedge`) | 90.0 | 30 | 80h artisan, 60h smith | 0.2 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 151 | **Tailstock and dead centre** (`prc_tailstock_deadcentre`) | 189.4 | 50 | 100h artisan, 60h smith | 0.2 | cap_tol_1mm, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 152 | **Treadle lathe with flywheel** (`prc_treadle_lathe_flywheel`) | 275.3 | 80 | 200h carpenter, 100h smith | 0.5 | cap_power_muscle, cap_tol_1mm, crank_conrod | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 153 | **Hand papermaking** (`prn_hand_papermaking`) | 139.7 | 80 | 300h artisan | 1 | rag_paper | BASELINE CONTAMINATED | Adequate/good |
| 154 | **Water-driven pulp stamper** (`prn_pulp_stamper`) | 309.7 | 100 | 200h carpenter, 150h smith | 1.5 | cap_power_water, rag_paper | BASELINE CONTAMINATED | Adequate/good |
| 155 | **Surface sizing** (`prn_sizing_surface`) | 60.8 | 50 | 100h artisan | 0.3 | mat_alum, rag_paper | BASELINE CONTAMINATED | Adequate/good |
| 156 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 239.3 | 150 | 200h artisan, 250h smith | 1 | cap_tol_1mm, mat_brass | GENERIC MISSING GATE | Adequate/good |
| 157 | **Coal seam and mining** (`pwr_coal_seam`) | 353.1 | 150 | 300h labourer, 400h miner | 1 | cap_tol_1mm | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 158 | **Leat and weir** (`pwr_leat_and_weir`) | 311.9 | 200 | 150h artisan, 500h labourer | 2 | water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 159 | **Millpond and storage** (`pwr_millpond`) | 393.8 | 150 | 100h artisan, 400h labourer | 1 | water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 160 | **Horizontal waterwheel (Norse)** (`pwr_norse_waterwheel`) | 169.4 | 120 | 150h artisan, 200h carpenter | 0.5 | water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 161 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 52.3 | 80 | 100h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 162 | **Peat extraction and burning** (`pwr_peat`) | 74.3 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 163 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 132.0 | 100 | 200h labourer | 0.5 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 164 | **Trompe (water-driven air blast)** (`pwr_trompe`) | 316.3 | 180 | 150h artisan, 250h carpenter | 1 | water_power_scale | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 165 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 280.7 | 80 | 160h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 166 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 264.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 167 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 242.0 | 150 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 168 | **Examination and credentialing** (`sc2_institution_examination`) | 387.2 | 80 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 169 | **Funded research programme** (`sc2_institution_funded_programme`) | 242.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 170 | **Referee and peer review** (`sc2_institution_referee`) | 242.0 | 100 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 171 | **Research group and principal investigator** (`sc2_institution_research_group`) | 242.0 | 100 | — | 5 | — | GENERIC MISSING GATE | Adequate/good |
| 172 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 1,320.0 | 200 | 400h scholar, 200h scribe | 8 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 173 | **Hypothesis and prediction** (`sc2_method_hypothesis`) | 242.0 | 90 | — | 8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 174 | **Negative result and null finding** (`sc2_method_negative_result`) | 242.0 | 90 | — | 20 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 175 | **Replication and repeatability** (`sc2_method_replication`) | 242.0 | 80 | — | 10 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 176 | **The decimal point convention** (`sc2_notation_decimal_point`) | 251.7 | 20 | 40h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 177 | **Exponent notation** (`sc2_notation_exponents`) | 263.8 | 45 | 90h scribe | 2 | — | GENERIC MISSING GATE | Adequate/good |
| 178 | **Positional notation and place value** (`sc2_notation_positional`) | 242.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 179 | **Root symbols and radical notation** (`sc2_notation_roots`) | 261.4 | 40 | 80h scribe | 3 | — | GENERIC MISSING GATE | Adequate/good |
| 180 | **Newton's law of universal gravitation** (`sc2_physics_gravitation`) | 285.6 | 100 | 180h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 181 | **Kinematics: position, velocity, acceleration** (`sc2_physics_kinematics`) | 283.1 | 90 | 170h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 182 | **Momentum and impulse** (`sc2_physics_momentum`) | 278.3 | 80 | 150h scribe | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 183 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 259.6 | 100 | 180h scribe | 4 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 184 | **Probability axioms and conditional probability** (`sc2_probability_axioms`) | 242.0 | 100 | — | 4 | — | GENERIC MISSING GATE | Adequate/good |
| 185 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 242.0 | 350 | 500h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 186 | **Cross-staff for latitude** (`sea_cross_staff`) | 341.7 | 80 | 150h artisan, 100h scholar | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 187 | **Diving bell** (`sea_diving_bell`) | 1,065.4 | 120 | 300h carpenter, 100h smith | 0.4 | sea_anchor | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 188 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | 1,383.8 | 100 | 3000h carpenter | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 189 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,589.5 | 0 | — | 0 | mat_lead | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 190 | **Lodestone knowledge** (`sea_lodestone`) | 123.4 | 20 | 80h scholar | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 191 | **Log line for speed** (`sea_log_line`) | 54.6 | 30 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 192 | **Pharos lighthouse** (`sea_pharos_lighthouse`) | 0.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 193 | **Skeleton-first hull construction** (`sea_skeleton_first`) | 1,064.5 | 250 | 200h artisan, 600h carpenter | 1 | cap_tol_1mm, sea_mortise_tenon | BASELINE CONTAMINATED | Adequate/good |
| 194 | **Field bleaching with sun** (`tex_field_bleaching`) | 181.0 | 50 | 300h labourer | 2 | mat_linen, tex_sailcloth | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 195 | **Hand ginning cotton** (`tex_hand_ginning`) | 48.1 | 30 | 200h labourer | 0.2 | tex_cotton_trade | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 196 | **Horizontal loom** (`tex_horizontal_loom`) | 155.3 | 80 | 100h artisan, 200h carpenter | 0.5 | cap_tol_1mm, tex_two_beam_loom | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 197 | **Indigo dyeing** (`tex_indigo`) | 129.2 | 60 | 140h artisan | 0.4 | mat_natron, tex_dye_woad | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 198 | **Knitting frame** (`tex_knitting_frame`) | 861.9 | 150 | 120h artisan, 200h carpenter, 220h smith | 1 | cap_tol_1mm, crank_conrod, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 199 | **Mordanting dyes with alum** (`tex_mordanting`) | 88.9 | 40 | 100h artisan | 0.3 | mat_alum, tex_dye_madder | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 200 | **Spinning wheel with flyer** (`tex_spinning_wheel`) | 145.6 | 100 | 120h artisan, 200h carpenter | 0.5 | cap_tol_1mm, crank_conrod, tex_drop_spindle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 201 | **Vegetable tanning of leather** (`tex_vegetable_tanning`) | 702.2 | 100 | 250h artisan, 200h labourer | 1.2 | mat_leather | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 202 | **Stirrup with foot loop** (`tl_stirrup`) | 353.2 | 60 | 50h artisan, 150h smith | 0.2 | mat_leather, lnd_horse_saddle_basic, mat_wrought_iron | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 203 | **Bilge pump** (`tr_bilge_pump`) | 415.6 | 50 | 150h carpenter, 100h smith | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 204 | **Block and tackle pulley** (`tr_block_tackle`) | 290.6 | 40 | 150h carpenter, 50h smith | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 205 | **Hopper wagon for bulk minerals** (`tr_hopper_wagon`) | 335.9 | 50 | 250h carpenter, 100h smith | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 206 | **Lateen sail** (`tr_lateen_sail`) | 814.0 | 80 | — | 0.5 | sea_square_sail | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 207 | **Reefing sails** (`tr_reefing`) | 253.0 | 50 | 300h sailor | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 208 | **Block rigging and rope lashing** (`tr_rigging_block_lashing`) | 242.0 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 209 | **Semaphore signal** (`tr_semaphore_signal`) | 279.7 | 40 | 100h carpenter, 100h smith | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 210 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 282.0 | 30 | 150h carpenter, 400h labourer | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 211 | **Square rig sails** (`tr_square_rig`) | 1,210.0 | 40 | — | 0.6 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 212 | **Wooden waggonway** (`tr_wooden_waggonway`) | 258.7 | 40 | 200h carpenter | 2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 213 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 836.0 | 60 | 80h artisan | 0.4 | mat_alum | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 214 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 1,167.4 | 80 | 100h artisan | 1 | mat_asbestos | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 215 | **Beam: warp holder and tension** (`tx2_beam`) | 10.9 | 40 | 60h carpenter | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 216 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 5.3 | 30 | 40h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 217 | **Bottle: glass container** (`tx2_bottle`) | 1,245.2 | 60 | 100h glassblower | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 218 | **Button: bone material** (`tx2_button_bone`) | 11.1 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 219 | **Button: horn material** (`tx2_button_horn`) | 11.0 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 220 | **Button: shell material** (`tx2_button_shell`) | 12.7 | 50 | 70h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 221 | **Cardboard box: folded laminate container** (`tx2_cardboard_box`) | 218.9 | 70 | 120h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 222 | **Carding: opening and aligning fibres** (`tx2_carding`) | 100.8 | 60 | 150h artisan | 0.2 | cap_tol_1mm, tex_wool | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 223 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 8.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 224 | **Comb: hair grooming tool** (`tx2_comb`) | 14.3 | 50 | 80h artisan | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 225 | **Corset: rigid body support garment** (`tx2_corset`) | 33.0 | 100 | 200h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 226 | **Cotton gin: separation of seed from fibre** (`tx2_cotton_ginning`) | 38.4 | 120 | 80h carpenter, 60h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 227 | **Yarn count standardisation** (`tx2_count_standard`) | 6.6 | 40 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 228 | **Currying: leather finish dressing** (`tx2_currying`) | 16.5 | 60 | 100h artisan | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 229 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 15.4 | 60 | 80h carpenter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 230 | **Doll: articulated child plaything** (`tx2_doll`) | 91.9 | 80 | 150h artisan | 1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 231 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 31.5 | 50 | 70h smith | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 232 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 629.2 | 60 | 100h artisan | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 233 | **Dyeing in garment: finished good colouration** (`tx2_dyeing_garment`) | 700.8 | 90 | 160h artisan | 1 | tex_dye_madder | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 234 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 634.5 | 80 | 140h artisan | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 235 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 631.8 | 70 | 120h artisan | 0.3 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 236 | **Envelope: paper folded container** (`tx2_envelope_gummed`) | 82.5 | 60 | 100h artisan | 0.3 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 237 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 125.2 | 50 | 60h smith | 0.15 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 238 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 7.4 | 40 | 60h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 239 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 30.7 | 70 | 40h carpenter, 80h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 240 | **Fulling: cloth densification** (`tx2_fulling`) | 689.3 | 60 | 80h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 241 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 10.5 | 40 | 50h artisan | 0.1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 242 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 7.4 | 40 | 60h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 243 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 21.8 | 50 | 60h smith | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 244 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 8.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 245 | **Mirror: reflective glass surface** (`tx2_mirror`) | 347.6 | 70 | 100h artisan | 0.3 | mat_glass_soda | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 246 | **Mohair: angora goat fibre** (`tx2_mohair`) | 8.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 247 | **Needle: sewing implement** (`tx2_needle`) | 123.0 | 40 | 60h smith | 0.1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 248 | **Paper bag: folded container** (`tx2_paper_bag`) | 122.1 | 60 | 100h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 249 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 18.3 | 50 | 70h smith | 0.5 | — | GENERIC MISSING GATE | Adequate/good |
| 250 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 60.5 | 80 | 120h artisan | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 251 | **Pin: sewing fastener** (`tx2_pin`) | 13.0 | 40 | 60h smith | 0.1 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 252 | **Postcard: prepaid correspondence** (`tx2_postcard`) | 36.5 | 70 | 100h artisan | 1 | mat_paper | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 253 | **Press stud: snap fastener** (`tx2_press_stud`) | 96.7 | 80 | 100h smith | 1 | mat_brass | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 254 | **Block printing: carved design application** (`tx2_printing_block`) | 48.5 | 100 | 200h artisan, 80h engraver | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 255 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 8.7 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 256 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 645.0 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 257 | **Retting of flax and hemp fibres** (`tx2_retting`) | 6.6 | 30 | 40h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Assumes term |
| 258 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 9.9 | 40 | 60h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 259 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 625.2 | 40 | 60h artisan | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 260 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 8.2 | 40 | 50h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Assumes term |
| 261 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 6.6 | 30 | 40h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 262 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 254.9 | 40 | 60h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 263 | **Singeing: flame removal of nap** (`tx2_singeing`) | 1,076.5 | 60 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 264 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 19.8 | 100 | 120h artisan | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 265 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 34.1 | 60 | 100h artisan | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 266 | **Splitting: leather layering** (`tx2_splitting`) | 17.6 | 70 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 267 | **Twist insertion control** (`tx2_twist_insertion`) | 9.9 | 50 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 268 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 9.9 | 50 | 60h artisan | 0.2 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 269 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 23.1 | 60 | 80h carpenter | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 270 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 19,156.1 | 80 | 60h engraver, 120h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 271 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 7.8 | 40 | 50h artisan | 0 | — | LIKELY ALREADY KNOWN BY 1300 | Adequate/good |
| 272 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 415.1 | 300 | 200h carpenter, 400h smith | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |

### Opening-project triage counts

- **PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK: 146**
- **LIKELY ALREADY KNOWN BY 1300: 86**
- **GENERIC MISSING GATE: 34**
- **BASELINE CONTAMINATED: 6**

### Highest-confidence fixes

- Replace `clock_pendulum` with an early weight-driven mechanical clock/escapement node. Pendulum belongs centuries later.
- Grant paper as imported material, not English rag-paper manufacture.
- Split the crank/connecting-rod/flywheel/cam/trip-hammer mega-node and trim `water_power_scale` so it does not imply mature factory line-shafting.
- Because the date is 1300, many projects Rome had to research should simply be inherited here; the current 130 grants understate medieval craft development even while a few individual grants overshoot it.

# The Mexica Triple Alliance (1500)

## Explicit civilization seeds

| Seed | Verdict | Note |
|---|---|---|
| **Chinampa raised-bed agriculture** (`fud_chinampa`) | GOOD | Signature central-Mexican raised-bed agriculture. |
| **Maize** (`fud_maize`) | GOOD | Correct staple crop. |
| **Cacao** (`fud_cacao`) | GOOD | Correct regional crop/trade good. |
| **Monumental stone construction without iron tools** (`civ_monumental_stone`) | GOOD | Correct and importantly specified as construction without iron tools. |
| **Obsidian blade knapping** (`mat_obsidian_blade`) | GOOD | Excellent region-specific material/craft grant. |

## Inherited/granted opening state — all nodes

| # | Granted node | Realism flag | Description |
|---:|---|---|---|
| 1 | **Sustained 700 C (pottery kiln)** (`cap_heat_0700`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 2 | **Muscle and animal power** (`cap_power_muscle`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 3 | **Tolerance 1 mm (skilled hand craft)** (`cap_tol_1mm`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 4 | **Glass panes for windows** (`civ_glass_windows`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 5 | **Wrought iron working and riveting** (`civ_iron_wrought`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 6 | **Marble veneer and ashlar facing** (`civ_marble_facing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 7 | **Monumental stone construction without iron tools** (`civ_monumental_stone`) | GOOD | Adequate/good |
| 8 | **Auction and competitive bidding** (`fin_auction`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 9 | **Coined money** (`fin_coined_money`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 10 | **Contract law and enforcement** (`fin_contract_law`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 11 | **Standing bureaucracy** (`fin_government`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 12 | **Maritime loan at high interest** (`fin_maritime_loan`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 13 | **Permanent market and market law** (`fin_market`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 14 | **Tax farming and revenue contracts** (`fin_tax_farming`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 15 | **Testament and inheritance law** (`fin_testament`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 16 | **Wage and labour payment** (`fin_wage`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 17 | **Cacao** (`fud_cacao`) | GOOD | Adequate/good |
| 18 | **Chinampa raised-bed agriculture** (`fud_chinampa`) | GOOD | Adequate/good |
| 19 | **Maize** (`fud_maize`) | GOOD | Adequate/good |
| 20 | **Board games, dice games, and pieces** (`hom_board_games`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 21 | **Beeswax candle** (`hom_candle_beeswax`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 22 | **Tallow candle** (`hom_candle_tallow`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 23 | **Flush latrine with running water** (`hom_flush_latrine_simple`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 24 | **Wooden furniture** (`hom_furniture_wooden`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 25 | **Hypocaust underfloor heating** (`hom_hypocaust`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 26 | **Lead and ceramic plumbing** (`hom_lead_plumbing`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 27 | **Locks and keys** (`hom_locks_keys`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 28 | **Mirror, polished bronze** (`hom_mirror_bronze_polished`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 29 | **Musical instruments** (`hom_musical_instruments`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 30 | **Oil lamp, simple** (`hom_oil_lamp_simple`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 31 | **Perfume by enfleurage** (`hom_perfume_enfleurage`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 32 | **Public bath (thermae)** (`hom_public_bath`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 33 | **Pivoting front axle** (`lnd_axle_pivot_front`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 34 | **Bridge** (`lnd_bridge`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 35 | **Litter** (`lnd_litter`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 36 | **Milestone** (`lnd_milestone`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 37 | **Paved trunk road network** (`lnd_paved_road_network`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 38 | **Iron tyre (tire)** (`lnd_tyre_iron`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 39 | **Spoked wheel** (`lnd_wheel_spoked`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 40 | **Alum** (`mat_alum`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 41 | **Asbestos** (`mat_asbestos`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 42 | **Beeswax** (`mat_beeswax`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 43 | **Bitumen and naphtha seeps** (`mat_bitumen`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 44 | **Brass (by cementation)** (`mat_brass`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 45 | **Bronze** (`mat_bronze`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 46 | **Calamine (zinc carbonate/silicate ore)** (`mat_calamine`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 47 | **Carbon black and lampblack** (`mat_carbon_black`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 48 | **Charcoal** (`mat_charcoal`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 49 | **Emery (Naxos)** (`mat_emery`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 50 | **Galena (lead sulfide)** (`mat_galena`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 51 | **Soda-lime glass** (`mat_glass_soda`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 52 | **Gold** (`mat_gold`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 53 | **Gypsum plaster** (`mat_gypsum`) | NO OBVIOUS HARD CONFLICT | Thin |
| 54 | **Lead** (`mat_lead`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 55 | **Leather** (`mat_leather`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 56 | **Quicklime and slaked lime** (`mat_lime`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 57 | **Linen** (`mat_linen`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 58 | **Mercury** (`mat_mercury`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 59 | **Natron (sodium carbonate)** (`mat_natron`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 60 | **Obsidian blade knapping** (`mat_obsidian_blade`) | GOOD | Adequate/good |
| 61 | **Olive oil** (`mat_olive_oil`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 62 | **Pyrolusite (manganese dioxide)** (`mat_pyrolusite`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 63 | **Salt** (`mat_salt`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 64 | **Shellac (traded)** (`mat_shellac`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 65 | **Silk (traded)** (`mat_silk`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 66 | **Silver** (`mat_silver`) | NO OBVIOUS HARD CONFLICT | Thin |
| 67 | **Sulfur** (`mat_sulfur`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 68 | **Tallow** (`mat_tallow`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 69 | **Tin** (`mat_tin`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 70 | **Vitriols (iron and copper sulfates)** (`mat_vitriols`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 71 | **Wrought iron (bloomery)** (`mat_wrought_iron`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 72 | **Cataract couching** (`med_cataract_couching`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 73 | **Legal protection for physicians** (`med_legal_physician`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 74 | **Opium and mandrake tinctures** (`med_opium_mandrake`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 75 | **Good surgical instrument kit** (`med_surgical_kit_good`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 76 | **Trepanation** (`med_trepanation`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 77 | **Wound suturing** (`med_wound_suturing`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 78 | **Burning glass** (`opt_burning_glass`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 79 | **Dioptra (sighting tube)** (`opt_dioptra`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 80 | **Geared mechanical transmission** (`opt_geared_mechanisms`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 81 | **Groma (surveying cross)** (`opt_groma`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 82 | **Polished metal mirror** (`opt_metal_mirror_polished`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 83 | **Steelyard balance** (`opt_steelyards`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 84 | **Sundial** (`opt_sundial`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 85 | **Water clock (clepsydra)** (`opt_water_clock`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 86 | **Water-filled globe as magnifier** (`opt_water_globe_magnifier`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 87 | **Carbon ink** (`prn_carbon_ink`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 88 | **Codex binding** (`prn_codex_bound`) | MIS-SCOPED / VERIFY LOCAL FORM | Thin |
| 89 | **Library and archive** (`prn_library_archive`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 90 | **Mosaic and fresco** (`prn_mosaic_fresco`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 91 | **Papyrus sheets** (`prn_papyrus_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 92 | **Parchment sheets** (`prn_parchment_sheets`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 93 | **Scribal copying** (`prn_scribal_copying`) | MIS-SCOPED / VERIFY LOCAL FORM | Thin |
| 94 | **Sculpture** (`prn_sculpture`) | NO OBVIOUS HARD CONFLICT | Thin |
| 95 | **Seals and stamps** (`prn_seals_stamps`) | MIS-SCOPED / VERIFY LOCAL FORM | Thin |
| 96 | **Theatre and pantomime** (`prn_theatre_pantomime`) | WRONG / FOREIGN / ANACHRONISTIC | Thin |
| 97 | **Wax tablets** (`prn_wax_tablets`) | MIS-SCOPED / VERIFY LOCAL FORM | Thin |
| 98 | **Force pump** (`pwr_force_pump`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 99 | **Screw press** (`pwr_screw_press_power`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 100 | **Anchor** (`sea_anchor`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 101 | **Coastal pilotage** (`sea_coastal_pilotage`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 102 | **Sounding lines** (`sea_sounding_lines`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 103 | **Steering oars** (`sea_steering_oars`) | MIS-SCOPED / VERIFY LOCAL FORM | Adequate/good |
| 104 | **Cotton by trade** (`tex_cotton_trade`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 105 | **Drop spindle** (`tex_drop_spindle`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 106 | **Dyeing with madder root** (`tex_dye_madder`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 107 | **Murex purple dyeing** (`tex_dye_murex`) | WRONG / FOREIGN / ANACHRONISTIC | Assumes term |
| 108 | **Dyeing with woad** (`tex_dye_woad`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 109 | **Felting** (`tex_felting`) | NO OBVIOUS HARD CONFLICT | Adequate/good |
| 110 | **Sailcloth** (`tex_sailcloth`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 111 | **Silk by trade** (`tex_silk_trade`) | WRONG / FOREIGN / ANACHRONISTIC | Thin |
| 112 | **Two-beam loom** (`tex_two_beam_loom`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 113 | **Warp-weighted loom** (`tex_warp_weighted_loom`) | WRONG / FOREIGN / ANACHRONISTIC | Adequate/good |
| 114 | **Wool fiber** (`tex_wool`) | NO OBVIOUS HARD CONFLICT | Adequate/good |

## Immediately startable opening projects — all nodes

`BASELINE CONTAMINATED` means the project is startable because at least one of its direct prerequisites is an inherited node flagged above as wrong/foreign/anachronistic. `GENERIC MISSING GATE` carries over a dependency defect already identified in the Rome audit and is not a judgment that the civilization is “too advanced.”

| # | Project | Cost | Founder h | Hired labour | Floor y | Prereqs | Realism flag | Description |
|---:|---|---:|---:|---|---:|---|---|---|
| 1 | **Chaff cutter** (`ag2_chaff_cutter`) | 499.6 | 50 | 140h smith | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 2 | **Composting** (`ag2_composting`) | 172.5 | 40 | 100h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 3 | **Grafting** (`ag2_grafting`) | 160.0 | 50 | — | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 4 | **Guano** (`ag2_guano`) | 128.8 | 30 | 80h merchant | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 5 | **Hopping** (`ag2_hopping`) | 102.0 | 40 | — | 0.15 | — | GENERIC MISSING GATE | Adequate/good |
| 6 | **Layering** (`ag2_layering`) | 120.0 | 40 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 7 | **Liming** (`ag2_liming`) | 161.9 | 30 | 80h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 8 | **Malting** (`ag2_malting`) | 163.2 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 9 | **Marling** (`ag2_marling`) | 129.3 | 25 | 60h labourer | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 10 | **Oil pressing** (`ag2_oil_pressing`) | 164.3 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 11 | **Potash** (`ag2_potash`) | 172.5 | 40 | 100h labourer | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 12 | **Pyrethrum** (`ag2_pyrethrum`) | 190.4 | 70 | — | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 13 | **Refrigeration - ice trade** (`ag2_refrigeration_ice`) | 190.4 | 70 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 14 | **Terracing** (`ag2_terracing`) | 194.3 | 50 | 150h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 15 | **Compass for navigation** (`air_compass_magnetic`) | 70.2 | 30 | 50h artisan | 0.1 | mat_silk, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 16 | **Kite** (`air_kite_basic`) | 126.2 | 20 | 40h artisan | 0.1 | mat_linen, mat_silk | BASELINE CONTAMINATED | Adequate/good |
| 17 | **Tethered observation balloon** (`air_observation_balloon_tethered`) | 1,231.3 | 120 | 200h artisan | 0.5 | mat_beeswax, mat_linen, mat_silk | BASELINE CONTAMINATED | Adequate/good |
| 18 | **Six months of listening before you act** (`arrival_orientation`) | 480.0 | 900 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 19 | **Roman masonry arch** (`civ_arch_roman`) | 339.7 | 60 | 120h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 20 | **Roman fired brick and tile** (`civ_brick_tile`) | 169.0 | 40 | 80h potter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 21 | **Chorobates: Roman water levelling rod** (`civ_chorobates`) | 99.8 | 25 | 30h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 22 | **Lightning conductor and grounding** (`civ_lightning_conductor`) | 113.6 | 80 | 150h smith | 0.4 | mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 23 | **Groma: Roman X-staff surveying tool** (`civ_surveying_groma`) | 82.6 | 20 | 20h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 24 | **Block and tackle with rope** (`cn_block_tackle_hoist`) | 208.2 | 30 | 60h carpenter | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 25 | **Treadwheel crane** (`cn_crane_treadwheel`) | 418.9 | 55 | 100h carpenter, 80h labourer | 0.7 | cap_power_muscle, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 26 | **Damp proof course barrier layer** (`cn_damp_proof_course`) | 424.8 | 50 | 100h mason | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 27 | **Gypsum plaster finish** (`cn_gypsum_plaster`) | 130.2 | 35 | 80h mason | 0.15 | mat_gypsum | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 28 | **Pile driving by drop hammer** (`cn_pile_driving`) | 416.6 | 40 | 150h labourer | 0.8 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 29 | **Post and lintel structure** (`cn_post_lintel`) | 188.5 | 25 | 50h carpenter, 100h mason | 0.4 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 30 | **Stone quarrying with wedge** (`cn_quarrying_wedge`) | 90.0 | 20 | 100h labourer | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 31 | **Timber scaffolding system** (`cn_scaffolding`) | 496.3 | 50 | 120h carpenter | 0.6 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 32 | **Soil compaction by roller** (`cn_soil_compaction`) | 719.2 | 70 | 120h labourer | 1 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 33 | **Stone polishing and smoothing** (`cn_stone_polish`) | 110.2 | 30 | 80h mason | 0.15 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 34 | **Codebook for optical signal tower** (`com_optical_codebook`) | 64.4 | 100 | 200h scribe | 0.25 | — | GENERIC MISSING GATE | Adequate/good |
| 35 | **Signal flags for maritime communication** (`com_signal_flags`) | 179.7 | 40 | 60h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 36 | **Spring motor (large clockwork)** (`en_spring_motor`) | 8.0 | 80 | — | 0.8 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 37 | **Treadwheel** (`en_treadwheel`) | 30.4 | 20 | 100h carpenter | 0.2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 38 | **Annona grain dole and administration** (`fin_annona`) | 3,232.0 | 600 | 200h scribe | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 39 | **Apprenticeship indenture and training contract** (`fin_apprenticeship`) | 12.8 | 80 | 80h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 40 | **Arbitrage and price equalisation** (`fin_arbitrage`) | 30.0 | 80 | 150h merchant | 1 | fin_market | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 41 | **Deposit bankers (argentarii)** (`fin_argentarii`) | 1,209.6 | 150 | 60h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 42 | **Bankruptcy law and insolvency** (`fin_bankruptcy`) | 32.0 | 120 | 200h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 43 | **Bill of exchange** (`fin_bill_exchange`) | 56.0 | 150 | 200h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 44 | **Bimetallism and fixed exchange** (`fin_bimetallism`) | 42.8 | 100 | 50h master, 150h merchant | 2 | fin_coined_money | BASELINE CONTAMINATED | Adequate/good |
| 45 | **Cartel and market sharing agreement** (`fin_cartel`) | 41.0 | 100 | 200h merchant | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 46 | **Census and population enumeration** (`fin_census`) | 1,688.0 | 200 | 200h merchant, 300h scribe | 2 | fin_government | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 47 | **Professional associations (collegia)** (`fin_collegium`) | 726.4 | 120 | 40h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 48 | **Contract of employment** (`fin_employment_contract`) | 8.0 | 60 | 50h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 49 | **Ferry and toll crossing** (`fin_ferry`) | 4,107.2 | 100 | 100h carpenter, 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 50 | **Gambling house and gaming establishment** (`fin_gambling_house`) | 1,690.0 | 100 | 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 51 | **Hotel and commercial lodging** (`fin_hotel`) | 4,659.2 | 120 | 150h carpenter, 200h merchant | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 52 | **Inn and coaching house** (`fin_inn`) | 2,830.0 | 100 | 150h merchant | 1.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 53 | **Lottery and state gambling** (`fin_lottery`) | 1,664.0 | 150 | 200h merchant, 150h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 54 | **Marine insurance** (`fin_marine_insurance`) | 3,284.0 | 200 | 300h merchant, 150h scribe | 2 | fin_maritime_loan | BASELINE CONTAMINATED | Adequate/good |
| 55 | **Monopoly and exclusive grant** (`fin_monopoly`) | 38.9 | 80 | 150h merchant, 50h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 56 | **Mortgage and real estate credit** (`fin_mortgage`) | 46.0 | 120 | 150h merchant, 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 57 | **Patent and exclusive right** (`fin_patent`) | 47.1 | 140 | 150h merchant, 100h scribe | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 58 | **Pawnshop and secured loan** (`fin_pawnshop`) | 820.0 | 60 | 100h merchant | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 59 | **Plantation and large estate agriculture** (`fin_plantation`) | 8,060.0 | 200 | 300h merchant | 3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 60 | **Postal service as paid business** (`fin_postal_service`) | 5,091.8 | 180 | 200h carpenter, 250h merchant | 2 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 61 | **Seigniorage and debasement** (`fin_seigniorage`) | 20.0 | 80 | 100h merchant | 0.2 | fin_coined_money | BASELINE CONTAMINATED | Adequate/good |
| 62 | **Partnership (societas)** (`fin_societas`) | 243.2 | 40 | 20h scribe | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 63 | **Tariff and import duty** (`fin_tariff`) | 38.0 | 100 | 150h merchant, 50h scribe | 2 | fin_tax_farming | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 64 | **Trademark and mark of quality** (`fin_trademark`) | 16.0 | 80 | 100h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 65 | **Trading post and remote store** (`fin_trading_post`) | 1,330.0 | 100 | 150h merchant | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 66 | **Usury law and interest regulation** (`fin_usury_law`) | 24.0 | 100 | 150h scribe | 1 | fin_contract_law | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 67 | **Large-scale fish curing and smoking** (`fud_fish_curing_and_smoking`) | 246.8 | 120 | 200h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 68 | **Hay making and dry storage** (`fud_hay_making_storage`) | 234.7 | 100 | 300h labourer | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 69 | **Button with eyelet** (`hom_button`) | 25.2 | 40 | 60h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 70 | **Roman cosmetics** (`hom_cosmetics_roman`) | 64.0 | 20 | — | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 71 | **Eraser, breadcrumb substitute** (`hom_eraser_breadcrumb`) | 4.0 | 30 | — | 0.1 | — | GENERIC MISSING GATE | Adequate/good |
| 72 | **Fireplace and chimney** (`hom_fireplace_chimney`) | 217.2 | 120 | 80h carpenter, 200h mason | 1 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 73 | **Flush toilet with S-bend water trap** (`hom_flush_toilet_trap`) | 183.1 | 80 | 80h artisan, 100h plumber | 0.5 | hom_flush_latrine_simple | BASELINE CONTAMINATED | Adequate/good |
| 74 | **Latrine water trap (S-bend)** (`hom_latrine_water_trap`) | 135.1 | 60 | 100h artisan, 80h plumber | 0.5 | hom_flush_latrine_simple | BASELINE CONTAMINATED | Adequate/good |
| 75 | **Mangle and wringer** (`hom_mangle_wringer`) | 133.4 | 100 | 120h artisan, 80h carpenter | 0.75 | cap_tol_1mm, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 76 | **Ceiling punkah, servant-pulled** (`hom_punkah_ceiling`) | 66.4 | 50 | 80h carpenter | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 77 | **Safety pin** (`hom_safety_pin`) | 19.3 | 40 | 50h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 78 | **Sprung mattress** (`hom_sprung_mattress`) | 228.4 | 120 | 150h artisan, 100h carpenter | 1 | cap_tol_1mm, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 79 | **Toothbrush** (`hom_toothbrush`) | 24.2 | 60 | 100h artisan | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 80 | **Toys and dolls** (`hom_toys_dolls`) | 60.4 | 60 | 60h artisan, 80h carpenter | 0.5 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 81 | **Umbrella** (`hom_umbrella`) | 71.8 | 80 | 60h artisan, 100h carpenter | 0.5 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 82 | **Establish a respectable cover identity** (`identity_cover`) | 1,264.0 | 500 | 400h scribe | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 83 | **Hobby horse (pedal-less bicycle)** (`lnd_hobby_horse`) | 434.8 | 40 | 100h carpenter, 60h smith | 0.5 | lnd_wheel_spoked | BASELINE CONTAMINATED | Adequate/good |
| 84 | **Wheelbarrow** (`lnd_wheelbarrow`) | 190.8 | 30 | 80h carpenter, 30h smith | 0.5 | lnd_wheel_spoked | BASELINE CONTAMINATED | Adequate/good |
| 85 | **Papyrus** (`mat_papyrus`) | 280.8 | 20 | 60h scribe | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 86 | **Parchment** (`mat_parchment`) | 374.4 | 30 | 80h scribe | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 87 | **Plaster cast immobilization** (`md2_plaster_cast`) | 174.4 | 100 | 120h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 88 | **Vector control** (`md2_vector_control`) | 228.2 | 100 | 120h scholar | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 89 | **Amputation and prosthetics** (`med_amputation`) | 9.9 | 0 | 50h artisan | 0 | med_surgical_kit_good | BASELINE CONTAMINATED | Adequate/good |
| 90 | **Bone setting** (`med_bone_setting`) | 7.4 | 0 | 50h artisan | 0.5 | med_surgical_kit_good | BASELINE CONTAMINATED | Adequate/good |
| 91 | **Herbal pharmacy (Dioscorides Materia medica)** (`med_herbal_pharmacy`) | 464.0 | 100 | 200h scholar | 0.5 | mat_olive_oil | BASELINE CONTAMINATED | Adequate/good |
| 92 | **Obstetric practice** (`med_obstetric_practice`) | 15.0 | 0 | 100h artisan | 0 | mat_linen | BASELINE CONTAMINATED | Adequate/good |
| 93 | **Surgical gloves and mask** (`med_surgical_gloves_mask`) | 173.4 | 40 | 100h artisan | 0 | mat_linen | BASELINE CONTAMINATED | Adequate/good |
| 94 | **Bloomery smelting of bog iron** (`met_bloomery_bog_iron`) | 2,004.4 | 100 | 2500h furnaceman, 2000h labourer | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 95 | **Investment casting and lost wax** (`met_investment_casting`) | 395.8 | 100 | 140h artisan | 0.8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 96 | **Ore dressing: crushing and hand sorting** (`met_ore_crushing_sorting`) | 80.5 | 20 | 400h labourer | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 97 | **Adhesive bonding** (`mfg_adhesive_bond`) | 175.6 | 140 | 120h artisan | 0.3 | mat_bitumen | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 98 | **Cold riveting** (`mfg_cold_riveting`) | 178.4 | 100 | 120h artisan | 0.2 | mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 99 | **Enamelling** (`mfg_enamelling`) | 173.4 | 120 | 140h furnaceman | 0.3 | cap_heat_0700, mat_glass_soda | BASELINE CONTAMINATED | Adequate/good |
| 100 | **Flux** (`mfg_flux`) | 167.2 | 60 | 60h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 101 | **Hot riveting** (`mfg_hot_riveting`) | 176.0 | 80 | 100h artisan | 0.2 | mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 102 | **Japanning** (`mfg_japanning`) | 175.6 | 110 | 130h artisan | 0.25 | mat_shellac | BASELINE CONTAMINATED | Adequate/good |
| 103 | **Casting mould** (`mfg_mould`) | 178.0 | 120 | 150h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 104 | **Painting** (`mfg_painting`) | 180.0 | 80 | 100h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 105 | **Production schedule** (`mfg_production_schedule`) | 184.0 | 130 | — | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 106 | **Silver soldering** (`mfg_silver_solder`) | 684.9 | 100 | 120h smith | 0.25 | cap_heat_0700, mat_silver | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 107 | **Soft soldering** (`mfg_soft_solder`) | 189.2 | 80 | 100h artisan | 0.2 | mat_lead | BASELINE CONTAMINATED | Adequate/good |
| 108 | **Amalgamation: extracting precious metals with mercury** (`mt2_amalgamation`) | 5,036.8 | 80 | 300h master | 0.5 | mat_mercury | BASELINE CONTAMINATED | Adequate/good |
| 109 | **Earthenware: low-fired, porous ceramic for everyday use** (`mt2_earthenware`) | 184.0 | 60 | 200h potter | 0.5 | cap_heat_0700 | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 110 | **Pelletising: forming ore fines into uniform balls** (`mt2_pelletising`) | 178.8 | 110 | 300h labourer | 0.8 | cap_tol_1mm | GENERIC MISSING GATE | Adequate/good |
| 111 | **Solder: lead-tin for joining metals by melting** (`mt2_solder_lead_tin`) | 7,809.4 | 100 | 250h smith | 0.5 | cap_heat_0700, mat_lead, mat_tin | BASELINE CONTAMINATED | Adequate/good |
| 112 | **Timbering: wooden support structures for mine stability** (`mt2_timbering_safety`) | 242.9 | 80 | 300h carpenter | 0.8 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 113 | **Type metal: lead-tin-antimony for printing type castings** (`mt2_type_metal`) | 2,599.8 | 110 | 300h furnaceman | 0.8 | mat_lead, mat_tin | BASELINE CONTAMINATED | Adequate/good |
| 114 | **Anemometer (wind speed)** (`opt_anemometer`) | 269.8 | 60 | 100h artisan, 40h carpenter, 60h smith | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 115 | **Manometer (pressure measurement)** (`opt_manometer`) | 252.7 | 60 | 60h artisan, 80h glassblower | 0.1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 116 | **Mandrel and self-centering chuck** (`prc_mandrel_chuck`) | 119.9 | 60 | 80h artisan, 120h smith | 0.25 | cap_tol_1mm, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 117 | **Straightedge and reference straightness** (`prc_straightedge`) | 65.4 | 30 | 80h artisan, 60h smith | 0.2 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 118 | **Tailstock and dead centre** (`prc_tailstock_deadcentre`) | 125.2 | 50 | 100h artisan, 60h smith | 0.2 | cap_tol_1mm, mat_wrought_iron | BASELINE CONTAMINATED | Adequate/good |
| 119 | **Wire mould and deckle** (`prn_wire_mould_deckle`) | 174.0 | 150 | 200h artisan, 250h smith | 1 | cap_tol_1mm, mat_brass | BASELINE CONTAMINATED | Adequate/good |
| 120 | **Coal seam and mining** (`pwr_coal_seam`) | 295.3 | 150 | 300h labourer, 400h miner | 1 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 121 | **Oil shale and bitumen deposits** (`pwr_oil_shale`) | 43.7 | 80 | 100h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 122 | **Peat extraction and burning** (`pwr_peat`) | 62.1 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 123 | **Petroleum seeps and collection** (`pwr_petroleum_seeps`) | 110.4 | 100 | 200h labourer | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 124 | **Citation and bibliographic reference** (`sc2_institution_citation`) | 208.8 | 80 | 160h scribe | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 125 | **Curriculum and course sequence** (`sc2_institution_curriculum`) | 176.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 126 | **Doctorate and research degree** (`sc2_institution_doctorate`) | 180.0 | 150 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 127 | **Examination and credentialing** (`sc2_institution_examination`) | 288.0 | 80 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 128 | **Funded research programme** (`sc2_institution_funded_programme`) | 180.0 | 120 | — | 5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 129 | **Referee and peer review** (`sc2_institution_referee`) | 180.0 | 100 | — | 8 | — | GENERIC MISSING GATE | Adequate/good |
| 130 | **Research group and principal investigator** (`sc2_institution_research_group`) | 180.0 | 100 | — | 5 | — | GENERIC MISSING GATE | Adequate/good |
| 131 | **Textbook and codified knowledge** (`sc2_institution_textbook`) | 880.0 | 200 | 400h scholar, 200h scribe | 8 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 132 | **Newton's three laws of motion** (`sc2_physics_newtons_laws`) | 188.8 | 100 | 180h scribe | 4 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 133 | **Controlled experiment, hypothesis, replication, publication** (`scientific_method`) | 160.0 | 350 | 500h scribe | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 134 | **Cross-staff for latitude** (`sea_cross_staff`) | 336.3 | 80 | 150h artisan, 100h scholar | 0.25 | cap_tol_1mm | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 135 | **Diving bell** (`sea_diving_bell`) | 774.8 | 120 | 300h carpenter, 100h smith | 0.4 | sea_anchor | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 136 | **Deep keel and the ability to sail to windward** (`sea_keel_deep`) | 1,361.6 | 100 | 3000h carpenter | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 137 | **Lead sheathing against shipworm** (`sea_lead_sheathing`) | 1,564.0 | 0 | — | 0 | mat_lead | BASELINE CONTAMINATED | Adequate/good |
| 138 | **Lodestone knowledge** (`sea_lodestone`) | 121.4 | 20 | 80h scholar | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 139 | **Log line for speed** (`sea_log_line`) | 53.7 | 30 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 140 | **Pharos lighthouse** (`sea_pharos_lighthouse`) | 0.0 | 0 | — | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 141 | **Sternpost rudder** (`sea_sternpost_rudder`) | 462.6 | 120 | 200h carpenter, 100h smith | 0.5 | cap_tol_1mm, sea_steering_oars | GENERIC MISSING GATE | Adequate/good |
| 142 | **Field bleaching with sun** (`tex_field_bleaching`) | 160.2 | 50 | 300h labourer | 2 | mat_linen, tex_sailcloth | BASELINE CONTAMINATED | Adequate/good |
| 143 | **Hand ginning cotton** (`tex_hand_ginning`) | 46.8 | 30 | 200h labourer | 0.2 | tex_cotton_trade | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 144 | **Horizontal loom** (`tex_horizontal_loom`) | 151.2 | 80 | 100h artisan, 200h carpenter | 0.5 | cap_tol_1mm, tex_two_beam_loom | BASELINE CONTAMINATED | Adequate/good |
| 145 | **Indigo dyeing** (`tex_indigo`) | 125.8 | 60 | 140h artisan | 0.4 | mat_natron, tex_dye_woad | BASELINE CONTAMINATED | Adequate/good |
| 146 | **Mordanting dyes with alum** (`tex_mordanting`) | 86.6 | 40 | 100h artisan | 0.3 | mat_alum, tex_dye_madder | BASELINE CONTAMINATED | Adequate/good |
| 147 | **Vegetable tanning of leather** (`tex_vegetable_tanning`) | 621.6 | 100 | 250h artisan, 200h labourer | 1.2 | mat_leather | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 148 | **Bilge pump** (`tr_bilge_pump`) | 347.6 | 50 | 150h carpenter, 100h smith | 0.3 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 149 | **Block and tackle pulley** (`tr_block_tackle`) | 243.1 | 40 | 150h carpenter, 50h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 150 | **Reefing sails** (`tr_reefing`) | 211.6 | 50 | 300h sailor | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 151 | **Block rigging and rope lashing** (`tr_rigging_block_lashing`) | 160.0 | 60 | — | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 152 | **Semaphore signal** (`tr_semaphore_signal`) | 233.9 | 40 | 100h carpenter, 100h smith | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 153 | **Sleeper and ballast foundation** (`tr_sleeper_ballast`) | 235.9 | 30 | 150h carpenter, 400h labourer | 1 | — | GENERIC MISSING GATE | Adequate/good |
| 154 | **Square rig sails** (`tr_square_rig`) | 1,012.0 | 40 | — | 0.6 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 155 | **Wooden waggonway** (`tr_wooden_waggonway`) | 216.4 | 40 | 200h carpenter | 2 | cap_power_muscle | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 156 | **Alum tanning: mineral salt curing** (`tx2_alum_tanning`) | 608.0 | 60 | 80h artisan | 0.4 | mat_alum | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 157 | **Asbestos cloth: fire-resistant fabric** (`tx2_asbestos_cloth`) | 1,301.8 | 80 | 100h artisan | 1 | mat_asbestos | BASELINE CONTAMINATED | Adequate/good |
| 158 | **Beam: warp holder and tension** (`tx2_beam`) | 7.9 | 40 | 60h carpenter | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 159 | **Bleaching by sunlight: oxidative whitening** (`tx2_bleaching_sun`) | 4.8 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 160 | **Bottle: glass container** (`tx2_bottle`) | 905.6 | 60 | 100h glassblower | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 161 | **Button: bone material** (`tx2_button_bone`) | 8.1 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 162 | **Button: horn material** (`tx2_button_horn`) | 8.0 | 40 | 60h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 163 | **Button: shell material** (`tx2_button_shell`) | 9.2 | 50 | 70h artisan | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 164 | **Carding: opening and aligning fibres** (`tx2_carding`) | 86.3 | 60 | 150h artisan | 0.2 | cap_tol_1mm, tex_wool | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 165 | **Cashmere: goat undercoat fibre** (`tx2_cashmere`) | 8.4 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 166 | **Comb: hair grooming tool** (`tx2_comb`) | 10.4 | 50 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 167 | **Corset: rigid body support garment** (`tx2_corset`) | 24.0 | 100 | 200h artisan | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 168 | **Cotton gin: separation of seed from fibre** (`tx2_cotton_ginning`) | 25.4 | 120 | 80h carpenter, 60h smith | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 169 | **Yarn count standardisation** (`tx2_count_standard`) | 4.8 | 40 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 170 | **Currying: leather finish dressing** (`tx2_currying`) | 12.0 | 60 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 171 | **Cutting table: stacked cloth cutting** (`tx2_cutting_table`) | 11.2 | 60 | 80h carpenter | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 172 | **Doll: articulated child plaything** (`tx2_doll`) | 66.8 | 80 | 150h artisan | 1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 173 | **Drawing pin: short fastening point** (`tx2_drawing_pin`) | 22.9 | 50 | 70h smith | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 174 | **Dyeing in fibre: pre-spin colouration** (`tx2_dyeing_fibre`) | 572.0 | 60 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 175 | **Dyeing in garment: finished good colouration** (`tx2_dyeing_garment`) | 579.2 | 90 | 160h artisan | 1 | tex_dye_madder | BASELINE CONTAMINATED | Adequate/good |
| 176 | **Dyeing in piece: woven cloth colouration** (`tx2_dyeing_piece`) | 576.8 | 80 | 140h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 177 | **Dyeing in yarn: skein colouration** (`tx2_dyeing_yarn`) | 574.4 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 178 | **Eye-pointed needle: self-threading sewing** (`tx2_eye_pointed_needle`) | 91.0 | 50 | 60h smith | 0.15 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 179 | **Flax cultivation and fibre** (`tx2_flax_fibre`) | 7.2 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 180 | **Flyer: the earliest spinning frame component** (`tx2_flyer`) | 22.3 | 70 | 40h carpenter, 80h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 181 | **Fulling: cloth densification** (`tx2_fulling`) | 569.7 | 60 | 80h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 182 | **Heddle: warp thread carrier and riser** (`tx2_heddle`) | 7.6 | 40 | 50h artisan | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 183 | **Hemp cultivation and fibre** (`tx2_hemp_fibre`) | 7.2 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 184 | **Hook and eye: wire fastener** (`tx2_hook_and_eye`) | 15.8 | 50 | 60h smith | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 185 | **Jute cultivation and fibre** (`tx2_jute_fibre`) | 8.4 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 186 | **Mirror: reflective glass surface** (`tx2_mirror`) | 252.8 | 70 | 100h artisan | 0.3 | mat_glass_soda | BASELINE CONTAMINATED | Adequate/good |
| 187 | **Mohair: angora goat fibre** (`tx2_mohair`) | 8.4 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 188 | **Needle: sewing implement** (`tx2_needle`) | 89.4 | 40 | 60h smith | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 189 | **Paperclip: bent wire fastener** (`tx2_paperclip`) | 13.3 | 50 | 70h smith | 0.5 | — | GENERIC MISSING GATE | Adequate/good |
| 190 | **Pattern grading: multi-size scaling** (`tx2_pattern_grading`) | 44.0 | 80 | 120h artisan | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 191 | **Pin: sewing fastener** (`tx2_pin`) | 9.4 | 40 | 60h smith | 0.1 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 192 | **Press stud: snap fastener** (`tx2_press_stud`) | 75.2 | 80 | 100h smith | 1 | mat_brass | BASELINE CONTAMINATED | Adequate/good |
| 193 | **Block printing: carved design application** (`tx2_printing_block`) | 44.1 | 100 | 200h artisan, 80h engraver | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 194 | **Ramie cultivation and fibre** (`tx2_ramie_fibre`) | 8.4 | 50 | 70h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 195 | **Resist dyeing: pattern preservation** (`tx2_resist_dyeing`) | 586.4 | 70 | 120h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 196 | **Retting of flax and hemp fibres** (`tx2_retting`) | 4.8 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Assumes term |
| 197 | **Rope laying: strand twisting** (`tx2_rope_lay`) | 7.2 | 40 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 198 | **Scouring: removal of grease and soil** (`tx2_scouring`) | 568.4 | 40 | 60h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 199 | **Selvedge: woven cloth edge** (`tx2_selvedge`) | 6.0 | 40 | 50h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Assumes term |
| 200 | **Shed: warp separation for pick insertion** (`tx2_shed`) | 4.8 | 30 | 40h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 201 | **Silk: cultivated fibre** (`tx2_silk_fibre`) | 247.2 | 40 | 60h artisan | 0 | — | GENERIC MISSING GATE | Adequate/good |
| 202 | **Singeing: flame removal of nap** (`tx2_singeing`) | 889.7 | 60 | 80h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 203 | **Sizing systems: body measurement standardisation** (`tx2_sizing_systems`) | 14.4 | 100 | 120h artisan | 2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 204 | **Spectacle frame: eye support structure** (`tx2_spectacle_frame`) | 24.8 | 60 | 100h artisan | 0.2 | — | GENERIC MISSING GATE | Adequate/good |
| 205 | **Splitting: leather layering** (`tx2_splitting`) | 12.8 | 70 | 100h artisan | 0.3 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 206 | **Twist insertion control** (`tx2_twist_insertion`) | 7.2 | 50 | 60h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 207 | **Warp sizing: fibre stiffening** (`tx2_warp_sizing`) | 7.2 | 50 | 60h artisan | 0.2 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 208 | **Warping mill: warp thread length setting** (`tx2_warping_mill`) | 16.8 | 60 | 80h carpenter | 0.25 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 209 | **Watch case: portable timepiece housing** (`tx2_watch_case`) | 13,931.7 | 80 | 60h engraver, 120h smith | 0.3 | — | GENERIC MISSING GATE | Adequate/good |
| 210 | **Wool: sheep fibre** (`tx2_wool_fibre`) | 7.6 | 40 | 50h artisan | 0 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |
| 211 | **Define and publish standard length, mass, time and temperature** (`units_standards`) | 355.2 | 300 | 200h carpenter, 400h smith | 0.5 | — | PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK | Adequate/good |

### Opening-project triage counts

- **PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK: 148**
- **BASELINE CONTAMINATED: 40**
- **GENERIC MISSING GATE: 23**

### Highest-confidence fixes

- Rebuild the ambient layer for Mesoamerica. This start cannot be meaningfully realism-audited downstream while Old World iron, wheels, glass, plumbing, coinage and Mediterranean materials are silently granted.
- Keep the five explicit Mexica seeds; they are sensible.
- Split `cap_power_muscle`: human power is universal, animal traction is not. The current capability name smuggles draught-animal power into a civilization explicitly defined as lacking it.
- Resource nodes must be geography-aware. Olive oil, linen, silk, shellac, natron and Mediterranean dyes should not exist in the opening inventory merely because they are tier-0 elsewhere.
- Once the inherited state is corrected, regenerate the 211 startable projects; many currently visible projects will disappear or acquire the correct prerequisite path automatically.

# Bottom line

The non-Roman starts are **not yet reliable alternate historical baselines**. Their hand-written identity files are often decent—especially Norse and Mexica—but the universal ambient grant mechanism overwhelms those identities. Fixing country-specific inherited knowledge/resources is higher priority than tuning individual project prices, because it changes what is legal to research at all. After that fix, rerun the same opening audit; otherwise a large fraction of “project balance” conclusions are measuring prerequisites the civilization should never have possessed.


---
