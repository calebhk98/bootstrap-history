# Module 40: Prime Movers, Machine Tools and Precision

You already have water wheels, the screw press, force pumps, gearing, and
the pole/bow lathe. Missing: turning continuous rotation into
reciprocating motion (crank and connecting rod), a horse harness that
lets the animal push with its whole body, a flywheel to carry an
intermittent-torque machine through its weak point, an accurate screw
thread, and, above all, a way to check whether a surface is truly flat
without already owning something flat to check it against. That last gap
is the real one: every micrometer, every interchangeable part, every
steam cylinder that does not leak, and eventually every transistor,
traces back to a flat reference surface. Rome in 100 AD is decades of
disciplined bootstrapping from that point, not centuries.

Quantify the gap. A Roman millwright already turns falling water into
rotary torque at real, usable efficiency. He cannot turn that torque into
a reciprocating stroke (forge hammer, pump piston) without a person on a
lever, because crank-and-connecting-rod is not generalized before the
Hierapolis sawmill relief (3rd century AD), and even there it looks like
a local curiosity. A Greek instrument maker can already hand-cut over
thirty bronze gears accurate enough to model the Saros eclipse cycle (the
Antikythera mechanism, roughly 150-100 BC), but nobody has connected that
skill to a general theory of flatness and measurement that lets two
workshops make parts that fit each other's machines. None of this needs a
new material. It needs new procedures, and one new idea: precision is
manufactured, not found.

---

### water_power_scaleup - Scaling up the water wheel (*rota aquaria*)

**What it is / why you want it.** More, reliable shaft power from wheels
you already build: match wheel type to site, control flow with a
millpond and leat, cascade multiple wheels on one stream.

**Why you would never guess this.** "Bigger wheel" is not the lever;
efficiency and controlled head/flow are.

**Prerequisites.** Water wheel construction, gearing, surveying and
hydraulic-concrete civil works (already in your toolkit).

**Roman-available inputs.** Oak/elm for wheel and shaft, iron for bearing
collars, worked stone for the wheel pit, bronze bushes.

**Procedure.** Measure head (level and staff) and flow (a weir of known
width). Power: P (watts) = 1000 x 9.81 x Q (m^3/s) x H (m) x efficiency
(DERIVED). Example: 3 m head, 0.3 m^3/s, 60% efficient overshot wheel
gives P ≈ 5,300 W, about 7 hp (1 hp = 745.7 W). Little head: undershot,
20-30% efficient plain, 60-70% curved-vane ("Poncelet"). Real head:
overshot, per Smeaton's 1759 tests roughly twice as efficient as common
undershot, 60-85% (MEASURED-but-approximate, 18th century figures). Build
a millpond and leat for controlled head. For more power, cascade wheels
down a slope as at Barbegal near Arelate: two rows of eight overshot
wheels, estimated 20-40 aggregate horsepower (ESTIMATED, basis: Leveau's
reconstructions from wheel-pit dimensions; estimates vary).

**How you know it worked.** Time the wheel grinding a known weight of
grain or lifting water a known height; compare types on the same stream.

**Failure modes.** Undershot wheels choke in flood, starve in drought;
overshot leats silt up; unlubricated bearings burn out.

**Cost & labour.** ESTIMATED (basis: scaled against aqueduct/mill work)
hundreds of artisan-days per wheel; Barbegal-scale is state-level.

**Danger.** Crush and drowning hazards at sluices.

**Confidence: HIGH.** Textbook physics; efficiency ranges widely
reported; Barbegal's figure is a scholarly estimate, not fact.

---

### crank_connecting_rod - The crank and connecting rod (no attested
Latin term)

**What it is / why you want it.** Converts continuous rotary motion into
reciprocating motion, and back, for saws, pumps, hammers, later engines.

**Why you would never guess this.** Trivial in hindsight, an offset pin
joined by a rigid rod. No Mediterranean culture generalized it before
Hierapolis, likely because a crank reverses its bearing's load twice per
revolution and chews up a soft bearing fast unless over-built.

**Prerequisites.** water_power_scaleup, bronze/iron forging,
bearings_lubrication.

**Roman-available inputs.** Wrought iron crank pin, bronze bushings, oak
rod and frame.

**Procedure.** Fix an iron pin off-centre on the shaft (the crank throw).
Join it by a rigid, bronze-bushed, greased rod to the reciprocating part.
Over-build the crank-pin bearing, it takes the full reversing load twice
a revolution. Test at low speed, watching for binding near end of travel.

**How you know it worked.** Smooth motion, no jerk; runs an hour without
the crank-pin bearing overheating (too hot to touch: stop).

**Failure modes.** Undersized bearing wears oval within days; a light rod
whips at the pin holes; a crank throw near the rod's own length can lock
the mechanism at dead centre.

**Cost & labour.** ESTIMATED (basis: iron/bronze content like a large
force pump) a few dozen artisan-days once the pattern is proven.

**Danger.** Serious entanglement and crush hazard, guard it.

**Confidence: MEDIUM.** Period-plausible (Hierapolis proves it), but no
surviving Roman text gives bearing sizing.

---

### cam_trip_hammer - The cam-lifted trip hammer (no attested Latin term)

**What it is / why you want it.** A cam shaft that lifts a heavy hammer
and drops it, for forging blooms or crushing ore, without sledgehammer
gangs.

**Why you would never guess this.** Obvious once you want it; the hard
part is rotary power strong enough to lift the hammer, which
water_power_scaleup supplies.

**Prerequisites.** water_power_scaleup, carpentry, iron forging.

**Roman-available inputs.** Oak beam ("helve") and frame, iron head, cams
and pivot.

**Procedure.** Mount lobed cams on the wheel's shaft. A pivoted beam
carries the hammer head; a tappet near the pivot is caught and lifted by
each lobe, then released. Use for forging (consolidating a bloom into bar
iron) or ore stamping (crushing silver, lead, or copper ore before
smelting, directly useful at a site like Rio Tinto).

**How you know it worked.** Even, steady strikes; denser forged work in
less labour; consistently sized crushed ore.

**Failure modes.** Cam lobes wear round and lose their snap; the helve
splits if undersized; a stamp run dry clogs and overheats.

