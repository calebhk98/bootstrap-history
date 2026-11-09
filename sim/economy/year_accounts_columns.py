"""Block helpers for the year's goods accounts (sim/economy/year_accounts.py): sources read as one list per figure, one entry per good."""
import itertools
import math
from typing import Dict, List, Mapping, Sequence

import numpy


def column(source: Mapping[str, float], goods: Sequence[str]) -> List[float]:
    """The source's figure for each good in order, 0.0 for a good it lacks (one pass, no Python call per good)."""
    return list(map(source.get, goods, itertools.repeat(0.0)))


def row_columns(by_agent: Mapping[str, Mapping[str, float]], agents: Sequence[str]):
    """(keys, values) of the rows of the given agents, agent after agent, each agent's rows in its dict's order; an agent with
    none adds nothing."""
    parts = [by_agent[agent] for agent in agents if agent in by_agent]
    return list(itertools.chain.from_iterable(parts)), list(itertools.chain.from_iterable(map(dict.values, parts)))


def summed_by_key(keys: Sequence[str], values: Sequence[float]) -> Dict[str, float]:
    """Each key's figures added one after another in the order given from 0.0, the sums `total[key] = total.get(key, 0.0) + value`
    leaves (`numpy.add.at` adds in index order). Keys in name order."""
    if not len(keys):
        return {}
    names, inverse = numpy.unique(numpy.array(keys), return_inverse=True)
    sums = numpy.zeros(len(names))
    numpy.add.at(sums, inverse, numpy.array(values, dtype=numpy.float64))
    return dict(zip(names.tolist(), sums.tolist()))


def sum_across(columns: Sequence[Sequence[float]], width: int) -> List[float]:
    """For each position, the exact sum (`math.fsum`) of that position in every column; zeros when there are no columns."""
    return [math.fsum(values) for values in zip(*columns)] if columns else [0.0] * width
