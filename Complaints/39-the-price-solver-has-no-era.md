# The price solver prices everything with all of human technology available

**Type:** Structural, and it affects every number the solver has ever printed
**Priority:** High. Not urgent - nothing is broken today - but it silently bounds what the whole tool means.

## What made it visible

Adding photovoltaic panels as one more technique for making electricity.
The solver picks the cheapest technique for every material, so it picked
solar - and because electricity can be converted back into both heat and
shaft work, that choice cascaded through the entire energy market:

```
electrical_mj   0.00122  [electrical_mj_photovoltaic]
mechanical_mj   0.00201  [mechanical_mj_motor]                <- from electricity
thermal_mj      0.00125  [thermal_mj_electrical_resistance]   <- from electricity
```

Every energy carrier in a simulation whose scenario is Rome in 100 AD now
bottoms out in a silicon panel. Not because anything is broken: because the
solver was asked which technique is cheapest, and it answered correctly.

## The actual defect, which is older than the panels

**`sim/solve_prices.py` has no notion of WHEN.** It has always solved the
whole tree with every technique in it simultaneously available. Hall-Heroult
aluminium and bloomery iron sit in the same solve, and the bloomery only
survives because nobody had yet added a technique that undercut it
everywhere. Photovoltaic is the first entry cheap enough to win globally,
so it is the first one to make the absence obvious.

This means **every price this tool has printed is the price of that thing in
a world with all of human technology available**, not the price in the
scenario being simulated. The 14x iron gap, the mercury result, the
capital and rent measurements - all of them were computed under that
assumption without anyone stating it.

It does not invalidate the findings that were about RELATIVE structure - the
joint-production reversal in `Complaints/29`, the rent mechanism in
`Complaints/32` - because those compared things inside one solve. It does
bound any claim of the form "in Rome, X costs Y".

## Evidence the mechanism itself is right

Re-run with photovoltaic excluded - the counterfactual for a civilisation
that does not have it:

```
electrical_mj   0.00388 h/MJ   via the dynamo
mechanical_mj   0.00258 h/MJ   via the waterwheel
aluminium_kg    0.442 h/kg
```

Electricity costs about 50% more than shaft work, which is the dynamo's
losses plus its labour and capital - exactly what it should be, and exactly
what was predicted before the run. So the conversion graph is right and the
era problem is separate from it.

## What a fix looks like

The tree already knows what is available when: nodes have prerequisites, and
a civilisation has a set of technologies it has actually reached. The solver
ignores all of it. A technique should be admissible only when the node that
produces it is reached, and the solve should be parameterised by that set.

That is not a small change - it turns one global solve into a solve per
technological state - but it is the difference between "what does aluminium
cost" and "what does aluminium cost HERE, NOW", and the second is the only
question this project is actually asking.

## Do not fix it by deleting the panels

The obvious shortcut is to drop `electrical_mj_photovoltaic` and let the
Roman answer come back. That hides the defect instead of fixing it, and it
would leave the tool still claiming a Roman price while quietly using
Hall-Heroult and the compound steam engine. The panels are correct data.
The solver's silence about time is the bug.

## Also found, and cheap

Three entries carry a genuinely ELECTRICAL requirement as `mechanical_mj`,
the same mislabelling that started this: `zinc_electrolytic_kg` (Faraday's
law electrolysis), `tungsten_kg` (induction sintering), and
`calcium_carbide_kg` - whose own `yield_basis` says outright that "the arc
furnace must reach roughly 2000 C, well above anything a combustion furnace
reaches" while still charging the heat as shaft work. One field each.

## Follow-up: the three mislabelled entries are fixed

Done as a separate commit from the era problem, which stays open. One field
each moved from `mechanical_mj` to `electrical_mj`, plus the sentences in
each `yield_basis` that asserted the now-wrong reason - two of the three
argued explicitly that electricity *is* shaft work through a dynamo, so
appending a correction without deleting the old claim would have left the
reader two answers.

Measured, same solve before and after:

```
                       before      after     change
calcium_carbide_kg    0.15605    0.14607     -6.4%
germanium_g            16.302     15.229     -6.6%   (*)
indium_g               16.302     15.229     -6.6%   (*)
tungsten_kg           0.27352    0.27114     -0.9%
zinc_kg               0.32024    0.31943     -0.2%
```

All five fall, and they fall because `electrical_mj` (0.00122/MJ) is cheaper
than `mechanical_mj` (0.00201/MJ) in this solve: shaft work is now made FROM
electricity through a motor, so the old labelling charged an electrolysis
cell for a conversion it never performs. The sizes track energy intensity -
calcium carbide is 12,600 MJ per tonne and moves 6%, zinc's 10,500 MJ is a
small share of a cost dominated by ore and acid and moves 0.2%.

The numbers above come from the photovoltaic-rooted solve this complaint is
about, so read them as a ratio between two labellings, not as prices.

### The remaining `mechanical_mj` entries were checked and are correct

Three non-energy entries still carry one: `oxygen_m3` (a Linde-process
compressor), `barium_kg` (a vacuum pump on the aluminothermic reduction) and
`wire_drawn_kg` (a drawbench). Each is a genuine rotating shaft that a belt
from a waterwheel or a steam engine drives directly, with no electricity
anywhere in the chain - which is the test. That makes the set complete;
there is no fourth one waiting to be found.
