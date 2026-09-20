# Module 86: Transport, Deep Systems

You already have the railway idea. Module 85 gives the freight arithmetic; Module 92 gives the flanged wheel, the boiler, the sternpost rudder, the differential. None of it runs on its own. A locomotive is not one invention, it is roughly two hundred small ones, and the one you skipped because it looked boring next to the boiler is the one that derails your train. This module is the two hundred and eleven boring ones, grouped into forty-six clusters by mechanism, since most are the same idea applied to a slightly different joint. Each section names one representative id and lists the others it covers under "Also covers"; check every id there before assuming something is missing. Entries are compressed: the kernel and the failure mode are the point, everything else is a phrase. A machine built from Roman-quality parts at Roman tolerances fails in Roman ways, and a magistrate will read a railway or a submarine as a military asset before he reads it as transport.

---

### tl_differential - Differential (bevel gears)

Also covers: tl_live_axle, tl_dead_axle, tl_propshaft, tl_universal_joint

**Kernel.** Without a differential the inside wheel scrubs on every corner, or the axle winds up and snaps; a cart's wheels spin free on the axle for this reason, but a powered axle needs a mechanism to let two driven wheels turn at different speeds under torque. Propshaft carries drive from engine to axle; universal joint lets it bend as the axle moves on its springs.

**Inputs/prereqs.** Bevel gear cutting, case hardening (10_metallurgy.md); bloomery iron housing, steel teeth.

**Procedure.** Cut bevel side gears and pinions on a spider carrier, fit in a housing, hand-lap until smooth, pack with grease.

**Fails.** Chipped hand-cut teeth, cracked housings, and grit-seized bearings are the usual failures.

**Cost/danger.** ESTIMATED 15-30 artisan-days per unit. A snapped propshaft under load can whip; otherwise low risk.

**Confidence: HIGH** - textbook mechanism, achievable with case-hardened gear teeth.

---

### tl_ackermann_steering - Ackermann steering geometry

Also covers: tl_kingpin, tl_fifth_wheel

**Kernel.** Parallel-linked steering points both front wheels the same direction, which is wrong: the inner wheel needs a tighter arc, and without the correction tyres scrub sideways every turn, invisible on iron tyres, expensive on rubber. Kingpin is the pivot each steered wheel turns on; lean it back slightly and the wheel self-centres after a turn, like a shopping-trolley castor.

**Inputs/prereqs.** Forged steel pins, basic linkage design.

**Procedure.** Angle steering arms so their lines cross near the rear axle centre; connect with a track rod.

**Fails.** Worn kingpin bushings cause wander.

**Cost/danger.** ESTIMATED 5-8 artisan-days. A seized kingpin locks steering at speed.

**Confidence: HIGH** - pure geometry.

---

### tl_leaf_spring - Leaf spring suspension

Also covers: tl_elliptic_spring, tl_coil_spring, tl_friction_damper, tl_hydraulic_shock

**Kernel.** A spring does not soften the ride, it defers the impact over time, and the longer a force acts the lower its peak stress on frame and axle. Left alone a spring keeps oscillating after every bump; a friction damper (rubbing leaves or a sliding block) or hydraulic shock (oil through a small orifice) bleeds that energy off so the vehicle settles instead of bouncing.

**Inputs/prereqs.** Hardened, tempered spring steel (10_metallurgy.md).

**Procedure.** Forge strips, heat to cherry red (~800C), quench, temper to straw yellow (~220C), stack and clamp.

**Fails.** Over-hardening cracks; under-hardening sags permanently.

**Cost/danger.** ESTIMATED 20-30 artisan-hours per set. Quenching risks steam burns; a snapped leaf whips.

**Confidence: HIGH** - continuous use since the 18th century.

---

### tl_brake_shoe - Brake shoe on a drum

Also covers: tl_drum_brake, tl_disc_brake, tl_handbrake, tl_wire_rope_brake, tl_hydraulic_brake_line

**Kernel.** The limit is never friction, it is heat disposal. A drum encloses the shoes, keeping out mud but trapping heat, so hard sustained braking (a long descent) causes fade, friction drops as the drum heats and the brake stops working. A disc is open to air, cools by convection, does not fade the same way, why it became standard once affordable.

**Inputs/prereqs.** Cast iron, leather/fibre linings, heavy oil for hydraulics (no synthetic rubber seals).

**Procedure.** Cast drum/disc to the hub, line shoes with friction material, link to lever or fluid line.

**Fails.** Glazed linings and leaking, air-trapped lines are the usual failures.

**Cost/danger.** ESTIMATED 8-15 artisan-days per axle. Failure on a loaded descent is lethal; hot drums burn on contact.

**Confidence: HIGH** mechanics; MEDIUM on hydraulic seal durability.

---

### tl_engine_block - Cast engine block

Also covers: tl_piston_assembly, tl_connecting_rod, tl_cam_follower

**Kernel.** A single casting with cored cooling passages avoids the joints that would otherwise leak; boring the cylinders true afterward matters more than the casting, a loose piston loses compression and a tight one seizes. Rings on the piston seal gas above and wipe oil below. Con-rod mass must be balanced end to end or the engine shakes apart at speed, easy to get wrong hand-forging.

**Inputs/prereqs.** Iron/bronze founding at scale, precision boring (40_power_precision.md), case hardening.

**Procedure.** Cast block with water jacket, bore cylinders slowly and true, fit rings checked in a gauge, balance rods by weighing.

**Fails.** An oiled, ring-less piston should fall under its own weight with slight drag, not free-fall or stick.

**Cost/danger.** ESTIMATED 40-80 artisan-days for a first block. Molten metal burns; a shattered rod at speed is shrapnel.

**Confidence: MEDIUM** - founding is attested Roman skill; engine-grade tolerance is the unknown.

---

### tl_intake_valve - Poppet valve with cam and spring

Also covers: tl_exhaust_valve

**Kernel.** The exhaust valve is the hottest part in the engine, in the combustion path every cycle; plain iron scales, warps and stops sealing within hours, needing an alloy that holds shape hot (nickel/chromium), which pushes hard against Roman metallurgy. Timing is equally unforgiving: late by a little and power drops, or the piston strikes the valve.

**Inputs/prereqs.** Alloy steel (10_metallurgy.md, rare chromite/nickel ore), precision grinding.

**Procedure.** Forge a wide seating face, grind seat and valve together with abrasive paste to a continuous contact ring, set cam timing by trial.

**Fails.** A leaking valve hisses at that cylinder when turned by hand through compression.

