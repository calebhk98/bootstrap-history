"""The one goods market: what every buyer and seller asks, and the only door to its records.

The founder, a firm, the state and the foreign traders deal with `Sim.goods_market`:

    quote_buy / quote_sell     what an order would cost or fetch, from the posted price
    buy / sell                 an order from a party (anything with money and goods; a seat
                               is a `SeatParty`), priced along the curve the order climbs
    note_purchase / note_sale  tonnes a party bought or sold this year, counted in the same book
    price / price_ratio / state  what screens read

A party is identified by a string. A seat is its seat id (`state.acting_seat` for the asking seat);
a firm or the state is its actor id. A sale by a seat and by a firm are the same entry in the year's
flows, so they move the clearing price the same way (`sim/world/market.py`); the posted price leaves
out the asking seat's own orders only, which keep the marginal curves that move a bill as it is filled. The clearing itself
is in market_clearing.py; who offers what is in goods_market_offers.py.
"""
from sim.world.producer_market import Offer

from . import purchase_rule
from .goods_market_offers import GoodsOffers
from .project_materials import tonnes_per_unit
from sim.agents.api import edges

class SeatParty:
    """One seat's money and stock, as a party to an order; every act runs as that seat."""

    def __init__(self, sim, seat_id):
        self._sim = sim
        self.party_id = seat_id

    def can_pay(self, money):
        with self._sim.act_as(self.party_id):
            return purchase_rule.can_pay(self._sim, money)

    def pay(self, money, purpose):
        with self._sim.act_as(self.party_id):
            self._sim.pay_edge(edges.EDGE_MARKET, money, purpose)

    def receive(self, money, purpose):
        with self._sim.act_as(self.party_id):
            self._sim.receive_from_edge(edges.EDGE_MARKET, money, purpose)

    def held(self, key):
        with self._sim.act_as(self.party_id):
            return self._sim.material_stock_t(key)

    def take_delivery(self, key, tonnes):
        self._move_stock(key, tonnes)

    def hand_over(self, key, tonnes):
        self._move_stock(key, -tonnes)

    def _move_stock(self, key, tonnes):
        sim = self._sim
        with sim.act_as(self.party_id):
            opening = sim._material_opening_stock()
            sim._material_stock()[key] += tonnes
            opening[key] = opening.get(key, 0.0) + tonnes
            sim.state.household._stock_throttle_sig = None


