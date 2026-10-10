"""How dear the economy's goods are against the opening's prices."""
import statistics
from typing import Mapping, Optional

from .national_prices import national_prices
from .notional import recently_traded_goods


def goods_level_over_opening(record, opening_prices: Mapping[str, float]) -> Optional[float]:
    """The median, over the goods that traded lately, of a good's price now over its price at the opening
    (both in the economy's unit); None when no such good has an opening price. Median, so the goods
    that never clear (their prices are estimates) do not move it."""
    recent = recently_traded_goods(record.memory)
    prices = national_prices(record)
    ratios = [prices[good] / opening_prices[good] for good in recent
              if prices.get(good, 0.0) > 0.0 and opening_prices.get(good, 0.0) > 0.0]
    return statistics.median(ratios) if ratios else None
