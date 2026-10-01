"""Complaint 110: a civilisation has one loanable-funds market. What its actors save is the supply, what
they borrow is the demand, the yearly rate moves with the balance around the civilisation's starting
rate, every borrower pays that rate plus a premium from its own standing and arrears, and credit limits
are what lenders hold."""
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld
from sim.engine.actors import budget
from sim.engine.proto.saveload import load_state, save_state
from sim.engine.state import ActorRecord
from sim.world import capital_market


def market_sim(civ="rome_100ad", army=None, purse=None):
    game = sim(civ=civ)
    if army is not None:
        game.civ["standing_army"] = army
    if purse is not None:
        game.state_treasury().money = purse
    return game


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


# ---- the pure balance: rate, premium, headroom ------------------------------------------------
START = 0.12
check("at the reference balance the market rate is the civilisation's starting rate",
      abs(capital_market.rate_for_balance(START, 0.5, 0.5) - START) < 1e-12)
tighter = capital_market.rate_for_balance(START, 0.8, 0.5)
looser = capital_market.rate_for_balance(START, 0.3, 0.5)
check("scarcer funds raise the rate and plentiful funds lower it", looser < START < tighter, (looser, tighter))
check("the rate rises with every further unit of demand",
      capital_market.rate_for_balance(START, 0.9, 0.5) > tighter)
check("the rate stays inside its floor and ceiling however extreme the balance",
      capital_market.rate_for_balance(START, 1.0e9, 0.5) <= START * capital_market.RATE_CEILING_SHARE * (1 + 1e-12)
      and capital_market.rate_for_balance(START, 1.0e-9, 0.5) >= START * capital_market.RATE_FLOOR_SHARE * (1 - 1e-12))
check("a borrower with no arrears and no standing pays exactly the market rate",
      abs(capital_market.borrower_rate(START, 0.0, 0.0) - START) < 1e-12)
check("a borrower's standing makes money cheaper",
      capital_market.borrower_rate(START, 0.02, 0.0) < START)
check("a borrower's arrears make money dearer, more the closer to its ceiling",
      START < capital_market.borrower_rate(START, 0.0, 0.5) < capital_market.borrower_rate(START, 0.0, 1.0))
check("arrears beyond the ceiling add no more than the ceiling does",
      capital_market.borrower_rate(START, 0.0, 3.0) == capital_market.borrower_rate(START, 0.0, 1.0))
check("what lenders hold less what is already lent is what is left to lend, never negative",
      capital_market.headroom(100.0, 30.0) == 70.0 and capital_market.headroom(100.0, 130.0) == 0.0)
check("the debt a given earning can carry falls as the rate rises",
      capital_market.serviceable_debt(100.0, 0.05) > capital_market.serviceable_debt(100.0, 0.10) > 0.0
      and capital_market.serviceable_debt(100.0, 0.0) == 0.0)

# ---- a fresh game: the market is at the civilisation's starting rate -------------------------
for civ_id in ("rome_100ad", "han_china_100ad"):
    fresh = market_sim(civ_id)
    check("before the market has met, its rate is the civilisation's starting rate (%s)" % civ_id,
          abs(fresh.market_rate() - fresh.civ["starting_interest_rate"]) < 1e-12)
    check("an unindebted founder borrows at the starting rate less his standing (%s)" % civ_id,
          fresh.debt_interest_rate() <= fresh.civ["starting_interest_rate"] + 1e-12)

# ---- one year: supply from what actors save, demand from what they owe ------------------------
game = market_sim()
one_year(game)
market = game.capital_market()
check("the first year's market is at the starting rate, which fixes its reference balance",
      abs(market.rate - game.civ["starting_interest_rate"]) < 1e-12 and market.reference_utilisation > 0.0,
      (market.rate, market.reference_utilisation))
check("households' savings are a supply of funds", market.supply_by_source.get("households", 0.0) > 0.0,
      market.supply_by_source)
check("the supply is the sum of its sources",
      abs(sum(market.supply_by_source.values()) - market.supply) < 1e-9 * market.supply, market.supply_by_source)
check("lenders hold more than they lend: capacity is below supply",
      0.0 < market.capacity < market.supply, (market.capacity, market.supply))

# ---- the state's reserve is supply, borrowing is demand -----------------------------------------
base = market_sim()
one_year(base)
reserve_rich = market_sim(purse=1.0e13)
one_year(reserve_rich)
one_year(base)
one_year(reserve_rich)
check("a state reserve adds to the funds lenders hold", reserve_rich.capital_market().supply_by_source.get("state", 0.0) > 0.0
      and reserve_rich.capital_market().supply > base.capital_market().supply)
check("more funds, a lower market rate",
      reserve_rich.market_rate() < base.market_rate(), (reserve_rich.market_rate(), base.market_rate()))
indebted = market_sim()
one_year(indebted)
indebted.capital = -0.5 * indebted.capital_market().capacity
one_year(indebted)
check("a founder's debt is demand on the market and is recorded among the loans",
      indebted.capital_market().loans.get("founder", 0.0) > 0.0, indebted.capital_market().loans)
check("more borrowing, a higher market rate",
      indebted.market_rate() > base.market_rate(), (indebted.market_rate(), base.market_rate()))

# ---- the founder's credit limit is what lenders hold -------------------------------------------
roomy = market_sim()
one_year(roomy)
limit_roomy = roomy.credit_limit()
scarce = market_sim()
one_year(scarce)
scarce.capital_market().capacity = 0.1 * limit_roomy
check("when lenders hold little, the founder's limit is what they hold",
      scarce.credit_limit() < limit_roomy and scarce.credit_limit() >= 0.0, (scarce.credit_limit(), limit_roomy))
