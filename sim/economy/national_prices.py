"""A good's one price over its market areas."""
from typing import Dict, Mapping, Set, Tuple


def national_prices(record) -> Dict[str, float]:
    """Each good's price over its areas, weighted by what each usually trades (this year's volume
    before any is remembered). Only the areas whose figure is a traded price count; a good none of whose
    areas traded last year is given the plain figure of its first area, which is then a quote
    (`MarketView.quote_kind`), so the price index follows trades where there are any."""
    weights = record.memory.volume_weights or record.volumes
    quoted = record.memory.quote_kinds
    totals: Dict[str, Tuple[float, float, float]] = {}
    for key, price in record.memory.prices.items():
        good = key.split("|", 1)[0]
        value, quantity, plain = totals.get(good, (0.0, 0.0, 0.0))
        plain = plain or price
        if key not in quoted:
            volume = weights.get(key, 0.0)
            value, quantity = value + price * volume, quantity + volume
        totals[good] = (value, quantity, plain)
    return {good: (value / quantity if quantity > 0.0 else plain)
            for good, (value, quantity, plain) in sorted(totals.items())}


def traded_spending_weights(volumes: Mapping[str, float], prices: Mapping[str, float], goods: Set[str]) -> Dict[str, float]:
    """What each of `goods` is spent on: its volume over its areas (`volumes` by market key) at `prices`. A good
    without a price or a volume carries no weight."""
    quantity: Dict[str, float] = {}
    for key, volume in volumes.items():
        good = key.split("|", 1)[0]
        if good in goods and volume > 0.0:
            quantity[good] = quantity.get(good, 0.0) + volume
    return {good: amount * prices[good] for good, amount in sorted(quantity.items()) if prices.get(good, 0.0) > 0.0}
