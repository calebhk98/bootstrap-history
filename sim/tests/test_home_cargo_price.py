"""Cargo bound for home is sized by the home market's own price response (Complaints/115).

The economy answers what a good's price would be after more of it lands in (or is taken from) the port's market,
by clearing the book that market last cleared with one more order; the engine hands that to the traders as
`price_after_cargo` for home. Once shipped, the cargo is entered in the book as a cargo account's orders and settled
after the clear (`test_trader_cargo_book.py` and `test_trader_cargo_settlement.py` pin that on small fixtures); here a
whole game checks the quote and that a year with cargo posts the foreign coin once.
"""
from .harness import *  # noqa: F401,F403

import math

from sim.agents.trader_routes import paying_tonnes, price_answers, route_terms
from sim.agents.tuning_trader import TRADER_RISK_SHARE
from sim.economy import goods_market, market_curves
from sim.economy import year_goods
from sim.economy.api import EDGE_EXTERNAL
from sim.economy import api as economy_api
from sim.economy.types import Bid, Offer
from sim.engine.agents_port import SimWorld
from sim.engine.project_materials import tonnes_per_unit

PARTNER = "han_china_100ad"
TRADER = "trader:test"


def agent_game():
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    return game


# --- (a) the quote is the market's own clearing: a summarised book re-cleared with the extra order.
buyers = [Bid("a%d" % number, "grain", "area", "tile", 20.0, 40.0, 10.0, 1.5, 5000.0) for number in range(6)]
buyers += [Bid("b%d" % number, "grain", "area", "tile", 0.0, 30.0, 14.0, 0.8, 5000.0, 0, 30.0) for number in range(4)]
sellers = [Offer("s%d" % number, "grain", "area", "tile", 60.0, 4.0 + number) for number in range(8)]
curve = market_curves.summarize(buyers, sellers)
check("a book is summarised into a few rows, not one per order", len(curve["bids"]) <= 2 and len(curve["offers"]) <= 8,
      (len(curve["bids"]), len(curve["offers"])))
base = goods_market.clear(buyers, sellers, "grain", "area", "", None)
for landed, taken in ((30.0, 0.0), (120.0, 0.0), (0.0, 30.0), (0.0, 90.0)):
    quoted = market_curves.price_response(curve, "grain", None, landed, taken)
    extra_offers = sellers + ([Offer("x", "grain", "area", "tile", landed, 0.0)] if landed else [])
    extra_bids = buyers + ([Bid("y", "grain", "area", "tile", taken, 0.0, 0.0, 0.0, math.inf)] if taken else [])
    cleared = goods_market.clear(extra_bids, extra_offers, "grain", "area", "", base.price).price / base.price
    check("the quote for %g landed and %g taken matches the book clearing with it" % (landed, taken),
          quoted is not None and abs(quoted / cleared - 1.0) < 0.05, (quoted, cleared))
more_supply = market_curves.price_response(curve, "grain", None, 120.0, 0.0)
more_demand = market_curves.price_response(curve, "grain", None, 0.0, 90.0)
check("supply landing lowers the price and demand taking raises it", more_supply < 1.0 < more_demand, (more_supply, more_demand))
check("a market that traded nothing has no answer",
      market_curves.price_response({"bids": [], "offers": [[1.0, 5.0]]}, "grain", None, 10.0, 0.0) is None)
check("the external edge's own orders are not part of the summarised book",
      market_curves.summarize([Bid(EDGE_EXTERNAL, "g", "a", "t", 1.0, 0.0, 0.0, 0.0, 1.0)], []) == {"bids": [], "offers": []})

# --- (b) a game on the agent economy answers for home once a year has cleared, and moves with cargo.
game = agent_game()
game.step()
game.step()
world = SimWorld(game)
home = world._home_place()
answering = [material for material in world.trade_materials() if world.price_after_cargo(material, home, 0.0, True) is not None]
check("the home market answers for goods it has a book for", bool(answering), len(world.trade_materials()))
material = answering[0]
price = world.price_at(material, home)
at_zero = world.price_after_cargo(material, home, 0.0, True)
check("with no extra cargo the quote is the market's price", abs(at_zero / price - 1.0) < 1e-9, (at_zero, price))
landed = [world.price_after_cargo(material, home, tonnes, True) for tonnes in (10.0, 1000.0, 100000.0)]
taken = [world.price_after_cargo(material, home, tonnes, False) for tonnes in (10.0, 1000.0, 100000.0)]
check("cargo landed at home pushes its price down, more cargo more so",
      price >= landed[0] >= landed[1] >= landed[2] and landed[2] < price, (price, landed))
check("cargo taken from home pushes its price up, more cargo more so",
      price <= taken[0] <= taken[1] <= taken[2] and taken[2] > price, (price, taken))

# --- (c) a saved game answers the same: the book is in the economy's saved record.
check("the economy's record carries the port books", bool(game.economy.agent.economy().record.curves),
      len(game.economy.agent.economy().record.curves))
record = game.economy.agent.economy().record.to_record()
check("the books survive the record's round trip", record["curves"] == json.loads(json.dumps(record["curves"])),
      None)

# --- (d) a year with trader cargo settles the partner's side once, in the foreign coin ledger.
def coin_imbalance(played):
    """What the home and partner coin ledgers together gained or lost in a year: each coin paid out is one received, so
    it is zero when the year's foreign money is posted once."""
    ledger = played._foreign_ledger(PARTNER)
    standard = S.load_civ(PARTNER)["coin_standard"]
    per_coin = standard["kg_per_unit"] * played._coin_metal_price(standard["material"])
    return ledger["home_coin_units"] + per_coin * ledger["partner_coin_units"], abs(ledger["home_coin_units"]) + 1e-9