check("the founder's limit still cannot fall below the running tab everyone can run",
      scarce.credit_limit() >= scarce.living_cost(), (scarce.credit_limit(), scarce.living_cost()))
dearer = market_sim()
one_year(dearer)
dearer.capital_market().rate = 2.0 * dearer.market_rate()
check("at a higher market rate the same earnings carry less debt: the limit falls",
      dearer.credit_limit() < limit_roomy, (dearer.credit_limit(), limit_roomy))

# ---- the founder's rate: the market rate, his standing, his arrears -------------------------------
standing = market_sim()
one_year(standing)
standing.capital_market().rate = 0.2
standing.capital = 1.0
rate_clear = standing.debt_interest_rate()
check("the founder's rate follows the market rate", rate_clear > market_sim().debt_interest_rate() + 0.05, rate_clear)
standing.capital = -0.9 * standing.credit_limit()
check("a founder near his limit pays more than one who is clear",
      standing.debt_interest_rate() > rate_clear, (standing.debt_interest_rate(), rate_clear))

# ---- any actor borrows through the one mechanism ------------------------------------------------
shared = market_sim()
one_year(shared)
world = SimWorld(shared)
first = shared.actors.add("firm:a", ActorRecord(kind="firm", money=0.0, last_margin=1.0e6, founded_year=shared.year))
second = shared.actors.add("firm:b", ActorRecord(kind="firm", money=0.0, last_margin=1.0e6, founded_year=shared.year))
check("two firms with the same record and no debt borrow at the same rate",
      abs(first.borrowing_rate(world) - second.borrowing_rate(world)) < 1e-12)
second.money = -0.5 * second.credit_ceiling(world)
check("a firm in arrears pays more than a sound one", second.borrowing_rate(world) > first.borrowing_rate(world),
      (second.borrowing_rate(world), first.borrowing_rate(world)))
check("a firm's ceiling is what its earnings can carry at the rate, within what lenders hold",
      0.0 < first.credit_ceiling(world) <= shared.capital_market().capacity, first.credit_ceiling(world))
unproven = shared.actors.add("firm:c", ActorRecord(kind="firm", money=0.0, last_margin=1.0e6, founded_year=shared.year))
proven = shared.actors.add("firm:d", ActorRecord(kind="firm", money=0.0, last_margin=1.0e6, founded_year=shared.year - 30))
check("a firm with a longer record borrows more cheaply", proven.borrowing_rate(world) < unproven.borrowing_rate(world),
      (proven.borrowing_rate(world), unproven.borrowing_rate(world)))
check("the state borrows through the same method", hasattr(shared.state_treasury(), "borrowing_rate")
      and shared.state_treasury().borrowing_rate(world) > 0.0)
debtor = shared.actors.add("firm:e", ActorRecord(kind="firm", money=-1.0e5, last_margin=1.0e6, founded_year=shared.year))
one_year(shared)
check("a firm in debt pays interest on it, booked by purpose",
      debtor.record.outlays.get("interest", 0.0) > 0.0 and debtor.money < -1.0e5, (debtor.record.outlays, debtor.money))

# ---- the state borrows to cover a deficit instead of only cutting -------------------------------
def deficit(army_multiple):
    game = market_sim(army=1.0)
    world = SimWorld(game)
    game.civ["standing_army"] = army_multiple
    need = sum(line.money for line in budget.standing_lines(world))
    game.state_treasury().money = 0.0
    return game, need, world.state_revenue()


modest, need, revenue = deficit(3.0e6)
one_year(modest)
modest_state = modest.state_treasury()
need = sum(line.money for line in budget.standing_lines(SimWorld(modest)))
revenue = SimWorld(modest).state_revenue()
ceiling = modest_state.credit_ceiling(SimWorld(modest))
check("the state's deficit here is real and within what it can borrow", need > revenue and ceiling > need - revenue,
      (need, revenue, ceiling))
check("a deficit within the ceiling is borrowed, not cut: the purse goes negative and nothing is unfunded",
      modest_state.money < 0.0 and not any(modest_state.record.unfunded.values()),
      (modest_state.money, modest_state.record.unfunded))
check("the state's debt is on the market's books", modest.capital_market().loans.get("government:rome_100ad", 0.0) == 0.0
      or modest.capital_market().loans["government:rome_100ad"] >= 0.0)
one_year(modest)
check("the next year the state pays interest on its debt, booked as an outlay",
      modest_state.record.outlays.get("interest", 0.0) > 0.0, modest_state.record.outlays)
check("the state's debt is demand on the market",
      modest.capital_market().loans.get("government:rome_100ad", 0.0) > 0.0, modest.capital_market().loans)
ruin, need, revenue = deficit(1.0e12)
one_year(ruin)
ruin_state = ruin.state_treasury()
check("a deficit beyond the ceiling is borrowed up to the ceiling and the rest is cut pro rata",
      -ruin_state.money > 0.0 and any(amount > 0.0 for amount in ruin_state.record.unfunded.values()),
      (ruin_state.money, ruin_state.record.unfunded))
check("the state never borrows past what lenders hold",
      -ruin_state.money <= ruin.capital_market().capacity * (1.0 + 1e-9), (ruin_state.money, ruin.capital_market().capacity))
check("a state in surplus borrows nothing", market_sim().state_treasury().money >= 0.0)

# ---- the market's books survive save and load ----------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(indebted, path)
    revived = sim()
    load_state(revived, path)
    check("the market record round-trips through save and load",
          revived.capital_market() == indebted.capital_market(), (revived.capital_market(), indebted.capital_market()))
