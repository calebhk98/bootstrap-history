# Module 98: Power Plants

A parts bin, not a story. It covers 115 machines and fuels downstream of the basic prime movers in 93_energy.md, grouped into families: a Cornish boiler and a Lancashire boiler are the same idea taken one step further, not two inventions. Read a family once and you have every member.

One fact organises all of it: a steam engine does not require coal. Charcoal, peat, wood gas and oil all work, worse in specific ways, and charcoal is GROWN at roughly 0.75 tonnes per hectare per year of managed coppice (ESTIMATED, basis: standard European coppice yield). Every furnace is a claim on land before it is a claim on labour.

Cast iron, precision boring, and sustained furnace heat are assumed available through the metallurgy and precision chains (10_metallurgy.md, 40_power_precision.md). This module tells you what to build once you have them.

---

### en_undershot_wheel - Undershot water wheel

Also covers: en_treadwheel, en_horse_gin

**Why you would never guess this.** Undershot is struck by water's speed alone; most momentum splashes past unused, so efficiency is only 25-30 percent (MEASURED, Smeaton 1759). Horsepower is not a metaphor: Watt defined it from a horse sustaining about 500W all day; a man on a treadwheel sustains roughly 75W (MEASURED), so ten men replace two-thirds of a horse.

**Prerequisites.** cap_power_water / cap_power_muscle.

**Roman-available inputs.** Oak or elm wheel.

**Procedure.** Build paddle wheel geared to shaft on any stream.

**How you know it worked.** Shaft turns steadily under load.

**Failure modes.** Flood carries the wheel off.

**Cost & labour.** ESTIMATED 40-60 artisan-days.

**Danger.** Crush injuries from gearing.

**Confidence: HIGH** - Smeaton's figures are real measurements.

---

### en_overshot_wheel - Overshot water wheel

Also covers: en_breastshot_wheel, en_poncelet_wheel

**Why you would never guess this.** Overshot fills buckets at the top and uses water's WEIGHT, not speed, falling through nearly the whole diameter - roughly double undershot's efficiency, 60-80 percent (MEASURED, Smeaton). Breastshot, entering at axle height, is the compromise at about 70 percent where terrain won't give full drop. Poncelet curves the entry vanes tangentially, no impact shock, recovering another 10 percent with no added height.

**Prerequisites.** cap_power_water.

**Roman-available inputs.** Timber wheel; a surveyed millrace.

**Procedure.** Cut a leat delivering water above the wheel's top.

**How you know it worked.** Buckets fill and empty cleanly.

**Failure modes.** Ice stops the wheel.

**Cost & labour.** ESTIMATED: leat dominates cost, weeks of gang labour.

**Danger.** Falling into the wheel pit.

**Confidence: HIGH** - Smeaton's figures are the benchmark.

---

### en_penstock - Penstock and flume

Also covers: en_draft_tube, en_tide_mill

**Why you would never guess this.** An open flume leaks and freezes; a penstock (pressure pipe) delivers the same head through smaller cross-section, siting the machine away from the stream. A draft tube below a turbine recovers kinetic energy otherwise lost, adding effective head so a turbine can sit above tailwater where no wheel can. A tide mill is a wheel plus a pond and one-way sluice: the tide fills it, the gate shuts, the wheel runs on the controlled fall, running only about ten hours in twenty-four.

**Prerequisites.** cap_power_water; draft tube needs en_fourneyron_turbine; tide mill needs en_overshot_wheel.

**Roman-available inputs.** Lead sheet (plumbum) for lining.

**Procedure.** Lay pipe on the surveyed gradient; fit sluice gate.

**How you know it worked.** No hammer noise on sluice closure.

**Failure modes.** Penstock bursts from water hammer.

**Cost & labour.** ESTIMATED: months of masonry for a tide pond.

**Danger.** Burst penstock can knock a person down.

**Confidence: MEDIUM** - solid physics, gains are site-specific.

---

### en_fourneyron_turbine - Fourneyron turbine

Also covers: en_francis_turbine, en_pelton_wheel, en_kaplan_turbine

**Why you would never guess this.** Fixed guide vanes aim water before it strikes the runner, so the whole flow works continuously - a barrel-sized turbine matches a house-sized wheel. Which type you build is dictated by head: Fourneyron (radial outflow, 1827) suits medium head at 80+ percent (MEASURED); Francis (inward flow) suits a wide range at 85+ percent (MEASURED); Pelton (needle jet, split buckets) suits high head at 90+ percent; Kaplan (adjustable-pitch blades) suits low head, high volume, adapting to changing flow.

**Prerequisites.** cap_tol_10um, boring_mill; each type also needs the one before it.

**Roman-available inputs.** Bronze (aes, Cornish tin, Cypriot copper) for runner and vanes.

**Procedure.** Cast and machine guide vanes and runner to matching clearance.

**How you know it worked.** Shaft speed matches calculated design speed.

**Failure modes.** Cavitation pits the runner.

**Cost & labour.** ESTIMATED: hundreds of artisan-hours per unit.

**Danger.** A burst runner at speed is a shrapnel event.

**Confidence: MEDIUM** - efficiencies documented; tolerances are the open question.

---

### en_water_wheel_governor - Governor for water wheel

Also covers: en_centrifugal_governor

**Why you would never guess this.** An unregulated mill speeds up the instant load drops and can burst a stone. The governor is a physical feedback loop predating electronics: spinning weights fly outward as speed rises, and the linkage throttles the gate or, on Watt's identical steam version, the throttle valve. It "hunts" slightly around its setpoint because it only reacts after speed has already changed.

**Prerequisites.** en_overshot_wheel; steam version needs en_separate_condenser, cap_tol_100um.

**Roman-available inputs.** Bronze flyball weights.

**Procedure.** Gear a spindle to the shaft; hang weighted arms.

**How you know it worked.** Speed stays within a narrow band under changing load.

**Failure modes.** Linkage friction causes violent hunting.

**Cost & labour.** ESTIMATED: days for a smith and fitter.