**Cost & labour.** ESTIMATED (basis: mostly carpentry) ten to twenty
artisan-days per station once proven.

**Danger.** Falling hammers, pivot pinch points; ore dust is a long-term
lung hazard, ventilate.

**Confidence: MEDIUM.** Well attested later (medieval Europe, Han China);
no direct Roman attestation.

---

### flywheel - The flywheel (no attested Latin term)

**What it is / why you want it.** A heavy wheel storing rotational energy
so an uneven-torque machine (a crank at dead centre) keeps turning
instead of stalling.

**Why you would never guess this.** Simple physics (stored energy = one
half moment of inertia times angular speed squared, DERIVED), but the
need only appears once a crank machine stalls at its weak point. Rome
already has an informal version: a heavy potter's wheel coasts through
inattention by stored momentum alone.

**Prerequisites.** crank_connecting_rod or cam_trip_hammer, casting or
stonework for the mass.

**Roman-available inputs.** Cast bronze, worked stone, or lead segments
in a wooden rim.

**Procedure.** Find the lowest-torque point in the cycle. Concentrate
mass at the largest practical radius (a rim, since stored energy scales
with radius squared). Mount on the shaft, sized by trial, adding mass
until stalling stops.

**How you know it worked.** Visibly even speed through a full cycle; no
stalling at start-up.

**Failure modes.** Too light: still stalls. Too heavy: hard to stop or
start. A poorly-set rim run too fast can burst, lethal.

**Cost & labour.** ESTIMATED (basis: scales with mass and radius) modest,
using stone or bronze already worked for millstones.

**Danger.** Real stored energy, a burst rim is lethal; build mass
incrementally, test at low speed first.

**Confidence: HIGH** on physics; MEDIUM on exact sizing, necessarily
trial-based.

---

### horse_collar_harness - The padded horse collar (no attested Latin
term, a genuine gap)

**What it is / why you want it.** A rigid, padded collar on the shoulders
so a horse pushes with its whole body, not against a throat strap.

**Why you would never guess this.** Do not trust the old dramatic claim.
Lefebvre des Noëttes argued in 1931 that Roman throat-and-girth harness
choked horses so badly none could pull more than about 500 kg. Modern
experimental archaeology (Jean Spruytte's reconstructions, Georges
Raepsaet's analysis) shows the actual Roman breast-strap harness
(archaeologically attested) chokes far less than assumed. Give a range,
not a false number: the collar's real advantage over good Roman
breast-strap harness is probably modest to moderate, on the order of
20-50% more sustained draught (ESTIMATED, basis: reconciling revisionist
trials against the older claim), not the multiple-hundred-percent leap
the old story implied. Still worth it: cheap, uncontroversial. Shape is
the non-obvious part: load must go to the shoulder skeleton, not the
windpipe.

**Prerequisites.** Leatherworking and basic framing (already Roman).

**Roman-available inputs.** Ox/horsehide, wool/straw stuffing, willow or
ash frame, iron hames.

**Procedure.** Measure the neck and shoulders carefully; a bad fit is
worse than none. Build a stuffed leather collar clearing the windpipe and
spine. Fit hames with trace attachments low. Break in gradually, watching
for chafing.

**How you know it worked.** Free breathing under load; no raw patch after
a day; visibly less strain than the old harness for the same load.

**Failure modes.** Poor fit causes shoulder sores that idle the animal
for weeks; soft stuffing collapses; hames set too high recreate throat
pressure.

**Cost & labour.** ESTIMATED (basis: comparable to existing fine Roman
harness) a few days of skilled leatherwork per collar plus iron.

**Danger.** Minimal, mostly to the horse if badly fitted.

**Confidence: MEDIUM.** Sound mechanical logic, but the quantitative
improvement is genuinely disputed; treat the figure as a bracket.

---

### whippletree - The whippletree / swingletree (no attested Latin term)

**What it is / why you want it.** A pivoted bar between traces and load
that automatically equalizes pull between two or more animals.

**Why you would never guess this.** Obvious once you want it; nobody
bothers until teaming animals and noticing how unevenly they pull.

**Prerequisites.** Basic woodworking and ironwork; pairs with
horse_collar_harness but works with any harness.

**Roman-available inputs.** Ash or oak bars, iron pivot pin and rings.

**Procedure.** Cut a bar, iron-shod at both ends with trace rings,
pivoted centrally on the load. One animal per end. For larger teams, hang
whippletrees off a larger pivoted "evener" bar.

**How you know it worked.** The bar visibly shifts toward whichever
animal pulls less.

**Failure modes.** A thin pivot pin shears; a too-short bar fouls the
animals' paths.

**Cost & labour.** ESTIMATED (basis: trivial material) well under a day's
labour per unit.

**Danger.** None significant.

**Confidence: HIGH.** Simple statics, well documented wherever teamed
draught animals were used.

---

### horseshoe - The nailed iron horseshoe (*solea ferrea*, cf. the
Roman strap-on hipposandal, a distinct, attested device)

**What it is / why you want it.** A shaped iron plate nailed into the
insensitive hoof wall, protecting it on hard ground, notably Rome's own
paved roads.

**Why you would never guess this.** Rome already has hipposandals
(strap-on, temporary), so the gap is committing to a permanent nailed
fitting, needing skill to avoid laming the animal (the nail must miss
sensitive tissue by millimetres).

**Prerequisites.** Iron smithing plus a deliberately trained farrier
skill, not something any smith should improvise.

**Roman-available inputs.** Wrought iron shoe, specially tapered nails
that curl outward.

**Procedure.** Trim and rasp the hoof level. Shape a hot shoe to the
outline, hot-fit briefly (painless on insensitive horn, a smoke mark
shows high spots). Cool, nail on at a shallow outward angle, clinch flat.
Reset every one to two months.

**How you know it worked.** Normal gait immediately after; the shoe stays
tight with even wear.

**Failure modes.** A nail driven too deep ("quicked") causes lameness and
infection; too-small a shoe constricts the hoof.

**Cost & labour.** ESTIMATED (basis: roughly half a kilogram of iron per
shoe) a small fraction of a day per shoeing, repeated regularly.