class GoodsMarket(GoodsOffers):

    def __init__(self, sim):
        self._sim = sim
        self._seat_parties = {}

    @property
    def acting_party_id(self):
        """The party id of the seat asking now."""
        return self._sim.state.acting_seat

    def seat_party(self, seat_id):
        """The party for one seat, the same object every time."""
        party = self._seat_parties.get(seat_id)
        if party is None:
            party = self._seat_parties[seat_id] = SeatParty(self._sim, seat_id)
        return party

    @property
    def acting(self):
        """The party for the seat asking now."""
        return self.seat_party(self._sim.state.acting_seat)

    # ---- the records: the one place they are written -------------------------------------

    def note_sale(self, seller_id, commodity, tonnes, reservation_ratio=None):
        """`seller_id` sold `tonnes` of a commodity into the market this year. A seller that names the
        lowest price it takes (its cost, as a ratio to the market's reference) sells only at or above
        it; one that names none takes whatever the market pays."""
        if tonnes > 0:
            flows = self._sim._market_flows()
            sold = flows["sold"].setdefault(commodity, {})
            before = sold.get(seller_id, 0.0)
            sold[seller_id] = before + tonnes
            reservations = flows.setdefault("reservation", {})
            if reservation_ratio is not None:
                held = reservations.setdefault(commodity, {})
                held[seller_id] = (held.get(seller_id, reservation_ratio) * before
                                   + reservation_ratio * tonnes) / (before + tonnes)
            elif seller_id in reservations.get(commodity, {}):
                del reservations[commodity][seller_id]

    def note_purchase(self, buyer_id, commodity, tonnes):
        """`buyer_id` bought `tonnes` of a commodity at the market this year."""
        if tonnes > 0:
            bought = self._sim._market_flows()["bought"].setdefault(commodity, {})
            bought[buyer_id] = bought.get(buyer_id, 0.0) + tonnes

    def forget(self, party_id):
        """A party's entries from earlier years are over: it is about to deal again this year, or has
        stopped. Its sales and purchases of this year are noted afterwards."""
        flows = self._sim._market_flows()
        for kind in ("sold", "bought", "reservation"):
            flows.setdefault(kind, {})
            for commodity in list(flows[kind]):
                flows[kind][commodity].pop(party_id, None)
                if not flows[kind][commodity]:
                    del flows[kind][commodity]

    def reset_draws(self):
        """Start a fresh count of what running works draw from the market."""
        self._sim._market_flows()["drawn"] = {}

    def note_draw(self, commodity, tonnes):
        """Running works used `tonnes` the founder neither held nor made."""
        if tonnes > 0:
            drawn = self._sim._market_flows()["drawn"]
            drawn[commodity] = drawn.get(commodity, 0.0) + tonnes

    def add_stock(self, material, tonnes):
        """Goods appear in the society's hands (a windfall, a confiscation sold on): they join this
        year's supply."""
        sim = self._sim
        entry = sim._market_entry(sim._material_tag(material)[0])
        if entry is not None and tonnes > 0:
            entry["stock_tonnes"] += tonnes

    # ---- reads ------------------------------------------------------------------------

    @staticmethod
    def _total(parties, party_id=None, except_party=None):
        """Tonnes one party has, or every party's, or every party but `except_party`'s; summed in party
        order so that a save and load cannot change the last digit."""
        if party_id is not None:
            return parties.get(party_id, 0.0)
        return sum(tonnes for party, tonnes in sorted(parties.items()) if party != except_party)

    def sold_tonnes(self, commodity, seller_id=None):
        """Tonnes sold this year: by one seller, or by all of them."""
        return self._total(self._sim._market_flows()["sold"].get(commodity, {}), seller_id)

    def bought_tonnes(self, commodity, buyer_id=None):
        return self._total(self._sim._market_flows()["bought"].get(commodity, {}), buyer_id)

    def drawn_tonnes(self, commodity):
        return self._sim._market_flows()["drawn"].get(commodity, 0.0)

    def others_offers(self, commodity):
        """Offers of every seller but the asking seat that named the lowest price it takes: (tonnes, ratio)."""
        flows = self._sim._market_flows()
        sold = flows["sold"].get(commodity, {})
        reservations = flows.get("reservation", {}).get(commodity, {})
        return tuple(Offer(sold[party], reservations[party])
                     for party in sorted(reservations) if party != self.acting_party_id and sold.get(party, 0.0) > 0.0)

    def others_sold_tonnes(self, commodity):
        """What every seller but the asking seat put on the market this year."""
        return self._total(self._sim._market_flows()["sold"].get(commodity, {}), except_party=self.acting_party_id)

    def others_bought_tonnes(self, commodity):
        return self._total(self._sim._market_flows()["bought"].get(commodity, {}), except_party=self.acting_party_id)

    def others_stamp(self):
        """What every party but the asking seat has sold and bought this year, comparable for equality,
        for caches whose answers read the posted price."""
        flows = self._sim._market_flows()
        asking = self.acting_party_id
        return tuple(
            tuple(sorted((commodity, tuple(sorted((party, tonnes) for party, tonnes in parties.items()
                                                  if party != asking)))
                         for commodity, parties in flows[kind].items()))
            for kind in ("sold", "bought"))

    def commodities_sold_by(self, seller_id):
        """Commodities this seller has sold into the market this year."""
        return sorted(commodity for commodity, sold in self._sim._market_flows()["sold"].items()
                      if sold.get(seller_id, 0.0) > 0.0)

    def price_ratio(self, material):
        """This year's posted spot price over the long-run cost; one where no market exists."""
        return self._sim.market_price_ratio(material)

    def state(self, material):
        """The market for one material as of now."""
        return self._sim.market_state(material)

    # ---- quotes -----------------------------------------------------------------------

    def quote(self, material):
        """Current buy and sell quote for a tonne of a material; None when it has no price."""
        sim = self._sim
        material = str(material or "").strip().lower()
        per_kg = self.unit_price(material)
        if per_kg is None:
            return None
        emp_key = sim._material_tag(material)[0]
        ratio = sim.market_price_ratio(material)
        brought = self.import_tonnes_available(material)      # a partner's good: its supply and the carriers' lift
        buy = (per_kg / tonnes_per_unit(material) * sim.price_index
               * sim.material_price_factor(emp_key) * ratio)
        return {"material": material, "stock_key": emp_key, "buy_per_tonne": buy,
                "market_price_ratio": ratio,
                "sell_per_tonne": buy * sim.MATERIAL_TRADE_SELL_SHARE_OF_BUY,
                "market_available_tonnes_per_year": (
                    sim._material_market_tonnes(emp_key) if brought is None else brought)}

    def price(self, material):
        """Money to buy one tonne now, or None when the material has no price."""
        quote = self.quote(material)
        return None if quote is None else quote["buy_per_tonne"]

    def purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as
        the order is filled. None when it has no price."""
        sim = self._sim
        unit_price = self.unit_price(material)
        if unit_price is None:
            return None
        emp_key, tag = sim._material_tag(material)
        per_tonne = (unit_price / tonnes_per_unit(material) * sim.price_index
                     * sim.market_price_ratio(material))
        factor = sim._price_factor_across_purchase(emp_key, tag, already, max(0.0, tonnes))
        return per_tonne * factor * max(0.0, tonnes), per_tonne * factor

    def quote_buy(self, material, tonnes, already=0.0):
        """What an order of `tonnes` costs: (money, mean money per tonne), or None."""
        return self.purchase_cost(material, tonnes, already)

    def sale_proceeds(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) for selling `tonnes` more after `already` tonnes sold this
        year. TEMPORARY HEURISTIC: the sell price is the quoted one divided by the same
        demand-pressure factor buying climbs, so a bigger sale fetches a lower mean price."""
        sim = self._sim
        quote = self.quote(material)
        if not quote or tonnes <= 0:
            return 0.0, 0.0
        emp_key, tag = sim._material_tag(quote["material"])
        baseline = sim._price_factor_across_purchase(emp_key, tag, 0.0, 0.0)
        across = sim._price_factor_across_purchase(emp_key, tag, already, tonnes)
        mean_price = quote["sell_per_tonne"] * baseline / max(across, baseline)
        return mean_price * tonnes, mean_price

    def quote_sell(self, material, tonnes, seller=None):
        """(stock key, tonnes the market takes now, money for them): the one figure `sell` pays
        and refusals quote as a way to raise cash."""
        seller = seller or self.acting
        quote = self.quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return None, 0.0, 0.0
        key = quote["stock_key"]
        sold_so_far = self.sold_tonnes(key, seller.party_id)
        absorbs = max(0.0, quote["market_available_tonnes_per_year"] - sold_so_far)
        sold = min(tonnes, seller.held(key), absorbs)
        if sold <= 0:
            return key, 0.0, 0.0
        return key, sold, self.sale_proceeds(material, sold, sold_so_far)[0]

    # ---- orders -----------------------------------------------------------------------

    def settle_purchase(self, buyer, key, tonnes, money, purpose="materials bought"):
        """The one place a purchase happens: the buyer pays, the book counts it, the goods arrive."""
        buyer.pay(money, purpose)
        self.note_purchase(buyer.party_id, key, tonnes)
        buyer.take_delivery(key, tonnes)

    def settle_import(self, buyer, key, tonnes, money, purpose):
        """A purchase from a foreign seller: the buyer pays and the goods arrive. It is not counted in
        the home book, since the tonnes never came out of the home supply."""
        buyer.pay(money, purpose)
        buyer.take_delivery(key, tonnes)

    def buy(self, buyer, material, tonnes):
        """Buy a material for a party: the order is cut to what the market sells in a year, and
        the price climbs as it is filled. Returns the tonnes bought."""
        quote = self.quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        tonnes = min(tonnes, quote["market_available_tonnes_per_year"])
        if tonnes <= 0:
            return 0.0
        cost = self.purchase_cost(quote["material"], tonnes)[0]
        if not buyer.can_pay(cost):
            return 0.0
        self.settle_purchase(buyer, quote["stock_key"], tonnes, cost)
        return tonnes

    def sell(self, seller, material, tonnes):
        """Sell stock for a party: the order is cut to what the market absorbs in a year, and the
        price falls as the year's sales add up. Returns the tonnes sold."""
        key, sold, money = self.quote_sell(material, tonnes, seller)
        if sold <= 0:
            return 0.0
        self.note_sale(seller.party_id, key, sold)
        seller.hand_over(key, sold)
        seller.receive(money, "materials sold")
        return sold