**Cost/danger.** ESTIMATED 3-5 artisan-days per valve. A dropped valve wrecks the engine.

**Confidence: MEDIUM** - simple mechanism, exhaust-valve alloy is the weak link.

---

### tl_carburettor - Carburettor (fuel atomiser)

Also covers: tl_fuel_pump, tl_anti_siphon_valve, tl_throttle, tl_air_filter

**Kernel.** Works by the Bernoulli effect: air forced through a narrowed throat speeds up and its pressure drops, pulling fuel from a float-held reservoir roughly in proportion to engine speed, no calculation needed. The float chamber is the trick, holding fuel level constant the way a cistern ballcock does. Anti-siphon valve stops fuel draining into the cylinder when off with the tank above.

**Inputs/prereqs.** Bronze sheet work, fine drilling; wool/cloth filter medium.

**Procedure.** Cast a venturi body, drill a fine fuel jet fed from a ballcock float chamber, fit a cable-linked throttle plate.

**Fails.** Black sooty exhaust means too rich; weak popping means too lean.

**Cost/danger.** ESTIMATED 6-10 artisan-days. Raw fuel in an open float chamber is a fire risk.

**Confidence: MEDIUM** - venturi physics is solid; a consistent hand-drilled jet is the practical bottleneck.

---

### tl_magneto_ignition - Magneto ignition

Also covers: tl_coil_ignition, tl_distributor, tl_spark_plug, tl_ignition_timing

**Kernel.** A magneto makes its own current from engine rotation, no battery needed, which matters until reliable storage batteries exist; coil ignition instead steps up battery voltage and is more reliable at high revolutions. Distributor is a rotating switch timed to firing order; wrong order runs the engine backward or not at all.

**Inputs/prereqs.** 50_electricity.md coils and magnets; fired clay or fused-quartz spark plug insulator surviving ~1000C.

**Procedure.** Wind a coil near a rotating magnet, build a distributor matched to cylinder count, fit a spinning-weight timing governor.

**Fails.** A spark should jump a visible gap in daylight shade.

**Cost/danger.** ESTIMATED 15-25 artisan-days. High voltage gives a sharp shock; fouled plugs near fuel are a fire risk.

**Confidence: MEDIUM** - electromagnetics attested; a reliable high-temp ceramic insulator is the weak link.

---

### tl_radiator - Radiator water cooling

Also covers: tl_water_pump, tl_thermostat, tl_fan_belt, tl_cooling_fan

**Kernel.** An engine needs to run hot, not cold; too cool and fuel does not vaporise properly and wear accelerates, which is the reason for the thermostat, a wax valve staying shut until roughly 82C and only then opening. Without it the engine spends its whole warm-up running rich and dirty.

**Inputs/prereqs.** Copper/bronze brazing.

**Procedure.** Braze a finned copper core, fit a paddle-wheel pump, cast a wax-pellet thermostat valve, belt-drive a fan.

**Fails.** Steady temperature under load, not climbing or never warming.

**Cost/danger.** ESTIMATED 10-18 artisan-days. Opening a hot pressurised system sprays scalding water.

**Confidence: HIGH** - simple heat exchange, within Roman brazing skill.

---

### tl_oil_pump - Pressure oil pump

Also covers: tl_pressure_relief_valve, tl_transmission_lubrication

**Kernel.** Splash lubrication (oil thrown by spinning gears) starves a fast bearing under load; pressure feed guarantees a fresh film arrives before the bearing can run dry and score. The relief valve is the unglamorous safety part: without it, pressure would climb without limit as revolutions rise, so a spring-loaded valve bleeds excess back to the sump once a set pressure is reached.

**Inputs/prereqs.** Precision gear cutting, spring steel; olive oil or refined mineral oil (93_energy.md).

**Procedure.** Cut two meshing gears in a tight housing, drill galleries to each bearing, fit a spring-loaded relief valve set by trial.

**Fails.** A disconnected feed line, engine idling, should flow steadily, not dribble.

**Cost/danger.** ESTIMATED 8-12 artisan-days. Hot oil sprays if a line bursts.

**Confidence: HIGH** - simple positive-displacement pump.

---

### tl_plate_clutch - Plate clutch and gearbox

Also covers: tl_cone_clutch, tl_sliding_gearbox, tl_synchromesh, tl_epicyclic_gearbox, tl_automatic_transmission

**Kernel.** An engine bolted to a moving wheel would stall instantly at rest, so something must slip briefly while torque rises: a cone clutch does it with a matched conical surface, simple but grabby; a flat plate clutch engages more gently. A sliding gearbox crashes and grinds unless engine and gear speeds are matched by ear (double-clutching) before the shift; synchromesh fixes this with a friction ring that spins the incoming gear to match speed before the teeth engage.

**Inputs/prereqs.** Precision gear cutting, spring steel clutch plates.

**Procedure.** Cut 3-4 gear ratio pairs on parallel shafts, add friction cones for synchromesh, build a spring-squeezed plate clutch.

**Fails.** Pulls away from rest without stalling; gears engage without grinding once rev-matched.

**Cost/danger.** ESTIMATED 20-40 artisan-days.

**Confidence: MEDIUM** - gear cutting attested; synchromesh tolerance is a stretch without machine tools (40_power_precision.md).

---

### tl_dynamo - Dynamo and electric starting

Also covers: tl_motor_dc, tl_storage_battery, tl_electric_starter

**Kernel.** A DC motor and DC dynamo are the same machine run in opposite directions; the starter is just a motor sized for brief huge torque, disengaging automatically once the engine fires. Lead-acid battery chemistry is counterintuitive: charging converts lead sulfate on one plate to spongy lead and on the other to lead dioxide, discharge reverses it, and the electrolyte water is consumed over time, needing periodic "watering."

**Inputs/prereqs.** 50_electricity.md coils/commutators; lead, sulfuric acid (20_chemistry.md, both Roman-known).

**Procedure.** Wind armature and field coils with a copper commutator; assemble lead plates in acid; charge until plates show the expected colour change; gear the starter through an overrunning clutch.

**Fails.** Charging shows steady bubbling; denser acid (tested by a floating gauge) means fuller charge.

**Cost/danger.** ESTIMATED 30-50 artisan-days. Sulfuric acid causes severe burns; hydrogen from charging is explosive near flame, ventilate.

**Confidence: MEDIUM** - electromagnetics and lead-acid chemistry are textbook; sustained plate quality is the manufacturing challenge.

---

### tl_headlamp - Headlamp and signal lighting

Also covers: tl_carbide_lamp, tl_indicator