**Danger.** To the horse if unskilled; to the farrier from kicks.

**Confidence: MEDIUM.** Clear benefit on paved roads, but genuinely a
craft skill needing practice.

---

### windmill - The windmill (no attested Latin term, wind power is
essentially unused for mechanical work in this period)

**What it is / why you want it.** A wind-driven mill where flowing water
is scarce, seasonal, or absent but wind is reliable.

**Why you would never guess this.** Obvious once you want it, but it took
centuries after 100 AD historically (Persian panemone mills from roughly
the 9th century, European post mills not before the 12th), likely because
water power was already good enough wherever anyone with the gearing
skill was trying.

**Prerequisites.** gearing_and_transmission, carpentry, sailcloth (linen).

**Roman-available inputs.** Oak framing, linen sails, iron main-shaft
bearing, hemp rigging.

**Procedure.** Build a post mill: the whole body sits on a massive
vertical post and rotates as a unit to face the wind, using a tail pole.
Mount four sails on a horizontal shaft, geared down via a wooden
lantern-and-wallower pair (well within existing carpentry, cruder than
the bronze gearing already proven in the Antikythera mechanism) to a
vertical shaft driving the stones. Fit a brake and a way to reef sails in
high wind.

**How you know it worked.** Reliable grinding across a range of wind
strengths, safely stoppable before a gale.

**Failure modes.** Unbraked mills over-speed and self-destruct in gusts;
a mill sited without checking prevailing wind sits idle or fights a
variable direction.

**Cost & labour.** ESTIMATED (basis: comparable timber/gearing to a water
mill, minus leat/millpond works) similar to or less than a water wheel.

**Where wind beats water.** Flat, treeless, windy regions without a good
perennial stream: North African grain provinces, drier southern Hispania,
and especially the Aegean islands, which lack major rivers but catch
strong, reliable seasonal winds (ESTIMATED, basis: inference from the
well documented later concentration of windmills in exactly these
regions).

**Danger.** An unbraced or storm-caught mill is a structural hazard.

**Confidence: MEDIUM.** Simple mechanism, well within Roman skill, but no
Roman-era windmill exists to point to.

---

### precision_three_plate - Whitworth's three-plate method (no Latin
term; the flagship trick of this module)

**What it is / why you want it.** A way to create a genuinely flat
surface (a "surface plate") using only three roughly-flat plates, an
abrasive, and patience, with no pre-existing flat reference at all. That
plate becomes the parent of every straightedge, square, screw, gauge, and
straight-bored cylinder that follows. It needs nothing Rome does not have.

**Why you would never guess this.** The surprise is the logic. Rub only
two plates together with abrasive and they converge until they fit
perfectly everywhere, no gaps. But "fits everywhere" does not mean flat:
two plates can converge on a matched curved pair, one convex, one
complementary concave, like a ball and socket, fitting perfectly to the
touch yet neither flat. Add a third plate, rub all three against each
other in rotation (A-B, B-C, C-A), correcting each pairing. Suppose A is
convex: for A-B to mate, B must be concave; for A-C to mate, C must also
be concave, matching A. But B and C, both concave, cannot mate against
each other, they only touch at centre or edge, never everywhere. The
contradiction resolves only if curvature is zero: flat is the one shape
self-consistent across all three pairings. Run the rotation long enough,
and pure internal geometric consistency drives all three plates to a
common true plane. Attributed to Joseph Whitworth in the 19th century,
but it uses nothing Rome lacks.

**Prerequisites.** Bronze casting or hard stonework; none of this
module's other entries, this is the true starting point.

**Roman-available inputs.** Cast bronze or dense stone (basalt, dense
limestone); ground emery or fine sand in olive oil as abrasive; red ochre
or minium (an existing Roman pigment) in oil as marking medium; a
hardened scraper.

**Procedure.** Cast or cut three plates of similar size, as flat as
ordinary craft skill allows. Coat plate A thinly with marking medium, rub
B against A with light, even pressure in a rotating pattern, separate:
the medium marks B's high spots, scrape them down. Repeat for B-C, then
C-A, rotating each plate's own orientation a third-turn between rubs so
hand-pressure bias averages out. Continue the cycle; each pass should
show fewer high spots. Done when every pairing shows even, full-area
transfer at once.

**How you know it worked.** All three plates mate with uniform contact
for every pairing. Further test: two clean, smooth plates pressed and
slid together will "wring," sticking by atmospheric pressure and surface
adhesion.

**Failure modes.** Stopping at two plates, the single most common error,
produces a matched curved pair, not flat. Skipping plate rotation lets
hand pressure bias the set toward a curve.

**Cost & labour.** ESTIMATED (basis: comparable to fine stone/bronze
finishing for optical glass or statuary) several weeks for the first
good set; later sets are faster.

**Danger.** Metal and stone dust, wear a cloth over nose and mouth.

**Confidence: HIGH.** Rigorous, well documented geometric logic; the
materials and abrasives are all attested Roman goods.

---

### straightedge_square_gauge - Deriving the straightedge, square, and
roundness from the plane (no Latin term)

**What it is / why you want it.** With a true flat plane, derive every
other geometric reference: a straight line, a right angle, a way to check
roundness. The surface plate is the parent of all subsequent measurement.

**Why you would never guess this.** Obvious once you have the plate; the
hard part was getting the plate.

**Prerequisites.** precision_three_plate.

**Roman-available inputs.** The same bronze or stone stock, straight
timber or iron bar, cord for layout.

**Procedure.** Straightedge: the three-plate logic works one dimension
down, lap three bars' edges against each other in rotation, or lap one
directly against the flat plate. Square: stand a straightedge on the
plate and check perpendicularity with a cord marked into twelve equal
lengths formed into a 3-4-5 triangle (already used by the agrimensores
with the groma); check the gap at increasing distance, a true right angle
shows zero gap at any distance. Roundness: rest a shaft in V-blocks on
the plate, touch it with a fixed scriber, turn slowly; a continuous mark
means round, a partial mark reveals a high or low spot.

**How you know it worked.** No gap between straightedge and plate at any
rotation; no gap in the scribed right angle at any distance; a continuous
scribe mark all around a rotating shaft.

