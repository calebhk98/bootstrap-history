"""One-line forwarders from `Sim` to the freight module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.freight.api import FREIGHT_DRIVER_WAGE_TRADE, FREIGHT_FEED_PRICE_MATERIAL


class ForwardFreightMixin:
    FREIGHT_DRIVER_WAGE_TRADE = FREIGHT_DRIVER_WAGE_TRADE
    FREIGHT_FEED_PRICE_MATERIAL = FREIGHT_FEED_PRICE_MATERIAL