**Danger.** A failed governor lets machinery run away.

**Confidence: HIGH** - Watt's governor is exceptionally well documented.

---

### en_post_mill - Post mill

Also covers: en_tower_mill

**Why you would never guess this.** In a post mill the whole timber body pivots on one post so a miller turns the building by hand - this caps size, since the post carries all weight and every gust's torque. A tower mill fixes the body and rotates only the cap on a bearing ring, allowing much greater height and cleaner wind, at the cost of a bearing carrying the cap's full weight without binding.

**Prerequisites.** cap_power_water (wind is treated as a power-capture prerequisite here).

**Roman-available inputs.** Oak frame; canvas sails (a mature Roman craft).

**Procedure.** Build pivoting body or fixed tower with rotating cap.

**How you know it worked.** Mill turns freely to face changing wind.

**Failure modes.** Post cracks under a broadside gust.

**Cost & labour.** ESTIMATED: weeks for post mill, months with masonry for tower.

**Danger.** Being struck by a moving sail is a recorded common cause of death.

**Confidence: HIGH** - well attested historical practice.

---

### en_patent_sail - Patent sail

Also covers: en_spring_sail, en_windmill_fantail

**Why you would never guess this.** Cloth sails must be reefed by hand on the arm in rising wind, dangerous and slow. Spring sail replaces cloth with spring-held shutters that open automatically once wind pressure exceeds the spring's setting. Patent sail links every shutter to one rod through the windshaft, so one lever, adjustable while running, sets the whole mill's power. The fantail applies the idea to orientation: a small crosswind rotor cranks the cap around to square the sails unattended.

**Prerequisites.** en_post_mill; fantail also needs en_tower_mill, cap_tol_100um.

**Roman-available inputs.** Iron shutter frames.

**Procedure.** Fit spring-tensioned shutters linked to a control rod.

**How you know it worked.** Shutters open in a gust and speed stays roughly constant.

**Failure modes.** Fatigued spring lets shutters flap.

**Cost & labour.** ESTIMATED: weeks per mill for precision ironwork.

**Danger.** Same sail-strike risk as the base mill.

**Confidence: HIGH** - Meikle and Cubitt's mechanisms are documented.

---

### en_wind_pump - Wind pump

Also covers: en_wind_electric

**Why you would never guess this.** A wind pump is a mill re-geared to a reciprocating pump crank, useful where there is no fall for a wheel - being intermittent, it needs a header tank exactly as wind-electric needs a battery. Wind electric couples the same mill through step-up gearing (a mill turns tens of rpm, a dynamo needs hundreds) to a dynamo, but the gearbox takes gust loads far beyond what a millstone drive was built for.

**Prerequisites.** en_post_mill; wind electric additionally needs dynamo.

**Roman-available inputs.** Bronze pump valves.

**Procedure.** Replace millstone drive with crank and pump rod to a header tank.

**How you know it worked.** Tank fills steadily.

**Failure modes.** Gearbox teeth shear in a gust.

**Cost & labour.** ESTIMATED: one to two weeks over an existing mill.

**Danger.** Crush hazard from moving rod and gearing.

**Confidence: MEDIUM** - gust-load durability is under-documented historically.

---

### en_atmospheric_engine - Atmospheric engine (Newcomen)

Also covers: en_double_acting

**Why you would never guess this.** This engine does not use steam pressure to move the piston, it uses ATMOSPHERIC pressure: near-atmospheric steam fills the cylinder, cold water condenses it to near-vacuum, and ordinary air (about ten tonnes per square metre) pushes the piston down. It is slow, four to twelve strokes a minute (MEASURED), because the cylinder reheats from cold every stroke. Double-acting fixes this: steam admitted alternately to both ends makes every stroke a power stroke, but the piston rod must pass sealed through one end, and that gland leaks constantly.

**Prerequisites.** cap_heat_1100, cap_tol_1mm, boring_mill.

**Roman-available inputs.** Cast iron cylinder (via the blast furnace chain, 10_metallurgy.md).

**Procedure.** Bore true cylinder, fit packed piston, fit boiler and beam linkage to pump rod.

**How you know it worked.** Piston completes full strokes and lifts water each cycle.

**Failure modes.** Packing leak loses vacuum.

**Cost & labour.** ESTIMATED: a skilled foundry crew, weeks.

**Danger.** LOW pressure, no explosion risk.

**Confidence: HIGH** - Newcomen's cycle is extremely well attested.

---

### en_high_pressure_engine - High pressure steam engine

Also covers: en_compound_engine, en_uniflow_engine

**Why you would never guess this.** Pushing with several atmospheres, instead of exploiting the one already free, makes an engine small enough to move itself - what made locomotives possible - but now a failed seam is a bomb, not a leak. Compound expands the same steam charge across two or three cylinders in series so no single wall swings through the whole temperature range, cutting fuel use roughly in half (ESTIMATED, basis: the widely cited 50 percent compounding gain). Uniflow pushes further: steam enters only at the ends and exhausts through mid-stroke ports, keeping the hot end always hot and the cold end always cold.

**Prerequisites.** cap_heat_1300, cap_tol_10um, boring_mill; compound needs en_separate_condenser; uniflow needs en_corliss_valve.

**Roman-available inputs.** Cast iron cylinder blocks.

**Procedure.** Bore high-precision cylinders.

**How you know it worked.** Steady speed under load, no valve chatter.

**Failure modes.** Boiler seam failure under pressure.

**Cost & labour.** ESTIMATED: a specialist crew for a season.

**Danger.** HIGH - never run without a working, unweighted safety valve.

**Confidence: HIGH** - compounding's fuel-saving figures are widely reported.

---

### en_steam_turbine_impulse - Impulse steam turbine (de Laval)

Also covers: en_steam_turbine_curtis, en_steam_turbine_reaction