**Failure modes.** Checking a straightedge in only one orientation hides
a curve; checking a square only at short range hides an error that grows
with distance.

**Cost & labour.** ESTIMATED (basis: far smaller than making the original
plates) a few days per tool.

**Danger.** None beyond ordinary workshop hazards.

**Confidence: HIGH.** Direct logical extensions of the three-plate
method; the cord-triangle right angle is independently attested Roman
surveying practice.

---

### screw_cutting_lathe - The lead screw, slide rest, and change gears
(the machine that makes machines)

**What it is / why you want it.** A lathe that cuts precise, repeatable
screw threads by linking workpiece rotation to a controlled tool
movement through a master screw (the lead screw). Once one accurate
screw and nut exist, the machine makes the next more accurately still.

**Why you would never guess this.** The hard part is the bootstrap:
cutting the first accurate screw seems to need a machine that itself
needs an accurate screw. The way out is the same self-referential trick
as the three-plate method: successive approximation, not a pre-existing
reference.

**Prerequisites.** precision_three_plate and straightedge_square_gauge
(true bed and reference), the pole or bow lathe as the starting machine.

**Roman-available inputs.** Bronze or iron for screw and nut, oak or
stone for the lathe bed, thin leather or papyrus for the wrap-around
template (Rome has no true paper, Chinese paper is not traded west for
centuries; papyrus from Egypt or a thin, evenly-cut strip of leather
serves the same purpose), fine abrasive for lapping.

