"""The production module for a test: built with `module_harness`, the game it reaches through `legacy_game` a stand-in the test supplies.

    module = production_host.build(SimpleNamespace(nodes=nodes), seat=ProductionSeat(), staff={"employees": {}})
    module.held_trade()

A method the module calls on itself can be replaced on the instance (`module.industry_depth = lambda node_id: 0.5`). A view given as a plain
value is that value; as a function it is called with the view's arguments (see `module_harness`). Defaults are the quiet answers: no
mechanics, one unit of money per labour hour, every trade a craft, no staff. The commands the module sent are in `module_harness.sent(module)`."""
from types import SimpleNamespace
from typing import Any, Dict, Optional

from sim.production.module import Production
from sim.production.state import ProductionSeat
from sim.tests import module_harness


def defaults(game: Any) -> Dict[str, Any]:
	return {
		"legacy_game": game, "money_per_labour_hour": 1.0, "trade_family": lambda trade: "craft",
		"staff": {"employees": {}, "freedmen": 0.0, "slaves": 0.0, "directors_extra": 0.0}, "staff_version": 0,
		"hour_commitments": {"wage_hours": 0.0}, "capability_sets": (frozenset(), frozenset(), {}),
		"mechanic": lambda name: {}, "techniques_held": frozenset(), "category_trait": lambda category, trait: False,
		"literacy": lambda field, country=None: 0.1, "held_goods_prices_in_hours": lambda held: {},
	}


def build(game: Optional[Any] = None, seat: Optional[ProductionSeat] = None, answers: Optional[Dict[type, Any]] = None,
          **views: Any) -> Production:
	"""The module over the quiet defaults and `views`, a fresh seat unless given, and `answers`, the replies of owners to commands."""
	game = SimpleNamespace() if game is None else game
	every_view = defaults(game)
	every_view.update(views)
	module = module_harness.build(Production, views=every_view, answers=answers, seat=seat or ProductionSeat(), module_id="production")
	module.clock.acting_seat = "founder"
	return module