**Why you would never guess this.** De Laval expanded the entire pressure drop in one fixed nozzle, producing a jet at the true molecular speed of steam - so the wheel must spin up to 30,000 rpm (MEASURED) and needs a reduction gear. Curtis splits that drop across two stages for usable speed. Parsons' reaction turbine uses 10-50 small stages, each blade row shaped like a nozzle so the reaction of steam leaving pushes the rotor - lower speed (about 3,000 rpm), no gearbox, the best efficiency, 85+ percent (MEASURED).

**Prerequisites.** cap_heat_1300, cap_tol_10um, boring_mill; Curtis and reaction build on en_steam_turbine_impulse.

**Roman-available inputs.** Bronze blading; cast iron casing.

**Procedure.** Machine nozzles to precise throat dimension.

**How you know it worked.** Rotor reaches design speed with no vibration.

**Failure modes.** Wet steam erodes blades rapidly.

**Cost & labour.** ESTIMATED: months for a specialist crew.

**Danger.** HIGH - rotational energy released at failure is catastrophic.

**Confidence: HIGH** - speeds and efficiencies are well documented.

---

### en_boiler_haystack - Haystack boiler

Also covers: en_boiler_wagon

**Why you would never guess this.** The haystack boiler, a domed brazed-copper vessel, holds only 2-3 atmospheres (MEASURED) before seams give way, and copper is expensive - exactly why pressure stayed near zero for steam's first century. Wagon boiler, a cylinder with one internal fire tube, is the next step, but its flat ends want to bulge under pressure and need heavy iron stay rods or they tear.

**Prerequisites.** cap_heat_1100, cap_tol_1mm.

**Roman-available inputs.** Copper sheet (haystack).

**Procedure.** Braze or rivet the shell; stay flat ends with iron rods.

**How you know it worked.** Holds steady pressure, no visible seam leak.

**Failure modes.** Seam brazing fails under thermal cycling.

**Cost & labour.** ESTIMATED: weeks of coppersmith work.

**Danger.** HIGH even at low pressure - a sudden seam failure sprays scalding steam.

**Confidence: HIGH** - the best-documented earliest boiler forms.

---

### en_boiler_cornish - Cornish boiler

Also covers: en_boiler_lancashire, en_boiler_locomotive

**Why you would never guess this.** Cornish runs one large fire-tube through the water-filled shell for more heated surface; Lancashire doubles that to two tubes. Locomotive boiler compresses the idea further: hundreds of small tubes carry hot gas through the water, packing huge surface into a portable shell - but a flat crown sheet sits above the fire holding back the water, and if the level drops below it, the dry iron overheats and fails, releasing the boiler's contents into the fire instantly.

**Prerequisites.** en_boiler_wagon, cap_tol_10um.

**Roman-available inputs.** Wrought iron plate and rivets.

**Procedure.** Fit one or two internal fire tubes, or a firebox with crown sheet and small-tube bank.

**How you know it worked.** Gauge shows a stable water level.

**Failure modes.** Crown sheet failure from low water ("blew its crown") is the classic explosion cause.

**Cost & labour.** ESTIMATED: a specialist boilershop for months.

**Danger.** HIGH - the fusible plug melts and vents steam before the iron fails catastrophically.

**Confidence: HIGH** - crown sheet failure is well documented.

---

### en_boiler_water_tube - Water tube boiler

Also covers: en_boiler_babcock, en_boiler_stirling

**Why you would never guess this.** This inverts the fire-tube idea: water sits inside many small tubes, fire outside. A pressurised tube is in tension, and a thin-walled small tube resists tension far better per unit weight than a large shell resists the same pressure - so water-tube boilers run higher pressure on less metal, and one tube's failure vents only a small amount of water, not the whole vessel. Babcock and Wilcox uses straight, easily inspected tubes between headers. Stirling coils the tubes for a compact, high-surface boiler, at the cost of uneven heating.

**Prerequisites.** cap_tol_10um, boring_mill.

**Roman-available inputs.** Bronze and cast iron headers.

**Procedure.** Expand tube ends into headers for a sealed joint.

**How you know it worked.** Holds high pressure with only minor weeping.

**Failure modes.** A single tube fails from scale, a violent local jet, not a full explosion.

**Cost & labour.** ESTIMATED: a specialist crew for a season.

**Danger.** MEDIUM relative to fire-tube boilers - a safer failure mode.

**Confidence: HIGH** - textbook pressure vessel engineering.

---

### en_separate_condenser - Separate condenser (Watt)

Also covers: en_condenser_jet, en_condenser_surface

**Why you would never guess this.** The win is not condensing the steam, the atmospheric engine already did that. The win is the cylinder no longer being cooled and reheated every stroke: the cold-water jet that condenses steam also chills the cylinder, so fresh steam next stroke condenses uselessly re-warming the metal before doing work - Watt measured this waste at roughly three-quarters of the fuel. A separate vessel keeps the cylinder hot, the condenser cold. Jet condenser sprays water directly in, fast but unrecyclable. Surface condenser condenses on cold tubes so steam and water never mix, letting a ship recycle its own boiler water.

**Prerequisites.** en_atmospheric_engine, cap_tol_10um.

**Roman-available inputs.** Copper or brass tubes.

**Procedure.** Build a vacuum-tight vessel connected by valve to the cylinder.

**How you know it worked.** Fuel use per stroke drops sharply.

**Failure modes.** Air leaking through a gland ruins the vacuum.

**Cost & labour.** ESTIMATED: a coppersmith and fitter, weeks per unit.

**Danger.** LOW physically; socially this was Watt's most fiercely litigated patent (1769-1800).

**Confidence: HIGH** - the fuel-waste figure is Watt's own.

---

### en_expansive_working - Expansive working (cutoff)

Also covers: en_cutoff_valve, en_corliss_valve

**Why you would never guess this.** Shutting the inlet valve early and letting trapped steam expand on its own throttles fuel more steeply than power, a roughly 20 percent efficiency gain (MEASURED). A simple cutoff valve sets one fixed point. The Corliss valve refines this into four independent trip-cam valves so cutoff adjusts smoothly while running - but every face must be flat to a hair's width or it leaks exactly the pressure the mechanism exists to save.

