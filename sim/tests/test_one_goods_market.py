"""Complaints 359 and 364: sellers and buyers go through one goods market, and a good nothing offers has no price
households spend on.

The founder, a firm and the state all deal with `Sim.goods_market`; the same sale moves the clearing price the same way
whoever makes it, and a good no home technique in reach and no partner offers draws no household spending. The rules are
called on a `GoodsMarket` over a stand-in game that holds only what each reads; the sales and takings wiring is in test_one_goods_market_wiring."""
from types import SimpleNamespace
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.engine import goods_market_offers
from sim.engine.goods_market_api import GoodsMarket
from sim.engine.goods_market_imports import HOME_SELLER
from sim.prices import rules as price_rules
from sim.engine.market_clearing import MarketClearingMixin
from sim.engine.market_demand import household_demand_by_material
from sim.engine.material_units import tonnes_per_unit
from sim.engine.society_actors import ActorsMixin
from sim.world import market

QUICK_TOPIC = True

MATERIAL = "iron"
FOUNDER = "seat:founder"


def stand_in(**changes):
    """A game for the goods market to read: this year's flows, the asking seat, and (for the offers) the home price table
    and one partner, Han, that makes cassia and wheat."""
    flows = {"sold": {}, "bought": {}, "drawn": {}, "reservation": {}}
    facts = {"solved_materials": {"cassia_kg", "wheat_kg"}, "prices_in_home_money": {"cassia_kg": 2.0, "wheat_kg": 9.0}}
    route = SimpleNamespace(cost_per_tonne=40.0)
    values = dict(
        _flows=flows, state=SimpleNamespace(acting_seat=FOUNDER, projects=SimpleNamespace(done=[]),
                                            scenario=SimpleNamespace(year=-100)),
        household=SimpleNamespace(), economy=SimpleNamespace(agent_prices_at=lambda: None),
        _material_prices=lambda: {"wheat_kg": 3.0, "iron": 5.0}, _price_tables=lambda: (None, {"wheat_kg": "solved", "iron": "solved"}),
        foreign_economies=lambda: ["han"], _foreign_economy_facts=lambda partner: facts, _foreign_route=lambda civ: route,
        partner_civ=lambda partner: {}, partner_price_level=lambda partner: 1.0, market_rate=lambda: 0.05,
        _trader_margin_share=lambda partner, route: 0.10, _cargo_lost_share=lambda route, material, partner: 0.02,
        _trader_cycle_years=lambda route, partner: 1.0, _agent_cost_per_tonne=lambda partner, route: 10.0,
        foreign_supply_tonnes=lambda partner, material: 500.0,
        _priced_key=lambda material, prices: material if material in prices else None,
        _commodity_materials=lambda commodity: [commodity])
    values.update(changes)
    game = SimpleNamespace(**values)
    game._market_flows = lambda: game._flows
    return game


def figures(game, with_flows):
    game.goods_market = GoodsMarket(game)
    game.founder_concern_offers = lambda commodity: ()
    return MarketClearingMixin._market_flow_figures(game, MATERIAL, with_flows)


def cleared(committed=0.0, founder_sales=0.0, actor_supply=0.0, actor_demand=0.0):
    return market.clear_market(market.MarketConditions(
        household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=committed, society_capacity_tonnes=100.0,
        actor_supply_tonnes=actor_supply, actor_demand_tonnes=actor_demand, founder_sales_tonnes=founder_sales,
        stock_tonnes=0.0, demand_price_elasticity=0.5, floor_ratio=0.4, ceiling_ratio=6.0))


# --- the same sale moves the clearing price the same way, whoever makes it ------------------------------------
TONNES = 5.0
by_founder, by_firm, untouched = stand_in(), stand_in(), stand_in()
GoodsMarket(by_founder).note_sale(FOUNDER, MATERIAL, TONNES)
GoodsMarket(by_firm).note_sale("firm:1", MATERIAL, TONNES)
check("a sale by the founder and one by a firm are entries of the same kind in the year's flows",
      by_founder._flows["sold"] == {MATERIAL: {FOUNDER: TONNES}} and by_firm._flows["sold"] == {MATERIAL: {"firm:1": TONNES}})
founder_committed, founder_sales, founder_supply, _d, _o = figures(by_founder, with_flows=True)
firm_committed, firm_sales, firm_supply, _d, _o = figures(by_firm, with_flows=True)
founder_price = cleared(committed=founder_committed, founder_sales=founder_sales, actor_supply=founder_supply).price_ratio
firm_price = cleared(committed=firm_committed, founder_sales=firm_sales, actor_supply=firm_supply).price_ratio
check("a sale by the founder lowers the price the year would close at",
      founder_price < cleared().price_ratio - 1e-6, (founder_price, cleared().price_ratio))
