"""The offers of producers that offer at the reservation the kernel gave (`year_goods_offers`), written to the order tables as rows."""
from .goods_order_tables import PRODUCER_OUTPUT


class OfferRows:
    """The offers of producers that offer at the reservation the kernel gave, collected as ids and written to the order tables as rows."""

    def __init__(self, orders, view):
        self.orders, self.view = orders, view
        self.seller, self.good, self.tile, self.market, self.quantity, self.reservation = [], [], [], [], [], []

    def add(self, producer, good: str, quantity: float, reservation: float) -> None:
        orders = self.orders
        self.seller.append(orders.agent_id(producer.agent_id))
        self.good.append(orders.good_id(good))
        self.tile.append(orders.tile_id(producer.tile))
        self.market.append(orders.market_id(good, self.view.area_of(good, producer.tile)))
        self.quantity.append(quantity)
        self.reservation.append(reservation)

    def write(self) -> None:
        if self.seller:
            self.orders.append_offers(self.seller, self.good, self.tile, self.market, self.quantity, self.reservation, PRODUCER_OUTPUT)
            self.__init__(self.orders, self.view)
