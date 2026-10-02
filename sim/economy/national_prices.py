"""A good's one price over its market areas."""
from typing import Dict, Tuple


def national_prices(record) -> Dict[str, float]:
    """Each good's price over its areas, weighted by what each usually trades (this year's volume
    before any is remembered)."""
    weights = record.memory.volume_weights or record.volumes
    totals: Dict[str, Tuple[float, float, float]] = {}
    for key, price in record.memory.prices.items():
        good = key.split("|", 1)[0]
        volume = weights.get(key, 0.0)
        value, quantity, plain = totals.get(good, (0.0, 0.0, 0.0))
        totals[good] = (value + price * volume, quantity + volume, plain or price)
    return {good: (value / quantity if quantity > 0.0 else plain)
            for good, (value, quantity, plain) in sorted(totals.items())}