check("...and the same sale by a firm moves it exactly the same way", abs(founder_price - firm_price) < 1e-12,
      (founder_price, firm_price))
check("a firm's sales are in the posted price; the founder's own orders stay out of it",
      figures(by_firm, with_flows=False)[2] == TONNES and figures(by_founder, with_flows=False)[1:3] == (0.0, 0.0),
      (figures(by_firm, with_flows=False), figures(by_founder, with_flows=False)))
check("the founder has no second path in: the old note methods are gone from the engine",
      not any(hasattr(S.Sim, name) for name in ("market_note_sale", "market_note_purchase", "market_note_draw")))

# --- a buyer other than the founder raises demand in the same book ---------------------------------------------
by_state, by_founder_buying = stand_in(), stand_in()
GoodsMarket(by_state).note_purchase("government:rome", MATERIAL, TONNES)
GoodsMarket(by_founder_buying).note_purchase(FOUNDER, MATERIAL, TONNES)
by_state.goods_market = GoodsMarket(by_state)
by_founder_buying.goods_market = GoodsMarket(by_founder_buying)
check("the state's purchases reach the book as the actors' demand and raise the price",
      abs(ActorsMixin.actor_demand(by_state, MATERIAL) - TONNES) < 1e-9
      and cleared(actor_demand=ActorsMixin.actor_demand(by_state, MATERIAL)).price_ratio > cleared().price_ratio)
check("...while the founder's purchases are his own, not the actors'",
      ActorsMixin.actor_demand(by_founder_buying, MATERIAL) == 0.0
      and figures(by_founder_buying, with_flows=False)[0] == 0.0 and figures(by_founder_buying, with_flows=True)[0] == TONNES,
      (figures(by_founder_buying, False), figures(by_founder_buying, True)))

# --- a good nobody offers has no household price and draws no spending -----------------------------------------
no_tariff = mock.patch.object(goods_market_offers.trade_duty, "import_terms", lambda game, partner: (0.0, False))
signature = mock.patch.object(goods_market_offers.trade_duty, "signature", lambda game, partners: ())
with no_tariff, signature:
    home_only = stand_in(foreign_economies=lambda: [])
    market_home = GoodsMarket(home_only)
    home_only.goods_market = market_home
    check("pepper has no price: nothing in reach makes it", price_rules.basis_with_imports(home_only._price_tables()[1].get("pepper_kg"), market_home.offered_by("pepper_kg")) is None)
    check("...so it cannot be quoted or bought", not market_home.can_be_bought("pepper_kg"))
    check("no home technique in reach and no partner offers pepper", market_home.offered_by("pepper_kg") is None)
    prices = market_home.household_prices()
    check("so households are given no price for it, and a good the home makes keeps its price",
          "pepper_kg" not in prices and prices["wheat_kg"] == 3.0, prices)
    check("a commodity nobody offers is unsourced, and one the home makes is not",
          market_home.commodity_is_unsourced("pepper_kg") and not market_home.commodity_is_unsourced("wheat_kg"))

    # a partner that makes cassia, which no home technique does: an import at the landed price
    partnered = stand_in()
    partnered.goods_market = GoodsMarket(partnered)
    partnered_prices = partnered.goods_market.household_prices()
    check("a partner offers cassia, so it is an import and can be bought",
          partnered.goods_market.offered_by("cassia_kg") == "han"
          and price_rules.basis_with_imports(partnered._price_tables()[1].get("cassia_kg"), partnered.goods_market.offered_by("cassia_kg")) == "imported"
          and partnered.goods_market.can_be_bought("cassia_kg"), partnered.goods_market.offered_by("cassia_kg"))
    cost = 2.0 * 1.0
    share = partnered.goods_market.merchants_cost_share(partnered._foreign_route(None), None, "han")
    landed = cost * (1.0 + share) + (40.0 + 10.0) * tonnes_per_unit("cassia_kg")
    check("...and households pay what it costs the partner plus the merchants' terms plus freight",
          abs(partnered_prices["cassia_kg"] - landed) < 1e-9 * landed, (partnered_prices["cassia_kg"], landed))
    check("a good the home makes is still sold by the home when a partner makes it too, unless the partner is cheaper",
          partnered.goods_market.offered_by("wheat_kg") == HOME_SELLER, partnered.goods_market.offered_by("wheat_kg"))

wanted = household_demand_by_material({"wheat_kg": 1.0}, 1_000_000.0, 550.0)
check("a need served by a good nobody prices draws no spending on it", wanted.get("pepper_kg", 0.0) == 0.0, wanted.get("pepper_kg"))