**Kernel.** A carbide lamp is chemistry, not electricity: calcium carbide dripped with water releases acetylene, burning bright white with zero electrical infrastructure, the obvious first headlamp before a dynamo exists. An electric headlamp needs a shaped reflector to throw a useful beam rather than a diffuse glow. An indicator is a flashing relay or, simplest, a hand-raised folding arm.

**Inputs/prereqs.** Calcium carbide needs an electric arc furnace (93_energy.md), a prerequisite gap; polished bronze reflectors.

**Procedure.** Build a two-chamber brass carbide lamp, water dripping onto carbide feeding a burner jet.

**Fails.** A steady bright flame from a controlled drip, not sputtering.

**Cost/danger.** ESTIMATED 4-8 artisan-days per lamp. Acetylene can flash back into the generator if the jet clogs.

**Confidence: MEDIUM** - lamp chemistry simple; the arc furnace prerequisite is the gap.

---

### tl_muffler - Muffler and windscreen wiper

Also covers: tl_windscreen_wiper

**Kernel.** An unsilenced engine is startlingly loud, loud enough to spook every draft animal on the road and read as an attack to a nearby garrison, so a baffled expansion chamber is a social necessity, not just comfort; it works by breaking exhaust pulses into smaller out-of-phase ones, at a cost in backpressure and power. A wiper only matters once glass exists (30_glass_optics.md); a cam-driven arm off the engine or a hand crank suffices.

**Inputs/prereqs.** Sheet metalwork; oiled leather or vulcanized rubber blade.

**Procedure.** Build a chambered box the exhaust snakes through; cam-drive a wiper arm against the glass.

**Fails.** Engine note drops to a muted rumble; wiper clears a wetted pane in one sweep.

**Cost/danger.** ESTIMATED 3-6 artisan-days. None significant; social value of the muffler is real.

**Confidence: HIGH** - simple mechanical fixes.

---

### tl_motor_lorry - Motor lorry and heavy road vehicles

Also covers: tl_articulated_trailer, tl_tractor, tl_caterpillar_track, tl_half_track, tl_snow_plough

**Kernel.** A wheel concentrates weight onto a small patch and sinks into soft ground; a caterpillar track spreads that weight over a long footprint, crossing mud and sand a wheeled vehicle cannot, at the cost of far higher friction losses per road mile. A half-track compromises, wheels for steering and road speed, tracks for traction, cheaper and faster on roads than full tracks.

**Inputs/prereqs.** tl_differential, tl_leaf_spring, tl_plate_clutch, tl_pneumatic_tyre or tl_solid_rubber_tyre.

**Procedure.** Build a ladder chassis, fit the drivetrain cluster above, link steel track plates over sprockets for tracked variants.

**Fails.** Climbs a measured grade loaded without stalling; a tracked vehicle crosses soft earth a wheeled cart bogs down in.

**Cost/danger.** ESTIMATED 60-120 artisan-days per vehicle. A heavy vehicle out of control on roads built for foot traffic is a serious hazard.

**Confidence: MEDIUM** - depends on every upstream drivetrain component.

---

### tl_omnibus - Omnibus and public transit

Also covers: tl_motorcycle, tl_horse_tram, tl_steam_tram, tl_electric_tram, tl_trolleybus

**Kernel.** A horse tram is not about the horse, it is about the rail: steel-on-steel rolling resistance is a fraction of steel-on-dirt, so the same horse on rails hauls several times its road load. A steam tram swaps the horse for a small enclosed engine; an electric tram swaps the boiler for a motor drawing current through a trolley pole from an overhead wire, needing a citywide power network first.

**Inputs/prereqs.** tl_iron_tyre or tl_pneumatic_tyre; tl_dynamo/tl_motor_dc and tr_catenary_overhead for electric variants.

**Procedure.** Lay smooth iron rail, build a sprung low-floor car, add the relevant power cluster for steam/electric versions.

**Fails.** A tram horse pulls a full load at a trot without distress where the same horse struggles on paving.

**Cost/danger.** Substantial civic capital, see 85_transport_civil.md. Social: a fixed rail claims permanent street space, expect political negotiation.

**Confidence: HIGH** horse tram; MEDIUM steam/electric, depending on upstream power modules.

---

### tl_spoked_wheel - Improved spoked and wire-spoke wheel

Also covers: tl_wire_spoke_wheel, tl_iron_tyre, tl_shrink_fit

**Kernel.** A shrink-fit tyre is not just a wear surface, it is a structural clamp: forged slightly small, heated to expand and fitted, then quenched, it contracts as it cools and squeezes the wheel under permanent tension, holding loose joints tight. Wrong temperature either fails to fit or splits the wood shrinking.

**Inputs/prereqs.** Already-routine Roman iron banding (85_transport_civil.md); drawn iron/bronze wire.

**Procedure.** Forge the band slightly undersized, heat to dull red, drop on and quench evenly around the circle.

**Fails.** A properly shrunk tyre rings clean when struck; a loose one sounds a dull rattle.

**Cost/danger.** MEASURED-adjacent, already Roman practice; wire lacing ESTIMATED 2-4 artisan-days per wheel. Hot iron near dry wood is a fire risk.

**Confidence: HIGH** - direct extension of existing Roman practice.

---

### tl_pneumatic_tyre - Pneumatic tyre

Also covers: tl_inner_tube, tl_tyre_bead, tl_tyre_tread, tl_vulcanized_rubber, tl_solid_rubber_tyre

**Kernel.** The win is not comfort, it is energy: a rigid iron or solid-rubber tyre loses energy to heat at every bump, while a rolling air cushion flexes and returns nearly all of it elastically, why pneumatic tyres roughly doubled achievable bicycle speed before reaching a car. None of it works without vulcanization: raw rubber is sticky hot and brittle cold, useless as a material, and sulfur cross-links the chains into something elastic across temperature.

**Inputs/prereqs.** Rubber is not Roman-native, comes only by expedition to West Africa or ruinous Far East trade (95_expeditions.md); sulfur from Sicily.

**Procedure.** Mix latex with roughly 5-8 percent sulfur, mould around a cord bead, heat 140-160C for an hour or more until it springs back sharply when dented.

**Fails.** A vulcanized sample bends double and springs straight back with no crack.

**Cost/danger.** ESTIMATED high per-unit until controlled rubber supply exists; solid rubber is a cheaper, heavier fallback sooner. Sulfur fumes are mildly toxic, ventilate.

**Confidence: HIGH** chemistry once rubber is in hand; LOW on supply timeline, dependent on 95_expeditions.md.

---

### tl_ball_bearing - Ball, roller and taper bearings

