# Tech tree coverage audit vs. published strategy games

Target tree: `/home/user/test/rome/data/tech_tree.json` (2,833 nodes, goal `point_contact_transistor`).
Premise: one modern person dropped into a pre-industrial society, with modern technical *knowledge* but none of
the industrial base, trying to bootstrap a working point-contact transistor from stone-age/ancient starting
conditions. Matching is by MEANING, not name — a Civ tech can land on a differently-named node here, or on
several nodes, or on none.

Status: COMPLETE.

---

## Source 1: Civilization V (with Brave New World) — 74 techs, checked 74/74

List taken from CivFanatics' tech list and cross-checked against the Civilization Wiki Civ5 tech page (both agree on all 74 entries, Ancient through Future era). Sources: https://civfanatics.com/civ5/info/techs/ , https://civilization.fandom.com/wiki/List_of_technologies_in_Civ5

Key context: the tree starts in **Rome, 100 AD** (`meta.start_year`), and its 268 root nodes (no prerequisites) are already full of Roman-era craft (`civ_arch_roman`, `fin_coined_money`, `cap_heat_1100` hand-blown bronze, etc). So every Civ V "Ancient Era" tech that describes a Bronze/early-Iron-Age starting capability is not a gap — it is the campaign's *pre-game given*, deliberately out of the tree because the player-character is dropped into a society that already has it.

