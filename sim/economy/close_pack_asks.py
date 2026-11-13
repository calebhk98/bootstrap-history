"""The width of the band each output slot of each producer may rise to in the year's close, as the close kernel reads it."""
import numpy as np

from .ask_adjust import NO_BOUND_MULTIPLE
from .ask_ceiling import AskAlternatives
from .year_arrays import YearArrays


def ask_multiples(setup, record, arrays: YearArrays) -> np.ndarray:
    """Per producer row and recipe slot: `AskAlternatives.multiple` of the slot's good on the producer's tile (a slot that is
    not a good, or not an output, has no room above cost)."""
    columns, matrices = arrays.producers, arrays.matrices
    found = np.full(columns.expected_prices.shape, NO_BOUND_MULTIPLE)
    alternatives = AskAlternatives(setup, record)
    good_names, tile_names = matrices.goods.ids, arrays.tiles.ids
    for row in range(len(columns.ids)):
        recipe = columns.recipe_row[row]
        tile = tile_names[columns.tile_row[row]]
        for slot in range(found.shape[1]):
            good = matrices.slot_goods[recipe, slot]
            if good < 0:
                break
            if matrices.slot_is_output[recipe, slot]:
                found[row, slot] = alternatives.multiple(good_names[good], tile)
    return found
