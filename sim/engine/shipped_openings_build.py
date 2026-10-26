"""Writes the shipped openings (shipped_openings.py): every cache entry one civilisation's opening uses."""
import json
import os
import random
from typing import List, Tuple

from sim.prices.api import solve_cache
from . import shipped_openings, shipped_rate_bands
from .core import Sim
from .data import load, load_civ
from .economy_port_year import SPIN_UP_YEARS_ENV


def build(civ_id: str) -> List[Tuple[str, str]]:
    """`build_reporting` without the spin-up's result."""
    return build_reporting(civ_id)[0]


def build_reporting(civ_id: str, before_writing=None):
    """Open a game of `civ_id` (computing what the disk cache lacks) and ship each cache entry it used;
    returns their (namespace, key) and how the opening's first stage ended (`spin_up_result`). The opening
    does not depend on the seed, kit or player, so one game stands for all. `before_writing(game)` is called on
    the opened game before anything is written; it may raise to refuse the opening (opening_checks_gate)."""
    if os.environ.get(SPIN_UP_YEARS_ENV):
        raise SystemExit("%s shortens the spin-up; a shipped opening must be the full one" % SPIN_UP_YEARS_ENV)
    _tree, _prices, nodes, _wages, _goods = load()
    civ = load_civ(civ_id)
    with solve_cache.recording() as touched, shipped_rate_bands.SolveRecorder() as solves:
        game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=civ)
    if before_writing is not None:
        before_writing(game)
    starting_rate = float(civ["starting_interest_rate"])
    with solve_cache.recording() as band_touched:
        shipped_rate_bands.solve_other_bands(solves.at_starting_rate(starting_rate), starting_rate)
    touched.extend(band_touched)
    shipped = []
    for directory, key in dict.fromkeys(touched):
        try:
            with open(os.path.join(directory, key + ".json"), encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, ValueError):
            continue    # an entry the disk cache could not keep is computed by the player
        shipped_openings.write(os.path.basename(directory), key, value)
        shipped.append((os.path.basename(directory), key))
    return shipped, game.economy.spin_up_result()


def prune(kept: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Remove shipped entries not in `kept`; returns those removed."""
    removed = [entry for entry in shipped_openings.shipped_entries() if entry not in set(kept)]
    for namespace, key in removed:
        os.remove(shipped_openings.path_of(namespace, key))
    return removed