Also covers: tl_roller_bearing, tl_taper_roller_bearing, tl_plain_bearing, tl_oil_bath, tl_grease_cup

**Kernel.** A plain bronze-sleeve bearing, already standard Roman practice, lets the softer bronze wear instead of the shaft, replaceable cheaply, but its friction stays fairly high. Rolling contact cuts friction roughly a hundredfold, but only if balls or rollers and races are round and hardened to a fine tolerance, any high spot concentrates load onto a point and dents the race (Hertzian fatigue).

**Inputs/prereqs.** Hardened, ground steel (10_metallurgy.md, 40_power_precision.md); bronze for plain bushings.

**Procedure.** Turn bronze sleeves to a thin oil-film clearance; grind rolling elements round, checked by rolling on flat plates and feeling for wobble.

**Fails.** A good bearing turns freely by hand with no roughness, stays cool after sustained running.

**Cost/danger.** ESTIMATED 1-3 artisan-days plain, 10-20 rolling per set.

**Confidence: HIGH** plain bearings; MEDIUM rolling, needing grinding precision beyond typical hand-forge tolerance.

---

### tl_safety_bicycle - Safety bicycle and its ancestors

Also covers: tl_velocipede, tl_penny_farthing

**Kernel.** A velocipede drives its front wheel from pedals on its own axle, so one pedal turn equals one wheel circumference; the only way to go faster without pedalling absurdly fast is a bigger wheel, what the penny-farthing does, why that wheel grew enormous and the rider perched dangerously high, prone to pitching over the front on any sudden stop. A safety bicycle breaks the link with a chain and sprockets, letting a normal wheel run a useful gear ratio, so the rider sits low and stable.

**Inputs/prereqs.** tl_chain_drive, tl_spoked_wheel, ideally tl_pneumatic_tyre.

**Procedure.** Build a low diamond tube frame with equal wheels, chain-drive the rear from a geared crank.

**Fails.** A rider mounts, rides and dismounts without special skill, unlike a penny-farthing.

**Cost/danger.** ESTIMATED 10-15 artisan-days. Low physical risk; expect new traffic rules once fast silent bicycles mix with carts.

**Confidence: HIGH** - simple once chain drive exists.

---

### tl_chain_drive - Chain drive, freewheel and gearing

Also covers: tl_freewheel, tl_derailleur, tl_hub_gear, tl_caliper_brake

**Kernel.** A freewheel is a ratchet letting the rear wheel spin faster than the pedals so a rider coasts downhill without feet flung around, a hazard on fixed-drive machines. A derailleur shifts the chain sideways across sprockets for gear choice, light but fragile; a hub gear packs the same choice inside a sealed shell, tougher, shiftable while stopped, harder to field-repair.

**Inputs/prereqs.** Precision chain link and sprocket manufacture; leather or rubber-substitute brake pads.

**Procedure.** Cut evenly spaced sprockets, pin link-plate chain, fit a ratchet-and-pawl freewheel in the hub, mount a lever-caliper brake.

**Fails.** Pedalling drives with no slip; stop pedalling and the wheel keeps spinning free.

**Cost/danger.** ESTIMATED 8-12 artisan-days.

**Confidence: HIGH** - simple, well-documented geometry.

---

### tl_macadam_road - Macadam and bound road surfaces

Also covers: tl_tarmacadam, tl_concrete_roadway, tl_cambered_drainage, tl_kerbing

**Kernel.** Macadam's trick is not the stone, Rome already builds fine multi-layer roads, it is that each layer uses progressively smaller stone so traffic compacts the surface into a self-binding mat, no mortar needed, cheaper and faster than a full Roman via though less durable. Tarmacadam fills remaining voids against water and dust. Reinforced concrete eliminates rutting at far higher cost.

**Inputs/prereqs.** Existing Roman road competence (85_transport_civil.md); bitumen/tar, reinforcing iron for concrete.

**Procedure.** Grade successively finer stone layers, shape to a shallow camber, pour hot tar and blind with grit for tarmacadam.

**Fails.** Water poured on the surface runs to the edges within moments, not pooling.

**Cost/danger.** ESTIMATED lower per-mile than a full via, higher than dirt track. No physical danger; reads as prosperity, not suspicion.

**Confidence: HIGH** - extension of attested Roman technique.

---

### tl_road_roller - Steam road roller and level crossings

Also covers: tl_level_crossing

**Kernel.** Hand or animal compaction of a macadam surface took twenty-plus men all day per stretch; a steam roller replaces that with a boiler and crank driving the roller directly, at the cost of needing a working steam plant on wheels. A level crossing looks like the cheap option next to a bridge, and it is, but it quietly moves the cost into risk: safe only with gates and signals timed to close well before a train arrives, and it fails catastrophically, not gradually, when that timing slips.

**Inputs/prereqs.** 93_energy.md boiler/piston basics; tr_semaphore_signal for a safe crossing.

**Procedure.** Mount a boiler and simple engine driving the front roller by crank; install gates linked to a lever a set distance up the line.

**Fails.** A rolled road shows no rut after a season; a gate is verified shut before the earliest possible train.

**Cost/danger.** ESTIMATED significant capital for the roller. An unattended crossing is a collision waiting to happen.

**Confidence: HIGH** mechanism; MEDIUM on the operating discipline, a human problem as much as engineering.

---

### tl_horse_collar - Horse collar, horseshoe, stirrup and harness

Also covers: tl_horseshoe, tl_stirrup, tl_tandem_harness, tl_whippletree

**Kernel.** The Roman yoke presses across a horse's windpipe and neck vessels, so the harder it pulls the more it chokes, meaning Roman haulage runs at a fraction of a horse's capacity, the animal is the hidden bottleneck. A rigid, padded collar moves that pressure onto chest and shoulders, bone and muscle, letting a horse pull roughly five times its own weight.

**Inputs/prereqs.** Leatherworking, ironworking, nothing exotic.

**Procedure.** Shape a padded collar to the shoulders, fit nailed iron shoes, hang a pivoting whippletree between paired traces.

**Fails.** A collared horse pulls a load the yoked equivalent cannot budge.

**Cost/danger.** ESTIMATED 1-2 artisan-days per set, trivial cost, a design win. A misplaced shoe nail lames the horse.

**Confidence: HIGH** - simple, well-attested, among the highest payoff-to-difficulty entries here.

---

### tr_edge_rail - Edge rail, bullhead and flat-bottom profiles

Also covers: tr_bullhead_rail, tr_flatbottom_rail, tr_chair_key, tr_fishplate, tr_rail_rolling, tr_rail_welding

