"""Scenarios for Complaint 316 in a whole game: a Rome state with an army its revenue cannot carry borrows only once it
holds the technology of public debt, or has it in its baseline knowledge. The gate itself (the credit ceiling, the
menu's borrow option) is test_state_borrowing_gate."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.agents import budget


# The settled opening leaves the households nothing to save (Complaints 607, 645), so no lender has room for the state. These
# scenarios are about the gate, not about the lenders, so they state the room lenders have for one borrower and the
# rate they lend at (the civilisation's own, not the ceiling the empty market sits at).
LENDERS_ROOM = 5.0e10


def with_lenders(game):
    game.market_credit_room = lambda actor_id: LENDERS_ROOM
    game.market_rate = lambda: float(game.civ["starting_interest_rate"])
    return game


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def army_between_revenue_and_credit():
    """An army whose bill is half of what the state could borrow against its revenue once it holds the
    technology: more than its revenue carries, less than its credit could."""
    game = with_lenders(sim())
    treasury = game.state_treasury()
    treasury.knowledge.add(game.nodes_with_mechanic("state_credit")[0])
    world = SimWorld(game)
    bill = lambda soldiers: sum(line.money for line in budget.standing_lines(world, soldiers))
    fixed_bill = bill(0.0)
    bill_per_soldier = bill(1.0) - fixed_bill
    return (0.5 * treasury.credit_ceiling(world) - fixed_bill) / bill_per_soldier


ARMY = army_between_revenue_and_credit()


def deficit_game(holds_node=False, baseline=False):
    """Rome with an army its revenue cannot carry but its credit could, and an empty purse."""
    game = with_lenders(sim())
    game.civ["standing_army"] = ARMY
    treasury = game.state_treasury()
    treasury.money = 0.0
    node = game.nodes_with_mechanic("state_credit")[0]
    if holds_node:
        treasury.knowledge.add(node)
    if baseline:
        game.state.projects.granted.add(node)
    return game, treasury


early, early_treasury = deficit_game()
one_year(early)
check("a state without the technology does not borrow: its purse never goes below nothing",
      early_treasury.money >= -1e-6, early_treasury.money)
check("it cuts spending instead, and the cut is recorded as unfunded need",
      any(amount > 0.0 for amount in early_treasury.record.unfunded.values()), early_treasury.record.unfunded)

later, later_treasury = deficit_game(holds_node=True)
one_year(later)
check("a state holding the technology borrows the deficit: its purse goes below nothing",
      later_treasury.money < 0.0, later_treasury.money)
check("and so cuts nothing within its ceiling", not any(later_treasury.record.unfunded.values()),
      later_treasury.record.unfunded)

given, given_treasury = deficit_game(baseline=True)
one_year(given)
check("a civilisation that already has the technology in its baseline knowledge borrows from the start",
      given_treasury.money < 0.0, given_treasury.money)

spent_early = sum(early_treasury.record.outlays.values())
spent_later = sum(later_treasury.record.outlays.values())
check("the state that can borrow spends more than the one that cannot", spent_later > spent_early,
      (spent_later, spent_early))
