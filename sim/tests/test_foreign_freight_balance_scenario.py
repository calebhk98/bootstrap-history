"""Scenario (Complaint 640): a running game prices foreign freight from its own prices, wages and market rate, and pays trade in coin.

The carrier and coin rules, on inputs the test builds, are in test_foreign_freight_balance.py."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim   # the freight and the coin ledger read the engine's own figures

from sim.engine.data import load_civ
from sim.geography import api as geography_api

PARTNER = "han_china_100ad"

# --- the engine prices it from this society's prices, wages and market rate.
s = sim(civ="rome_100ad", capital=1e9)
balanced, one_sided = s._freight_mode_costs(0.0), s._freight_mode_costs(1.0)
check("every mode pays its return leg when flows are one-sided",
      all(one_sided[mode] > balanced[mode] for mode in balanced), (balanced, one_sided))
check("a cart costs more than its feed and driver alone: the oxen and the cart are capital",
      balanced["cart"] > (s._land_freight_physical_inputs().feed_kg_per_tonne_km
                          * s._material_price_per_kg("wheat_kg")
                          + s._land_freight_physical_inputs().driver_hours_per_tonne_km
                          * s.labour.wage_per_hour("labourer")), None)
check("the sea is still far cheaper than land per tonne-km",
      balanced["sail"] < 0.2 * balanced["cart"], balanced)
_market_rate = s.market_rate
s.market_rate = lambda: 4.0 * _market_rate()
dearer = s._freight_mode_costs(0.0)
_walking = set(geography_api.walking_cargo_modes())
# a herd that walks has no carrier capital, so dearer money reaches it only through the prices of its feed and
# the drovers' keep, which a cart pays too on top of its oxen and wagon
_rise = {mode: dearer[mode] / balanced[mode] for mode in balanced if balanced[mode] > 0.0}
check("dearer money in this society raises every mode's freight, a walking herd's less than a cart's",
      all(dearer[mode] > balanced[mode] for mode in balanced if mode not in _walking)
      and all(_rise[walk] < _rise["cart"] for walk in _walking if walk in _rise),
      (balanced, dearer))
s.market_rate = _market_rate
route = s._foreign_route(PARTNER, 1.0)
check("the route to the partner carries travel days, longer for more distance",
      route.travel_days > 0.0 and all(leg.travel_days > 0.0 for leg in route.legs), route.travel_days)
check("a route with a balanced return is cheaper than the same route with an empty one",
      s._route_freight_per_tonne(PARTNER, 0.0) < s._route_freight_per_tonne(PARTNER, 1.0), None)
book = s.state.economy.foreign_market_book
book[PARTNER] = {"iron": {"trade_tonnes": 10.0}, "cloth": {"trade_tonnes": -10.0}}
check("freight reads last year's flow imbalance from the partner's book: balanced is 0",
      s._foreign_flow_imbalance(PARTNER) == 0.0, None)
book[PARTNER] = {"iron": {"trade_tonnes": 10.0}}
check("...and one-sided flow is 1", s._foreign_flow_imbalance(PARTNER) == 1.0, None)
book.clear()

r = sim(civ="rome_100ad", capital=1e9)
r.foreign_economies = lambda: [PARTNER]
coin = load_civ(PARTNER)["coin_standard"]
home_per_coin = coin["kg_per_unit"] * r._material_prices()[coin["material"]]
home_opening = r.home_coin_stock_units()
check("with no trade the home stock is its opening one and the price level is one",
      r.home_price_level() == 1.0 and r.partner_price_level(PARTNER) == 1.0, None)
r._coin_carriage_money_per_tonne = lambda civilization_id: 0.0   # carriage of coin: test_coin_carriage_and_treasury_keeping
r._settle_flow(PARTNER, 5.0, 0.1 * home_opening, home_per_coin)
check("an import is paid in coin that leaves the home stock",
      abs(r.home_coin_stock_units() - 0.9 * home_opening) < 1e-6 * home_opening, r.home_coin_stock_units())
check("...and arrives in the partner's stock, at its own coin's value",
      abs(r._foreign_ledger(PARTNER)["partner_coin_units"] * home_per_coin
          - 0.1 * home_opening) < 1e-6 * home_opening, None)
check("a persistent deficit lowers the home price level",
      r.home_price_level() < 1.0 < r.partner_price_level(PARTNER), None)
r._settle_flow(PARTNER, 5.0, 100.0 * home_opening, home_per_coin)
check("an import beyond the coin held is paid only as far as the stock goes",
      r.home_coin_stock_units() >= -1e-12 * home_opening and r.home_coin_stock_units() < 1e-6 * home_opening,
      r.home_coin_stock_units() / home_opening)   # floating-point dust is relative to a stock of this size
r._settle_flow(PARTNER, -5.0, 0.2 * home_opening, home_per_coin)
check("an export brings coin back in",
      r.home_coin_stock_units() > 0.1 * home_opening, r.home_coin_stock_units() / home_opening)
