"""Trader actors own the goods they carry between countries (Complaints/115, folded 405).

A cargo sold to a partner enters that partner's market book, so a gap the traders serve narrows over the
years; and a good the traders carry in a direction is not also carried that way by the economy's stand-in
external orders.
"""
from .harness import *  # noqa: F401,F403

from sim.economy.api import EDGE_EXTERNAL
from sim.agents.trader import depth_room
from sim.agents.trader_routes import paying_tonnes, price_answers, route_terms
from sim.agents.tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE
from sim.engine.agents_port import SimWorld

PARTNER = "han_china_100ad"
TRADER = "trader:test"


def agent_game():
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
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
    """The goods the stand-in external orders reach; the actors' own cargo orders (no price schedule, offers at any
    price) are not the stand-in's."""
    orders = game.economy.agent._external_orders()[EDGE_EXTERNAL]
    return ({bid.good for bid in orders.bids if bid.flexible_quantity > 0.0},
            {offer.good for offer in orders.offers if offer.reservation_price > 0.0})


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

# --- (c) a cargo sized against the price it makes settles: no flips, and the partner's price stops at the band freight sets.
game = agent_game()
world = SimWorld(game)
home = world._home_place()
rate = game.market_rate()
candidates = []
for material in world.trade_materials():
    terms = route_terms(world, home, PARTNER, material)
    entry = game._foreign_entry(PARTNER, world.commodity_of(material), game._foreign_economy_facts(PARTNER))
    if terms and entry and entry["capacity_tonnes"] > 0.0 and terms["gain"] > terms["bought"] * (rate + 0.05):
        candidates.append((terms["gain"] / terms["bought"], material))
check("a Rome start has a gap with the partner wide enough to pay the interest on the cargo", bool(candidates), None)


def payable(material):
    """Tonnes of a cargo of the material that still pays on the route out."""
    terms = route_terms(world, home, PARTNER, material)
    return paying_tonnes(world, home, PARTNER, material, terms, 1e12 / terms["outlay"], rate)


material = max(candidates, key=lambda pair: payable(pair[1]))[1]
check("...and a cargo of the widest-paying good pays", payable(material) > 0.0, material)


def cargo_for(world, source, destination):
    """What a trader with ample capital would carry on the route: as far as it still pays."""
    terms = route_terms(world, source, destination, material)
    if terms is None or terms["gain"] <= 0.0:
        return 0.0
    tonnes = 1e12 / terms["outlay"]
    if price_answers(world, material, destination):
        return paying_tonnes(world, source, destination, material, terms, tonnes, rate)
    return min(depth_room(world, source, destination, material), tonnes)


signed, partner_prices, taken_from_home = [], [], []
for _year in range(8):
    world = SimWorld(game)
    out, back = cargo_for(world, home, PARTNER), cargo_for(world, PARTNER, home)
    partner_prices.append(world.price_at(material, PARTNER))
    if out:
        world.ship(TRADER, material, out, home, PARTNER)
    if back:
        world.ship(TRADER, material, back, PARTNER, home)
    signed.append(out - back)
    taken_from_home.append(out)
    game.close_partner_books()
world = SimWorld(game)
home_price = world.price_at(material, home)
# the cargo is bought at home too, so what it pays is the home price after the cargo is taken; the home book moves in
# steps (its sellers' reservations), so the cargo is the marginal one that pays rather than a price reached exactly
home_price_after = world.price_after_cargo(material, home, taken_from_home[-1], False) or home_price


def pays(cargo):
    sold = world.price_after_cargo(material, PARTNER, cargo, True)
    bought = world.price_after_cargo(material, home, cargo, False)
    return sold - bought * (1.0 + TRADER_RISK_SHARE + rate) - world.freight_between(home, PARTNER, material, 1.0) > 0.0


check("the cargo always goes the way of the gap: it never flips sign", all(flow > 0.0 for flow in signed), signed)
check("the partner's price falls from where it began and stays above the home price it is bought at",
      all(home_price < price < partner_prices[0] for price in partner_prices[1:]), (partner_prices, home_price))
check("...a quarter more cargo than the last year's would not pay at the prices it meets, and the cargo itself does",
      pays(taken_from_home[-1]) and not pays(taken_from_home[-1] * 1.25), taken_from_home)
check("...and cargo taken from home raises the home price the trader pays", home_price_after > home_price,
      (home_price_after, home_price))
check("...and no longer swings from year to year",
      all(abs(later / earlier - 1.0) < 0.01 for earlier, later in zip(partner_prices[1:], partner_prices[2:])),
      partner_prices)
