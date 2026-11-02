"""Route tolls and port dues paid by merchants: each is levied where a haul changes to a mode and goes to whoever holds
that tile (geography's `route_dues_by_holder`). The setup prices them per tonne by mode (`route_dues`), and the carriage
table already charges them in its handling, so a fee covers them; the merchant pays them as money to the holder's
account, and the port turns that account's money into the holder's coin (markets/port_dues.py).

The setup prices dues at the opening wage; `owed_per_tonne` scales them by the year's carriage wage scale
(`CarriageTable.scale`, set by `carriage_hours.wage_scale`), as the table scales the handling that contains them. A
merchant whose purse cannot cover both the dues and the fee of a shipment pays the dues first, to the holders in
name order, and the carrier is paid what is left of the purse (merchants.py `dispatch`)."""
from typing import Callable, Dict

from sim.geography.api import route_dues_by_holder

from .tile_costs import CarriageTable
from .types import TileId

ACCOUNT_PREFIX = "dues:"


def account(holder: str) -> str:
    """The economy account the dues owed to a holder collect in until the port pays the holder."""
    return ACCOUNT_PREFIX + holder


def owed_per_tonne(setup, carriage: CarriageTable) -> Callable[[TileId, TileId], Dict[str, float]]:
    """A function giving {holder: money per tonne} of the dues on the cheapest haul between two tiles, by who holds the
    tile each is levied at now, at the year's wage (the opening's dues times the table's scale when called)."""
    def owed(source: TileId, destination: TileId) -> Dict[str, float]:
        if not setup.route_dues:
            return {}
        legs = [{"from": tile, "mode": mode} for tile, mode in carriage.haul(source, destination).legs]
        by_holder = route_dues_by_holder(legs, setup.route_dues, setup.country_of)
        return {holder: owed * carriage.scale for holder, owed in by_holder.items()}
    return owed
