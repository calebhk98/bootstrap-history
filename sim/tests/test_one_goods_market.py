"""Complaints 359 and 364: a good nothing offers has no price households spend on.

A good no home technique in reach offers draws no household spending. The rules are
called on a `GoodsMarket` over a stand-in game that holds only what each reads; the sales and takings wiring is in test_one_goods_market_wiring."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.tests import market_stand_in
from sim.markets.goods_market import GoodsMarket
from sim.prices.rules import HOME_SELLER
from sim.prices import rules as price_rules
from sim.content import api as content
from sim.engine.data import ROOT
from sim.markets import household_needs

QUICK_TOPIC = True

FOUNDER = "seat:founder"


def stand_in(**changes):
    """A game for the goods market to read: this year's flows, the asking seat, and (for the offers) the home price table."""
    flows = {"sold": {}, "bought": {}, "drawn": {}}
    values = dict(
        _flows=flows, year=-100, state=SimpleNamespace(acting_seat=FOUNDER, projects=SimpleNamespace()), techniques_held=frozenset,
        **market_stand_in.market_memory(), economy=SimpleNamespace(agent_prices_at=lambda: None),
        materials=SimpleNamespace(
            prices=lambda: {"wheat_kg": 3.0, "iron": 5.0},
            priced_key=lambda material, prices: material if material in prices else None,
            commodity_materials=lambda commodity: [commodity]),
        _price_tables=lambda: (None, {"wheat_kg": "solved", "iron": "solved"}))
    values.update(changes)
    game = SimpleNamespace(**values)
    game.market_flows = lambda: game._flows
    return game


# --- a good nobody offers has no household price and draws no spending -----------------------------------------
home_only = stand_in()
market_home = GoodsMarket(home_only)
home_only.goods_market = market_home
check("pepper has no price: nothing in reach makes it", price_rules.basis_with_imports(home_only._price_tables()[1].get("pepper_kg"), market_home.offers.offered_by("pepper_kg")) is None)
check("...so it cannot be quoted or bought", not market_home.offers.can_be_bought("pepper_kg"))
check("no home technique in reach offers pepper", market_home.offers.offered_by("pepper_kg") is None)
prices = market_home.offers.household_prices()
check("so households are given no price for it, and a good the home makes keeps its price",
      "pepper_kg" not in prices and prices["wheat_kg"] == 3.0, prices)
check("a good the home makes is sold by the home", market_home.offers.offered_by("wheat_kg") == HOME_SELLER, market_home.offers.offered_by("wheat_kg"))

model, _final_goods = household_needs.household_model((), lambda: content.load_needs(ROOT))
wanted = household_needs.demand_by_material(model, {"wheat_kg": 1.0}, 1_000_000.0, 550.0)
check("a need served by a good nobody prices draws no spending on it", wanted.get("pepper_kg", 0.0) == 0.0, wanted.get("pepper_kg"))