**Kernel.** A thin raised iron edge, not a thick flat plate, is the efficient shape: the flange only needs a narrow guiding edge, so concentrating iron there saves metal for equal strength. Bullhead rail is symmetrical top and bottom, so once worn on one side it turns over and relays, doubling service life, but needs a cast chair clamping the head, keyed with a driven wedge; flat-bottom rail sits on the sleeper without one, saving weight, but only once mill tolerances are good enough.

**Inputs/prereqs.** Rolling mill (10_metallurgy.md); wrought iron, then steel.

**Procedure.** Roll bar through narrowing rollers to profile, cast chairs to head shape, bolt fishplates at joints.

**Fails.** A finished length rings uniformly when struck, no dull spots.

**Cost/danger.** Largest single capital line of any rail project (85_transport_civil.md). Mill work risks serious burns.

**Confidence: HIGH** geometry; MEDIUM on mill tolerance.

---

### tr_sleeper_ballast - Sleeper, ballast and track gauge

Also covers: tr_wooden_waggonway, tr_rail_gauge_standardization

**Kernel.** Ballast size is a choice: too large and rails rock on point contact, too small and the bed settles and washes out. Sleepers need precise, repeated spacing, checked with a wooden gauge and string, since an uneven foundation telegraphs straight into wheel impact.

**Inputs/prereqs.** tr_edge_rail for the modern version; plain carpentry for the waggonway.

**Procedure.** Compact a graded stone bed, set sleepers to a template spacing, fix one agreed gauge across every line meant to interconnect.

**Fails.** No visible sleeper movement under a loaded wagon at speed; separately built lines run through without transfer.

**Cost/danger.** Major recurring capital, see 85_transport_civil.md. Skipped standardisation is the single most expensive mistake to fix later.

**Confidence: HIGH** - documented from the historical record.

---

### tr_semaphore_signal - Semaphore, block and interlocking signalling

Also covers: tr_block_signalling, tr_interlocking_signal, tr_track_circuit, tr_automatic_train_stop

**Kernel.** A semaphore only tells a driver about track visible from that post; the invention is dividing the line into blocks and never allowing two trains in one block, preventing rear-end collisions by rule, not driver vigilance. Interlocking locks out any lever combination that sets conflicting routes, so an honest mistake causes delay, not a wreck; a track circuit automates detection, low voltage short-circuited the instant a train's wheels bridge the gap; an automatic train stop trips the brake past a danger signal, since fog and night mean not every signal is seen.

**Inputs/prereqs.** 50_electricity.md; tr_edge_rail for a continuous usable rail.

**Procedure.** Divide the line into blocks with token exchange; mechanically interlock levers; wire a low-voltage relay circuit through each block.

**Fails.** Deliberately try a conflicting lever setting; the interlock should physically refuse it.

**Cost/danger.** Modest hardware, ongoing cost is trained signalling staff. Social: reads as a military-grade control system to Rome.

**Confidence: HIGH** - simple logic, documented historically.

---

### tr_points_frog - Points, frog, turntable and yard switching

Also covers: tr_grade_crossing, tr_marshalling_hump, tr_turntable

**Kernel.** A frog, where two rails cross, must support a wheel's full weight across a physical gap, unavoidable geometry, the wheel bridges it on flange and tread together. A hump yard pushes a train slowly over a rise, uncoupling wagons one at a time at the crest so gravity alone rolls each into its sorted siding, eliminating the labour of shunting each one by hand.

**Inputs/prereqs.** tr_edge_rail, tr_flanged_wheel.

**Procedure.** Cast a frog bridging the crossing gap, grade a hump-yard rise with fanned sorting tracks, build a turntable pit on a rolling-element ring.

**Fails.** A hump wagon rolls unassisted into its assigned siding; a loaded locomotive rotates on the turntable with modest effort.

**Cost/danger.** Significant earthworks for a hump yard. A hump yard among free-rolling wagons is a serious crush hazard.

**Confidence: HIGH** - simple mechanics.

---

### tr_flanged_wheel - Flanged wheel, axle box and bogie

Also covers: tr_axle_bearing_box, tr_bogie_truck, tr_leading_truck

**Kernel.** Putting the flange on the wheel, not a groove in the rail, is right because a flanged wheel runs on a simple flat rail while a grooved one collects debris; the flange slips sideways slightly on curves, a tolerated, designed-in imperfection. The axle bearing box is unglamorous and lethal if neglected: it needs a drain hole so grit-laden oil does not accumulate, since a clogged, dry box overheats catastrophically, a "hot box," historically a leading cause of derailment, caught only by scheduled inspection.

**Inputs/prereqs.** tr_edge_rail; casting within a few mm, case hardening.

**Procedure.** Cast wheels with a proud flange, case-harden tread and flange, drill drained axle boxes on a re-oiling schedule.

**Fails.** No squeal on the tightest curve; box runs warm, never hot, on checks.

**Cost/danger.** Moderate per wheelset; inspection labour matters more than build cost. A hot box can derail a train.

**Confidence: HIGH** - attested historical pattern.

---

### tr_screw_coupling - Screw coupling, buffer and knuckle coupler

Also covers: tr_sprung_buffer, tr_knuckle_coupler

**Kernel.** The problem of a train is starting it, since you cannot accelerate every wagon at once, so slack in every coupling is a feature: it lets the locomotive take up each wagon's inertia one at a time, "snatching" the train into motion link by link. A screw coupling is tightened by a man walking between wagons turning a threaded rod by hand, slow and historically one of the most dangerous railway jobs, a screwman crushed between buffers is a grim routine record; sprung buffers cushion the impact, tuned so they neither transmit shock nor rebound enough to uncouple; a knuckle coupler removes the human entirely.

**Inputs/prereqs.** Iron founding/forging at scale; cast steel for reliable knuckle geometry.

**Procedure.** Forge hook and threaded bar; tune sprung buffer heads; cast a hinged latching jaw for knuckle couplers.

**Fails.** A coupled train starts with a visible sequential "snatch," not one violent jerk.

**Cost/danger.** ESTIMATED 2-4 artisan-days per coupling. Screw coupling by hand is documented as one of the most dangerous manual railway jobs.

**Confidence: HIGH** - simple mechanics, documented injury patterns to plan around.

---

### tr_brake_shoe - Rail brake shoe, vacuum and Westinghouse air brake

Also covers: tr_vacuum_brake, tr_westinghouse_brake

