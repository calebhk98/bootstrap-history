"""Complaint 327 (and 412): a state's surplus is not swept out of the economy. Reserve beyond the need it
holds against risk is lent through the loanable-funds market (the state as a saver, earning interest) and
spent on works, a named purchase that hires people; no outlay of the state goes to nobody."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim   # legacy: pins how the engine's budget spends a surplus; the agent-economy budget is test_economy_agent_state.py


from sim.agents.purses import COIN, INTEREST_PAID, LENT
from sim.engine.coin_hoard import KEEPING_CAUSE


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def purchases(treasury):
    """Every purpose a state may pay for: a line it keeps up, or a named purchase or payment."""
    named = {"interest", "patronage", "relief", KEEPING_CAUSE, LENT}
    return set(treasury.record.need) | named | {purpose for purpose in treasury.record.outlays if purpose.startswith("building ")}


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
check("the purse still equals what it held plus income less outlays",
      abs(rich_treasury.money - (1.0e12 + sum(rich_treasury.record.income.values())
                                 - sum(rich_treasury.record.outlays.values()))) < 1e-6 * 1.0e12, rich_treasury.money)

# ---- the state is a saver on the loanable market ------------------------------------------------
saver = sim()
saver_treasury = saver.state_treasury()
saver_treasury.money = 1.0e12
one_year(saver)
check("a state with a reserve beyond its need is a source of funds on the market",
      saver.actors.state.purses.offers.get(saver_treasury.actor_id, 0.0) > 0.0, saver.actors.state.purses.offers)
one_year(saver)
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
paid = borrowed.actors.state.purses.book.money_flow(COIN).get(INTEREST_PAID, 0.0)
check("borrowers paid interest over the years", paid > 0.0, paid)
lent, _rate = borrowed.state_lending()
check("part of what the state supplies is lent, as claims on the borrowers, because they want funds",
      0.0 < lent <= borrowed.actors.state.purses.offers[borrowed_treasury.actor_id],
      (lent, borrowed.actors.state.purses.offers))
check("the claims the state holds are the borrowers' debts",
      abs(lent - borrowed.actors.state.purses.lent(borrowed_treasury.actor_id)) < 1e-6 * lent, lent)
check("the state earned interest on what it lent, no more than borrowers paid",
      0.0 < borrowed_treasury.record.income.get("interest_on_lending", 0.0) <= paid,
      (borrowed_treasury.record.income, paid))
every_receipt = (borrowed_treasury.record.income.get("interest_on_lending", 0.0)
                 + sum(actor.record.income.get("interest_on_lending", 0.0) for actor in borrowed.actors.actors.values()
                       if actor is not borrowed_treasury)
                 + borrowed.state.household.cash_flow.get("interest_on_lending", 0.0))
check("no lender's interest income exceeds what was paid",
      every_receipt <= paid * (1.0 + 1e-9), (every_receipt, paid))
bare = sim()
bare.civ["standing_army"] = 1.0e8  # a need no revenue covers
bare.state_treasury().money = 0.0
one_year(bare)
one_year(bare)
check("a state with no spare reserve lends nothing and earns no interest on lending",
      bare.state_treasury().record.income.get("interest_on_lending", 0.0) == 0.0, bare.state_treasury().record.income)

# ---- a surplus no work wants is kept and lent, not spent on unnamed works --------------------------
stable = sim()
stable_treasury = stable.state_treasury()
for _year in range(25):
    one_year(stable)
check("what the surplus did not spend on named works stays the treasury, which the loanable market is offered, not swept away",
      "works" not in stable_treasury.record.outlays and "discretionary" not in stable_treasury.record.outlays
      and stable.actors.state.purses.offers.get(stable_treasury.actor_id, 0.0) > 0.0,
      (stable_treasury.record.outlays, stable.actors.state.purses.offers))
