"""The resources module built for a test, with plain values for the views it reads (sim/tests/module_harness.py).

    module = resources_stand_in.build(budget=30.0)           # seat state empty, Rome's map, a purse that raises 30
    module.open_mine(OpenMine("aluminium_kg", 5.0))           # the module's own handler, called directly
    resources_stand_in.paid(module)                           # the amounts it paid to named edges, in order

Every default is what a unit price and no state-reach would read; a test overrides the views it is about."""
import json
import os
from typing import Any, Dict, List, Optional

from sim.ledger.api import PayEdge
from sim.materials.api import ApplyThrottle
from sim.resources.module import Resources
from sim.resources.state import ResourcesSeat, ResourcesWorld
from sim.tests import land_views, module_harness

LAND_VIEWS = ("deposit_catalogue", "deposits_listed", "deposits_worked_before", "deposit_working_rate", "prospect_finds",
              "tile_endowment", "tiles_listed_by", "land_area_of", "felled_after_cuts", "felled_after_regrowth")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rome() -> Dict[str, Any]:
    with open(os.path.join(ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
        return json.load(handle)


def build(budget: float = 1e18, year: int = 100, seat: Optional[ResourcesSeat] = None, world: Optional[ResourcesWorld] = None,
          views: Optional[Dict[str, Any]] = None, answers: Optional[Dict[type, Any]] = None) -> Resources:
    """A Resources module whose reads are plain values; `budget` is what the seat can raise for one purchase."""
    civ = rome()
    plain: Dict[str, Any] = {
        "year": year, "start_year": 100, "civilisation": civ, "price_index": 1.0,
        "material_price": lambda material: 1.0, "wage": lambda trade: 1.0, "labour_quote": lambda trade, hours: 1.0,
        "money_per_labour_hour": 1.0, "normalized_material": lambda material: material, "material_demand": {},
        "material_checks": {}, "charcoal_per_hectare": 1.0, "material_shortfall": lambda material, by_tag=None: 0.0,
        "material_market_tonnes": lambda material: 0.0, "material_unsupplied_sentence": lambda material: None,
        "material_binding": None, "goods_stock": lambda commodity: 0.0,
        "acting_balance": 1e15, "can_pay": lambda cost: cost <= budget, "purchase_budget": budget,
        "spending_power": lambda kind="buy": budget,
        "affordable_units": lambda unit_cost, decimals=1: budget / max(unit_cost, 1e-9), "afford_means": "cash",
        "inspection_reach": 0.5, "forest_reach": 0.5, "revenue_estimate": 0.0, "running": lambda node_id: False,
        "running_stamp": (None, (), None), "effect_best": lambda channel: None, "effect_terms": lambda channel: [],
        "mineral_scale": lambda material: 1.0, "weather_seed": lambda year, region=None: 17,
        "automatic_policy": lambda name: True,
        "money_text": lambda amount, grouped=False, short=False: "%g" % amount,
        "mass_text": lambda amount, **keywords: "%g t" % amount, "area_text": lambda amount, **keywords: "%g ha" % amount,
        "mass_rate_text": lambda amount, **keywords: "%g t/year" % amount,
        "mass_per_area_text": lambda amount, **keywords: "%g t per area" % amount}
    plain.update(land_views.of(civ, LAND_VIEWS))
    plain.update(views or {})
    answers = {ApplyThrottle: 1.0, **(answers or {})}      # the materials module reads full pace unless a test says otherwise
    return module_harness.build(Resources, views=plain, answers=answers, world=world or ResourcesWorld(),
                                seat=seat or ResourcesSeat(), module_id="resources")


def paid(module: Resources) -> List[float]:
    """The amounts the module paid to named edges, in order."""
    return [command.amount for command in module_harness.sent(module) if isinstance(command, PayEdge)]
