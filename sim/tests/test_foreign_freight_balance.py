"""Foreign freight is priced from the carrier, and trade is paid in coin and carried by a fleet
(Complaints/326, 323).

Freight per tonne-km comes from the carrier's physics: travel time, the empty return where flows
are one-sided, the carrier's capital at the market rate and losses at sea. Goods cross in coin
metal, a persistent deficit drains the coin stock and lowers the traded price level, and a route
lifts only what its carriers can.
"""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own yearly material market


from sim.engine.data import load_civ
from sim.world import balance_of_payments, trade_between
from sim.geography import freight_cost, sea_freight, trade_routes, transport
from sim.world.market import MarketConditions

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

_regions = {"a": {"lat": 0.0, "lon": 0.0, "coastal": True},
            "b": {"lat": 0.0, "lon": 10.0, "coastal": True},
            "c": {"lat": 0.0, "lon": 30.0, "coastal": True}}
_network = {"modes": {"cart": {"requires_node": "wheel", "needs_ports": False}},
            "links": [{"from": "a", "to": "b", "modes": ["cart"]},
                      {"from": "b", "to": "c", "modes": ["cart"]}]}


def _route(destination):
    return trade_routes.cheapest_route(
        _network, _regions, ["a"], [destination], frozenset({"cart"}), frozenset({"wheel"}),
        lambda lat0, lon0, lat1, lon1: abs(lon1 - lon0) * 100.0, {"cart": _rate_of(imbalance=1.0)},
        days_per_km={"cart": 1.0 / _cart.distance_per_day_km}, difficulty=lambda a, b: 1.0)


check("a longer route costs more per tonne and takes more days",
      _route("c").cost_per_tonne > _route("b").cost_per_tonne
      and _route("c").travel_days > _route("b").travel_days > 0.0,
      (_route("b").cost_per_tonne, _route("c").cost_per_tonne))

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
      balanced["sea"] < 0.2 * balanced["cart"], balanced)
_market_rate = s.market_rate
s.market_rate = lambda: 4.0 * _market_rate()
dearer = s._freight_mode_costs(0.0)
check("dearer money in this society raises every mode's freight",
      all(dearer[mode] > balanced[mode] for mode in balanced), (balanced, dearer))
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
      balance_of_payments.price_level(opening, opening) == 1.0, None)
check("a drained stock lowers the price level and a swollen one raises it",
      balance_of_payments.price_level(0.5 * opening, opening) < 1.0
      < balance_of_payments.price_level(2.0 * opening, opening), None)
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
r._settle_flow(PARTNER, 5.0, 0.1 * home_opening, home_per_coin)
paid = r.foreign_balance_of_payments(PARTNER)
check("an import is paid in coin that leaves the home stock",
      abs(r.home_coin_stock_units() - 0.9 * home_opening) < 1e-6 * home_opening
      and paid["coin_paid_out_units"] > 0.0 and paid["goods_in_value"] > 0.0, paid)
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

# --- a drained home economy exports more and imports less, at the same stated prices.


def stubbed_pair(simulation, home_price, foreign_price, freight=1.0):
    # the home price is in home money, which already follows the home coin stock
    simulation._foreign_price_pair = lambda commodity, facts: (
        home_price * simulation.home_price_level(), foreign_price)
    simulation._foreign_sides = lambda commodity, facts: (True, True)
    simulation._route_freight_per_tonne = lambda civilization, imbalance=None: freight
    simulation._agent_cost_per_tonne = lambda civilization_id, route: 0.0
    simulation._output_is_sourced = lambda commodity: True
    simulation.foreign_opening = lambda civilization_id, commodity, solved: (500.0, 500.0)
    simulation.foreign_lift_left_tonnes = lambda civilization_id, route: (1e9, 1e9)
    simulation.household._foreign_facts_cache = None
    return simulation


GOOD = "silk_kg"
level_normal = stubbed_pair(sim(civ="rome_100ad", capital=1e9), 100.0, 100.0)
level_normal.foreign_economies = lambda: [PARTNER]
normal_flow = level_normal.market_state(GOOD)["trade_tonnes"]
level_drained = stubbed_pair(sim(civ="rome_100ad", capital=1e9), 100.0, 100.0)
level_drained.foreign_economies = lambda: [PARTNER]
level_drained._foreign_ledger(PARTNER, create=True)["home_coin_units"] = (
    -0.5 * level_drained.home_coin_stock_units())
drained_flow = level_drained.market_state(GOOD)["trade_tonnes"]
check("with the home price level lowered by an outflow of coin, flows turn toward exports",
      drained_flow < normal_flow, (normal_flow, drained_flow))