**Kernel.** A cast iron brake shoe overheats under sustained use like a road brake, losing friction when needed most. The vacuum brake's failure logic is counterintuitive: a vacuum runs the train's length, and if any coupling or hose breaks, air rushes in and brakes apply on every wagon at once, the failure mode is "stop," backwards from what you would guess and what a safety system needs.

**Inputs/prereqs.** tr_flanged_wheel, tr_screw_coupling for the connected pipe runs.

**Procedure.** Run a continuous pipe coupled between every wagon, evacuated or pressurised from the locomotive; fit local valves applying each brake automatically on pressure drop.

**Fails.** Deliberately uncouple a hose mid-train stationary; every wagon's brake should apply immediately.

**Cost/danger.** Substantial fleet-wide retrofit, justified by safety alone. Trains without a fail-safe brake are a documented cause of runaways.

**Confidence: HIGH** - documented, mechanically simple once understood.

---

### tr_locomotive_boiler - Locomotive boiler, smokebox, blastpipe, superheater, injector

Also covers: tr_smoke_box, tr_blastpipe, tr_superheater, tr_injector_feedwater

**Kernel.** A locomotive boiler needs far more heat transfer surface per area than a stationary one, solved with dozens of small fire-tubes; tube failure ruptures the boiler explosively, so ferrule expansion (a tight mechanical swage) at every tube end is standard. The blastpipe is the clever bit: exhaust steam up a narrow chimney nozzle drags hot firebox gases through the tubes by suction, so the harder the engine works, the harder it draws its own fire, no fan needed.

**Inputs/prereqs.** 93_energy.md boiler fundamentals; tube-rolling, ferruling; wrought iron/steel plate.

**Procedure.** Ferrule fire-tubes tight at both ends, fit a mesh char arrester, aim exhaust up a blastpipe nozzle, route steam through extra tubes for superheating, fit a nested-cone injector.

**Fails.** Fire draws visibly harder the instant the throttle opens; the injector delivers a steady hiss with no water hammer.

**Cost/danger.** Major fabrication project, comparable to 93_energy.md's boilers at tighter, portable tolerance. A ruptured tube or low-water crown sheet is this module's worst failure mode.

**Confidence: HIGH** mechanisms; MEDIUM on Roman-era quality control at full working pressure without modern testing.

---

### tr_slide_valve - Slide valve, piston valve and valve gear

Also covers: tr_piston_valve, tr_stephenson_linkmotion, tr_walschaerts_valve, tr_compound_expansion, tr_articulated_locomotive

**Kernel.** A slide valve rubs a flat face continuously under steam, wasting power to friction; a piston valve seals with rings instead, only the rings touch the bore, cutting friction sharply, like the main piston. Stephenson link motion uses two eccentrics, forward and reverse, driving a curved link; sliding the pickup point blends between them, choosing direction and a shortened, efficient "cutoff," and Walschaerts gear does the same from the piston rod's crosshead instead, smoother and easier to maintain.

**Inputs/prereqs.** tr_locomotive_boiler; precision linkage fabrication.

**Procedure.** Cut offset eccentric cams, link through a curved slotted bar to the valve rod with a driver-adjustable pickup; duct exhaust from high to low pressure cylinders for compounding.

**Fails.** Steam ports show even, symmetric opening when hand-turned slowly; a compound engine shows quieter exhaust and lower coal use.

**Cost/danger.** Among the most skill-intensive fabrication here. A loose link near wheels at speed can shatter violently.

**Confidence: MEDIUM** - documented mechanisms, hard to fabricate reliably by hand.

---

### tr_electric_locomotive - Electric and diesel-electric traction

Also covers: tr_pantograph, tr_catenary_overhead, tr_third_rail, tr_diesel_electric

**Kernel.** Electric traction is not steam but cleaner, it needs infrastructure first, overhead catenary (a sagging cable plus contact wire, a spring-loaded pantograph pressed against it) or a third rail with a sliding shoe, either a larger project than the locomotive. The pantograph's problem is contact at speed: too little pressure and it bounces and arcs, burning both; too much wears the wire fast.

**Inputs/prereqs.** 50_electricity.md generation at scale; 93_energy.md diesel fundamentals; refined petroleum fuel.

**Procedure.** String a sag-compensated catenary, fit a spring-tuned pantograph, couple a diesel to a generator driving axle motors.

**Fails.** No visible arcing at running speed; pulls away smoothly with no stall risk.

**Cost/danger.** Very high fixed infrastructure, justify only on highest-traffic routes. A live catenary or third rail needs disciplined access control (50_electricity.md).

**Confidence: MEDIUM** - machines documented, infrastructure is the larger unknown.

---

### tr_hopper_wagon - Specialised wagons: hopper, tank, refrigerated, sleeping car

Also covers: tr_tank_wagon, tr_refrigerated_wagon, tr_sleeping_car

**Kernel.** A hopper wagon eliminates shovel labour, released through a bottom chute by gravity, but the chute must be wide or fine/damp cargo "bridges," arches over the opening and jams. A tank wagon carries sloshing liquid weight over rough track, a seam weakness that is a slow drip static becomes a leak dynamically; hand-riveted seams were a known weak point.

**Inputs/prereqs.** tr_flanged_wheel, tl_leaf_spring; cork/sawdust insulation, natural ice.

**Procedure.** Taper a hopper body to a wide hinged chute; weld or rivet tested tank seams; line refrigerated bodies with insulation and vented roof-corner ice bunkers.

**Fails.** A hopper empties fully with no bridging; a refrigerated wagon holds even cool temperature end to end after a day's run.

**Cost/danger.** Moderate premium over a plain wagon. A leaking tank carrying anything flammable is a serious derailment hazard.

**Confidence: HIGH** - simple extensions of the basic wagon.

---

### tr_carvel_planking - Hull planking, framing and caulking

Also covers: tr_clinker_planking, tr_frame_first_construction, tr_keelson, tr_caulking_oakum, tr_hull_sheathing_wood, tr_copper_sheathing

**Kernel.** Clinker planking (each plank overlapping the one below) is not just an old look, the overlap gives flex and a hydrodynamic benefit at speed. Carvel planking (flush edges over an internal frame) gives a smoother, stronger hull, but only if every seam is caulked with oakum, tarred rope fibre driven in from both sides, or it weeps; frame-first construction (ribcage first, then planking) gives far more precise, repeatable shapes than shell-first.

**Inputs/prereqs.** Existing Roman shipwrighting (85_transport_civil.md); copper (Cyprus, Spain).

**Procedure.** Build the frame first over keel and keelson, plank over it, drive oakum into every seam from both sides, seal with hot pitch, nail copper sheet with copper nails.

