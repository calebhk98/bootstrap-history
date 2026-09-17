# Capital was not the gap. Every price in this model is pure labour content, and that is the gap.

**Type:** Modelling, direction-setting
**Priority:** High for what gets built next. Nothing is broken.

## The claim this replaces

This project recorded, after `sim/solve_prices.py` first converged, that
`iron_bar_kg` came out about 14x below its book price and that the reason was
structural: `data/production/_SCHEMA.md` had **no field for fixed capital**, so
a blast furnace cost a process nothing. That was stated here as the diagnosis.
It was wrong, and it was wrong in a way worth keeping rather than quietly
overwriting, because it was a plausible reading that measurement refuted.

## What happened when the field was built

`capital` now exists, is validated, and is populated on 13 processes with
build materials and build labour in physical quantities this file already
prices. Amortising it - build cost divided by service life times annual
output - gives, computed directly off the committed data:

```
pig_iron_kg    prime cost 0.32922 h/kg    capital charge 0.005643   1.71% of cost
iron_bar_kg    prime cost 0.95153 h/kg    capital charge 0.002340   0.25%
glass_raw_kg   prime cost 0.09611 h/kg    capital charge 0.006151   6.40%
```

`iron_bar_kg` moves from 14.013x to about 13.98x. Glass, the biggest mover
because its pot furnace is relined every three years, goes from 277x to about
261x.

This is not a case of stingy estimates. The denominator is service life times
annual output, and for genuinely long-lived high-throughput plant that product
is in the millions of units. A blast furnace stack built for 16,220 labour-
hours and producing 400 tonnes a year for 40 years spreads its entire cost over
16 million kg of iron. Multiply every build estimate by five and the charge is
still a few percent. **Physical depreciation of pre-modern capital is a small
unit cost, and that is a real result rather than a data problem.**

## What the gap actually is

The solver fixes rent on extracted materials at zero (`RENT_IS_ZERO`), does not
price `energy_mj`, and does not read `capital`. Put those together and the
consequence is exact, not approximate: **every computed price in this model is
the total labour embodied in the good, valued at relative wages.** There is no
other claim on output anywhere in the system.

A pre-modern economy's prices are nothing like pure labour content, and the
disagreement table shows exactly where that bites. Measured over the 151
materials with a book price:

```
extracted, rent fixed at zero : n= 60  median disagreement   55.2x
produced, has a real recipe   : n= 91  median disagreement   19.2x
worst 25 disagreements        : 15 of 25 are extracted
```

The worst offenders are scarce minerals: cinnabar 20,571x, cryolite 18,519x,
agate 6,667x, graphite 5,556x, calcite 4,444x. Cinnabar at 0.035 h/kg says a
kilogram of the stuff is two minutes of digging. The model has no way to know
there were about three cinnabar deposits worth working in the Roman world,
because scarcity has no price in it at all.

And the zero propagates. A produced good's inputs bottom out in extracted ones,
so the produced side's 19.2x median is partly the same missing rent arriving
one step later. That is why fixing rent is worth more than any amount of
further capital data.

## What should come next, in order

1. **Rent on extracted materials.** The largest single term, and the one that
   makes a mine a finite thing rather than a tap. This is also what CLAUDE.md
   3.1 is really asking for: a gold deposit appearing in Rome should change
   prices, and it cannot while the rent on every deposit is zero.
2. **The cost of capital, which is not depreciation.** The expense of
   pre-modern plant was overwhelmingly the capital tied up in it - interest and
   opportunity cost in a world of thin credit and high default risk - plus the
   risk of a ruined campaign. Both sit in the "margin, risk" row
   `_SCHEMA.md` already lists as unmodelled. Note the size: a capital recovery
   factor at 10% over 40 years is about 0.102 a year against straight-line
   depreciation's 0.025, so carrying cost is roughly 4x wear even before risk.
   Four times one percent is still small, which is worth saying plainly - this
   is a correction, not the answer either.
3. **Energy.** Twelve materials are flagged UNDERPRICED today for want of it.

`capital` stays. It is correct, it is physical, and it will matter for choice
of technique - a water-powered hammer against a hand one is a capital-versus-
labour trade the model can now represent. It is simply not where the price
level is hiding.

## One thing to fix before the solver reads `capital`

`iron_bar_kg`'s own capital entry lists `iron_bar_kg` among its build
materials (800 kg of it, for the finery hearth and hammer), and `pig_iron_kg`'s
hearth lining lists 3,000 kg of `iron_bar_kg` while `iron_bar_kg` is made from
`pig_iron_kg`. Both are correct physics and both are cycles. They are harmless
while nothing reads the field. The moment the amortisation formula is wired
into `sim/solve_prices.py`, they meet the resolvability defect in
`Complaints/31`, which refuses every cycle - so 31 is now a prerequisite for
wiring capital in, not a someday item. It took under an hour from writing that
complaint for its predicted case to appear in real data.