| Civ V tech (era) | Verdict | Matched node(s) / reasoning |
|---|---|---|
| Agriculture (Anc) | Baseline, out of scope | Roman agriculture assumed at start; tree's `crop_rotation`, `fud_*`, `ag2_*` are *improvements* on this baseline, not the baseline itself |
| Pottery (Anc) | Baseline, out of scope | `cap_heat_0700` ("pottery kiln") appears only as a capability rung; firing clay itself is assumed |
| Animal Husbandry (Anc) | Baseline, out of scope | Domestication assumed; tree picks up at breeding/selection (`ag2_progeny_testing`, `crop_rotation`) |
| Archery (Anc) | Baseline/out of scope | Not on any path to a transistor; bows are pre-existing Roman military kit |
| Mining (Anc) | Baseline, out of scope | Basic mining assumed; `mining`(28) and `met_*` cover deep/advanced mining |
| Sailing (Anc) | Baseline, out of scope | Basic rigging assumed; `marine`(50), `ships`(20), `navigation`(19) cover everything beyond it |
| Calendar (Anc) | Baseline, out of scope | Roman calendar assumed |
| Writing (Anc) | Baseline, out of scope | Roman literacy assumed; tree covers writing *instruments* (`if_iron_gall_ink`, `if_fountain_pen`) as later refinements |
| Trapping (Anc) | Out of scope | Not on any path to the goal |
| The Wheel (Anc) | Baseline, out of scope | Carts assumed; `transport`(59) and `rail`(46) cover everything past it |
| Masonry (Anc) | Baseline, out of scope | `civ_arch_roman`, `civ_monumental_stone` are roots — Roman masonry is starting competence |
| Bronze Working (Anc) | Baseline, out of scope | Bronze and iron already in Roman hands; tree starts at `met_bloomery_bog_iron`/`cementation_steel` |
| Optics (Cla) | Match | `optics`(56 nodes), `glass_optics`(10), `camera_obscura` |
| Philosophy (Cla) | Match (loose) | Greek philosophy assumed present; formal scientific method covered later by `sc2_method_*`(24), `laboratory`(28) |
| Horseback Riding (Cla) | Baseline, out of scope | — |
| Mathematics (Cla) | Match | `mathematics`(7), `algebra`(21), `geometry`(7), `notation`(14) — far deeper than Civ's single node |
| Construction (Cla) | Match | `civ_arch_roman`, `structures`(16), `foundations`(12) |
| Iron Working (Cla) | Baseline, out of scope | Rome already has iron; tree begins at refinement (`cementation_steel`) |
| Theology (Med) | **Reject** | No equivalent anywhere; religion appears only as political *obstacle* text in node notes (e.g. state suspicion of associations), never as a researchable node — correctly out of scope for a technology-bootstrapping premise |
| Civil Service (Med) | Match | `fin_government`, `fin_civil_service_exam` |
| Currency (Med) | Match | `fin_coined_money`, `fin_bimetallism`, `fin_paper_money` |
| Engineering (Med) | Match | `foundations`(12), `structures`(16), `civ_*` cluster |
| Metal Casting (Med) | Match | `blast_furnace`, `cap_heat_1300`, `metallurgy`(17) |
| Compass (Med) | Match | `air_compass_magnetic`, `in2_magnetometer_compass`, `in2_gyrocompass` |
| Education (Med) | Match | `fin_university`, `institution`(39), `sc2_institution_curriculum` |
| Chivalry (Med) | **Reject** | No equivalent; mounted-knight military doctrine is irrelevant to the premise |
| Machinery (Med) | Match | `machine_tools`(34), `tooling`(16) |
| Physics (Med) | Match | `physics`(38) |
| Steel (Med) | Match | `cementation_steel`, `crucible_steel`, `mat_blister_steel` |
| Astronomy (Ren) | Match | `in2_cassegrain_reflector` (telescope), `sea_astronomical_tables` |
| Acoustics (Ren) | Match | `sc2_physics_acoustics`, `sc2_physics_wave_motion`, `sound`(15) |
| Banking (Ren) | Match | `banking`(6), `fin_central_bank`, `credit`(8) |
| Printing Press (Ren) | Match | `printing_press`, `if_movable_type` |
| Gunpowder (Ren) | Match | `chm_black_powder`, `gunpowder` |
| Navigation (Ren) | Match | `navigation`(19), `expedition`(12) |
| Economics (Ren) | Match (diffuse) | No single "economics" node, but `commerce`(16)+`credit`(8)+`banking`(6)+`law`(14)+`institution`(39) cover the practical content far more thoroughly than Civ's one node |
| Chemistry (Ren) | Match | `chemistry`(15), `chemical_engineering`(36) |
| Metallurgy (Ren) | Match | `metallurgy`(17), `alloys`(31), `heat_treatment`(18) |
| Archaeology (Ren) | **Reject** | Civ game-mechanic tech (unlocks antiquity sites/Great Works); no real-world equivalent needed for the premise |
| Scientific Theory (Ren) | Match | `sc2_method_hypothesis`, `method`(24), `laboratory`(28) — this whole cluster is one of the tree's deepest |
| Military Science (Ren) | Match | `mil_war_college`, `mil_general_staff`, `mil_operational_research` |
| Fertilizer (Ren) | Match | `chm_superphosphate`, `chm_haber_bosch`, `fud_haber_process_synthetic_nitrogen` |
| Rifling (Ren) | Match | `mil_rifling`, `mil_minie_ball` |
| Biology (Ind) | Match | `md2_cell_theory`, `md2_dna`, `md2_gene`, `md2_chromosome`, `md2_mendelian_inheritance` |
| Steam Power (Ind) | Match | `steam_prime`(7), `steam_auxiliary`(15), `steam_boiler`(8) |
| Electricity (Ind) | Match | `electrical`(21), `crude_cell`, `galvanometer`, `motor_transformer_ac` |
| Replaceable Parts (Ind) | Match | `interchangeable_parts`, `cap_tol_10um` |
| Railroad (Ind) | Match | `rail`(46 nodes — the tree's 4th-largest category) |
| Dynamite (Ind) | Match | `chm_dynamite`, `met_dynamite_blasting` |
| Refrigeration (Ind) | Match | `refrigeration`(5), `fud_freezing_with_mechanical_cold` |
| Telegraph (Ind) | Match | `com_morse_code`, `com_duplex_telegraph`, `telegraphy`(4) |
| Radio (Ind) | Match | `radio`(20) |
| Flight (Ind) | Match | `aviation`(44) |
| Combustion (Ind) | Match | `ic_prime`(4), `ic_auxiliary`(5), `motor_subsystems`(37) |
| Plastics (Mod) | Match | `polymer`(14) |
| Penicillin (Mod) | Match | `md2_penicillin_fermentation`, `md2_penicillin_production`, `md2_penicillin_freeze_dry` |
| Electronics (Mod) | Match | `electronics`(19), `circuit_concept`(20), `component`(22) — this is the goal node's own neighbourhood |
| Mass Media (Mod) | Match | `com_broadcasting_institution`, `radio` |
| Radar (Mod) | Match | `radar`(2), `com_radar_magnetron`, `el2_radar_pulse_modulation_detection` |
| Atomic Theory (Mod) | Match | `atomic_theory` node directly, plus `sc2_physics_quantum_photon`, `quantum_solidstate_theory` |
| Ecology (Mod) | **Reject** | No equivalent; ecosystem science plays no role in bootstrapping a transistor |
| Computers (Mod) | Match | `com_analytical_engine`, `com_accumulator`, `com_binary_arithmetic`, `com_boolean_algebra` (mechanical/relay computing; full stored-program computing is a tier-5 side branch past the goal, appropriately) |
| Rocketry (Mod) | Match (partial, correctly limited) | `en_rocket_motor`, `mil_ballistic_rocket` — WWII V2-level only, which is all the premise needs |
| Lasers (Mod) | **Reject (by design)** | Laser (1960) postdates the point-contact transistor (1947); the tree's endpoint is the goal node, so absence is correct, not a gap |
| Nuclear Fission (Mod) | **Reject** | A reactor/bomb programme is an entire separate industrial undertaking orders of magnitude larger than one transistor; irrelevant to the premise despite being chronologically earlier |
| Globalization (Mod) | **Reject** | Civ diplomacy/policy balance tech, no real-world equivalent needed |
| Robotics (Mod) | **Reject** | Far beyond the goal |
| Satellites (Mod) | **Reject** | Far beyond the goal (post-1957) |
| Stealth (Mod) | **Reject** | Far beyond the goal, military balance |
| Advanced Ballistics (Mod) | **Reject** | Military balance tech, irrelevant |
| Particle Physics (Fut) | **Reject** | Post-goal, Civ "Future Era" catch-all |
| Nuclear Fusion (Fut) | **Reject** | Post-goal |
| Nanotechnology (Fut) | **Reject** | Post-goal |
| Future Tech (Fut) | **Reject** | Placeholder repeatable tech, not a real technology |

**Civ V summary:** of 74 techs, 0 produced a genuine gap. Every "no equivalent" case is either (a) a pre-game Roman-baseline given, (b) a Civ balance/social tech with no real-world engineering content, or (c) chronologically/thematically beyond the transistor goal. This is expected — Civ V's tree is ~35x smaller and built for whole-civilization balance, not one artisan's build order.

## Source 2: Civilization IV (Beyond the Sword) — 92 techs, checked 92/92

List from CivFanatics' Civilopedia technologies page (alphabetical listing of all 92 BtS techs): https://civfanatics.com/civ4/civilopedia/technologies/

64 of the 92 overlap in meaning with Civ V entries already tabled above and get the same verdict (Agriculture, Alphabet≈Writing-baseline, Animal Husbandry, Archery, Astronomy, Banking, Biology, Bronze Working, Calendar, Chemistry, Civil Service, Combustion, Compass, Computers, Construction, Currency, Ecology→reject, Economics, Education, Electricity, Engineering, Feudalism/Chivalry-type→reject, Fishing→baseline reject, Flight, Fusion→reject beyond scope, Gunpowder, Horseback Riding, Hunting→baseline reject, Iron Working, Machinery, Masonry, Mass Media, Mathematics, Medicine, Metal Casting, Military Science, Mining, Optics, Philosophy, Physics, Plastics, Pottery, Printing Press, Railroad, Refrigeration, Replaceable Parts, Rifling, Robotics→reject, Rocketry, Sailing, Satellites→reject, Scientific Method, Stealth→reject, Steam Power, Steel, Theology→reject, The Wheel, Writing, Fission→reject, Laser→reject by design, Radio, Radar-not present in IV). Only the genuinely new names are tabled below.

| Civ IV tech (new vs. Civ V list) | Verdict | Matched node(s) / reasoning |
|---|---|---|
| Artillery | Match | `mil_artillery_piece`, `mil_artillery_carriage`, `mil_artillery_shell` — present in the large `weapons`(47) category |
| Assembly Line | Match | `lnd_assembly_line`: "Assembly line and mass production" |
| Code of Laws | Match (loose) | `fin_contract_law`, `law`(14) category — Rome's actual legal code is baseline, but the tree's specific legal *institutions* are covered |
| Communism | **Reject** | Political-economic ideology, no technological content, irrelevant to premise |
| Composites | **Reject (beyond scope)** | Modern carbon-fibre/composite materials (1960s+) postdate the transistor goal; no node, correctly absent |
| Constitution | **Reject** | Political-system tech, irrelevant |
| Corporation | Match | `fin_joint_stock`: "Joint-stock company with permanent existence" |
| Democracy | **Reject** | Political-system tech, irrelevant |
| Divine Right | **Reject** | Religious-political tech, irrelevant |
| Drama | **Reject** | Culture/Great Works tech, irrelevant |
| Fiber Optics | **Reject (beyond scope)** | Postdates the transistor by decades; no node, correctly absent |
| Genetics | Match | `md2_dna`, `md2_mendelian_inheritance`, `md2_chromosome`, `md2_gene` |
| Guilds | Match | `fin_guild`: "Guild and monopoly craft" |
| Industrialism | Match | `mfg_*` organisation cluster (`mfg_production_schedule`, `mfg_standard_hour`, `mfg_time_study`, `interchangeable_parts`) |
| Liberalism | **Reject** | Political ideology tech, irrelevant |
| Literature | **Reject** | Culture/Great Works tech; no equivalent and none needed |
| Meditation | **Reject** | Religious tech, irrelevant |
| Military Tradition | **Reject** | Political-military doctrine tech, irrelevant |
| Monarchy | **Reject** | Political-system tech, irrelevant |
| Monotheism | **Reject** | Religious tech, irrelevant |
| Music | Match | `hom_musical_instruments`, `hom_piano` (present as consumer-goods flavour, not a research goal) |
| Mysticism | **Reject** | Religious tech, irrelevant |
| Nationalism | **Reject** | Political-ideology tech, irrelevant |
| Paper | Match | `rag_paper`, `mat_paper`, `prn_hand_papermaking`, `prn_fourdrinier_machine` |
| Polytheism | **Reject** | Religious tech, irrelevant |
| Priesthood | **Reject** | Religious-institutional tech, irrelevant |
| Superconductors | **Reject (beyond scope)** | Practical superconductivity applications postdate 1947 electronics goal; no node, correctly absent |

**Civ IV summary:** confirms the Civ V finding and adds one useful axis — Civ IV carries a much heavier load of *political and religious* techs (Communism, Constitution, Democracy, Divine Right, Liberalism, Meditation, Monarchy, Monotheism, Mysticism, Nationalism, Polytheism, Priesthood: 12 of the 28 new entries). All are correctly out of scope: this tree is about one person's engineering bootstrap, not a civilization's government or belief system, and it treats Rome's political/religious environment as a *risk factor in node notes* (e.g. "the state will actively resist this") rather than as something to be researched. No new gaps found.

## Source 3: Civilization VI (base game) — 68 techs, checked 68/68

List from CivFanatics' Civ VI technology page: https://civfanatics.com/civ6/info/technology/ (cross-checked era groupings via web search against the Civ Wiki's Civ6 breakdown). Civ VI's Civics tree (government/culture) is a separate, parallel tree in that game and is almost entirely political/social — it is not technology and is skipped here as out of scope by the same premise argument developed under Civ IV's political/religious techs above.

