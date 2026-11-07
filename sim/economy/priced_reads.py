"""Reads of a year view kept until the market memory is next written to, for a caller that prices many cohorts alike."""


def kept_reads(view, key, compute):
    """`compute()` once per `key` until the view's memory is written to; a view without kept reads computes every time.
    The result is shared by every caller of the key: callers read it and never change it."""
    current = getattr(view, "_current", None)
    if current is None:
        return compute()
    reads = current()
    try:
        return reads[key]
    except KeyError:
        found = reads[key] = compute()
        return found


def kept_need_prices(view, basket_of, tile, key):
    """`households_basket.need_prices(basket_of(), view, tile)` for the basket the caller names by `key` (with the tile; `basket_of` is only called on a miss): the priced list
    is kept like any read, and the price of a good on a tile (the offered price in the area it is bought in) is read once for every
    basket priced there. A view without kept reads prices the basket every time."""
    from sim.world import need_basket
    current = getattr(view, "_current", None)
    if current is None:
        from .households_basket import need_prices
        return need_prices(basket_of(), view, tile)
    reads = current()
    full_key = ("need_prices", tile, key)
    try:
        return reads[full_key]
    except KeyError:
        pass
    prices = reads.get(("prices_on", tile))
    if prices is None:
        prices = reads[("prices_on", tile)] = {}

    def price_of(good):
        try:
            return prices[good]
        except KeyError:
            found = prices[good] = view.offered_price(good, view.area_of(good, tile))
            return found
    found = reads[full_key] = list(need_basket.need_prices(basket_of(), price_of))
    return found
