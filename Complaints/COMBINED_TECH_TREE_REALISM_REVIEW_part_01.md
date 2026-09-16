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
