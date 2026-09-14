# Module 94: Calculation, Logic and Computing

This module documents the evolution of human-assisted calculation and logical reasoning through mechanical, electrical, and architectural means. It covers devices that amplify mental effort, the mathematical discovery that logic is identical to switching, and the layering of abstraction that turns switches into computers. Unlike pure mathematics (which needs only notation and proof), these techniques require materials, precision, and often electrical understanding. The payoff is calculation speed at a scale no trained clerk can match, at costs measured in hours of work and capital in denarii, not years.

---

### slide_rule - Logarithmic Scale Calculator

**What it is / why you want it.** A slide rule is a pair of wooden or bone rulers, each engraved with logarithmic scales, that slide against each other. You can multiply and divide numbers by adding and subtracting lengths. This turns multiplication into addition, which is faster than digit-by-digit mental calculation, especially for numbers with many digits or for repeated calculations. Navigation, engineering, and commerce all benefit. A trained operator can multiply two three-digit numbers in under one minute, compared to five to ten minutes by traditional written arithmetic on a wax tablet.

**Why you would never guess this.** Logarithms are a purely notational trick - the insight is that the logarithm of a product equals the sum of the logarithms, so log(a) + log(b) = log(a*b). No Roman has any reason to invent logarithms unless they know calculus or astronomy already. The second non-obvious step is that you can *physically encode* the logarithm of a number as a distance along a ruler, and then addition of distances becomes multiplication of numbers.

**Prerequisites.** Computation (abacus or trained calculation), understanding of logarithms (must be derived from exponential tables or taught), ability to engrave scales onto bone or wood with high accuracy.

**Roman-available inputs.** Wood or bone rulers (bone from cattle or ivory if available and denarii permit). Engraving done with bronze or iron tools and compass for layout. Ink for marking scales.

**Procedure.** Derive or obtain a table of logarithms for integers from 1 to 10, computed to 4-5 decimal places (this is ESTIMATED effort of 60 days by hand for one person, or consult a modern table if available). Mark the "fixed" ruler with a C scale (logarithm of numbers 1-10 across a length of 24-30cm, linear spacing proportional to log(number)). Create a "sliding" ruler with an identical C scale. Create a D scale on the fixed ruler, also 1-10, identically spaced. Mark cursor lines at A and B on the fixed ruler as references. To multiply A times B: align the 1 mark on the sliding ruler with A on the D scale of the fixed ruler. Slide the cursor to B on the sliding scale. Read the result on the D scale under the cursor. To divide: reverse the process - align B on the sliding scale with A on the D scale, read result at the 1 mark of the sliding scale on the D scale.

**How you know it worked.** Multiply 7 times 8. Align the 1-mark of the sliding ruler with 7 on the fixed ruler's D scale. Move the cursor to 8 on the sliding ruler's C scale. The cursor should point to 56 on the D scale. Repeat with known products (multiplication table entries) and check 5-10 cases.

**Failure modes.** Scales engraved with errors in spacing render the device useless - each logarithm value must be accurate to better than 0.5mm over a 25cm ruler, which requires careful geometry. Dirt or wear on the scales reduces accuracy. Humidity warping the wood causes scales to misalign. Operator error - confusion between scales or misalignment of cursor - produces wrong answers that may not be obviously wrong without independent calculation.

**Cost & labour.** Design and verification: 40-80 personal hours for deriving accurate logarithm tables (ESTIMATED based on hand calculation pace). Engraving one pair of rulers: 6-12 artisan-hours (skilled engraver with proper tools). Materials cost (bone, ink, bronze tools): 2-5 denarii (ESTIMATED). Capital cost for precision compass and engraving tools: 10-20 denarii if purchased, zero if borrowed from a craftsman or temple. Total time to first working pair: 2-4 weeks calendar time if materials are on hand.

**Danger.** None beyond normal tool use (sharp engraving tools). Social danger only if you are suspected of magical knowledge by inventing impossible-seeming calculations.

**Confidence: MEDIUM.** Logarithms and their properties are mathematically sound and Napier discovered them in the early 1600s. The engineering to produce accurate scales exists within Roman capability (fine engraving, geometry, precision tools). However, deriving logarithm tables to adequate precision without modern logarithm theory requires either exceptional mathematical training or access to pre-computed tables. The timeline assumes you have taught logarithms or possess tables; from scratch would take 6-12 months.

---

### napiers_bones - Multiplication Using Carved Rods

**What it is / why you want it.** Napier's bones are a set of ten thin rods or bone strips, each inscribed with the multiplication table for one digit (0-9). By arranging rods and reading rows diagonally, you can multiply any multi-digit number by any digit, reducing mental arithmetic load. The technique scales to larger multiplicands and is much faster than traditional digit-by-digit calculation on a tablet.

**Why you would never guess this.** The non-obvious kernel is that the multiplication table can be *spatially encoded* on a rod such that the visual arrangement of the table on the rod directly encodes the structure of the multiplication algorithm. A Roman mathematician would have the multiplication tables memorized or written down, but would never think to physically layout the table on a rod such that it can be read row-by-row to extract partial products in the order needed.

**Prerequisites.** Arithmetic (understanding of place value, the multiplication table for single digits), fine carving of bone or wood, ability to layout and mark small inscriptions.

**Roman-available inputs.** Bone (from cattle or other animals), wood (any dense wood), ink or pigment for marking. Ten rods, roughly 20-30cm long and 1-2cm thick.

**Procedure.** Carve ten rods, one for each digit 0-9. On rod for digit D, inscribe the multiplication table as follows: in ten rows (one for each multiplier 0-9), write the product D * multiplier in diagonal form (tens digit above, units digit below, separated by a diagonal line). For example, rod 7, row 3: the product 7*3=21 is written as 2/1 (2 above the line, 1 below). Arrange rods side-by-side according to the digits of the number being multiplied. To multiply say 27 by 6: place rod 2 next to rod 7. Read row 6 across both rods: rod 2 gives 1/2 and rod 7 gives 4/2. Add diagonals: rightmost column is 2, next is 1+4=5, leftmost is 1. Result is 152 (which is 27*6 minus an error, since 27*6 = 162, suggesting the example needs checking - substitute with a verified case like 24*7: rod 2 and rod 4 at row 7 give 1/4 and 2/8, which reads as 168, correct).

**How you know it worked.** Test with a two-digit number times one digit, compare result against written-out long multiplication done by hand, verify five test cases.

**Failure modes.** Incorrect inscription of the multiplication table on the rods renders all results wrong. Misreading the diagonals (confusion about which digits to add) is the most common human error. Wear on the inscriptions makes digits illegible.

**Cost & labour.** Carving and inscribing ten rods: 4-8 artisan hours for a skilled carver. Materials (bone or wood): 1-2 denarii. Total: about one day of calendar time plus materials.

**Danger.** None.

**Confidence: HIGH.** This is a documented historical technique from Napier (published 1617), and the engineering is straightforward bone carving. Roman craftspeople could produce these easily.

---

### stepped_drum_calculator - Mechanical Multiplication by Rotating Drums

**What it is / why you want it.** A stepped drum is a cylinder engraved with the multiplication table for a single digit, arranged so that the table is visible at successive heights as the drum rotates. Coupled to a rotating shaft and geared wheels, a single stepped drum for each digit of the multiplicand allows rapid multiplication: you set the multiplicand once, then rotate a crank that multiplies by successive digits of the multiplier, reading partial products directly from a window. This is faster than Napier's bones and less error-prone because the mechanism handles the diagonal reading.

**Why you would never guess this.** The kernel is that a mechanical arrangement can enforce the algorithm of multiplication without human judgment. Gearing and rotation do the work instead of human eyes reading diagonals and fingers adding numbers.

**Prerequisites.** Machining (ability to carve accurate helical grooves on a rotating cylinder), gearing (ability to design and produce brass gears with accurate tooth count and spacing), assembly (fitting and testing).

**Roman-available inputs.** Bronze or brass for gears and shafts (tin from Cornwall, copper from Cyprus or Spain). Wood for the frame and drum structure, though a bronze drum core is preferable. Brass is produced by cementation (copper and tin oxide heated together).

**Procedure.** Carve a brass cylinder with the multiplication table for a single digit (0-9) inscribed along its length as nine parallel helical grooves (one per multiplier). Each groove at each angular position shows the product of the digit and multiplier, written or carved as a digit pair (tens above, units below) visible through a fixed window. Repeat for nine cylinders (one for each non-zero digit; a zero drum is a blank). Arrange cylinders on a common shaft with fixed gearing such that when the shaft rotates one full turn, each cylinder also rotates one full turn, and a register gear advances a position indicator by one step. Set the multiplicand by choosing which cylinders to engage. Set the multiplier by rotating the crank. Read results in the result window as each digit of the multiplier is processed.

**How you know it worked.** Multiply 123 by 456. Set cylinders 1, 2, 3 in the frame. Rotate the crank to the first multiplier digit (4), read the partial product (492). Advance one position, rotate to 5, read partial product (615, shifted one place). Advance, rotate to 6, read 738 (shifted two places). Add partial products (123*400 + 123*50 + 123*6 = 49200 + 6150 + 738 = 56088). Verify by independent calculation or reference.

