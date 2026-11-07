"""`year-time`: step a saved game for some years, print each year's wall seconds and a digest of the game after them,
and with `--reload-check` also save and load the game after its first year and check the digest is the same. The save
named is copied and never written. This is how a change to the economy's speed is measured and its game checked
reproducible (docs/architecture/NUMBA_PORT_PLAN.md)."""
import hashlib
import json
import os
import random
import shutil
import tempfile
import time

from sim.engine.ui_port import Sim, load, load_civ
from .protocol import civ_of_save, load_state, save_state


def canonical(value):
    """`value` with every dict's keys sorted, so two saves of one game compare equal whatever order sets were written in."""
    if isinstance(value, dict):
        return {str(key): canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    return value


def save_digest(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return hashlib.sha256(json.dumps(canonical(data), sort_keys=True).encode()).hexdigest()


def loaded(path, nodes):
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_of_save(path)), defer_economy=True)
    load_state(game, path)
    return game


def stepped(path, nodes, years, directory, name, reload_after=None):
    """(seconds of each year, the digest after them) of the game saved at `path` stepped `years` years; with
    `reload_after`, the game is saved and loaded again after that many years."""
    game = loaded(path, nodes)
    seconds = []
    for year in range(years):
        if reload_after is not None and year == reload_after:
            middle = os.path.join(directory, name + "_middle.json")
            save_state(game, middle)
            game = loaded(middle, nodes)
        began = time.perf_counter()
        game.step()
        seconds.append(round(time.perf_counter() - began, 3))
    after = os.path.join(directory, name + ".json")
    save_state(game, after)
    return seconds, save_digest(after)


def cmd_year_time(args):
    _tree, _prices, nodes, _wages, _goods = load()
    with tempfile.TemporaryDirectory(prefix="year_time_") as directory:
        start = os.path.join(directory, "start.json")
        shutil.copy(args.session, start)
        seconds, digest = stepped(start, nodes, args.years, directory, "straight")
        report = {"years": args.years, "seconds": seconds, "digest": digest}
        if args.keep:
            shutil.copy(os.path.join(directory, "straight.json"), args.keep)
        if args.reload_check:
            _again, reloaded = stepped(start, nodes, args.years, directory, "reloaded", reload_after=1)
            report["reload_digest"] = reloaded
            report["reproducible_after_reload"] = reloaded == digest
    print(json.dumps(report))
    return 0 if not args.reload_check or report["reproducible_after_reload"] else 1
