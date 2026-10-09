"""The technologies the society holds: its own at the start, and what its actors have since learnt.

A node the founder completes is the founder's. A firm or the government holds it only once it has copied it
(agents/imitation.py) or been licensed it (`disclose`), so until then the society's costs and prices do not
reflect it and the founder's technique earns the difference.
"""
from typing import Any, FrozenSet, Iterable, Set

# actor kinds that are the society's producers and rulers; households and interest groups are not
SOCIETY_KINDS = ("firm", "government")


def held_by_society(granted: Iterable[str], actors: Iterable[Any]) -> Set[str]:
    held = set(granted)
    for actor in actors:
        if actor.kind in SOCIETY_KINDS and actor.record.exited_year is None:
            held.update(actor.knowledge)
    return held


def society_techs(sim: Any) -> FrozenSet[str]:
    """Techniques the society holds now in `sim`, as a frozen set."""
    projects = sim.state.projects
    actors = []
    if sim.state.actors is not None and sim.state.actors.records:
        actors = [actor for kind in SOCIETY_KINDS for actor in sim.actors.of_kind(kind)]
    return frozenset(held_by_society(projects.granted, actors))