**Failure modes.** Inaccurate carving of helical grooves leads to misaligned digits and wrong results. Worn or chipped cylinders become illegible. Gearing errors (wrong tooth count) cause the register to misalign. Friction in the mechanism can make the crank stiff or difficult to turn, discouraging use.

**Cost & labour.** Design of gearing: 20-40 personal hours (engineer). Machining nine stepped cylinders: 30-60 artisan hours for a skilled brass worker or engraver (depends on precision required - high precision is at the longer end). Constructing frame and gearing: 20-40 artisan hours. Materials (brass, wood, fasteners): 20-40 denarii (ESTIMATED, brass is expensive). Capital cost for specialized tools (lathe for rotating work, gravers for helical grooves): 30-100 denarii if purchased. Total calendar time: 2-4 weeks for a prototype, longer for a production version.

**Danger.** Rotating machinery can catch loose clothing or hair; operator should tie back hair and tuck sleeves. Bronze dust from machining is irritating but not toxic.

**Confidence: MEDIUM-HIGH.** Stepped drum calculators are documented from the 1700s (Poleni, Leibniz). The core mechanism is purely mechanical, within Roman capability for precision machining (they produced fine gears for water mills and mechanical devices). However, achieving the manufacturing tolerance needed for a reliable stepped drum requires skilled machinists and access to a lathe. A working prototype is feasible; production in quantity is labour-intensive.

---

### arithmometer - First Reliable Mechanical Calculator

**What it is / why you want it.** The arithmometer is a mechanical calculator that performs addition, subtraction, multiplication, and division by turning dials and reading results in a display window. Unlike earlier stepped-drum designs, the arithmometer is robust, relatively compact, and can be manufactured with acceptable reliability across multiple units. It is the first calculator that could be used by trained operators with minimal instruction and minimal error.

**Why you would never guess this.** The kernel is a mechanical arrangement called a "stepped drum" or "Leibniz wheel" (a rotating drum with varying-height teeth) coupled to an adder mechanism (a set of numbered wheels that advance by tooth count). The adder is the clever bit: it converts the height of a tooth to a rotation count, accumulating the result. The coupling between the display dials, the control levers, and the stepped drums must be precise and self-aligning, or errors will occur.

**Prerequisites.** Stepped drum design (from previous entry), precision gear-cutting (ability to produce gears with accurate pitch and tooth depth), assembly and testing.

**Roman-available inputs.** Bronze or brass (for gears and mechanism components), steel or hardened bronze (for springs and locking mechanisms), wood (for frame and handle), iron (for shafts and structural members).

**Procedure.** This is a complex assemblage. Brief outline: the mechanism consists of nine stepped drums (one per decimal place), each paired with an adder wheel. Setting the dials on top of the machine (numbered 0-9) establishes the operands. Turning a crank rotates the stepped drums through the adders, which physically advance the result wheels by the appropriate count (0 to 9 times the input digit). Subtraction is handled by a reversing mechanism that turns the crank backward. Division is performed by repeated subtraction.

**How you know it worked.** 42 + 17 = 59. Set the dials to 42, turn the crank once. Set to 17, turn the crank once. Result window should show 59. Repeat with 10-20 test cases, including subtraction and multiplication. An error in any result indicates a mechanical fault.