**Prerequisites.** en_high_pressure_engine; Corliss additionally needs cap_tol_10um.

**Roman-available inputs.** Bronze valve faces.

**Procedure.** Fit a slide or trip valve with adjustable cutoff.

**How you know it worked.** Fuel use falls as cutoff shortens.

**Failure modes.** Valve seat wear reintroduces leakage.

**Cost & labour.** ESTIMATED: weeks per engine for Corliss gear.

**Danger.** LOW beyond the base engine's own pressure hazard.

**Confidence: HIGH** - the 20 percent gain is standard.

---

### en_economiser - Economiser

Also covers: en_feedwater_heater, en_superheater

**Why you would never guess this.** Three ways to catch heat about to be thrown away. An economiser, a tube bank in the flue after the boiler, saves 15-20 percent of fuel (MEASURED) essentially for free. A feedwater heater warms cold water on its way INTO the boiler using waste steam, saving another 10-15 percent (MEASURED). A superheater raises steam temperature further without adding pressure or moisture - dry steam does more work and does not erode turbine blades the way wet steam does.

**Prerequisites.** en_separate_condenser.

**Roman-available inputs.** Cast iron flue tubes.

**Procedure.** Route a tube bank through the flue.

**How you know it worked.** Chimney gas feels cooler by hand-test.

**Failure modes.** Superheater tubes scale and oxidise fastest of anything in the boiler.

**Cost & labour.** ESTIMATED: days to weeks as an extension.

**Danger.** MEDIUM - superheated steam burns are worse, being invisible.

**Confidence: HIGH** - all three figures are widely cited.

---

### en_safety_valve - Safety valve (pop-off)

Also covers: en_pressure_gauge, en_steam_trap

**Why you would never guess this.** Three instruments answering what is happening inside a sealed vessel. The safety valve, weighted to lift at a set pressure, is the single most important safety device of the steam age; one weighted down for more power, a common lethal shortcut, is a bomb on a schedule. The pressure gauge (a curved tube that tries to straighten under pressure) is the only way to know what pressure a vessel holds. The steam trap drains condensed water while holding steam back; without it, a rush of steam can slam pooled condensate down the pipe, bursting fittings.

**Prerequisites.** en_high_pressure_engine (valve); cap_measure_temp, cap_tol_100um (gauge).

**Roman-available inputs.** Bronze valve body and spring.

**Procedure.** Fit a valve calibrated below rated pressure; fit a Bourdon-tube gauge.

**How you know it worked.** Valve lifts cleanly at the marked pressure.

**Failure modes.** A tied-down safety valve is the classic explosion cause.

**Cost & labour.** ESTIMATED: days per set.

**Danger.** HIGH - most historical boiler explosions trace to exactly this failure.

**Confidence: HIGH** - the causal link is well documented.

---

### en_parallel_motion - Parallel motion linkage (Watt)

Also covers: en_sun_planet_gear, en_reduction_gear

**Why you would never guess this.** A beam engine's piston rod moves straight, but the beam's far end swings in an arc - Watt's rhomboid linkage constrains that path straight using only pivoted rods, his favourite invention. Sun-and-planet gear exists because Watt could not use a crank (patented by Pickard): a planet gear walks around a fixed sun gear, converting motion to rotation around the patent. Reduction gear steps turbine speeds of 5,000-30,000 rpm down to the 10-500 rpm machinery wants, each mesh losing about 2 percent to friction (MEASURED).

**Prerequisites.** en_double_acting, cap_tol_100um; reduction gear needs en_steam_turbine_impulse, cap_tol_10um.

**Roman-available inputs.** Iron linkage rods.

**Procedure.** Fabricate the linkage to measured beam geometry.

**How you know it worked.** Piston rod travels visibly straight, no side-load wear.

**Failure modes.** Worn pins let the rod side-load.

**Cost & labour.** ESTIMATED: weeks per set, a specialist trade.

**Danger.** LOW, standard moving-machinery hazards.

**Confidence: HIGH** - all three are exceptionally well documented.

---

### en_turbine_blading - Turbine blade design and profile

Also covers: en_turbine_condenser_vacuum

**Why you would never guess this.** With hundreds of identical blades on one rotor, even a 1 percent profile deviation costs roughly 5 percent of overall efficiency (ESTIMATED, basis: standard turbomachinery tolerance sensitivity), and sets up fatiguing vibration. A turbine's exhaust benefits from a hard vacuum, 0.05-0.1 atmosphere (MEASURED), since every extra 0.1 atmosphere extracts roughly another 5 percent of available work (MEASURED) - but air leaking through a shaft gland destroys that vacuum as fast as the pump removes it.

**Prerequisites.** cap_tol_10um, boring_mill; vacuum system needs en_steam_turbine_reaction, cap_vac_1torr.

**Roman-available inputs.** Bronze blade stock.

**Procedure.** Machine each blade to a master template.

**How you know it worked.** No audible vibration at full speed.

**Failure modes.** A fatigue crack gives no warning until sudden failure.

**Cost & labour.** ESTIMATED: months per set, the most demanding precision task here.

**Danger.** HIGH - a burst rotor disc at speed is lethal nearby.

**Confidence: MEDIUM** - solid physics; the sensitivity figure is a rule of thumb.

---

### en_four_stroke_cycle - Four-stroke cycle (Otto)

Also covers: en_two_stroke_cycle, en_gas_engine

**Why you would never guess this.** Firing once every two revolutions sounds wasteful, but it lets you compress the fuel-air mixture first, and a compressed charge burns faster with far higher peak pressure, 50-100 psi (MEASURED), than any steam stroke. Two-stroke fires every revolution using the piston to uncover ports, roughly doubling power, but fresh charge and exhaust briefly mix, so unburnt fuel escapes. The coal gas engine is the same cycle burning coal gas, ignited by an external heated tube - only 20 percent efficient (MEASURED) but simple and reliable, history's first commercially successful internal combustion engine.