**Fails.** A coppered hull stays free of fouling season after season.

**Cost/danger.** Copper sheathing is the expensive addition, justified mainly for long tropical voyages. Low physical risk.

**Confidence: HIGH** - sits on already-excellent Roman shipwrighting.

---

### tr_iron_hull - Iron and steel hull, plating and bulkheads

Also covers: tr_steel_hull, tr_riveted_plating, tr_welded_hull, tr_double_bottom, tr_watertight_bulkhead

**Kernel.** An iron hull is a step change: iron plate can be built larger and thinner-walled than wood, which needs thickness against rot and worm, so an iron ship can be much bigger for the same displacement. Riveted plating, red-hot rivets hammered flush, is labour-intensive but reliable if well done; a poor rivet leaks slowly, catastrophically once corrosion widens the gap.

**Inputs/prereqs.** Bulk iron/steel plate (10_metallurgy.md); riveting or welding skill.

**Procedure.** Overlap and rivet red-hot plate flush; build a full second inner hull skin for a double bottom; seal every bulkhead penetration and test by deliberate flooding.

**Fails.** A riveted seam under load shows no weeping; a deliberately flooded compartment leaves neighbours dry.

**Cost/danger.** Major multi-year shipyard investment. Riveting risks burns and falls; an unsealed bulkhead gives false confidence.

**Confidence: MEDIUM** - documented but depends on the bulk iron/steel supply chain (10_metallurgy.md).

---

### tr_square_rig - Sail plans: square, lateen, fore-and-aft, jib, staysail, reefing

Also covers: tr_lateen_sail, tr_fore_aft_rig, tr_fore_and_aft_rigging, tr_jib, tr_staysail, tr_reefing

**Kernel.** A square sail is powerful running before the wind and nearly useless toward it, a pure geometric limit. A lateen sail, hung steeply, points much closer to the wind, letting a ship sail across it and tack against it; fore-and-aft rigging generalises this, and with a sternpost rudder lets a captain choose a departure date rather than wait for fair wind.

**Inputs/prereqs.** Existing Roman square-rig ships (85_transport_civil.md); tr_sternpost_rudder for the full windward benefit.

**Procedure.** Cut square sails for downwind, triangular lateen/fore-and-aft sails for closer work, rig stays fore and aft, sew reef points across each sail.

**Fails.** The ship demonstrably tacks a course into the wind, which a pure square-rigger cannot do at all.

**Cost/danger.** Moderate, mostly a redesign of existing sailmaking skill (90_textiles.md). Sail-handling aloft is dangerous.

**Confidence: HIGH** - within existing Roman textile and rigging skill.

---

### tr_bowsprit - Bowsprit, mast stepping and rigging hardware

Also covers: tr_mast_stepping, tr_rigging_block_lashing

**Kernel.** A bowsprit lives under two opposing loads at once, compression from the jib's pull and tension from its lashing; if the lashing fails, the spar fails suddenly under unopposed compression. Mast stepping, the joint where mast meets keel or deck, carries both sail thrust and gust bending moment, and a failed step drops the rig, not just bends it.

**Inputs/prereqs.** 90_textiles.md rope-making; existing Roman shipwrighting.

**Procedure.** Step the mast into a deep, wedged socket; lash the bowsprit with inspected turns; train riggers on sample splices pulled to failure.

**Fails.** A tensioned stay struck gives a taut, high-pitched sound; a good splice breaks near, not at, the splice.

**Cost/danger.** ESTIMATED 1-3 artisan-days per mast. A failed mast or bowsprit at sea can kill crew far from repair.

**Confidence: HIGH** - existing Roman craft; the risk is skill transfer, not material.

---

### tr_sternpost_rudder - Propulsion: rudder, propeller and shafting

Also covers: tr_screw_propeller, tr_variable_pitch_propeller, tr_paddle_wheel, tr_reduction_gearing, tr_stern_tube

**Kernel.** See 92_vehicles_flight.md's sternpost_rudder entry: a single centred blade gives far more steering leverage than side-hung oars, letting a captain point high into the wind, tack, and choose a departure date. A paddle wheel throws water up as well as back, wasting energy, worse in rough seas.

**Inputs/prereqs.** See 92_vehicles_flight.md sternpost_rudder and screw_propeller; bronze, case-hardened steel for gearing.

**Procedure.** Hang a single rudder blade on pintles, cast and balance a multi-blade propeller, align the shaft through a packed stern tube, fit reduction gears where needed.

**Fails.** No unusual vibration through the hull at speed; the stern tube packing stays compressed and dry outside after a voyage.

**Cost/danger.** High skilled labour. A failed stern tube seal can flood a ship.

**Confidence: HIGH** rudder (attested in 92_vehicles_flight.md); MEDIUM propeller/shaft precision.

---

### tr_marine_engine - Marine steam and diesel propulsion machinery

Also covers: tr_triple_expansion, tr_marine_turbine, tr_marine_diesel, tr_water_tube_boiler

**Kernel.** A marine engine runs continuously for weeks with no shore maintenance, crankshaft connecting directly, horizontally, to the propeller shaft. Triple expansion pushes the compound logic further, steam expands through three cylinder sizes, more work per unit of coal, why it became the workhorse of ocean freight.

**Inputs/prereqs.** 93_energy.md boilers/combustion; tr_locomotive_boiler's tube lessons; tr_reduction_gearing for turbines.

**Procedure.** Connect a horizontal direct-drive engine to the shaft; stage compound/triple cylinders to receive prior exhaust.

**Fails.** A triple-expansion engine shows quieter exhaust and lower coal use than single expansion for equal power.

**Cost/danger.** Among the largest capital investments here (93_energy.md scale). A marine boiler failure at sea is catastrophic, far from help.

**Confidence: MEDIUM** - documented mechanisms, reliable continuous duty at Roman tolerance is the open question.

---

### tr_windlass - Deck machinery: windlass, capstan, anchor, chain, bilge pump, ballast, block and tackle

Also covers: tr_capstan, tr_stockless_anchor, tr_chain_cable, tr_bilge_pump, tr_ballast_tank, tr_block_tackle

**Kernel.** A windlass or capstan multiplies human force through gear reduction; without it no crew can haul a large anchor against water resistance and its own weight, gearing is the difference between possible and impossible. Chain cable does not rot or chafe on a rocky bottom, but every link must be forge-welded fully shut, one flawed link opens under load and the ship is adrift.

**Inputs/prereqs.** Iron chain forging; existing Roman rope and pulley technique.

