"""Foreign freight is priced from the carrier, and trade is paid in coin
(Complaints/326, 323): the rules, on inputs the test builds. The engine's own figures are in the _scenario file.

Freight per tonne-km comes from the carrier's physics: travel time, the empty return where flows
are one-sided, the carrier's capital at the market rate and losses at sea. Goods cross in coin
metal, and a persistent deficit drains the coin stock and lowers the traded price level.
"""
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

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

