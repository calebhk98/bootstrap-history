# Freight omits travel time, empty returns and the carriers' capital

**Status:** closed - freight from the carrier is one function (`freight_money_per_tonne_km` in `sim/geography/freight_cost.py`) for foreign legs and domestic hauls: travel days, the empty return (by the share the opposite flow fills, from the domestic flow ledger), the carrier's capital, hulls lost at sea, and tolls and port dues stated per mode in `data/world/geography/route_modes/modes.json` (`dues_hours_per_tonne`), paid by foreign legs and domestic hauls alike; rivers are edges between tiles derived from the tile layers; live animals walk to market by a droving mode (tests: freight_dues, freight_domestic_haul)

Route freight (`sim/engine/foreign_routes.py`) priced feed, crew rations and
hours per tonne-km and a port handling charge per sea leg. It left out: goods
tied up on a voyage that lasts months (interest, spoilage), the empty return of
a cart or hull, the price of the carrier itself and its wear, tolls and port
dues, and the sailing seasons.

## What closed it

- **Dues on domestic hauls.** `DomesticHaulMixin` (`sim/engine/domestic_haul.py`)
  prices a domestic haul with `leg_money_per_tonne`, the same function a foreign
  leg's rate goes through, plus the mode's `dues_hours_per_tonne` at the carriers'
  wage, once per haul. No per-tonne tariff could be sourced, so the figure stays a
  labelled heuristic (confidence D) in the mode data. Search of the sources found
  that medieval river tolls were levied per vessel (the standard 1241 Rhine toll
  for an average ship was a fixed sum, larger ships paying more) or in kind on
  named cargoes, and the Roman portoria were ad valorem customs, which the
  civilisation's own import and export duty already covers; neither gives
  hours per tonne. Sources: Medievalists.net, "Tolling the Rhine in 1254:
  Complementary Monopoly Revisited" (https://www.medievalists.net/2012/12/tolling-the-rhine-in-1254-complementary-monopoly-revisited/);
  the Viabundus toll project (https://www.landesgeschichte.uni-goettingen.de/roads/viabundus/).
- **Rivers.** The map no longer lies in regions: `sim/geography/routes_graph.py`
  derives a river edge between each pair of bordering tiles that both carry
  navigable river length (`river_km_navigable`, Natural Earth) or share a river
  id, with the current's direction from the tiles' heights, and `river_boat`,
  `steam_ship` and `canal` route along them; a land edge between tiles on one
  river is a crossing. No authored river reaches are needed; test
  freight_domestic_haul reads the edges off the real map and hauls along one.
- **Domestic flow ledger.** `sim/geography/flow_ledger.py` is a plain-dict ledger
  of tonnes carried from tile to tile. The economy's merchants record what they
  carried each year (`EconomyRecord.carried`, saved with the record); the
  carriage table is built at the share of return trips the opposite flows leave
  empty (`EconomySetup.carriage_rates_at`, exact because a carrier's cost is
  linear in that share), rebuilt when the stepped share changes. The engine's
  domestic material hauls read the same ledger from the stored record. An
  empty ledger means the cart returns empty, as before. Each tile pair is a
  corridor of its own (labelled transitional heuristic in `overall_imbalance`).
- **Droving.** A `drove` mode (`carries: living_stock`, `cargo_walks`) walks
  animals overland at the cost of their own feed (maintenance and the work of
  walking, `sim/geography/droving.py`) and the drovers' days, with a daily loss
  rate (`cargo_loss_per_day`, labelled) counted in the cargo's cost share. Modes
  state the cargo classes they take; goods never go by drove and stock never goes
  by cart, but is shipped on water. Living-stock materials (the materials
  `data/world/living_stock.json` lists) take their route and domestic haul from
  these modes. Pace and herd size come from popular summaries of historical
  droving (Droving, https://en.wikipedia.org/wiki/Droving; Cattle drives in the
  United States, https://en.wikipedia.org/wiki/Cattle_drives_in_the_United_States),
  confidence D; the loss rate and the walking resistance are labelled heuristics.
  Plant stock in the same data file is walked too, which is wrong for seed; a
  per-material carriage class in the stock data would fix it.

The cargo's own charges are `Complaints/340` (closed).

Related: 135, 323, 338.
