"""Foreign freight is priced from the carrier, and trade is paid in coin
(Complaints/326, 323).

Freight per tonne-km comes from the carrier's physics: travel time, the empty return where flows
are one-sided, the carrier's capital at the market rate and losses at sea. Goods cross in coin
metal, and a persistent deficit drains the coin stock and lowers the traded price level.
"""
from .harness import *  # noqa: F401,F403

sim = unopened_sim   # the freight and the coin ledger read the engine's own figures


from sim.engine.data import load_civ
from sim.world import balance_of_payments
from sim.geography import api as geography_api
from sim.geography import freight_cost, sea_freight, transport

PARTNER = "han_china_100ad"

# --- the carrier's cost, on stated numbers.
_cart = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)
_prices = freight_cost.CarrierPrices(vehicle=100.0, animals=2000.0)


def _rate_of(rate=0.1, imbalance=0.0, inputs=_cart, prices=_prices, loss=0.0):
    return freight_cost.freight_money_per_tonne_km(inputs, 0.5, 1.0, prices, rate, 250.0, imbalance, loss)


check("a one-sided flow pays the carrier's return leg: twice the balanced rate",
      abs(_rate_of(imbalance=1.0) / _rate_of(imbalance=0.0) - 2.0) < 1e-9,
      (_rate_of(imbalance=1.0), _rate_of(imbalance=0.0)))
check("a half-balanced flow pays half a return leg",
      abs(_rate_of(imbalance=0.5) / _rate_of(imbalance=0.0) - 1.5) < 1e-9, None)
check("dearer money raises freight, through the carrier's capital",
      _rate_of(rate=0.3) > _rate_of(rate=0.1), (_rate_of(rate=0.3), _rate_of(rate=0.1)))
check("a carrier that costs nothing and money at nothing leaves only running costs",
      abs(_rate_of(rate=0.0, prices=freight_cost.CarrierPrices(0.0, 0.0))
          - (_cart.feed_kg_per_tonne_km * 0.5 + _cart.driver_hours_per_tonne_km)) < 1e-12, None)
check("losing hulls at sea adds to the rate",
      _rate_of(inputs=sea_freight.sailing_freight_physical_inputs(), loss=0.01)
      > _rate_of(inputs=sea_freight.sailing_freight_physical_inputs(), loss=0.0), None)
check("no flow either way is the fully one-sided case",
      freight_cost.imbalance_of_flows(0.0, 0.0) == 1.0
      and freight_cost.imbalance_of_flows(10.0, 10.0) == 0.0
      and freight_cost.imbalance_of_flows(30.0, 10.0) == 0.5, None)
check("travel days follow the carrier's pace over the distance",
      abs(freight_cost.days_on_leg(2000.0, _cart) - 2.0 * freight_cost.days_on_leg(1000.0, _cart)) < 1e-9,
      None)

def _route(destination_tiles):
    held = {"lnd_two_wheel_cart"}
    return geography_api.route(
        _HAN_TILES[:1], destination_tiles, ["cart"],
        mode_costs={"cart": _rate_of(imbalance=1.0)}, held_nodes=held)


_HAN_TILES = geography_api.tiles_held(load_civ(PARTNER))
_NEAR = geography_api.reach(_HAN_TILES[:1], ["cart"], 60.0, held_nodes={"lnd_two_wheel_cart"})
_FAR = geography_api.reach(_HAN_TILES[:1], ["cart"], 250.0, held_nodes={"lnd_two_wheel_cart"})
_near_tile = sorted((tile for tile in _NEAR if tile != _HAN_TILES[0]), key=_NEAR.get)[-1]
_far_tile = sorted((tile for tile in _FAR if tile != _HAN_TILES[0]), key=_FAR.get)[-1]
check("a longer route costs more per tonne and takes more days",
      _route([_far_tile])["cost_per_tonne"] > _route([_near_tile])["cost_per_tonne"]
      and _route([_far_tile])["days"] > _route([_near_tile])["days"] > 0.0,
      (_route([_near_tile])["cost_per_tonne"], _route([_far_tile])["cost_per_tonne"]))

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
check("dearer money in this society raises every mode's freight (a herd that walks has no carrier capital)",
      all(dearer[mode] > balanced[mode] for mode in balanced if mode not in _walking)
      and all(dearer[mode] == balanced[mode] for mode in balanced if mode in _walking), (balanced, dearer))
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

# --- the coin that pays for goods.
opening = 1000.0
check("a stock at its opening level leaves traded prices where they are",
      balance_of_payments.money_stock_price_level(opening, opening) == 1.0, None)
check("a drained stock lowers the price level and a swollen one raises it",
      balance_of_payments.money_stock_price_level(0.5 * opening, opening) < 1.0
      < balance_of_payments.money_stock_price_level(2.0 * opening, opening), None)
check("an economy cannot pay out more coin than it holds",
      balance_of_payments.coin_paid(500.0, 200.0) == 200.0
      and balance_of_payments.coin_paid(-5.0, 200.0) == 0.0, None)

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
      r.home_coin_stock_units() >= -1e-6 and r.home_coin_stock_units() < 1e-6 * home_opening, None)
r._settle_flow(PARTNER, -5.0, 0.2 * home_opening, home_per_coin)
check("an export brings coin back in",
      r.home_coin_stock_units() > 0.1 * home_opening, r.home_coin_stock_units() / home_opening)
