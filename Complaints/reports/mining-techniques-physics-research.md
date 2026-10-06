# Mining techniques as physical terms, and the mint: research for Complaint 374

Research only. No code or data changed. Source tags: **read** (page or PDF opened this session), **snippet** (search-result text only, not opened), **recalled** (from memory, unchecked). Every figure not tagged read needs confirming before it enters a `declare()` with confidence above D.

## 1. What exists now

- `mining_tech` is a node mechanic `{yield, cost, materials?}` (`data/branches/MECHANICS.md`). `Sim.mining_tech(material)` multiplies the entries of every running node, then clamps with `MINING_TECH_YIELD_CEILING` and `MINING_TECH_COST_FLOOR` (both `temporary_heuristic`, confidence D, `sim/engine/economy_mining.py`).
- Nodes carrying it today: `met_mine_pumping` (yield and cost multipliers), `met_black_powder_blasting`, `met_dynamite_blasting`, `pwr_rotary_drilling`, `railway`, `steam_atmospheric`, `blast_furnace`, `mat_bulk_steel`. The multipliers are unsourced.
- Nodes the task names that do not exist in `data/branches/` as nodes: Archimedean screw, water-wheel battery, drainage adit, ruina montium or hushing, fire-setting, ventilation furnace. A grep of `data/branches/*.json` for screw, adit, hush, ruina and fire-set finds only unrelated notes. `met_safety_lamps_ventilation` and `met_winding_engine` exist without `mining_tech`. Ancient techniques are today "free" (fire-setting is hard-wired into `sim/world/mine_fire_setting.py`, hand lifting into `deposits._lift_hours_per_tonne_metre`).
- The works formulas (`sim/world/mine_works.py`, `sim/world/deposits.py`), in labourer-hours per tonne of ore:
  - breaking = breaking_hours_by_hardness + fire_setting_hours (per tonne of rock, times rock_per_ore)
  - hoist = lift_hours_per_tonne_metre x shaft_depth_metres
  - haulage = trips_per_tonne x 2 x haul_distance_metres / carry_speed_metres_per_hour
  - drainage = water_tonnes_per_tonne_ore x lift_hours_per_tonne_metre x shaft_depth_metres
  - timbering = timbered_share x timber_hours_per_metre / drive_rock_tonnes_per_metre x rock_per_ore
  - shaft build (`shaft_cost_labour_hours`) = breaking + spoil_lift + support + drainage_works (per metre of head) + hoist_frame + ventilation (a second shaft, same bill as the working shaft less frame and sump)
  - lift_hours_per_tonne_metre = gravity x 1000 kg / (sustained_power_per_labourer x hoist_efficiency x 3600 s)
- Mint (`sim/economy/mint.py`, `currency.py`): a coin is a mass of metal, the mint charge is a policy share (`mint_charge_share`), and capacity is `MINT_YEARLY_STRIKE_SHARE` of the money stock per year, a labelled heuristic. No mint labour, no fineness, no assay.

## 2. Per-technique tables

General shape of every row: the technique changes one term of the works by changing a physical parameter of that term (a power source, an efficiency, a head, a distance, a load per trip, a hardness-dependent rate). Parameters live in a technique data file (proposed `data/production/mining_methods.json`, schema documented in `_SCHEMA.md`), referenced by the node through a new mechanic `mining_method` (replaces `mining_tech`).

### 2.1 Archimedean screw (drainage lift)

| Item | Detail |
|---|---|
| Term changed | drainage (lift per tonne-metre of water) and the drainage works in the shaft bill |
| New term | `drainage_hours_per_tonne_ore = water_tonnes_per_tonne_ore x water_lift_hours_per_tonne_metre x head_to_lift_metres`, with `water_lift_hours_per_tonne_metre = gravity x 1000 / (power_per_worker x machine_efficiency x 3600)`; `machine_efficiency` is that of the screw, not of a windlass. Stages: `stage_count = ceil(head_to_lift_metres / head_per_stage_metres)`; works hours = `stage_count x hours_to_build_one_stage`, rebuilt every `service_life_years`. |
| Figures | Screws drained Spanish mines "in successive lifts" (Diodorus 5.37, already cited in `mine_works.py`; Strabo 3.2.10 mentions Egyptian screws in Spain, snippet). Screw and wheel remains both found at Rio Tinto; a wooden screw near Rio Tinto (snippet, Wikipedia reverse overshot wheel, read for the wheel facts). Modern screw pump efficiency 70 to 84 percent across flows (snippet, firgelli, a vendor page: weak). Human-powered screw 250 to 500 L/min at 0.2 to 1 m lift (snippet, same vendor page: weak, a shallow irrigation lift, not a mine stage). Head per stage and power per worker in a mine: **not found**. |
| Lives in | method row `archimedean_screw`: `{term: "drainage", power_source: "human", machine_efficiency, head_per_stage_metres, stage_build_hours, service_life_years, workers_per_stage}`; node `archimedean_screw` (to be authored, preconditions: carpentry, helical geometry). |
| Source quality | Mechanism sourced; the three numbers (efficiency in a leaky wooden screw, head per stage, crew) are not. Derive head per stage from geometry (inclination angle and the screw length one carpenter can build) once Oleson 1984 is read. |

