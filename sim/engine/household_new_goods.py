"""Which goods households can turn to that the opening's basket did not hold: the ones something offers now, at a price."""
from typing import Dict, Mapping


def prices_in_hours(prices: Mapping[str, float], per_hour: float, opening_prices: Mapping[str, float],
                    offered_at_home: Mapping[str, bool]) -> Dict[str, float]:
    """Labour-hour price of each positively priced good that the opening's basket held or the home society now offers
    (a good only a partner offers is not the home market's)."""
    return {material: price / per_hour for material, price in prices.items()
            if price > 0.0 and (material in opening_prices or offered_at_home.get(material, False))}


def new_goods_units(wanted: Mapping[str, float], opening_units: Mapping[str, float],
                    priced_in_hours: Mapping[str, float]) -> Dict[str, float]:
    """{material: units wanted a year} of goods wanted now that the opening's basket did not hold, in sorted order.
    A good with no price draws none; derived demand reaches inputs of recipes the society cannot price, which are left out."""
    return {material: units for material, units in sorted(wanted.items())
            if units > 0.0 and material not in opening_units and material in priced_in_hours}
