"""Every cohort's basket priced together, the first time a pass over the cohorts asks for one after a write to the memory.

A pass that asks `households_basket.cohort_need_prices` cohort by cohort (the orders, the wage floor, the outside option) would price each
basket by itself; `prime_cohort_baskets` asks `priced_need_prime.price_asked` for the distinct baskets of all cohorts in one kernel call, and
the pass then reads kept answers. A cohort whose basket changes later (`household_work_year.decide`) has another key, and is priced when asked."""
from . import household_work_year
from .cohort_store import table_of
from .priced_need_prime import price_asked


def prime_cohort_baskets(setup, record, view, buying: bool) -> None:
    """Price the basket of every cohort of `record` (`household_work_year.cohort_basket` with `buying`) under the key `cohort_need_prices` asks it by,
    once per write to the view's memory; a view without kept reads has nothing to prime."""
    current = getattr(view, "_current", None)
    if current is None:
        return
    reads = current()
    flag = ("cohorts_primed", buying)
    if flag in reads:
        return
    reads[flag] = True
    store = table_of(record.cohorts)
    asks = {}
    for signature in household_work_year.signatures_of(record, store, store.order(), buying):
        key = ("cohort_basket", signature)
        if ("need_prices", signature[0], key) not in reads and (signature[0], key) not in asks:
            asks[(signature[0], key)] = household_work_year.basket_of_signature(setup, signature)
    price_asked(view, reads, [(tile, key, basket) for (tile, key), basket in asks.items()])


def prime_food_baskets(setup, record, view) -> None:
    """Price the food basket of every (tile, hearth) the cohorts of `record` stand on (the baskets `household_work_year.grinding_plan` reads), once per
    write to the view's memory."""
    current = getattr(view, "_current", None)
    if current is None or not setup.milled_as:
        return
    reads = current()
    if "food_primed" in reads:
        return
    reads["food_primed"] = True
    store = table_of(record.cohorts)
    order = store.order()
    asks = {}
    tiles = store.tile_names(order)
    for tile, hearth in zip(tiles, household_work_year.hearths_of(record, tiles, [store.ids[row] for row in order.tolist()])):
        if ("need_prices", tile, ("food", hearth)) not in reads and (tile, hearth) not in asks:
            asks[(tile, hearth)] = household_work_year.tile_food_basket(setup, tile, hearth)
    price_asked(view, reads, [(tile, ("food", hearth), basket) for (tile, hearth), basket in asks.items()])
