"""What the goods market asks of its world besides prices: the memory it keeps for the acting seat, the goods that never cross a
border and the tariff and embargo of one country toward another. For the stub games of the market's tests."""


def market_memory():
    """Members to splat into a stub game: a fresh memory, no goods barred from trade, no tariff and no embargo."""
    kept = {}
    return dict(civ={"id": "home"}, remembered=kept.get, remember=kept.__setitem__, not_traded_materials=frozenset,
                border_terms=lambda destination, source: (0.0, False))


def markets_over(economy=None, goods_market=None, **views):
    """The markets module reading `views`, holding the stand-in `economy` and `goods_market` objects the test supplies."""
    from sim.markets.module import Markets
    from sim.tests import module_harness
    markets = module_harness.build(Markets, views=views)
    if economy is not None:
        markets.economy = economy
    if goods_market is not None:
        markets.goods_market = goods_market
    return markets
