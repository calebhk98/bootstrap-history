"""The one goods market: what every buyer and seller asks, and the only door to its records.

The founder, a firm, the state and the foreign traders deal with `Sim.goods_market`:

    quote_buy / quote_sell     what an order would cost or fetch: the economy's price on the acting tile, carriage, and the
                               climb the economy's own book gives the order (goods_pricing.py)
    post_order                 a seat's order for the year's clearing, at its price limit; nothing settles until then
                               (port_goods_orders.py), as a seat's hires do

A seat is identified by its seat id (`state.acting_seat` for the asking seat); a firm or the state by its actor id. A seat's
orders and an actor's reach the same clearing, which sets the price. The asking seat's own orders keep the marginal curves
that move a bill as it is filled. Who offers what is in goods_offers.py.
"""
from sim.refusal import Refusal
from sim.rekey import rekey

from . import port_goods_orders
from .goods_offers import GoodsOffers
from .goods_pricing import GoodsPricing
from .rules import tonnes_sold


class GoodsMarket:
    """The goods market. Its concerns are parts, addressed as `goods_market.<part>.<method>`:

        pricing   the price at the acting tile, carriage and the climb over an order   (goods_pricing.py)
        offers    who sells what and the household price table                          (goods_offers.py)"""

    def __init__(self, sim):
        self._sim = sim
        self.offers = GoodsOffers(sim)
        self.pricing = GoodsPricing(sim, self)

    @property
    def _stored(self):
        """The record the seats' posted orders and the last clearing's trades are kept in."""
        return self._sim.economy.agent.stored

    @property
    def acting_party_id(self):
        """The party id of the seat asking now."""
        return self._sim.state.acting_seat

    # ---- the records ----

    def reset_draws(self):
        """Start a fresh count of what the asking seat's running works draw from the market; other seats' counts stay."""
        self._sim.market_flows()["drawn"][self.acting_party_id] = {}

    def note_draw(self, commodity, tonnes):
        """The asking seat's running works used `tonnes` it neither held nor made."""
        if tonnes > 0:
            drawn = self._sim.market_flows()["drawn"].setdefault(self.acting_party_id, {})
            drawn[commodity] = drawn.get(commodity, 0.0) + tonnes

    def rename_draws(self, old, new):
        """A seat handed over: its draws this year are kept under the new id."""
        rekey(self._sim.market_flows()["drawn"], old, new)

    # ---- reads ------------------------------------------------------------------------

    def drawn_tonnes(self, commodity, seat_id=None):
        """Tonnes of a commodity the seat's (the asking one by default) running works drew from the market this year."""
        return self._sim.market_flows()["drawn"].get(seat_id or self.acting_party_id, {}).get(commodity, 0.0)

    def posted_tonnes(self, side, commodity, seat_id=None):
        """Tonnes the seat (the asking one by default) has ordered to buy or sell of a commodity that the year's clearing has not
        yet settled."""
        return port_goods_orders.posted_tonnes(self._stored, seat_id or self.acting_party_id, side, commodity)

    def others_stamp(self):
        """What every seat but the asking one has ordered, comparable for equality, for caches whose answers read the posted
        price."""
        asking = self.acting_party_id
        return tuple((seat, tuple((order["side"], order["stock_key"], order["tonnes"], order["limit_per_tonne"]) for order in orders))
                     for seat, orders in sorted(port_goods_orders.posted_orders(self._stored).items()) if seat != asking)

    def seat_orders(self):
        """The asking seat's posted orders the year's clearing has not yet settled: [{"side", "material", "stock_key", "tonnes",
        "limit_per_tonne", "carriage_per_tonne", "cost_factor", "project"}], in posting order."""
        keys = ("side", "material", "stock_key", "tonnes", "limit_per_tonne", "carriage_per_tonne", "cost_factor", "project")
        return [{key: order.get(key) for key in keys} for order in port_goods_orders.posted_orders(self._stored, self.acting_party_id)]

    def seat_trades(self):
        """What the last clearing bought and sold for the asking seat: {"bought": {stock key: tonnes}, "sold": {stock key: tonnes},
        "orders": [one result per order handled, a refused one with its cause]}."""
        trades = {side: port_goods_orders.traded_tonnes(self._stored, self.acting_party_id, side) for side in ("bought", "sold")}
        trades["orders"] = port_goods_orders.order_results(self._stored, self.acting_party_id)
        return trades

    def commodities_sold_by(self, seller_id):
        """Commodities this seat sold into the last clearing."""
        return sorted(port_goods_orders.traded_tonnes(self._stored, seller_id, "sold"))

    # ---- quotes -----------------------------------------------------------------------

    def quote(self, material):
        """Current buy and sell quote for a tonne of a material; None when it has no price. The buy price is the
        economy's price on the acting tile plus carriage, after what the seat has bought this year; the sell
        price is the same price less the fall a sale into that market causes. `making_cost_per_tonne` is what a
        held technique makes it for, None when none does."""
        sim = self._sim
        material = str(material or "").strip().lower()
        price = self.pricing.price_at_tile_per_tonne(material)
        if price is None:
            return None
        emp_key = sim.materials.tag(material)[0]
        good = self.pricing.economy_good(material)
        offered = None if good is None else sim.economy.agent_offered_tonnes(good)
        proceeds = self.pricing.sale_proceeds(material, 0.0, self.posted_tonnes("sell", emp_key))
        if proceeds is None:
            return None
        carriage = self.pricing.carriage_per_tonne(material, price)
        return {"material": material, "stock_key": emp_key,
                "buy_per_tonne": self.pricing.purchase_cost(material, 0.0)[1],
                "sell_per_tonne": proceeds[1],
                "price_at_tile_per_tonne": price, "price_kind": self.pricing.price_kind(material),
                "carriage_per_tonne": carriage,
                "making_cost_per_tonne": self.pricing.making_cost_per_tonne(material),
                "market_available_tonnes_per_year": (
                    offered if offered is not None else sim.materials.market_tonnes(emp_key))}

    def _with_buyers(self, material, quote):
        """The quote with the tonnes the economy's buyers took and still wanted last year of the good the material is
        traded as, None where the economy does not trade it."""
        good = self.pricing.economy_good(material)
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
        return (max(0.0, self._sim.materials.stock_t(key) - ordered),
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
        proceeds = self.pricing.sale_proceeds(material, sold, self.posted_tonnes("sell", key))
        if proceeds is None:
            return None, 0.0, 0.0
        return key, sold, proceeds[0]

    # ---- orders -----------------------------------------------------------------------

    def cancel_orders(self, side, material):
        """Withdraw the asking seat's own posted orders to `side` a material, which nothing has settled yet: {"cancelled": count,
        "tonnes": total, "kept_for_projects": [project]}, or a refusal with a cause when it has none. An order a project placed
        is kept (cause `belongs_to_project`): the project waits for its result, so stop the project instead."""
        material = str(material or "").strip().lower()
        count, tonnes, projects = port_goods_orders.cancel_orders(self._stored, self.acting_party_id, side, material)
        if not count and projects:
            return Refusal("belongs_to_project", "the order to %s %s belongs to %s; stop the project to end it." % (side, material, ", ".join(projects)),
                           material=material, side=side, projects=projects)
        if not count:
            return Refusal("no_such_order", "no order to %s %s is posted." % (side, material), material=material, side=side)
        return {"cancelled": count, "tonnes": tonnes, "side": side, "material": material, "kept_for_projects": projects}

    def post_order(self, side, material, tonnes, limit_per_tonne=None, project=None, cost_factor=1.0, limit_includes_carriage=False):
        """Post the asking seat's order for the year's clearing: "buy" `tonnes` paying the market no more than `limit_per_tonne`,
        or "sell" them (cut to the stock not already ordered sold) at no less; the quote's mean price over the order when no limit
        is given. A buy's carriage to the seat's tile, and `cost_factor` (a project's opposition and geography) on the money, are
        charged when the goods arrive; the reply states them. Refused with a cause when the good is not traded, when the seat
        already has an order the other way in the same good (it would trade with itself), or when the seat's money, counting what
        its other orders and its staff will draw, would not cover. The goods and the money move when the year clears."""
        quote = self.quote(material)
        tonnes = float(tonnes)
        if not quote:
            return Refusal("no_price", "%s has no price here, so it cannot be ordered." % material, material=material)
        if tonnes <= 0:
            return Refusal("no_quantity", "an order needs a quantity above zero.", material=material)
        good = self.pricing.economy_good(material)
        if good is None:
            return Refusal("not_traded", "%s is not traded in the economy, so it cannot be ordered." % material, material=material)
        key = quote["stock_key"]
        buying = side == "buy"
        economy = self._sim.economy
        for other in port_goods_orders.posted_orders(self._stored, self.acting_party_id):
            if other["side"] != side and other["good"] == good:
                return Refusal("opposite_order_posted", "an order to %s %s is already posted this year; a seat does not trade with "
                               "itself, so this order is refused (withdraw that one first with the cancel-orders command)." % (other["side"], material),
                               material=material, posted_side=other["side"])
        if not buying:
            tonnes = min(tonnes, self.sale_limits(material)[0])
            if tonnes <= 0:
                return Refusal("not_enough_held", "no %s is held that is not already ordered sold." % material, material=material)
        carriage = quote["carriage_per_tonne"] if buying else 0.0
        mean = (self.pricing.purchase_cost(quote["material"], tonnes)[1] - carriage if buying
                else self.pricing.sale_proceeds(quote["material"], tonnes, self.posted_tonnes("sell", key))[1])
        limit = float(limit_per_tonne) if limit_per_tonne is not None else mean
        if buying and limit_per_tonne is not None and limit_includes_carriage:
            limit -= carriage
        if limit <= 0:
            return Refusal("no_limit", "an order needs a price limit above zero%s." % (" once carriage is counted" if buying else ""),
                           material=material, limit_per_tonne=limit)
        order = {"side": side, "material": quote["material"], "good": good, "stock_key": key, "tonnes": tonnes,
                 "limit_per_tonne": limit, "carriage_per_tonne": carriage, "cost_factor": float(cost_factor), "project": project}
        committed = None
        if buying:
            committed = port_goods_orders.reserve(order)[0]
            if not self._sim.finance.can_pay(committed + economy.seat_committed_money(self.acting_party_id)):
                return Refusal("cannot_pay", "the money for that order, at that limit and with carriage, is not in hand once the "
                               "seat's other orders and its staff are counted.", material=material, asked_tonnes=tonnes,
                               limit_per_tonne=limit, needs_money=committed)
        order_id = port_goods_orders.add_order(self._stored, self.acting_party_id, order)
        return {"posted": True, "order_id": order_id, "side": side, "material": quote["material"], "tonnes": tonnes, "limit_per_tonne": limit,
                "carriage_per_tonne": carriage, "cost_factor": order["cost_factor"], "committed_money": committed,
                "quote_per_tonne": (quote["buy_per_tonne"] - carriage if buying else quote["sell_per_tonne"]),
                "quote_carriage_per_tonne": carriage}
