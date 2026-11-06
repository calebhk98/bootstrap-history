"""People who join the labour core from outside its own flows (apprentices a seat taught, staff an institution granted)."""
from .market.aptitude import split_evenly


def add_people(state, area, trade, people):
    """`people` more workers of `trade` in a labour area, spread over the ability bands as the population is."""
    if people <= 0.0:
        return
    bands = state.workers.setdefault(area, {}).setdefault(trade, [0.0] * len(split_evenly(1.0)))
    for index, share in enumerate(split_evenly(people)):
        bands[index] += share