### 2.2 Water-wheel battery (reverse overshot, drainage lift)

| Item | Detail |
|---|---|
| Term changed | same drainage term; adds a finite maximum head per installation |
| New term | per wheel: `water_lifted_per_hour = wheel_bucket_volume x buckets_emptied_per_hour`; `wheel_head_metres = about the wheel diameter less the sump and discharge allowance`; battery head = `wheel_count_in_series x head_per_wheel`; crew hours per tonne-metre = `crew_size x hours / (tonnes_lifted x head_per_wheel)`. |
| Figures | Rio Tinto: 16 wheels in pairs, each pair lifting about 3.5 m, total about 30 m (snippet, Wikipedia; read the page via fetch, citing Palmer 1928, Davies 1935, Boon and Williams, JRS 56, 1966). Wheel diameter: Santo Domingos (Portugal) had ten wheels, eight of 4.876 m diameter, 8 cm larger than the Rio Tinto wheel in the British Museum, two of 3.657 m (**read**, Wollmann, Der Anschnitt 2/3 2019, German, PDF text). Rio Tinto wheel had 27 spoke pairs (read, same). Wollmann argues the wheels were not treadmills: the crew stood beside the wheel and pulled spokes down by hand (**read**), against the Wikipedia statement "treading slats" (snippet). Ruda in Romania: 75 m depth needing at least 32 wheels (snippet via Wikipedia). Dolaucothi: wheel fragment from 50 m below known workings (snippet). **Not found:** litres per hour per wheel, crew size per wheel. |
| Lives in | method row `reverse_overshot_wheel_battery`: `{term: "drainage", head_per_wheel_metres, wheels_in_series, crew_per_wheel, machine_efficiency, build_hours_per_wheel}`; node to be authored. |
| Source quality | Head and geometry good enough to build the finite-head rule and the cost of each stage; throughput and crew need Boon and Williams 1966 or Wollmann full text (the saved PDF may carry them: not read fully). |

### 2.3 Drainage adit (sough)

| Item | Detail |
|---|---|
| Term changed | removes the lift for water above the adit level; replaces it with a one-off drive cost; shortens the pumped head |
| New term | `pumped_head_metres = max(0, working_depth_metres - adit_invert_depth_below_portal_metres)`; `adit_drive_length_metres = adit_invert_depth_below_portal_metres / adit_gradient + horizontal_offset_to_working_metres`; `adit_build_hours = adit_drive_length_metres x drive_rock_tonnes_per_metre x breaking_hours_per_tonne (hardness of the country rock) + timbering + its own ventilation shafts` (drives longer than natural draught supports need airshafts; cost is already modelled for shafts). Water above the adit leaves by gravity, so `drainage_hours_per_tonne_ore` uses `pumped_head_metres`. The adit also drains the catchment of every shaft along it: build cost is shared across shafts, a district-level work, not a per-shaft one. |
| Figures | Great County Adit, Cornwall: begun 1748, over 64 km of tunnel, draining over 100 mines at an average depth of 80 to 100 m, discharge over 14.5 million gallons a day in 1839 (snippet, Wikipedia and Cornish Mining pages). Derbyshire: Meerbrook sough over four miles; Vermuyden sough took 20 years, Cromford sough 30 years (snippet, Wikipedia Sough). Bettenay 2022: horizontal adits from the valley side drain, allow mining upwards and haul by gravity; Melle-type workings need multiple shafts for ventilation (**read**). Adit gradient: **not found** (recalled: a few parts per thousand; do not use). Hard-rock drive advance for the build: see 2.4, the Kongsberg figure. |
| Lives in | a district feature in geography (adit portal elevation) plus the method row `drainage_adit`: `{term: "drainage_head", gradient, build_term: "drive"}`. It is a project (build), not a multiplier: once built it lowers `pumped_head_metres` for all workings above its invert. |
| Source quality | Mechanism, scale and discharge are good; gradient and per-metre advance rate needed. The adit's build hours can be computed from the existing breaking and fire-setting terms with no new number. |

### 2.4 Fire-setting (hard-rock breaking, already in the model; becomes an explicit method)

