# Blind reconstruction of point_contact_transistor's tech tree

Method note: only the goal node's id+name were looked up in the real tree (via a
one-line python snippet). Everything below is derived from the node's NAME plus
general knowledge of the history and physics of technology, worked breadth-first.
No other node in the real tree was consulted while writing this file. Entries are
numbered in the order they were expanded (BFS), and each entry says which of its
own capabilities were pushed onto the queue for later expansion.

Known axioms (per task brief, not re-derived below): `units_standards`,
`arithmetic_positional`, `scientific_method` (founder's starting knowledge), and
`atomic_theory`, `em_theory`, `quantum_solidstate_theory` (compressed physics
chains). Wherever a capability below is essentially "which physics theory this
depends on," it is treated as covered by one of these and not expanded further.

---

## 1. point_contact_transistor / "Point-contact transistor" (ROOT — id+name looked up)

Required capabilities:
1. A semiconductor crystal (germanium) of controlled, high purity
2. Two fine metal point contacts (wires) held extremely close together (tens of micrometers apart) on the crystal surface
3. A precision mechanism to position and press those contacts with controlled, gentle force
4. A way to measure and amplify very small currents/voltages, for testing and for using the output
5. A stable, low-voltage, low-noise DC power supply
6. Empirical/theoretical understanding of metal-semiconductor junction rectification
7. Theoretical understanding of solid-state band structure / charge carriers (electrons and holes) — covered by `quantum_solidstate_theory` axiom, not expanded
8. A chemically prepared (etched) semiconductor surface, free of a thick native oxide/contamination layer
9. Existing vacuum-tube amplifier technology, both as the incumbent the device competes with and as lab instrumentation
10. Basic circuit and measurement theory (Ohm's law, current/voltage/resistance relations)

Queue additions: 1, 2, 3, 4, 5, 6, 8, 9, 10 (7 is an axiom, skipped)

---

## 2. Controlled-purity semiconductor crystal

Required capabilities:
1. Chemical purification of the raw element (germanium was originally a zinc-smelting byproduct) down to near-elemental form
2. A process for growing or casting it as a single, low-defect crystal rather than a polycrystalline lump
3. A high-temperature furnace with a controlled (non-oxidizing) atmosphere to melt/anneal it
4. A way to verify purity after processing, since impurity level directly sets electrical behavior
5. Chemically inert crucibles/containers that survive the melt without contaminating it

Queue additions: 1, 2, 3, 4

---

## 3. Fine wire point contacts positioned to micrometer precision

Required capabilities:
1. Wire-drawing technology capable of producing very fine, uniform-diameter wire
2. A springy, conductive metal alloy (e.g. phosphor bronze, gold) suitable for the contact tips
3. A precision screw/spring adjustment mechanism to bring two points within tens of micrometers of each other without touching
4. Magnifying optics to see the contacts well enough to place them
5. A rigid, vibration-free mount so the gap does not drift

Queue additions: 1, 2, 3, 4

---

## 4. Precision micromanipulator / positioning mechanism

Required capabilities:
1. Machining to fine (sub-millimeter) tolerances — lathes and mills
2. Hardened tool steel for cutting dies and tool bits
3. A way to measure the tolerances achieved (metrology), ultimately traceable to a length standard (`units_standards` axiom)
4. A powered, steady rotational drive for the machine tools (originally line-shaft, by this era electric motors)
5. Fine screw-thread cutting

Queue additions: 1, 2, 4

---

## 5. Sensitive small-current/voltage measurement and amplification

Required capabilities:
1. A moving-coil galvanometer (permanent magnet + wound coil) to detect microampere-scale currents
2. Precision, stable resistor standards for calibration
3. A stable reference voltage source
4. Vacuum-tube amplification, for signals too small for a galvanometer alone (overlaps with entry 9's tech)
5. Fine, insulated conductor wire for wiring up instruments

Queue additions: 1, 2, 3

---

## 6. Stable low-voltage DC power supply (battery)

Required capabilities:
1. Electrochemistry / galvanic cell principles (a reactive metal pair plus electrolyte produces steady EMF)
2. Suitable electrode materials (e.g. zinc, carbon, lead)
3. Electrolyte chemistry that doesn't rapidly degrade the electrodes
4. A sealed or leak-tolerant container

Queue additions: 1

---

## 7. Empirical understanding of metal-semiconductor junction rectification

Required capabilities:
1. Prior experience with crystal-detector ("cat's whisker") rectifiers from early radio
2. Access to naturally semiconducting minerals (e.g. galena) as the historical starting point
3. Basic AC/DC circuit theory to even describe "rectification" as a concept
4. A source of an alternating signal to demonstrate rectification against (radio-frequency oscillation, or simply AC mains)

Queue additions: 1, 2

---

## 8. Chemically prepared (etched) contaminant-free semiconductor surface

Required capabilities:
1. Controlled electrolytic/chemical etching process (current + electrolyte to remove a controlled surface layer)
2. Production and safe handling of the etching acids themselves
3. Clean-handling practice so the freshly etched surface isn't immediately recontaminated
4. A way to judge when etching is sufficient (visual/optical or electrical test)

Queue additions: 1, 2

---

## 9. Existing vacuum-tube amplifier technology

Required capabilities:
1. A vacuum pump able to reach and hold a high vacuum inside a sealed envelope
2. A heated filament/cathode giving thermionic electron emission
3. A vacuum-tight glass-to-metal seal for the envelope and lead-throughs
4. Glassblowing/glassworking craft to shape and seal the envelope
5. A control grid and understanding of how a small grid voltage can modulate a much larger plate current

Queue additions: 1, 2, 3, 4

---

## 10. Basic circuit and measurement theory

Required capabilities:
1. Concept and measurement of voltage, current, resistance as distinct, related quantities (Ohm's law)
2. Conductive wire together with electrical insulation materials to build controlled circuits
3. Ultimately grounded in electromagnetic theory — covered by `em_theory` axiom, not expanded further

Queue additions: 2

---

## 11. Chemical purification of germanium

Required capabilities:
1. Basic inorganic chemistry: converting the element to a volatile/soluble compound (e.g. a chloride) and back, to strip impurities
2. Distillation apparatus and general laboratory glassware
3. A way to chemically analyze the product for remaining impurities
4. Controlled heating for the reactions involved

Queue additions: 2, 3

---

## 12. Single-crystal growth process

Required capabilities:
1. A seed-crystal technique (nucleating growth from a single oriented seed)
2. Precise, steady temperature control at the melt/solid boundary
3. A mechanical pulling and/or rotating mechanism to draw the crystal out slowly and evenly
4. A controlled, non-reactive (inert) atmosphere so the melt doesn't oxidize while growing

Queue additions: 2, 4

---

## 13. High-temperature controlled-atmosphere furnace

Required capabilities:
1. Refractory materials that hold shape and don't contaminate the load at high temperature
2. A heating element technology (resistive heating elements, or induction heating)
3. A way to measure furnace temperature accurately (thermocouple or pyrometer)
4. A supply of purified inert or reducing gas (hydrogen, nitrogen, argon) to exclude oxygen

Queue additions: 1, 2, 3, 4

---

## 14. Purity verification via resistivity measurement

Required capabilities:
1. A precision, known current source
2. A precision voltmeter/galvanometer (already queued in entry 5)
3. Calibrated geometric/electrical standards to convert a reading into a resistivity figure

Queue additions: none new (fully covered by entry 5's descendants)

---

## 15. Fine wire-drawing technology

Required capabilities:
1. Ductile, work-hardenable metal stock
2. Hardened dies with a precisely sized hole
3. A drawing bench / mechanical pulling force
4. Annealing between drawing passes so the wire doesn't become too brittle to continue

Queue additions: 2, 4

---

## 16. Spring-metal alloy for contact wires (phosphor bronze / gold)

Required capabilities:
1. Alloying know-how (combining copper with tin/phosphorus, or working with gold) to get a springy, corrosion-resistant, conductive wire
2. Controlled melting and casting of the alloy stock before drawing
3. Heat-treatment (aging/tempering) to set the springiness

Queue additions: none new (folds into general metallurgy already queued elsewhere)

---

## 17. Precision screw/spring adjustment mechanism

Required capabilities:
1. Precision screw-thread cutting (fine, consistent pitch)
2. Machining to fine tolerances (already queued in entry 4)
3. Spring steel for the return/tension element

Queue additions: 1

---

## 18. Magnifying optics / microscope

Required capabilities:
1. Optical-quality glass manufacture
2. Lens grinding and polishing to precise curvature
3. Optical theory of refraction and focal length — covered by `em_theory`/physics axioms, not expanded
4. A mechanical focusing stage

Queue additions: 1, 2

---

## 19. Moving-coil galvanometer

Required capabilities:
1. A permanent magnet strong and stable enough to provide a steady field
2. Very fine wire, wound into a coil, suspended or pivoted with low friction
3. Electromagnetic induction/force theory — covered by `em_theory` axiom
4. A pointer/scale readout mechanism

Queue additions: 1

---

## 20. Precision resistor standards

Required capabilities:
1. An alloy whose resistivity is stable with temperature (e.g. manganin, constantan) — metallurgy
2. A way to draw/form that alloy into wire of known, reproducible dimensions (already queued as wire drawing)
3. Calibration against an accepted reference standard, ultimately the `units_standards` axiom

Queue additions: none new

---

## 21. Stable reference voltage source

Required capabilities:
1. A standard electrochemical cell (a very stable, low-drift battery construction)
2. The same electrochemistry base as entry 6
3. Careful temperature control to keep the reference stable

Queue additions: none new (folds into entry 6's electrochemistry)

---

## 22. Electrochemistry / galvanic cell principles

Required capabilities:
1. Knowledge of a reactivity series of metals (which metal pairs generate useful EMF)
2. An electrolyte medium that conducts ions between electrodes
3. Containers/vessels that resist the electrolyte chemically
4. A way to measure the resulting voltage/current (already queued, entry 5)

Queue additions: none new

---

## 23. Prior experience with crystal-detector ("cat's whisker") rectifiers

Required capabilities:
1. Early radio-frequency signal generation/reception (spark or continuous-wave transmitters, antennas) providing something to detect
2. Access to naturally semiconducting minerals (galena, etc.) — sourcing/mineralogy
3. A simple fine-wire contact (precursor to entry 3's precision version)

Queue additions: 1

---

## 24. Naturally occurring semiconducting minerals as historical precedent

Required capabilities:
1. Basic mineralogy/prospecting to identify and source such minerals
2. No further manufacturing capability implied beyond sourcing

Queue additions: none (terminal/leaf capability)

---

## 25. Controlled electrolytic/chemical etching process

Required capabilities:
1. A DC current source (already covered, entry 6)
2. An electrolyte solution appropriate to the semiconductor being etched
3. Timing/process control to stop etching at the right depth
4. Rinsing/drying steps that don't recontaminate the surface

Queue additions: none new beyond entry 26 (acid production)

---

## 26. Production and safe handling of etching acids

Required capabilities:
1. Industrial acid manufacture (e.g. nitric acid, hydrofluoric acid) — chemical industry base
2. Acid-resistant containers (glass, wax-lined, ceramic)
3. Ventilation/safety practice for corrosive fumes

Queue additions: 1

---

## 27. Vacuum pump technology

Required capabilities:
1. A mechanical piston or rotary pump mechanism (machining, again entry 4's descendants)
2. Airtight seals and gaskets
3. Understanding of gas pressure and vacuum physics — covered by physics axioms
4. Lubricants that function under partial vacuum

Queue additions: 2

---

## 28. Heated filament / thermionic cathode

Required capabilities:
1. A refractory metal wire (tungsten, or oxide-coated nickel) able to survive sustained heating
2. A way to pass controlled current through it to heat it (already covered by circuit basics)
3. Understanding of thermionic emission (the "Edison effect")

Queue additions: 1

---

## 29. Vacuum-tight glass-to-metal seal

Required capabilities:
1. Glassblowing/glassworking craft (already queued next)
2. A metal alloy whose thermal expansion closely matches the glass, so the seal doesn't crack on heating/cooling
3. A furnace/torch capable of local, controlled glass softening

Queue additions: 1

---

## 30. Glassblowing / glassworking craft

Required capabilities:
1. Glass manufacture itself (silica + fluxing agents, melted and formable)
2. A furnace or torch providing localized high heat
3. Hand tools and skill for shaping molten glass
4. Annealing ovens so finished glassware doesn't retain stress and shatter

Queue additions: none new (glass manufacture folds into furnace/refractory technology already queued)

---

## 31. Precision machining (lathes and mills)

Required capabilities:
1. Hardened tool steel for cutting edges (already queued, entry 4)
2. A powered, steady rotational drive — by this era, electric motors
3. A rigid machine frame/bed manufactured to its own precision (bootstrapping problem, resolved historically by progressively refined machine tools)
4. Metrology to check the work (already covered under `units_standards`)

Queue additions: 2

---

## 32. Hardened tool steel / cutting-die manufacture

Required capabilities:
1. Alloying steel with carbon/other elements for hardenability
2. Controlled heat-treatment (quench and temper) to achieve hardness without brittleness
3. A furnace capable of the needed temperatures (already queued, entry 13)

Queue additions: none new

---

## 33. Metal annealing and heat treatment

Required capabilities:
1. Controlled-temperature furnace (already queued, entry 13)
2. Understanding of how heating/cooling rate changes metal grain structure
3. Cooling media (oil, water, air) matched to the desired result

Queue additions: none new

---

## 34. Electric motor technology

Required capabilities:
1. Electromagnetism (already covered, `em_theory` axiom)
2. Wound copper coils and a commutator or equivalent for continuous rotation
3. A source of electrical power to drive it (already covered)
4. Bearings low-friction enough for sustained rotation

Queue additions: none new (bearings folds into precision machining already queued)

---

## 35. Distillation apparatus and laboratory glassware

Required capabilities:
1. Glass manufacture and glassblowing (already queued, entry 30)
2. Controlled heating (already queued)
3. Condenser design (cooling a vapor back to liquid)

Queue additions: none new

---

## 36. Precise temperature control (thermocouple/pyrometer)

Required capabilities:
1. Knowledge of the thermoelectric (Seebeck) effect for thermocouples
2. Two dissimilar metal wires joined at a junction
3. A calibrated meter to read the small generated voltage (already covered, entry 5's descendants)

Queue additions: none new

---

## 37. Refractory furnace-lining materials

Required capabilities:
1. High-melting-point minerals/ceramics (fireclay, magnesia, alumina)
2. Processing (firing) them into brick or castable form
3. Sourcing/mining of the raw refractory minerals

Queue additions: none new (terminal, folds into general ceramics/mining)

---

## 38. Inert/controlled gas atmosphere supply

Required capabilities:
1. A method to generate or purify a gas such as hydrogen or nitrogen (chemical or fractional-distillation-of-air methods)
2. Piping/valves that hold gas pressure without leaks (already covered, entry 27's sealing)
3. Drying/purifying stages to strip out oxygen and moisture

Queue additions: none new

---

## 39. Airtight seals and gaskets (general)

Required capabilities:
1. A resilient, deformable material (early: leather/wax; later: rubber) that conforms under compression
2. Precisely machined mating surfaces (already covered, entry 4/31)

Queue additions: none new

---

## 40. Industrial acid manufacture (nitric / hydrofluoric)

Required capabilities:
1. A source of the base raw materials (e.g. nitrogen fixation for nitric acid, fluorspar mineral for hydrofluoric acid)
2. Chemical process control (reaction vessels, temperature, concentration)
3. Corrosion-resistant vessels for handling the product (already covered, entry 26)

Queue additions: none new

---

# FINAL DEDUPLICATED CAPABILITY LIST (Phase One conclusion)

1. Controlled-purity semiconductor crystal (germanium), chemically purified from raw source material
2. Single-crystal growth process (seeded, pulled/cooled under control)
3. High-temperature furnace with controlled/inert atmosphere
4. Purity/quality verification via resistivity measurement
5. Fine wire-drawing technology
6. Springy conductive contact-metal alloy (phosphor bronze / gold)
7. Precision screw-thread cutting and fine mechanical adjustment mechanisms
8. Magnifying optics / microscope (optical glass + lens grinding)
9. Moving-coil galvanometer / sensitive current-voltage measurement
10. Precision resistor standards (stable-resistivity alloys)
11. Stable low-voltage DC power supply (battery electrochemistry)
12. Empirical metal-semiconductor rectification knowledge (crystal/cat's-whisker detectors)
13. Naturally occurring semiconducting minerals as historical starting point
14. Early radio-frequency generation/reception (context driving detector work)
15. Controlled electrolytic/chemical etching of semiconductor surfaces
16. Industrial acid manufacture and safe handling (nitric, hydrofluoric, etc.)
17. Vacuum pump technology
18. Heated filament / thermionic cathode (refractory metal wire, e.g. tungsten)
19. Vacuum-tight glass-to-metal sealing (matched thermal-expansion alloys)
20. Glassblowing / glassworking craft and glass manufacture
21. Precision machining (lathes, mills) to fine tolerances
22. Hardened tool steel and cutting-die manufacture
23. Metal annealing / heat-treatment processes
24. Electric motor technology (to drive machine tools, pumps, etc.)
25. Distillation apparatus and general laboratory glassware
26. Precise temperature control (thermocouples/pyrometers)
27. Refractory furnace-lining materials
28. Inert/controlled gas atmosphere supply (purified H2, N2, etc.)
29. Airtight seals and gaskets
30. Basic circuit/measurement theory (Ohm's law) plus insulated conductor wire
31. Vacuum-tube amplifier technology as a whole (assembled from 17-20 plus grid-control concept)
32. Rigid, vibration-free precision mounting/positioning fixtures

(Physics/chemistry axioms deliberately not re-derived: `atomic_theory`, `em_theory`,
`quantum_solidstate_theory`, plus founder-knowledge axioms `units_standards`,
`arithmetic_positional`, `scientific_method`.)
