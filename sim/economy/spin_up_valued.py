"""What the settle check values a spin-up year's output and producers' stock at (the rule sets' `spin_up_valued`). The
opening's prices are a table of costs; where a market settles far from it (wood, draught animals, a by-product nobody
wants) a quantity valued at them counts for many times what it sells for, and a small change in it reads as a large share
of a year's output. Where a year carries its own prices and quantities, the check reads a change between two years at
the earlier year's prices (sim/markets/spin_up_gap.py `valued_gaps`): a quantity counts for what it trades at, and a
swing in prices is still no change in what is made or held."""
from typing import Dict, Mapping, Optional


def at_the_opening_prices(_prices: Mapping[str, Optional[float]], _output: Mapping[str, float], _stock: Mapping[str, float]) -> None:
    """Nothing more is carried: the year's output and stock stand as valued at the opening's prices."""
    return None


def at_the_years_prices(prices: Mapping[str, Optional[float]], output: Mapping[str, float], stock: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    """{"prices": each good's price this year (the goods that have one above nothing), "output": the quantities made,
    "stock": the quantities producers hold}; a good of which nothing is made or held is left out."""
    return {"prices": {good: price for good, price in prices.items() if price is not None and price > 0.0},
            "output": {good: quantity for good, quantity in output.items() if quantity != 0.0},
            "stock": {good: quantity for good, quantity in stock.items() if quantity != 0.0}}
