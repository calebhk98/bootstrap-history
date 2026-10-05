"""Trader actors own the goods they carry between countries (Complaints/115, folded 405).

A cargo sold to a partner enters that partner's market book, so a gap the traders serve narrows over the
years; and a good the traders carry in a direction is not also carried that way by the economy's stand-in
external orders or by the engine's aggregate foreign flow.
"""
from .harness import *  # noqa: F401,F403

from sim.economy.api import EDGE_EXTERNAL
from sim.agents.tuning_trader import TRADER_DEPTH_SHARE
from sim.engine.agents_port import SimWorld

PARTNER = "han_china_100ad"
TRADER = "trader:test"


def agent_game():
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    return game


def exportable(game):
    """A material dear at the partner, priced both sides, that the partner makes (so its book has capacity)."""
    world = SimWorld(game)
    home = world._home_place()
    facts = game._foreign_economy_facts(PARTNER)
    for material in world.trade_materials():
        gap = (world.price_at(material, PARTNER) or 0.0) - (world.price_at(material, home) or 0.0)
        entry = game._foreign_entry(PARTNER, world.commodity_of(material), facts)
        if gap > 0.0 and entry is not None and entry["capacity_tonnes"] > 0.0:
            return material
    return None


def bid_goods(game):
    orders = game.economy.agent._external_orders()[EDGE_EXTERNAL]
    return {bid.good for bid in orders.bids}, {offer.good for offer in orders.offers}


# --- (a) a gap a trader serves narrows at the partner once its cargo enters the partner's book.
game = agent_game()
material = exportable(game)
check("a Rome start has a good dearer at the partner with a book entry there", material is not None, material)
prices = []
for _year in range(4):
    world = SimWorld(game)
    prices.append(world.price_at(material, PARTNER))
    world.ship(TRADER, material, world.market_depth(material, PARTNER) * TRADER_DEPTH_SHARE, world._home_place(), PARTNER)
    game.close_partner_books()
prices.append(SimWorld(game).price_at(material, PARTNER))
check("the partner's price falls once traders sell it the good, and stays below where it began",
      all(later < prices[0] for later in prices[1:]), prices)
home_price = SimWorld(game).price_at(material, SimWorld(game)._home_place())
check("...so the gap traders serve is narrower than it was",
      prices[-1] - home_price < prices[0] - home_price, (prices[0], prices[-1], home_price))
check("a year's tally is cleared when the partner's book closes", not game.state.economy.foreign_actor_trade, None)

# --- (b) a good traders carry in a direction is not also carried that way by the stand-in external orders.
game = agent_game()
game.economy.open_agent()
bids_before, offers_before = bid_goods(game)
world = SimWorld(game)
carried_out = sorted(bids_before & set(world.trade_materials()))
carried_in = sorted(offers_before & set(world.trade_materials()))
check("the economy's external orders reach goods traders can also carry", bool(carried_out) and bool(carried_in),
      (carried_out[:3], carried_in[:3]))
out_good = carried_out[0]
in_good = next(good for good in carried_in if good != out_good)
world.ship(TRADER, out_good, 1.0, world._home_place(), PARTNER)
world.ship(TRADER, in_good, 1.0, PARTNER, world._home_place())
bids_after, offers_after = bid_goods(game)
check("a good traders export draws no export bid from the economy", out_good not in bids_after, out_good)
check("a good traders import draws no import offer from the economy", in_good not in offers_after, in_good)
check("...while the other goods keep theirs",
      bids_after >= bids_before - {out_good} and offers_after >= offers_before - {in_good}, None)
check("a good traders export may still be imported by the economy (the gap runs one way)",
      (out_good in offers_after) == (out_good in offers_before), out_good)
check("...and a good traders import may still be exported by it",
      (in_good in bids_after) == (in_good in bids_before), in_good)

# --- (c) the engine's own aggregate flow (the agent economy off) leaves a good the actors carry to them.
SILK = "silk_kg"


def engine_game():
    """A game on the engine's own market with a partner dearer than home for every good, at stated terms."""
    game = sim(civ="rome_100ad", capital=1e9, agent_economy=False)
    game.foreign_economies = lambda: [PARTNER]
    game._foreign_price_pair = lambda commodity, facts: (10.0, 100.0)
    game._foreign_sides = lambda commodity, facts: (True, True)
    game._output_is_sourced = lambda commodity: True
    game.foreign_opening = lambda civilization_id, commodity, solved: (
        2 * (game._market_entry(commodity) or {"reference_tonnes": 0.0})["reference_tonnes"],) * 2
    game._route_freight_per_tonne = lambda civilization: 1.0
    game._agent_cost_per_tonne = lambda civilization_id, route: 0.0
    game.foreign_lift_left_tonnes = lambda civilization_id, route: (float("inf"),) * 2
    game.household._foreign_facts_cache = None
    return game


def engine_flows(game):
    entry = game._market_entry(SILK)
    return game.foreign_trade(SILK, entry, game._market_conditions(SILK, entry, True))[1]


game = engine_game()
check("the engine's aggregate flow exports the good to a dearer partner",
      sum(flow for _id, flow, _outcome in engine_flows(game)) < 0.0, engine_flows(game))
game.note_actor_trade(PARTNER, SILK, 1.0, True)
check("...and leaves it alone once actors carry it to that partner", engine_flows(game) == [], engine_flows(game))