**Prerequisites.** cap_heat_1100, cap_tol_1mm, boring_mill.

**Roman-available inputs.** Cast iron cylinder block.

**Procedure.** Bore the cylinder close-tolerance.

**How you know it worked.** Smooth running, regular even firing by ear.

**Failure modes.** Timing drift fires against a closing exhaust valve.

**Cost & labour.** ESTIMATED: weeks to months per engine.

**Danger.** MEDIUM - a flawed cylinder's explosion is violent but contained.

**Confidence: HIGH** - figures are well documented.

---

### en_hot_bulb_engine - Hot bulb engine

Also covers: en_carburetted_engine, en_compression_ignition

**Why you would never guess this.** Three ways to ignite fuel with no spark. Hot bulb ignites fuel by dripping it onto a bulb glowing from the previous cycle's own combustion, 25 percent efficient (MEASURED). Carburetted engine draws fuel into the airstream by suction in a narrowing throat, working only because petrol evaporates readily. Compression ignition uses no spark: air compressed 15:1 versus 8:1 for a spark engine (MEASURED) reaches 500°C+ and ignites injected fuel on contact, the best of the three, 40 percent (MEASURED).

**Prerequisites.** cap_heat_1100-1300; cap_tol_1mm (hot bulb, carburettor) or cap_tol_10um, boring_mill (compression ignition).

**Roman-available inputs.** Cast iron cylinder and bulb.

**Procedure.** Fit a glowing bulb chamber, or a Venturi and float chamber.

**How you know it worked.** Reliable restart from a warm bulb or cold-cranking.

**Failure modes.** Hot bulb goes cold and won't restart.

**Cost & labour.** ESTIMATED: hot bulb simplest, compression ignition most demanding.

**Danger.** MEDIUM to HIGH depending on type.

**Confidence: HIGH** - all three figures are well documented.

---

### en_poppet_valve - Poppet valve and camshaft

Also covers: en_sleeve_valve, en_fuel_injection

**Why you would never guess this.** A camshaft geared to the crank opens each valve at exactly the right instant - but the valve head runs red-hot and can stick or burn. Sleeve valve avoids that: a sliding sleeve has ports lining up with the cylinder's own, quieter, but clearance must be tiny or it leaks compression. Fuel injection replaces a carburettor's suction with a pump forcing fuel at 200+ atmospheres (MEASURED) into 10-100 micron droplets, timed to within one degree of crank rotation.

**Prerequisites.** en_four_stroke_cycle, cap_tol_100um; sleeve valve and injection need cap_tol_10um; injection needs en_compression_ignition.

**Roman-available inputs.** Bronze valve seats.

**Procedure.** Cut cam profiles to required timing.

**How you know it worked.** Quiet valve train.

**Failure modes.** Spring fatigue lets a valve float and strike the piston.

**Cost & labour.** ESTIMATED: weeks for valve gear.

**Danger.** MEDIUM, moving-machinery and high-pressure fuel hazards.

**Confidence: MEDIUM-HIGH** - injection pressure at Roman tooling is open.

---

### en_supercharger - Supercharger (mechanically driven)

Also covers: en_turbocharger

**Why you would never guess this.** Both raise power 30-50 percent (MEASURED) by forcing extra air into the cylinder, but draw the energy from opposite places. A supercharger, belt-driven off the crankshaft, steals engine output to run. A turbocharger spins a wheel in the exhaust instead, at no direct cost - but its bearing must survive over 800°C continuously (MEASURED), and boost lags the throttle.

**Prerequisites.** en_poppet_valve, cap_tol_10um; turbocharger also needs en_compression_ignition.

**Roman-available inputs.** Cast iron rotor housing.

**Procedure.** Fit a rotor compressor geared to the crank, or to an exhaust turbine wheel.

**How you know it worked.** Measurable power increase at the same fuel setting.

**Failure modes.** Over-boost causes knock.

**Cost & labour.** ESTIMATED: turbocharger bearing materials are the harder build.

**Danger.** MEDIUM, exhaust-side components burn on contact.

**Confidence: MEDIUM** - turbocharger bearing life is uncertain.

---

### en_stirling_engine - Stirling hot air engine

Also covers: en_compressed_air_engine, en_spring_motor

**Why you would never guess this.** In a Stirling engine, air shuttles between hot and cold ends via a displacer, with a regenerator recapturing heat each pass - the heat source is OUTSIDE the working gas, so it runs on any fuel, but real efficiency is only about 25 percent (MEASURED) against a theoretical 40, since gas-to-metal heat transfer is slow. Compressed air engine has no combustion: air compressed elsewhere expands adiabatically, so efficiency is only 40-50 percent. Spring motor stores mechanical energy wound before use, useless for sustained work.

**Prerequisites.** cap_heat_1100, cap_tol_100um; compressed air needs cap_power_steam, cap_tol_1mm; spring motor needs cap_tol_1mm.

**Roman-available inputs.** Cast iron cylinders.

**Procedure.** Build linked hot/cold cylinders with displacer and regenerator, or a storage vessel and expansion cylinder.

**How you know it worked.** Stirling runs continuously on steady heat.

**Failure modes.** Regenerator clogs, killing efficiency silently.

**Cost & labour.** ESTIMATED: Stirling is a demanding fit, weeks.

**Danger.** LOW, the safest cluster in this module.

**Confidence: HIGH** - all three are well documented.

---

### en_gas_turbine - Gas turbine (Brayton cycle)

Also covers: en_jet_engine, en_rocket_motor, en_liquid_propellant

**Why you would never guess this.** A gas turbine compresses air through ten or more stages (MEASURED) and burns fuel continuously rather than in pulses - combustor temperature runs above 900°C continuously (MEASURED), demanding nickel alloys that hold strength far longer than bronze or iron. A jet engine extracts only enough turbine power to drive its compressor and expands the rest out a nozzle for thrust, sensible only at high speed and altitude. A rocket carries its own oxidiser, burning at 2000-3000°C (MEASURED). Liquid propellant systems pump fuel and oxidiser at a matched ratio, and a practical oxidiser demands corrosion resistance no ordinary iron or bronze survives.