with_cargo, without = game, agent_game()
without.step()
without.step()
world = SimWorld(with_cargo)
home = world._home_place()
priced = [m for m in world.trade_materials()
          if world.price_at(m, PARTNER) and world.price_at(m, home) and world.price_after_cargo(m, home, 0.0, True)]
check("a Rome start has goods priced at home and at the partner with a home book", bool(priced), len(priced))
paid_in, received_in = world.ship(TRADER, priced[0], 5.0, PARTNER, home)
paid_out, received_out = world.ship(TRADER, priced[0], 5.0, home, PARTNER)
check("a cargo's money is what the trader books: price times tonnes at each end",
      abs(paid_in - world.price_at(priced[0], PARTNER) * 5.0) < 1e-6 and abs(received_in - world.price_at(priced[0], home) * 5.0) < 1e-6
      and abs(paid_out - world.price_at(priced[0], home) * 5.0) < 1e-6, (paid_in, received_in, paid_out, received_out))
check("the cargo is tallied at home for the quote", with_cargo.actor_home_trade(priced[0]) == (5.0, 5.0),
      with_cargo.actor_home_trade(priced[0]))
orders = with_cargo.economy.agent._external_orders()[EDGE_EXTERNAL]
check("the cargo's legs are noted until the year's market has cleared", len(with_cargo.cargo_legs()) == 2,
      with_cargo.cargo_legs())
check("the cargo adds no order to the economy's external orders",
      all(bid.flexible_quantity > 0.0 for bid in orders.bids) and all(offer.reservation_price > 0.0 for offer in orders.offers), None)
settled_before = dict(with_cargo._foreign_ledger(PARTNER))
with_cargo.step()
without.step()
check("money and goods are conserved in the economy's book with the cargo's year",
      with_cargo.economy.agent.economy().record.book.check_conservation(1e-9).ok, None)
check("the cargo's legs are settled when the year closes", not with_cargo.cargo_legs(), with_cargo.cargo_legs())
extra_in = with_cargo._foreign_ledger(PARTNER)["goods_in_value"] - settled_before["goods_in_value"]
extra_out = with_cargo._foreign_ledger(PARTNER)["goods_out_value"] - settled_before["goods_out_value"]
check("the partner is paid in coin for the cargo brought home, at the booked price at least",
      extra_in >= paid_in * (1.0 - 1e-6), (extra_in, paid_in))
check("the partner pays in coin for the cargo taken from home that the home market sold", extra_out > 0.0, extra_out)
for label, played in (("with", with_cargo), ("without", without)):
    imbalance, scale = coin_imbalance(played)
    check("coin paid between home and the partner is posted once in a year %s trader cargo" % label,
          abs(imbalance) < 1e-6 * scale, (imbalance, scale))
check("the traders' home tally is cleared when the year closes", not with_cargo.state.economy.home_actor_trade, None)

# --- (e) home-bound cargo sized by the price settles over the years, with no sign flips.
def home_run(played):
    """Two years of a good the partner sells at a third of home's price; traders bring it home as far as it pays.
    Returns the cargo each year and whether a quarter more would still have paid."""
    world = SimWorld(played)
    home = world._home_place()
    rate = played.market_rate()
    economy = played.economy.agent.economy()
    volumes = economy.record.volumes

    def area_of(m):
        return market_curves.port_area(economy.area_map, economy.setup.port_tile, m)

    # the good with the most trade at the port among those dear enough per tonne that a gap pays after carriage
    material = max((m for m in world.trade_materials() if world.price_after_cargo(m, home, 0.0, True)
                    and world.price_at(m, home) * 2.0 / 3.0 > 1.2 * world.freight_between(PARTNER, home, m, 1.0)),
                   key=lambda m: volumes.get(m + "|" + area_of(m), 0.0) * played.economy.material_prices()[m])
    cheap_per_unit = played.economy.material_prices()[material] / 3.0
    real_partner_price = played.partner_price_per_unit
    played.partner_price_per_unit = lambda partner, good: cheap_per_unit if good == material else real_partner_price(partner, good)
    # the capital of the traders together buys many times what the market trades in a year
    capital_tonnes = 10.0 * volumes.get(material + "|" + area_of(material), 0.0) * tonnes_per_unit(material)
    backs, marginal = [], []
    for _year in range(2):
        world = SimWorld(played)
        terms = route_terms(world, PARTNER, home, material)
        back = 0.0
        if terms is not None and terms["gain"] > 0.0:
            back = paying_tonnes(world, PARTNER, home, material, terms, capital_tonnes, rate)
        quarter_more = back * 1.25
        marginal.append(back > 0.0 and quarter_more < capital_tonnes and (
            world.price_after_cargo(material, PARTNER, quarter_more, True)
            - world.price_after_cargo(material, home, quarter_more, False) * (1.0 + TRADER_RISK_SHARE + rate)
            - terms["freight"] > 0.0))
        if back > 0.0:
            world.ship(TRADER, material, back, PARTNER, home)
        backs.append(back)
        played.step()
    return backs, marginal


backs, marginal = home_run(without)
check("cargo bound for home never flips sign once the partner's book has opened (the year after the first)",
      all(back > 0.0 for back in backs[1:]), backs)
check("home-bound cargo stays finite", all(math.isfinite(back) for back in backs), backs)
check("each year's cargo is the marginal one at the quote: a quarter more would not pay",
      all(not pays_year for pays_year in marginal), marginal)
