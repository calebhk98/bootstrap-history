"""Every cohort's basket priced together, the first time a pass over the cohorts asks for one after a write to the memory.

A pass that asks `households_basket.cohort_need_prices` cohort by cohort (the orders, the wage floor, the outside option) would price each
basket by itself; `prime_cohort_baskets` asks `priced_need_prime.price_asked` for the distinct baskets of all cohorts in one kernel call, and
the pass then reads kept answers. A cohort whose basket changes later (`household_work_year.decide`) has another key, and is priced when asked."""
from . import household_work_year
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
    asks = {}
    for cohort in record.cohorts.values():
        signature = household_work_year.basket_signature(record, cohort, buying)
        key = ("cohort_basket", signature)
        if ("need_prices", cohort.tile, key) not in reads and (cohort.tile, key) not in asks:
            asks[(cohort.tile, key)] = household_work_year.cohort_basket(setup, record, cohort, buying)
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
    asks = {}
    for cohort in record.cohorts.values():
        hearth = household_work_year.has_hearth(record, cohort)
        key = ("food", hearth)
        if ("need_prices", cohort.tile, key) not in reads and (cohort.tile, hearth) not in asks:
            asks[(cohort.tile, hearth)] = household_work_year.tile_food_basket(setup, cohort.tile, hearth)
    price_asked(view, reads, [(tile, ("food", hearth), basket) for (tile, hearth), basket in asks.items()])