**Prerequisites.** cap_heat_1600, cap_tol_10um, boring_mill; jet needs en_gas_turbine; rocket needs cap_heat_2000; liquid propellant needs en_rocket_motor.

**Roman-available inputs.** None of the core alloys are Roman-native.

**Procedure.** Depends entirely on capability nodes (cap_heat_1600-2000) documented elsewhere.

**How you know it worked.** Sustained combustion at rated temperature without blade creep.

**Failure modes.** Blade creep at sustained high temperature.

**Cost & labour.** ESTIMATED: beyond ordinary accounting, a dedicated research programme.

**Danger.** HIGH - uncontained failure at these temperatures is instantly lethal nearby.

**Confidence: LOW-MEDIUM** - materials and tolerances are uncertain here.

---

### en_alternator - Alternator (AC generator)

Also covers: en_commutator, en_dynamo, en_exciter, en_three_phase_gen

**Why you would never guess this.** Every rotating generator does the same thing (a coil moving through a field has voltage induced, proportional to speed); this family is about what you do with that voltage afterward. An alternator brings raw output straight to slip rings unmodified, voltage and frequency both scaling with speed. A commutator, a split ring reversing the connection each half-turn, converts the same voltage into pulsating DC - its brushes wear and arc constantly. A dynamo is a self-exciting commutator generator. An exciter supplies adjustable field current. Three-phase generation staggers three coils around the rotor, smoothing torque ripple.

**Prerequisites.** cap_tol_10um, cap_power_steam; dynamo needs the existing dynamo tech; others build on en_alternator.

**Roman-available inputs.** Copper wire, drawn fine for windings.

**Procedure.** Wind coils on a rotating armature.

**How you know it worked.** A test lamp lights steadily as the shaft turns.

**Failure modes.** Commutator brush wear causes sparking then loss of contact.

**Cost & labour.** ESTIMATED: weeks per machine, slow skilled winding.

**Danger.** Electrical burns and fire from shorted windings.

**Confidence: HIGH** - textbook electromagnetism.

---

### en_battery_lead_acid - Lead acid storage battery

Also covers: en_battery_nickel_iron

**Why you would never guess this.** Lead-acid uses lead and lead oxide plates in sulfuric acid, 2V per cell (six cells for 12V), 80-90 percent round-trip efficiency (MEASURED) - but overcharging boils the acid, releasing hydrogen and oxygen, a real explosion risk near flame. Nickel-iron is pricier but far more abuse-tolerant, lasting 5,000+ cycles (MEASURED) against a few hundred, at lower voltage per cell (1.2V) and faster idle self-discharge.

**Prerequisites.** cap_tol_100um; nickel-iron also needs mat_nickel.

**Roman-available inputs.** Lead (plumbum, Britain, Spain).

**Procedure.** Cast differing lead plates; assemble in an acid-resistant case.

**How you know it worked.** A cell holds measurable voltage for hours.

**Failure modes.** Overcharge gassing is a fire hazard.

**Cost & labour.** ESTIMATED: days per battery bank.

**Danger.** Sulfuric acid burns skin and eyes.

**Confidence: HIGH for lead-acid**; **LOW for nickel-iron** - pure nickel supply is the constraint.

---

### en_battery_charging - Battery charging system

Also covers: en_rotary_converter

**Why you would never guess this.** Charging voltage must sit just above the battery's own voltage plus wiring drop, and shifts with temperature, so a setting right in summer overcharges in winter. A rotary converter is an older answer to producing DC from AC with no separate rectifier: a synchronous motor and DC generator on one shaft - elegant, but has no starting torque and must be brought to speed some other way.

**Prerequisites.** en_battery_lead_acid, en_alternator; rotary converter needs en_three_phase_gen.

**Roman-available inputs.** Bronze rheostat contacts.

**Procedure.** Fit adjustable resistance in series.

**How you know it worked.** Full charge with no excessive gassing or heat.

**Failure modes.** Thermal runaway if voltage isn't adjusted for a hot room.

**Cost & labour.** ESTIMATED: a fitter's afternoon to set up.

**Danger.** Same acid and gas hazards as the battery.

**Confidence: MEDIUM** - exact set points are cell-specific.

---

### en_transmission_line - Transmission line (high voltage power cable)

Also covers: en_insulator, en_transformer

**Why you would never guess this.** Power lost in a wire scales with the CURRENT SQUARED times resistance, so doubling voltage halves current and cuts losses to a quarter - the entire reason lines run at 10-100 kV (MEASURED). A transformer, two coils sharing an iron core, steps voltage up for the line and down at the far end. An insulator, typically porcelain, is shaped to lengthen the surface path leakage current must cross, since a straight air gap alone is not enough once the line is dirty or wet.

**Prerequisites.** en_alternator, cap_tol_100um; transformer needs motor_transformer_ac.

**Roman-available inputs.** Stranded copper cable.

**Procedure.** String conductor on porcelain insulators.

**How you know it worked.** No hissing or visible corona at night.

**Failure modes.** Insulator contamination causes flashover.

**Cost & labour.** ESTIMATED: copper cost dominates, scaling with distance.

**Danger.** HIGH - tens of kilovolts kills instantly.

**Confidence: HIGH** - the I-squared-R relationship is basic physics.

---

### en_switchgear - Switchgear (high voltage switch)

Also covers: en_circuit_breaker, en_fuse, en_lightning_arrester

**Why you would never guess this.** The instant contacts separate under load, current tries to keep flowing as an arc hot enough to weld them if not extinguished fast. Switchgear handles routine switching, oil-immersed to quench the arc. A circuit breaker does this automatically and, unlike a fuse, resets, but must interrupt fault currents of thousands of amps. A fuse melts at a known current after a delay, sacrificing itself once. A lightning arrester is a spark gap breaking down only above a surge voltage, then must stop conducting or it becomes a permanent short.

