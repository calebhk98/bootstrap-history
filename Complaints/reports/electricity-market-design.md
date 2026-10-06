# Electricity delivery market: design

Date: 2026-10-06. Branch `electricity-market-design` (from `structural-dedupe-and-owner-decisions`). Research and design only: no code or data changed, no tests run. Follows `Complaints/reports/authored-revenue-audit.md` (class C_electricity, ranked first) and `Complaints/closed/295-*.md` (energy carriers have prices, nodes that sell them have no output to derive).

Source tags: **read** = I opened the page and took the figure from it; **snippet** = figure seen only in a search-result summary, not confirmed on the page; **recalled** = textbook physics or history I am stating from memory, to be checked before it is written into data; **derived** = computed here from other figures; **needed** = a figure the build requires and this report does not supply.

## 1. The problem in one paragraph

About two dozen `el2_` and `en_` nodes (three-wire distribution, ring mains, substations, transformers, meters, dispatch, power-factor correction, grid interconnection and so on) carry typed `rev_hours` and repay their build in weeks (`el2_three_wire_distribution_system` and `el2_ring_main_distribution` are the two fastest paybacks in the whole tree). Nothing in `data/production/` prices the service they provide. The generators are priced: `electrical_mj_dynamo` and `electrical_mj_photovoltaic` in `data/production/70_energy.json` make the carrier `electrical_mj` at the generator, and eleven other entries (aluminium, silicon, calcium carbide, electrolytic and arc recipes in `20_nonferrous.json`, `30_fuel_stone.json`, `50_chemicals.json`, `92_metals_components_gaps.json`, `93_chemistry_nuclear_gaps.json`) draw `electrical_mj` as if it arrived at their door for free of loss and of lines. The wire, pole, transformer and meter between the two have no entry, so no node can derive an output from them (`sim/engine/node_output.py` returns None for a node that gates nothing, and `node_revenue.py` falls back to `authored`).

## 2. What the existing code gives us

- `node_output.entries_gated_by(node_id, production)` finds every entry whose `requires_node` is the node. `output_baskets` bounds each line by plant `annual_output_at_basis`, by staff hours and by `annual_output_t`, sells carrier outputs through `energy_prices.EnergyPrices.sold` and buys carrier inputs through `bought`. A delivery entry with a `capital` list therefore gives a node derived revenue with no engine change, provided the output is something `output_baskets` can value.
- Energy carriers are a closed tuple, `("thermal_mj", "mechanical_mj", "electrical_mj")`, repeated in `sim/engine/energy_prices.py`, `solve_prices_core.py`, `validate_production.py` and `sim/economy/recipes.py`. Only `thermal_mj` is graded by a capability (temperature reached versus needed; `CAPABILITY_CAP_FIELDS`). Mechanical and electrical price at the pool.
- `EnergyPrices.sold` carries a labelled transitional cap (CLAUDE.md 4.4): a producer sells no dearer than its own technique costs, because no demand for megajoules exists. Delivery nodes will hit this cap too until a demand side exists (stage 4).
- Complaint 295 already names the fix for the power nodes: gate an energy entry with its capacity and give energy a demand to sell against.

## 3. What each node physically does