**Procedure.** Build a geared windlass or capstan sized to the anchor; forge and test chain links individually; fit ballast pumps and distribution valves.

**Fails.** A small crew hauls the loaded anchor aboard; a bilge pumped on schedule never outpaces the crew in ordinary weather.

**Cost/danger.** Moderate, within routine shipyard capability. A parted chain under load can whip with lethal force; poor ballast has capsized ships historically.

**Confidence: HIGH** - simple mechanical advantage and metalwork.

---

### tr_marine_chronometer - Navigation instruments: chronometer, sextant, gyrocompass, log, lighthouse, ship telegraph

Also covers: tr_sextant_navigation, tr_gyrocompass_repeater, tr_log_sounding, tr_lighthouse_fresnel, tr_ship_telegraph

**Kernel.** See 92_vehicles_flight.md's marine_chronometer entry: longitude is a clock problem, and a spring-driven timepiece that loses time to temperature-driven expansion is useless until compensated. A sextant reads the angle between a body and horizon via two mirrors, one half-silvered; accuracy depends on mirror flatness (30_glass_optics.md), a manufacturing bottleneck, not conceptual.

**Inputs/prereqs.** 30_glass_optics.md mirrors/lenses; 50_electricity.md for repeaters; 60_mathematics_method.md for celestial calculation.

**Procedure.** Grind and silver flat sextant mirrors; build a temperature-compensated gimballed chronometer; cast a stepped Fresnel lens; wire a master gyrocompass to remote dials.

**Fails.** A sextant star-altitude reading matches almanac prediction within a small margin.

**Cost/danger.** High per unit, skilled-craft items at this stage. No physical danger; a bad instrument's danger is navigational, running a ship onto rocks.

**Confidence: MEDIUM** - documented and buildable, precision (especially the chronometer) is a open craft problem.

---

### tr_lifeboat - Lifeboat, submarine hull and periscope

Also covers: tr_submarine_hull, tr_periscope

**Kernel.** A lifeboat must be strong enough for a frightened crew in bad weather yet light enough to hoist on hand-cranked davits; sealed buoyant compartments, not hull shape, keep a swamped boat afloat. A submarine hull's constraint is geometry, not material: it must be round to distribute pressure evenly, any flat panel risks sudden collapse, why riveted seams, fine on a surface ship, are unsafe at depth.

**Inputs/prereqs.** tr_carvel_planking or tr_iron_hull; 30_glass_optics.md for periscope mirrors.

**Procedure.** Build a light hull with sealed buoyant compartments and hand-cranked davits; build a fully round submarine hull with no flat panel below the pressure line.

**Fails.** A deliberately swamped lifeboat still floats level; a periscope image stays bright, not dim or doubled.

**Cost/danger.** High for a pressure-tested submarine hull. Failure at depth is instantly fatal with no warning; test unmanned and remote-monitored, never manned first.

**Confidence: HIGH** lifeboats; LOW submarine hulls, where Roman-era riveting quality may not be adequate and the cost of being wrong is total.

---

### tr_dry_dock - Shipyard infrastructure: dry dock, slipway, tugs, dredging

Also covers: tr_slipway_launch, tr_tug, tr_dredger

**Kernel.** A dry dock's gates must seal absolutely, since any leak fills the dock and re-floats or damages the ship being worked on below the waterline. A slipway looks simple, an inclined ramp the hull slides down, but launch angle and lubricant must be calculated correctly, too steep or too slick and the hull accelerates uncontrollably, a hazard.

**Inputs/prereqs.** tr_carvel_planking/tr_iron_hull; 85_transport_civil.md harbours_and_dredging.

**Procedure.** Build dock gates with redundant seals, tested by controlled partial flooding; calculate slipway angle against hull weight; build a compact high-power tug; fit wear-resistant dredger liners.

**Fails.** A pumped-dry dock shows no measurable water rise overnight; a slipway launch reaches the water at controlled speed.

**Cost/danger.** Substantial civic infrastructure (85_transport_civil.md). An uncontrolled launch can crush anyone in the hull's path.

**Confidence: HIGH** - extends existing Roman harbour engineering directly.

---

### tr_canal_lock - Canal lock and canal lift

Also covers: tr_canal_lift

**Kernel.** A lock's difficulty is not the chamber, already covered in 85_transport_civil.md's canals_and_locks entry, it is discipline: gates must seal and be operated in a strict fill-then-open sequence, or the lock drains and strands the boat. A canal lift replaces a flight of locks with one vertical motion, a water-filled tank raised by counterweight or engine, which sounds like a pure improvement but rarely is, far more mechanically complex and expensive than an equivalent lock flight, justified only where the level change is large and land for a long flight is unavailable.

**Inputs/prereqs.** Read 85_transport_civil.md canals_and_locks first, this is a supplement.

**Procedure.** Build a standard mitre-gated lock; where justified, build a sealed tank on guided rails, raised by counterweight or engine.

**Fails.** A lock cycles a boat with no water loss beyond one chamber-full per passage.

**Cost/danger.** A lock is comparatively cheap; a lift is a major standalone project. Main risk of a lift is economic over-building.

**Confidence: HIGH** lock (85_transport_civil.md); MEDIUM lift, a rare, niche solution even historically.

---

## Sources and confidence

Most entries describe 18th to 20th century industrial mechanisms with textbook physics and documented failure modes: hot boxes, screwman injuries, boiler explosions, lifeboat swamping. Confidence runs HIGH to MEDIUM on mechanism throughout. Consistent LOW-to-MEDIUM points: hand-achieving factory-grade fabrication tolerance, most acute in valve gear, synchromesh, and precision bearings; anything needing rubber (tl_pneumatic_tyre cluster), which has no Roman substitute and depends on 95_expeditions.md; submarine hulls, where an undetected flaw is unrecoverable; and cost/labour, marked ESTIMATED with stated basis, in artisan-days rather than denarii where wage data was unavailable. No number here is invented; MEASURED marks a historical figure, ESTIMATED/DERIVED marks a reasoned one with basis given.

## Where to go next

- [85_transport_civil.md](85_transport_civil.md) - the freight arithmetic, Roman baseline civil engineering, canals and locks in full, and the case for a railway at all.
- [10_metallurgy.md](10_metallurgy.md) - bulk iron and steel, the bottleneck behind rail rolling, boiler plate, gear steel and hull plating throughout this module.
- [93_energy.md](93_energy.md) - boilers, superheating, safety valves and combustion fundamentals every steam and motor entry above assumes.
- [95_expeditions.md](95_expeditions.md) - where rubber, and anything else flagged here as non-Roman, comes from and what it costs to get.
