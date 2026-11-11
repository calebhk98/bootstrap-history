# Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden

**Status:** partly - porter and dockworker trades exist, carriage books to them, and the economy's carriage table now offers only modes whose means are held and prices foot with porter crew; `economy-check --accounts --carriage` prints porter and dockworker hours demanded and hired; the whole-game measurement is in "What is left": porters are not hired after year 1 because the merchants' worth of an hour stays under the porter wage; open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming). Depends on 609.

**What was wrong.** Land carriage on foot was a route mode whose hours were `labourer`, and port loading was a fixed
hours-per-tonne booked to the unskilled trade. In a society without draught animals (the Mexica) porters were among the
largest labour groups, so the labour market never saw the demand for them (see also 552).

**What is built.** `data/world/trades.json` has `porter` and `dockworker` trades (training 0: anyone can take them up at
once; no sourced fatality rate, so zero with the absence statement). `data/world/geography/route_modes/modes.json` gives
foot `crew_trade: porter` and sail `handling_trade: dockworker`. `routes_carriage` passes the trade,
`EconomySetup.carriage_handling_trade` carries it, and `Crew.hours_by_trade` (`sim/economy/carriage_hours.py`) books
handling to it. Every mode's crew is bid in its own trade (the heuristic `CARRIAGE_CREW_UNSKILLED_SHARE` is deleted). `occupation_groups.json` lists both in the transport group. Test:
`sim/tests/test_porters_and_dockworkers.py`.

**What is left.**

- Cause found and fixed in code (not yet measured in a game). The economy's carriage table was built from every mode the
  freight module could price (`Models.freight_mode_costs(cargo="goods")`, read by `sim/markets/port_setup.py` `opening_values`) with
  no check of the mode's `requires_nodes`, so a society without draught animals or ships still had cart, pack, river boat and
  sail in its table and its merchants bid carter and sailor hours for them; the labour core's need shares
  (`sim/labour/workforce_carriage.py`, usable modes only) never seeded those trades, so nothing was hired. And `foot` had no
  carrier model in `Models.build_carrier_models`, so it was never priced and never routed, so no porter hours were ever bid.
  Now `freight_mode_costs(cargo=...)` offers only the modes whose required nodes the society holds (`rules.usable_mode_costs`),
  and the porter mode is a freight carrier from its mode data (`sim/geography/porter_freight.py`, `geography.porter_carrier`),
  priced by its crew hours with no vehicle. Tests: `LandCarriageMeansTests` in `sim/tests/test_porters_and_dockworkers.py`,
  `test_foot_is_a_porter_carrier_...` in `test_land_map_carriage.py`, `test_goods_modes_leave_out_a_mode_whose_means_...` in
  `test_foreign_freight_wiring_rules.py`.
- Known limit: the mode set is fixed when the economy opens (`opening_values`), so a node a player learns later (a draught
  animal herd, the cart) does not add its mode to the economy's carriage table until a new opening; the freight module's
  own route searches do follow the nodes held. Domestic fallback hauls (`Haul.unjoined_haul`) still price `cart` whatever is held.

