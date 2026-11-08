"""The cohorts' bids as order-table rows, written straight from the answers of `households_orders_kernel.year_orders`.

For each cohort, in order: the bid of each priced good the kernel switched on (goods in name order, `order_local` of its
basket template), then, when the cohort has a store plan, the bid of each store good with a budget. The rows are what
`households_orders_pack._orders_of` made into `Bid` objects; the sum of their budgets, added in that order, is the cohort's
planned spending."""
import numpy

from sim.jit import njit

from .households_store import STORE_PRIORITY
from .households_orders_kernel import RO_BUDGET, RO_CAP, RO_FLEX, RO_FLOOR, RO_ON, SO_BUDGET, SO_FLEX



@njit
def _emit(figures, buyer, good, tile, market, priority, count, agent, good_id, tile_id, market_id, tier, floor, flexible, reference,
          elasticity, budget, ceiling):
    """Write one bid as row `count` of the output columns."""
    buyer[count], good[count], tile[count], market[count], priority[count] = agent, good_id, tile_id, market_id, tier
    figures[count, 0], figures[count, 1], figures[count, 2] = floor, flexible, reference
    figures[count, 3], figures[count, 4], figures[count, 5] = elasticity, budget, ceiling


@njit
def _add(total, carry, value):
    """One step of the compensated sum Python's `sum` of floats takes (Neumaier): the running total and the lost low digits."""
    step = total + value
    if abs(total) >= abs(value):
        carry += (total - step) + value
    else:
        carry += (value - step) + total
    return step, carry


@njit
def cohort_bid_rows(cohort_agent, cohort_tile, cohort_template, cohort_row_start, cohort_store_start, cohort_plan, order_ptr,
                    order_local, template_row0, template_store0, template_stores, template_substitution, row_good, row_market,
                    row_priority, row_price, store_good, store_market, store_price, rows, stores):
    """The bid rows of every cohort and each cohort's planned spending. Per template: `order_ptr` cuts `order_local` (the
    local rows in name order), `template_row0` and `template_store0` say where its rows and store goods start in the per-row
    and per-store arrays, `template_stores` how many store goods it has. Returns (buyer, good, tile, market, priority, figures
    of floor, flexible, reference price, elasticity, budget and ceiling, planned spending per cohort)."""
    capacity = len(rows) + len(stores)
    buyer = numpy.zeros(capacity, dtype=numpy.int64)
    good = numpy.zeros(capacity, dtype=numpy.int64)
    tile = numpy.zeros(capacity, dtype=numpy.int64)
    market = numpy.zeros(capacity, dtype=numpy.int64)
    priority = numpy.zeros(capacity, dtype=numpy.int64)
    figures = numpy.zeros((capacity, 6))
    planned = numpy.zeros(len(cohort_agent))
    count = 0
    for cohort in range(len(cohort_agent)):
        template = cohort_template[cohort]
        row0, store0 = template_row0[template], template_store0[template]
        substitution = template_substitution[template]
        total, carry = 0.0, 0.0
        for place in range(order_ptr[template], order_ptr[template + 1]):
            local = order_local[place]
            row = cohort_row_start[cohort] + local
            if rows[row, RO_ON] > 0.0:
                _emit(figures, buyer, good, tile, market, priority, count, cohort_agent[cohort], row_good[row0 + local],
                      cohort_tile[cohort], row_market[row0 + local], row_priority[row0 + local], rows[row, RO_FLOOR], rows[row, RO_FLEX],
                      row_price[row0 + local], substitution, rows[row, RO_BUDGET], rows[row, RO_CAP])
                total, carry = _add(total, carry, rows[row, RO_BUDGET])
                count += 1
        if cohort_plan[cohort] > 0.0:
            for local in range(template_stores[template]):
                store = cohort_store_start[cohort] + local
                if stores[store, SO_BUDGET] > 0.0:
                    _emit(figures, buyer, good, tile, market, priority, count, cohort_agent[cohort], store_good[store0 + local],
                          cohort_tile[cohort], store_market[store0 + local], STORE_PRIORITY, 0.0, stores[store, SO_FLEX],
                          store_price[store0 + local], substitution, stores[store, SO_BUDGET], numpy.inf)
                    total, carry = _add(total, carry, stores[store, SO_BUDGET])
                    count += 1
        planned[cohort] = total + carry if carry != 0.0 and numpy.isfinite(carry) else total
    return buyer[:count].copy(), good[:count].copy(), tile[:count].copy(), market[:count].copy(), priority[:count].copy(), \
        figures[:count].copy(), planned
