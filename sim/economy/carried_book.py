"""The goods the merchants carried in a year, by good and tile pair, valued at the price of each end.

`carried_goods` is {good: {origin tile: {destination tile: [tonnes, value at the origin's price, value at the
destination's price]}}}, all in the economy's unit, plain lists so the record saves as it is. A country's trade book
is read off it: what came in from another country is worth what it fetched where it landed, what went out is worth
what it fetched where it left. Plain functions over dicts; no economy is read here."""
from typing import Callable, Dict, List, Mapping, Optional

CarriedGoods = Dict[str, Dict[str, Dict[str, List[float]]]]
TONNES, AT_ORIGIN, AT_DESTINATION = 0, 1, 2


def note_carried(carried: CarriedGoods, good: str, origin: str, destination: str, units: float, tonnes: float,
                 price_at_origin: Optional[float], price_at_destination: Optional[float]) -> None:
    """Add `units` of a good (`tonnes` of it) carried from one tile to another. An end whose market has no price
    is valued at the other end's; with neither, the flow is kept at no value."""
    if origin == destination or tonnes <= 0.0 or units <= 0.0:
        return
    at_origin = price_at_origin if price_at_origin is not None else price_at_destination
    at_destination = price_at_destination if price_at_destination is not None else price_at_origin
    row = carried.setdefault(good, {}).setdefault(origin, {}).setdefault(destination, [0.0, 0.0, 0.0])
    row[TONNES] += tonnes
    row[AT_ORIGIN] += units * (at_origin or 0.0)
    row[AT_DESTINATION] += units * (at_destination or 0.0)


def trade_book(carried: Mapping[str, Mapping[str, Mapping[str, List[float]]]], country_of: Callable[[str], str],
               country: str) -> Dict[str, Dict[str, float]]:
    """{good: {"in_tonnes", "in_value", "out_tonnes", "out_value"}} of what crossed the country's border: imports
    valued at the destination's price, exports at the origin's. Goods that crossed nothing are left out."""
    book: Dict[str, Dict[str, float]] = {}
    for good in sorted(carried):
        for origin, row in sorted(carried[good].items()):
            for destination, (tonnes, at_origin, at_destination) in sorted(row.items()):
                coming_in = country_of(destination) == country and country_of(origin) != country
                going_out = country_of(origin) == country and country_of(destination) != country
                if not (coming_in or going_out):
                    continue
                entry = book.setdefault(good, {"in_tonnes": 0.0, "in_value": 0.0, "out_tonnes": 0.0, "out_value": 0.0})
                direction = "in" if coming_in else "out"
                entry[direction + "_tonnes"] += tonnes
                entry[direction + "_value"] += at_destination if coming_in else at_origin
    return book


def trade_value(book: Mapping[str, Mapping[str, float]], direction: str) -> float:
    """Total value of a trade book's imports ("in") or exports ("out")."""
    return sum(entry[direction + "_value"] for entry in book.values())
