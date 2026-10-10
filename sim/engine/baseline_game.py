"""Plays one baseline game for the ensemble (Complaints/266): a civilisation left alone, one snapshot a year.

Each game takes a long time to build and play, so nothing here runs on import and the tests use a stub
runner in its place.
"""
import random
from typing import Any, Dict, List, Set


def society_technologies(game: Any) -> Set[str]:
    """What the society holds: the state's knowledge, the opening techniques and the starting grant."""
    from sim.engine.agents_port import SimWorld
    return set(game.state_treasury().knowledge) | set(SimWorld(game).baseline_knowledge()) | set(game.granted)


def snapshot(game: Any) -> Dict[str, Any]:
    from sim.geography.api import tiles_held
    return {"year": game.year, "population": float(game.population.total), "wage_index": float(game.wage_index),
            "literacy_general": float(game.civ.get("literacy_general", 0.0)),
            "literacy_elite": float(game.civ.get("literacy_elite", 0.0)),
            "territory_tiles": len(tiles_held(game.civ, game.world_map)),
            "technologies": sorted(society_technologies(game))}


def play_baseline(civilisation_id: str, seed: int, years: int) -> List[Dict[str, Any]]:
    """The opening and each of `years` years of a game nobody plays; it stops early if the run ends."""
    from sim.engine.ui_port import Sim, load, load_civ
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(seed), events=True, manual=True, civ=load_civ(civilisation_id),
               cfg={"immortal": True, "horizon_years": years})
    game.done_year = {}
    rows = [snapshot(game)]
    for _year in range(years):
        game.step()
        rows.append(snapshot(game))
        if game.state.founder.dead_reason:
            break
    return rows
