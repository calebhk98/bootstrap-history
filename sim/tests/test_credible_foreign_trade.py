"""Foreign trade falls out of the partner's own society, the map and freight
(Complaints/298, 299, 300).

Capacity comes from the partner's regions and techniques, freight from the
cheapest route over the map's links and modes, and goods only one side makes
can still cross when their value per tonne pays for the haul.
"""
import dataclasses

from .harness import *  # noqa: F401,F403

from sim.engine import foreign_economies as _foreign_module
from sim.engine import foreign_capacity as _capacity
from sim.engine.data import load_civ, load_geography, starting_schedule
from sim.engine.material_units import tonnes_per_unit
from sim.world import market, trade_between
from sim.geography import api as geography_api
from sim.geography import sea_freight, transport

PARTNER = "han_china_100ad"


def rome_with_partner():
    simulation = sim(civ="rome_100ad", capital=1e9)
    simulation.foreign_economies = lambda: [PARTNER]
    return simulation


# --- sea freight: wind does the work, so a tonne-km costs crew time only.
sea = sea_freight.sailing_freight_physical_inputs()
cart = transport.draught_freight_physical_inputs(
    transport.OX, 2, transport.CART, transport.DIRT_TRACK)
check("a sailing hull needs far fewer hours per tonne-km than an ox cart",
      cart.driver_hours_per_tonne_km / sea.driver_hours_per_tonne_km
      >= transport.LAND_TO_SEA_FREIGHT_COST_RATIO_LOW,
      (cart.driver_hours_per_tonne_km, sea.driver_hours_per_tonne_km))
check("...and the hull's distance per day follows its voyage speed",
      abs(sea.distance_per_day_km - sea_freight.ground_km_per_day()) < 1e-9, None)

# --- routes over tiles, from the geography contract.
_ROME_TILES = geography_api.tiles_held(load_civ("rome_100ad"))
_HAN_TILES = geography_api.tiles_held(load_civ(PARTNER))
_COSTS = {"sail": 0.03, "cart": 1.0}
_SAIL_NODE = "sea_square_sail"
_CART_NODE = "lnd_two_wheel_cart"


def _tile_route(ends_hold, costs=_COSTS, origins=_HAN_TILES, destinations=_ROME_TILES):
    held = [frozenset(end) for end in ends_hold]
    modes = [mode for mode in geography_api.usable_modes(held) if mode in costs]
    return geography_api.route(origins, destinations, modes, mode_costs=costs,
                               held_nodes=frozenset().union(*held))


both_sail = {_SAIL_NODE, _CART_NODE}
route = _tile_route([both_sail, both_sail])
check("Rome to Han China has a route over tiles with sail legs and a finite cost",
      route is not None and route["cost_per_tonne"] < float("inf")
      and any(leg["mode"] == "sail" for leg in route["legs"]), route and route["cost_per_tonne"])
check("...its legs run in order from origin to destination",
      route["legs"][0]["from"] in _HAN_TILES and route["legs"][-1]["to"] in _ROME_TILES
      and all(first["to"] == second["from"] for first, second in zip(route["legs"], route["legs"][1:])), None)
check("the route's cost is the sum of its legs'",
      abs(route["cost_per_tonne"] - sum(leg["cost_per_tonne"] for leg in route["legs"])) < 1e-6, None)
check("a mode only one end holds is not used",
      "sail" not in geography_api.usable_modes([both_sail, {_CART_NODE}]), None)
check("a partner with no mode the map can carry between them has no route",
      _tile_route([set(), set()], costs={"sail": 0.03, "cart": 1.0}) is None, None)
check("a shared tile needs no legs",
      _tile_route([both_sail, both_sail], origins=_ROME_TILES, destinations=_ROME_TILES)["legs"] == [], None)

# --- Rome and Han on the shipped map.
s = rome_with_partner()
facts = s._foreign_economy_facts(PARTNER)
route = facts["route"]
check("the route to the partner is a chain of legs on the map",
      route is not None and route.legs and all(
          leg.origin in geography_api.tile_ids() and leg.destination in geography_api.tile_ids()
          for leg in route.legs),
      route and route.describe())
check("...joining its regions to this society's",
      route.legs[0].origin in _HAN_TILES and route.legs[-1].destination in _ROME_TILES,
      route.describe())
check("...by sea, which both can sail, rather than the whole way by cart",
      any(leg.mode == "sail" for leg in route.legs), route.describe())
centroid_cart_freight = (s._freight_mode_costs()["cart"] * route.distance_km)
check("freight over the chosen route is far below hauling the same distance by cart",
      facts["freight_per_tonne"] < 0.2 * centroid_cart_freight,
      (facts["freight_per_tonne"], centroid_cart_freight))
check("the legs are readable for the player",
      s.foreign_route_legs(PARTNER) and all(len(leg) == 5 for leg in s.foreign_route_legs(PARTNER)),
      None)
no_sea = dict(load_civ(PARTNER),
              starting_techs=[node for node in load_civ(PARTNER)["starting_techs"]
                              if node != "sea_square_sail"])
overland = s._foreign_route(no_sea)
check("a partner that cannot sail is reached overland, and dearly",
      overland is not None and all(leg.mode != "sail" for leg in overland.legs)
      and overland.cost_per_tonne > 5 * route.cost_per_tonne,
      overland and overland.describe())

# --- capacity comes from the partner's own regions and techniques.
solved = facts["solved_materials"]
iron_capacity, iron_demand = s.foreign_opening(PARTNER, "iron", solved)
han_iron_share = s.geography.held_share(_HAN_TILES, "iron")
check("a mined commodity is the national output times the share of the deposits on its tiles, not population scaled",
      abs(iron_capacity - s._national_output_tonnes("iron") * han_iron_share) < 1e-6
      and han_iron_share > 0.0, (iron_capacity, han_iron_share))