**Prerequisites.** en_transmission_line, cap_tol_100um; circuit breaker needs en_switchgear.

**Roman-available inputs.** Silver alloy fuse wire (argentum, Spain).

**Procedure.** Build oil-immersed contacts sized to fault current.

**How you know it worked.** A test trip interrupts a simulated fault cleanly.

**Failure modes.** Switchgear oil carbonises from repeated arcing.

**Cost & labour.** ESTIMATED: days per unit for a specialist fitter.

**Danger.** HIGH, same order as the transmission line itself.

**Confidence: MEDIUM-HIGH** - interrupting capacity depends on build quality.

---

### en_substation - Substation (transformer station)

Also covers: en_grid_interconnection, en_frequency_standardisation, en_power_factor_correction, en_load_factor_diversity

**Why you would never guess this.** A substation steps transmission voltage (order 50 kV) down to distribution (order 10 kV) then to building level (roughly 400V), meshed rather than chained: if one fails, power reroutes. Frequency standardisation, settling on 50 or 60 Hz (MEASURED), exists because every generator on a shared grid must spin in exact lockstep. Power factor correction cancels lagging current from motor loads with capacitor banks. Load factor and diversity management is an accounting fact: real systems run at only 70-90 percent (MEASURED) of the sum of every individual peak.

**Prerequisites.** en_switchgear, en_transformer; the other three build on en_substation.

**Roman-available inputs.** Steel plate housing.

**Procedure.** House step-down transformers, switchgear, and protection together.

**How you know it worked.** Voltage across town stays within a narrow band.

**Failure modes.** Transformer oil overheats and can rupture catastrophically.

**Cost & labour.** ESTIMATED: a season's work, the largest single distribution project.

**Danger.** HIGH, combining every transformer and switchgear hazard at scale.

**Confidence: MEDIUM** - 50/60 Hz is a period convention.

---

### en_hydroelectric_station - Hydroelectric power station

Also covers: en_thermal_station

**Why you would never guess this.** A hydroelectric station couples a turbine to an alternator behind a dam; efficiency is about 90 percent (MEASURED), since there is no combustion step to lose heat in. A thermal, coal-fired station chains boiler to turbine to alternator, and losses compound - boiler around 80 percent, turbine around 40 percent, overall only about 32 percent (MEASURED) - most fuel energy leaves as low-grade heat in the cooling water.

**Prerequisites.** Hydro: en_francis_turbine, en_alternator, en_substation. Thermal: en_steam_turbine_reaction, en_alternator, en_substation.

**Roman-available inputs.** Stone for dam and powerhouse.

**Procedure.** Build dam and reservoir.

**How you know it worked.** Substation output matches calculated capacity under steady load.

**Failure modes.** Reservoir silting reduces effective head over time.

**Cost & labour.** ESTIMATED: the largest capital project in this module, years of labour.

**Danger.** Dam failure is catastrophic and mass-casualty.

**Confidence: HIGH** - both efficiency figures are well documented.

---

### en_flywheel_storage - Flywheel energy storage

Also covers: en_pumped_storage

**Why you would never guess this.** A flywheel stores energy rising with the SQUARE of both radius and speed - why a burst flywheel is so dangerous, that energy has to go somewhere instantly. It smooths only seconds of power ripple, not hours. Pumped storage does the opposite: a reversible turbine-pump lifts water uphill when power is surplus and lets it fall back when needed, round-trip efficiency about 75 percent (MEASURED), needing a real elevation difference, 100 metres typical (MEASURED) - but able to store a city's worth of energy for hours or days.

**Prerequisites.** Flywheel: cap_tol_100um, cap_power_steam. Pumped storage: en_hydroelectric_station.

**Roman-available inputs.** Cast iron flywheel rim, inspected before mounting.

**Procedure.** Cast and inspect the rim for flaws.

**How you know it worked.** Flywheel visibly smooths speed fluctuation between strokes.

**Failure modes.** A hidden casting flaw at speed flings the rim apart.

**Cost & labour.** ESTIMATED: weeks for casting and balancing.

**Danger.** Flywheel failure is HIGH and hard to predict in advance.

**Confidence: HIGH** - basic, well established physics for both.

---

### en_hydraulic_accumulator - Hydraulic accumulator

Also covers: en_hydraulic_power_main

**Why you would never guess this.** A steady pump charges an accumulator, a weighted piston storing pressurised water, smoothing output into pressure available on demand - the precharge air or weight acts like a spring. A hydraulic power main extends this the way a grid extends a generator: cast iron pipes at 600-1000 psi (MEASURED, the real historical London and Manchester networks ran this pressure) run to remote actuators, simpler and quieter than belts and shafting.

**Prerequisites.** cap_heat_1100, cap_tol_100um; power main needs en_hydraulic_accumulator.

**Roman-available inputs.** Cast iron pipe (continuing lead-pipe aqueduct plumbing, 85_transport_civil.md).

**Procedure.** Fit a weighted piston accumulator downstream of the pump.

**How you know it worked.** Pressure at the far end stays in useful range.

**Failure modes.** A burst main floods streets and cuts every downstream actuator.

**Cost & labour.** ESTIMATED: a season's crew, pipe-laying dominates cost.

**Danger.** A burst main can knock a person down.

**Confidence: HIGH** - the London and Manchester networks are documented.

---

### en_charcoal_burning - Charcoal production by burning

Also covers: en_peat_fuel, en_coal_mining_washing

**Why you would never guess this.** A steam engine does not need coal. Charcoal is GROWN, not mined: managed coppice yields roughly 0.75 tonnes of wood per hectare per year (ESTIMATED, basis: standard European coppice yield), so an ironworks needs thousands of hectares of forest behind it, a land commitment, not a supply contract. Burning wood in a covered clamp leaves charcoal at about 25 percent of the original weight (MEASURED). Peat delivers only about half of coal's energy per weight (MEASURED), needing no mining. Coal washing still leaves 5-15 percent ash (MEASURED).

