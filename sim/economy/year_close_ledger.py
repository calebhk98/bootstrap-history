"""The close's one write to the year ledger: the runs of capacity that wore out, for every producer at once.

`note_plant_worn(ledger, producer_ids, worn)` is `ledger.plant_worn[producer_id] = worn` for each producer in order, through the
ledger's own figure kernel (`year_ledger_kernels.set_figure`), so the entry order the ledger keeps is the loop's."""
import numpy as np

from .year_ledger_block_kernels import set_in_order
from .year_ledger_tables import PLANT_WORN


def note_plant_worn(ledger, producer_ids, worn) -> None:
    """Set the ledger's `plant_worn` of each producer to the matching entry of `worn` (an array of floats)."""
    if not len(producer_ids):
        return
    tables = ledger.tables
    agents = tables.agent_numbers(producer_ids)
    figures = tables.figures
    set_in_order(figures.plant_worn, figures.order_plant_worn, tables.counters, PLANT_WORN, agents, np.asarray(worn, dtype=np.float64))
