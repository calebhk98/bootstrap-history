# Mining and precious metals: review of the model

Measured: `solve_prices.py --civ rome_100ad --why silver_kg` gives 378 h/kg, from `lead_kg` (per 1 t lead + 3.33 kg Ag). Silver carries 95% of the batch by demand-anchored value. Coin is 2.7 g silver (`coin_standard`), so money per hour follows silver's solved cost.

## 1. What the model gets right
- Mining is built from physics: breaking, hoist lift (energy), haulage, drainage, timbering, barren rock, fire-setting wood, shafts amortised over service life. No price enters (`deposits.py`, `mine_works.py`, `mine_fire_setting.py`).
- Labour per tonne is sane: about 80 h per tonne of hard deep ore is about 100 kg per shift, inside Bettenay's 25-250 kg band.
- Silver per lead is the right order. Wood 2022 puts argentiferous galena at about 0.2 wt% Ag, about 2.3 kg per t Pb. Laurion is about 2 kg per t Pb (search figure of 400 g/t Ag at 20% Pb, unverified). The model's 4.0 contained, 3.33 delivered, is 1.5 to 2 times high.
- Lead and silver are one joint process with cupellation; lead is 80,000 t/yr (matches Settle-Patterson via Wood). Gold has a hydraulic deposit with an aqueduct build cost. The patio route is era-gated.

