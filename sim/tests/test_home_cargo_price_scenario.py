"""Scenarios: cargo bound for home is sized by the home market's own price response (Complaints/115). The quote's
rules are in test_home_cargo_price.

The economy answers what a good's price would be after more of it lands in (or is taken from) the port's market,
by clearing the book that market last cleared with one more order; the engine hands that to the traders as
`price_after_cargo` for home. Once shipped, the cargo is entered in the book as a cargo account's orders and settled
after the clear (`test_trader_cargo_book.py` and `test_trader_cargo_settlement.py` pin that on small fixtures); here a
whole game checks the quote and that a year with cargo posts the foreign coin once.
"""
from .harness import *  # noqa: F401,F403

import math

from sim.agents.trader_routes import paying_tonnes, route_terms
from sim.agents.tuning_trader import TRADER_RISK_SHARE
from sim.economy import market_curves
from sim.economy.api import EDGE_EXTERNAL
from sim.engine.agents_port import SimWorld
from sim.engine.material_units import tonnes_per_unit
from sim.engine import foreign_economies as foreign_module

# the partner book is how a partner outside the agent economy trades, so the shipped Han (now inside it) is put outside
_RECORDS = foreign_module.foreign_economy_records()
foreign_module.foreign_economy_records = lambda: tuple(
    dict(record, agent_economy=False) if record["civilization"] == "han_china_100ad" else record for record in _RECORDS)
# ...and, having no economy of its own to answer for its people, it has no cast of its own in the years played here
from sim.engine import agents_port_cast
agents_port_cast.opening_cast = lambda sim: agents_port_cast.cast_from_civilisations(sim.civ, [])

PARTNER = "han_china_100ad"
TRADER = "trader:test"


def agent_game():
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
    game.goal, game.done_year = GOAL, {}
    return game


_settle_flow = S.Sim._settle_flow


def _recording_settle_flow(self, civilization_id, flow_tonnes, value, home_money_per_partner_coin):
    """Settle as the engine does and note what the partner's ledger gained or lost, at the rate of the posting."""
    ledger = self._foreign_ledger(civilization_id, create=True)
    before = (ledger["home_coin_units"], ledger["partner_coin_units"])
    _settle_flow(self, civilization_id, flow_tonnes, value, home_money_per_partner_coin)
    postings = self.__dict__.setdefault("_test_postings", [])
    postings.append((ledger["home_coin_units"] - before[0], ledger["partner_coin_units"] - before[1],
                     home_money_per_partner_coin, abs(ledger["home_coin_units"] - before[0])))


S.Sim._settle_flow = _recording_settle_flow


# --- (b) a game on the agent economy answers for home once a year has cleared, and moves with cargo.
game = agent_game()
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
    """What the home and partner coin ledgers together gained or lost in a year, each posting valued at its own
    rate (the coin metal's price moves as the year closes): each coin paid out is one received, so it is zero
    when the year's foreign money is posted once. Returns (imbalance, scale)."""
    postings = played.__dict__.get("_test_postings", [])
    return (sum(home + rate * partner for home, partner, rate, _paid in postings),
            sum(paid for _home, _partner, _rate, paid in postings) + 1e-9)


with_cargo = game
imbalance_without_cargo = coin_imbalance(with_cargo)   # the year played so far carried no trader cargo
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
check("money and goods are conserved in the economy's book with the cargo's year",
      with_cargo.economy.agent.economy().record.book.check_conservation(1e-9).ok, None)
check("the cargo's legs are settled when the year closes", not with_cargo.cargo_legs(), with_cargo.cargo_legs())
extra_in = with_cargo._foreign_ledger(PARTNER)["goods_in_value"] - settled_before["goods_in_value"]
extra_out = with_cargo._foreign_ledger(PARTNER)["goods_out_value"] - settled_before["goods_out_value"]
check("the partner is paid in coin for the cargo brought home, at the booked price at least",
      extra_in >= paid_in * (1.0 - 1e-6), (extra_in, paid_in))
check("the partner pays in coin for the cargo taken from home that the home market sold", extra_out > 0.0, extra_out)
for label, (imbalance, scale) in (("with", coin_imbalance(with_cargo)), ("without", imbalance_without_cargo)):
    check("coin paid between home and the partner is posted once in a year %s trader cargo" % label,
          scale > 1.0 and abs(imbalance) < 1e-6 * scale, (imbalance, scale))
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
    for year in range(2):
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
        if year == 0:   # the second year's cargo is read before anything else would happen, so it is not played out
            played.step()
    return backs, marginal


backs, marginal = home_run(with_cargo)
check("cargo bound for home never flips sign once the partner's book has opened (the year after the first)",
      all(back > 0.0 for back in backs[1:]), backs)
check("home-bound cargo stays finite", all(math.isfinite(back) for back in backs), backs)
check("each year's cargo is the marginal one at the quote: a quarter more would not pay",
      all(not pays_year for pays_year in marginal), marginal)
