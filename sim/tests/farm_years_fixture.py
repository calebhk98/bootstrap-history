"""Helpers for tests that run a Rome game's society year by year (the farm and food tests): complete technologies, run
the demographic and society steps, and build the game."""
from .harness import sim
from sim.diffusion.api import AdvanceSociety


def complete(test_sim, node_ids):
    """Mark technologies as completed by the founder this year."""
    for node_id in node_ids:
        test_sim.state.projects.done.add(node_id)
        test_sim.state.projects.done_year[node_id] = test_sim.state.scenario.year


def run_years(test_sim, years):
    for _ in range(years):
        year = test_sim.state.scenario.year
        test_sim._demographic_recovery(year)
        test_sim.send(AdvanceSociety(year))
        test_sim.state.scenario.year = year + 1


def rome():
    return sim(civ="rome_100ad", events=False)
