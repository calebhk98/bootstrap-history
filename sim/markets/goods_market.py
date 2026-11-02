"""The one goods market: what every buyer and seller asks, and the only door to its records.

The founder, a firm, the state and the foreign traders deal with `Sim.goods_market`:

    quote_buy / quote_sell     what an order would cost or fetch: the economy's price on the acting tile, carriage, and the
                               climb the economy's own book gives the order (goods_pricing.py)
    post_order                 a seat's order for the year's clearing, at its price limit; nothing settles until then
                               (port_goods_orders.py), as a seat's hires do
    price / state              what screens read

A seat is identified by its seat id (`state.acting_seat` for the asking seat); a firm or the state by its actor id. A seat's
orders and an actor's reach the same clearing, which sets the price. The asking seat's own orders keep the marginal curves
that move a bill as it is filled. Who offers what is in goods_offers.py.
"""
from sim.refusal import Refusal

from .goods_offers import GoodsOffers
from .goods_pricing import GoodsPricing
from .rules import tonnes_sold


class GoodsMarket(GoodsPricing, GoodsOffers):

    def __init__(self, sim):
        self._sim = sim

    @property
    def acting_party_id(self):
        """The party id of the seat asking now."""
        return self._sim.state.acting_seat

    # ---- the records ----

    def reset_draws(self):
        """Start a fresh count of what running works draw from the market."""
        self._sim._market_flows()["drawn"] = {}

    def note_draw(self, commodity, tonnes):
        """Running works used `tonnes` the founder neither held nor made."""
        if tonnes > 0:
            drawn = self._sim._market_flows()["drawn"]
            drawn[commodity] = drawn.get(commodity, 0.0) + tonnes

    # ---- reads ------------------------------------------------------------------------

    def drawn_tonnes(self, commodity):
        return self._sim._market_flows()["drawn"].get(commodity, 0.0)

    def posted_tonnes(self, side, commodity, seat_id=None):
        """Tonnes the seat (the asking one by default) has ordered to buy or sell of a commodity that the year's clearing has not
        yet settled."""
        return self._sim.economy.posted_goods_tonnes(seat_id or self.acting_party_id, side, commodity)

    def others_stamp(self):
        """What every seat but the asking one has ordered, comparable for equality, for caches whose answers read the posted
        price."""
        asking = self.acting_party_id
        return tuple((seat, tuple((order["side"], order["stock_key"], order["tonnes"], order["limit_per_tonne"]) for order in orders))
                     for seat, orders in sorted(self._sim.economy.posted_goods_orders().items()) if seat != asking)

    def seat_orders(self):
        """The asking seat's posted orders the year's clearing has not yet settled: [{"side", "material", "stock_key", "tonnes",
        "limit_per_tonne"}], in posting order."""
        keys = ("side", "material", "stock_key", "tonnes", "limit_per_tonne")
        return [{key: order[key] for key in keys} for order in self._sim.economy.posted_goods_orders(self.acting_party_id)]

    def seat_trades(self):
        """What the last clearing bought and sold for the asking seat: {"bought": {stock key: tonnes}, "sold": {stock key: tonnes}}."""
        economy = self._sim.economy
        return {side: economy.seat_traded_tonnes(self.acting_party_id, side) for side in ("bought", "sold")}

    def commodities_sold_by(self, seller_id):
        """Commodities this seat sold into the last clearing."""
        return sorted(self._sim.economy.seat_traded_tonnes(seller_id, "sold"))

    def state(self, material):
        """The market for one material as of now."""
        return self._sim.market_state(material)

    # ---- quotes -----------------------------------------------------------------------

    def quote(self, material):
        """Current buy and sell quote for a tonne of a material; None when it has no price. The buy price is the
        economy's price on the acting tile plus carriage, after what the seat has bought this year; the sell
        price is the same price less the fall a sale into that market causes. `making_cost_per_tonne` is what a
        held technique makes it for, None when none does."""
        sim = self._sim
        material = str(material or "").strip().lower()
        price = self.price_at_tile_per_tonne(material)
        if price is None:
            return None
        emp_key = sim._material_tag(material)[0]
        offered = sim.economy.agent_offered_tonnes(material)
        proceeds = self.sale_proceeds(material, 0.0, self.posted_tonnes("sell", emp_key))
        if proceeds is None:
            return None
        carriage = self._carriage_per_tonne(material, price)
        return {"material": material, "stock_key": emp_key,
                "buy_per_tonne": self.purchase_cost(material, 0.0)[1],
                "sell_per_tonne": proceeds[1],
                "price_at_tile_per_tonne": price, "price_kind": self.price_kind(material),
                "carriage_per_tonne": carriage,
                "making_cost_per_tonne": self.making_cost_per_tonne(material),
                "market_available_tonnes_per_year": (
                    offered if offered is not None else sim._material_market_tonnes(emp_key))}

    def price(self, material):
        """Money to buy one tonne now, or None when the material has no price."""
        quote = self.quote(material)
        return None if quote is None else quote["buy_per_tonne"]

    def _with_buyers(self, material, quote):
        """The quote with the tonnes the economy's buyers took and still wanted last year of the good the material is
        traded as, None where the economy does not trade it."""
        good = self._economy_good(material)
        record = None if good is None else self._sim.economy.agent_good_market_record(good)
        return {**quote, "buyers_take_tonnes_per_year": None if record is None else record["sold"] + record["unmet"]}

    @staticmethod
    def sale_room_tonnes(quote, sold_so_far):
        """Tonnes the market will still take from a seller this year: no more than the buyers took and still wanted last
        year where the economy trades the good (Complaint 668), whatever the sellers hold."""
        buyers_take = quote.get("buyers_take_tonnes_per_year")
        room = quote["market_available_tonnes_per_year"] if buyers_take is None else buyers_take
        return max(0.0, room - sold_so_far)

    def sale_limits(self, material):
        """(held tonnes not yet ordered sold, market room tonnes) for a sale."""
        quote = self.quote(material)
        if not quote:
            return 0.0, 0.0
        key = quote["stock_key"]
        ordered = self.posted_tonnes("sell", key)
        return (max(0.0, self._sim.material_stock_t(key) - ordered),
                self.sale_room_tonnes(self._with_buyers(material, quote), ordered))

    def quote_sell(self, material, tonnes):
        """(stock key, tonnes the market takes now, money for them): what a sale at today's quote would fetch, for refusals
        that quote a way to raise cash."""
        quote = self.quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return None, 0.0, 0.0
        key = quote["stock_key"]
        held, room = self.sale_limits(material)
        sold = tonnes_sold(tonnes, held, room)
        if sold <= 0:
            return key, 0.0, 0.0
        proceeds = self.sale_proceeds(material, sold, self.posted_tonnes("sell", key))
        if proceeds is None:
            return None, 0.0, 0.0
        return key, sold, proceeds[0]

    # ---- orders -----------------------------------------------------------------------

    def post_order(self, side, material, tonnes, limit_per_tonne=None):
        """Post the asking seat's order for the year's clearing: "buy" `tonnes` at no more than `limit_per_tonne`, or "sell" them
        (cut to the stock not already ordered sold) at no less; the quote's mean price over the order when no limit is given.
        Answers the posted order and the quote, or a refusal. The goods and the money move when the year clears."""
        quote = self.quote(material)
        tonnes = float(tonnes)
        if not quote:
            return Refusal("no_price", "%s has no price here, so it cannot be ordered." % material, material=material)
        if tonnes <= 0:
            return Refusal("no_quantity", "an order needs a quantity above zero.", material=material)
        key = quote["stock_key"]
        buying = side == "buy"
        if not buying:
            tonnes = min(tonnes, self.sale_limits(material)[0])
            if tonnes <= 0:
                return Refusal("not_enough_held", "no %s is held that is not already ordered sold." % material, material=material)
        mean = (self.purchase_cost(quote["material"], tonnes)[1] if buying
                else self.sale_proceeds(quote["material"], tonnes, self.posted_tonnes("sell", key))[1])
        limit = float(limit_per_tonne) if limit_per_tonne is not None else mean
        if buying and not self._sim.can_pay(limit * tonnes):
            return Refusal("cannot_pay", "the money for that order, at that limit, is not in hand.", material=material,
                           asked_tonnes=tonnes, limit_per_tonne=limit)
        self._sim.economy.post_goods_order(self.acting_party_id, {
            "side": side, "material": quote["material"], "good": self._economy_good(material), "stock_key": key,
            "tonnes": tonnes, "limit_per_tonne": limit})
        return {"posted": True, "side": side, "material": quote["material"], "tonnes": tonnes, "limit_per_tonne": limit,
                "quote_per_tonne": quote["buy_per_tonne"] if buying else quote["sell_per_tonne"]}
