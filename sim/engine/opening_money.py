"""Pricing the opening's money at the agent economy.

A game starts with its money counted at the labour package's opening figure (the coin's labour cost in
the price solver). The economy then settles its own wage for an hour of work, and that is the one
money per labour hour: the markets module rescales each seat's money when the economy first opens
(`RepriceOpeningMoney`) and asks the root to count the tree's money fields afresh (`RepriceTree`).
"""
from . import money_units
from sim.workforce.api import build_schedule


def reprice_tree(sim, money_per_labour_hour=None):
    """Count the tree's money fields at the money an hour of work is worth now (or at the figure given), and
    keep that figure in the save, so a resumed game can count them the same without opening its economy."""
    schedule = build_schedule(sim.view("trade_records")(), sim.start_civ)
    sim.nodes = priced_nodes(sim, sim.nodes, schedule, money_per_labour_hour)
    sim.state.economy.nodes_money_per_labour_hour = schedule.money_per_labour_hour
    sim._done_changed()
    sim._operating_changed()


def priced_nodes(sim, nodes, schedule, money_per_labour_hour=None):
    """The tree with its money fields at the money an hour of work is worth now (or at the figure given);
    `schedule` is the opening's wage schedule, whose wages and money per labour hour are replaced by it."""
    schedule.money_per_labour_hour = (sim.labour.money_per_labour_hour() if money_per_labour_hour is None
                                      else money_per_labour_hour)
    return money_units.rebased_nodes(nodes, schedule.wages_per_hour(), schedule.money_per_labour_hour)



def saved_tree_pricing(money_from_economy, nodes_money_per_labour_hour):
    """The money an hour of work was worth when a save's tree was priced, or None when the save never priced it
    (a game that resumes it without opening its economy cannot count the tree's money fields)."""
    return nodes_money_per_labour_hour if money_from_economy else None
