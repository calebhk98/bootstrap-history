# Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden

**Status:** partly - porter and dockworker trades exist, carriage books to them, and the economy's carriage table now offers only modes whose means are held and prices foot with porter crew; `economy-check --accounts --carriage` prints porter and dockworker hours demanded and hired; the whole-game measurement in "What is left" has not been run

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
