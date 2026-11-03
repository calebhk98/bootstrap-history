"""The prices module built for a test, with plain values for the views it reads (sim/tests/module_harness.py).

    module = prices_stand_in.build(civilisation={"id": "x", "starting_interest_rate": 0.05}, market_rate=lambda: 0.08)
    module.price_tables()                   # a method of the module, called directly

Every default is an empty world: nothing granted or in use, no farmland, no seller, a rate of the starting rate. A test
overrides the views it is about."""
from typing import Any, Dict, Optional

from sim.prices.module import Prices
from sim.tests import module_harness


class _OpeningSchedule:
    """The opening wage schedule a stand-in civilisation opens on: no trade wages, an hour worth one unit of money."""
    money_per_labour_hour = 1.0

    def document(self):
        return {"wage_rates_denarii_per_hour": {}, "money_per_labour_hour": self.money_per_labour_hour}


def build(views: Optional[Dict[str, Any]] = None, **overrides: Any) -> Prices:
    """A Prices module whose reads are plain values; keyword arguments (or `views`) override a view by name."""
    plain: Dict[str, Any] = {
        "civilisation": {"id": "stand_in", "starting_interest_rate": 0.05}, "year": 100, "techniques_granted": set(),
        "techniques_in_use": frozenset(), "techniques_held": set(),
        "operating": set(), "price_epoch": (), "producers_stamp": (), "market_rate": 0.05,
        "money_per_labour_hour": 1.0, "labour_quote": lambda trade: 1.0, "farm_land_hectares": 0.0,
        "household_prices": {}, "material_seller": lambda material: None,
        "is_venture": lambda node_id: False, "concern_baskets_now": lambda node_id: None,
        "venture_ramp": lambda node_id: 1.0, "material_pool": lambda material: (material, material),
        "wage_schedule_for": lambda civilisation: _OpeningSchedule(), "unskilled_trade": "labourer"}
    plain.update(views or {})
    plain.update(overrides)
    return module_harness.build(Prices, views=plain, module_id="prices")