**Procedure.** Wrap a strip of thin leather or papyrus of fixed width
helically around a cylinder so successive wraps' edges just touch; strip
width and
diameter fix the helix angle (a chosen pitch). Scribe along the strip's
edge onto the cylinder, unwrap: a true helical line exists, guaranteed by
geometry, not hand skill. Cut a shallow groove along it with a file or
graver. Cast a matching nut and lap the two together with fine abrasive,
screwing back and forth repeatedly; mutual wear-in averages out local
errors, since only a consistent helix satisfies the nut at every point.
This becomes the master lead screw, mounted along a new lathe bed
parallel to the workpiece axis. Build a slide rest, a tool holder riding
a nut on the lead screw: as it turns (geared via exchangeable "change
gears" to a fixed spindle ratio), the tool advances at a matched,
repeatable rate; different gear ratios give different pitches, all
derived from the one master screw.

**How you know it worked.** A new screw threads smoothly into a matching
nut, even resistance along its length; two screws cut on the same setting
are interchangeable with each other's nuts.

**Failure modes.** A stretchy wrap template distorts the helix; stopping
lapping early leaves a screw that binds; a lathe bed not itself straight
reintroduces the error.

**Cost & labour.** ESTIMATED (basis: fine bronze instrument content, far
more hand labour for lapping) several months for the first master screw
and lathe; each later one is far faster.

**Danger.** Entanglement hazard from rotating work and the slide rest.

**Confidence: MEDIUM.** The wrap-strip helix and successive-
approximation lapping are well documented as how early instrument makers
solved this bootstrap problem, but the number of lapping cycles needed is
inherently trial-dependent.

---

### micrometer_gauge_blocks - Screw micrometer, vernier scale, and end
standards (no Latin term)

**What it is / why you want it.** Instruments that measure a length
precisely and repeatably instead of by eye, plus accurate blocks that
stack ("wring" together) to build any length from a handful of standard
sizes, so two workshops make parts that fit.

**Why you would never guess this.** The vernier scale is pure geometry:
two graduated scales of slightly different spacing, read together, give a
fraction of the smallest division without finer engraving.

**Prerequisites.** straightedge_square_gauge for scale division;
screw_cutting_lathe for the screw micrometer, which needs a fine,
accurate thread.

**Roman-available inputs.** Bronze or iron for frames and screws, bronze
or hardened iron for gauge blocks, fine dividers.

**Procedure.** Vernier: engrave a main scale accurately divided and a
shorter sliding scale slightly finer (nine divisions spanning the same
length as ten main-scale divisions); the vernier mark that aligns with a
main-scale mark gives the fractional reading by inspection. Screw
micrometer: mount a fine, accurately-pitched screw so one turn advances a
measuring face exactly one thread pitch, and engrave a graduated collar
dividing that turn into equal fractions. Gauge blocks: exact thicknesses,
each pair of faces lapped dead flat with the three-plate technique, so
combinations stack to any length; sufficiently flat, clean, dry blocks
will wring. Define your own reference standard now: deposit a master
bar, checked against your best straightedge, in a temple or archive, as
Rome keeps weight and volume standards for the libra, so every gauge
afterward is checked against one reference and parts from different
cities fit.

**How you know it worked.** Two independently-made blocks of the same
nominal size show no gap face to face; a part measured twice gives the
same reading both times.

**Failure modes.** An unevenly-engraved vernier gives a plausible but
wrong reading, worse than none, because it is trusted; blocks that will
not wring reliably usually mean surface-plate flatness is not yet good
enough.

**Cost & labour.** ESTIMATED (basis: fine instrument-making labour) weeks
of skilled work for the first complete set and reference standard.

**Danger.** None beyond ordinary fine metalworking hazards.

**Confidence: MEDIUM.** The vernier and end-standard logic is pure
geometry, HIGH confidence on its own; the screw micrometer's confidence
is lower, tracking the master screw's quality from screw_cutting_lathe,
which pulls the entry's overall rating down to MEDIUM.

---

### boring_mill - The cylinder boring machine (no Latin term)

**What it is / why you want it.** A machine that bores a hole straight
and round by supporting the cutting bar rigidly at both ends and
advancing it steadily, instead of cutting freehand or cantilevered. This,
not the idea of steam power, is what blocked a working steam engine so
long: a piston cannot seal against a cylinder that wanders off round or
straight.

**Why you would never guess this.** People assume steam engines waited on
a conceptual leap; mostly they waited on this. John Wilkinson's 1774
boring machine, built for cannon barrels, first let Watt build a
cylinder good enough to seal reliably. Boulton reportedly said
Wilkinson's bored cylinders did not err from true by more than the
thickness of a worn shilling coin across the whole bore (MEASURED as a
historical quotation, treat as the attested claim, not an exact figure).

**Prerequisites.** precision_three_plate and straightedge_square_gauge,
screw_cutting_lathe, water_power_scaleup or crank_connecting_rod to
drive it.

**Roman-available inputs.** Cast bronze or wrought iron for the cylinder
blank, hardened iron tools, oak and iron for the boring-bar frame.

**Procedure.** Mount the blank to rotate steadily on a mandrel, like an
oversized lathe workpiece. Pass a rigid boring bar through its axis,
supported in fixed, true bearings at both ends, not cantilevered. A
one-end-supported bar droops wherever it meets a harder or softer patch
in the cast metal, producing an oval or tapered bore; a bar fixed at both
ends cannot wander. Fix a cutting tool at the desired radius and advance
the bar slowly (lead-screw fed) while the blank rotates, cutting a bore
round and straight throughout. Finish with a fine pass, checking with the
V-block-and-scriber logic via an internal probe.

**How you know it worked.** A piston or plug slides the full bore length
with even resistance; a feeler shim cannot be worked in anywhere without
binding evenly.

**Failure modes.** A single-end-supported bar reintroducing droop, the
exact failure this machine prevents; casting flaws (blowholes, hard
spots) in the blank, common in this era, worth sound-testing before
committing hours.

**Cost & labour.** ESTIMATED (basis: comparable scale to a large force
pump) a substantial capital project, months of skilled labour for the
first machine.

**Danger.** Heavy rotating cast metal is a serious crush hazard if
mounting fails.

**Confidence: HIGH** on the mechanical principle (supported-both-ends
beats cantilevered); MEDIUM on exact achievable tolerance with
Roman-grade materials, since 18th century cast iron somewhat exceeds
early Roman foundry quality.

---

### steam_atmospheric - The Newcomen atmospheric engine (no Latin term)

**What it is / why you want it.** The first genuinely useful steam-
powered pump, mainly for mine drainage, where atmospheric pressure does
the work and steam only creates a vacuum.

**Why you would never guess this.** This is not really a steam engine
doing work by steam pressure. Low-pressure steam fills a cylinder below a
piston, then a cold-water jet condenses it almost instantly, creating a
partial vacuum; atmospheric pressure above pushes the piston down, the
actual power stroke. It works with crude tolerances precisely because it
needs no high pressure and no fine seal (a leaky piston is merely
inefficient, not dangerous), which is why it could exist before
boring_mill-grade cylinders did.

**Prerequisites.** bearings_lubrication and basic iron/copper working
suffice; crank_connecting_rod is not needed (a simple rocking beam is
used); this is deliberately the cheap, crude, real starting point.

**Roman-available inputs.** Copper or bronze boiler, cast bronze cylinder
(Rome AS YOU FIND IT has no cast iron in the West, bloomery wrought iron
only. By the time you can build an engine at all you will have introduced the
blast furnace, so cast iron cylinders will in fact be available and are the
better choice; the bronze option below is the fallback if you reach this point
first, which the tech tree says you should not. Bronze
is the practical cylinder metal here), leather piston seal, coal (mined
in Roman Britain) or wood as fuel.

**Procedure.** Build a simple low-pressure boiler. Build a large vertical
cylinder and piston, chained over a pivoted beam to a pump rod. Admit
steam below the piston as the heavier pump-rod side pulls it up. At the
top of the stroke, close the steam valve and inject a cold-water spray,
condensing the steam almost instantly. Atmospheric pressure pushes the
piston down, lifting water at the pump end. Drain and repeat.

**How you know it worked.** A steady, rhythmic cycle of steam admission,
the condensing "thump," the beam rocking, and water continuously lifted.

**Failure modes.** A leaky piston or boiler wastes enormous fuel without
stopping the engine, just starving it; scale buildup risks overheating.

**Cost & labour.** ESTIMATED (basis: comparable to the largest Roman
industrial installations) a very large build effort; worthwhile chiefly
where fuel is free on site. Widely cited estimates put early
Newcomen-type thermal efficiency well under 1% (MEASURED as a commonly
cited range, treat as an order of magnitude, not a precise percentage).

**Danger.** A dry or over-pressured boiler can rupture even at low
pressure; scalding is routine. Introduce it openly as a mine-drainage
pump, a clearly practical purpose.

**Confidence: HIGH** on mechanism and logic; MEDIUM on exact efficiency
figures.

---

### steam_watt - Watt's separate condenser (no Latin term)

**What it is / why you want it.** Keeps the working cylinder permanently
hot and condenses in a separate, permanently cold vessel, avoiding the
waste of reheating the cylinder every stroke, which Newcomen's design
does.

**Why you would never guess this.** It looks like a small plumbing
change, but the waste removed is enormous: repeated reheating of the
cylinder metal, not the water pumped, consumes most of Newcomen's fuel.

**Prerequisites.** steam_atmospheric as the base design; boring_mill
matters more here, a tighter-sealing piston keeps more of the now more
valuable steam from leaking uselessly.

**Roman-available inputs.** Same as steam_atmospheric, plus insulating
lagging (straw, wool, ash) for the hot cylinder jacket.

**Procedure.** Build a separate small condenser vessel, valved, kept
permanently in cold water. Insulate the main cylinder in a steam jacket
kept hot by live steam, so it never cools between strokes. Where
Newcomen would inject cold water directly, open the valve to the
condenser instead, pulling a vacuum without cooling the cylinder. Pump
condensed water and air out of the condenser continuously.

**How you know it worked.** For the same cylinder and work, fuel
consumption drops noticeably, commonly cited as two to three times
better fuel economy (MEASURED, widely cited historical duty-trial
comparisons, exact multipliers vary).

**Failure modes.** A leaking condenser valve loses most of the vacuum
benefit; insufficient cooling-water flow lets it warm and stop condensing.

**Cost & labour.** ESTIMATED (basis: a modest addition, one vessel,
valve, auxiliary pump) smaller than the base engine's own cost.

**Danger.** Same pressure and scalding hazards as steam_atmospheric.

**Confidence: HIGH.** One of the best documented improvements in the
history of technology; the logic is straightforward thermodynamics.

---

### steam_high_pressure - High pressure, non-condensing steam (no Latin
term)

