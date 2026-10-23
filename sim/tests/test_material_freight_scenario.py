"""Scenario (Complaint 640 audit): the freight crossing wired into a live Sim. The markup and scarcity arithmetic are rule
tests in test_material_freight, and a held material costing nothing to haul is held by test_mineral_access_from_tiles.
Here a Sim's coal freight distance is geography's own route, and its cost per kilogram is the cart's rate over that distance
with the mode's dues once."""
from .harness import *  # noqa: F401,F403

from sim.geography import transport as _transport
from sim.geography import api as geography_api

s_mexica = unopened_sim(civ="mexica_1500", capital=1.0)
_mexica_coal_km = s_mexica.material_freight_distance_km("coal")

# =============================================================================
# THE DISTANCE IS REAL GEOGRAPHY, NOT INVENTED. material_freight_distance_km
# has to equal geography's own route from the tiles held to the nearest
# producing region, not a number this crossing made up (CLAUDE.md SS3.1).
# =============================================================================
_candidates = list(s_mexica.geography.source_tiles("coal"))
_held = geography_api.tiles_held(s_mexica.civ, s_mexica.world_map)
_held_nodes = s_mexica.geography._world.held_nodes
_route = geography_api.route(_held, _candidates,
                             geography_api.usable_modes([_held_nodes]), s_mexica.state.economy.improvements,
                             held_nodes=_held_nodes, world_map=s_mexica.world_map)
_expected_km = _route["km"] if _route else None
check("the freight distance is the kilometres of geography's cheapest route over the modes held "
      "from the tiles held to the nearest coal-bearing tile",
      _expected_km is not None and abs(_mexica_coal_km - _expected_km) < 1e-6,
      (_mexica_coal_km, _expected_km))

# =============================================================================
# THE COST IS TRACEABLE TO TRANSPORT.PY'S OWN TONNE-KM FIGURES. Recomputing
# material_freight_cost_per_kg by hand, from transport.py's own physical
# inputs for the same team/vehicle/surface plus this file's own book feed
# price and labourer wage, must match exactly - this crossing is not
# allowed to add a fudge factor transport.py's own numbers cannot explain.
# =============================================================================
_inputs = _transport.draught_freight_physical_inputs(
    _transport.OX, int(s_mexica.LAND_FREIGHT_TEAM_SIZE),
    _transport.CART, _transport.DIRT_TRACK)
_feed_price = s_mexica._material_price_per_kg(s_mexica.FREIGHT_FEED_PRICE_MATERIAL)
_wage = s_mexica.labour.wage_per_hour(s_mexica.FREIGHT_DRIVER_WAGE_TRADE)
# the return trip follows last year's domestic flow ledger (domestic_haul.py); the opening economy already carries goods
_expected_denarii_per_tonne_km = s_mexica.land_freight_money_per_tonne_km(s_mexica._domestic_flow_imbalance())
_running_denarii_per_tonne_km = (_inputs.feed_kg_per_tonne_km * _feed_price
                                 + _inputs.driver_hours_per_tonne_km * _wage)
check("a cart haul costs more than its feed and driver: the carrier's capital and empty return are in",
      _expected_denarii_per_tonne_km > _running_denarii_per_tonne_km, None)
_dues = s_mexica.domestic_haul_dues_per_tonne("cart")


def _expected_cost_per_kg_over(distance_km):
    """The cart rate over the distance, divided by the share of lift left after the carrier's food, plus the dues."""
    return geography_api.freight_cost.leg_money_per_tonne(
        _expected_denarii_per_tonne_km, _inputs, distance_km,
        restock_days=geography_api.provisions.RESTOCK_INTERVAL_DAYS, dues_per_tonne=_dues) / 1000.0


# no way joins Mesoamerica to coal: one leg of the cart over the great-circle distance, priced like a found route's legs
_mexica_coal_haul = s_mexica.material_haul_route("coal")
check("coal's freight cost per kilogram is the cart's own feed, driver and capital over the distance, with the mode's dues",
      [leg.mode for leg in _mexica_coal_haul.legs] == ["cart"]
      and s_mexica.material_freight_cost_per_kg("coal") >= _expected_cost_per_kg_over(_mexica_coal_km) - 1e-9,
      (s_mexica.material_freight_cost_per_kg("coal"), _expected_cost_per_kg_over(_mexica_coal_km)))
check("a haul pays the cart's dues once, whatever the distance",
      _dues > 0.0 and len(_mexica_coal_haul.legs) == 1
      and abs(_mexica_coal_haul.cost_per_tonne
              - (_expected_denarii_per_tonne_km * _mexica_coal_km
                 / geography_api.provisions.restocked_share(
                     _inputs, _mexica_coal_km, geography_api.provisions.RESTOCK_INTERVAL_DAYS) + _dues)) < 1e-6,
      _dues)
