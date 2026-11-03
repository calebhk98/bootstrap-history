"""Route tolls and port dues paid by merchants: each is levied where a haul changes to a mode and goes to whoever holds
that tile (geography's `route_dues_by_holder`). The setup prices them per tonne by mode (`route_dues`), and the carriage
table already charges them in its handling, so a fee covers them; the merchant pays them as money to the holder's
account, and the port turns that account's money into the holder's coin (markets/port_dues.py).

A due is money, not labour, so `owed_per_tonne` charges it as the setup priced it, in opening-year money, carried to today's
by the memory's `opening_wage_level`, and does not apply the year's carriage wage scale (`CarriageTable.scale`). A merchant whose purse cannot cover both the dues and the fee of a shipment pays the dues first, to the holders in
name order, and the carrier is paid what is left of the purse (merchants.py `dispatch`)."""
from typing import Callable, Dict

from sim.geography.api import route_dues_by_holder

from .tile_costs import CarriageTable
from .types import TileId

ACCOUNT_PREFIX = "dues:"


def account(holder: str) -> str:
    """The economy account the dues owed to a holder collect in until the port pays the holder."""
    return ACCOUNT_PREFIX + holder


def owed_per_tonne(setup, carriage: CarriageTable, money_level: float) -> Callable[[TileId, TileId], Dict[str, float]]:
    """A function giving {holder: money per tonne} of the dues on the cheapest haul between two tiles, by who holds the
    tile each is levied at now, as the setup priced them times `money_level` (today's money per opening-year money): a toll is
    not worked by a crew, so the year's wage does not move it."""
    def owed(source: TileId, destination: TileId) -> Dict[str, float]:
        if not setup.route_dues:
            return {}
        legs = [{"from": tile, "mode": mode} for tile, mode in carriage.haul(source, destination).legs]
        return {holder: amount * money_level for holder, amount in route_dues_by_holder(legs, setup.route_dues, setup.country_of).items()}
    return owed
