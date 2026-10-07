# Freight remains: rivers, domestic dues, droving, flow ledger (Complaint 326)

Branch `freight-remains-research`. Research only; no code or data changed. Tags: `read` (page opened this session and the figure seen), `snippet` (seen in a search result summary only, page not opened), `recalled` (from memory, not checked, verify before authoring), `repo` (read from this repository). Confidence letters follow `data/production/_SCHEMA.md`. Per CLAUDE.md 4.5 no freight rate below is an input: rates fall out of physical inputs, and the sourced rates are validation relations in tests.

## 0. What the repository already has (found by reading)

- `freight_money_per_tonne_km` (`sim/geography/freight_cost.py`) already prices running cost, carrier capital, losses and a return-leg factor from an `imbalance` argument. `imbalance_of_flows(tonnes_out, tonnes_in)` exists and assumes fully one-sided when nothing is known to flow back. The ledger below is what supplies those tonnes.
- The complaint text says the map has no river legs. That is out of date. `sim/geography/routes_graph.py` builds `river` edges between bordering tiles that both carry at least `route_river_navigable_km_threshold` of the layer `river_km_navigable`, or share a `river_id`. The layer `river_km_navigable` (Natural Earth rivers and canals of scalerank 6 or lower, length inside the tile) exists; no `river_id` layer and no `river_current_km_per_hour` layer exist in `data/world/geography/layers/`. The current's sign comes from the tile elevation difference and its size from a typical-current constant. So what is open is not "no place for rivers" but: which tile pairs lie on the same river (two bordering tiles may hold two different rivers), how fast the water runs, which reaches were navigable in the scenario's era, and seasons.
- Dues: `dues_hours_per_tonne` per mode in `data/world/geography/route_modes/modes.json`, a labelled heuristic (conf D), charged when a haul changes to a mode, currently only on foreign legs (`sim/engine/foreign_routes.py`).
- Living stock: `Complaints/reports/living-stock-research.md` proposes per-species `intake_fraction_per_day`, `adult_mass_kg` and an `annual_loss` fraction in `living_stock.json`; droving should read those, not duplicate them.

## 1. River transport

### 1.1 Figures

| Figure | Value | Source | Tag | Conf | Target |
|---|---|---|---|---|---|
| Diocletian Edict, wheat, cost per kg per km: sea | 0.00067 denarii (mean of 55 sea routes) | Scheidel 2014, JRA 27, https://www.cambridge.org/core/journals/journal-of-roman-archaeology/article/shape-of-the-roman-world-modelling-imperial-connectivity/E61006878912791FDEE7CFAD95530770 | read | C | validation test only |
| same: river downstream | 0.0034 (1 denarius per modius for 20 miles) | same | read | C | validation test |
| same: river upstream | 0.0068 (2 denarii per modius for 20 miles) | same | read | C | validation test |
| same: wagon | 0.035 | same | read | C | validation test |
| Ratios to sea from those rows | river down about 5, river up about 10, wagon about 52 | same, derived | read | C | `sim/tests` relation: sea < river down < river up < road |
| Duncan-Jones reading of the same edict (Alexandria to Rome reference) | sea 4 times cheaper than river down, 8 times cheaper than river up, 34 times cheaper than donkeys, 42 times cheaper than wagons | search summary, https://intarch.ac.uk/journal/issue36/5/5-4.html | snippet | C | shows the ratios are disputed; tests use a range, not a point |
| Upstream to downstream price ratio | 2 (Edict, as read above) | Scheidel 2014 | read | C | output of `river_boat` upstream and downstream paces, tested |
| Yangtze delta 1680s, grams of silver per ton-mile: water, land | water 0.125, land 1.254 (England: 0.464 and 4.965); water to land about 1 to 10 in both | Cheng, LSE Economic History WP 371 (2024), https://www.lse.ac.uk/asset-library/information/wp371.pdf, opened as text | read | B | validation relation: water to land about an order of magnitude |
| Yangtze delta canals and minor rivers | up to 55 km per day; major river with tailwind up to 65 km per day even upstream | same | read | C | `river_boat` pace by reach class |
| Creeks in hill country | downstream up to 80 km per day, upstream about 28 km per day | same | read | C | current-dependent pace relation |
| Packhorses on land, same paper | about 45 km per day flat, about 30 km per day hilly | same | read | C | check the `pack` pace |
| England about 1700: river against road | river about a tenth of the road cost per ton-mile on a naturally navigable river | search summary of Bogart's survey, https://sites.socsci.uci.edu/~dbogart/transport_revolution_surveyjan2013.pdf | snippet | C | validation relation |
| Rhone and Tiber upstream haulage | barges hauled upstream by gangs of men (medieval Rhone records: about 1.5 tonnes pulled per hauler); on the Tiber by oxen or men on towpaths (`naves codicariae`); sailing up the Tiber unreliable (strong current, meanders) | https://ostia-antica.org/introduction/rome-transport-tiber.htm ; https://en.wikipedia.org/wiki/Chain_boat_navigation | snippet | C | towing inputs of the `river_boat` upstream mode |
| Nile: current carries boats north, prevailing north wind carries sailing boats south | both directions cheap, no towing | search summaries of Egyptian sources | snippet | B | wind assist on a reach (see 1.3) |
| Mexica lake canoes carry several tonnes; a porter (tameme) carries about 23 kg and walks 21 to 28 km a day | | https://www.infobae.com/en/2022/04/24/mexico-tenochtitlan-what-were-the-means-of-transport-used-by-the-mexicas ; search summaries | snippet | D | a `river_boat` variant on lake edges with no current; the repo's `foot` row is consistent |

