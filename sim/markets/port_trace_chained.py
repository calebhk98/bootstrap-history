"""A chained price index for the spin-up trace, beside the model's own fixed-basket level."""


def chained_ratio(prices_before, prices_now, quantities_now):
    """This period's prices over last period's, both valued at this period's quantities (a Paasche-type link of a
    chained index), over the goods priced in both periods with a positive quantity; None when no good qualifies.
    Follows Eurace@Unibi's Statistical_Office/Eurostat_aux_functions.c `Eurostat_calc_price_index`, where the
    index is last period's times sum(price_now * quantity) / sum(price_before * quantity). Quantities here are the
    year's output by good (the trace has no sold quantity by good)."""
    now_total = 0.0
    before_total = 0.0
    for good, quantity in quantities_now.items():
        price_now = prices_now.get(good)
        price_before = prices_before.get(good)
        if quantity <= 0.0 or not price_now or not price_before:
            continue
        now_total += price_now * quantity
        before_total += price_before * quantity
    return now_total / before_total if before_total > 0.0 else None


def next_chained_index(index_before, prices_before, prices_now, quantities_now):
    """The chained index after this period: `index_before` times `chained_ratio`; unchanged when no ratio exists."""
    ratio = chained_ratio(prices_before, prices_now, quantities_now)
    return index_before if ratio is None else index_before * ratio