44 of the 68 overlap in meaning with technologies already tabled under Civ IV/V and get the same verdict. New names are tabled below.

| Civ VI tech (new vs. earlier lists) | Verdict | Matched node(s) / reasoning |
|---|---|---|
| Astrology | **Reject** | Ancient pantheon/religion tech (unlocks holy sites); no technical content, irrelevant to premise |
| Irrigation | Match | `ag2_gravity_irrigation`, `civ_gate_sluice`, `fud_rice_cultivation` |
| Celestial Navigation | Match | `tr_sextant_navigation`, `sc2_geometry_spherical_trig`, `exp_openocean_navigation` |
| Shipbuilding | Match | `sea_clinker_hull`, `sea_skeleton_first`, `sea_mortise_tenon` (`ships` category, 20 nodes) |
| Military Tactics | **Reject** | Ancient-era unit-upgrade tech with no real technical content; baseline Roman military competence |
| Apprenticeship | Match | `fin_apprenticeship`, `prc_apprentice_system`, `prc_toolroom_institution` |
| Stirrups | Match | `tl_stirrup` |
| Military Engineering | **Reject (period mismatch)** | Civ VI's version covers medieval siege engineering; the tree's `fortification`(12) category jumps straight from ancient assumption to 16th-century artillery fortification (`mil_bastion`, `mil_trace_italienne`) with nothing medieval between — correctly irrelevant since the character starts in Imperial Rome, not medieval Europe, and isn't besieging anyone |
| Castles | **Reject (period mismatch)** | Same reasoning — castles are a medieval-European institution the Roman-start premise never passes through |
| Cartography | Match | `fin_survey_map`: "Survey and map as state instrument" |
| Mass Production | Match | Same node as Civ IV's Assembly Line: `lnd_assembly_line` |
| Printing | Match | `printing_press`, `if_movable_type` (same as Civ V's Printing Press) |
| Square Rigging | Match | `tr_square_rig`, `sea_spritsail` |
| Siege Tactics | **Reject (period mismatch)** | No trebuchet/catapult/battering-ram content anywhere in the tree; consistent with the fortification gap above — correctly out of scope |
| Industrialization | Match | Same `mfg_*`/`interchangeable_parts` cluster as Civ IV's Industrialism |
| Ballistics | Match | `mil_ballistic_rocket`, `mil_fire_control_computing`, `opt_ballistic_galvanometer`, `tactics`(3: `mil_range_table`, `mil_indirect_fire`, `mil_forward_observer`) |
| Sanitation | Match | `sanitation_antisepsis`, `hom_flush_latrine_simple`, `hom_flush_toilet_trap`, `civ_sewer_roman`, `civ_sewer_separate` — exactly the anticipated match named in the task brief |
| Combined Arms | **Reject** | Military-doctrine balance tech (unlocks unit combos), no discrete technical content |
| Synthetic Materials | Match | `ch2_polymer_nylon`/`chm_nylon`/`tx2_nylon_6_6`, `tex_rayon_nitro`, plus the wider `polymer`(14) category |
| Telecommunications | Match (partial, correctly limited) | `telephone`(5), `telephony`(4), `telegraphy`(4) clusters cover the wired basis; satellite-relay telecom is beyond the transistor-era goal and correctly absent |
| Guidance Systems | **Reject (beyond scope)** | Missile/inertial-guidance tech postdates and is orthogonal to the point-contact transistor goal |

**Civ VI summary:** the only new pattern here (not visible in IV or V) is the **medieval-siege/castle gap** — Military Engineering, Castles, Siege Tactics all land on nothing. This is judged a non-gap for the same reason as the political/religious techs: the character starts in Imperial Rome, an already-competent siege-warfare society (Rome besieged fortified cities for centuries before 100 AD, so trebuchets-and-castles knowledge is either baseline or simply never on the path to a transistor). It is, however, a real structural observation: the tree's `fortification` category has an odd shape, jumping from an implicit ancient baseline straight to 16th-century star-fort/trace-italienne design with no medieval rung — consistent because a modern person's *knowledge* of fortification would work the same way (they'd remember cannon-era fortification design, not castle-building craft). No new gaps found beyond the two already-rejected period mismatches.

## Source 4: Humankind — 78 techs, checked 78/78

List from the official Humankind Encyclopedia's technologies-by-era page: https://humankind-encyclopedia.games2gether.com/en-us/research/game-content/technologies

Humankind's tree is heavier on pure military-doctrine and government/policy techs than any Civ game (Organized Warfare, Conquest, Standing Army, Siege Tactics, Heavy Infantry, War Summons, Centralized Power, Supply Lines, Guerilla Warfare, Military Coordination, Nationhood, Line Formation, Trench Warfare, Amphibious Warfare, Covert Ops, Insurrection Theory, Naval Air Strategy, Free Trade Theory, Social Housing, Suburbs — 19 entries), plus baseline-craft repeats already covered (Bronze-working, Calendar, Writing, Wheel, Masonry, Sailing, Domestication, Fishing, City Defense) and goal-irrelevant sci-fi/modern-balance entries (Exosuit, Neural Implant, Composite Armor, Military Laser, Communication Satellites, Fusion Reactor, Space Orbital, World-Wide Web). Only genuinely new technical concepts are tabled.

| Humankind tech (new vs. Civ lists) | Verdict | Matched node(s) / reasoning |
|---|---|---|
| Carpentry | **Reject** | General woodworking is baseline Roman craft competence; ship-specific carpentry covered under `ships`(20)/`sea_*` |
| Irrigation | Match | (as Civ VI) `ag2_gravity_irrigation`, `civ_gate_sluice` |
| Hydrology | Match (diffuse) | No dedicated science-of-water-cycles node, but practical hydraulics is deep: `water`(13), `water_prime`(11), `civ_dam_*`, `foundations`(12) |
| Craftsmanship | **Reject** | Generic flavour tech, baseline |
| Fortifications | **Reject (period mismatch)** | As Civ VI Military Engineering/Castles — no medieval fortification content; tree jumps ancient→star-fort |
| Rhetoric | **Reject** | Culture/oratory tech, no technical content |
| Trade Expeditions | Match | `expedition`(12 nodes): `exp_atlantic_crossing`, `exp_openocean_navigation`, etc. |
| Alchemy | **Reject (by design)** | A modern arrival knows real chemistry, not alchemy — the tree correctly skips straight to `lab_apparatus`, `atomic_theory`; no transitional "alchemy" stage exists anywhere, which is exactly right for the premise |
| Furnace Steel | Match | `blast_furnace`, `crucible_steel`, `cementation_steel` |
| Guilds | Match | `fin_guild` |
| Military Architecture | **Reject (period mismatch)** | Same castle/siege gap as Civ VI |
| Seafaring Mastery | Match | `marine`(50), `ships`(20), `navigation`(19) — among the tree's largest categories |
| Chartered Companies | Match | `exp_colony_administration`: "Colonial administration and a chartered company"; `fin_joint_stock` |
| Flintlock | Match | `mil_flintlock`, `mil_matchlock`, `mil_fuse_slow_match` |
| Movable Typeface | Match | `if_movable_type`, `printing_press` |
| Naval Artillery | Match | `mil_artillery_piece` + `ships`/`marine` clusters |
| Siege Cannons | Match | `mil_artillery_piece`, `mil_artillery_carriage` |
| Three-Masted Ship | Match | `sea_square_sail`, `tr_square_rig`, `ships` category |
| Encyclopedia | Match | `fin_almanac`, `prn_index_concordance`, `prn_cataloguing_system`, `sc2_institution_textbook` |
| Propeller | Match | `air_propeller_wing` |
| Urban Planning | **Reject** | City-district policy tech; practical urban infrastructure is separately covered (`infrastructure`, `sanitation`, `water`) |
| Wireless Telegraphy | Match | `com_radio_spark_transmitter` (spark-gap wireless telegraphy predates voice radio and is exactly this) |
| Mechanization | Match | `field_machinery`(22 nodes) |
| Microbiology | Match | `md2_microbiology_culture`, `germ_theory` |
| Continuous Track | Match | `tl_caterpillar_track`: "Caterpillar track: endless belt" |
| Automation | Match (partial) | `com_relay_computer`, `com_jacquard_loom`, `mfg_*` process-control cluster |
| Civil Engineering | Match | `structures`(16), `foundations`(12), `civ_*` cluster |
| Mass Entertainment | Match | `cinema`(5), `com_broadcasting_institution` |
| Mechanized Harvesting | Match | `ag2_combine_harvester`, `fud_mechanical_reaper` |
| Power Lines | Match | `electrical_dist`(8): `en_circuit_breaker`, `en_fuse`, `en_insulator`, `en_lightning_arrester` |
| Renewable Energy | Match (partial, appropriately limited) | `pwr_selenium_photovoltaic`/`pwr_selenium_cell` (the era-correct solar-cell precursor); grid-scale wind/solar is beyond the goal and correctly absent |
| Research Institute | Match | `fin_research_institute` (exact name match) |
| Uranium Enrichment | **Reject (beyond scope)** | Part of the nuclear-weapons/reactor complex, an unrelated multi-billion-dollar undertaking, irrelevant to one transistor |

**Humankind summary:** confirms the two patterns already seen (political/military-doctrine techs are correctly out of scope; medieval siege/castle technology is a genuine, consistent blind spot across all three sources so far — but one the premise itself excuses, since the character starts in Rome and never needs to besiege a castle). One new and pleasing finding: **Alchemy has no node**, and that is a *correct* absence rather than an oversight — a modern arrival already knows real chemistry and the tree reflects that by never inventing a fictional alchemical stage.

## Source 5: Old World — attempted, inaccessible

Old World's tech list lives on the Fandom wiki (`oldworld.fandom.com/wiki/Tech_tree`) and the official Hooded Horse wiki (`wiki.hoodedhorse.com/Old_World/Technology`). Both are blocked from this session: Fandom returns HTTP 402 to the fetch tool and Cloudflare-challenges direct `curl`; Hooded Horse returns HTTP 403; the Wayback Machine mirror is also unreachable from this environment. General web search surfaced only a partial, unstructured set of names (Stonecutting, Divination, Drama, Navigation, Barding, Ironworking, Statecraft, Philosophy) — not enough to treat as a real source list. Rather than guess at the remaining ~60 entries from memory (which the task brief explicitly warns against), this source is skipped. The names that did surface look like they overlap heavily with ground already covered by the three Civ games (bronze/iron working, statecraft/civil-service-type techs, philosophy, navigation) rather than pointing at anything new, so the risk of missing something Old-World-specific here is judged low, but this is a real gap in this audit's coverage, not a finding about the tree.

## Source 6: Rise of Nations — attempted, low yield

Rise of Nations' Fandom wiki also 402s to the fetch tool, and the alternative source (Heaven Games' tech database) only serves category navigation pages ("Military, Civics, Commerce, Science, Religion, Taxation, Strategy, Fortification, Militia, Attrition, Crops, Health, Lumber, Architecture, Metal, Supply, Knowledge") without the underlying technology names reachable from this session. This is also a structurally weaker source for this audit even where accessible: Rise of Nations' Library tree is four disciplines of seven numbered levels each (28 slots total), and most levels are named for a bonus track rather than a discrete real technology (e.g. repeated "Taxation I-V" style progressions), which does not map cleanly onto this tree's node-per-real-technology structure. Given the access failure and the source's low structural fit, it is skipped rather than reconstructed from memory.

## Source 7: Age of Empires II — sampled, ~35 of ~70 generic techs checked (lighter-touch pass)

AoE2's Fandom wiki also 402s and its interactive tech-tree sites (ageofnotes.com, aoe2techtree.net, liquipedia) render as JS apps that don't expose their data to the fetch tool, so no single clean master list was obtainable; the list here was assembled from multiple partial fetches (aoedb.net's Blacksmith/University listing, ageofnotes' Blacksmith-upgrades guide, and targeted searches for named techs) covering Town Center, Blacksmith, University, Market, Mill, Lumber Camp, Dock, Monastery, Stable, and Castle upgrades. Given this source's structural mismatch with the target — the large majority of AoE2's ~70 techs are flat stat multipliers on military units (+1 range, +20 HP, 15% faster gather) rather than discrete technologies with independent real-world meaning — and that its period focus (medieval Western Europe warfare and economy) duplicates ground already exhaustively checked via Civ IV/VI and Humankind, this pass is a lighter sample rather than a full 70-row audit, checking the technologies with plausible independent real-world content.

All checked non-military-stat techs found a match: Fletching/Bodkin Arrow/armor upgrades → `weapons`(47)/`armour`(2) clusters (correctly out of scope individually as unit-balance stats, not gaps); Horse Collar, Heavy Plow, Crop Rotation → `crop_rotation`, `agriculture`(21); Gold/Stone Mining → `mining`(28); Guilds → `fin_guild`; Banking, Coinage → `banking`(6)/`fin_coined_money`; Masonry, Chemistry → baseline/`chemistry`(15); Block Printing → `if_woodblock_printing`, `tx2_printing_block`; Careening/Dry Dock → `sea_drydock`, `tr_dry_dock`; Herbal Medicine → `med_herbal_pharmacy`; Treadmill Crane → `cn_crane_treadwheel` (exact match); Conscription → `mil_conscription_reserve`. Murder Holes, Fortified Wall, Hoardings, and Sappers are the same 16th-century-star-fort-vs-medieval-castle mismatch already logged under Civ VI/Humankind (no new information). Illuminated-manuscript-style Monastery techs (Illumination) correctly found nothing — art/devotional content, not technology.

**AoE2 summary:** no new gaps. This source mainly served as a third independent confirmation that the medieval-siege/castle blind spot is real but premise-appropriate, and that the tree's agriculture/finance/medicine/printing coverage is already deeper than a dedicated medieval-warfare game's economy techs.

## Source 8: Europa Universalis IV — institutions, 7/7 checked

EU4 does not have a conventional tech tree; it has 7 "Institutions" (society-wide paradigm shifts a country must embrace or fall behind): Renaissance, Colonialism, Printing Press, Global Trade, Manufactories, Enlightenment, Industrialization. Source: web search converging on the EU4 wiki's Institutions page (`eu4.paradoxwikis.com`/`productionwiki-eu4.paradoxwikis.com`); the Paradox wiki itself would not render for the fetch tool, but the institution list and mechanics description came through consistently across independent search results.

| EU4 institution | Verdict | Matched node(s) / reasoning |
|---|---|---|
| Renaissance | Match (structural) | The tree's `institution`(39) category (`academy_network`, `school_founded`, `corpus_dispersed`, `endowment_land`) is a node-level model of exactly this: building durable, hard-to-suppress knowledge institutions in a society that doesn't have them yet |
| Colonialism | Match | `expedition`(12): `exp_atlantic_crossing`, `exp_africa_circumnavigation`, `exp_colony_administration` |
| Printing Press | Match | `printing_press`, `if_movable_type` (identical name) |
| Global Trade | Match | `commerce`(16), `fin_commodity_exchange`, `exp_trade_route_extend` |
| Manufactories | Match | `mfg_*` cluster, `tex_textile_factory`, `interchangeable_parts` |
| Enlightenment | Match | `sc2_institution_journal`, `sc2_institution_learned_society`, `sc2_institution_referee`, `fin_learned_society` — the tree's `laboratory`(28)/`method`(24)/`institution`(39) clusters are essentially this concept broken into buildable steps |
| Industrialization | Match | `rail`(46), `power`(43), `machine_tools`(34), `interchangeable_parts` |

**EU4 summary:** no gaps, but a genuinely useful structural echo — EU4 models "does this society have the *institution* to keep doing science" as a single binary flag per country; this tree models the same idea as ~40 discrete, buildable `institution`-category nodes (an academy needs land endowment, dispersed copies, a founded school, a trained and manumitted staff...). It is effectively an unpacking of EU4's Renaissance/Enlightenment institutions into their component engineering problems, which is a good sign the tree's authors were thinking about the right layer of abstraction.

## Source 9: Victoria (II) — production-chain goods, ~50/50 checked

Victoria II's goods list is well-known and stable game data; the Paradox wiki pages (`vic2.paradoxwikis.com`, and Victoria 3's `vic3.paradoxwikis.com`) would not render through the fetch tool (JS-dependent shell), so the list used here is the converged result of a web search that cross-referenced multiple community sources: Coal, Coffee, Copper, Cotton, Dye, Electric Gear, Electric Power, Explosives, Fabric, Fertilizer, Financial Services, Fish, Fruit, Fuel, Furniture, Glass, Grain, Gunpowder, Horses, Iron, Lead, Liquor, Lumber, Luxury Clothes, Luxury Furniture, Machine Parts, Oil, Opium, Paper, Pharmaceuticals, Precious Metal, Print, Radio, Regular Clothes, Rubber, Shares, Shoes, Silk, Small Arms, Spices, Steel, Sugar, Sulphur, Tea, Telephones, Timber, Tobacco, Tropical Wood, Wine, Wool (~49 goods).

