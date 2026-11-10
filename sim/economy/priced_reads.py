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


def offered_prices_for(view, tile, goods):
    """`view.offered_price(good, view.area_of(good, tile))` for each of `goods`, as a dict: read from the tile's block of prices when the
    view keeps one (`YearView.offered_prices_for`), good by good for any other view."""
    block = getattr(view, "offered_prices_for", None)
    if block is not None:
        return block(tile, goods)
    return {good: view.offered_price(good, view.area_of(good, tile)) for good in goods}


def cleared_prices_for(view, tile, goods):
    """`view.cleared_price(good, view.area_of(good, tile))` for each of `goods`, as a dict: read from the tile's block of cleared prices when
    the view keeps one (`YearView.cleared_prices_for`), good by good for any other view."""
    block = getattr(view, "cleared_prices_for", None)
    if block is not None:
        return block(tile, goods)
    return {good: view.cleared_price(good, view.area_of(good, tile)) for good in goods}


def usual_prices_for(view, tile, goods):
    """`view.usual_price(good, view.area_of(good, tile))` for each of `goods`, as a dict: read from the tile's block of usual prices when the
    view keeps one (`YearView.usual_prices_on`), good by good for any other view or a good outside the block."""
    block_of = getattr(view, "usual_prices_on", None)
    block = None if block_of is None else block_of(tile)
    if block is None:
        return {good: view.usual_price(good, view.area_of(good, tile)) for good in goods}
    prices, covered = block.prices, block.covered
    return {good: prices.get(good) if good in covered else view.usual_price(good, view.area_of(good, tile)) for good in goods}


def tile_price_reader(view, tile):
    """`price_of(goods)` for a tile: the function that gives the offered price of a good (None for none) for a need that is served by
    `goods` (pairs of good and effect). The prices of the whole tile come from one block read (`YearView.offered_prices_on`), and
    when the block covers every good of the need the answer is the block's own `dict.get`; a good the block does not cover, and a
    view without blocks, is read by itself."""
    block_of = getattr(view, "offered_prices_on", None)
    block = None if block_of is None else block_of(tile)

    def by_itself(good):
        return view.offered_price(good, view.area_of(good, tile))
    if block is None:
        return lambda goods: by_itself
    prices, covered = block.prices, block.covered

    def reader_for(goods):
        if block.covers_all(good for good, _effect in goods):
            return prices.get
        return lambda good: prices.get(good) if good in covered else by_itself(good)
    return reader_for


def kept_need_prices(view, basket_of, tile, key):
    """`households_basket.need_prices(basket_of(), view, tile)` for the basket the caller names by `key` (with the tile; `basket_of` is only called on a miss): the
    `PricedNeeds` are kept like any read, priced in one kernel batch (`priced_need_prime.price_asked`) with every tile basket asked since the last write when
    the key is the tiles' own. A view without kept reads prices the basket every time."""
    from .priced_need_prime import TILE_BASKET_KEY, asked_by, price_asked, pending_asks
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
    basket = basket_of()
    asked = asked_by(view) if key == TILE_BASKET_KEY else None
    pending = [(tile, key, basket)]
    if asked is not None:       # the tiles' own baskets: asked on every tile after every write, so all are priced in one batch at the first miss
        asked[(tile, key)] = basket
        if "primed" not in reads:
            reads["primed"] = True
            pending = pending_asks(asked, reads)
    if not price_asked(view, reads, pending):
        from .households_basket import need_prices
        reads[full_key] = need_prices(basket, view, tile)
    return reads[full_key]


def kept_need_prices_many(view, asks):
    """`kept_need_prices(view, basket_of, tile, key)` for each ask (a (tile, key, basket_of) triple), as a list in the asks' order: the asks the
    view's reads do not hold yet are priced together in one kernel call (`priced_need_prime.price_asked`), and any the grid cannot answer for
    are priced from the offered prices as a single ask is."""
    from .priced_need_prime import price_asked
    current = getattr(view, "_current", None)
    if current is not None:
        reads = current()
        misses = [(tile, key, basket_of()) for tile, key, basket_of in asks if ("need_prices", tile, key) not in reads]
        if len(misses) > 1:
            price_asked(view, reads, misses)
    return [kept_need_prices(view, basket_of, tile, key) for tile, key, basket_of in asks]