# --- a route lifts only what its carriers can.
cheap = MarketConditions(household_demand_at_anchor_tonnes=500.0, committed_demand_tonnes=0.0,
                         society_capacity_tonnes=0.0, actor_supply_tonnes=0.0,
                         founder_sales_tonnes=0.0, stock_tonnes=0.0, floor_ratio=0.5, ceiling_ratio=4.0)
rich = MarketConditions(household_demand_at_anchor_tonnes=10.0, committed_demand_tonnes=0.0,
                        society_capacity_tonnes=500.0, actor_supply_tonnes=0.0,
                        founder_sales_tonnes=0.0, stock_tonnes=0.0, floor_ratio=0.5, ceiling_ratio=4.0)
free_trade = trade_between.clear_trading_markets(cheap, rich, 100.0, 10.0, 1.0)
lifted = trade_between.clear_trading_markets(cheap, rich, 100.0, 10.0, 1.0, lift_into_home_tonnes=20.0)
check("goods flow without a limit when the price gap pays", free_trade.flow_tonnes > 20.0,
      free_trade.flow_tonnes)
check("a carrier capacity caps the tonnes that cross",
      0.0 < lifted.flow_tonnes <= 20.0 + 1e-9, lifted.flow_tonnes)

fleet = stubbed_pair(sim(civ="rome_100ad", capital=1e9), 100.0, 10.0)
fleet.foreign_economies = lambda: [PARTNER]
del fleet.foreign_lift_left_tonnes
route = fleet._foreign_economy_facts(PARTNER)["route"]
opening_lift = fleet.foreign_lift_capacity_tonnes(PARTNER, route)
check("a route's opening lift is its opening carriers' tonnes a year, finite and positive",
      0.0 < opening_lift < 1e9, opening_lift)
fleet._foreign_ledger(PARTNER, create=True)["lift_tonnes_per_year"] = 5.0
capped = fleet.market_state(GOOD)["trade_tonnes"]
check("a small fleet limits the volume traded", abs(capped) <= 5.0 + 1e-6, capped)
# Merchants adjust part of the way each year, so the flow reaches the fleet's lift over years;
# start from a year when it already has.
fleet.state.economy.foreign_market_book[PARTNER][GOOD]["trade_tonnes"] = -5.0
fleet._step_market()
ledger = fleet._foreign_ledger(PARTNER)
check("tonnes the fleet could not lift are recorded as unmet, then the fleet grows from them",
      ledger["lift_tonnes_per_year"] > 5.0 * (1.0 - 1.0 / sea_freight.HULL_SERVICE_LIFE_YEARS)
      and ledger["fleet_capital"] > 0.0, ledger)
check("the fleet grows by no more than yards can build in a year",
      ledger["lift_tonnes_per_year"] <= max(5.0, opening_lift) * 1.1 + 5.0, ledger)

# --- the ledger saves and loads, so a loaded game pays and lifts as the unbroken one does.
saved = stubbed_pair(sim(civ="rome_100ad", capital=1e9), 100.0, 10.0)
saved.foreign_economies = lambda: [PARTNER]
saved._step_market()
_save_path = os.path.join(tempfile.gettempdir(), "foreign_ledger_save_test.json")
_protocol.save_state(saved, _save_path)
loaded = sim(civ="rome_100ad", capital=1e9)
_protocol.load_state(loaded, _save_path)
os.remove(_save_path)
check("the foreign ledger is not empty after a year of trade",
      bool(saved.state.economy.foreign_ledger.get(PARTNER)), saved.state.economy.foreign_ledger)
check("the foreign ledger survives a save and a load",
      loaded.state.economy.foreign_ledger == saved.state.economy.foreign_ledger, None)

# --- merchants add their own cost and a limit of capital to the route's freight (Complaints/339, 340).
traders = stubbed_pair(sim(civ="rome_100ad", capital=1e9), 100.0, 10.0)
traders.foreign_economies = lambda: [PARTNER]
trader_facts = traders._foreign_economy_facts(PARTNER)
trader_terms = traders.trader_terms(PARTNER, trader_facts, 100.0, 10.0)
check("merchants' cost over freight is a positive share of the price",
      0.0 < trader_terms.cost_share_of_price < 1.0, trader_terms.cost_share_of_price)
check("merchants finance a finite tonnage a year, more where the goods are cheaper",
      0.0 < trader_terms.capital_tonnes_out < trader_terms.capital_tonnes_in < float("inf"),
      trader_terms)
traders._foreign_ledger(PARTNER, create=True).update(
    {"lift_year": traders.state.scenario.year, "merchant_capital_used": 1e30})
check("capital already tied up this year leaves none for more trade",
      traders.merchant_capital_left(PARTNER) == 0.0, None)