| Item | Detail |
|---|---|
| Term changed | breaking: rock broken per labourer-hour in hard rock, with wood burned per tonne |
| New term | `breaking_hours_per_tonne_rock = wood_cutting_hours_per_tonne_wood x wood_tonnes_per_tonne_rock + face_labour_hours_per_tonne_rock` (fire tending, raking, scaling overhangs). Currently the face labour is the flat hardness figure (`BREAKING_HOURS_PER_TONNE_*`, unsourced, D) and the wood term is added to it. |
| Figures | Wood per tonne rock: 0.3 to 1.2 across 66 Fournel experiments, mean 0.6; Kongsberg 0.4; Melle 0.7 up to 2.8 (**read**, Bettenay Table 1, already in `mine_fire_setting.py`). 1,140 kg of wood per cubic metre of rock (snippet of the Bettenay abstract; check against the wood-per-tonne figure above). Rock broken per miner per day 150, 250, 425 kg for realistic, optimistic, extreme Melle (**read**, Table 4). Late 19th century Kongsberg: advancing one fathom of a drive 6.5 ft by 5 ft took 37.5 man-days in 1860 to 1864 and 38.5 in 1881 to 1885 using fire-setting, equal to about 385 kg of rock per miner per day (**read**, Bettenay Table 2 citing Timberlake 1990 and Collins 1883). Forest worker output 1 to 1.5 green tonnes per day, early medieval; 2.5 to 3.5 modern manual (**read**). |
| Lives in | method row `fire_setting` (hard rock only): `{term: "breaking", applies_to_hardness: ["hard"], wood_tonnes_per_tonne_rock, face_hours_per_tonne_rock}`. Always available (no node), as bronze-age practice. |
| Source quality | Well sourced for wood; the face labour per tonne can now be derived from the Kongsberg figure (385 kg per man-day, total labour including wood is partly inside it), which is a reason to refit `BREAKING_HOURS_PER_TONNE_HARD` against measured man-days rather than keep 20 h/t. |

### 2.5 Gunpowder blasting (`met_black_powder_blasting`) and dynamite (`met_dynamite_blasting`)

| Item | Detail |
|---|---|
| Term changed | breaking in hard and medium rock: replaces fire-setting with hand drilling plus charge; removes the wood term and the fume ventilation load; adds powder as an input |
| New term | `breaking_hours_per_tonne_rock = (drill_hole_metres_per_tonne_rock x drilling_hours_per_hole_metre + charging_and_tamping_hours_per_blast) + powder_kilograms_per_tonne_rock x powder_hours_per_kilogram`, where the powder is a produced good (its recipe already exists via the tree; the cost falls out of the price solver). Rock hardness enters through `drilling_hours_per_hole_metre` (harder rock, slower drilling) and powder per tonne. |
| Figures | First documented mining blast: Schemnitz, 8 February 1627 (snippet, Geo7 Weiss Arzberg and others). Many 15th and 16th century blasting records are dubious (**read**, medievalists.net summary; no quantities). Hand boring of shot holes reached England with German miners about 1670; the chisel-bit jumper bar was in general use by 1759 (snippet). Monthly sinking rates with hand drilling and black powder 3.2 to 4.5 m, 3.0 to 4.0 m "satisfactory" (snippet, unnamed source on a shaft-sinking page: unverified, and shaft sinking, not drifting). Cornish tutwork paid about thirty shillings a fathom (snippet). **Not found:** powder per tonne of rock, drilling rate per man-hour by hardness, drift advance with powder in the same Kongsberg drive for comparison. |
| Lives in | method row `black_powder_blasting`: `{term: "breaking", replaces: "fire_setting", drill_hours_per_hole_metre_by_hardness, hole_metres_per_tonne_rock_by_hardness, powder_kg_per_tonne_rock_by_hardness, fume_ventilation_factor}`; `met_dynamite_blasting` is a second row (nitroglycerine based powder per tonne smaller, faster charge); `pwr_rotary_drilling` and `met_pneumatic_drill` change only `drill_hours_per_hole_metre` through their power source (compressor fuel per hole metre). |
| Source quality | Poor. The driving number (hours per tonne by method and hardness) is the one thing the Kongsberg fire-setting figure anchors on one side only. Next source: Timberlake 1990 and Agricola Book V; also Berg 1988 (Kongsberg productivity, cited in Bettenay, not opened). |

### 2.6 Hushing and ruina montium (water breaks the ground)

