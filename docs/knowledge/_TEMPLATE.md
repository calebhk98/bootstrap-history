# KNOWLEDGE MODULE TEMPLATE

Every knowledge module in `rome/knowledge/` MUST follow this structure. It is
written for a **competent adult with no specialist training** who has been
dropped into 100 AD. Assume the reader is smart, literate, has this guide, and
has nothing else. Assume they do NOT already know that a glass bead is a
microscope.

---

## Entry format

Each recipe/technique is one `###` section using exactly these fields:

### <TECH_ID> - Plain English name (*Latin/Greek name if one exists*)

**What it is / why you want it.** One or two sentences. State the payoff.

**Why you would never guess this.** The non-obvious kernel. If there isn't one,
write "Obvious once you want it." Do not pad.

**Prerequisites.** Tech IDs from `rome/data/tech_tree.json`, plus any raw
materials, plus any skill you must already have.

**Roman-available inputs.** Name the substance the way a Roman would recognise
it AND the modern name, with where in the Empire it comes from.

**Procedure.** Numbered steps. Give real numbers: masses, ratios,
temperatures (state both °C and a Roman-observable proxy such as "cherry red",
"straw yellow on iron", "flows like honey"), times, vessel materials.

**How you know it worked.** An observable test. Romans have no instruments;
give them a sense-based or simple-comparison check.

**Failure modes.** What actually goes wrong and what it looks like.

**Cost & labour.** Personal hours (you), artisan hours by trade, materials with
quantities, capital in denarii, calendar time. Mark each as MEASURED (real
historical figure), DERIVED (computed from a stated basis), or ESTIMATED.

**Danger.** Physical (poison, explosion, burns) and social (what a Roman
magistrate would think you are doing).

**Confidence: HIGH | MEDIUM | LOW** - plus one line saying why. HIGH means the
chemistry/physics is textbook and the Roman-era feasibility is well attested.
LOW means you are extrapolating.

---

## Hard rules for anyone writing these modules

1. **Never invent a number.** If you do not know a figure, write
   `ESTIMATED (basis: ...)` and give your reasoning. A flagged estimate is
   correct; a confident fake number is a failure.
2. **Anachronism check.** Before you list an input, ask: did the Roman world of
   100 AD actually have this, and where from? Traps that have caught people:
   - Roman *nitrum*/*natron* is **sodium carbonate**, NOT saltpetre.
     Potassium nitrate must be farmed in nitre beds. This is the single most
     common error in "bootstrap Rome" plans.
   - Romans had **no cast iron in the West** (bloomery only), no coke, no
     blast furnace, no crucible steel of their own (wootz was imported).
   - Romans had **no zero, no positional notation, no algebraic symbolism**.
   - Romans had **no distilled spirits**, no soap-as-cleanser (sapo was a
     Gallic hair pomade), no paper (Chinese paper is 105 AD, not traded west
     for centuries), no horse collar, no stirrup, no spinning wheel,
     no crank-and-connecting-rod until c. 3rd century (Hierapolis).
   - Romans **did** have: glassblowing and near-colourless glass, mercury
     (Almadén, Spain - imperially operated), lead, tin (Cornwall), brass by
     cementation, hydraulic concrete, water mills, the screw press,
     the force pump, alum (Melos), pyrolusite (MnO2), sulfur, vitriols,
     lodestone, and asbestos.
   - New World materials do **not** exist for you: no rubber, no quinine,
     no Chile saltpetre, no potato, no maize, no tobacco.
     Far-East materials are trade-reachable but ruinously dear:
     silk, shellac/lac, camphor, cassia.
3. **State the temperature range** for anything thermal, and say how to reach
   it with charcoal + bellows (~1200 °C hand, ~1500 °C water-blown) versus
   what needs a better trick.
4. **Cite when you can.** Pliny *Naturalis Historia*, Vitruvius, Dioscorides,
   Frontinus, Columella, Galen, Hero of Alexandria are the primary sources a
   Roman scholar can actually consult. Use book/chapter where you are sure.
   If unsure of the citation, say "attributed, unverified".
5. **No em dashes.** Use commas or a plain hyphen.
6. Cross-reference other modules by filename and anchor.