- Verify in a whole game that porter and dockworker hours are bid and hired: `python3 sim/simulator.py economy-check --accounts --carriage --years 5 --civs mexica_1500` (`sim/economy/carriage_report.py`); the porter row should show hired hours near the demanded ones. The `occupational_distribution` slow topic is now only a data lint (619).
- Measured on this commit (`python3 sim/simulator.py economy-check --accounts --carriage --years 5 --civs mexica_1500`, shipped
  openings): porter demanded 2212.5 / hired 1104.6 in year 1, demanded 1475 / hired 0 in year 2, no bid in year 3 (fallback fee
  421.46 paid to a household of the source tile), demanded 370.47 / hired 0 in year 4, none in year 5. Traced with a wrapper that
  printed each bid's maximum wage, the porter wage in the bid's area and the porter hours on offer (not committed):
  - Every porter bid is in one area (`work@honduras_02`). Its maximum wage (`carriage_money_wanted` over `carriage_hours_wanted`,
    `sim/economy/merchants_dispatch_kernel.py` `ask_crew`) was 2.0068 in year 1, 2.0134 in year 2, 1.934 in year 4, flat across years and
    identical for the three merchants, while the porter wage the market cleared at was 1.978 before year 1, then 2.080, 2.134 (and 2.42 in year 5).
  - Year 2 and 4: the maximum is under the wage, so `clearing.eligible_bids` drops the bid ("an employer whose maximum is under the wage
    wants none"). Hours on offer were not short (porter supply in the area, hours hired plus idle: 84692 in year 2 against 1475 demanded),
    so supply renewal is not the cause. The hours are booked to the account the clearing reads (`crew_hours_bought` is built from the
    clearing's own `hours_hired_by_market`).
  - Year 1 is half hired because the seeded porter workforce offers 1497.3 hours in that area against 2212.5 bid (hired 1104.6, supply
    left idle about 393); the seed is cut to the plan (`opening_placement.seeds_where_hired`) and the bid ceiling sat within 1.5 percent of the wage.
  - The cause is therefore the merchant's worth of an hour: gain (expected price at the destination less at the source, less the fee's
    non-crew part) per crew hour stays near the opening-wage fee, so it lies under a porter wage that the household reservation (the
    unskilled wage) lifts a few percent a year. A shipment that stops paying at the new wage is cut (`crew_cuts`), the plan then empties and the
    next year's shipments go out through the household-fee fallback. No code fix is made yet: the lever is how a merchant's expected
    prices follow the price level (they stay near the opening-wage spread while the wage moves), which belongs to the merchants'
    expectation rule, and a bid ceiling raised without it would hire hours the merchant's own prices cannot pay for.
- Re-examined for the bid-ceiling lever (no code change made; the diagnosis above is not confirmed). Read in code: merchants'
  expected prices do follow observed prices every year (`merchant_year.learn_year`, `MERCHANT_EXPECTATION_SPEED` closes a share of the
  gap to each year's cleared price), so "expectations stay at the opening level" is not what the rule does. What fixes a bid is
  `ask_crew` (`gain` = expected spread less the fee's non-crew part, shared by hours), stored as `carriage_money_wanted` at the
  year's dispatch and bid the next year (`carriage_hours.bid_figures`): a bid is the worth of an hour at last year's expectations
  and last year's wage. Where the spread of a route sits at its fee (arbitrage leaves little more), a wage that has risen since
  the plan was made puts the bid under the wage whatever the speed of learning, and the fee's crew part is already re-priced each
  year (`carriage_hours.wage_scale`), but as one multiplier from the carried-flow mean wage, so an area whose porter wage is
  above that mean has a fee per crew hour under its wage while the bid, being the spread over hours, ignores the fee there.
  Not reproduced on this commit: `python3 sim/simulator.py economy-check --accounts --carriage --years 4 --civs mexica_1500`
  (shipped openings current, numba installed) shows porter demanded 5.5e-08 in year 1, no bid in year 2, 1.33e8 in year 3 (hired 100.59)
  and 1.25e8 in year 4 (hired 118.35), with porter wages by area from 0.02 to 68 in a trace of the dispatch tables, so the
  one-area picture above (honduras_02, wage near 2) no longer holds and the commits since the measurement (the 977 pool-stock
  series) change the trade volumes. Re-measure before choosing a fix; a design that follows from the code reading is to re-price a
  plan's bid at bid time from the current fee and wage (the plan would then need the per-route spread and hours, not their sums).
- `sea_freight.PORT_HANDLING_HOURS_PER_TONNE` (read in `sim/markets/port_setup.py`, `sim/freight/models.py`) stays a labelled heuristic: no source found (a port-economics page gives a longshore crew
  5 to 10 tons an hour but not the crew size, so no per-worker figure follows).
- The sea handling money (`handling_rates`, `sim/markets/port_setup.py`) is still priced at the unskilled wage; porter and dockworker wages come from the
  labour market, not from it.

**Research needed.** Hours of porter and longshore labour per tonne (Roman Ostia and Portus portage, tlamemeh loads and
daily distances from a primary or monograph source, such as Hassig, Aztec Warfare and Trade and Conquest, which has not been opened).
The foot mode's 27 kg and 22 km a day sit near Wikipedia "Tlamemeh" (23 kg, 21 to 25 km a day; secondary).

**Research pass (source-porter-hours).** No figure was replaced; no opened source supports a better one.
Opened: Law and Rodway, Himalayan Journal 64 (2008), "Lowland porters in the Solu Khumbu" (Nepal; commercial porters carry far
above body weight, "a 24 year old man who weighed 52 kg carrying a 90 kg load from Jiri to Kakou, a six-day walk"; no km a day,
so no daily distance follows; Nepal is a different society and a paid-by-weight market, not a Mexica relay).
Wikipedia "Tlamemeh" re-opened: quotes "carrying on average 23 kilos" and "daily commute of 21 to 25 kilometers", with no
inline citation and no Hassig page. Not opened (503/403): Bastien et al. 2005 (Science), Malville 1999 (only seen as quoted in
search summaries), the Karwansaray blog quoting Hassig pp. 32-33 for a load and a five-league stage. Port hours per tonne:
searches for Ostia and Portus saccarii and early-modern stevedoring found no per-worker rate; the one opened-in-summary source
gives pay per ton, not hours. Still open: open Hassig (Aztec Warfare 1988, pp. 32-35) in print, Bastien 2005 full text, and a
port-history rate for tons per gang-day with the gang size.

## The porter picture moves with the opening (orchestrator, 2026-11)

`python3 sim/simulator.py economy-check --accounts --carriage --years 3 --civs mexica_1500` on a cold full spin-up at three commits gives
three different pictures: at 09fcea68 (where the bid-ceiling trace above was made on that day's shipped openings) porter demand is
under 1e-6 hours every year; at 1ffc8ef8 demand is about 1e8 hours with about 1 percent hired; at e69ab838 on the rebuilt openings,
year 1 demands under 1e-7, year 2 pays a large household fallback fee, and years 3 to 5 demand about 1.3e8 with about a hundred hired.
So there is no single commit to bisect: the merchants' porter plan swings between nothing and a large demand the labour market barely
fills, depending on the opening draw (473, the spin-up does not settle). Open on the current openings: why a large porter demand finds
almost no hire when porter wages sit near the opening wage.