| Item | Detail |
|---|---|
| Term changed | replaces breaking, hoist and haulage of overburden or loose ground by labour with erosion by released water; the cost becomes reservoir and channel building plus the catchment's water. Today stripping overburden is not charged at all (`ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH` note, Complaint 349), so the baseline has to gain a stripping term before this technique has anything to replace. |
| New term | `ground_moved_tonnes_per_year = water_released_cubic_metres_per_year x eroded_tonnes_per_cubic_metre_of_water x ground_erodibility_factor` (by ground class); the ground the water cannot move (rock core) still needs breaking; labour = reservoir and channel building amortised (`channel_length_metres x channel_hours_per_metre / service_life`) plus gate tending and clearing. Water is limited by catchment: `water_available = rainfall_runoff x catchment_area`, a constraint from geography, so the mechanism fails in dry districts by physics. |
| Figures | Las Médulas: the system used about 16 million cubic metres of water a year (snippet, an amusingplanet article repeating tourist-board figures; the same page gives 190 thousand per day, which is not consistent with 16 million a year). Seven aqueducts, about 300 km total length (snippet, same). Excavated volume: 90 million cubic metres in one snippet, 240 million in another, which disagree. Pliny NH 33.74 (ruina montium, corrugi, reservoirs above the working) not opened. Gold: Pliny's 20,000 lb a year at NH 33.78 is already in the precious-metals source report (read there). Hushing in the Dales: dam the stream, release the torrent, scour the soil to bare the seams (snippet, Wikipedia Gunnerside Gill; Historic England listing for Moss Dam); no volumes found. Existing model: hydraulic alluvial class has `AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC` and a flow-limited capacity already (`deposits.shaft_rock_capacity_tonnes_per_year`). |
| Lives in | the existing `alluvial_hydraulic` class is the seed; generalise to a method row `hydraulic_stripping`: `{term: "stripping", water_source: "catchment", erodibility_by_ground_class, channel_hours_per_metre}`. Geography supplies catchment area and runoff. |
| Source quality | Mechanism good; every quantity weak or inconsistent. Do not build the quantitative form until the water per tonne eroded is found (hydraulic mining literature: sluice and giant-monitor duty of water per cubic metre of gravel, 19th century California, recalled not sourced). |

### 2.7 Newcomen atmospheric engine (`steam_atmospheric`) and winding engine

