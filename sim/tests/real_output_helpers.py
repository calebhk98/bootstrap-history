"""Shared by the real-output topics: close market years on a built game."""
from .harness import *  # noqa: F401,F403


def close_years(game, years):
    for _year in range(years):
        game.assembly.phase_handler("market")(game.view("seat_list")()["playing"])