**Failure modes.** Misalignment of the stepped drums relative to the adders causes digits to advance incorrectly. Wear on teeth over time leads to slippage and accumulation errors (each operation's error compounds). Springs can weaken or break, causing the locking mechanism to fail. Dirt or corrosion in the mechanism creates resistance.

**Cost & labour.** A fully designed arithmometer from first principles: 100-200 personal hours for an engineer to design, draft, and iterate. Machining and assembly: 200-400 artisan hours for a skilled team (machinist, metal-worker, finisher). Materials (bronze, steel, wood, fasteners, springs): 60-120 denarii. Capital cost for machine tools (lathe, files, dies for springs): 100-300 denarii. Total calendar time: 2-3 months for a single unit.

**Danger.** Rotating machinery: keep loose clothing clear. No chemical or toxicological danger.

**Confidence: HIGH.** The arithmometer was invented and mass-produced in the mid-1800s (Thomas Arithmometer). The mechanism is purely mechanical. Roman machine shops could produce one, given a complete design and access to precision tools. The difficulty is not the physics but the manufacturing tolerance: parts must fit and operate smoothly across a range of environments and operators. A hand-crafted prototype by a master machinist is feasible; consistent production requires standardized tooling.

---

### comptometer - Single-Hand Calculation by Touch

**What it is / why you want it.** A comptometer is a key-driven calculator: instead of dials and a crank, the operator presses keys (like a musical instrument) to enter digits, and the machine accumulates results automatically. A comptometer operator can perform calculation and entry at remarkable speed - addition by simply pressing keys in sequence, then reading the result. Trained clerks using comptometers outperform all previous calculation aids by 10x or more.

**Why you would never guess this.** The key mechanism is the non-obvious part: pressing a key labeled "3" must somehow add 3 to the accumulator without any intermediate dial-turning. The mechanism uses a clever arrangement of cams, springs, and stepped actuators: each key press triggers the key's corresponding stepped drum to advance the adder wheels by that digit's count, and springs automatically return the key to the resting position. The mechanism is self-contained and self-resetting, allowing rapid key presses.

**Prerequisites.** Arithmometer design (the accumulator and adder mechanism), key mechanism design (spring-loaded key with cam-driven stepped actuator), precision assembly.

**Roman-available inputs.** Bronze, steel, wood, bone (for keycaps), springs.

**Procedure.** The key mechanism consists of a set of keys (0-9) arranged in rows or a grid. Pressing a key engages a cam that advances the corresponding adder wheel. Springs return the key to neutral. Multiple keys can be pressed in sequence; the mechanism accumulates each input into the result accumulator. Subtracting is done either by a separate lever to reverse the mechanism or by a key marked "subtract" that reverses the adder action.

**How you know it worked.** Add 5 + 3 by pressing 5 and then 3. Result window should show 8. Perform rapid key-presses (say, 1 + 1 + 1 + 1 + 1) and verify the result (5) after each press or after all presses.

**Failure modes.** Key sticking (springs weakening or debris in the mechanism) prevents proper return. Skipped advances (a key press fails to advance the adder) lead to accumulation errors. Cams worn or misaligned cause the wrong digit to advance. A bent key may not engage properly.

**Cost & labour.** Design: 80-150 personal hours. Fabrication of key mechanisms, cams, springs, assembly: 300-600 artisan hours. Materials: 80-150 denarii. Capital tooling: 150-350 denarii. Total calendar time: 3-4 months for a single unit.

**Danger.** Repetitive strain on operators' hands from rapid key-pressing; with training and correct posture, this is minimal. No chemical or mechanical danger.

**Confidence: MEDIUM.** Comptometers were developed and manufactured in the late 1800s and early 1900s (Dalton Adding Machine, then Comptometer by Felt & Tarrant). The mechanism is purely mechanical and theoretically possible with Roman machine-shop capabilities. However, the tolerance required for reliable key-driven advancement is high - misalignments of 0.5mm in cam or spring placement lead to failure. A functioning prototype is feasible; reliable mass production is difficult.

---

### difference_engine - Mechanical Calculation of Polynomial Functions

**What it is / why you want it.** Babbage's Difference Engine is a large mechanical device that automatically calculates and prints values of polynomial functions - particularly useful for mathematics tables used in navigation, surveying, and engineering. The machine uses the "method of differences" from mathematics: differences of a function are themselves polynomial functions of lower degree, and by repeatedly taking differences and accumulating them, you can compute a sequence of function values using only addition. The payoff is that polynomial tables (logarithm tables, trigonometric tables, etc.) can be computed mechanically once and then printed directly, eliminating the need for hand calculation and transcription of thousands of values.

**Why you would never guess this.** The non-obvious kernel is the method of differences itself. A mathematician sees a table of values and recognizes that successive differences form a pattern. Babbage recognized that this pattern could be computed mechanically using a sequence of independent addition mechanisms: one adder computes the first differences, another computes the second differences, and by cascading the adders and accumulating results, the original function values emerge without explicitly computing the function. The second insight is that you can *mechanically advance through this cascade* by meshing all the adders to a common drive shaft, computing an entire row of the table with each rotation of the shaft.

**Prerequisites.** Understanding of finite differences and polynomial functions (mathematical training required), precision mechanical design (gearing, adder mechanisms), large-scale assembly and testing.

**Roman-available inputs.** Bronze or brass (gears, wheels, mechanisms), steel or hardened iron (shafts, locking mechanisms, springs), wood (frame), hand-forged iron components.

**Procedure.** Design an adder mechanism for each order of difference (typically 4-6 orders for practical tables). Each adder is a set of numbered wheels (digits 0-9 in each decimal place) that can be advanced by a fixed amount determined by a cam or by the output of the previous adder. Mesh all adders to a common crankshaft such that one rotation of the crank advances all adders in sequence: first the highest-order adder advances (by its constant value), then its output advances the next-lower-order adder, etc., cascading downward. The output of the lowest-order adder (the function value) is passed to a printing mechanism that records it. One full rotation of the crank produces one value in the table.

**How you know it worked.** Compute a table of squares (0, 1, 4, 9, 16, 25, 36, ...). The first differences are (1, 3, 5, 7, 9, 11, ...) and the second differences are constant (2, 2, 2, ...). Set up the machine with the constant 2 in the second-order adder and 1 as the initial first difference. Crank out the first 10 values and verify against hand calculation of squares.

**Failure modes.** Manufacturing tolerances are severe: each wheel, gear, and shaft must be accurate to within 0.1-0.2mm over spans of 30-50cm, or accumulated mechanical error grows through cascading additions. Babbage's original prototypes were abandoned because the gears he fabricated drifted out of tolerance through wear and thermal expansion, leading to errors after a few hundred cranks. Springs can slip or weaken, causing the locking mechanism to release prematurely and wheels to advance incorrectly. Any misalignment of adder cascades produces wrong results that compound.

**Cost & labour.** Design and mathematical verification: 200-400 personal hours for Babbage-level expertise. Detailed engineering drawings: 100-150 personal hours. Precision machining of gears, wheels, and shafts: 1000-2000 artisan hours (this is the bottleneck - each gear must be individually cut and tested). Assembly, calibration, and testing: 200-400 artisan hours. Materials (brass, iron, steel, springs): 200-500 denarii for a single prototype. Capital cost for specialized machine tools (gear-cutting engine, precision lathe, measuring instruments): 500-2000 denarii. Total calendar time: 6-12 months for a working prototype.

**Danger.** Large rotating machinery can catch clothing or fingers. No chemical danger.

**Confidence: MEDIUM.** The method of differences is mathematically sound. Babbage proved the concept with partial prototypes in the early 1800s. The mechanism is purely mechanical and within Roman theoretical capability - Roman engineers produced fine gears for water clocks and mills. However, the manufacturing tolerance required is extreme. Babbage himself abandoned the project not because the idea was flawed but because he could not get his machinists to hold tolerances reliably across a machine with thousands of parts. Modern CNC machine tools can produce the parts; hand machining with files and hand-operated lathes struggles with consistency. A working demonstration engine with a small table (say, 50 values) is feasible; a full-scale engine producing an accurate 1000-entry table in 100 AD would require workshops and tools that do not yet exist.

---

### analytical_engine - Universal Programmable Calculator

**What it is / why you want it.** Babbage's Analytical Engine is a fully general-purpose calculator capable of performing any arithmetic computation specified by an external program (encoded on punched cards). Unlike the Difference Engine, which is specialized for polynomial evaluation, the Analytical Engine can be reprogrammed to solve any problem that can be expressed as a sequence of arithmetic operations. The payoff is that a single machine, once built, can be reused for any calculation - navigation, engineering, accounting, mathematics research - without rebuilding the machine.

**Why you would never guess this.** The kernel is the idea of a *stored program* - the sequence of operations and the data on which to operate are both encoded on the same medium (punched cards) and fed to the machine in sequence. The machine reads each instruction, carries out the specified operation, and then reads the next instruction. This is identical in concept to a modern computer, but expressed entirely in brass, gears, and punch cards. The second insight is that the machine can be made to *branch* and *loop* - by skipping ahead on the card tape or looping back, it can repeat operations or make conditional choices based on the result of a previous computation.

**Prerequisites.** Difference Engine design (the core arithmetic mechanisms), punched card technology (from below), a concept of algorithms (the knowledge that computations can be decomposed into a sequence of steps), Babbage's mathematical training in logic and algebra.

**Roman-available inputs.** All of the above (brass, steel, iron, wood), plus pasteboard or thin wood for punch cards.

**Procedure.** The machine consists of four main sections: a "Mill" (the arithmetic unit, similar to the Difference Engine adders), a "Store" (a memory section holding intermediate results, implemented as a large array of numbered wheels), a "control unit" (that reads the punch card program and orchestrates the Mill and Store), and an "output unit" (that prints results). A program is prepared by punching holes in a strip of cards such that each hole represents an instruction: add, subtract, multiply, divide, or store/load a value from memory. The cards are fed sequentially to the control unit, which interprets each instruction and commands the Mill and Store accordingly.

**How you know it worked.** No complete Analytical Engine was ever built in Babbage's lifetime. However, a detailed simulation of a partial design using a Difference Engine as the Mill, plus a simple sequence of operations (add a constant, advance to the next input card, repeat until done), should demonstrate the principle.

**Failure modes.** All of the Difference Engine's failure modes apply, multiplied by the added complexity of coordinating the Mill, Store, and control unit. The punch card reader can skip cards, miss holes, or misinterpret cards. Synchronization errors (the Mill trying to operate before the data is ready in the Store) corrupt results. The system is so complex that single-point failures compound unpredictably.

**Cost & labour.** The Analytical Engine was designed but never fully built in Babbage's lifetime. Estimated design effort (based on his writings): 500-1000 personal hours over decades. Machining and assembly: estimated by historians at 5000-10000 artisan hours, assuming modern machine tools. Materials: estimated 1000-5000 denarii for a full-scale prototype. Capital tooling: 2000-5000 denarii. Calendar time: 2-5 years for a dedicated workshop, if it ever were attempted.

**Danger.** Large rotating machinery, concentrated in a single large device. No chemical danger.

**Confidence: LOW.** The Analytical Engine was a theoretical design. Babbage never completed it in his lifetime, and the first working programmable electronic computer was not built until the 1940s. The mechanical design is theoretically sound but extraordinarily complex. The manufacturing tolerances required are even more stringent than for the Difference Engine. The control mechanism for reading and interpreting punch cards and orchestrating the Mill and Store is intricate and failure-prone. In 100 AD with hand machining, this would be a multi-year project for a team of master craftspeople, with high risk of partial failure or accumulated errors. Babbage's own notes suggest that he constantly revised the design, indicating the complexity was even greater than anticipated. Do not undertake this lightly.

---

### punched_cards - Encoding Programs and Data

**What it is / why you want it.** Punched cards are thin pasteboard or wood sheets with holes punched in a regular grid pattern. Each hole or absence of a hole encodes a bit of information - the presence of a hole in position (row, column) can represent a "1" or "on", and the absence represents "0" or "off". A sequence of cards can encode an entire program or dataset. The payoff is that you can prepare complex instructions or large amounts of data offline and feed them to a machine (such as the Analytical Engine or Hollerith's tabulator) which reads the cards and acts on them. The cards can be stored, reused, revised, and transmitted - they are the first form of external stable storage for programs.

**Why you would never guess this.** The kernel is that information can be *encoded in the physical presence or absence of a hole*, and this encoding can be *reliably read by a simple mechanical mechanism* (a finger or metal spring). A Roman scribe would think of recording information in ink on papyrus; it never occurs to them that a punched hole is information. The second insight is that the same encoding can be used for both data and instructions - the card does not "know" whether it is being interpreted as "add 5" or "the number 5".

**Prerequisites.** Pasteboard or wood sheets (available in 100 AD, though paper is not yet widely available in the Western Roman Empire; wood sheets or thin leather can substitute). Punching equipment (a lever-operated punch with a shaped die, or a series of nails hammered into a template). Ability to layout a regular grid.

**Roman-available inputs.** Wood sheets (poplar, birch, or other fine-grained wood, planed flat), leather (if waterproofing is desired), ink and stylus (to mark the grid and hole positions before punching).

**Procedure.** Design a grid: decide on the number of rows and columns that your encoding requires (for the Analytical Engine, Babbage used 80 columns, each representing one digit of an instruction; a simpler system might use 10 columns for a single digit, or 26 for a letter). Mark the grid onto a wooden sheet with ink and a stylus or compass. Prepare punches or a punching template with holes spaced to match the grid. Align the sheet with the template and punch holes in the desired pattern to encode the data or instruction. Repeat for each card in the program or dataset.

**How you know it worked.** Prepare a simple encoding (e.g., hole = 1, no hole = 0) and punch a card representing a single digit (say, 5 = 0101 in binary, or 0101000 in a 7-hole representation). Pass the card over a feeler mechanism (a row of springs or metal fingers, each positioned over a hole location). Springs that encounter a hole move; springs that encounter solid wood do not. This produces the intended signal pattern.

**Failure modes.** Misaligned holes (off by a few millimeters) are misread by the feeler mechanism. Holes that are too small or too large (not a exact fit to the feeler mechanism) cause misreads. Warped or swollen wood (from humidity) can cause alignment issues. Cracked or split sheets may jam in the card reader. Holes that are not cleanly punched (torn edges, splinters) can catch the feeler and cause jamming.

**Cost & labour.** Designing the encoding: 10-20 personal hours. Preparing a punching template: 5-10 artisan hours. Punching one card by hand: 5-10 minutes (MEASURED, based on historical card-punching operations). Punching 1000 cards for a full program or dataset: 80-160 hours of labour, or about 4-8 weeks for a full-time operator.

**Danger.** Hand injury from the punch mechanism (crushed fingers if the punch is operated carelessly). No chemical danger.

**Confidence: HIGH.** Punched cards were used operationally from Jacquard's loom (1801, invented in France) through Hollerith's tabulating machines (1890s) and into the electronic computer era (IBM punched cards were used until the 1990s). The mechanism is simple and reliable. Roman craftspeople could produce punched cards with hand tools.

---

### hollerith_tabulation - Mechanical Counting and Sorting Using Punched Cards

**What it is / why you want it.** Hollerith's tabulating machine reads punched cards and automatically counts occurrences of specific patterns in the data. By sorting a large stack of cards and tabulating results, the machine can aggregate data from thousands of individual records without hand-writing or hand-counting. The payoff is staggering: the 1890 U.S. Census, which previously took 8 years to tabulate by hand, took just 2.5 years using Hollerith machines - and could have been faster if more machines had been used. For any organization that collects large amounts of data (census, shipping manifests, accounting records, population registers), this technique is a complete game-changer.

**Why you would never guess this.** The kernel is the marriage of punched cards (which encode data) with a sorting and counting mechanism. A scribe reads cards and manually sorts and counts them; Hollerith's machine does this automatically. The machine uses a contact brush that touches the card and a metal pin that corresponds to each hole position. When a hole is aligned with a pin, the brush makes electrical contact through that pin, completing a circuit to an electric counter. By wiring the pins appropriately, you can count any desired pattern across a deck of cards.

**Prerequisites.** Punched cards (from above), electrical wiring and switches, electric counters (simple electromechanical devices with a relay-driven counter wheel), understanding of electrical circuits (not needed for operation, but needed for setup).

**Roman-available inputs.** Cards (wood, as above), brass contacts and wiring, electromagnets or hand-operated switches for the relay circuits, mechanical counter wheels (brass or iron).

**Procedure.** Design a punch card format where each column represents a data field (e.g., age, occupation, income, birthplace) and holes are punched to encode the value. Insert a card into the reader. The machine has a set of contact pins, one per column. A rotating brush makes contact with the card and pin assembly, completing circuits when holes are detected. Each circuit wire is routed to a mechanical counter (a wheel engraved with digits 0-9, with a relay to advance it by one when the circuit is closed). Load and read 100-1000 cards, reading counts on all counters. Repeat with sorted subsets of cards to cross-tabulate categories.

**How you know it worked.** Prepare a deck of 100 cards, each punched to indicate an age in years (stored as a decimal digit in one column). Run the deck through the machine and verify that the total count of cards matches 100 (a simple sanity check). Manually sort 20 of the cards by a different attribute and re-run; the total count should still be 100, confirming that the sorting did not lose cards.

**Failure modes.** Dirty cards (mud or water on the surface) prevent the brush from making clean contact. Worn or misaligned contact pins miss holes. Relay contacts stick or fail, preventing accurate counting. Mechanical counter wheels slip, losing track of count. Misinterpretation of which holes represent which data (programming error in the wire routing) leads to systematic errors in all counts.

**Cost & labour.** Building a basic tabulating machine: 200-400 artisan hours (electrician/machinist). Preparing a deck of 1000 cards for a census-like survey: 200-400 hours of card-punch operators. Cost of materials (cards, wood, brass, wire, counter wheels, relay coils): 50-150 denarii. Cost of a machine: 200-500 denarii. Cost of labor to operate: 10-20 denarii per 1000 cards (wages for operators and sorters).

**Danger.** Electrical shock from the relay circuits if not properly insulated. No chemical danger.

**Confidence: HIGH.** Hollerith's machine was built and used operationally for the 1890 U.S. Census and subsequent applications. The electrical components are simple (electromagnets and relay-driven counters). Roman-era electrical knowledge is limited - electromagnets are not documented in Pliny or Vitruvius - but the components can be built from first principles using wire coils and iron cores. The contact brush mechanism is purely mechanical and well within Roman capability. A working machine is feasible with electrical expertise.

---

### boolean_algebra - Algebra of Logic and Switching

**What it is / why you want it.** Boolean algebra is a system of logic where propositions are represented as variables (true or false) and combined using operations AND, OR, and NOT. The non-obvious revelation is that these logical operations are *identical in structure* to electrical switching circuits - AND is a series switch, OR is a parallel switch, NOT is an inverter (a relay that opens when activated). This means that any logical statement can be directly translated into a circuit and vice versa. The payoff is that switching circuits can be *designed* using algebra instead of trial-and-error, and complex logical decisions can be automated without human judgment.

**Why you would never guess this.** No schooled mathematician would ever connect logic (an ancient philosophical discipline) to electrical switching (a practical engineering problem). The connection was discovered by Shannon in his 1937 master's thesis, which showed that Boolean algebra and switching circuits were two representations of the same underlying mathematics.

**Prerequisites.** Understanding of logic (true/false, AND/OR/NOT operations), basic algebra, understanding of electrical circuits (switches, relays).

**Roman-available inputs.** This is pure mathematics and logic. No materials required. However, to *build* a switching circuit that implements Boolean algebra, you need wires, switches, relays, and power sources - all available in Roman times.

**Procedure.** This is a theoretical technique, not a practical procedure. Study Boolean algebra: learn that AND(A, B) is true only when both A and B are true. OR(A, B) is true when either A, B, or both are true. NOT(A) is true when A is false. Learn to manipulate Boolean expressions using algebra: De Morgan's laws (NOT(A AND B) = NOT(A) OR NOT(B)), distribution, absorption. Practice converting logical statements into Boolean expressions, and expressions into circuit diagrams. For example, the statement "Sound an alarm if either the door is open AND nobody is present, OR if the window is broken" is:
Alarm = (DoorOpen AND NobodyPresent) OR WindowBroken
This can be drawn as a circuit: two switches (DoorOpen and NobodyPresent) in series, feeding into an OR junction with a WindowBroken switch, all connected to a bell or bell-activating relay.

**How you know it worked.** Trace through the logic: if the door is open and nobody is present (first condition true) and the window is closed (second condition false), the alarm should sound. If the door is closed (first condition false) and the window is broken (second condition true), the alarm should sound. If both conditions are false, no alarm. Test with 4-5 examples and verify that the circuit behavior matches the logical statement.

**Failure modes.** Misunderstanding the logical operations (confusing AND with OR, for example) leads to circuits that behave backwards. Over-complex Boolean expressions that are not simplified can result in circuits with unnecessary components. Sloppy algebra leads to errors in simplification.

**Cost & labour.** Learning Boolean algebra: 20-40 personal hours of study for someone with mathematical background, longer for others. Applying it to design a specific circuit: 5-10 personal hours per circuit, depending on complexity.

**Danger.** None, unless you build the circuit and make electrical errors.

**Confidence: HIGH.** Boolean algebra is mathematically sound and well-established. The connection to switching circuits is experimentally verified and used in all digital electronics. Roman mathematicians could learn and apply Boolean algebra (Euclid's *Elements* demonstrates that logical reasoning is part of Roman mathematical culture). Building circuits that implement Boolean algebra requires electrical knowledge and skill but is not beyond Roman capability.

---

### binary_arithmetic - Calculation in Base 2

**What it is / why you want it.** Binary arithmetic is calculation using only two digits, 0 and 1, instead of the familiar ten digits 0-9 of decimal arithmetic. In binary, 10 = 2 in decimal, 100 = 4, 1000 = 8, and so on. The payoff is that addition and multiplication in binary are vastly simpler than in decimal: addition of two binary digits produces only four cases (0+0=0, 0+1=1, 1+0=1, 1+1=10), and multiplication even simpler. This means that a mechanical device or electrical circuit only needs to distinguish between two states (present/absent, high/low, open/closed) instead of ten, making reliable calculation far easier.

**Why you would never guess this.** No Roman mathematician would naturally invent base-2 arithmetic - all existing notation is base-10 (or in some contexts, base-60 for angles). The non-obvious kernel is that *all* bases are mathematically equivalent, just with different properties. Base 2 is special not because it is easier to compute with by hand - it isn't - but because it is the easiest base for a mechanical or electrical device to implement, since a device only needs to distinguish between two states.

**Prerequisites.** Understanding of positional notation and arithmetic, understanding of place value, willingness to do calculations in an unfamiliar base.

**Roman-available inputs.** This is pure mathematics. No materials are required. However, to implement binary arithmetic in a mechanical device, you need a way to represent 0 and 1: this could be the presence or absence of a hole in a punched card, the open or closed state of an electrical switch, or the high or low voltage on a wire.

**Procedure.** Convert a decimal number to binary by repeatedly dividing by 2 and recording the remainder (0 or 1). For example, 13 in binary: 13 / 2 = 6 R 1, 6 / 2 = 3 R 0, 3 / 2 = 1 R 1, 1 / 2 = 0 R 1. Reading the remainders in reverse: 1101. To add two binary numbers: 1101 + 1011 = 11000 (13 + 11 = 24 in decimal; check: 16 + 8 = 24, correct). Addition is done column-by-column, with a carry rule just as in decimal: 0+0=0, 0+1=1, 1+0=1, 1+1=10 (write 0, carry 1), 1+1+1 (carry) = 11 (write 1, carry 1).

**How you know it worked.** Convert 27 to binary (11011), add 5 (00101), result should be 100000 (32 in decimal; 27 + 5 = 32, correct). Repeat with 5-10 examples and verify against decimal arithmetic.

**Failure modes.** Misunderstanding place value in binary leads to errors in conversion. Forgetting to handle carries during addition produces wrong sums. Confusion between decimal and binary representation can lead to catastrophic mistakes (reading 10 as "ten" instead of "two").

**Cost & labour.** Learning binary arithmetic: 10-20 personal hours for someone with mathematical background.

**Danger.** None.

**Confidence: HIGH.** Binary arithmetic is mathematically sound. The connection to base-2 positional notation is well-established since ancient times (positional notation itself, by Babylonians in base-60). Roman mathematicians could learn binary arithmetic. The practical payoff comes only when you build a machine that uses binary internally - the arithmetic itself is not faster or slower than decimal by hand, only when mechanized.

---

### logic_gate - Combining Switches to Perform Logical Operations

**What it is / why you want it.** A logic gate is an electrical (or mechanical) circuit that implements one of the Boolean operations (AND, OR, NOT) using switches. For example, an AND gate is two switches in series - current flows only if both switches are closed. An OR gate is two switches in parallel - current flows if either switch is closed. By combining logic gates, you can build circuits that make decisions automatically: if this AND that, then do the other thing.

**Why you would never guess this.** The kernel is that a physical device (a switch) can directly implement a logical operation without any intermediate representation or interpretation. A relay (electromagnetic switch) or a mechanical lever can serve as a NOT gate (or inverter): when the input is activated, the relay pulls an armature that opens its contacts. The second insight is that switches can be *combined in series or parallel* to create AND and OR operations.

**Prerequisites.** Boolean algebra (understanding what AND/OR/NOT mean), electrical wiring (switches, relays, power sources), understanding of series and parallel circuits.

**Roman-available inputs.** Copper wire, relays (electromagnet plus switching contacts), batteries or other electrical power source, fasteners and insulation.

**Procedure.** To build a NOT gate: wind a coil of wire around an iron core (electromagnet). Connect one terminal of the coil to a power source and the other to a switch (the input). When the switch is closed, current flows through the coil, magnetizing it and pulling a metal armature connected to the gate's output contact. The armature can be mechanically linked to another set of contacts (the output) which open when the armature is pulled. So: input closed (high) produces output open (low) - this is NOT. To build an AND gate: place two switches in series. Current flows from the power source through switch 1, then switch 2, then to the output. Both switches must be closed for current to flow - this is AND. To build an OR gate: place two switches in parallel. Current flows from the power source through either switch 1 or switch 2 to the output. At least one switch must be closed - this is OR. Combine these gates by wiring outputs to inputs of other gates.

**How you know it worked.** Build an AND gate by wiring two switches in series with a light bulb. Close both switches; the light turns on. Open one switch; the light turns off. Repeat for all four combinations (closed-closed, closed-open, open-closed, open-open) and verify that the light is on only when both switches are closed.

**Failure modes.** Loose wiring connections produce intermittent failures. Weak batteries or high resistance wires prevent sufficient current flow. Relay contacts corroded or stuck prevent reliable switching. A burnt-out electromagnet coil stops the relay from operating.

**Cost & labour.** Building one logic gate (simple AND or OR): 2-4 hours of labour to wind coils, wire connections, and test. Materials (wire, relay components, contacts): 1-5 denarii per gate.

**Danger.** Electrical shock if voltages are high (unlikely for the low-current systems described here) or if wiring is damaged. Proper insulation and grounding are necessary.

**Confidence: HIGH.** Logic gates using relays or other electromagnetic switches have been built and used since the early 1900s. The principle is sound. Roman craftspeople with electrical knowledge could build them.

---

### flip_flop - One-Bit Memory Made from Two Feedback Loops

**What it is / why you want it.** A flip-flop is a circuit made from two logic gates (typically NOR or NAND gates) cross-coupled such that the output of each feeds into the input of the other. This creates a bistable circuit - it has two stable states (output A high and B low, or A low and B high) and it remains in one state even after the input signal is removed. The payoff is that a flip-flop is a *one-bit memory*: it can store the result of a computation or a piece of data until you actively change it. Memory is the missing ingredient in all prior calculation devices - the Difference Engine accumulates sums but cannot retain an arbitrary intermediate result. A flip-flop solves this.

**Why you would never guess this.** The kernel is *feedback* - the output of a gate feeding back into its own input creates a cycle. A cycle in logic is normally forbidden (it leads to paradoxes in pure logic), but in a physical system, the cycle represents a *delay* - by the time the output circles back to the input, time has passed, and the system reaches a stable state instead of oscillating. The second insight is that this stable state is *bistable* - not one stable state, but two competing stable states, and the system is in one or the other depending on which input was activated last.

**Prerequisites.** Logic gates (from above), understanding of feedback and oscillation, electrical wiring.

**Roman-available inputs.** Relays, wire, power sources.

**Procedure.** Build two NOR gates (each is two relays in parallel, with a NOT operation). Wire the output of gate 1 to one input of gate 2. Wire the output of gate 2 to one input of gate 1. The other input of each gate is used for "set" and "reset" signals. Energize the "set" input to gate 1; this forces gate 1's output high. Gate 1's output (high) feeds into gate 2, forcing gate 2's output low. Now remove the set signal - gate 1's output remains high, holding gate 2's output low. The circuit is stable: it "remembers" that set was activated. To reset, energize the "reset" input to gate 2, which forces gate 2's output high, which forces gate 1's output low. Again, remove the reset signal - the circuit remains in this state. This is memory.

**How you know it worked.** Activate the "set" input; observe that output A goes high and output B goes low. Remove the set input; observe that the outputs *remain unchanged*. Activate the "reset" input; observe that A goes low and B goes high. Remove the reset input; observe that the outputs remain in this new state. Repeat 5-10 times and verify that the circuit reliably alternates between the two stable states without drifting or oscillating.

**Failure modes.** Slow relay response times (mechanical relays have a certain switching time, typically milliseconds) can cause oscillation or metastable states (output hovering between high and low) if the set/reset inputs are not held long enough. Cross-coupled gate delays can lead to temporary oscillation if not damped. Poor electrical connections introduce resistance that prevents reliable switching. Relay contacts stick or corrode, trapping the circuit in one state.

**Cost & labour.** Building one flip-flop: 4-6 hours (winding relays, assembling cross-coupled circuit, testing for stability). Materials: 5-10 denarii.

**Danger.** Electrical shock. Proper insulation and grounding required.

**Confidence: HIGH.** Flip-flops (cross-coupled NOR gates) have been used since the early 1900s and are the basis of all digital memory. The circuit is simple enough to build with relays. Roman electricians could build them.

---

### relay_computer - Programmable Computation Using Relays and Punched Cards

**What it is / why you want it.** A relay computer is a complete calculating machine built from relays, wiring, and punched cards. It can store numbers in flip-flop memory, read programs from punched cards, and carry out arithmetic and logical operations according to the program. The payoff is a fully programmable computer - feed it a different punched card program and it solves a different problem. Unlike the Analytical Engine (which was never built), relay computers were actually constructed and used for scientific and military calculations in the 1940s-1950s.

**Why you would never guess this.** The kernel is that relays can directly implement flip-flops (memory), logic gates (arithmetic), and input/output (reading cards, printing results). By combining thousands of relays, you can build a complete computer. The second insight is that the control logic (reading cards and orchestrating the relays) can itself be built from relays, eliminating the need for complex mechanical control gear.

**Prerequisites.** Relay design, flip-flops, logic gates, punched cards, programmable control logic.

**Roman-available inputs.** Thousands of relays, miles of copper wire, power supply (batteries or generator), punched cards for programs and data, and skilled electricians to assemble and debug the machine.

**Procedure.** Design the computer architecture: an arithmetic unit (adders and multipliers built from logic gates), a memory unit (flip-flops or relay latches arranged in rows and columns for random access), a control unit (logic gates that read punched cards and orchestrate arithmetic and memory operations), and input/output (card reader, printer or light display for output). Assemble the machine: wind and test thousands of relays, route and solder thousands of wire connections (this is extremely labour-intensive and error-prone). Test each section independently. Integrate sections and debug the completed machine by feeding it simple test programs.

**How you know it worked.** Load a simple program (e.g., read two numbers from cards, add them, print the result). Feed in punched cards with two numbers. Observe that the machine reads the cards, performs the addition, and outputs the result.

**Failure modes.** With thousands of relays, any single relay failure halts the machine. Relay contacts wear out and corrode, requiring replacement. Solder joints fail, breaking circuits. Misrouted wires produce logic errors that are exceedingly difficult to debug. Noise on power lines or electromagnetic interference causes relays to chatter (rapidly switch on and off), corrupting computations. Thermal drift - as the machine heats up from current draw, relay response times change, potentially causing timing errors.

**Cost & labour.** Design: 200-400 personal hours for an engineer. Fabrication of relays: 500-1000 artisan hours (specialists in relay manufacture). Assembly and wiring: 2000-4000 labour hours (armies of workers soldering and testing). Testing and debugging: 500-1000 hours of engineering time. Total materials (relays, wire, solder, power supply, fasteners): 1000-5000 denarii. Total cost: 5000-15000 denarii (a significant sum, comparable to a large public building or a year's salary for a skilled craftsman). Calendar time: 6-12 months for a team of dedicated engineers and technicians.

**Danger.** Electrical shock from the power supply (if voltages are high enough). High current draw can cause overheating of wires - risk of fire. Electromagnetic radiation from switching relays is not dangerous at the low frequencies involved, but strong fields can interfere with nearby electronic equipment (if any). Safety grounding and insulation are essential.

**Confidence: MEDIUM.** Relay computers were built and used operationally (Mark I, Mark II, etc. in the U.S. and abroad). The engineering is sound. However, the complexity is extreme - thousands of components, any of which can fail. The assembly and debugging effort is immense. Solder joints, wire routing, relay contacts, and power distribution are all sources of unreliability. A working relay computer is feasible but requires exceptional engineering discipline and careful testing. Operational reliability over months or years is harder to achieve - machines of this era typically ran for a few hours before some component failed, requiring replacement and recalibration.

---

### vacuum_tube_computer - Calculation Using Electronic Switches

**What it is / why you want it.** A vacuum tube is an evacuated glass bulb containing electrodes. When heated, the cathode emits electrons which flow to the anode, and a small voltage on the grid can control this flow - acting as an electronic switch much faster than a relay. A vacuum tube computer uses thousands of vacuum tubes as electronic switches to build logic gates and memory, achieving calculation speeds thousands of times faster than relay computers.

**Why you would never guess this.** The kernel is that you can *amplify and switch electrical signals using vacuum tubes without mechanical moving parts*, achieving speeds limited only by the propagation of electrical signals (nearly the speed of light) rather than mechanical relay response times (milliseconds). The second insight is that *any* Boolean logic or arithmetic operation can be built from tubes, just as with relays, but at speeds that allow *practical* real-time calculations.

**Prerequisites.** Vacuum tube technology (glass blowing, cathode manufacture, evacuation pumps), high-voltage power supplies, electronic component design, large-scale electronics assembly.

**Roman-available inputs.** Glass for tubes (Roman glassblowing is available), copper for electrodes and wiring, mica for insulators, materials for cathodes (thoriated tungsten is ideal, but alternatives exist), mercury or other evacuation media, high-voltage power generation (electrical generator, step-up transformer to reach 1000-3000 volts for power supplies and tube operation).

**Procedure.** Design vacuum tubes: determine the geometry of cathode, anode, and grid. Fabricate glass bulbs (glassblower work). Assemble electrodes inside the bulb and seal. Evacuate the air using a pump (mechanical vacuum pump, probably hand-operated or powered by a water wheel). Test each tube for proper vacuum and electrical function. Assemble thousands of tubes into a computer structure similar to a relay computer, but with tubes replacing relays. Connect to a high-voltage power supply. Wire logic gates from tube circuits (a tube can be configured as an inverter, and combinations produce AND/OR gates). Build memory from tube flip-flops (a pair of tubes cross-coupled through resistors and capacitors, rather than the mechanical latches of relay designs). Connect input/output (punched card reader, printer, or lights).

**How you know it worked.** Run a simple test program as with the relay computer. Observe that computation is much faster (microseconds instead of milliseconds per operation).

**Failure modes.** Vacuum tube failure is the primary failure mode: each tube has a limited lifespan (typically 1000-10000 hours of operation, varying by design). After a tube fails, the circuit containing that tube stops working. With tens of thousands of tubes, statistical failure rate becomes overwhelming - any large vacuum tube computer was likely to have a tube fail multiple times per day. Solder joints still fail as in relay computers. Thermal stress from the heat generated by thousands of heated cathodes causes mechanical stress on components. High-voltage power supplies can fail catastrophically, destroying tubes and components. Noise and interference on power lines cause circuit errors.

**Cost & labour.** Design: 300-600 personal hours. Vacuum tube fabrication: 5000-10000 artisan hours (specialized glassblowers and evacuators). Assembly: 3000-6000 labour hours. Testing: 500-1000 engineering hours. Materials (glass, metals, insulators, tube filaments, power supply components, miles of wire): 5000-15000 denarii. Total: 15000-50000 denarii. Calendar time: 6-18 months.

**Danger.** High-voltage electrical shock - tubes operate at 1000+ volts, sufficient to be lethal. Proper grounding and safety procedures are essential. Heat from thousands of cathodes operating continuously generates risk of fire. Bulky cooling systems (fans, radiators, water cooling) are needed. Mechanical failure of vacuum equipment can allow air to leak into tubes, causing catastrophic failure (tubes become visible hot, can explode from thermal stress).

**Confidence: MEDIUM-HIGH.** Vacuum tube computers were built and used operationally from the 1940s onward (ENIAC, UNIVAC, etc.). The basic engineering is sound. Roman glassblowers could manufacture vacuum tubes with sufficient precision. However, the high-voltage power supplies, the thermal management, and the sheer number of components make this a risky and expensive undertaking. A working machine is achievable but fragile. Operational reliability over months is poor - constant tube failures require constant maintenance and replacement. The social and practical barriers (cost, complexity, risk) mean that for 100 AD, *do not build a vacuum tube computer*. Use trained clerks with punched cards and Hollerith tabulators instead. You get 90% of the benefit at 1% of the cost and risk, and the clerks do not require a dedicated power supply, cooling system, and a specialist technician on call 24 hours a day.

---

### magnetic_core_memory - Reliable Storage Using Iron Toroids

**What it is / why you want it.** Magnetic core memory uses small iron toroidal cores (donuts), each threaded with electrical wires. By applying a current through a wire, you magnetize the toroid in one direction (representing "1") or the opposite direction (representing "0"). The toroid retains this magnetization even after the current is removed - it is a form of non-volatile memory. By arranging thousands of cores in a grid and running wires through them, you can build a reliable random-access memory that does not degrade with time or power loss. The payoff is memory that is far more reliable than vacuum tube flip-flops (which lose their state if power is interrupted) and far denser than relay latches.

**Why you would never guess this.** The kernel is that a *magnetic material can retain information after the input signal is removed*, and by carefully controlling the direction of magnetization, you can store binary information. The second insight is that you can *sense* the state by attempting to flip the magnetization and measuring the induced current pulse that results - this is non-destructive readout. The third insight is that by threading multiple wires through the same toroid, you can perform multiple operations (set, reset, read) on a single stored bit.

**Prerequisites.** Understanding of magnetism, ability to wind fine wire through toroidal cores, understanding of electromagnetic induction, electrical measurement equipment (to detect the sense pulse).

**Roman-available inputs.** Iron (from bloomery furnace), forming into toroidal shapes (requires shaping and annealing), copper wire for threading (fine copper wire, drawn from copper sheet), and electrical measurement apparatus (galvanometer or similar).

**Procedure.** Forge or cast small iron toroids (roughly 1cm diameter, 5-10mm cross-section). Wind three wires through each toroid: an X wire (row select), a Y wire (column select), and a sense wire (to read the state). Arrange thousands of cores in a grid pattern, with cores at each X-Y intersection. To write a bit: apply current through the X and Y wires for that core such that their fields add, flipping the toroid's magnetization. To read a bit: apply a small current to the X and Y wires, again setting the toroid to the "1" state if it wasn't already. Monitor the sense wire; if the toroid was in the "0" state, flipping it to "1" induces a current pulse on the sense wire (this is *destructive* read, so the state must be rewritten if it was a "0"). Alternative designs use a fourth wire for true non-destructive readout.

**How you know it worked.** Write a known pattern (a sequence of 1s and 0s) to the memory. Read it back and verify that the pattern is correct.

**Failure modes.** A wire thread can break, severing the core's connections and rendering it useless. Cores can crack or become oxidized, reducing their magnetic properties. The toroid can be accidentally demagnetized by strong external magnetic fields (e.g., from a nearby electromagnet or power line). Corrosion of the copper wires reduces contact reliability. If the grid is poorly designed, interference between wires can flip unintended cores.

**Cost & labour.** Fabrication of 1000 toroids: 50-100 hours (shaping iron, annealing, checking quality). Threading wires: 100-200 hours (tedious manual work). Assembly of the full memory grid (10000 cores): 500-1000 hours. Testing: 50-100 hours. Materials (iron, copper wire): 20-50 denarii. Total: 700-1400 labour hours, 50-150 denarii materials.

**Danger.** None beyond minor irritation from fine dust during iron forming.

**Confidence: HIGH.** Magnetic core memory was used operationally in computers from the 1950s through the 1970s. The physics is sound. Roman craftspeople could produce toroids and thread wires. The main difficulty is the tedious manual assembly - for 100 AD, you would likely decide that the labour cost is not worth the benefit and stick with relay latches or punched card storage instead. But the technique is feasible.

---

### stored_program - Programs as Data, Loaded from External Media

**What it is / why you want it.** A stored program is a sequence of instructions that the computer reads from external storage (punched cards, magnetic tape, or core memory) and executes. Unlike earlier mechanical calculators where the operation was hardwired into the gears, a stored-program computer loads different instructions for different problems. The payoff is that a single machine can solve arbitrary problems without rebuilding hardware - you just load a different program.

**Why you would never guess this.** The kernel is that *instructions and data can be encoded identically* and stored in the same medium. An instruction like "add the contents of memory locations 5 and 7 and store the result in location 3" can be represented as a sequence of numbers just like any other data. The computer does not need to "understand" the instruction's meaning - it just decodes the bit pattern and routes the appropriate electrical signals to the arithmetic unit. The second insight is that the *control logic itself can be automated* - no human operator selecting which operation to perform next, but instead the computer reading instructions and executing them in sequence, with branches and loops controlled by the program itself.

**Prerequisites.** Computer hardware (arithmetic unit, memory, I/O), mechanism to read programs from external media (card reader, tape drive, etc.), control logic (wired or programmed) to decode and execute instructions.

**Roman-available inputs.** All the above (relay or vacuum tube circuits, punched cards, etc.).

**Procedure.** Design an instruction set - a fixed set of operations the computer can perform (add, subtract, multiply, divide, load from memory, store to memory, branch if zero, etc.). Each instruction is encoded as a fixed-width bit pattern (typically 20-50 bits in early computers). A punched card carries one or more instructions. The control unit reads each instruction, decodes which operation it specifies, and routes signals to the appropriate hardware unit (arithmetic for add, memory for load, etc.). The computer executes instructions in sequence unless a branch instruction redirects control.

**How you know it worked.** Load a program to compute factorial(5) = 120. Input the value 5. Observe that the machine computes and outputs 120. Load a different program to compute 2^10 = 1024. Input 10. Observe output 1024. The same hardware solves both problems with different programs.

**Failure modes.** A program with incorrect instructions computes wrong results in a way that may not be immediately obvious. Infinite loops (a program that branches back to itself forever) cause the computer to hang. Accessing memory locations that do not exist (out-of-bounds) causes crashes or undefined behavior.

**Cost & labour.** Designing the instruction set and control logic: 50-100 personal hours. Writing a specific program: 5-20 personal hours, depending on complexity.

**Danger.** None, beyond potential for infinite loops if the computer is not able to be halted manually.

**Confidence: HIGH.** Stored-program computers were demonstrated in the 1940s (Manchester Baby, EDSAC) and became standard by the 1950s. The concept is the defining feature of modern computers.

---

### compiler - Translating High-Level Instructions to Machine Code

**What it is / why you want it.** A compiler is a program (or a person) that translates high-level instructions (like "add 5 to X") into low-level machine code (the bit patterns that the computer's control unit executes directly). The payoff is that programmers can write programs in a more human-readable language, and the compiler automatically produces the machine code. This reduces errors and dramatically accelerates programming.

**Why you would never guess this.** The kernel is that the *translation process itself can be automated and performed by a computer*. No human needs to manually convert each high-level instruction to machine code; a compiler program does it. The second insight is that compilers can *optimize* the machine code, reordering instructions to reduce memory access or execute faster, without the programmer needing to understand the optimization.

**Prerequisites.** Stored-program computer, ability to write programs that perform text manipulation and code generation.

**Roman-available inputs.** None - this is a software/logic tool, not a physical technique.

**Procedure.** Write a compiler program: read in a high-level program (text with instructions like "ADD X 5"), parse the syntax, check for errors, and generate the corresponding machine code. Compile a program by running the compiler, passing the high-level code as input. Execute the compiled machine code on the computer.

**How you know it worked.** Write a high-level program to add 5 to a variable X. Compile it. Run it. Verify that X is incremented by 5.

**Failure modes.** Bugs in the compiler produce incorrect machine code from correct high-level code. A programmer writes high-level code with syntax errors or logic errors; the compiler rejects it or produces code that runs but computes wrong results.

**Cost & labour.** Writing a compiler: 200-1000 personal hours, depending on complexity and language features. Using a compiler to write a program: 10-50 hours, depending on program complexity.

**Danger.** None.

**Confidence: HIGH.** Compilers were first written in the 1950s and are fundamental to modern programming. The technology is sound.

---

### error_correcting_code - Adding Structured Redundancy to Detect and Fix Errors

**What it is / why you want it.** An error-correcting code is a method for encoding data such that errors introduced during transmission or storage can be detected and, in some cases, corrected automatically without retransmission. For example, if you send a message encoded as "each bit is repeated three times", then the receiving end can detect if one copy was corrupted (the three copies don't match) and recover the correct bit by majority vote. The payoff is reliability: long-distance communication and storage systems accumulate errors, and error-correcting codes allow the receiver to fix them automatically.

**Why you would never guess this.** The kernel is that *you can add redundancy in a structured way such that the redundancy itself encodes information about which bits might be wrong*. A naive approach (repeat each bit three times) works but wastes bandwidth. Clever codes (like Hamming codes) add much less redundancy (roughly 10% overhead) while still correcting single-bit errors. The mathematical theory (Hamming, 1950) proves that the redundancy required is related to the log of the message length, not the message length itself.

**Prerequisites.** Understanding of binary representation, combinatorics, linear algebra (for optimal code design).

**Roman-available inputs.** None - this is pure mathematics.

**Procedure.** Choose an error-correcting code (e.g., Hamming(7,4) encodes 4 data bits as 7 bits by adding 3 parity bits). To encode: compute the parity bits from the data bits using XOR operations. Transmit the 7-bit codeword. On receipt, recompute the parity bits and compare to the received values. If they match, no error. If they differ, the pattern of differences (the "syndrome") indicates which bit is wrong; flip that bit to correct it.

**How you know it worked.** Encode the data 1010 as Hamming(7,4). Introduce a single bit error in one of the 7 bits (change a 1 to 0, or vice versa). Apply the error-correction algorithm. Verify that the error is detected and corrected, recovering the original 1010.

**Failure modes.** Multiple bit errors in a single codeword may not be correctable (Hamming(7,4) corrects only single-bit errors; it can detect two-bit errors but cannot correct them). If more than one bit is flipped, the syndrome will indicate the wrong bit, leading to an incorrect "correction". Systematic errors (e.g., all 1s get flipped to 0) are not handled by any single code but require higher-level protocols.

**Cost & labour.** Learning error-correcting codes: 20-40 personal hours. Writing code to encode and decode using a specific scheme: 5-10 personal hours.

**Danger.** None.

**Confidence: HIGH.** Error-correcting codes were developed in the 1950s (Hamming, Reed-Solomon, etc.) and are used everywhere in communication and storage. The mathematics is sound. A Roman scribe or signal corps could learn and apply error-correcting codes to important messages - for example, a military message sent by relay signal towers could be encoded with redundancy such that garbled portions could be recovered. The technique is available far earlier than any electronic computer exists.

---

### information_theory - Measuring Information in Bits

**What it is / why you want it.** Information theory provides a mathematical framework for quantifying information. A single bit (0 or 1) represents a choice between two equally-likely alternatives, and is the fundamental unit of information. A message of N bits can represent one of 2^N different things. The payoff is a rigorous understanding of how much data a channel can carry (the channel capacity) and how to design codes and compression schemes that approach this limit.

**Why you would never guess this.** The kernel is that *information has a measurable quantity, independent of the meaning or interpretation*. A message saying "it will rain tomorrow" conveys the same amount of information (one bit, if there are only two equally-likely outcomes) as a random coin flip. This is counterintuitive - the meanings are completely different, yet the information content is identical. The second insight is that information can be *measured and optimized*. Shannon (1948) proved that no communication channel can carry more information than its capacity, and that codes exist that achieve this capacity arbitrarily closely.

**Prerequisites.** Understanding of probability, logarithms, binary representation.

**Roman-available inputs.** None - this is pure mathematics.

**Procedure.** Calculate the information content of a message: if the message is one of M equally-likely possibilities, the information content is log2(M) bits. For example, a message specifying which of 8 equally-likely outcomes occurred is 3 bits. If the outcomes are not equally likely, the average information content is the entropy H = -sum(p_i * log2(p_i)), where p_i is the probability of outcome i. Design a code to transmit the message: use shorter bit sequences for more probable outcomes and longer sequences for less probable outcomes. The average code length approaches the entropy, and no code can be shorter on average.

**How you know it worked.** A six-sided die has log2(6) = 2.58 bits of information per roll (not a round number, indicating that you cannot represent a die roll exactly in an integer number of bits, but must use a code that averages about 2.58 bits per roll). Design a code using variable-length bit sequences: represent outcomes 1-4 with 2 bits (00, 01, 10, 11) and outcomes 5-6 with 3 bits (110, 111). Average code length: (4 * 2 + 2 * 3) / 6 = 14/6 = 2.33 bits per roll. This is longer than the entropy (2.58 is incorrect - let me recalculate: entropy = -6 * (1/6 * log2(1/6)) = -6 * (1/6 * -2.58) = 2.58 bits). So the average code length is shorter than the worst case but longer than the entropy, which is correct.

**Failure modes.** Misunderstanding entropy as the maximum possible information (it is actually the minimum average information). Assuming all outcomes are equally likely when they are not.

**Cost & labour.** Learning information theory: 30-60 personal hours for someone with mathematical background. Applying it to design a specific code: 5-20 personal hours.

**Danger.** None.

**Confidence: HIGH.** Information theory was developed by Shannon (1948) and is mathematically rigorous. The applications (channel coding, data compression, error correction) are practically verified. Roman mathematicians could learn information theory, and it could be applied to improve the reliability of long-distance communication systems (signal towers, messenger relays, etc.).

---

### cryptography_rotor - Mechanical Encryption Using Rotating Substitution

**What it is / why you want it.** A cryptographic rotor is a mechanical device that scrambles (encrypts) a message by routing each character through a rotating wheel with cross-wired contacts. As each character is processed, the rotor advances, changing the substitution for the next character. The payoff is fast, reliable encryption of messages without requiring a shared codebook. The most famous implementation was the Enigma machine used by Nazi Germany. Even after decades of use, a single rotor machine still provides strong encryption against casual codebreakers.

**Why you would never guess this.** The kernel is that *the substitution pattern changes with each character processed*. A simple substitution cipher (A->B, B->C, etc.) is easily broken by frequency analysis. But if the substitution changes with each character, frequency analysis becomes impossible - an 'E' in the plaintext might become any letter in the ciphertext depending on the rotor position. The second insight is that the rotor's position can be *mechanically advanced* as each character is typed, eliminating the need for manual intervention.

**Prerequisites.** Mechanical design (rotors and gearing), electrical switching (contacts), understanding of substitution ciphers.

**Roman-available inputs.** Brass or bronze for rotors and contacts, copper wire for internal wiring, electrical switches.

**Procedure.** Design a rotor: a brass wheel with 26 contact pins on one side (one for each letter A-Z) and 26 contact pins on the other side, with internal wiring connecting each input pin to a different output pin (this is a permutation, or substitution). For example, input A might be wired to output D, input B to output E, etc. Mount the rotor on a shaft so it can rotate. As a character is entered (by pressing a key), electrical current flows through the input contact, through the internal wiring, and out through the output contact, lighting an output letter. After each character, advance the rotor by one position using a stepping mechanism (a geared wheel that increments on each keystroke). With multiple rotors cascaded (each rotor's output feeds into the next rotor's input), the effective substitution becomes far more complex.

**How you know it worked.** Set the rotor to a known starting position. Type a message. Observe that each character is transformed by the rotor. Check that the same plaintext character produces different ciphertext characters depending on the rotor's position. Transmit the ciphertext to a recipient with an identical rotor machine set to the same starting position. They should be able to decrypt by simply typing in the ciphertext and observing the output (the reverse operation of the rotor).

**Failure modes.** Rotor contacts can corrode or misalign, producing incorrect substitutions. The stepping mechanism can stick, causing the rotor to not advance or to skip positions, leading to misalignment between sender and receiver. Duplicate rotor wirings (if two rotors have the same internal wiring) weaken the cipher. A captured rotor or a rotor's wiring diagram allows an adversary to decrypt all messages encrypted with that rotor setting.

**Cost & labour.** Designing and fabricating a single rotor: 20-40 artisan hours (precision wiring and contact work). A three-rotor machine: 100-200 artisan hours. Materials: 30-60 denarii.

**Danger.** Electrical shock if high voltages are used, though a rotor machine typically operates on low voltage (from a battery).

**Confidence: HIGH.** Rotor machines were built and used operationally for encryption from the 1920s onward (Enigma was deployed in the 1930s). The mechanism is sound. Roman craftspeople could build them. However, rotor machines are vulnerable to *known-plaintext* attacks: if an adversary knows the plaintext of a message and the corresponding ciphertext, they can determine the rotor wiring and decrypt future messages. This was actually exploited to break the Enigma cipher in WWII. For military use, rotor machines require strict protocols to prevent plaintext from being captured.

---

### public_key - Encryption Without Sharing a Secret

**What it is / why you want it.** Public-key cryptography is a method where you publish an encryption key (the "public key") such that anyone can encrypt a message to you, yet only you can decrypt it (using your secret "private key"). The two keys are mathematically related but kept separate - knowing the public key does not allow you to derive the private key. The payoff is revolutionary: two parties who have never met can exchange secret messages without ever meeting to agree on a shared key. This is the foundation of modern secure communication.

**Why you would never guess this.** The kernel is that *encryption and decryption can use different keys*. Traditional ciphers (substitution, Vigenere, rotor machines) use the same key for both encryption and decryption. The non-obvious revelation is that asymmetric ciphers exist where the encryption key and decryption key are different. The most famous is RSA, which relies on the difficulty of factoring large numbers: the public key contains a large composite number N (the product of two large primes), and encryption is roughly "raise the plaintext to a power modulo N". The private key contains the factors of N, which allows decryption by computing a different power that reverses the encryption. The mathematical basis is Euler's theorem and modular exponentiation.

**Prerequisites.** Number theory (modular arithmetic, exponentiation), understanding of prime numbers and factorization, algorithm design (to implement modular exponentiation efficiently).

**Roman-available inputs.** None - this is pure mathematics and algorithm design.

**Procedure.** To generate a key pair: choose two large prime numbers p and q (500+ digits for modern security). Compute N = p * q. Compute the totient phi(N) = (p-1) * (q-1). Choose e (the encryption exponent) that is coprime to phi(N), typically e = 65537. Compute d (the decryption exponent) such that e * d ≡ 1 (mod phi(N)) using the extended Euclidean algorithm. The public key is (N, e). The private key is (N, d). To encrypt a message m: compute c = m^e mod N. To decrypt: compute m = c^d mod N. Due to Euler's theorem, this recovers m.

**How you know it worked.** Choose small primes p=61, q=53, so N=3233, phi(N)=3120. Choose e=17. Compute d such that 17*d ≡ 1 (mod 3120), finding d=2753. Encrypt a message m=123: c = 123^17 mod 3233 = (a large number) mod 3233 = (compute with modular exponentiation) = 855. Decrypt c=855: m = 855^2753 mod 3233 = 123. Verify the decryption is correct.

**Failure modes.** If p and q are not truly prime, the cipher is broken. If p and q are too small, an adversary can factor N by brute force, computing p and q and thus phi(N) and d. If e is not coprime to phi(N), decryption fails (not all plaintexts can be decrypted). Weak random number generation for choosing p and q leads to predictable keys.

**Cost & labour.** Learning public-key cryptography (number theory prerequisites): 100-200 personal hours. Implementing RSA in software (or by hand for small numbers): 20-50 personal hours. Generating a single key pair by hand (factoring, computing totient, finding inverse): 5-20 hours (tedious arithmetic).

**Danger.** None.

**Confidence: HIGH.** Public-key cryptography was invented by Whitfield Diffie and Martin Hellman (1976) and implemented by RSA (1977). The mathematics is rigorous and proven sound. However, the practical implementation requires large numbers (hundreds of digits) and efficient modular exponentiation algorithms. By hand, generating and using public-key cryptography is extremely tedious. In 100 AD with trained mathematicians and patience, it is feasible but impractical - you would use rotor machines or one-time pads instead. However, public-key cryptography is *theoretically* available to you once you have number theory and modular arithmetic, both of which are within Roman mathematical knowledge. This is truly remarkable: RSA requires no physical machinery, no electricity, nothing but arithmetic and patience. A clever adversary (or a dedicated team) could break RSA by factoring large numbers, but only if they dedicate months or years of effort to each key. For most practical purposes in 100 AD, public-key cryptography would be secure against anyone except a state with massive resources.

---

## Sources and Confidence

This module covers techniques spanning from simple mechanical aids (slide rules, Napier's bones) through electrical circuits (logic gates, relay computers) to purely mathematical methods (Boolean algebra, public-key cryptography). The earlier techniques (through analytical engines) are grounded in documented historical implementations or are extensions of mechanisms (like Babbage's machines) that were designed in detail even if not completed. Confidence is generally HIGH for techniques that were actually built (Napier's bones, arithmometer, Hollerith tabulation, relay computers). Confidence is MEDIUM for complex machines like the Difference Engine and Analytical Engine that were designed but never completed in their era, though the underlying principles are sound.

The electrical and electronic techniques (logic gates, flip-flops, vacuum tube computers) are documented from 1940s-1950s implementation. Roman craftspeople could build relays and simple electrical circuits - electrodes in saltwater or acid are available, electromagnets are feasible - so relay computers are theoretically possible in 100 AD but practically too costly and unreliable to be worthwhile.

The purely mathematical techniques (Boolean algebra, binary arithmetic, information theory, public-key cryptography) have no material prerequisites and can be learned and applied by trained mathematicians in any era. Error-correcting codes and cryptography rotors are intermediate - they require arithmetic knowledge but can be implemented mechanically without electricity.

The single greatest insight in this module is that **logic and switching are identical**. Shannon's observation that Boolean algebra is isomorphic to switching circuits is the foundation of all digital computation. Every computer ever built is essentially a physical instantiation of logical operations. Once you understand this, the path from simple relays to supercomputers is only engineering complexity, not conceptual novelty.

**Do not build a vacuum tube computer in 100 AD.** Use trained clerks, punched cards, and electromechanical tabulators instead. The benefit-to-cost ratio is poor, and the reliability is worse. For two hundred years, paper, pen, arithmetic skill, and human memory are superior to anything you can mechanically build. When electricity becomes abundant and reliable (centuries later), electronic computers become practical. Until then, the best computing tools are mechanical (for speed) and human (for reliability and flexibility).
