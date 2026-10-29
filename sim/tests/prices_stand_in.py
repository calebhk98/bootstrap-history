"""The prices module built for a test, with plain values for the views it reads (sim/tests/module_harness.py).

    module = prices_stand_in.build(civilisation={"id": "x", "starting_interest_rate": 0.05}, market_rate=lambda: 0.08)
    module.price_tables()                   # a method of the module, called directly

Every default is an empty world: nothing granted or in use, no farmland, no seller, a rate of the starting rate. A test
overrides the views it is about."""
from typing import Any, Dict, Optional

from sim.prices.module import Prices
from sim.tests import module_harness


def build(views: Optional[Dict[str, Any]] = None, **overrides: Any) -> Prices:
    """A Prices module whose reads are plain values; keyword arguments (or `views`) override a view by name."""
    plain: Dict[str, Any] = {
        "civilisation": {"id": "stand_in", "starting_interest_rate": 0.05}, "year": 100, "techniques_granted": set(),
        "techniques_in_use": frozenset(), "techniques_held": set(),
        "operating": set(), "price_epoch": (), "producers_stamp": (), "market_rate": 0.05,
        "money_per_labour_hour": 1.0, "labour_quote": lambda trade, hours=0.0: 1.0, "farm_land_hectares": 0.0,
        "household_prices": {}, "material_seller": lambda material: None, "agent_wage": lambda trade: None,
        "agent_land_rent": None, "is_venture": lambda node_id: False, "concern_baskets_now": lambda node_id: None,
        "venture_ramp": lambda node_id: 1.0, "material_pool": lambda material: (material, material)}
    plain.update(views or {})
    plain.update(overrides)
    return module_harness.build(Prices, views=plain, module_id="prices")


def build_over_book(cost_book: Any, reference: str, commodity_of_material: Optional[Dict[str, str]] = None, **overrides: Any) -> Prices:
    """A Prices module costed against one given `CostBook`, whose incumbents make every good by the entry `reference`."""
    module = build(**overrides)
    memo: Dict[Any, Any] = {}
    module.cost_book = lambda: (None, cost_book, memo)
    module.reference_entry = lambda material: reference
    module.material_commodity_map = lambda: dict(commodity_of_material or {})
    return module