**What it is / why you want it.** Steam well above atmospheric pressure,
pushing the piston directly, no bulky condenser needed, giving smaller,
lighter engines, at the cost of a genuinely strong boiler.

**Why you would never guess this.** "Just use more pressure" looks
obvious, but it came later historically because it demands boiler
engineering good enough not to kill people, which lagged well behind the
idea. A weak boiler at high pressure is a bomb, not an engine.

**Prerequisites.** boring_mill for a cylinder that seals under real
pressure; a genuine step up in boiler-plate quality and riveting/brazing
skill beyond steam_atmospheric.

**Roman-available inputs.** Wrought iron plate (better than a
low-pressure kettle needs), copper for fittings and safety valves,
careful riveted or brazed seams.

**Procedure.** Build a boiler from wrought iron plate sized for the
intended pressure with a real safety margin. Fit a safety valve lifting
automatically past a set pressure, not optional. Fit a reliable
water-level gauge (a glass or mica sight-tube) so an operator sees before
water drops low enough to overheat the boiler metal, the most common
cause of catastrophic failure. Admit steam directly to a precisely
bored, sealed cylinder, exhausting used steam to atmosphere
("non-condensing"). Optionally cut off admission partway through the
stroke and let it expand for more work.

**How you know it worked.** A much smaller, lighter engine delivers the
same power as an atmospheric one; the safety valve lifts cleanly under a
deliberate test; the water gauge tracks level reliably.

**Failure modes, stated honestly.** Boiler explosions were a genuine,
common cause of death in this era: flawed plate, a tampered safety
valve, or water run low so the overheated shell ruptures when more water
reaches it, killed people through much of the 19th century, especially
in steamboats and factories, forcing the first engineering inspection
laws (a documented pattern, not a specific death toll, a precise figure
here would not be genuine). Never run a high-pressure boiler without a
tested safety valve and reliable water gauge, or load down the valve.

**Cost & labour.** ESTIMATED (basis: a real step up in metalworking
quality and inspection discipline from steam_watt) meaningfully more
expensive per unit of power, justified where size and weight matter.

**Danger.** Severe, genuinely lethal if ignored; treat every boiler as a
potential bomb until proven, test incrementally well below rated
pressure; a failure draws hostile official attention, test isolated.

**Confidence: HIGH** on the engineering logic and historical pattern of
failure; deliberately no specific safe pressure figure is given, that
depends on actual achieved iron-plate quality, tested empirically.

---

### bearings_lubrication - Plain bearings, babbitt metal, and lubricants
(no single Latin term; cf. existing Roman bronze bushings)

**What it is / why you want it.** Every rotating or sliding part above
needs a bearing that resists wear, tolerates misalignment, and is cheap
to replace, plus a lubricant that stays put under real load.

**Why you would never guess this.** Rome already has more of this than
assumed: the Nemi ships (ceremonial vessels sunk in Lake Nemi, later
excavated) were fitted with wooden ball-and-roller thrust bearings, a
genuine attested Roman rolling-element bearing (MEASURED, an
archaeological finding). The gap is a soft, sacrificial alloy purpose-
built to protect the shaft it supports.

**Prerequisites.** Bronze casting, tin (Cornwall) and antimony ore
(stibnite, already used as a Roman cosmetic, "stibium," per Pliny) for a
babbitt-like alloy.

**Roman-available inputs.** Tin bronze and leaded bronze for ordinary
bushings, tin and antimony for a soft white-metal liner, olive oil and
animal tallow as lubricants.

**Procedure.** For ordinary loads, cast plain bronze or leaded-bronze
bushings, as already practiced in Roman wheel hubs. For higher loads
(crank-pins, boring-mill spindles), cast a soft sacrificial liner: a
tin-based alloy with a smaller proportion of antimony and copper (the
1839 Babbitt patent alloy is commonly cited near nine parts tin to one
part each antimony and copper by weight, MEASURED as a historically
documented formula, expect to adjust by trial). The liner wears
preferentially, embeds grit harmlessly, and is cheaply recast. Lubricate
with olive oil for lighter, faster bearings and tallow for heavier,
slower loads (tallow solidifies in cold weather); feed from a reservoir
or wick, not manual reapplication.

**How you know it worked.** A bearing run under load for a full day feels
only warm, not hot; smooth, even wear on inspection.

**Failure modes.** Olive oil oxidizes and gums up over weeks; a too-hard
bearing (skipping the soft liner) transfers wear to the expensive shaft.

**Cost & labour.** ESTIMATED (basis: small material quantities, mostly
labour) modest per bearing; the real saving is reduced downtime.

**Danger.** Molten-metal casting burns.

**Confidence: HIGH** on plain bronze bearings and the Nemi precedent;
MEDIUM on the specific babbitt proportions, expect adjustment by trial.

---

