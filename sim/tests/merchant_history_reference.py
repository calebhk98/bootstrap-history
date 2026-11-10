"""`MerchantTable._history_by_name` as it was: every history key visited, the merchant's kept."""
from sim.economy.merchant_figures import MarketFigures
from sim.economy.merchant_table import HISTORY_STRIDE


def history_by_name(table, numbering, only_row=None):
    names = numbering.name_list
    found = {}
    for place, key in enumerate(table.history_key.tolist()):
        owner, market = key // HISTORY_STRIDE, key % HISTORY_STRIDE
        if only_row is None or owner == only_row:
            found.setdefault(owner, {})[MarketFigures.key_of_name(names[market])] = \
                table.history_price[table.history_starts[place]:table.history_starts[place + 1]].tolist()
    return found
