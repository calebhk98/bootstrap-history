"""Pricing the opening's money at the agent economy.

A game starts with its money counted at the labour package's opening figure (the coin's labour cost in
the price solver). The economy then settles its own wage for an hour of work, and that is the one
money per labour hour: the markets module rescales each seat's money when the economy first opens
(`RepriceOpeningMoney`) and asks the root to count the tree's money fields afresh (`RepriceTree`).
"""
from . import money_units


def opening_schedule(sim):
    """The opening wage schedule of the game's civilisation: the workforce module's, built once from the live trade registry.
    It is shared, so a caller that wants another money value asks `priced_schedule` for a copy."""
    return sim.view("wage_schedule_for")(sim.start_civ)


def priced_schedule(sim, schedule, money_per_labour_hour=None):
    """`schedule` with an hour of work worth the money it is worth now (or the figure given); `schedule` is unchanged."""
    return schedule.priced_at(sim.view("money_per_labour_hour")() if money_per_labour_hour is None
                              else money_per_labour_hour)


def priced_nodes(nodes, schedule):
    """The tree with its money fields at the wages and the money an hour of work is worth in `schedule`."""
    return money_units.rebased_nodes(nodes, schedule.wages_per_hour(), schedule.money_per_labour_hour)


def reprice_tree(sim, money_per_labour_hour=None):
    """Count the tree's money fields at the money an hour of work is worth now (or at the figure given), and
    keep that figure in the save, so a resumed game can count them the same without opening its economy."""
    schedule = priced_schedule(sim, opening_schedule(sim), money_per_labour_hour)
    sim.nodes = priced_nodes(sim.nodes, schedule)
    sim.state.economy.nodes_money_per_labour_hour = schedule.money_per_labour_hour
    sim._done_changed()
    sim._operating_changed()


def saved_tree_pricing(money_from_economy, nodes_money_per_labour_hour):
    """The money an hour of work was worth when a save's tree was priced, or None when the save never priced it
    (a game that resumes it without opening its economy cannot count the tree's money fields)."""
    return nodes_money_per_labour_hour if money_from_economy else None
