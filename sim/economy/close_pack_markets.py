"""The close pack's market figures (clearing price and unmet demand by good column and area column) read from the ledger's market
rows by array, with the market memory's numbers of each market's good and area translated to the year arrays' columns."""
import numpy as np


def columns_of_markets(first: np.ndarray, area: np.ndarray, good_names, area_names, good_row, area_row):
    """(good column, area column) of each goods market row, -1 where the year arrays have no column for the good or area.
    `first` and `area` are the market table's good and area numbers; `good_names` and `area_names` the numberings' names by number."""
    good_of_number = np.array([good_row.get(name, -1) for name in good_names], dtype=np.int64)
    area_of_number = np.array([area_row.get(name, -1) for name in area_names], dtype=np.int64)
    if not len(first):
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    return good_of_number[first], area_of_number[area]


def clearing_and_unmet(shape, delivered, priced, unmet, unmet_order, good_column, area_column):
    """(clearing price, unmet quantity), each (good column, area column), from per-market arrays: a market's price counts where goods
    moved in it and it has a price; its unmet quantity where one was noted. Markets are the first `len(good_column)` rows."""
    clearing, wanted = np.full(shape, np.nan), np.zeros(shape)
    count = len(good_column)
    placed = (good_column >= 0) & (area_column >= 0)
    priced_market = placed & (delivered[:count] > 0.0) & (priced[:count] == priced[:count])
    clearing[good_column[priced_market], area_column[priced_market]] = priced[:count][priced_market]
    short = placed & (unmet_order[:count] != 0)
    wanted[good_column[short], area_column[short]] = unmet[:count][short]
    return clearing, wanted
