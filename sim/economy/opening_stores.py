"""Opening stocks of durable stores of wealth: the output of past mining that loss has not yet taken,
held by households in proportion to their income. The workings come from the deposits (the port
reads them from geography); nothing here names a good."""
from typing import Mapping, Tuple

from .metal_stock import METAL_GOODS_LOSS_PER_YEAR
from .types import EDGE_PRODUCTION, GoodsMove


def retained_output(per_year: float, years_worked: float, years_since_last: float, loss_per_year: float) -> float:
    """What is left of a deposit's output: `per_year` for `years_worked` years, the last made
    `years_since_last` years ago, each year's output losing `loss_per_year` of itself a year."""
    if years_worked <= 0.0 or per_year <= 0.0:
        return 0.0
    kept = 1.0 - loss_per_year
    if loss_per_year <= 0.0:
        return per_year * years_worked
    return per_year * kept ** years_since_last * (1.0 - kept ** years_worked) / loss_per_year


def seed_opening_stores(setup, record, store_goods, loss_per_year: float = METAL_GOODS_LOSS_PER_YEAR) -> None:
    """Give households the opening stock of each of `store_goods` (the goods fit to hold as wealth)
    that the setup has workings for. A good with no workings (`setup.opening_store_gaps` says why)
    opens empty."""
    total_income = sum(cohort.last_year_income for cohort in record.cohorts.values())
    moves = []
    for good, workings in sorted(setup.opening_store_output.items()):
        spec = setup.specs.get(good)
        if good not in store_goods or spec is None or spec.unit_mass_kg <= 0.0:
            continue
        kilograms = sum(retained_output(per_year, years, since, loss_per_year) for per_year, years, since in workings)
        for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
            share = (cohort.last_year_income / total_income if total_income > 0.0
                     else cohort.people / sum(each.people for each in record.cohorts.values()))
            quantity = kilograms * share / spec.unit_mass_kg
            if quantity > 0.0:
                moves.append(GoodsMove(EDGE_PRODUCTION, cohort.agent_id, good, cohort.tile, quantity,
                                       "opening stock of a durable store"))
    if moves:
        record.book.move_many(moves)
