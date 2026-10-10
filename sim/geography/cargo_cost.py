"""What the cargo itself costs while it is carried: interest on its value, spoilage, loss at sea.

The carrier's cost per tonne-km is `freight_cost.py`; the cargo's cost depends on the good's value and
perishability and on how long it is tied up, so it is a share of the price (or money on a stated
value), not a rate over the route. Foreign routes and domestic hauls use the same terms.

Standalone: rates, years and distances in; shares and money out. Spoilage rates are data in
`data/world/spoilage.json`.
"""
import functools
import json
import math
import os

from sim.constants import declare

SPOILAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "world", "spoilage.json")
MAX_LOST_SHARE = declare(
    "MAX_LOST_SHARE", 0.9, kind="temporary_heuristic",
    unit="share of a cargo", source=None, confidence="D",
    why="A cap so a very long or hazardous route does not price a good at infinity; goods "
        "that are mostly lost are not carried and a route-risk model would replace the cap.")


@functools.lru_cache(maxsize=None)
def spoilage_rates(path=SPOILAGE_PATH):
    """{material: decay rate per year} for the goods that spoil."""
    with open(path) as source:
        document = json.load(source)
    return {material: float(entry["rate"]) for material, entry in document["rates_per_year"].items()}


def interest_money(cargo_value, annual_rate, years):
    """Interest on money tied up in a cargo for a number of years."""
    return cargo_value * annual_rate * years


def spoilage_share(rate_per_year, years):
    """Share of a cargo lost to spoilage over a time, from a continuous decay rate."""
    return 1.0 - math.exp(-max(0.0, rate_per_year) * max(0.0, years))


def sea_loss_share(loss_per_thousand_km, sea_km):
    """Share of a cargo lost with hulls over the distance sailed."""
    return min(MAX_LOST_SHARE, loss_per_thousand_km * max(0.0, sea_km) / 1000.0)


def daily_loss_share(loss_per_day, days):
    """Share of a cargo lost over some days on the road at a daily loss rate (a herd's strays and wasting)."""
    return 1.0 - (1.0 - min(1.0, max(0.0, loss_per_day))) ** max(0.0, days)


def lost_share(*shares):
    """Share lost when independent hazards each take their share in turn."""
    kept = 1.0
    for share in shares:
        kept *= 1.0 - share
    return min(MAX_LOST_SHARE, 1.0 - kept)


def worst_spoilage_rate(materials):
    """The fastest-spoiling of a commodity's materials (zero for none that spoil)."""
    rates = spoilage_rates()
    return max((rates.get(material, 0.0) for material in materials), default=0.0)