Not found this session (all `recalled`, to source before any data row is written): the navigable extent of each named river in each scenario era (Rhone up to Lyon and beyond by haulers; Rhine to Basel; the Danube as a frontier river; the Po and its canals; the Tiber from the sea to Rome and a little above; the Nile to the first cataract; the Guadalquivir to Seville and Cordoba; the Yellow River with its shifting, silting bed; the Yangtze; the Grand Canal with its summit-level and lock problems; the Thames to Oxford, the Severn above Shrewsbury, the Trent; the Rhine and Baltic rivers with portages for the Norse; the Mexica lake and canal system). Anchors to read: Pliny and Strabo on river reaches (Roman); Wilson and Bekker-Nielsen on rivers in the Roman economy (the AIAC 2018 panel, https://www.propylaeum.de/themen/aiac2018/sektion-5/panel-20, snippet); Willan on English river navigation; Needham, Science and Civilisation in China vol. 4 part 3; Hassig on Mexica transport. No seasonal figure (low water, ice, flood, monsoon wind) was found for any river.

### 1.2 Can navigability be derived from a river dataset?

Partly, with labelled thresholds. The open dataset is HydroRIVERS (HydroSHEDS): https://www.hydrosheds.org/products/hydrorivers and its technical document https://data.hydrosheds.org/file/technical-documentation/HydroRIVERS_TechDoc_v10.pdf (the PDF would not render as text this session, so the description below is from search summaries and memory). Seen in summaries (snippet): a global line network of reaches with catchment of at least 10 km2 or flow of at least 0.1 m3 per second, 8.5 million reaches averaging 4.2 km, each with length, distance to headwater and to outlet, stream order, long-term average discharge, and up and down connectivity. Recalled field names to verify: `HYRIV_ID`, `NEXT_DOWN`, `MAIN_RIV`, `LENGTH_KM`, `DIST_DN_KM`, `DIST_UP_KM`, `CATCH_SKM`, `UPLAND_SKM`, `DIS_AV_CMS`, `ORD_STRA`. It has no slope field; slope comes from the elevation along the reach (distance to outlet gives a profile against `elevation_mean_m` or a DEM), or from the companion RiverATLAS attributes (recalled: a stream gradient field). Licence: recalled as free including commercial use with attribution; verify before committing any derived data.

Derivation, all labelled `temporary_heuristic` until validated against known reaches:

- Per reach: average discharge and slope give channel depth and current by hydraulic geometry (depth and width grow as small powers of discharge; current from slope and depth). The draught of the era's hull (a repo carrier input) against depth gives navigable or not; the current gives upstream and downstream pace and whether towing is needed. This is physics from discharge and slope, so no per-river authoring is needed for the default.
- Modern discharge is regulated and beds have moved (Yellow River, Po delta, Nile before the dams), and the dataset has no seasonality. So keep one authored correction: per reach and era, an override listing reaches known open or closed, each with a source and tag. The derived layer is the default; the override is the only authored part.
- Swappable by one option: a map parameter `river_source` with values `natural_earth_tiles` (today: the `river_km_navigable` tile layer) and `hydrorivers` (a reach table reduced to the same outputs). Both produce the same tile layers and edge attributes: `river_km_navigable`, `river_id`, `river_current_km_per_hour`, plus per-edge `draught_m` and `towpath`. `routes_graph.py` must not know which source made them. A mod overlay can supply the same layers by hand.
- Resolution caveat: tiles are coarse cells, so a tile holds many reaches; the layer is the main-stem length, and an edge joins adjacent tiles sharing a `river_id`.

### 1.3 Data design (rivers)

- Derived from geography: navigable length per tile, `river_id` (from `MAIN_RIV` grouping), current (from slope), draught limit (from discharge), upstream and downstream pace, towpath need.
- Authored, small, sourced and era-tagged: reach overrides; portages (the Norse carries between river systems: an edge of mode `foot` or `pack` tagged `portage`, so the router sees a handling change); wind assist (from a prevailing-wind layer if one exists, not a per-river flag); seasons as per-reach `open_months`, defaulting to the whole year, scaling annual working days in `freight_cost` (`LAND_WORKING_DAYS_PER_YEAR` has no river counterpart yet).
- Upstream against downstream: current is a signed speed on the edge (already `Edge.current_km_per_hour`). Downstream pace is boat speed plus current; upstream is boat speed minus current when sailing is impossible, and below a floor the boat is towed, with haulers' hours and feed as physical inputs (the Rhone figure gives pull per hauler). The Edict ratio of two between up and down is then an output to test, not an input.
- Canals (Grand Canal, Po canals, Mexica canals): an improvement like the road (`needs_improvement`), with zero current and a lock or summit-level delay per lock; the Grand Canal is a built improvement, not a river.

## 2. Domestic dues

### 2.1 Figures

| Figure | Value | Source | Tag | Conf | Target |
|---|---|---|---|---|---|
| Rhine tolls levied per ship, scaled with vessel size; average ship in 1241 about 8 denari | per vessel, not per value | Tolling the Rhine in 1254, https://www.medievalists.net/2012/12/tolling-the-rhine-in-1254-complementary-monopoly-revisited/ | read | B | `dues_basis: per_vehicle` on `river_boat` |
| Rhine stations: 12 between Mainz and Cologne in 1250; 79 locations on the Rhine and tributaries over the years 800 to 1800; minimum spacing about 5 km | | same | read | B | `dues_stations_per_100km` as a polity trait, tested as an outcome |
| In-kind Rhine tolls (lead, copper, wine, slaves), heavier than the money toll | | same | read | C | the ledger records goods paid as dues |
| Severn, 17th and 18th century: upstream a penny, downstream threepence per ton; towns charged for passing under their bridges | per tonne, direction dependent | https://tewkesburyhistory.org/River-Trade-On-The-Severn-1565-1765 | snippet | C | `dues_basis: per_tonne` with a value per direction |
| Likin (China from 1853): internal transit duty on goods passing between districts, ad valorem, 2 to 10 percent, levied at stations | per value | https://en.wikipedia.org/wiki/Likin_(taxation) | snippet | C | `dues_basis: ad_valorem` |
| Roman portoria: customs at provincial boundaries, about a fortieth of value; local tolls at bridges and city gates | per value | recalled (already cited in `modes.json`) | recalled | C | civilisation `state_revenue` data, not mode dues |
| Octroi (city gate dues on food and wine); Chinese customs barriers on the Grand Canal; Japanese barrier dues | per load or per value by good | not searched | recalled | D | `per_vehicle` or `ad_valorem` at a settlement boundary |
| Turnpike tolls in England per vehicle and per head of cattle; drove roads ran parallel to avoid them | per animal and per vehicle | https://www.rh7.org/factshts/drovers.pdf | snippet | C | droving mode: a per-head charge, no vehicle toll |

### 2.2 Data design (dues)

Three bases occur in the record, so one hours-per-tonne field is not enough once domestic dues are charged:

- `per_tonne` (hours of unskilled labour per tonne, what exists): keep for bridge, gate and quay dues.
- `per_vehicle` (Rhine: per ship; turnpike: per cart): hours or money per carrier unit, divided by the carrier's cargo tonnes in `freight_cost`, so a larger hull pays less per tonne with no further rule.
- `ad_valorem` (portoria, likin, octroi): a share of the cargo's value at the point of levy. Value is a price computed by the solver at run time, so the rate lives on the levying polity, not the mode.

Each mode row keeps `dues_hours_per_tonne` and gains `dues_basis`, `dues_by_direction` (upstream, downstream) and `dues_stations_per_100km`, each with `dues_conf` and `dues_source`. A civilisation file states an `internal_customs` block: the ad valorem share, station spacing, the receiving actor. The levier is the owner of the tile or edge where the haul is charged (tile holdings already exist in `tile_holdings.py`), so a haul across three lords pays three stations, as on the Rhine; likin compounding then needs no special case. The payee is recorded in the ledger (section 4), so the revenue reaches the right state or interest group through the existing revenue path, with no bespoke branch (CLAUDE.md 4.3, 4.7). One option, `domestic_dues`, turns domestic dues on; default off until the ledger exists. Foreign legs keep today's heuristic as a fallback; a sourced rate replaces it row by row.

## 3. Droving of live animals

### 3.1 Figures

| Figure | Value | Source | Tag | Conf | Target |
|---|---|---|---|---|---|
| Cattle, distance per day | 10 to 15 miles; elsewhere about 2 miles an hour covering 15 to 20 miles; Welsh drives 12 to 14 miles | https://en.wikipedia.org/wiki/Droving ; https://www.rh7.org/factshts/drovers.pdf | snippet | C | `km_per_day` per species on the drove mode |
| Pace was limited because faster cattle lose weight | | same | snippet | C | the weight-loss relation |
| Sheep, Wales to London: 20 to 25 days, flocks of 1,500 to 2,000, weight loss under 4 percent | | https://en.wikipedia.org/wiki/Droving | snippet | C | `weight_loss_fraction_per_day` for sheep, derived from the total |
| Turkeys: over 250,000 a year walked to London by 1750 from Norfolk and Suffolk, flocks of 100 to 1,000, a few miles a day, feet tarred | | https://queenofmarkets.substack.com/p/lets-talk-turkey | snippet | D | poultry `km_per_day` |
| Geese fitted with boots, cattle with iron shoes (cues) on hard roads | | search summaries (Hampshire and Herefordshire droving pages) | snippet | D | shoeing as a drove input (iron, labour) |
| Drove roads 40 to 50 feet wide, often hedged; ran beside turnpikes to avoid tolls; grazing and overnight stances were paid for | | https://commonculture.org.uk/wp-content/uploads/2018/01/Drove-Roads-Story.pdf | snippet | C | a drove edge over unenclosed grazing land |
| Grazers' intake 2 to 3 percent of live weight a day | | `Complaints/reports/living-stock-research.md` (AHDB, FAO) | repo | C | read from `living_stock.json` `intake_fraction_per_day` |
| Pigs: pace, weight loss, mortality | not found; pigs drive poorly and were fattened near the destination | | not found | to set | pig row |
| Mortality on the road for any species | not found | | not found | to set | `mortality_per_day` |

### 3.2 Data design (droving)

Droving is a carriage mode in which the cargo is the carrier. New row in `modes.json`: `drove`, `edge_classes: [land]`, `model: drove`, no required node (any actor can walk animals), `max_grade` by species, no `needs_improvement`. Its physical inputs come per species from `living_stock.json`, not typed on the mode: `km_per_day`, `weight_loss_fraction_per_day`, `mortality_per_day`, `intake_fraction_per_day`, `drover_hours_per_head_day`, and `shod` (an iron and labour input). The mode applies only to goods flagged live stock. Its alternative is slaughter at origin and carriage as carcass or preserved meat, so the choice falls out of price, not a rule.

What a drove costs per tonne of live weight and per km: drover wages over the days, feed drawn on the way (grazed from the pasture pool of tiles passed, `usable_forage_kg`, or bought where the route is arable, so a drove competes with local herds and a drove road is simply uncultivated pasture), grazing and stance fees paid to the tile's holder, shoeing, and the expected loss in weight and head. There is no carrier capital and no empty vehicle return (the drovers walk home, which costs their hours only). A delivered batch has lower mean weight and fewer head, and its market value comes from the delivered state, so the pace limit emerges: faster means more loss. A sibling to `freight_money_per_tonne_km` in a new small module (`sim/geography/droving_cost.py`) returns the same shape so `routes_rates.py` can pick the cheaper mode. Dues: a per-head charge, `dues_basis: per_head`, zero by default.

## 4. A domestic flow ledger

### 4.1 What it records

One row per shipment-leg per period: `period`, `sender` and `receiver` (actor ids: household, firm, state, interest group), `good`, `tonnes` (and `head` for live animals), `origin_tile`, `destination_tile`, the leg `{from, to, mode, km}`, `carrier` (the actor that owns and operates the carrier, possibly the sender), `freight_paid` (to the carrier), `dues_paid` (list of `{payee, amount, basis}`), `goods_paid_in_kind`. Rows are aggregated by origin, destination, mode and good per period, never per cart, so the ledger stays small.

Where it comes from: the route search already returns legs with km and mode (`route`, `route_costs`), and trade clearing already decides who sells to whom. The ledger is written at clearing from those two outputs. Per CLAUDE.md 4.6 nothing is migrated; the field is saved with the game and the save detection picks it up.

### 4.2 Feeding the carriers

`Complaints/reports/transport-and-building-demand-research.md` section 4.2 proposes freight service goods whose recipes consume crew hours per tonne-km. The ledger is the demand side: tonnes times leg km by mode over a period gives tonne-km per mode, which converts to hours of carter, bargeman, sailor and drover trades, and to feed, wear and carrier replacement through the physical inputs already in `freight_cost.py`. It replaces that report's temporary mean-haul heuristic with measured flows (its open question 2). Further uses of the same rows:

- Return legs: per directed edge pair and mode, `imbalance_of_flows(tonnes_out, tonnes_in)` computed from the ledger replaces the pessimistic default for domestic hauls. A cart returns empty only if nothing travels back on that edge by that mode.
- Backhaul as a choice: a carrier accepting a return cargo at a lower rate makes price depend on the opposing flow; this arrives with the carrier market, not with the ledger.
- Dues revenue: `dues_paid` summed by payee gives each state or lord its toll income, a plausibility check against its revenue data.

Pricing reads the previous period's ledger, which avoids a circular solve; the one-period lag is a labelled heuristic.

## 5. Staged build plan

Tests are written first (CLAUDE.md section 6). Another agent owns `sim/geography` and `data/world/geography` at the time of writing; stages 1 and 2 wait for that to merge.

Stage 0 (data only, no behaviour change): source the `recalled` and `snippet` rows (reaches by era, Rhine and likin rates, drove pace, loss and mortality by species) until each reads `read`. Test: `python3 sim/simulator.py validate` passes.

Stage 1: river identity and current. Add `river_id` and `river_current_km_per_hour` behind `river_source`; first Natural Earth with grouping by name, then HydroRIVERS as the second source.
- Two tiles joined by a river edge share a `river_id`.
- Downstream pace exceeds upstream pace on every river edge.
- A river leg is cheaper per tonne-km than a road leg over the same distance in the same era.
- The water to land cost ratio lies within an order of magnitude of ten (Cheng 2024, Edict).
- Changing `river_source` leaves the router interface and output shape unchanged.

Stage 2: towing and seasons.
- Upstream towed cost is at least the downstream cost.
- A reach closed for part of the year raises annual cost per tonne-km through fewer working days.
- A reach with no current has the same cost up and down.

Stage 3: domestic dues. Add `dues_basis`, direction and stations to the mode rows, polity `internal_customs`, the `domestic_dues` option.
- With the option off, domestic cost and the fingerprint are unchanged.
- A haul across more stations pays more.
- A per-vehicle toll falls per tonne as cargo per hull rises.
- An ad valorem duty scales with value.
- Total dues paid equals total dues received by payees.

Stage 4: flow ledger, in a package behind its `api.py`, written at trade clearing and saved with the game.
- Tonnes sent equal tonnes received per row, less stated losses.
- Tonne-km per mode equals the sum over rows.
- Save and load round-trips it.
- Imbalance from the ledger equals `imbalance_of_flows` on the same tonnes.

Stage 5: carrier demand from the ledger (joins the transport report's Stage 3).
- A coastal civilisation with traded bulk goods shows sailor hours from the ledger; an inland one without a navigable river shows none.
- Doubling a flow doubles the hours.

Stage 6: droving. The `drove` row, `droving_cost.py`, species inputs from `living_stock.json`.
- A longer drove delivers lower weight and fewer head, and a faster pace raises the loss.
- Droving beats carcass carriage over short distances and loses over long ones (a crossover relation, the distance not typed).
- A drove pays no vehicle toll but a per-head grazing charge.
- A drove draws feed from tile forage along its route and lowers local stock.

## 6. Open questions

1. Grain of the river layer: tiles are coarse, so a navigable reach shorter than a tile is invisible. Should rivers become authored edges between tile pairs, or stay derived from tile layers with a `river_id`?
2. Era: HydroRIVERS discharge is modern and regulated, and the Yellow River, Po and Nile have moved. Is a per-scenario override list the acceptable single authored part?
3. Seasonality: no source found for any river. Is a flat open fraction per climate class acceptable as a labelled heuristic?
4. Ad valorem dues need a price at the levy point. Does the solver expose a price per tile per good, or does the ledger value cargo at the origin price?
5. Which package owns the ledger: economy, labour or geography? It crosses the walls in `docs/architecture/PACKAGE_WALLS.md`; its surface should be an `api.py` call.
6. Droving loss and mortality for pigs, geese and cattle are unsourced for the Roman, Han and Mexica scenarios; the English record is post-medieval. Is it acceptable as a stand-in at confidence D?
7. Do tolls in kind belong in stage 3, or only money dues?
8. Is the heuristic `dues_hours_per_tonne` kept as a floor under sourced bases, or does each sourced row replace it fully?
