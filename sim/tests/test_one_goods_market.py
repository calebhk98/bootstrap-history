"""Complaints 359 and 364: sellers and buyers go through one goods market, and a good nothing offers has no price
households spend on.

The founder, a firm and the state all deal with `Sim.goods_market`; the same sale is the same entry in the year's flows
whoever makes it, and a good no home technique in reach offers draws no household spending. The rules are
called on a `GoodsMarket` over a stand-in game that holds only what each reads; the sales and takings wiring is in test_one_goods_market_wiring."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from . import module_harness

from sim.tests import market_stand_in
from sim.markets.goods_market import GoodsMarket
from sim.markets.goods_imports import HOME_SELLER
from sim.prices import rules as price_rules
from sim.content import api as content
from sim.engine.data import ROOT
from sim.markets import household_needs
from sim.markets.module import Markets

QUICK_TOPIC = True

MATERIAL = "iron"
FOUNDER = "seat:founder"


def markets_over(game):
    """The markets module over the goods market `game` holds."""
    markets = module_harness.build(Markets, views={"material_commodity": lambda material: material})
    markets.goods_market = game.goods_market
    return markets


def stand_in(**changes):
    """A game for the goods market to read: this year's flows, the asking seat, and (for the offers) the home price table."""
    flows = {"sold": {}, "bought": {}, "drawn": {}}
    values = dict(
        _flows=flows, year=-100, state=SimpleNamespace(acting_seat=FOUNDER, projects=SimpleNamespace()), techniques_held=frozenset,
        **market_stand_in.market_memory(), economy=SimpleNamespace(agent_prices_at=lambda: None),
        _material_prices=lambda: {"wheat_kg": 3.0, "iron": 5.0}, _price_tables=lambda: (None, {"wheat_kg": "solved", "iron": "solved"}),
        _priced_key=lambda material, prices: material if material in prices else None,
        _commodity_materials=lambda commodity: [commodity])
    values.update(changes)
    game = SimpleNamespace(**values)
    game._market_flows = lambda: game._flows
    return game


# --- the same sale moves the clearing price the same way, whoever makes it ------------------------------------
TONNES = 5.0
by_founder, by_firm, untouched = stand_in(), stand_in(), stand_in()
GoodsMarket(by_founder).note_sale(FOUNDER, MATERIAL, TONNES)
GoodsMarket(by_firm).note_sale("firm:1", MATERIAL, TONNES)
check("a sale by the founder and one by a firm are entries of the same kind in the year's flows",
      by_founder._flows["sold"] == {MATERIAL: {FOUNDER: TONNES}} and by_firm._flows["sold"] == {MATERIAL: {"firm:1": TONNES}})
check("the founder has no second path in: the old note methods are gone from the engine",
      not any(hasattr(S.Sim, name) for name in ("market_note_sale", "market_note_purchase", "market_note_draw")))

# --- a buyer other than the founder raises demand in the same book ---------------------------------------------
by_state, by_founder_buying = stand_in(), stand_in()
GoodsMarket(by_state).note_purchase("government:rome", MATERIAL, TONNES)
GoodsMarket(by_founder_buying).note_purchase(FOUNDER, MATERIAL, TONNES)
by_state.goods_market = GoodsMarket(by_state)
by_founder_buying.goods_market = GoodsMarket(by_founder_buying)
check("the state's purchases reach the book as the actors' demand and raise the price",
      abs(markets_over(by_state).actor_demand(MATERIAL) - TONNES) < 1e-9)
check("...while the founder's purchases are his own, not the actors'",
      markets_over(by_founder_buying).actor_demand(MATERIAL) == 0.0)

# --- a good nobody offers has no household price and draws no spending -----------------------------------------
home_only = stand_in()
market_home = GoodsMarket(home_only)
home_only.goods_market = market_home
check("pepper has no price: nothing in reach makes it", price_rules.basis_with_imports(home_only._price_tables()[1].get("pepper_kg"), market_home.offered_by("pepper_kg")) is None)
check("...so it cannot be quoted or bought", not market_home.can_be_bought("pepper_kg"))
check("no home technique in reach offers pepper", market_home.offered_by("pepper_kg") is None)
prices = market_home.household_prices()
check("so households are given no price for it, and a good the home makes keeps its price",
      "pepper_kg" not in prices and prices["wheat_kg"] == 3.0, prices)
check("a good the home makes is sold by the home", market_home.offered_by("wheat_kg") == HOME_SELLER, market_home.offered_by("wheat_kg"))

model, _final_goods = household_needs.household_model((), lambda: content.load_needs(ROOT))
wanted = household_needs.demand_by_material(model, {"wheat_kg": 1.0}, 1_000_000.0, 550.0)
check("a need served by a good nobody prices draws no spending on it", wanted.get("pepper_kg", 0.0) == 0.0, wanted.get("pepper_kg"))
