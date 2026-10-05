"""Complaint 327 (and 412): a state's surplus is not swept out of the economy. Reserve beyond the need it
holds against risk is lent through the loanable-funds market (the state as a saver, earning interest) and
spent on works, a named purchase that hires people; no outlay of the state goes to nobody."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # legacy: pins how the engine's budget spends a surplus; the agent-economy budget is test_economy_agent_state.py


from sim.agents.tuning_spending import RESERVE_CEILING_YEARS_OF_NEED


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def purchases(treasury):
    """Every purpose a state may pay for: a line it keeps up, or a named purchase or payment."""
    return set(treasury.record.need) | {"interest", "patronage", "works", "relief"}


# ---- no outlay without a recipient --------------------------------------------------------------
rich = sim()
rich_treasury = rich.state_treasury()
rich_treasury.money = 1.0e12
for _year in range(4):
    one_year(rich)
check("no state outlay is the sweep that paid no one",
      "discretionary" not in rich_treasury.record.outlays, rich_treasury.record.outlays)
check("every state outlay is a line it keeps up or a named purchase",
      set(rich_treasury.record.outlays) <= purchases(rich_treasury),
      (sorted(rich_treasury.record.outlays), sorted(purchases(rich_treasury))))
check("a reserve beyond what the state holds against risk buys works",
      rich_treasury.record.outlays.get("works", 0.0) > 0.0, rich_treasury.record.outlays)
check("works are people hired out of the labour market, so they are demand",
      rich_treasury.workforce.get("labourer", 0.0) > 0.0, rich_treasury.workforce)
check("the purse still equals what it held plus income less outlays",
      abs(rich_treasury.money - (1.0e12 + sum(rich_treasury.record.income.values())
                                 - sum(rich_treasury.record.outlays.values()))) < 1e-6 * 1.0e12, rich_treasury.money)

# ---- the state is a saver on the loanable market ------------------------------------------------
saver = sim()
saver_treasury = saver.state_treasury()
saver_treasury.money = 1.0e12
one_year(saver)
check("a state with a reserve beyond its need is a source of funds on the market",
      saver.capital_market().supply_by_source.get("state", 0.0) > 0.0, saver.capital_market().supply_by_source)
one_year(saver)
lent, _rate = saver.state_lending()
check("part of what the state supplies is lent, because the market's borrowers want funds",
      0.0 < lent <= saver.capital_market().supply_by_source["state"], (lent, saver.capital_market().supply_by_source))
# a borrower in the market: firms and the founder owe and pay interest, and the lenders are paid exactly that
from sim.engine.state import ActorRecord
borrowed = sim()
borrowed_treasury = borrowed.state_treasury()
borrowed_treasury.money = 1.0e12
for number in range(3):
    borrowed.actors.add("firm:debtor%d" % number, ActorRecord(kind="firm", money=-5.0e7))
borrowed.household.capital = -1.0e6  # the founder owes too
for _year in range(4):
    one_year(borrowed)
market = borrowed.capital_market()
paid = market.interest_paid_total
check("borrowers paid interest over the years", paid > 0.0, paid)
check("what lenders received is what borrowers paid, less what waits in the pool for the next meeting",
      abs(market.interest_received_total + market.interest_pool - paid) < 1e-9 * paid,
      (market.interest_received_total, market.interest_pool, paid))
check("the state earned interest on what it lent, no more than borrowers paid",
      0.0 < borrowed_treasury.record.income.get("interest_on_lending", 0.0) <= paid,
      (borrowed_treasury.record.income, paid))
every_receipt = (borrowed_treasury.record.income.get("interest_on_lending", 0.0) + market.interest_to_households
                 + sum(firm.record.income.get("interest_on_lending", 0.0) for firm in borrowed.actors.active_firms()))
check("no lender's interest income exceeds what was paid",
      every_receipt <= paid * (1.0 + 1e-9), (every_receipt, paid))
bare = sim()
bare.civ["standing_army"] = 1.0e8  # a need no revenue covers
bare.state_treasury().money = 0.0
one_year(bare)
one_year(bare)
check("a state with no spare reserve lends nothing and earns no interest on lending",
      bare.state_treasury().record.income.get("interest_on_lending", 0.0) == 0.0, bare.state_treasury().record.income)

# ---- the reserve does not outgrow its need when the economy is stable ----------------------------
stable = sim()
stable_treasury = stable.state_treasury()
for _year in range(25):
    one_year(stable)
stable_need = sum(stable_treasury.record.need.values())
check("a state in surplus year after year keeps a reserve within a small multiple of its standing need",
      stable_treasury.money <= (RESERVE_CEILING_YEARS_OF_NEED + 1.0) * stable_need,
      (stable_treasury.money, stable_need))
check("what the surplus did not keep went on works, which are demand",
      stable_treasury.record.outlays.get("works", 0.0) > 0.0 and "discretionary" not in stable_treasury.record.outlays,
      stable_treasury.record.outlays)
