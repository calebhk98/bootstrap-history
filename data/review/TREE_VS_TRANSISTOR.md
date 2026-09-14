# The road to `point_contact_transistor`, checked against the real history

Status: complete. Part 1 (the reconstruction) was written and saved before
the tree's closure was consulted at all, per the task's method requirement.
Method: web research (Computer History Museum's Silicon Engine, ETHW, Purdue
Physics history, technicshistory.com, and primary-adjacent secondary sources),
cross-checked against the general secondary literature (Riordan & Hoddeson's
*Crystal Fire*, Shockley's *Electrons and Holes*) from training knowledge where
a live source was not fetched verbatim. Sources are cited inline by domain;
full URLs are in the appendix at the end of this file.

---

## PART 1 — Independent reconstruction: what actually had to exist by Dec 16, 1947

### 1.1 The event itself, precisely

Bardeen and Brattain achieved the first working point-contact transistor at
Bell Telephone Laboratories on **December 16, 1947**; it was demonstrated to
lab management on **December 23, 1947** (the date usually cited publicly).
Shockley was present at the December demo but had not been in the room for
the Dec 16 breakthrough itself, which is part of why he went on to conceive
the (theoretically distinct) junction transistor weeks later, in January
1948. Public announcement was June 30, 1948. [computerhistory.org, ethw.org]

The device: two gold-foil point contacts, spaced roughly 50 micrometers
apart, mounted on a plastic (Bakelite-like) wedge and pressed onto the
surface of a **small slab of polycrystalline germanium** supplied (in
purified, doped form) via the wartime Purdue germanium programme. The
contacts were made by gluing gold foil to the wedge's point and slitting it
with a razor blade — a shop trick, not a precision-manufacturing process.
One contact was reverse biased, one forward; a signal on one modulated
current through the other, giving power gain. [technicshistory.com,
edn.com, CHM]

**Important, load-bearing correction to a common assumption**: the germanium
was *polycrystalline*, not single-crystal. Single-crystal germanium was
first pulled by Gordon Teal and John Little at Bell Labs starting **October
1948** — ten months *after* the point-contact transistor — using a modified
Czochralski technique, and its main payoff was for the *junction* transistor
(1950-51), not the point-contact device. Likewise, **zone refining**, the
technique everyone associates with "purifying germanium for the transistor,"
was developed by William Pfann at Bell Labs starting in **1950-51** and
published in 1952 — again *after* December 1947. Neither single-crystal
growth nor zone refining was a prerequisite for the actual invention; both
were prerequisites for turning it into a *manufacturable, reliable* device a
few years later. [CHM "Development of Zone Refining", CHM "First
Grown-Junction Transistors", technicshistory.com, ethw.org Teal oral
history]

### 1.2 What germanium purification the Dec-1947 device actually needed

What *did* exist by 1947, and was necessary:

- **Ore to metal.** Germanium is not mined as such; it was recovered as a
  byproduct of **zinc smelting flue dust** (also from some coal ashes),
  beginning at industrial scale in the 1940s. [USGS Mineral Commodity
  Profile; ResearchGate "Copper Flash Smelting Flue Dust as a Source of
  Germanium"] This means the raw-material chain is not "mine germanium ore"
  but "already be running a base-metal (zinc) smelting industry big enough
  to produce flue dust in quantity, then know to chemically scavenge a
  trace element out of that waste stream." That is a nontrivial industrial
  and chemical-analytic precondition most people would not think to name.
- **Chemical purification of germanium metal from GeO2**, developed and
  scaled through the wartime radar-rectifier programme (below), pushed
  crystal purity from roughly **99% at the start of the war to roughly
  99.999% by its end** through *fractional/directional crystallization*
  (repeated partial melting and freezing to reject impurities to the melt,
  a slower, cruder ancestor of zone refining) plus careful chemical
  reduction — not zone refining, which did not exist yet.
  [technicshistory.com quoting the wartime purity gain figure]
- **Deliberate doping.** Purdue's Seymour Benzer (under Karl Lark-Horovitz)
  spent over a year solving germanium rectifiers' "back-voltage" failure,
  eventually finding a **tin-doping** recipe that made rectifiers stable to
  over 100 V reverse bias. This is real materials science — controlled,
  intentional impurity addition to get a target electrical property — done
  three years before "doping" was even the accepted word for it, and it is
  the specific germanium (Purdue's high-back-voltage stock) that Bardeen
  and Brattain switched to using for their late-1947 experiments.
  [Purdue Physics history page]
- **Bell's own materials group.** Jack Scaff and Henry Theuerer at Bell
  Labs (with Ohl) did parallel wartime work characterizing dopants: they
  established that Group III elements (B, Al) give P-type and Group V (P,
  Sb, As) give N-type conduction — the donor/acceptor framework — during
  1945-46, published as NDRC contract reports, not journal papers.
  [search result quoting Scaff/Theuerer/Schumacher NDRC 14-555, Oct 1945]

So "germanium purification" for the actual transistor is not one node. It
is: (a) recognize germanium as recoverable from zinc-smelter waste, (b) a
wartime-funded, multi-year, multi-institution *programme* (not a single
technique) of chemical purification plus repeated-melt crystallization
driving purity from 99% to 99.999%, (c) an empirically-discovered, dopant
specific recipe (tin) for stabilizing electrical behavior, arrived at only
after a full year of one researcher's dedicated failure-driven search.
Only after all of that does a slab of usable germanium exist to press two
gold contacts onto.

### 1.3 The wartime crystal-rectifier programme as the hidden engine

None of the above happens without a specific, well-documented funding and
institutional structure:

- Vacuum-tube diodes cannot rectify efficiently at microwave (radar)
  frequencies because of transit-time and interelectrode-capacitance
  limits; radar receivers needed a **point-contact semiconductor
  rectifier/mixer** instead (silicon, then germanium). This was a matter of
  wartime survival (radar performance), so it got NDRC (Division 14)
  funding and coordination through the **MIT Radiation Laboratory**, with
  major materials work subcontracted to **Purdue** (germanium, under
  Lark-Horovitz) and **Bell Labs / DuPont / Sylvania / GE** (silicon and
  germanium both), 1942-1945. [Purdue Physics "War Period"; CHM "Semiconductor
  diode rectifiers serve in WWII"]
- This is the single biggest reason 99.999%-pure, deliberately-doped
  germanium existed in 1947 at all: a state actor spent several years and
  many institutions' worth of trained physicists and chemists on it because
  radar sets needed the rectifiers *right now*, not because anyone was
  trying to build an amplifier. The transistor is, in a very real sense, a
  spinoff of a crash wartime materials programme, not a standalone research
  target.
- The programme also produced the **diagnostic and production
  infrastructure**: standardized electrical test rigs for rectifier
  back-voltage and forward resistance, X-ray methods for crystal quality,
  and a trained cohort of people (Scaff, Theuerer, Ohl, Lark-Horovitz,
  Benzer, and others) who moved straight from "make radar diodes reliable"
  into "make a semiconductor amplifier" in 1945.

### 1.4 The physics theory stack (this is the part the founder already "knows")

- **Quantum mechanics and the quantum theory of solids** (Bloch, Peierls,
  Sommerfeld free-electron and band models), late 1920s.
- **Band theory of semiconductors specifically**: Alan Wilson, 1931-32,
  building on Bloch/Peierls, first formal donor/acceptor band picture.
  [Royal Society, CHM "Theory of Electronic Semi-Conductors"]
- **Rectification theory**: Wilson's 1932 tunneling explanation was wrong;
  the correct explanation (a surface/interface barrier — the
  Mott-Schottky-Davydov theory) arrived independently from Davydov (USSR),
  Mott (UK), and Schottky (Germany) in **1938**. [search result above]
- **Bardeen's surface-state theory, March 19, 1946**: explains *why*
  Shockley's April-1945 field-effect amplifier concept failed to work
  (surface states screen the applied field before it can modulate the
  bulk). This is the specific theoretical pivot that redirected the Bell
  group from "field effect" to "point contact" experiments — i.e., the
  theory here is not generic background, it is the proximate cause of the
  successful experiment 21 months later. [CHM "Invention of the
  Point-Contact Transistor"; CHM "The Surface State Job"]
- Statistical mechanics / Fermi-Dirac statistics for carrier populations,
  needed for any quantitative theory of doped semiconductors, is implicit
  throughout and was mature physics by the 1930s.

### 1.5 Precursor devices and the electrical/instrument industry under it all

- **Cat's-whisker crystal detectors** (Bose 1901, Pickard/galena patents
  1906) are the ancestral proof that a metal-semiconductor point contact
  rectifies at all; this is 40+ years of prior art and a whole radio
  industry's worth of practical experience with point contacts before
  1947.
- **The vacuum-tube triode** (De Forest, 1906-07) is the *functional target
  the transistor was built to replace* — Bell's entire "solid state
  amplifier" programme, chartered in 1945 under Shockley and Stanley
  Morgan with Brattain and Bardeen recruited into it, existed because the
  Bell System needed cheaper, more reliable, lower-power amplification for
  the telephone network's electromechanical switches and long-line
  repeaters than tubes and relays could give it. [insight.ieeeusa.org,
  britannica.com]
- **Instrumentation actually used in the Nov-Dec 1947 runs**: battery
  supplies, galvanometers/ammeters, an audio oscillator, and (per the
  standard account) an oscilloscope to watch the amplified waveform; none
  of this is exotic by 1947 — it is off-the-shelf electrical-measurement
  apparatus, but it presupposes a mature electrical instrument industry
  (precision meters, stable voltage sources, calibrated oscillators)
  behind it.
- **Bell Labs' machine shop and glass/metal fabrication culture**: the
  actual point-contact rig was hand-built from a plastic wedge, gold foil,
  a razor blade, and a bent paper clip — deliberately *not* high-precision
  manufacturing, but it still required a shop where physicists could get
  small custom parts (the plastic wedge, the spring contacts used in
  earlier point-contact rectifier work) made fast, on demand, by skilled
  technicians. [technicshistory.com; "Crystal Fire" quotes above]

### 1.6 The institutional/industrial base under all of it

- A telephone monopoly (AT&T/Western Electric) large enough to fund a
  multi-thousand-person basic-and-applied research lab (Bell Labs) with no
  requirement that every project show near-term return — Kelly could
  reactivate a "solid state amplifier" project in 1945 purely because Bell
  judged it strategically important for the phone network 10-20 years out.
- A national wartime research-funding apparatus (NDRC/OSRD) able to direct
  years of multiple universities' physics and chemistry departments at one
  narrow materials problem (radar crystal rectifiers) because it was a
  matter of military necessity — this is the actual origin of 1947-grade
  germanium purity, not a lone inventor's chemistry.
- A pre-existing radio/electronics manufacturing base (Sylvania, GE, RCA,
  Western Electric) that could scale diode production during the war, which
  is also where a lot of the practical crystal-handling know-how (mounting,
  doping trial-and-error, contact-forming) accumulated.
- A university physics establishment already fluent in quantum mechanics
  and solid-state theory by the 1930s (an international, decades-long,
  academic-freedom-dependent enterprise, not something one lab bootstraps).

---

## PART 2 — Comparison to the tree's 157-node closure

Checked against `rome/data/tech_tree.json` via `python3 rome/sim/simulator.py
validate|path point_contact_transistor|why <id>`. Confirmed: 157-node
required closure, 142.2-year critical path, 33 nodes deep, matching the
prompt.

### 2.1 The headline finding: the road gates the goal behind a device it did not need

`point_contact_transistor`'s direct `pre` list is:

```
galena_detector, gp_whisker_forming, micrometer_gauges, prc_lapping_plate,
quantum_solidstate_theory, single_crystal, vacuum_tube
```

`single_crystal` ("Czochralski single crystal growth and controlled
doping") is a **hard prerequisite** of the goal. Its own knowledge-base
entry (`rome/knowledge/55_semiconductors.md`, `single_crystal_growth`)
states, at HIGH/MEASURED confidence: *"polycrystalline germanium, however
many zone-refining passes, will never make a working transistor."* The
`point_contact_transistor` entry's own procedure step 1 is *"Confirm the
slab is single-crystal, n-type, with `semiconductor_metrology`."*

This is factually wrong for the device actually built on December 16,
1947. Independent sourcing above (Computer History Museum, EDN "Point
Contact Transistors: More to the Point", technicshistory.com, and the
general secondary literature) is consistent: **the original point-contact
transistor was built on a slab of polycrystalline germanium.** Gordon
Teal's first single-crystal germanium was pulled in **October 1948**, ten
months later, and its payoff was for the *junction* transistor (Teal &
Sparks, grown junction, 1950-51) — a device the tree itself, correctly,
gates separately behind `single_crystal` under `junction_transistor`
already. `zone_refining` is even more clearly out of place: the tree's own
`zone_refining` entry says outright, *"Pfann worked this out in 1952,
after the transistor already existed."* The authors knew this and gated
the goal behind it anyway.

**Why the KB's stated mechanism doesn't actually forbid the point-contact
device**, and this is worth stating precisely rather than just citing
authority: grain-boundary recombination kills minority-carrier lifetime
over the *centimeter-scale bulk path* a junction transistor's carriers
must survive crossing. A point-contact device's active region is the gap
*between two point contacts a few hundredths of a millimetre apart* —
often smaller than a single grain in coarse polycrystalline germanium, and
far too short a path for the boundary recombination the single-crystal
entry describes to be fatal. The mechanism the tree cites is real and is
exactly why single-crystal growth became necessary a few years later for
*junction* devices; it does not apply with the same force to the
geometry the goal node itself describes ("two fine metal points... a
fraction of a millimetre apart").

**Structural consequence, and this is the more important bug**: because
`single_crystal` is the *only* path by which `germanium_extraction`,
`gecl4_purification`, `ge_reduction`, and `cap_pure_6N` enter the goal's
closure, correcting the historical error by simply deleting the
`single_crystal` edge would also silently delete the entire, genuinely
necessary germanium-purification chain, leaving `point_contact_transistor`'s
own `mat.germanium_g` charged against nothing that produces germanium —
the exact "floating free" bug the tree's own commit history says it has
already caught and fixed once for `phosphor_bronze_g` and `mat_gold` on
`gp_whisker_forming` (see that node's `note` field, which documents the
fix). Any correction here has to *re-point* the germanium supply chain
directly onto the goal (or onto `gp_whisker_forming`), not merely remove
`single_crystal`.

I computed the exact set-differences by walking `tech_tree.json`'s `pre`
edges directly (script, not simulator, so this is independently checked
against the `why` output above):

- Full required closure today: **156 nodes** (excl. goal).
- Closure with the `point_contact_transistor -> single_crystal` edge cut,
  nothing else changed: **134 nodes**. Difference: **22 nodes** fall out.
- Of those 22, **9** are the genuinely-necessary germanium production
  chain (`germanium_extraction, gecl4_purification, ge_reduction,
  cap_pure_6N, zinc_industry_scale, lead_chamber, spectroscope,
  mirror_amalgam, fused_quartz, glass_borosilicate` — note
  `zinc_industry_scale` itself is one of the 9, since it has no other route
  into the closure either) — these must be **re-attached** directly to the
  goal (or to `gp_whisker_forming`) or the material floats free.
- The remaining **13** are pure padding that existed only to grow, machine,
  and quality-control a single crystal and a zone-refined ingot:
  `single_crystal, zone_refining, gp_czochralski_puller,
  in2_xray_diffraction_camera, gp_controlled_atmosphere_chamber,
  prc_gauge_blocks_johansson, arc_furnace_ferroalloys, semiconductor_metrology,
  el2_potentiometer, el2_potentiometer_method_measurement,
  el2_valve_voltmeter_high_impedance, mirror_amalgam is in the 9 not
  here, cap_measure_light`. (13 items; sum of their own listed `yrs`
  ≈ 36.8 years, cost ≈ 232,000 den — mostly parallel side-apparatus, not
  serial.)
- **Net effect of the correct fix: closure drops from 157 to about 144
  nodes** (goal included), and the printed critical path — which today
  runs `... -> germanium_extraction -> gecl4_purification -> ge_reduction
  -> zone_refining -> single_crystal -> point_contact_transistor` — loses
  the `zone_refining` (6.0 yr) and `single_crystal` (5.0 yr) links, cutting
  the **142.2-year floor to about 131 years**, an **11-year reduction**,
  none of it bought with money (both were flagged "money cannot buy this
  down" floors in the first place; they are just floors for a different,
  later device).

This is the single highest-value correction available in the whole tree
for this goal: it is a pure win (shorter critical path, fewer nodes,
cheaper build) that also makes the road historically correct, because the
thing being cut was never load-bearing for December 1947 in the first
place. `single_crystal` (with its whole apparatus tail) belongs on
`junction_transistor`'s road, not this one — and per §2.1's own numbers,
`junction_transistor` currently reaches `single_crystal` only *through*
`point_contact_transistor`, so it would need its own direct edge added to
keep that later device correctly gated once this fix lands.

### 2.2 MISSING

**M1. A germanium-doping node independent of single-crystal growth.**
The real donor/acceptor doping of germanium — Group V (P, As, Sb) for
n-type, Group III (B, Al, In) for p-type, established by Scaff, Theuerer
and Schumacher at Bell during the war, and Purdue's Seymour Benzer's
**roughly one-year, dedicated, empirical search** for a tin-doping recipe
that fixed catastrophic "back-voltage" failure — has no node of its own
anywhere in this tree. It exists only as a sentence inside
`single_crystal`'s recipe text ("Add a precisely weighed dopant trace...").
Once §2.1's fix removes `single_crystal` from the goal's road, doping
vanishes from the road entirely even though the goal's own node text
requires "an n-type germanium slab." This is real, load-bearing,
historically well-documented process that deserves its own gated step
between `ge_reduction` and `point_contact_transistor`/`gp_whisker_forming`
— not a Czochralski-pull-only feature.
  - **Proposed node**: `ge_doping_control` — controlled donor/acceptor
    doping by weighed trace addition during melt/directional-freeze
    (pre-single-crystal, matches the actual 1945-46 Bell/Purdue
    technique), producing n-type or p-type germanium ingot.
  - **Marginal cost**: its natural prerequisites — `ge_reduction`,
    `analytical_chemistry`, `balance_analytical` — are *already* in the
    goal's closure (present today via the `single_crystal` branch; present
    under the corrected tree via the re-pointed germanium chain in §2.1).
    So the marginal addition is **+1 node** to the closure, essentially free
    riding on infrastructure the tree already pays for. Recommend giving it
    a real, non-zero calendar floor (ESTIMATED 1-1.5 years) rather than an
    instant unlock: foreknowledge tells you *which* dopant and roughly what
    concentration to target (skipping Benzer's year of blind search), but
    not the concentration-vs-yield curve for a specific furnace and
    crucible-contamination profile, which still has to be found by running
    real batches (see Part 3, §3.6).

**M2. Nothing else major.** The rest of the reconstruction in Part 1 —
quantum mechanics / band theory / Mott-Schottky rectification theory
(folded, deliberately and reasonably, into the single `quantum_solidstate_theory`
node, whose own note explicitly says "Historically this took from 1900 to
1947 and several Nobel prizes. You carry the conclusions" — this is the
right abstraction for this game's premise, not a gap); the cat's-whisker
precursor (`galena_detector`, present and historically apt); the vacuum
tube as the device being replaced (`vacuum_tube`, present, direct
prerequisite); the germanium-from-zinc-flue-dust supply chain
(`zinc_industry_scale -> germanium_extraction`, present, and its own note
independently gets the "parts-per-thousand in flue dust against 1.6 ppm in
the crust" figure right); the forming-pulse point-contact fabrication
technique (`gp_whisker_forming`, present and accurate to Riordan &
Hoddeson's account) — are all represented at a reasonable grain. See §2.3
for the one item worth flagging as shallow.

### 2.3 PRESENT BUT SHALLOW

**S1. `semiconductor_metrology` (four-point probe + Hall effect) is a
plausible but slightly late-dated bundle, and it is currently reachable
*only* through the disputed `single_crystal`/`zone_refining` branch.**
Real point-probe resistivity measurement predates December 1947 — Bell's
own researchers used point-probe electrical characterization on germanium
surfaces before the December runs — so *some* minimal electrical
characterization step belongs directly under `point_contact_transistor`
or `gp_whisker_forming`. But the specific package modeled (four-point
probe *and* Hall effect *and* "every pass and pull becomes a measured,
converging process") reads as the more mature, systematic metrology
regime that came together across 1948-1950, not the ad hoc bench testing
of one specific December 1947 device. Recommend: keep a cheaper,
narrower "resistivity point-probe test" as a real, direct prerequisite of
`gp_whisker_forming` (it already sits downstream of `galvanometer` and
`electromagnet`/Wheatstone-bridge, both already in the closure, so this
would also be close to free), and move the full Hall-effect
`semiconductor_metrology` package to gate `single_crystal`/`junction_transistor`
where doping-profile verification actually mattered for manufacturing.

**S2. The germanium purification chain itself is *not* shallow** —
`germanium_extraction` (5 yr) -> `gecl4_purification` (5 yr) ->
`ge_reduction` (3 yr), 13 years across three separately-gated,
separately-risked nodes, reasonably matches a multi-year, multi-step,
multi-institution wartime effort, and `gecl4_purification`'s
99.9999% figure (`cap_pure_6N`) lines up with the sourced "99% to 99.999%
over the war" purity trajectory almost exactly. This is the one part of
the semiconductor branch the tree got both right and appropriately deep;
it is flagged only because §2.1's fix moves *where* it attaches, not
*how much* is modeled.

### 2.4 QUESTIONABLE (pad the road without having been needed for THIS device)

1. **`single_crystal`** — Czochralski growth did not exist until Oct 1948
   and was not what the Dec 1947 device used. 5.0 yr / 53,700 den / on the
   critical path. Belongs on `junction_transistor`'s road (add a direct
   edge there), not this one.
2. **`zone_refining`** — invented and published 1950-52, explicitly "after
   the transistor already existed" per the tree's own text. 6.0 yr /
   71,000 den / on the critical path. Same disposition as (1).
3. **`gp_czochralski_puller`** — the pulling rig itself; only exists to
   serve (1). 0.8 yr / 967 den.
4. **`in2_xray_diffraction_camera`** — used here only to verify single-crystal
   quality (Bragg-geometry lattice check); not something Bardeen and
   Brattain needed to press two points onto a polycrystalline slab.
   1.5 yr / 3,755 den.
5. **`gp_controlled_atmosphere_chamber`**, **`prc_gauge_blocks_johansson`**
   — furnace-chamber and gauge-block support specifically for the
   Czochralski rig. 0.7 yr / 1.0 yr respectively, modest cost each.
6. **`arc_furnace_ferroalloys`** — a direct prerequisite of `zone_refining`
   specifically (ferroalloys/carbides for the zone-refining furnace
   hardware); falls away with it. 12.0 yr / 77,980 den — the single most
   expensive item in the padding set.
7. **`semiconductor_metrology`, `el2_potentiometer`,
   `el2_potentiometer_method_measurement`, `el2_valve_voltmeter_high_impedance`,
   `cap_measure_light`, `mirror_amalgam`(via the X-ray camera) etc.** — the
   instrument tail that exists to characterize crystal quality and dopant
   profile for (1)/(2); see S1 for the more nuanced disposition (some of
   this legitimately belongs on the road in a lighter form, just not this
   heavy a form, and not gating this goal).
8. **Minor, low-priority bug worth a one-line flag**: `point_contact_transistor`'s
   `req_any` field lists a substitution group `{silicon_path: 0.9,
   single_crystal: 1.0}`. `silicon_path` itself requires
   `junction_transistor`, which requires `point_contact_transistor` — a
   forward reference that can never resolve as an alternate route *to* the
   goal. Harmless today (the goal's `pre` list, not `req_any`, does the
   real gating) but worth cleaning up alongside the `single_crystal` fix,
   since removing `single_crystal` from `pre` would leave this `req_any`
   group as the *only* remaining place the tree records that the goal has
   anything to do with single-crystal material at all, and it is inert.

---

## PART 3 — Where knowing the answer helps, and where it cannot

This founder is not Bell Labs. Bell had a state-funded, multi-institution
wartime materials programme (NDRC/OSRD, Purdue, MIT Rad Lab, Bell, DuPont,
Sylvania, GE, three-plus years, dozens of trained physicists and chemists
working full time on one narrow problem because a war depended on it), a
century-deep electrical-industrial base under that programme, a machine
shop and instrument-making culture on tap, and a telephone monopoly
willing to fund open-ended basic research. The founder has one head full
of correct answers and no other person who believes them yet. Going
through Part 1's reconstruction item by item:

**3.1 Theory (quantum mechanics, band theory, Mott-Schottky rectification,
Bardeen's 1946 surface-state insight) — foreknowledge is close to a total
win.** This is 47 years and several Nobel prizes of *other people's* labor
compressed to nothing but the founder's own writing-it-down time. The tree
gets this exactly right: `quantum_solidstate_theory` has a 4-year floor
that is really "write and cross-check your own notes," not "wait for
diffusion" — and it correctly has *zero* calendar-floor dependency on any
external institution. This is the cleanest case in the whole tree of
foreknowledge buying down a real historical cost to nearly zero, and the
tree already models it that way.

**3.2 The wartime crystal-rectifier programme's *empirical* content
(purification recipes, the tin-doping back-voltage fix) — foreknowledge
compresses but does not eliminate.** Knowing *that* tin fixes germanium's
back-voltage problem saves Seymour Benzer's roughly one year of blind
trial-and-error search. It does not save the physical time of running
doped-melt batches, freezing them, cutting samples, and testing them on
*this* founder's actual furnace, actual crucible-contamination profile,
and actual power-supply stability — none of which existed at Purdue either
until they built and iterated on their own apparatus. This is why I
recommended (§2.2, M1) that `ge_doping_control` keep a real, non-zero
calendar floor of roughly a year rather than becoming instant: the target
is known, the apparatus-specific calibration to reach it is not.

**3.3 The germanium purification chain itself (extraction from flue dust,
GeCl4 fractional distillation, hydrogen reduction) — mostly a floor,
partly compressible.** Knowing that germanium hides in zinc-smelter flue
dust at all is worth a great deal on its own — nobody in a pre-industrial
society would think to look for an element nobody has isolated in
parts-per-million concentrations inside another industry's waste stream,
and the tree correctly gives this to the founder for free via the recipe
text rather than requiring in-game discovery. But once you know *where* to
look, extracting, distilling, and reducing it to 6N metal is real bench
chemistry bound by real reaction rates, real furnace-cycle times, and a
trained workforce that has to exist before it can run three years of
distillation columns in parallel with everything else the founder is
building. The tree's own "Calendar floor: N years (money cannot buy this
down)" tags on all three of `germanium_extraction`, `gecl4_purification`,
and `ge_reduction` are the right instinct; foreknowledge shortens the
*search* for the right recipe, not the throughput of the equipment running it.

**3.4 The industrial base under all of it — the deepest, least
foreknowledge-buyable floor in the whole tree, and correctly so.**
`zinc_industry_scale`'s own note states this almost exactly right already:
*"CALENDAR FLOOR is set by diffusion, not by construction: the economy
needs roughly a generation to train the trades, form the capital and build
the suppliers. Money cannot buy this down."* Knowing that germanium comes
from zinc smelting does not let you skip needing an actual zinc industry
at the necessary *scale* — dozens of trained furnacemen, a coppice or coal
supply chain feeding tens of thousands of tonnes of fuel a year, enough
buyers of ordinary zinc (brass, galvanising, batteries) to make the
industry self-sustaining before its waste stream is worth mining for a
trace element nobody yet wants. This is a real, physical, generational
floor and the tree is right to make it the single longest link on the
critical path (12 years) after `power_grid`'s 25. Precisely the same logic
applies to the machine-tool chain further up the same critical path
(`workshop_first -> case_hardening -> precision_three_plate -> ...
-> screw_lathe -> boring_mill`, tools that make the tools that make the
next tools) and to `power_grid` itself: electricity at industrial scale is
a societal buildout measured in decades, not a technical puzzle a founder
can solve faster by knowing the answer, because the bottleneck is training
enough other people and building enough physical plant, not knowing what
to build. This is what the game should make the player feel, and on this
road it already does.

**3.5 Precision instrumentation and shop culture (micrometers, lapping
plates, gauge blocks, vacuum pumps, glass-metal seals) — a genuine middle
case.** Foreknowledge here is worth real time (it prevents false starts:
you know in advance that platinum-glass expansion matching works, that a
Sprengel pump needs no pistons, that Dumet wire is the cheap long-run
answer) but the *tool-chain-on-tool-chain* structure — you cannot cut a
precision lead screw without an already-precise lathe, cannot build that
lathe without an earlier, cruder one — is itself multi-generational in a
way that is bounded by what the previous generation of tools can
physically achieve, not by what the founder knows should exist at the far
end. This segment of the critical path (roughly `workshop_first` through
`boring_mill`/`interchangeable_parts`) is compressible at the margins by
avoiding dead ends, not collapsible the way the theory node is.

**3.6 The `single_crystal`/`zone_refining` detour — the clearest, sharpest
case for what foreknowledge is worth, stated as a number.** This is the
one place in the whole road where the tree currently makes the founder
pay for the *wrong kind* of knowledge. A founder who actually remembers
how the first transistor worked would know it ran on ordinary
polycrystalline germanium and would never authorize an 11-year,
230,000-denarius side-programme to grow and zone-refine a single crystal
they don't need yet. The tree's current road effectively forces the
founder to build the *1951* supply chain to reach the *1947* device. §2.1
and §2.4's fix is the concrete form of "the founder knows the answer" —
not a discount on any physical floor, but the removal of an entire
unnecessary floor the tree accidentally inserted. That asymmetry — real,
generational floors the tree is right to keep (zinc industry, power grid,
tool chain, the empirical dopant search) standing right next to one 11-year
floor that foreknowledge should have erased outright and didn't — is, I
think, the single most useful thing this review found: it gives the game
both halves of the feeling it wants in one place, the calendar floor money
can't buy down right next to the one floor that turned out to be a
mistake, not a lesson.

---

## Appendix — sources consulted

- Computer History Museum, "Silicon Engine" timeline entries: Invention of
  the Point-Contact Transistor (1947); Discovery of the p-n Junction
  (1940); Conception of the Junction Transistor (1948); Development of
  Zone Refining; First Grown-Junction Transistors Fabricated (1951);
  "The Theory of Electronic Semi-Conductors" is Published (1931).
  computerhistory.org/siliconengine/
- Engineering and Technology History Wiki (ETHW): "Bell Demonstrates
  Transistor"; "Russell Ohl"; Oral History of Gordon K. Teal.
  ethw.org
- Purdue University Department of Physics and Astronomy, "The War Period
  (1941-1945)" and Karl Lark-Horovitz biography.
  physics.purdue.edu/about/history/war_period.html
- technicshistory.com, "The Transistor, Part 2: Out Of The Crucible."
- EDN, "Point Contact Transistors: More to the Point."
- IEEE-USA InSight, "Your Engineering Heritage: Bell Labs and the
  Transistor."
- CHM Core blog / David A. Laws, "The Surface State Job."
- USGS Mineral Commodity Profile, Germanium (Butterman & Jorgenson).
- ResearchGate, "Copper Flash Smelting Flue Dust as a Source of
  Germanium."
- General secondary literature drawn on for cross-checking dates and
  figures per the task's suggested reading list: Riordan & Hoddeson,
  *Crystal Fire*; Shockley, *Electrons and Holes in Semiconductors*
  (background knowledge, not separately re-fetched verbatim this session).
- The tree itself: `rome/data/tech_tree.json`,
  `rome/knowledge/55_semiconductors.md`, and simulator output
  (`validate`, `path point_contact_transistor`, `why <id>` for
  `point_contact_transistor`, `single_crystal`, `zone_refining`,
  `semiconductor_metrology`, `ge_reduction`, `gecl4_purification`,
  `germanium_extraction`, `zinc_industry_scale`, `gp_czochralski_puller`,
  `gp_whisker_forming`, `quantum_solidstate_theory`, `junction_transistor`,
  `silicon_path`).
