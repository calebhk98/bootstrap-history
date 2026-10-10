"""A seller that sells out raises its ask; the half of the rule whose other half is the markdown of unsold
stock (producers.UNSOLD_ASK_MARKDOWN_SHARE). It keeps raising until the ask is high enough that some stock
goes unsold, where the markdown takes over, so the ask settles near the price that just clears it."""
from typing import List

from sim.constants import declare

from . import inventory

SOLD_OUT_ASK_RAISE_SHARE = declare(
    "SOLD_OUT_ASK_RAISE_SHARE", 0.05, kind="temporary_heuristic",
    unit="share of the expected price a seller adds in a year it sold everything it had", source=None,
    confidence="D",
    why="A seller with nothing left learns only that its ask was no higher than buyers would pay, not by how "
        "much, so it tries a little more. Smaller than the markdown of unsold stock because a raise that "
        "overshoots costs a year of sales while a cut that overshoots costs only margin; raises that were "
        "too fast swung durable purchases (Complaint 468).")


def sold_out_outputs(producer, recipe, view) -> List[str]:
    """Outputs of a producer that worked last year and holds nothing beyond its own runs' inputs and the
    working stock its sales call for: everything it offered sold at its ask."""
    if producer.last_runs <= 0.0:
        return []
    sold = []
    for good in sorted(recipe.outputs):
        spare = (view.stock(producer.agent_id, good, producer.tile)
                 - recipe.inputs.get(good, 0.0) * producer.capacity_runs
                 - inventory.target_stock(producer.expected_sales) * recipe.outputs[good])
        if spare <= 0.0:
            sold.append(good)
    return sold
