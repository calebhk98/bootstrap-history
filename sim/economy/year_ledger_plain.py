"""A nested ledger view read as plain dicts from its pair rows in blocks (what `NestedView.as_plain` returns)."""
from typing import Callable, Dict, List, Sequence

import numpy


def plain_by_agent(members: numpy.ndarray, names: Sequence[str], agents: numpy.ndarray, subkeys: numpy.ndarray,
                   extras: numpy.ndarray, amounts: numpy.ndarray, names_of_subs: Callable[[List[int], List[int]], list]
                   ) -> Dict[str, Dict[str, float]]:
    """Each member agent's rows as `sub name -> amount`, members in the order given (`members` are agent numbers, `names` their
    names) and each agent's rows in the order the rows come: the agents are sorted once (stable), the sub names are made for all rows in
    one call, and each member's dict is built from its slice. A row of an agent that is not a member is dropped; a member with no row
    has `{}`."""
    sizes = int(max(members.max(initial=-1), agents.max(initial=-1))) + 1
    is_member = numpy.zeros(sizes, dtype=bool)
    is_member[members] = True
    kept = numpy.flatnonzero(is_member[agents])
    order = kept[numpy.argsort(agents[kept], kind="stable")]
    sorted_agents = agents[order]
    first = numpy.searchsorted(sorted_agents, members, side="left").tolist()
    last = numpy.searchsorted(sorted_agents, members, side="right").tolist()
    subs = names_of_subs(subkeys[order].tolist(), extras[order].tolist())
    figures = amounts[order].tolist()
    return {name: dict(zip(subs[start:stop], figures[start:stop])) for name, start, stop in zip(names, first, last)}