| Item | Detail |
|---|---|
| Term changed | drainage lift: power from fuel instead of labour. A fuel-driven pump has no worker-hours per tonne-metre, only fuel per tonne-metre and attendants; extends reachable head (see section 3). Winding engine (`met_winding_engine`) does the same to the hoist term. |
| New term | `fuel_kilograms_per_tonne_metre_of_water = gravity x 1000 / duty_joules_per_kilogram_of_fuel`; `duty_joules_per_kilogram_of_fuel = fuel_energy_per_kilogram x engine_efficiency`, with the engine efficiency a property of the engine design (atmospheric: low because the cylinder is heated and cooled each stroke). Labour = `attendants_per_engine x hours / tonnes_lifted_per_hour` plus engine build and rebuild hours (boiler, cylinder, beam, pump rods). Fuel is a produced good; its cost, including land for wood or mine labour for coal, falls out of the solver. A pumping engine at a coal mine burns coal the mine produces, a feedback the solver handles through the coal price. |
| Figures | Duty is foot-pounds lifted by one bushel of coal. Smeaton, the average of fifteen engines at Newcastle in 1769: 5,590,000 (snippet, Grace's Guide and others). Smeaton's old and new engine: 4.6 million and 9.1 million (snippet). Smeaton on Watt's engines about 1778: about 18 million at Birmingham, about half a million more at Hull (**read**, Treatise on the Cornish Pumping Engine, Appendix G, goobi.tib.eu). The same text has Smeaton concluding that Watt's engines did on average double the duty of the atmospheric engine (read). Bushel weight 84 lb (snippet, one search summary; check). Conversion in SI from these: 5.59 million ft-lb per 84 lb bushel is about 0.2 MJ per kilogram of coal lifted-work, which against a coal of order 25 MJ per kilogram is below one percent efficiency (calculation from the tagged figures, with the coal energy recalled). Cylinder operating at about 12 strokes a minute, boiler at 1 to 2 psi (snippet, Wikipedia Newcomen); normal maximum lift 50 yards per pump column due to pipe pressure (snippet, same; that is the stage limit). |
| Lives in | method row `atmospheric_engine`: `{term: "drainage", power_source: "fuel", duty_joules_per_kilogram_of_fuel, head_per_pump_column_metres, attendants, build_hours, service_life_years}`; same shape for `watt_engine` (duty about three times; read) so technique ladders replace each other rather than multiplying. |
| Source quality | Best of all: duty is an engineering measurement with named measurer and year. The conversion should be a documented test, not a typed number: engine efficiency from heat balance can be derived and compared with Smeaton's measurements as a check. |

### 2.8 Ventilation furnace and shaft ventilation

| Item | Detail |
|---|---|
| Term changed | the ventilation term: currently a second shaft at the working shaft's cost. A furnace at the foot of the upcast shaft makes draught independent of the temperature difference between the two openings, so it allows deeper, longer, or one-sided workings, at a running cost in fuel. |
| New term | `required_airflow = workers x airflow_per_worker + lamps x airflow_per_lamp + firedamp_dilution_airflow (coal and gassy ground only)`; `natural_draught_airflow = f(shaft_height_difference_metres, temperature_difference, shaft_cross_section)` (from the stack equation, physical); where natural draught falls short, a furnace supplies `furnace_fuel_per_hour = airflow x air_heat_capacity x temperature_rise / (fuel_energy x stack_efficiency)`. No-furnace workings are capped by what natural draught can supply, which limits workings length and depth in physics, not by a ceiling. |
| Figures | Furnaces at the bottom of the upcast were later replaced by fans (snippet, a general history page). Bettenay: multiple shafts to aid ventilation and to dissipate fire-setting fumes (**read**, already cited in `mine_works.py`). **Not found:** airflow per worker, furnace fuel consumption, airflow achieved. The airflow need per person is a physiological figure (oxygen and carbon dioxide limits) that can be derived and sourced from occupational health references; I did not search for it. |
| Lives in | a district or working method row `furnace_ventilation`; node `met_safety_lamps_ventilation` today bundles two different things (see 2.10). |
| Source quality | Poor for numbers; the formula is derived physics. |

### 2.9 Iron rails and wagons (`railway`, `lnd_iron_edge_rail`)

| Item | Detail |
|---|---|
| Term changed | haulage (underground and to the dressing floor) |
| New term | `haulage_hours_per_tonne_ore = 2 x haul_distance_metres / carry_speed_metres_per_hour x workers_per_trip / tonnes_per_trip` (carrier is a person, a horse and driver, or a locomotive), plus `rail_laying_hours_per_metre x haul_distance_metres / (tonnes_carried_over_rail_life)`. The barrow is the current default: 100 kg per trip, 3,000 m per hour round trip. |
| Figures | Wagons on rails let one horse deliver 10 to 13 tons of coal per run, about four times a road wagon (snippet, Early Transport PDF). Horse on a road: about 1 ton load; on wooden waggonway 2 to 3 tons including carriage; on a macadam road laid with iron strips the friction falls sevenfold (snippet, two pages). These are fully derivable: tractive effort = rolling resistance coefficient x weight, so tonnes per horse = horse pull / (resistance coefficient x gravity). Both coefficients are physical constants for a surface and wheel pair, and belong in the existing land-transport data, which already prices freight; mining haulage should call the same function. |
| Lives in | no new mining datum: the mining haulage term should call the land-transport freight function (`sim/geography` freight) for a track surface and carrier, rather than hold barrow constants. `railway` loses its `mining_tech` entry (yield 1.3, cost 1.0, which also never changed cost). |
| Source quality | Good, and mostly a reuse of existing physics. |

### 2.10 Safety lamp (and open flame lighting)

| Item | Detail |
|---|---|
| Term changed | not a labour term. It changes (a) whether a seam with firedamp can be worked at all (an access gate), (b) the accident and explosion risk, and (c) a small running cost in lamp oil or candles, which is the "lamp oil" omission listed in the review report. |
| New term | `workable = firedamp_concentration_class not in explosive_without_gauze or has_safety_lamp`; `lighting_hours_per_tonne = lamp_fuel_kilograms_per_worker_hour x workers_hours_per_tonne x fuel_labour_hours_per_kilogram`. Explosion risk goes into the risk fields already carried by nodes (`risk`), not into labour. |
| Figures | Davy made the first lamps from mid-October to December 1815 (snippet, Royal Institution page): a flame inside wire gauze that absorbs heat so the gas outside is not ignited. Felling disaster, 1812 (snippet, Wikipedia). Lamp fuel per worker-hour: **not found**. |
| Lives in | deposit data gets `firedamp_class` (coal and some metal veins); node `met_safety_lamps_ventilation` should be split into a lamp node (gate) and a ventilation node (furnace, 2.8). |
| Source quality | Mechanism and date good; no labour effect to model, which is itself a finding: today's node has no `mining_tech` and should stay without one. |

## 3. What replaces the generic multiplier

1. **A `mining_method` mechanic per node** naming the term it replaces and its physical parameters (the rows above). `Sim.mining_tech` becomes `Sim.mine_works_for(deposit)`: for each term (breaking, stripping, drainage, hoist, haulage, ventilation), pick the cheapest available running method for that deposit, not the product. Methods replace each other within a term (screw, wheel battery, engine all compete for drainage; adit changes the head they must overcome and is applied before them).
2. **The yield multiplier is retired**, because what it stood for (a pump lets a mine go deeper, so more of the deposit is extractable) is a reach limit: each lifting method has `maximum_head_metres` (stages x head per stage, from 2.1, 2.2, 2.7); a deposit's ore below the reach is not accessible, and extractable tonnage becomes `ore_above_reach(deposit, reach)`. This needs the deposit to carry a depth profile (tonnes by depth), which `SHAFT_DEPTH_METRES_*` hides today; until then keep the depth class and use its single depth.
3. **The cost multiplier is retired**, because each method's hours per tonne come from its own formula. The floor and ceiling (`MINING_TECH_COST_FLOOR`, `MINING_TECH_YIELD_CEILING`) are then deleted: the bounds are the physical limits inside the formulas (efficiency at most one, a head per stage that cannot grow, a draught that cannot exceed the stack effect, a catchment that cannot yield more water than falls on it). Where a bound is needed for a transitional heuristic, label it per 4.4 and give it a named constant tied to a method.
4. **Compounding goes away by construction.** The old multipliers multiplied (pumping 1.4, blasting, rails 1.3 and steam 1.6 together could reach the ceiling of 3). With one chosen method per term and a real formula, a second pump technology cannot stack on the first; it only competes.
5. **Materials scoping** (`materials` list in the old spec) becomes the deposit's own attributes (hardness, depth, firedamp, water) rather than a per-material list, in line with 4.7 (no content ids in engine).

## 4. Mint: labour per coin, fineness, seigniorage (Complaint 374, second item)

What the model has: coin is `kg_per_unit` of silver, `mint_charge_share` is a policy fraction, striking capacity is `MINT_YEARLY_STRIKE_SHARE x money supply`, labelled temporary. No labour, no assay, no fineness.

What to model, each tied to lower-level state:

| Part | Formula in spelled-out names | Figures and sources |
|---|---|---|
| Striking labour | `striking_hours_per_coin = 1 / coins_struck_per_worker_hour`, with a crew arrangement (a team at each anvil table). | Efficient hammerers could strike about 100 coins an hour; 32 malliatores listed for the second century Rome mint (snippet, a Wight museum paper on how Romans made a coin; experimental archaeology claim, not independently checked). The product, about 6,400 coins a day, is the source's own arithmetic. |
| Die cutting labour | `die_hours_per_coin = hours_per_die / coins_per_die`, where `coins_per_die` is a wear property of die metal and strike force. | Engravers cut about 2 dies a day each, about 4 for the Rome mint in the first century BC (snippet, coinbooks.org E-Sylum). Coins per die: **not found**; it is the quantity die-study scholars (Callatay, Duncan-Jones, noted in the review as "not opened") estimate, and it also converts surviving dies into output, so it ties the model to the numismatic ensemble of 4.2 without a dated target. |
| Blank making and refining | `refining_hours_per_kilogram_of_fine_silver` from cupellation (lead, fuel, litharge recovery), alloying, rolling or casting blanks, weighing and adjusting each blank. | Not found in this pass. Cupellation losses by process are in the Bettenay Table 4 (read: 0 to 2 percent of silver lost in cupelling, 5 to 15 percent of lead lost in cupelling and re-smelting), so the existing Melle model already fixes the loss side for the refining of mine silver; the mint's own re-melting loss per cycle is separate and unsourced. |
| Fineness control | `fineness = fine_silver_mass / coin_mass`; the issuer's specification; the mint's assay method (touchstone, then cupellation assay) has a measurement error and a cost; the delivered fineness is `specified_fineness + assay_error + alloying_error` with a tolerance the state enforces (a "remedy"). Debasement is then an issuer choice of specified fineness against a metal cost saved. | Medieval England: samples from each batch put aside for an annual Trial of the Pyx, a privy mark identified the moneyer, the penalty for coin under standard might be severe (snippet, moneyness.ca and Money Museum pages). The unit `fire_assay` already exists as node `met_fire_assay` (assay for ore grade) and should also serve as the mint's measurement, so fineness control is a capability, not a flag. |
| Seigniorage and brassage | `mint_price_of_bullion = parity x (1 - mint_charge_share)`; `minimum_charge_share = (mint_labour_cost + refining_cost + fuel + metal_loss_value) / metal_value_struck`; the issuer chooses a charge at or above this floor, and a charge far above it invites bullion to go elsewhere (to an external or private mint), which `mint.py` already represents by parity both ways for weighed metal. | English silver seigniorage hovered around 5 percent for centuries; gold minting fees typically 0.5 to 2 percent; the mint master took a smaller share, brassage, for his time, tools and wages (snippet, moneyness.ca, Munro lecture notes). Treat these as ensemble checks (relationship: charge above cost floor), never as inputs. |

How it plugs in: `mint_orders` replaces `MINT_YEARLY_STRIKE_SHARE` with `capacity = mint_workers x coins_per_worker_hour x hours_per_year`, `mint_workers` coming from labour hiring like any firm (4.3, general actors: any state or player mint uses the same mechanism). `settle_mint` already books seigniorage as the issuer's gain; add the mint's labour and fuel as costs paid out of the charge, so seigniorage is the net.

## 5. Staged build plan

Tests assert relationships, never target outputs (4.1, 4.2).

**Stage 0, make the baseline measurable (no behaviour change).**
Add `python3 sim/simulator.py` subcommand or test that prints, per deposit, the per-term hours per tonne (breaking, hoist, haulage, drainage, timbering) and the shaft bill split. Tests: the terms sum to `vein_hours_per_tonne_ore`; per-term values are non-negative. Run the fingerprint before and after (CLAUDE.md section 6).

**Stage 1, generalise the lift term.**
Introduce `water_lift_hours_per_tonne_metre(method)` and `reach_metres(method)` with the human windlass as the first method row (so behaviour is unchanged). Tests: drainage hours scale linearly with water per tonne; drainage hours scale linearly with head; a method with double the efficiency halves the drainage hours; a method whose reach is below the shaft depth makes the deposit inaccessible; hand lift matches the existing numbers (regression).

**Stage 2, add the ancient lifting methods.**
Archimedean screw and reverse overshot wheel battery rows, nodes, and the stage count rule (read Oleson 1984 and Boon and Williams 1966 for head per stage and crew first). Tests: a deeper deposit needs more stages and costs more per tonne (monotone); two methods for the same term do not stack; with the screw available a deep wet mine costs less than with the windlass for the same water (relationship only, no target ratio); build hours per stage rebuild after the service life.

**Stage 3, adit.**
District feature for portal elevation; adit as a build project. Tests: pumped head is non-negative and strictly less than depth when an adit exists; an adit does not reduce the cost of workings below its invert; build hours grow with drive length; a district with several shafts shares one adit cost (cost per shaft falls with shaft count).

**Stage 4, breaking methods.**
Refit `BREAKING_HOURS_PER_TONNE_HARD` against the Kongsberg man-days per fathom using the fire-setting method row; then add black powder with powder as a produced good. Tests: with powder available and cheap, hard rock cost falls below fire-setting; with powder price set very high the fire-setting method is chosen (methods compete by cost); wood consumption in the economy falls when powder is chosen (propagation, 4.3); no `if node == ...` in the engine (4.7).

**Stage 5, fuel-driven lift.**
Atmospheric engine, winding engine, with duty converted from the sourced measurements; fuel is a solver good. Tests: coal use per tonne-metre equals gravity times mass divided by duty (formula check); a Watt row has strictly lower fuel use than a Newcomen row (ordering from Smeaton's measurement); at a pit where coal is expensive the engine's advantage over human lift shrinks (price propagation, relationship only); a mine that drains with its own coal raises coal's extraction cost slightly (feedback present).

**Stage 6, haulage, ventilation, lamp.**
Haulage calls the freight function; ventilation from airflow need and natural draught with furnace fuel; lamp as an access gate. Tests: rail haulage hours per tonne fall as friction coefficient falls; haulage grows with haul distance; furnace fuel grows with airflow; a gassy seam is unworkable without the lamp node and workable with it; no labour change from the lamp.

**Stage 7, retire `mining_tech`.**
Delete the mechanic, the ceiling and floor constants, and the data entries; update `MECHANICS.md`; `python3 sim/simulator.py validate`; `python3 sim/constants.py --burndown` shows the two heuristics gone. Tests in `sim/tests/test_mines.py` that read `mining_tech` are rewritten to read the new function.

**Stage 8, hydraulic stripping.** After a stripping term exists in the baseline (Complaint 349) and water per tonne eroded is sourced.

**Stage 9, mint.**
Mint labour per coin, die labour, capacity from workers; fineness and assay; seigniorage net of cost. Tests: capacity scales with mint workers; seigniorage is the charge less cost, never above the metal value struck; a charge below the cost floor produces a loss the issuer must fund (relationship); halving the specified fineness halves the fine silver per coin; assay with larger error widens the delivered fineness spread but not its mean; debasement raises coin count per kilogram of silver (check of the accounting).

**Closure and reopening** (the third item of Complaint 374) is outside this report; the status line of 374 says producer exit is done in round four.

## 6. Open questions

1. Head per screw stage, and the labour that drives one: no figure from a mining source found. Read Oleson 1984 (Greek and Roman Mechanical Water-Lifting Devices) and the Rio Tinto finds.
2. Water throughput and crew per Roman reverse overshot wheel. Boon and Williams 1966 (paywalled) and the Wollmann article (PDF saved here, only partly read; it argues hand-pulling, not treading, which changes the power source from legs to arms and so the power per worker).
3. Water inflow per tonne of ore (the existing `WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH` is a guess): the same open item as Complaints 343 and 349. A physical alternative is inflow from catchment infiltration into the working's drawdown area, which needs hydrogeology inputs the map does not carry.
4. Adit gradient and per-metre drive labour in non-hard rock. Per-metre advance by hardness class from the Kongsberg (hard, fire-set) figure only.
5. Powder per tonne of rock and drilling hours per hole metre by hardness; Schemnitz 1627 productivity change. The 3.2 to 4.5 m per month sinking figure is from an unidentified page.
6. Water per tonne eroded for hushing and ruina montium, and a consistent Las Médulas volume (the two snippets disagree by more than a factor of two). Read Lewis and Jones 1970 on Roman gold mining in north-west Spain, and Pliny NH 33.70 to 77.
7. Newcomen: bushel weight and the coal energy used in the SI conversion are not verified; the 1769 average of 5.59 million is from a snippet. Read Appendix G of the Cornish engine treatise at the page that gives Newcomen and Smeaton values.
8. Mint: coins per die; hammerer rate (a single experimental claim); refining labour and loss per recoinage; Roman assay practice (touchstone use in antiquity is recalled, not sourced here).
9. Is the reach rule (extractable ore above `reach_metres`) enough without a tonnes-by-depth profile for deposits? The catalogue holds a depth class only; a depth profile is a data task in geography (Complaint 440).
10. Ancient method nodes are not in the tree: do they appear as capabilities (any tradition has fire-setting), or as nodes with prerequisites, and does the start-date of a civilisation decide the initial set? This is a design decision for the owner, with the constraint that fire-setting must be available at the start.

## 7. Sources

Read: Bettenay 2022, Metalla 26.2 (https://metalla.org/index.php/METALLA/en/article/download/9777/9276/8260), Tables 1, 2, 4 and the wood-sourcing text. Wollmann 2019, Der Anschnitt 2/3 (https://www.bergbaumuseum.de/fileadmin/forschung/zeitschriften/der-anschnitt/2019/2019-02-03/anschnitt-2-3-2019-wollmann.pdf), partial text extraction. Treatise on the Cornish Pumping Engine, Appendix G (https://goobi.tib.eu/viewer/!fulltext/1029262349/44). Wikipedia, Reverse overshot water wheel (https://en.wikipedia.org/wiki/Reverse_overshot_water_wheel), which cites Palmer 1928, Davies 1935, Boon and Williams 1966. Medievalists.net, civil uses of gunpowder (https://www.medievalists.net/2014/08/civil-uses-gunpowder-demolishing-quarrying-mining-15th-18th-centuries-reappraisal/), no quantities.

Snippet only: Wikipedia Great County Adit and Sough (https://en.wikipedia.org/wiki/Great_County_Adit, https://en.wikipedia.org/wiki/Sough); Las Médulas (https://www.amusingplanet.com/2026/03/las-medulas-wrecking-of-mountains.html, https://en.wikipedia.org/wiki/Las_M%C3%A9dulas); Gunnerside Gill (https://en.wikipedia.org/wiki/Gunnerside_Gill); Roman coin making (https://www.iow.gov.uk/documentlibrary/download/how-they-made-a-roman-coin-v2) and die cutting (https://coinbooks.org/esylum_v17n20a12.html); English seigniorage (https://www.moneyness.ca/2013/10/medieval-qe.html and https://www.economics.utoronto.ca/munro5/L03AMedievalMoney.pdf); Newcomen duty (https://gracesguide.co.uk/Long_Benton_Colliery); early railways (https://www.mosaicprojects.com.au/PDF_Papers/P207_The_first_railway_projects.pdf); Davy lamp (https://www.rigb.org/node/3129); screw pump performance (https://www.firgelliauto.com/blogs/mechanisms/archimedian-screw-water-lift, a vendor page); sinking rates (https://magazine.cim.org/en/the-evolution-of-shaft-sinking/evolution-of-shaft-sinking-part-two-en/).

Project documents read: Complaint 374, `Complaints/reports/silver-mining-and-minting-review.md` (the precious-metal sources report was not read in full), `sim/world/mine_works.py`, `sim/world/mine_fire_setting.py`, `sim/world/deposits.py`, `sim/engine/economy_mining.py`, `sim/economy/mint.py`.
