# Silver still costs about a tenth of the labour its attested wage implies

**Status:** closed - the same gap as 349, which carries the remaining work; the Strabo-Polybius cross-check is kept there

After costing ore dressing, roasting, cupellation bellows and hearth attendance, assay-weighted silver per lead and the silver recoveries (143, 288, 337), Rome's solved silver is about 320 labour hours per kg (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`). One denarius (2.7 g) is then below one labour hour and the opening unskilled wage is more than one denarius per hour, so a ten-hour day pays about a dozen denarii against the attested one denarius a day.

An independent cross-check that is not a price: Strabo (3.2.10, citing Polybius) gives about 40,000 workers at the New Carthage mines and about 25,000 drachmae a day to Rome. At about 4.3 g of silver per drachma that is about 107 kg a day over 40,000 worker-days, about 370 worker-days (about 3,700 hours at ten a day) per kg. That is the same order as one denarius per ten-hour day, and about twelve times the solved cost. Polybius's figure is state revenue, so the output was at least that, and not every worker was a miner; both push the true labour per kg somewhat lower, not by a factor of twelve.

## What the physics still says

At the deposits' own grades the work per kg of silver is small: Hispania's rock is 1 kg of silver per tonne, and hard deep rock costs about 70 hours per tonne in `sim/world/deposits.py`, so the rock alone is about 70 hours per kg. Reaching 3,700 hours per kg needs either a far leaner grade or most of the 40,000 doing work the model does not charge. None of that is tuned away here.

## Where the remaining gap may lie (candidates, each needs a source before any number moves)

- Grade. `hispania_silver` is 1 kg of silver per tonne of rock (conf B, but the source is Strabo's headcount, not an assay). Assayed ores of the Iberian pyrite belt and the Linares-Carthago district are usually reported far leaner; a grade ten times lower multiplies the rock, dressing and haulage per kg tenfold. This is the most likely single cause, and the grade should be checked against slag-heap and ore assays.
- Drainage and ventilation. They are folded into `HAULAGE_MULTIPLIER_DEEP_VEIN` with no derivation; a derivation from water inflow per tonne of rock and the lift head (a wheel battery of several dozen treaders per shaft is attested) would show whether 3.5 is nearly right or several times too low.
- Rent and ownership. The solver prices the marginal deposit's cost plus a Ricardian margin, but not a mine owner's or concessionaire's claim, the imperial monopoly on the richest mines, or the state's tax (roughly the Polybius figure itself). Those make silver cost more to a buyer than its production labour.
- Slave versus wage labour. Mining labour in these districts was mostly unfree, costing subsistence rather than the free wage, which makes the labour-hour cost of silver lower, not higher, so this does not close the gap.
- Joint-cost split. The lead and silver batch is split by demand-anchored value share, so silver carries about 96 percent of the batch. A physical split has no basis (the two are one process), and the batch itself is the number to raise, so this is an accounting choice, not a source of the gap.
- Cupel, furnace and dressing work. Hearth throughput, bellows rates and the dressing rate are conf D heuristics; each could be off by a factor of a few, which is not a factor of twelve.

## What it would take

Source the Iberian ore assays and check the grade first; then derive drainage per tonne of rock from inflow and head; then a mine-ownership and state-take mechanism (an actor's claim on a deposit) belongs to the state and market work, not to the recipes. Do not move any of the heuristic rates to hit the day wage (CLAUDE.md 4.1).

## Update (silver-and-gold-cost)

Grade was checked first and is not the lever: Laurion lead is reported at about 2 kg of silver per tonne of lead and Rio Tinto jarosite ore at about 0.2 percent silver (Wood et al., Internet Archaeology 56), the same order as the recipe's roughly 3 kg per tonne of lead. Rome's silver is still about 319 labour hours per kg (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`), unchanged; about 120 of it is the galena the deposits' supply curve prices, about 60 charcoal, the rest furnace and dressing labour. What is still not costed is filed as 333.

## Update (mine-labour-per-tonne)

Labour per tonne of rock checked against Kongsberg and Melle figures and fire-setting wood added to hard rock; silver moved from about 319 to about 335 hours per kg and the gap remains. See 342, 343, 344.