Electricity is a flow that must be generated at the moment it is used, priced at the point of delivery, with the chain generation, step-up, transmission, step-down, distribution, metering, end use. Storage exists (`en_battery_*`, `en_pumped_storage`, `en_flywheel_storage`) but only shifts time at a cost and a round-trip loss; the market is a delivered flow, not a stock (recalled; the standard textbook point, restated by Insull's load factor argument below).

| Stage | What the physics is | Nodes |
|---|---|---|
| Generation (class b, already priced) | converts mechanical or radiant energy to current | `en_dynamo`, `en_alternator`, `en_three_phase_gen`, `en_exciter`, `en_commutator`, `en_hydroelectric_station`, `en_thermal_station`, `en_steam_turbine_*`, `en_wind_electric`, `el2_dynamo_*`, `el2_alternator_rotating_field`, `el2_rectifier_*`, `el2_motor_rotary_converter_AC_DC`, `en_rotary_converter` |
| Voltage change | a transformer trades current for voltage, so line current and I squared R fall | `en_transformer`, `el2_transformer_core_air` (small signal, not power), `el2_insulator_bushing`, `el2_substation_voltage_regulation`, `en_substation`, `el2_tap_changer_load_compensator` |
| Bulk transmission | long line at high voltage between generator and load centre | `en_transmission_line`, `en_insulator`, `el2_insulator_pin_porcelain`, `en_grid_interconnection`, `en_lightning_arrester`, `el2_lightning_arrestor_gap` |
| Distribution | low-voltage feeders and mains reaching each consumer | `el2_three_wire_distribution_system`, `el2_ring_main_distribution`, `el2_earthing_grounding_system` |
| Protection and switching | limits the cost of a fault (lost output, burnt plant) | `en_switchgear`, `en_circuit_breaker`, `en_fuse`, `el2_switch_knife`, `el2_circuit_breaker_thermal`, `el2_circuit_breaker_magnetic`, `el2_fuse_wire_element`, `el2_protective_relaying_differential` |
| Quality and reactive power | keeps voltage and current in phase so line current does not carry reactive power | `en_power_factor_correction`, `el2_power_factor_correction_capacitor`, `el2_standardised_voltage_nominal`, `el2_standardised_frequency_nominal`, `en_frequency_standardisation`, `el2_synchroscope_phase_angle_indicator` |
| Operation | schedules plant so load factor and diversity rise | `en_load_factor_diversity`, `el2_load_dispatch_and_scheduling` |
| Storage (time shift) | charge, hold, discharge with a round-trip loss | `en_battery_lead_acid`, `en_battery_nickel_iron`, `en_battery_charging`, `en_pumped_storage`, `en_flywheel_storage` |
| Metering and connection | makes sale by energy possible; connects the customer | `el2_meter_energy_kWh_meter`, `el2_meter_*` (instrument family), `el2_plug_socket_portable` |
| End use (buyers, not sellers of delivery) | consume delivered current | `el2_electroplating_and_electrorefining`, `el2_arc_welding_*`, `el2_resistance_welding_*`, `el2_induction_heating_*`, `el2_dielectric_heating_*`, `el2_electropolishing_*`, `el2_electrostatic_precipitation_*`, `el2_electric_lift_motor_gear_reduction`, `el2_electric_drill_handheld_motor`, `el2_trolleybus_catenary_power`, `el2_electric_locomotive_traction_motor`, motors (`el2_induction_motor_*`, `el2_synchronous_motor`, `el2_universal_motor_AC_DC`), `hom_electric_lighting` |

The audit puts only the delivery rows in class c. End-use nodes sell goods or services that already have (or need) their own entries (the audit classes several as d, enabling).

## 4. Physics the entries must carry

### 4.1 Loss

For a line of length L, conductor section A, resistivity rho, carrying current I at voltage V, the loss is I squared times rho L / A. Since delivered power is P = V I times a phase and power-factor factor, the loss fraction is

    loss_fraction = resistivity * length * current_density / (voltage * power_factor_term)

with current_density = I / A (the conductor's thermal or economic limit, a material property). Facts that fall out, each of which becomes a relationship test:

- loss fraction rises linearly with distance and falls as 1/voltage for a fixed conductor current density;
- for a fixed loss fraction and power the copper section falls as 1/voltage squared (raising voltage by ten cuts I squared R by a hundred for the same conductor: **read**, Wikipedia, Electric power transmission);
- copper mass per unit of delivered power per kilometre is density / (current_density * voltage) (derived).

Economic conductor size (Kelvin's law: annual interest on the conductor equals annual cost of the energy lost in it) says the loss is not a free input: it is chosen so marginal copper cost equals marginal loss cost (recalled; Kelvin 1881). The entry can therefore state the thermal current density as the physical bound and let one derived loss fraction fall out per tier; the choice between tiers is the solver's.

### 4.2 Sourced figures

| Figure | Value | Tag | Source |
|---|---|---|---|
| Pearl Street, 1882: six dynamos of 100 kW, 82 customers, 400 lamps at opening; 508 customers and 10,164 lamps by 1884 | as stated | read | [Wikipedia, Pearl Street Station](https://en.wikipedia.org/wiki/Pearl_Street_Station) |
| 110 V DC supply; three-wire 220 V design replaced the two-wire to cut conductor copper | as stated | read (110 V lighting, three-wire used thinner wire to save copper: ETHW); snippet (220 V figure) | [ETHW Pearl Street Station](https://ethw.org/Pearl_Street_Station), [ETHW Edison's Electric Light and Power System](https://ethw.org/Edison%27s_Electric_Light_and_Power_System) |
| Pearl Street served about one square mile; underground wiring 100,000 ft per ETHW, which differs from the 80,000 ft first stated (disputed, range 80,000 to 100,000 ft; 80,000 not found on a page) | 100,000 ft (corrected) | read (area and 100,000 ft); snippet (80,000 ft) | [ETHW Pearl Street Station](https://ethw.org/Pearl_Street_Station), [ETHW Early Applications](https://ethw.org/Early_Applications_of_Electric_Power) |
| Pearl Street setup cost including real estate | 300,000 dollars ("about $300,000" covering real estate, station, wires, conduits) | read | [ETHW Pearl Street Station](https://ethw.org/Pearl_Street_Station) |
| Heavy copper cost kept Pearl Street unprofitable for its first five years | as stated | read (qualitative) | [ETHW Edison's Electric Light and Power System](https://ethw.org/Edison%27s_Electric_Light_and_Power_System) |
| Three-wire saves 60 to 70 percent of the copper investment (Edison, Hopkinson and Siemens reached it at about the same time) | 60 to 70 percent; consistent with the derived 3/8 below (62.5 percent saving) | read (Insull's 1898 address, p. 17) | [Insull, Central-Station Electric Service, 1915](https://archive.org/details/centralstationel00insurich) |
| Three-wire with a neutral the same section as the outer wires uses three eighths of the two-wire copper at equal power and equal percentage loss | 3/8 | derived | doubling voltage quarters the section per wire (section 4.1); three wires of a quarter against two of one |
| Ferranti, Deptford to London, 10,000 V, supply from February 1891; stepped down to 2.5 kV at substations | as stated | read | [Grace's Guide, London Electric Supply Corporation](https://www.gracesguide.co.uk/London_Electric_Supply_Corporation) |
| Lauffen to Frankfurt, 15 kV, about 175 km, 1891 | as stated | read | [Wikipedia, Electric power transmission](https://en.wikipedia.org/wiki/Electric_power_transmission) |
| 100 miles at 765 kV, 1000 MW: loss 0.5 to 1.1 percent; at 345 kV same load and distance: 4.2 percent | as stated | read | same |
| US transmission and distribution losses about 5 percent of energy, 2018 to 2022 | as stated | read | [EIA FAQ 105](https://www.eia.gov/tools/faqs/faq.php?id=105&t=3) |
| Overhead ACSR for 33, 22 and 11 kV networks; a 100 mm2 "Dog" conductor: 6/4.72 mm aluminium over 7/1.57 mm steel, 105.0 mm2 aluminium, 118.5 mm2 total, 14.15 mm diameter, 0.2792 ohm/km at 20 C | mass 394 kg per km (corrected from 273, which is near the aluminium-only mass); ampacity about 231 A at 75 C and 282 A at 85 C (replaces 232 to 343 A) | read (mass, areas, resistance: Table 1); snippet (ampacity, search summary of IS 398 Part II; the cited spec has none) | [MSEDCL ACSR specification SP/T-120, 2019, Table 1](https://www.mahadiscom.in/supplier/wp-content/uploads/2019/06/Final-ACSR-conductor-specification-24.04.19-docx-1-Copy.pdf) |
| Chicago Edison average rates: about 20 cents per kWh in 1892, 10 in 1897, 5 in 1906, 2.5 in 1909 | as stated; a second search summary repeats it, but neither the Wikipedia Commonwealth Edison nor Samuel Insull page text contained it when fetched | snippet | [Wikipedia, Commonwealth Edison](https://en.wikipedia.org/wiki/Commonwealth_Edison) |
| Insull: load factor (average over peak demand) is the profit lever; a plant serves loads several times its rating through diversity; time-of-use pricing | qualitative | read (two-part rate, load factor, diversity of rural summer and suburban winter peaks: IER page; Buteau not opened) | [Antoine Buteau, lessons from Insull](https://www.antoinebuteau.com/lessons-from-samuel-insull/), [IER, Samuel Insull](https://www.instituteforenergyresearch.org/the-grid/energy-pioneers-samuel-insull/) |
| London Electric Supply Corporation advertised 7.25 pence (7 1/4 d) per Board of Trade unit in 1888 | as stated | read | [Grace's Guide, LESCo](https://www.gracesguide.co.uk/London_Electric_Supply_Corporation) |
| Hopkinson two-part demand and energy tariff 1892; Wright's hours-of-use block tariff about 1896 | as stated; Fortnightly page read for both years; Brighton link (Wright was engineer at Brighton from 1894) from a search summary of Grace's Guide only, the page returned 503 | read (years), snippet (Brighton) | [Grace's Guide, Arthur Wright](https://gracesguide.co.uk/Arthur_Wright), [Fortnightly](https://www.fortnightly.com/node/23556) |
| UK coal per unit sold fell from 4.1 lb (1914) to 3.75 lb (1918) as units grew and load factor rose | as stated | read | [1922 Britannica, Electricity Supply](https://en.wikisource.org/wiki/1922_Encyclop%C3%A6dia_Britannica/Electricity_Supply) |
| Copper resistivity, copper density, aluminium resistivity and density | physical constants | recalled | CRC Handbook; enter with the source cited in the entry |
| Economic conductor size: Kelvin's law (annual interest on the conductor equals annual cost of energy wasted), applied through a constant A that is 380 for copper and 165 for aluminium; economic current density is not a fixed number because it depends on the cost of copper per ton and of station capacity per kW | law and constants as stated; no numeric current density | read | [Del Mar, Electric Power Conductors, 1909](https://archive.org/details/electricpowercon00delmrich), pp. 156-157 |
| Copper and aluminium conductor mass per mile, stranded (copper: aluminium), by size | 1,000,000 cmil 16,140 : 4,870 lb/mile (4,550 : 1,373 kg/km); 500,000 cmil 8,070 : 2,430 lb/mile; 4/0 3,420 : 1,030 lb/mile; No. 1 1,351 : 407 lb/mile; per wire, includes 1 percent for stranding. Aluminium is about 0.30 of copper mass at the same section | as stated; kg/km derived (lb/mile times 0.2819) | read (Table IV, p. 140) | [Del Mar, Electric Power Conductors, 1909](https://archive.org/details/electricpowercon00delmrich) |
| Finished wood-pole line, 22 kV three-phase, 130 ft span: 40 creosoted cedar poles (35 ft) per mile (about 25 per km), 48 crossarms, 144 H.T. insulators per mile; conductor 16,000 ft of No. 1 hard-drawn copper plus 700 ft No. 4 ties and 10,800 ft No. 10 telephone wire = 4,550 lb per mile (about 1,280 kg/km). Cost per mile: materials ex-conductor 562 dollars, labour other than clearing 295 dollars (clearing 363 dollars in wooded country), conductor 682.50 dollars at 15 dollars per 100 lb; total 1,902.50 dollars (1913 prices) | as stated; kg/km derived | read (Preliminary Estimate No. 1, pp. 40-41) | [Still, Overhead Electric Power Transmission, McGraw-Hill 1913](https://archive.org/details/overheadelectric00stilrich) |
| Steel-tower line, 80 kV two three-phase circuits, 480 ft span: 10 A-frame flexible towers plus one strain tower per mile, 90 suspension insulator sets per mile; conductor No. 00 hard-drawn copper 13,350 lb per mile (about 3,760 kg/km); materials ex-conductor 1,620 dollars, labour 968 dollars of which clearing 363 dollars, conductor 2,002 dollars; total 4,590 dollars per mile (1913 prices) | as stated; kg/km derived | read (Preliminary Estimate No. 2, p. 42) | [Still, Overhead Electric Power Transmission, McGraw-Hill 1913](https://archive.org/details/overheadelectric00stilrich) |
| Wood pole mass: 65 ft, 7 in. top diameter eastern white cedar pole about 2,410 lb | as stated | read (p. 197) | [Still, Overhead Electric Power Transmission, McGraw-Hill 1913](https://archive.org/details/overheadelectric00stilrich) |
| Pole spacing and poles per km | 40 poles per mile at 130 ft span (22 kV wood); about 11 towers per mile at 480 ft span (80 kV steel); normal steel-tower span 400 to 600 ft; with a No. 4 conductor spans should not much exceed 250 to 300 ft | as stated | read (pp. 40-42, 225) | [Still, Overhead Electric Power Transmission, McGraw-Hill 1913](https://archive.org/details/overheadelectric00stilrich) |
| Insulator and crossarm mass per km by voltage class | needed; costs only (insulator price curve to 100 kV, Fig. 17, p. 39 of Still, curve values not read) | needed | no mass table found in Still, Del Mar or the Standard Handbook |
| Transformer active material, 20 kVA single-phase oil-cooled, 5000 to 200 V, same I squared R loss in each design: 50 Hz 76 kg steel plus 68 kg copper = 144 kg (7.2 kg/kVA), core loss 190 W, copper loss 365 W, efficiency 97.9 percent; 25 Hz 252 kg (12.6 kg/kVA), core loss 214 W; 15 Hz 426 kg (21.3 kg/kVA), core loss 230 W | as stated; per kVA derived. Mass per kVA falls with size (output rises as the fourth power of linear dimension, weight as the third: [Kapp, Transformers, 1896](https://archive.org/details/transformerssing00kapprich), pp. 57-58, read) | read (Tables 11 and 12, pp. 89-91) | [Hobart, The Design of Static Transformers, 1911](https://archive.org/details/designofstatictr0000hmho) |
| Winding current density in transformers 1,000 to 2,000 circular mils per ampere; core flux density 40,000 to 60,000 lines per sq in at 60 Hz | as stated | read (p. 335) | [Foster, Electrical Engineer's Pocket-Book, 3rd ed., 1903](https://archive.org/details/electricalengine01fost) |
| Distribution transformers, 2,200 to 110/220 V, 60 Hz, core loss W and copper loss W at full load: 1 kW 20 and 26; 5 kW 45 and 102; 50 kW 240 and 605. Full-load efficiency 95.8 percent at 1 kW to 98.4 percent at 50 kW. Core loss runs 24 hours a day: a 5 kW transformer loaded 4 hours a day has full-load efficiency 97.1 percent and all-day efficiency 93.0 percent | as stated (ratings and column order read from the OCR text and the 5 kW worked example, which agrees with the table; the intermediate rows are garbled in the scan, so only 1, 5 and 50 kW are quoted from it) | read (Sec. 12 pars. 101-102, p. 1040; ordinary-print check against the page image not done) | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft) |
| Net weight including oil, large 60 Hz single-phase power transformers 250 to 1,000 kVA, 11 to 44 kV class: about 5,600 to 18,000 lb | scan too garbled to assign a weight to a rating; do not enter into data | read (unusable) | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft), Sec. 6 pars. 96-102 |
| Meter cost per customer, meter reading labour per customer-year | needed | needed | utility histories (Hughes, Networks of Power; Platt, Electric City) |
| Distribution labour: setting poles | 40 to 50 poles a day with a gin wagon, two linemen and a teamster | read | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft), Sec. 11 par. 167 |
| Line patrol: one patrolman per about 20 miles of line | as stated | read | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft), Sec. 11 par. 230 |
| Linemen hours per km-year (maintenance); station attendants per MW | needed | needed | not found in the sources searched here |
| Service life: untreated wood poles cedar 15, chestnut 12, cypress 9, juniper 8.5, pine 6.5 years; treated poles 20 years or more; creosote adds 2 to 3 years | as stated | read | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft), Sec. 11 pars. 146-148, p. 982 |
| Service life, UK well-seasoned creosoted poles about 35 years in good soil, 18 to 20 in poor soil; US average about 12 years untreated, 14 to 16 cedar and chestnut; steel towers 50 years or more if painted; wood poles 30 years or more | as stated | read | [Still, Overhead Electric Power Transmission, McGraw-Hill 1913](https://archive.org/details/overheadelectric00stilrich), pp. 197-198, 225 |
| Depreciation basis for distribution: poles about 15 years with little salvage; other overhead line material 5 to 10 years; overhead system about 5 percent a year; lead-sheathed cable about 15 years; weather-proof wire 2.5 percent of cost; fixed charges overhead 11 percent, underground 10 percent | as stated | read | [Fowle (ed.), Standard Handbook for Electrical Engineers, 5th ed., McGraw-Hill 1922](https://archive.org/details/standardhandbook00fowluoft), Sec. 12 pars. 222-224, p. 1070 |
| Service life of transformers; life of insulators and crossarms | needed | needed | not found; the Standard Handbook depreciation table (Sec. 10 par. 898) is garbled in the scan |
| Load factor by customer class, Chicago Edison: office building 3.7 percent (323 hours a year), small shop 7, day saloon 16, lunch counter 20, large dry-goods store 25, industry 35, all-night restaurant 48 percent. Station daily curve: December 1897 about 48 percent, May 1898 nearly 60 percent. Annual system load factor 1899 a little over 28 percent | as stated | read | [Insull, Central-Station Electric Service, 1915](https://archive.org/details/centralstationel00insurich), pp. 26-27 and 83 |
| Diversity at the transformer: a block of 189 residence customers, separate maxima summing 68.5 kW, load factor 5.5 percent on that sum, 19 percent on the transformer maximum of 20 kW | as stated | read | [Insull, Central-Station Electric Service, 1915](https://archive.org/details/centralstationel00insurich), pp. 127-128 |
| System diversity, Chicago, one winter: street railway about 20 percent, own departments a little over 5 percent, combined 12.8 percent, expected 20 percent; non-coincident maxima 25.8 percent above the coincident maximum; central-station investment about 100 dollars per kW (c. 1909) | as stated | read | [Insull, Central-Station Electric Service, 1915](https://archive.org/details/centralstationel00insurich), pp. 86-87, 131-132 |
| Insull's tariff steps, Chicago: income 25 cents per kWh in 1881-82 and about 7 cents by 1898; income about 10 cents against cost about 12 in 1896; 2.05 cents (Commonwealth Edison, 1914). Railway wholesale: 15 dollars per kW of maximum demand per year plus 0.5 cent per kWh, cut to 0.4; actual 0.77 cent at 48.7 percent load factor and 0.9 cent at 42.6 percent. Retail 1915: smallest residence 10, 5 and 3 cents per kWh by hours of use of the maximum demand (12 and 9 cents quoted c. 1910); other companies quoted manufacturers 2.25 to 3 cents. The Wright demand system is the basis of all contracts | as stated | read | [Insull, Central-Station Electric Service, 1915](https://archive.org/details/centralstationel00insurich), pp. 17, 31, 65-72, 75, 80-81, 95, 217, 438 |
| Early load factor by supply station other than Chicago (Pearl Street, Deptford, British stations) | needed | needed | not found; the Whittaker central-station handbook scan (archive.org centralstatione00yeamgoog) is too garbled to read tables |
| Round-trip efficiency of lead-acid, nickel-iron, pumped storage | needed | needed | battery and hydro handbooks |
| Luminous efficacy: carbon filament, tungsten filament, arc lamp, candle, oil lamp, gas mantle | needed | needed | lighting engineering history (Illuminating Engineering Society) |
| Motor efficiency by type and size | the existing `electrical_mj_motor` basis | read | `data/production/70_energy.json` (92.5 percent basis) |

## 5. Design

### 5.1 One service, defined once

Split the carrier into the thing generated and the thing delivered.

- `electrical_mj` keeps its meaning to every consumer: current at the customer's meter. Eleven entries already draw it and the motor, resistance-heat and lighting conversions read it, so none of them needs editing.
- New material `electricity_generated_mj`, the output of each generator technique at the busbar (`electrical_mj_dynamo`, `electrical_mj_photovoltaic` and the alternator, turbine and hydro entries that stage 5 of the audit's B_conversion list adds). It is an ordinary priced good, not a carrier, so `node_output` values it through `goods` with no special case. **Open question for the implementer:** the carriers are "not tree materials" (70_energy.json note); confirm the solver accepts a good with no tree node. If it does not, the fallback is a fourth carrier added to the four `ENERGY_CARRIER_FIELDS` lists.
- Delivery is a set of technique entries whose output is `electrical_mj` and whose inputs include `electricity_generated_mj` grossed up for loss, exactly as `electrical_mj_dynamo` grosses up `mechanical_mj` for the dynamo's efficiency.

### 5.2 Entry shape

One entry per voltage tier (and one for on-site supply with no line). Per batch of delivered energy:

- `outputs`: `electrical_mj` per batch.
- `inputs`: `electricity_generated_mj` equal to the batch divided by one minus the loss fraction. The loss fraction is computed from section 4.1 and written down in `yield_basis`, per CLAUDE.md 4.5 (a physical fact, never tuned to a sale price).
- `labour_hours`: linemen, electricians and station attendants per batch.
- `capital`: the line and its terminal plant, each with `build_materials` (copper wire, poles, insulators, transformer iron, switchgear), `build_labour_hours`, `service_life_years` and `annual_output_at_basis` equal to rated power times hours in a year times the load factor. Insull's argument enters here: capital cost per delivered megajoule is capital divided by annual delivered energy, and load factor is the fraction of the year the line is full. `en_load_factor_diversity` and `el2_load_dispatch_and_scheduling` raise it (section 5.4).
- `requires_node`: the gating node (table in section 6).
- `reach_km` (new, section 5.3): the distance the tier clears.

Machines stay in `80_machines.json` as the schema asks (transformer unit per kVA, meter unit, kilometre of line per voltage class), referenced from `build_materials`.

### 5.3 Distance and reach

The price solver is global, with no location; distance belongs to geography. Reuse the existing pattern for temperature: the solver prices a small set of reach bands (the cheapest tier whose `reach_km` clears the band), exactly as `capability_price_for_requirement` does for temperature, and an agent buys the band its own distance clears. The distance comes from `sim/geography` (the route and freight layer already measures tile distances). A consumer entry that states no distance pays the default band, the local network, so existing consumer data is untouched. For a customer far from any generator the band with the lowest delivered cost wins (a line with a transformer pair, a higher voltage) and the price rises with distance until a higher tier takes over. This is the delivered-price behaviour the tests in section 8 check.

### 5.4 Terms a node improves

An improvement node gates a better entry variant (a cheaper or lossier technique the solver may choose), the schema's existing way of making a node "better something": the solver picks the cheapest entry, so a variant that cuts a term is adopted only where it pays.

- more voltage, therefore less loss and less copper per MW-km: `en_transformer`, `en_transmission_line`, `en_insulator`, `el2_insulator_*`, `en_substation`, `el2_substation_voltage_regulation`;
- less copper for the same loss: `el2_three_wire_distribution_system` (three-eighths copper at equal loss, derived above);
- fewer faults and shorter outages, so fewer lost megajoules and less repair labour per unit: `el2_ring_main_distribution` (two feed paths), `el2_protective_relaying_differential`, `en_circuit_breaker`, `en_fuse`, `en_switchgear`, `en_lightning_arrester`, `el2_earthing_grounding_system`; modelled as an availability fraction in `annual_output_at_basis` and a repair-labour term. **needed**: fault rate per km and restoration time (utility reliability histories). Mark any stand-in as a 4.4 heuristic until measured;
- less reactive current: `en_power_factor_correction`, `el2_power_factor_correction_capacitor` lower the line current for the same real power, which lowers I squared R by the square of the power factor ratio (recalled, standard AC theory);
- higher load factor and diversity, so more annual output per tonne of line: `en_load_factor_diversity`, `el2_load_dispatch_and_scheduling`, `en_grid_interconnection`, `el2_synchroscope_phase_angle_indicator` (parallel running), `el2_standardised_*`, `en_frequency_standardisation` (allow interconnection; each raises the `annual_output_at_basis` of the plant in the entries it gates, or lets a tier of larger units exist);
- metering: `el2_meter_energy_kWh_meter` is what makes sale by energy possible. Without it the only entry sells by the lamp (Pearl Street billed by lamp before its meters; **recalled**), and an unmetered customer draws more than a metered one. The unmetered entry carries a consumption multiplier input that the metered entry lacks; its size is a **needed** figure and is labelled a 4.4 heuristic until sourced;
- storage: `en_battery_*`, `en_pumped_storage`, `en_flywheel_storage` become entries that take `electrical_mj` and return `electrical_mj` at a round-trip efficiency; they earn the spread between peak and off-peak price, which exists only once the market has a time dimension (stage 5).

### 5.5 Who buys delivered electricity

- Industry: the eleven entries already listing `electrical_mj` (electrolysis, arc, carbide), plus the motor entry (`mechanical_mj_motor`) and the resistance and arc heating entry (`thermal_mj_electric`), plus the `el2_` end-use nodes once they gate entries (welding, plating, induction, dielectric heating).
- Traction: `tr_electric_locomotive` and `el2_trolleybus_catenary_power` draw delivered energy in their running entries.
- Households: the household need `warmth_and_light` in `data/world/needs.json` is met today by fuels only. Add a good for lamp-hours of light with `electrical_mj` as its input and a lamp as capital, and let it satisfy `warmth_and_light` against candles, kerosene and gas. The relative cost per unit of light falls out of luminous efficacy (**needed**), not a price table.
- The transitional cap in `EnergyPrices.sold` (a producer sells no dearer than its own technique costs) has to go when these demands exist, or delivery nodes will earn only their cost and no scarcity rent.

### 5.6 What replaces authored `rev_hours`

For each delivery node, `node_output.output_baskets` derives yearly delivered megajoules from the line capital's `annual_output_at_basis` (bounded also by staff hours), sells them at the delivered price, buys the generated energy at its price and the labour at wages. The node's revenue is delivered sales less generated energy bought and consumables, which is the wheeling margin and equals capital recovery plus wages when the price is at cost, and more when scarce. The typed `rev_hours` stays only for nodes that gate nothing (class d), which the audit already plans to zero.

Upkeep follows the same entries (poles replaced, copper theft and fault repair labour as a staff term), so `up_hours` no longer needs to be authored either.

## 6. Node by node

Generation nodes are class b and need no new delivery entry; they feed `electricity_generated_mj`. Rows give the entry the node would gate or the term it would improve.

| Node | Gates or improves |
|---|---|
| `el2_three_wire_distribution_system` | Gates the low-voltage DC distribution tier entry with the three-wire copper bill (about three eighths of two-wire copper at equal loss, derived). Replaces the two-wire tier |
| `el2_ring_main_distribution` | Gates a feeder-tier variant with two feed paths: availability term up, fault-repair labour down, same copper per MW-km |
| `el2_substation_voltage_regulation` | Gates the step-down capital (transformer plus regulator) in the AC distribution tier; reduces voltage-drop losses at the tail of a feeder |
| `el2_tap_changer_load_compensator` | Variant of the substation entry with a lower voltage-excursion loss and no manual attendant hours |
| `en_transformer` | Gates the AC tiers at all: transformer capital and its no-load and load loss term |
| `en_transmission_line` | Gates the high-voltage tier: line capital per km, loss fraction by voltage, reach band |
| `en_insulator`, `el2_insulator_pin_porcelain`, `el2_insulator_bushing` | Raise the maximum voltage a tier may carry (flashover limit); capital terms per km of line and per terminal |
| `en_substation` | Terminal plant for each tier, the term that couples tiers |
| `en_grid_interconnection` | Raises load diversity (annual output per tonne of plant) and enables reach beyond a single generating station |
| `en_power_factor_correction`, `el2_power_factor_correction_capacitor` | Cuts line current for the same real power: lowers the loss term and raises capacity per tonne of copper |
| `en_load_factor_diversity`, `el2_load_dispatch_and_scheduling` | Raise load factor, so more annual output from the same line capital; dispatch needs the telegraph (its existing prerequisite) |
| `el2_standardised_voltage_nominal`, `el2_standardised_frequency_nominal`, `en_frequency_standardisation` | Allow parallel running and interchangeable equipment: gate the interconnected variants; reduce the number of distinct plant types (capital per unit) |
| `el2_synchroscope_phase_angle_indicator` | Gates parallel operation of alternators (generation side variant, availability) |
| `en_switchgear`, `en_circuit_breaker`, `el2_circuit_breaker_thermal`, `el2_circuit_breaker_magnetic`, `en_fuse`, `el2_fuse_wire_element`, `el2_switch_knife`, `en_lightning_arrester`, `el2_lightning_arrestor_gap`, `el2_earthing_grounding_system` | Protection terms: availability and repair labour, plus a capital line item in each tier. Each node is a small input to the tier entry, not a seller (the audit may class several as d) |
| `el2_protective_relaying_differential` | Selective fault clearing: availability term in the ring-main and HV variants |
| `el2_meter_energy_kWh_meter` | Gates the metered entry (sale by energy) against the per-lamp entry; meter capital per customer and reading labour |
| `el2_meter_*` (other instruments) | Enabling; class d, no delivery entry |
| `el2_plug_socket_portable` | Connection capital per customer; enabling for small loads |
| `en_battery_lead_acid`, `en_battery_nickel_iron`, `en_battery_charging`, `en_pumped_storage`, `en_flywheel_storage` | Storage entries (carrier in, carrier out, round-trip loss); earn only with a time dimension |
| `el2_trolleybus_catenary_power`, `tr_electric_locomotive` | Buyers of delivered current; catenary is the last-mile line capital of a traction customer, which may be the same tier entry sized to the route |
| `el2_electroplating_and_electrorefining`, `el2_arc_welding_*`, `el2_resistance_welding_*`, `el2_induction_heating_*`, `el2_dielectric_heating_*`, `el2_electropolishing_*`, `el2_electrostatic_precipitation_*`, `el2_electric_lift_*`, `el2_electric_drill_*` | End use: entries that draw `electrical_mj`; their node revenue derives from the goods or services they sell once those entries exist (the audit classes most as d or b) |
| `el2_rectifier_mercury_arc`, `el2_rectifier_metal_layer`, `en_rotary_converter`, `el2_motor_rotary_converter_AC_DC` | Conversion between AC and DC with a loss; they let a DC consumer sit on an AC network (a conversion step in the delivery chain with its own capital and efficiency) |

## 7. Staged build plan

1. **Confirm the mechanism, change no behaviour.** Check that a good with no tree node (`electricity_generated_mj`) is accepted by the solver and the validator, and that a `reach_km` band can be added beside `temperature_reached_c`. Decide between the good and the fourth carrier. Output: a one-page decision in this report's follow-up. Test: `simulator.py validate` stays clean.
2. **Generated versus delivered, one tier.** Rename the generator outputs to `electricity_generated_mj`; add one on-site entry (no line, small loss, switchgear only) and one low-voltage DC distribution entry gated by `el2_three_wire_distribution_system`, with sourced copper and loss. Expect aluminium and other electrolytic prices to rise by the loss fraction; record before and after with the fingerprint. Move the two fastest-payback nodes to derived revenue.
3. **AC tiers and the transformer.** Entries for medium and high voltage gated by `en_transformer`, `en_transmission_line`, `en_substation`, insulator nodes; loss and copper per MW-km from section 4.1 with sourced current densities. The solver picks the cheapest tier at each band.
4. **Reach in geography.** Price the reach bands in the solver; have agents buy the band their distance clears (`sim/geography` distance). Households and firms far from a generator pay more.
5. **Demand side and removal of the cap.** Lamp-hour good for households; traction and motor consumers wired; delete the producer-sells-at-own-cost cap in `EnergyPrices.sold` for delivery lines once demand is in place.
6. **Operation terms.** Load factor and diversity through `annual_output_at_basis`; availability for protection and ring mains; reactive power; metering variants; storage entries with a time-of-day price. These are the nodes of section 6 that improve a term rather than gate a tier.
7. **Close the audit class.** Re-run the audit's payback diagnostic for class C_electricity; every node left on authored revenue is either class d (delete) or a documented gap.

Each stage ends with `simulator.py validate`, the stage's tests, and a fingerprint record and check so the change in behaviour is the intended one.

## 8. Relationship tests

Tests are written first (CLAUDE.md section 6) and assert relationships, never a dated price.

- **Distance:** with a fixed generator price, the delivered price of electrical_mj is non-decreasing in distance within one tier.
- **Voltage:** at a given distance and power, a higher-voltage tier has a lower loss fraction (inverse in voltage for fixed current density) and less copper per unit of capacity (inverse in voltage squared for fixed loss).
- **Tier crossover:** there is a distance beyond which a higher tier has the lower delivered price, and the solver picks it; before that distance it picks the lower tier.
- **Three-wire:** at equal power and equal loss fraction the three-wire entry's copper bill is three eighths of the two-wire entry's; the delivered price falls when the node is held.
- **Capital intensity:** delivered price falls as load factor rises (more annual output per unit of line capital); a fixed-capital line's price is insensitive to generator price only in proportion to its loss.
- **Earnings fall with capacity (agent economy layer):** hold demand fixed and add line capacity; the delivery node's yearly earnings per unit of capacity fall as the spot price falls toward cost. This lives in the market layer (`concern_volume.py` spot-over-incumbent factor), not in the cost-based solver, which prices at cost.
- **Metering:** the metered entry's delivered price per consumed megajoule is lower than the per-lamp entry's whenever the unmetered consumption multiplier exceeds the metered entry's extra capital and labour.
- **Power factor:** holding the power-factor node raises the capacity per unit copper and lowers loss for the same real power.
- **Consumer propagation:** raising the generator price or the loss fraction raises the price of aluminium by the electrical share of its cost, no more (checks that consumers read the delivered price).
- **No content ids:** a grep test that no engine file names `el2_` or `en_` nodes (CLAUDE.md 4.7).
- **Derived revenue:** for each gated node, `_revenue_basis` is `derived`, and the node's payback is longer than the quarter-year the audit flags.

## 9. Risks and open questions

- The solver prices electricity as an annual average; an hour-by-hour price (the real signal that earns storage its margin) needs the market layer to carry a time dimension, which stage 6 only approximates. Until then storage entries should stay unrevenued or be labelled heuristic.
- Capital per route is not capital per tier: a short line is cheaper than a long one. Pricing by band approximates this; the band widths are a design choice to measure, not a number to type.
- Fault and availability terms have no sourced rates yet. Do not type stand-ins without a 4.4 label.
- The meter's consumption multiplier is the most speculative figure; if no source is found, drop the unmetered entry and let the meter node be class d.
- Some `el2_` nodes the audit lists in class d (instruments, tubes, relays) are not part of this market and should not be given delivery entries to rescue their revenue.
- Web access here returned partial pages; figures tagged snippet should be re-read at source before they enter `data/`.