### gearing_and_transmission - Involute versus cycloidal teeth, gear
cutting, belts, and line shafting (no Latin term; cf. the Antikythera
mechanism's attested fine gearing)

**What it is / why you want it.** Reliable ways to cut gear teeth that
mesh predictably, and distribute power from one prime mover to many
machines using belts and a central shaft.

**Why you would never guess this.** The Antikythera mechanism (roughly
150-100 BC, over thirty bronze gears, the largest with 223 teeth,
MEASURED, an extensively studied excavated artifact) proves fine
gear-cutting already exists. Missing is a standardized tooth shape
letting gears from different batches mesh correctly, and a habit of
distributing power around a whole workshop.

**Prerequisites.** straightedge_square_gauge for tooth-spacing layout;
screw_cutting_lathe and dividing jigs help greatly.

**Roman-available inputs.** Bronze for fine gearing, iron for heavier
gearing, leather for belting, oak for shafting.

**Procedure.** Cycloidal teeth: a profile from rolling a circle along the
blank's edge, correct only at one fixed centre distance, but almost
certainly close to what cut the Antikythera gears. Involute teeth (the
better, later standard): based on the involute of a circle, any two
involute gears of the same pitch mesh correctly despite small
center-distance variation, and one rack-shaped cutter generates any size
of a given pitch, which is what makes it practical for interchangeable
production. Cut teeth using a dividing plate to mark equal spacing, then
cut each space with a shaped cutter or file. For workshop power, mount a
line shaft driven by wheel or engine in fixed bearings, and belt each
machine via its own pulley, engaged or disengaged with a loose idler
pulley.

**How you know it worked.** Gears run quietly with no chattering; a
belted machine engages and disengages smoothly.

**Failure modes.** Mismatched cycloidal gears bind or chatter; an
unguarded line shaft and belts are a serious entanglement hazard.

**Cost & labour.** ESTIMATED (basis: fine metalwork for small precision
gears, much less for transmission gearing) ranges widely with size.

**Danger.** Unguarded rotating gears, shafts, and belts are a common
source of severe injury; guard pinch points.

**Confidence: HIGH** on cycloidal cutting, directly attested by the
Antikythera mechanism, and on the involute and line-shafting principles
themselves, which are sound geometry and mechanics; MEDIUM on how fast a
Roman workshop reaches production-grade involute cutting in practice.

---

### hydraulics_pumps - Improving the force pump, the trompe, the
hydraulic press, and the accumulator (cf. the Roman force pump,
Vitruvius, *De Architectura*, Book X)

**What it is / why you want it.** Rome already has a genuinely good force
pump (double-acting, valved, attested by surviving bronze pumps at
Bolsena and Silchester, MEASURED). The path forward: better seals and
higher pressure, plus the trompe (air compression, no moving parts), the
hydraulic press (force multiplication by unequal piston areas), and the
accumulator (smoothing pump output, like the flywheel).

**Why you would never guess this.** The trompe stands out: compressed
air with zero seals and zero precision machining, at a time when no good
air-tight piston exists. Falling water in a pipe entrains air bubbles at
turbulent inlets near the top, carrying them into a chamber where air
separates and rises into a dome under pressure set by fall height, ideal
for a forge blast well before piston technology is ready.

**Prerequisites.** The existing Roman force pump as baseline;
bearings_lubrication and better leatherwork for tighter seals;
boring_mill once higher pressures are wanted.

**Roman-available inputs.** Bronze for pump barrels and valves, leather
for piston cups (tallow-soaked), lead pipe for the trompe's fall-pipe,
stone or timber for the accumulator's frame.

**Procedure.** Improve force-pump seals with tallow-soaked leather cup
packing. Build a trompe: a vertical pipe from a header tank fed by a
natural fall, small air-inlet holes near the top where turbulence
entrains bubbles, into a closed chamber; water drains out the bottom
while air collects under pressure in a dome above. Build a hydraulic
press: two cylinders of different piston diameter joined by a
water-filled pipe; force at the small piston gives a proportionally
larger force at the large one, scaled by the area ratio (DERIVED, basic
fluid statics). Build an accumulator: a weighted ram a force pump fills
intermittently, feeding pressure out smoothed between strokes, analogous
to a flywheel.

**How you know it worked.** The improved pump holds pressure longer; the
trompe delivers a continuous bubble stream that visibly blows out a
candle; the press visibly multiplies a small known force.

**Failure modes.** Trompe air inlets too large or small flood the pipe or
entrain too little air; press seals leak under high force.

**Cost & labour.** ESTIMATED (basis: modest addition to existing Roman
practice) generally cheap relative to the precision machine tools
elsewhere in this module.

**Danger.** Pressurized water and air lines can fail suddenly if
undersized, test incrementally.

**Confidence: HIGH.** The force pump baseline is directly attested; the
trompe, press, and accumulator rest on simple, well understood fluid
statics.

---

### interchangeable_parts - Go/no-go gauges, tolerance, jigs and
fixtures (a management and measurement innovation, more than a
mechanical one)

**What it is / why you want it.** A system letting any one made part
replace any other without hand-fitting, turning a shop of skilled
individuals into one where less specialized labour, guided by gauges and
fixtures, produces consistent quantities. This is what turns a workshop
into an industry.

**Why you would never guess this.** Interchangeability is not mainly
about better machines, it needs a different idea of "correct": instead of
comparing a part to a mental ideal by feel (unique results every time),
define an acceptable range around a target size, a tolerance, and give
every worker a gauge that tests only "is this within range." The machine
tools above make it cheaper, but ordinary hand tools with disciplined
gauging and fixtures already get most of the benefit.

**Prerequisites.** straightedge_square_gauge and micrometer_gauge_blocks
for gauge-making.

**Roman-available inputs.** Bronze or hardened iron for gauge bodies, oak
or iron for jig and fixture frames.

**Procedure.** Pick a part made repeatedly and hand-fitted each time: a
ship's pulley block, needed by the hundred for the fleet and cranes, is
an excellent Roman example. Decide a tolerance: a nominal critical
dimension and a range wide enough for skilled work to hit reliably,
narrow enough that anything in range fits any mate. Make a go/no-go
gauge accurately with micrometer_gauge_blocks: the "go" end must fit a
correct part, the "no-go" end must not. Build a jig or fixture
positioning the workpiece identically every time. Retrain the shop to
aim at passing the gauge, letting less specialized labour do what used to
need a trained craftsman per piece. Real precedent: the Portsmouth Block
Mills (Britain, early 1800s, Marc Isambard Brunel's design, Henry
Maudslay's machine tools) applied exactly this, commonly reported to
have let a much smaller unskilled workforce replace well over a hundred
skilled block-makers at far higher output (MEASURED, a well documented
case, exact figures vary between sources, treat as illustrative).

**How you know it worked.** Two parts made weeks apart by different
workers both pass the same gauge and swap freely.

**Failure modes.** A tolerance too narrow causes high rejection; too wide
lets through parts that pass but do not function well together.

**Cost & labour.** ESTIMATED (basis: a modest one-time cost per part
type) small against labour savings once made in real quantity.

**Danger.** None beyond ordinary workshop hazards.

**Confidence: HIGH** on the underlying principle and historical
precedent; specific Portsmouth figures are illustrative, not exact.

---

### clockwork_escapement - Verge and foliot, pendulum, and balance
spring (cf. the Roman water clock, clepsydra, and the Antikythera
mechanism)

**What it is / why you want it.** A mechanism regulating a weight- or
spring-driven gear train into a steady, controlled tick, giving first a
mechanical clock, then a genuinely accurate one, needed for navigation
(longitude at sea), physics, and later electrical systems.

**Why you would never guess this.** Rome already has the two hardest
pieces solved separately, never combined. Ctesibius' water clock
(clepsydra), in Vitruvius, uses a float-regulated constant-head reservoir
feeding water steadily to a graduated dial, a genuinely clever feedback
device (MEASURED, an attested Roman invention). The Antikythera mechanism
proves fine gear-cutting already exists. Missing is only the escapement
idea: making a gear train release energy in small, discrete, evenly-timed
ticks.

**Prerequisites.** gearing_and_transmission for the drive train.

**Roman-available inputs.** Iron or bronze for the gear train, verge, and
escape wheel, a foliot bar with adjustable weights, coiled bronze wire
for a later balance spring.

**Procedure.** Verge and foliot: a weight-driven gear train ends in a
toothed "escape wheel." A vertical rod (the verge), with two angled
pallets, alternately catches and releases teeth, swinging a weighted
horizontal bar (the foliot), converting steady pull into a regular tick;
foliot weight position tunes the rate. Crude: early tower clocks are
commonly cited around fifteen to thirty minutes drift per day
(ESTIMATED, basis: commonly cited ranges from histories of early clocks),
fine for a monastery bell, not navigation. Pendulum: replace the foliot
with a swinging pendulum (credited to Galileo, roughly 1602, noting a
fixed-length pendulum's consistent period), coupled so each swing
releases one tooth; daily error commonly cited as dropping to a few
seconds to a minute for a well-built example (MEASURED-but-approximate).
Balance spring: for a clock that must move, fit an oscillating balance
wheel restrained by a coiled spring, giving a steady rate independent of
orientation, enabling a marine timekeeper for longitude and later
laboratory/telegraph timing.

**How you know it worked.** A visibly steady tick; checked daily against
an independent reference, accumulated error stays roughly constant, not
erratic.

**Failure modes.** Asymmetric foliot weights run it fast or slow; a
roughly-cut escape wheel ticks erratically (a gear-cutting problem, not
regulation).

**Cost & labour.** ESTIMATED (basis: fine metalwork comparable to
Antikythera-grade gearing) weeks of skilled work for a first example.

**Danger.** None beyond ordinary metalworking hazards; a very accurate
clock invites curiosity, framing it as an elaboration of the clepsydra
helps.

**Confidence: HIGH** on the verge-and-foliot and pendulum logic, simple
and needing nothing beyond Roman gear-cutting skill; MEDIUM on the
balance spring, whose achievable accuracy in a first Roman attempt is
uncertain.

---

## The bootstrap ladder of precision

Read this module as one dependency chain, not a shopping list. Each rung
needs the one below it, and the top feeds back down to improve every rung
again:

flat plate (precision_three_plate, needs only patience and three
roughly-flat blanks) -> straightedge (lapped against the plate) -> square
(built from the straightedge and plate) -> master screw (bootstrapped by
the wrap-strip helix and successive lapping) -> lead-screw lathe (built
around the master screw) -> micrometer and gauge blocks (accurate because
a true screw and flat reference now exist) -> bored cylinder (boring_mill,
whose bar is guided true because its frame was built and checked with the
tools above) -> engine (steam_atmospheric, then steam_watt, then
steam_high_pressure, each needing that bored cylinder to seal) -> better
machine tools (on-demand rotary power to drive a bigger boring mill, a
bigger lathe, a proper gear-cutting machine, more accurately than hand or
water power alone could manage).

This is a loop, not a line: a better engine builds a better lathe, a
better lathe cuts a better lead screw, a better lead screw makes a better
micrometer, a better micrometer checks the plate finer than eye alone,
and a finer plate bores the next cylinder straighter still. Do not skip
rungs: jumping from flat plate straight to steam engine has historically
failed, because the engine's usefulness is bottlenecked by exactly the
precision those steps supply.

---

## Sources and confidence

Roman-era sources: Vitruvius, *De Architectura*, Book X, for the force
pump, water-raising machinery, and general mechanical principles; Pliny,
*Naturalis Historia*, for materials (stibium/antimony, tin, lead) and
existing Roman machinery; the Hierapolis sawmill relief (3rd century AD)
for an early crank-and-connecting-rod mechanism, cited as "attributed,
unverified" beyond its bare existence; the Antikythera mechanism, studied
extensively by modern scholarship (notably the Antikythera Mechanism
Research Project and Tony Freeth's analyses), as direct proof of
Greek-Roman-era gear-cutting.

Later sources, used strictly as reference points for physics and honest
ranges, not as things Rome already has: Smeaton's 1759 wheel-efficiency
comparison; Leveau's reconstructions of Barbegal's output; Lefebvre des
Noëttes' 1931 harness thesis and its revision by Spruytte and Raepsaet;
Maudslay's screw-cutting lathe, Wilkinson's 1774 boring machine,
Newcomen's atmospheric engine, Watt's separate condenser, and
non-condensing high pressure steam (Trevithick, Evans, around 1800);
Babbitt's 1839 bearing-alloy patent; Whitworth's formalization of the
three-plate method; the Portsmouth Block Mills project (Brunel, Maudslay,
Goodrich); and the general history of verge-and-foliot, pendulum, and
balance-spring clock regulation.

Confidence is mixed by design, each entry states its own level. Physics
and geometry (water power arithmetic, three-plate logic, gear tooth
theory, fluid statics) are HIGH throughout, textbook and checkable by the
reader's own measurements. Attested Roman starting points (the force
pump, the clepsydra, the Antikythera mechanism, the Nemi bearings) are
HIGH because they are excavated or directly described artifacts. Numeric
ranges borrowed from later history (wheel efficiencies, steam duty
figures, clock accuracy, harness draught improvement) are marked
MEASURED-but-approximate or ESTIMATED with a stated basis, because they
come from post-Roman trials and cannot be assumed to transfer unchanged
to Roman materials and workmanship. Treat every such figure as the right
order of magnitude, confirmed by the reader's own testing on site, not as
a number to design blindly around.
