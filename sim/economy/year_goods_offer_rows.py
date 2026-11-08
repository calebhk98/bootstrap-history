"""The offers of producers that offer at the reservation the kernel gave (`year_goods_offers`), written to the order tables as rows."""
from .goods_order_tables import PRODUCER_OUTPUT


class OfferRows:
    """The offers of producers that offer at the reservation the kernel gave, collected by name and written to the order tables as
    rows (ids are looked up once per name when they are written)."""

    def __init__(self, orders, view):
        self.orders, self.view = orders, view
        self._clear()

    def _clear(self) -> None:
        self.seller, self.good, self.tile, self.area, self.quantity, self.reservation = [], [], [], [], [], []

    def add(self, producer, good: str, quantity: float, reservation: float) -> None:
        self.seller.append(producer.agent_id)
        self.good.append(good)
        self.tile.append(producer.tile)
        self.area.append(self.view.area_of(good, producer.tile))
        self.quantity.append(quantity)
        self.reservation.append(reservation)

    def write(self) -> None:
        """Append the collected offers to the order tables, in the order they were added."""
        if not self.seller:
            return
        orders = self.orders
        orders.append_offers(orders.agent_ids_of(self.seller), orders.good_ids_of(self.good), orders.tile_ids_of(self.tile),
                             orders.market_ids(self.good, self.area), self.quantity, self.reservation, PRODUCER_OUTPUT)
        self._clear()
