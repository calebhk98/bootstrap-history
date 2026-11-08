"""The year's cheapest moving costs between the state's areas as one matrix (`YearInputs.carriage_from` for every origin at once)."""
import numpy as np

from .market_state import MarketState
from .records import YearInputs


def dense_carriage(state: MarketState, inputs: YearInputs) -> np.ndarray:
    """`matrix[origin, area]` is the cheapest cost of carrying a person from origin to area, NaN where there is no way. An area
    reaches itself at zero, as `carriage_from` has it, also when no route names it."""
    count = len(state.ids.areas)
    matrix = np.full((count, count), np.nan)
    np.fill_diagonal(matrix, 0.0)
    names, costs = inputs.carriage_costs()
    if names:
        where = np.array([state.ids.areas.number(name) for name in names], np.int64)
        matrix[np.ix_(where, where)] = np.where(np.isinf(costs), np.nan, costs)
    return matrix
