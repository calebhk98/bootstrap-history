# Mining labour per tonne was checked against sources; silver is still far below whole-workforce figures

**Status:** closed - folded into 349

The suspicion in 305 and 333 was that the deposit model charges too little labour per tonne of rock. Checked (`python3 sim/engine/solve_prices.py --civ rome_100ad --why silver_kg`, `python3 -m sim.tests --only mine_labour_per_tonne`):

- Hard-rock face breaking (20 h per tonne of rock) agrees with the Kongsberg fire-set drive, 37.5 man-days per fathom of a 6.5 by 5 foot drive, about 385 kg of rock per man-day (Timberlake 1990 quoting Collins 1883, as tabulated in Bettenay 2022, Metalla 26.2, Table 2). Pinned by a test.
- Deep hard workings (Hispania lead and silver, Rio Tinto copper, Dacian gold) now charge breaking, a hoist and drainage multiplier, and fire-setting wood, about 80 h per tonne of rock, about 100 kg of rock per eight-hour miner-shift. That sits inside Bettenay's 25-250 kg per miner per day all-in range for Melle (probably 50-150). So for those deposits the labour per tonne of rock is not the miss.
- What was missing and is now charged: wood for fire-setting hard rock, 0.6 t of rock per t of wood (Bettenay Table 1, Fournel mean) and 1-1.5 t of green wood delivered per forest worker-day (Bettenay). About 11 h per tonne of hard rock (`sim/world/mine_fire_setting.py`). Silver moved from about 319 to about 335 labour hours per kg.

What remains: whole-workforce figures are an order above the model. Bettenay's Table 3 gives 1.4 to 2.3 kg of silver per mine worker-year for medieval districts (about 1000-1700 hours per kg at 300 eight-hour days) and Strabo-Polybius gives about 3,700 hours per kg (305); the model gives about 335. Those include prospecting, shaft sinking, barren rock from sub-grade ore, timbering, ventilation, sorting and processing. Bettenay's own statement is that a large share of rock raised at faces was not viable ore and that processing took about as many people as mining. Candidates, each needing a source: 343 (dead work and the grade basis), 344 (unsourced shares and shift length).

A day's wage in Rome is still about 11 denarii against the attested one; the gold to silver ratio is about 40 (was about 42). Do not close the gap by tuning.
