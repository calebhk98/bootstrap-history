"""Writes the shipped openings (shipped_openings.py): one full spin-up per civilisation, under its cache key."""
import os
import random

from . import shipped_openings, solve_cache
from .core import Sim
from .data import load, load_civ
from .economy_port_year import SPIN_UP_CACHE_DIRECTORY, SPIN_UP_YEARS_ENV


def build(civ_id: str) -> str:
    """Open a game of `civ_id` (running the spin-up unless the disk cache holds it) and ship its record;
    returns the key. The opening does not depend on the seed, kit or player, so one game stands for all."""
    if os.environ.get(SPIN_UP_YEARS_ENV):
        raise SystemExit("%s shortens the spin-up; a shipped opening must be the full one" % SPIN_UP_YEARS_ENV)
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_id))
    key = game.economy.agent.opening_cache_key()
    record = solve_cache.cached_json(key, _missing(key), cache_dir=SPIN_UP_CACHE_DIRECTORY)
    shipped_openings.write(key, record)
    return key


def prune(kept_keys) -> list:
    """Remove shipped records whose keys are not in `kept_keys`; returns the keys removed."""
    removed = [key for key in shipped_openings.shipped_keys() if key not in set(kept_keys)]
    for key in removed:
        os.remove(shipped_openings.path_of(key))
    return removed


def _missing(key):
    def compute():
        raise RuntimeError("the opening's spin-up record %s is not in the disk cache after opening" % key)
    return compute