## 2. Wrong or missing, ranked by effect on the silver price
1. **Price is set by flow cost, not by stock and demand.** The 3,700 h/kg "attested" figure is wage divided by coin silver (1 denarius a day, 2.7 g, so 370 days per kg). It is the same fact as Strabo's headcount division, not independent evidence. Patterson's stock is about 10,000 t against 200 t/yr of output, so output is about 2% of the stock. Price there reflects money demand, state ownership and rent. Production labour is only the floor. The solver gives silver its marginal-deposit cost, and coin is then pinned to that, so every nominal wage inherits the error. There is no stock, no velocity and no minting demand.
2. **The supply curve has no lean tail.** Four named silver deposits and five lead deposits, all with round grades (conf C/D), set the margin at about 120 h/kg (Laurion). Real output needed hundreds of small and poor workings (Domergue's catalogue). The marginal ore is much leaner than the named districts. `hispania_silver` at 1 kg/t is "conf B" from Strabo's headcount, not an assay. Ore grade is the largest single factor (349).
3. **Dressing and processing are heuristic and low.** Polybius, in Strabo 3.2.10, describes ore crushed, sieved, re-crushed and re-sieved five times, then smelted. The model charges 20 h per t of rock (conf D). Bettenay has processing staff about equal to mine staff. The direct silver recipe charges about a twentieth of that rate (333).
4. **Works left out:** adit drainage, stripping, lamp oil, supervision. Water inflow per tonne has no source (343, 349).
5. **Double count of silver supply.** The silver deposits (200 t/yr) and the lead byproduct (about 80,000 t × 3.3 kg, about 270 t/yr) are both counted against a 200 t/yr empire total (291).
6. **Jarosite route is absent.** Rio Tinto silver came from jarosite and gossan, which needs extra lead added as a flux (Anguilano et al. 2010, read). Rio Tinto is carried only as a deep hard copper deposit.
7. **Techniques are not physical.** `mining_tech` applies tree multipliers with defensive bounds (ceiling 3, floor 0.35); screw, wheel battery, adit and ruina montium do not enter the works formulas.
8. **Gold.** `gold_kg` is hand sluicing at an unsourced 0.3 g/m³, 13,000 h/kg. Las Médulas is 167 to 204 h/kg and Dacia about 11,400 h/kg in the deposit file, and neither feeds the price. The gold to silver ratio is about 40 (Rome attested about 12, cited not opened) (334).
9. **Minting and uptime.** The coin is a definitional mass of silver: no mint labour, fineness or seigniorage, no demand split (coin, plate, ornament). Mines have a fixed 150-year reserve and no closures, though Hirt describes whole periods of abandonment.

## 3. Sourced figures
Opened and read:
- Strabo 3.2.10 (Perseus). Polybius: 40,000 workmen at New Carthage, 25,000 drachmae a day to Rome, five crush-and-sieve cycles. The 25,000 is a state revenue, so it is a floor on output.
- Pliny NH 33.96-97 (Attalus). Baebelo gave Hannibal 300 lb of silver a day, driven 1.5 miles into the hill. NH 33.78: Asturia, Gallaecia and Lusitania gave 20,000 lb of gold a year (6.5 t).
- Wood 2022, Archaeometry. Argentiferous galena is about 0.2 wt% Ag. Roman lead is 80,000 t/yr after Settle and Patterson.
- Anguilano et al. 2010, ArcheoSciences 34. Jarosite smelting needs added lead. Plumbojarosite is 3 to 32% Pb. The 0.2% Ag figure for jarosite is from a search abstract, not the paper.
- Hirt (Warwick draft): qualitative only (abandonment periods, Kosmaj slag about 1 Mt).

Known only from search snippets or other agents' reading, to be confirmed before use:
- Bettenay 2022 Table 3 (1.4 to 2.3 kg Ag per worker-year, per Complaint 342).
- Patterson 1972: about 10,000 t Roman silver stock at the mid-2nd century.
- Laurion: 13 Mt ore at 20% Pb and 400 g/t Ag, giving 3,500 t Ag. About 20 t Ag/yr in the early 5th century. Attributed to Wood et al., not verified in the file I read.
- Las Médulas: Pliny's 6.5 t/yr, and a modern range from under 25 kg/yr to 1,600 t total, which is very uncertain.
- Han: silver was marginal, with bronze and gold as the standard monies.
- Not opened at all: Domergue, Conophagos, Hopper, Davies, Agricola text, Callataÿ, Kassianidou.

Cross-check only: a gold to silver ratio near 12 times the 13,000 h/kg gold route gives about 1,100 h/kg silver.

## 4. Fix list for the implementing agent
Do not tune a number to reach the attested wage.
1. **Stock-flow money.** Add a silver stock (opening about 10,000 t from Patterson, conf C) with losses, hoarding, plate and ornament. Silver's price is set by money demand over the stock, with production cost as the long-run floor. Anchor money per hour to a basket, not only to silver's solved cost. This is the largest change and needs a design note first.
2. **Mining-gated supply.** Mines open only where price is at or above cost plus rent. Build the supply curve from a per-district grade-tonnage distribution with a lean tail (Domergue's catalogue, slag assays).
3. **Per-deposit assay.** Replace district-wide silver per lead with a figure per deposit. Use 2 to 2.3 kg per t Pb for Laurion and Wood's 0.2% for galena. Split the 200 t/yr empire total once between lead-silver and silver-only deposits.
4. **Dressing.** Replace the 20 h/t rock heuristic with crush-sieve cycles from Polybius and Agricola VIII throughput, and make the direct silver recipe use the same rate.
5. **Missing works.** Add an adit alternative to screw or wheel lift, stripping, lamp oil, supervision; source water inflow first.
6. **Jarosite route.** Add a Rio Tinto jarosite recipe that consumes lead flux, with a sourced grade.
7. **Techniques as works.** Let a technique replace a `mine_works` term; drop the generic multipliers.
8. **Gold.** Make `gold_kg` draw from deposits. Add hydraulic and lode routes as techniques, with aqueduct build hours, and a limited ornament supply. Check the gold to silver ratio afterwards.
9. **Mint and uptime.** Add mint labour, fineness and seigniorage tied to the stock, and closure and reopening of workings.

## 5. Complaints closed per fix
284, 305: fixes 1, 2. 291: 2, 3. 333: 4, 5. 342: 2, 4, 5. 343: 5. 349: 2, 3, 4, 6. 334: 8 (and 9 for minting).