Rather than a name-for-name table (goods aren't technologies — they're the *output* of a production chain, and the interesting question is whether this tree models the chain that makes them), each good was checked for whether its underlying real-world production process has node coverage. All ~49 did: raw extraction (`mining`(28), `en_coal_mining_washing`, `mat_copper`, `mt2_copper_reverberatory`/`mt2_copper_electrowinning`), textiles (`textiles`(50) + `fibres`(18) + `weaving`(17) + `spinning`(9) — cotton/wool/silk/fabric/clothes chain is one of the tree's deepest branches), chemicals (`lead_chamber`/`chm_contact_sulfuric` for sulphuric acid, `chm_black_powder`/`gunpowder` for gunpowder, `chm_dynamite` for explosives, `chm_superphosphate`/`fud_haber_process_synthetic_nitrogen` for fertilizer), rubber (`mat_natural_rubber`, `mat_rubber_coagulated` for the plantation good, `ch2_polymer_buna`/`ch2_polymer_neoprene` for the synthetic follow-on), pharmaceuticals/opium (`md2_morphine`, `med_opium_mandrake`), leather/tanning (`tex_chrome_tanning`, `tex_vegetable_tanning`), electric power and telephones (`electrical`(21), `power_system`(11), `telephone`(5)), financial services/shares (`credit`(8), `fin_joint_stock`), and paper/print (`rag_paper`, `printing`(19)).

**Victoria summary:** no gaps — if anything the comparison runs the other way. Victoria represents each of these as one abstract tradeable "good"; this tree represents the same economic object as a chain of 3-6 real, separately-costed process nodes (ore to matte to blister copper to refined copper, say). This is the clearest evidence in the whole audit that the excess size is concentrated in *process depth* within domains Victoria/Civ treat as a single line item, not in domains those games cover and this one skips.

---

## Consolidated MISSING list

**Headline finding: this audit did not find a genuine missing technology.** Across 74 (Civ V) + 92 (Civ IV) + 68 (Civ VI) + 78 (Humankind) + ~35 sampled (AoE II) + 7 (EU4 institutions) + ~49 (Victoria II goods) = **~403 individual entries checked** (plus targeted spot-checks: Newtonian mechanics/gravitation, screw-thread standards, double-entry bookkeeping, vulcanized/synthetic rubber, sulphuric acid, feedback control), every single "no node found" case resolved to one of: a pre-game Roman baseline, a political/religious/social-balance tech with no engineering content, a chronological mismatch (medieval castles the Rome-start premise never reaches, or post-1947 technology beyond the goal), or a diffuse-but-real match spread across several nodes rather than one. Two sources (Old World, Rise of Nations) could not be retrieved in usable form; that is a coverage gap in this *audit*, not a finding about the tree (see their sections above for why, and for why the risk of a missed Old-World-specific gap is judged low).

Ranked by how much they might matter to this game's premise, if the bar is lowered from "no node at all" to "no *dedicated* node, only diffuse coverage":

1. **Formal economic/price theory** (Civ V/IV's "Economics", EU4's trade-theory undertone) — no node teaches supply-and-demand, price formation, or monetary theory as such; the tree only has the *institutions* of commerce (`fin_coined_money`, `fin_central_bank`, `commerce`(16), `credit`(8), `banking`(6)). *Why it might matter*: the character has to fund a multi-decade covert program without triggering the state's suspicion of large private wealth (a recurring theme in node notes, e.g. `academy_network`'s warning about being seen as a "faction") — reasoning about markets, debasement, and patronage economics as a *system* could plausibly be its own capability rather than assumed. *Where it would sit*: alongside `fin_government`/`fin_census`, tier 1-2, `institution` or a new `economics` category. Judged low-priority: the tree's practical financial-institution coverage is already unusually deep for a craft-focused tree, and a modern arrival's economic intuition (inflation, markets) is closer to "things they already know" than "things they must research," consistent with how the tree treats other modern-knowledge givens.

