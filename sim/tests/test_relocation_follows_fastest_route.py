"""Complaints/416: moving the household's base takes the days of the fastest route over the modes its people hold, not
a straight-line pace and not the cheapest haul. The route search runs on the small fixture map, the quote on a
stand-in labour over the real settlement mixin (no game). The same through a game on the real map is
test_relocation_follows_fastest_route_scenario."""
import itertools
from types import SimpleNamespace

from .harness import check

from sim.geography import api as geography_api
from sim.geography import routes_search
from sim.labour import labour_settlement
from sim.tests.test_geography_routes import small_map

QUICK_TOPIC = True

SMALL_MAP = small_map()
FOOT_AND_CART = {"foot", "cart"}


# --- the fastest route is no slower than the cheapest, and slower-but-cheaper hauls exist to tell them apart
pairs = list(itertools.permutations(sorted(SMALL_MAP.tiles), 2))
mode_sets = ({"foot", "cart"}, {"foot", "river_boat"}, {"foot", "cart", "river_boat", "sail"})
slower = []
for origin, destination in pairs:
    for modes in mode_sets:
        cheapest = routes_search.route(SMALL_MAP, [origin], [destination], modes)
        fastest = routes_search.route(SMALL_MAP, [origin], [destination], modes, fastest=True)
        if (cheapest is None) != (fastest is None):
            slower.append(("joined by one search and not the other", origin, destination, sorted(modes)))
        elif cheapest is not None and fastest["days"] > cheapest["days"] + 1e-9:
            slower.append((origin, destination, sorted(modes), fastest["days"], cheapest["days"]))
check("on every pair and mode set of the small map the fastest route takes no more days than the cheapest",
      not slower, slower[:3])
cheapest = routes_search.route(SMALL_MAP, ["a1"], ["a2"], FOOT_AND_CART)
fastest = routes_search.route(SMALL_MAP, ["a1"], ["a2"], FOOT_AND_CART, fastest=True)
check("and where they differ the fastest is strictly quicker and dearer (a1 to a2 on foot or cart)",
      fastest["days"] < cheapest["days"] - 1.0 and fastest["cost_per_tonne"] > cheapest["cost_per_tonne"],
      (fastest["days"], cheapest["days"]))


# --- the base's journey asks the fastest route, over the modes the household holds
class _Settlement(labour_settlement.SettlementMixin):
    """The real settlement rule over a base tile, held technologies, a payroll and a director pool."""

    def __init__(self, pool=1000.0, payroll=5000.0, modes=FOOT_AND_CART):
        self.asked = []
        self._pool, self._payroll = pool, payroll
        self._world = SimpleNamespace(state=SimpleNamespace(economy=SimpleNamespace(improvements={})))
        self.modes = modes

    def base_tile(self):
        return "a1"

    def held_technologies(self):
        return frozenset({"held_node"})

    def director_pool(self):
        return self._pool

    def _relocation_wage_bill_per_year(self):
        return self._payroll


def _on_small_map(settlement, body):
    """Run `body` with the settlement's route asked of the small map, recording each ask."""
    real = labour_settlement.geography
    labour_settlement.geography = SimpleNamespace(
        usable_modes=lambda held_sets: settlement.modes,
        route=lambda origins, destinations, modes, improvements=None, held_nodes=None, fastest=False:
            settlement.asked.append((origins, destinations, set(modes), fastest, held_nodes))
            or geography_api.route(origins, destinations, modes, improvements, held_nodes=held_nodes, fastest=fastest,
                                   world_map=SMALL_MAP))
    try:
        return body()
    finally:
        labour_settlement.geography = real


settlement = _Settlement()
days = _on_small_map(settlement, lambda: settlement.travel_days_to_tile("a2"))
check("the days to a tile are those of the fastest route from the base over the held modes",
      settlement.asked == [(["a1"], ["a2"], FOOT_AND_CART, True, frozenset({"held_node"}))]
      and abs(days - fastest["days"]) < 1e-9 and days < cheapest["days"], (settlement.asked, days))
unjoined = _Settlement(modes={"rail"})
check("a tile no route joins has no travel days and no quote",
      _on_small_map(unjoined, lambda: (unjoined.travel_days_to_tile("a2"), unjoined.relocation_quote("a2")))
      == (None, None))


# --- the quote is the share of a year spent walking, of the director's hours and of the payroll
class _FixedDays(_Settlement):
    def __init__(self, days, **fields):
        super().__init__(**fields)
        self._days = days

    def travel_days_to_tile(self, tile):
        return self._days


quote = _FixedDays(73.0, pool=1000.0, payroll=5000.0).relocation_quote("anywhere")
check("a journey of a fifth of a year costs a fifth of the director's hours and a fifth of the payroll",
      quote == (73.0, 200.0, 1000.0), quote)
quote = _FixedDays(1000.0, pool=1000.0, payroll=5000.0).relocation_quote("anywhere")
check("a journey longer than a year costs a year's hours and payroll, no more", quote == (1000.0, 1000.0, 5000.0), quote)
check("a journey with no route has no quote", _FixedDays(None).relocation_quote("anywhere") is None)
