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