check("...and its own demand opens in balance with it", iron_demand == iron_capacity, None)
_real_share = s._foreign_mineral_share
s._foreign_mineral_share = lambda civilization_id, commodity: 0.0
check("a mined commodity its tiles hold no share of has no capacity",
      s.foreign_opening(PARTNER, "iron", solved)[0] == 0.0, None)
s._foreign_mineral_share = _real_share
check("a material extracted from a deposit its regions do not hold cannot be made",
      not s._foreign_can_make(PARTNER, "platinum_g", frozenset({"platinum_g", "platinum_ore_kg"})),
      None)


def forget_capacity_caches(simulation):
    """The capacity caches assume one technique set per economy."""
    for name in ("_foreign_can_make_cache", "_foreign_demand_cache"):
        simulation.household.__dict__.pop(name, None)


forget_capacity_caches(s)
capacity, wanted = s.foreign_opening(PARTNER, "silk_kg", solved | {"silk_kg"})
check("a grown good the partner has a technique for opens with capacity equal to its demand",
      capacity > 0.0 and capacity == wanted, (capacity, wanted))
forget_capacity_caches(s)
capacity, wanted = s.foreign_opening(PARTNER, "silk_kg", frozenset())
check("the same good with no technique is wanted but cannot be supplied",
      capacity == 0.0 and wanted > 0.0, (capacity, wanted))
_per_hour = starting_schedule(PARTNER).money_per_labour_hour
_prices_in_hours = {material: price / _per_hour for material, price
                    in _foreign_module._foreign_prices_in_own_coin(PARTNER).items() if price > 0.0}
_population = float(load_civ(PARTNER)["population"])
_spending = sum(tonnes / tonnes_per_unit(material) * _prices_in_hours[material]
                for material, tonnes in _capacity.budget_scaled_final_tonnes(
                    _prices_in_hours, _population).items())
check("the partner's final-goods spending is held to the income its households have",
      0.0 < _spending <= _population * _capacity.MEAN_INCOME_HOURS_PER_CAPITA * (1.0 + 1e-6),
      _spending)

# --- goods only one side makes cross, priced from the importer's side.


def stubbed_pair(simulation, home_makes, partner_makes, price=1000.0, freight=1.0,
                 partner_capacity=500.0, partner_demand=500.0, home_demand=500.0):
    simulation._foreign_price_pair = lambda commodity, facts: (price, price)
    simulation._foreign_sides = lambda commodity, facts: (home_makes, partner_makes)
    simulation._route_freight_per_tonne = lambda civilization: freight
    simulation._agent_cost_per_tonne = lambda civilization_id, route: 0.0
    simulation._output_is_sourced = lambda commodity: True
    simulation.foreign_opening = lambda civilization_id, commodity, solved: (
        partner_capacity, partner_demand)
    simulation.home_unmade_demand_tonnes = lambda commodity: home_demand
    simulation.household._foreign_facts_cache = None
    return simulation


GOOD = "silk_kg"
exporter = stubbed_pair(rome_with_partner(), True, False, partner_capacity=0.0,
                        partner_demand=500.0)
check("a good only this society makes flows out to a partner that wants it",
      exporter.market_state(GOOD)["trade_tonnes"] < 0.0, exporter.market_state(GOOD)["trade_tonnes"])
importer = stubbed_pair(rome_with_partner(), False, True, partner_capacity=500.0,
                        partner_demand=10.0, home_demand=500.0)
check("a good only the partner makes flows in to a society that wants it",
      importer.market_state(GOOD)["trade_tonnes"] > 0.0, importer.market_state(GOOD)["trade_tonnes"])
check("...with no home capacity of its own",
      importer._market_outcome(GOOD)[0].society_capacity_tonnes == 0.0, None)
dear = stubbed_pair(rome_with_partner(), False, True, freight=1e9, partner_demand=10.0)
check("freight above any price gap stops the flow",
      dear.market_state(GOOD)["trade_tonnes"] == 0.0, None)
check("no home demand for a good it cannot make means no trade in it",
      stubbed_pair(rome_with_partner(), False, True, home_demand=0.0).market_state(GOOD)[
          "trade_tonnes"] == 0.0, None)

# --- value per tonne against freight decides what crosses, not a name.
freight_per_tonne = facts["freight_per_tonne"]


def crossing(price_per_tonne):
    home = market.MarketConditions(100.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    foreign = market.MarketConditions(1.0, 0.0, 100.0, 0.0, 0.0, 0.0)
    return trade_between.clear_trading_markets(
        home, foreign, price_per_tonne, price_per_tonne, freight_per_tonne).flow_tonnes


check("a good worth many times the freight per tonne crosses the long route",
      crossing(200.0 * freight_per_tonne) > 0.0, freight_per_tonne)
check("a good worth too little to cover the freight even at the importer's ceiling does not",
      crossing(0.1 * freight_per_tonne) == 0.0, None)

# --- goods whose output is only a generic estimate are not traded against.
generic = rome_with_partner()
check("a commodity whose output is generic, not sourced, is not traded",
      not generic._output_is_sourced("steel_noric_kg")
      and generic.market_state("steel_noric_kg")["trade_tonnes"] == 0.0, None)
check("a commodity with a sourced output table is eligible",
      generic._output_is_sourced("iron"), None)

# --- the shipped data.
check("every mode the engine prices is one the map knows and the tree can unlock",
      set(s._freight_mode_costs()) <= set(geography_api.usable_modes([set(NODES)])), None)
check("the shipped data still leaves foreign economies to a decision by measurement",
      all(isinstance(record.get("enabled", False), bool)
          for record in _foreign_module.foreign_economy_records()), None)
