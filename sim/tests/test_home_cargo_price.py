"""Cargo bound for home is sized by the home market's own price response (Complaints/115).

The economy answers what a good's price would be after more of it lands in (or is taken from) the port's market,
by clearing the book that market last cleared with one more order; the engine hands that to the traders as
`price_after_cargo` for home, and the cargo they carry enters the economy's book as orders at the port.
"""
from .harness import *  # noqa: F401,F403

import math

from sim.agents.trader_routes import paying_tonnes, price_answers, route_terms
from sim.agents.tuning_trader import TRADER_RISK_SHARE
from sim.economy import goods_market, market_curves
from sim.economy import year_goods
from sim.economy.api import EDGE_EXTERNAL
from sim.economy.types import Bid, Offer
from sim.engine.agents_port import SimWorld

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

# --- (d) the cargo enters the book: the home price the economy then clears at moves as the quote said.
def clearing_prices(played, years_of_cargo):
    """The price each port market clears at this year, with `years_of_cargo` shipped into it first."""
    seen = {}
    real_clear = goods_market.clear

    def spy(bids, offers, good, area, currency, last_price):
        result = real_clear(bids, offers, good, area, currency, last_price)
        seen[(good, area)] = result
        return result
    year_goods.goods_market.clear = spy
    try:
        world_now = SimWorld(played)
        for material_id, tonnes, landing in years_of_cargo:
            if landing:
                world_now.ship(TRADER, material_id, tonnes, PARTNER, home)
            else:
                world_now.ship(TRADER, material_id, tonnes, home, PARTNER)
        played.step()
    finally:
        year_goods.goods_market.clear = real_clear
    return seen


with_cargo, without = agent_game(), agent_game()
for each in (with_cargo, without):
    each.step()
    each.step()
world = SimWorld(with_cargo)
priced = [m for m in world.trade_materials()
          if world.price_at(m, PARTNER) and world.price_at(m, home) and world.price_after_cargo(m, home, 0.0, True)]
check("a Rome start has goods priced at home and at the partner with a home book", bool(priced), len(priced))
# the good whose market is thickest: a cargo of a tenth of the year's trade moves it measurably
volumes = with_cargo.economy.agent.economy().record.volumes
material = max(priced, key=lambda m: volumes.get(m + "|" + market_curves.port_area(
    with_cargo.economy.agent.economy().area_map, with_cargo.economy.agent.economy().setup.port_tile, m), 0.0))
area = market_curves.port_area(with_cargo.economy.agent.economy().area_map,
                               with_cargo.economy.agent.economy().setup.port_tile, material)
from sim.engine.project_materials import tonnes_per_unit
traded_units = volumes.get(material + "|" + area, 0.0)
tonnes = 0.2 * traded_units * tonnes_per_unit(material)
port_economy = with_cargo.economy.agent.economy()
port_key = material + "|" + area
quote = market_curves.price_response(port_economy.record.curves[port_key], material,
                                     port_economy.record.memory.prices.get(port_key), traded_units * 0.2, 0.0)
national = world.price_after_cargo(material, home, tonnes, True) / world.price_at(material, home)
check("the national price moves by the port's share of the port's move", quote <= national <= 1.0, (quote, national))
cleared_without = clearing_prices(without, [])
cleared_with = clearing_prices(with_cargo, [(material, tonnes, True)])
realised = cleared_with[(material, area)].price / cleared_without[(material, area)].price
check("the cargo shifted the price the economy cleared at, downward", realised < 1.0, (realised, quote))
check("the quote matches the price the economy then clears at, within tolerance",
      abs(realised / quote - 1.0) < 0.10, (realised, quote))
check("the traders' home tally is cleared when the year closes", not with_cargo.state.economy.home_actor_trade, None)
settled = with_cargo.economy.agent.economy().record.book.check_conservation(1e-9)
check("money and goods stay conserved with the cargo in the book", settled.ok, settled.breaches[:3])

# --- (e) home-bound cargo sized by the price settles over the years, with no sign flips.
def home_run(carry, material=None):
    """Six years of a good the partner sells at a third of home's price; traders bring it home as far as it pays when
    `carry`. Returns the good, the cargo each year and the home price at each year's start."""
    played = agent_game()
    played.step()
    played.step()
    world = SimWorld(played)
    home = world._home_place()
    rate = played.market_rate()
    economy = played.economy.agent.economy()
    volumes = economy.record.volumes

    def area_of(m):
        return market_curves.port_area(economy.area_map, economy.setup.port_tile, m)

    if material is None:
        # the good with the most trade at the port among those dear enough per tonne that a gap pays after carriage
        material = max((m for m in world.trade_materials() if world.price_after_cargo(m, home, 0.0, True)
                        and world.price_at(m, home) * 2.0 / 3.0 > 1.2 * world.freight_between(PARTNER, home, m, 1.0)),
                       key=lambda m: volumes.get(m + "|" + area_of(m), 0.0) * played.economy.material_prices()[m])
    cheap_per_unit = played.economy.material_prices()[material] / 3.0
    real_partner_price = played.partner_price_per_unit
    played.partner_price_per_unit = lambda partner, good: cheap_per_unit if good == material else real_partner_price(partner, good)
    # the capital of the traders together buys many times what the market trades in a year
    capital_tonnes = 10.0 * volumes.get(material + "|" + area_of(material), 0.0) * tonnes_per_unit(material)
    backs, prices = [], []
    for _year in range(6):
        world = SimWorld(played)
        terms = route_terms(world, PARTNER, home, material)
        back = 0.0
        if carry and terms is not None and terms["gain"] > 0.0:
            back = paying_tonnes(world, PARTNER, home, material, terms, capital_tonnes, rate)
        prices.append(world.price_at(material, home))
        if back > 0.0:
            world.ship(TRADER, material, back, PARTNER, home)
        backs.append(back)
        played.step()
    return material, backs, prices


material, backs, home_prices = home_run(True)
_same, _none, control_prices = home_run(False, material)
check("cargo bound for home never flips sign once the partner's book has opened (the year after the first)",
      all(back > 0.0 for back in backs[1:]), backs)
check("home-bound cargo stays finite", all(math.isfinite(back) for back in backs), backs)
check("the home price ends below what it does with no cargo", home_prices[-1] < control_prices[-1], (home_prices, control_prices))