**Prerequisites.** cap_heat_1100; coal mining needs mining_concession.

**Roman-available inputs.** Managed coppice (established Roman practice, 75_agriculture_food.md).

**Procedure.** Stack cut wood in an earth-covered clamp with a controlled vent; air-dry peat a season.

**How you know it worked.** Charcoal rings and breaks with a clean fracture.

**Failure modes.** A clamp catching full fire burns the yield to ash.

**Cost & labour.** ESTIMATED: days per batch.

**Danger.** Carbon monoxide poisoning tending a clamp.

**Confidence: HIGH** - coppice yield figures are standard.

---

### en_coke_oven - Coke oven (beehive or by-product)

Also covers: en_town_gas_retort, en_gas_holder, en_gas_producer

**Why you would never guess this.** Heating coal or wood without enough air releases gas while what remains concentrates into cleaner solid fuel. A beehive oven wastes that gas; a by-product oven captures tar, ammonia, and gas for sale, leaving hotter, cleaner coke. Town gas retort takes the gas itself as product: coils condense tar, water absorbs ammonia (recovered with lime), leaving a fuel mix for piped lighting - the process burns roughly 1.5 times as much coal-energy as the gas delivers (ESTIMATED, basis: typical historical retort accounting). A gas holder stores it under a floating bell in a water seal. A gas producer fuels an engine on site.

**Prerequisites.** coal_coke (oven); en_coke_oven (retort); en_town_gas_retort (holder); cap_heat_1100 (producer).

**Roman-available inputs.** Coal or wood feedstock.

**Procedure.** Heat coal in a sealed chamber collecting gas; scrub through water to strip ammonia.

**How you know it worked.** Coke rings clean and grey when struck.

**Failure modes.** Gas leaks are an odourless carbon monoxide risk.

**Cost & labour.** ESTIMATED: months to build a gasworks, ongoing skilled labour to run.

**Danger.** HIGH - carbon monoxide poisoning and gas explosion are well documented hazards.

**Confidence: HIGH** - coking and town gas manufacture are documented.

---

### en_oil_drilling - Oil drilling and production

Also covers: en_oil_shale_retorting, en_oil_refining_distillation, en_oil_cracking

**Why you would never guess this.** A cable-tool rig, a heavy bit repeatedly dropped, is simple but slow; a rotary rig with circulating mud, which cools the bit and holds back the pressure it's about to hit, is faster but complex - either way, an uncontrolled pocket can blow the rig back up the hole. Oil shale retorting heats shale to 500-600°C (MEASURED), yielding only 10-15 percent by weight (MEASURED). Refining separates crude by boiling point in a column of bubble trays; clean separation between cuts is difficult. Cracking breaks heavy molecules into shorter, valuable ones, but the furnace cokes internally.

**Prerequisites.** cap_power_steam, cap_heat_1100 (drilling); en_oil_drilling, destructive_distillation (refining); en_oil_refining_distillation (shale, cracking).

**Roman-available inputs.** Iron bar for drill string.

**Procedure.** Sink a well by cable-tool or rotary rig with mud.

**How you know it worked.** Distinct fractions collect at different tray levels.

**Failure modes.** A drilling blowout is sudden and violent.

**Cost & labour.** ESTIMATED: a season's crew for drilling, more for refining.

**Danger.** HIGH for drilling (blowout, fire) and cracking furnaces (vapour leaks).

**Confidence: MEDIUM** - deep rotary drilling here is uncertain.

---

### en_petrol - Petrol (gasoline) production

Also covers: en_kerosene, en_fuel_oil, en_lubricating_oil

**Why you would never guess this.** Four cuts from one refining process, each suited to a job purely by boiling range. Petrol, the lightest, suits spark engines because it vaporises quickly, but that volatility makes its vapour dangerously easy to ignite at a distance. Kerosene was refined for lighting, needing careful flash-point and purity control. Fuel oil, the heavy end, is cheap but so viscous it must be heated to pump in cold weather. Lubricating oil is not a fuel: viscosity matches the duty, light for fast machinery, heavy for slow.

**Prerequisites.** en_oil_refining_distillation for all four.

**Roman-available inputs.** Refined crude oil fractions.

**Procedure.** Draw the desired cut from the column; test flash point at a safe distance.

**How you know it worked.** Petrol ignites readily from a spark at safe distance.

**Failure modes.** Petrol vapour pooling and igniting from a spark yards away.

**Cost & labour.** ESTIMATED: days per batch once the refining column exists.

**Danger.** Petrol vapour is the most acutely dangerous substance in this module.

**Confidence: HIGH** - refining fractions are well documented.

---

## Sources and confidence

Water wheel and turbine efficiency figures trace to Smeaton's 1759 experiments and documented nineteenth-century turbine trials, HIGH confidence. Steam, boiler, and internal combustion figures (Newcomen's stroke rate, Watt's fuel-waste measurement, compression ratios, economiser and turbine gains) are standard, widely cited, HIGH throughout. Electrical distribution figures (transmission voltage, diversity factor, battery cycle life) are HIGH to MEDIUM, documented but sometimes design-specific rather than universal. The charcoal coppice yield and town-gas energy-accounting figures are flagged ESTIMATED with stated basis. The gas turbine, jet, and rocket cluster is LOW-MEDIUM: textbook physics, but whether the needed nickel alloys and tolerances are reachable from this tree's earlier metallurgy is genuinely open. No number here lacks a MEASURED, ESTIMATED, or DERIVED basis.

## Where to go next

- [93_energy.md](93_energy.md) - the base prime movers and fuels this module extends.
- [10_metallurgy.md](10_metallurgy.md) - cast iron, precision casting, and the alloys many entries depend on.
- [40_power_precision.md](40_power_precision.md) - the boring mills and tolerance chains referenced throughout as prerequisites.
- [30_glass_optics.md](30_glass_optics.md) - porcelain and precision ceramic firing, relevant to insulators and rocket nozzle linings.
