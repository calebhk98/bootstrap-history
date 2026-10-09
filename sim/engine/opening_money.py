"""Pricing the opening's money at the agent economy.

A game starts with its money counted at the labour package's opening figure (the coin's labour cost in
the price solver). The economy then settles its own wage for an hour of work, and that is the one
money per labour hour: the founder's purse, seats' purses and the tree's money fields, all counted in
hours at construction, are repriced to it when the economy first opens.
"""
from . import money_units
from .data import TRADE_REGISTRY
from .wage_schedule import build_schedule


def reprice_opening_money(sim, before):
    """From now the money an hour of work is worth is the economy's unskilled wage. `before` is the figure
    the game's money was counted at; purses and the tree move by the ratio of the two."""
    sim.state.economy.money_from_economy = True
    after = sim.labour.money_per_labour_hour()
    ratio = after / before
    for seat_id in list(sim.state.seats):
        with sim.act_as(seat_id):
            household = sim.state.household
            household.capital = household.capital * ratio
            if household.cash_mark is not None:
                household.cash_mark = household.cash_mark * ratio
    sim.nodes = priced_nodes(sim, sim.nodes, build_schedule(TRADE_REGISTRY, sim.start_civ))
    sim._done_changed()
    sim._operating_changed()


def priced_nodes(sim, nodes, schedule):
    """The tree with its money fields at the money an hour of work is worth now; `schedule` is the opening's
    wage schedule, whose wages and money per labour hour are replaced by now's."""
    schedule.money_per_labour_hour = sim.labour.money_per_labour_hour()
    return money_units.rebased_nodes(nodes, schedule.wages_per_hour(), schedule.money_per_labour_hour)