2. **Hydrology / water-cycle science as formal theory** (Civ VI's Irrigation implies some understanding of it; Humankind names it explicitly) — no dedicated node for rainfall, catchment, and aquifer theory as science; only practical hydraulic engineering (`water`(13), `water_prime`(11), `civ_dam_*`, `foundations`). *Why it might matter*: reservoir sizing and well-siting for a workshop in an arid Mediterranean province could depend on this. *Where it would sit*: `soil` or `water` category, tier 0-1. Judged very low priority — practical hydraulic engineering nodes already let a player build what they need; formal hydrology reads more like the kind of thing a Civ tech invents to have *something* in that tech slot than like a real bottleneck on the path to a transistor.

No other candidate survived scrutiny. Notably absent from the list, and deliberately: alchemy (the tree correctly skips it because a modern arrival knows real chemistry), medieval siege/castle technology (correctly out of scope — the character starts in Imperial Rome and never besieges anyone), and the entire cluster of post-transistor/beyond-goal technology (lasers, nuclear fission/fusion, satellites, computing beyond relay logic, composites, fiber optics, superconductors) which several sources include but which postdates or is orthogonal to `point_contact_transistor` by design.

## Structural observations on the EXTRA (what the tree's size reveals)

Node counts were grouped into thematic clusters (the tree's 200+ raw `cat` values are fine-grained — many have 1-4 nodes and look auto-derived from source-document section headers rather than hand-balanced, so raw category counts are noisy; clusters below sum related categories and cover ~2,139 of the 2,833 nodes, the rest being smaller media/consumer/power-generation categories):

| Thematic cluster | Nodes | 
|---|---|
| Precision / machine-tools / measurement & metrology | 313 |
| Transport (rail, marine, aviation, road, carriages) | 309 |
| Chemistry, materials & metallurgy | 304 |
| Electronics, electrical & computing (the goal's own neighbourhood) | 230 |
| Physics, mathematics & optics (pure science) | 175 |
| Medicine & health | 165 |
| Agriculture & food | 163 |
| Institutions, finance, law & social organisation | 150 |
| Textiles, fibres & leather | 136 |
| Structures & civil engineering | 115 |
| Military, weapons & fortification | 79 |

Reading this against the published trees above:

- **The single biggest raw category is `measurement` (88 nodes) — bigger than any other category by a wide margin**, and it isn't even all of the metrology story: `machine_tools`(34), `metrology`(16), `capability`(34, the tiered "what tolerance/temperature/vacuum can you sustain" ladder) and `precision`(7) sit next to it. No published game gives measurement-and-tolerance its own tech line at all — Civ's "Replaceable Parts" is one node; this tree spends over 300. That is the tree's real thesis, stated in node form: **you cannot bootstrap precision electronics without first bootstrapping the ability to measure precision itself**, one tolerance rung and one calibration standard at a time. This is the opposite of Civ V's four hypothetical "textiles vs agriculture" imbalance — the actual excess is concentrated in *epistemic infrastructure* (how do you know you succeeded), not any single craft domain.
- **Transport (309) and military (79) sit at opposite extremes**, which is a tell by itself. A civilization-balance game inflates military for parity between competing empires; this tree treats weapons as incidental — useful for patronage, income, or political cover, never the point — while transport (getting people, ore, and finished instruments across a pre-railroad empire reliably) gets nearly four times the space, because *logistics*, not *combat*, is the actual constraint on a one-person covert programme.
- **Medicine (165 nodes) is larger than military and comparable to agriculture.** This is not what a "build a transistor" brief would predict, and it's a genuine authorial signature: keeping a tiny team of irreplaceable specialists alive for decades in a pre-antibiotic, pre-anaesthetic world is its own subgoal (and `collegium_licensed` / `med_medical_education`'s notes make the "physician" identity explicit as *cover*, not just care).
- **Agriculture (163) and textiles (136) are close to each other and both mid-sized** — contrary to the prompt's illustrative worst case (400 vs 11), the tree is not lopsided here; both are "background economy" domains sized similarly, neither dominant nor starved.
- **Electronics/electrical/computing (230), the goal's own neighbourhood, is large but not the largest cluster** — smaller than measurement, transport, or materials. This is appropriate: the transistor itself is a narrow target once the precision/materials/measurement base exists; most of the tree's bulk is that base, not elaboration on the goal.
- **No dedicated "culture," "government," or "religion" cluster exists at all** — the closest is `institution`(39) + `law`(14) + `organisation`(30), all narrowly practical (assay offices, patent offices, guilds, universities), never Civ-style abstractions like a national government type or a state religion. Every published source's political/religious tech content (a combined ~60 entries across all sources checked) lands here as a correct, total absence — the tree has no equivalent because it needs none: this is one person's build order, not a civilization's government.

## Rejected candidates (by premise, not by absence)

The following published-game technologies had no node and were deliberately NOT counted as gaps, because the premise (one modern person, starting in Rome 100 AD, trying to reach one working transistor) rules them out:

- **Pre-game Roman-baseline givens** (all sources): Agriculture, Pottery, Animal Husbandry, Archery, Mining, Sailing, Calendar, Writing, Trapping, The Wheel, Masonry, Bronze/Iron Working, Alphabet, Hunting, Fishing, Carpentry, Domestication, Craftsmanship, Military Tactics, Astrology, Compass (basic form) — the tree's 268 root nodes already assume a functioning Iron-Age Roman society; these are what the character starts *inside*, not what they research.
- **Political, governmental and legal-system techs** (all sources, ~30 entries): Code of Laws, Communism, Constitution, Democracy, Divine Right, Feudalism, Guilds-as-political-structure (craft-guild economics itself IS matched), Liberalism, Monarchy, Nationalism, Centralized Power, Imperial Power, Statecraft-type techs — irrelevant to a single engineering project.
- **Religious/devotional techs** (~15 entries): Theology, Meditation, Monotheism, Mysticism, Polytheism, Priesthood, Astrology, Divine Right — religion appears only as political *risk* in this tree's node notes, never as something to research.
- **Culture/Great-Works/social techs** (~10 entries): Archaeology, Drama, Literature, Rhetoric, Mass-Entertainment-as-policy, Illuminated manuscripts — no technical content.
- **Military-doctrine/unit-balance techs with no discrete real technology** (~20 entries): Chivalry, Military Tradition, Combined Arms, Organized Warfare, Conquest, Standing Army, War Summons, Guerilla Warfare, Line Formation, Military Coordination, Naval Air Strategy, Insurrection Theory, Amphibious Warfare, Covert Ops — game-balance abstractions, not technologies.
- **Medieval siege/castle technology** (Civ VI, Humankind, AoE II — ~6 entries): Castles, Military Engineering, Siege Tactics, Military Architecture, Fortifications — a genuine, consistent absence across three independent sources, and correctly so: the character starts in Imperial Rome (already a siege-capable society) and the tree's own fortification content picks up again at 16th-century star forts (`mil_bastion`, `mil_trace_italienne`), skipping the intervening medieval period entirely because nothing there is relevant to reaching a transistor.
- **Post-goal / beyond-scope technology** (~20 entries across Civ V/IV/VI, Humankind): Nuclear Fission/Fusion, Lasers, Satellites, Stealth, Robotics, Advanced Ballistics, Particle Physics, Nanotechnology, Future Tech, Fiber Optics, Composites, Superconductors, Guidance Systems, Communication Satellites, Fusion Reactor, Space Orbital, World-Wide Web, Neural Implant, Exosuit, Uranium Enrichment — chronologically or thematically past `point_contact_transistor`, correctly outside the tree's endpoint.
- **Alchemy** (Humankind) — deliberately and correctly absent: a modern arrival knows real chemistry and the tree never invents a fictional transitional stage.

## Sources consulted

1. Civilization V (Brave New World) — CivFanatics and Civilization Wiki tech lists, cross-checked (74/74 techs)
2. Civilization IV (Beyond the Sword) — CivFanatics Civilopedia (92/92 techs)
3. Civilization VI (base game) — CivFanatics technology list (68/68 techs)
4. Humankind — official Humankind Encyclopedia (78/78 techs)
5. Old World — inaccessible (Fandom 402, Hooded Horse 403, Wayback unreachable); skipped rather than reconstructed from memory
6. Rise of Nations — inaccessible in structured form; also a poor structural fit (abstract bonus-level tree); skipped
7. Age of Empires II — sampled ~35 of ~70 generic (non-unit-stat) technologies across Blacksmith/University/Market/Mill/Dock/Monastery/Stable/Castle
8. Europa Universalis IV — 7/7 Institutions
9. Victoria II — ~49/49 goods, checked for production-chain (not name) coverage

---
Status: COMPLETE.
