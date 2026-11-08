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
    """`households_basket.need_prices(basket_of(), view, tile)` for the basket the caller names by `key` (with the tile; `basket_of` is only called on a miss): the priced list
    is kept like any read (so is each priced need, by need and tile), and the prices on a tile (the offered price in the area each good is bought in) are read once, as a block, for every
    basket priced there. A view without kept reads prices the basket every time."""
    from sim.world import need_basket
    from .priced_need_prime import TILE_BASKET_KEY, asked_by, need_key, price_asked, pending_asks
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
    if asked is not None:       # the tiles' own baskets: asked on every tile after every write, so all are priced in one batch at the first miss
        asked[(tile, key)] = basket
        if "primed" not in reads:
            reads["primed"] = True
            pending = pending_asks(asked, reads)
            if len(pending) > 1 and price_asked(view, reads, pending):
                return reads[full_key]
    reader_for = reads.get(("prices_on", tile))
    if reader_for is None:
        reader_for = reads[("prices_on", tile)] = tile_price_reader(view, tile)
    exponent = 1.0 - basket.substitution
    found = []
    for spec in basket.needs:     # a need priced on this tile is shared by every basket that holds the same need
        each = need_key(tile, spec, exponent)
        try:
            need = reads[each]
        except KeyError:
            need = reads[each] = need_basket.priced_need(spec, exponent, reader_for(spec.goods))
        if need is not None:
            found.append(need)
    reads[full_key] = found
    return found
