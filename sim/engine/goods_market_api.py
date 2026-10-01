"""The one goods market: what every buyer and seller asks, and the only door to its records.

The founder, a firm, the state and the foreign traders deal with `Sim.goods_market`:

    quote_buy / quote_sell     what an order would cost or fetch, from the posted price
    buy / sell                 an order from a party (anything with money and goods; the founder
                               is `FounderParty`), priced along the curve the order climbs
    note_purchase / note_sale  tonnes a party bought or sold this year, counted in the same book
    price / price_ratio / state  what screens read

A party is identified by a string. The founder is `FOUNDER`; a firm or the state is its actor id.
A sale by the founder and by a firm are the same entry in the year's flows, so they move the
clearing price the same way (`sim/world/market.py`); the posted price leaves out the founder's own
orders only, which keep the marginal curves that move a bill as it is filled. The clearing itself
is in market_clearing.py; who offers what is in goods_market_offers.py.
"""
from . import purchase_rule
from .goods_market_offers import GoodsOffers
from .project_materials import tonnes_per_unit

FOUNDER = "founder"


class FounderParty:
    """The founder's money and stock, as a party to an order."""

    party_id = FOUNDER

    def __init__(self, sim):
        self._sim = sim

    def can_pay(self, money):
        return purchase_rule.can_pay(self._sim, money)

    def pay(self, money, purpose):
        self._sim.state.household.debit(money, purpose)

    def receive(self, money, purpose):
        self._sim.state.household.credit(money, purpose)

    def held(self, key):
        return self._sim.material_stock_t(key)

    def take_delivery(self, key, tonnes):
        sim = self._sim
        opening = sim._material_opening_stock()
        sim._material_stock()[key] += tonnes
        opening[key] = opening.get(key, 0.0) + tonnes
        sim.state.household._stock_throttle_sig = None

    def hand_over(self, key, tonnes):
        sim = self._sim
        opening = sim._material_opening_stock()
        sim._material_stock()[key] -= tonnes
        opening[key] = opening.get(key, 0.0) - tonnes
        sim.state.household._stock_throttle_sig = None


class GoodsMarket(GoodsOffers):

    def __init__(self, sim):
        self._sim = sim
        self.founder = FounderParty(sim)

    # ---- the records: the one place they are written -------------------------------------

    def note_sale(self, seller_id, commodity, tonnes):
        """`seller_id` sold `tonnes` of a commodity into the market this year."""
        if tonnes > 0:
            sold = self._sim._market_flows()["sold"].setdefault(commodity, {})
            sold[seller_id] = sold.get(seller_id, 0.0) + tonnes

    def note_purchase(self, buyer_id, commodity, tonnes):
        """`buyer_id` bought `tonnes` of a commodity at the market this year."""
        if tonnes > 0:
            bought = self._sim._market_flows()["bought"].setdefault(commodity, {})
            bought[buyer_id] = bought.get(buyer_id, 0.0) + tonnes

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
    def _total(parties, party_id=None, others=False):
        """Tonnes one party has, or every party's, or every party but the founder's; summed in party
        order so that a save and load cannot change the last digit."""
        if party_id is not None:
            return parties.get(party_id, 0.0)
        return sum(tonnes for party, tonnes in sorted(parties.items()) if not (others and party == FOUNDER))

    def sold_tonnes(self, commodity, seller_id=None):
        """Tonnes sold this year: by one seller, or by all of them."""
        return self._total(self._sim._market_flows()["sold"].get(commodity, {}), seller_id)

    def bought_tonnes(self, commodity, buyer_id=None):
        return self._total(self._sim._market_flows()["bought"].get(commodity, {}), buyer_id)

    def drawn_tonnes(self, commodity):
        return self._sim._market_flows()["drawn"].get(commodity, 0.0)

    def others_sold_tonnes(self, commodity):
        """What every seller but the founder put on the market this year."""
        return self._total(self._sim._market_flows()["sold"].get(commodity, {}), others=True)

    def others_bought_tonnes(self, commodity):
        return self._total(self._sim._market_flows()["bought"].get(commodity, {}), others=True)

    def others_stamp(self):
        """What every party but the founder has sold and bought this year, comparable for equality,
        for caches whose answers read the posted price."""
        flows = self._sim._market_flows()
        return tuple(
            tuple(sorted((commodity, tuple(sorted((party, tonnes) for party, tonnes in parties.items()
                                                  if party != FOUNDER)))
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
        per_kg = sim._material_price_per_kg(material)
        if per_kg is None:
            return None
        emp_key = sim._material_tag(material)[0]
        ratio = sim.market_price_ratio(emp_key)
        buy = (per_kg / tonnes_per_unit(material) * sim.price_index
               * sim.material_price_factor(emp_key) * ratio)
        return {"material": material, "stock_key": emp_key, "buy_per_tonne": buy,
                "market_price_ratio": ratio,
                "sell_per_tonne": buy * sim.MATERIAL_TRADE_SELL_SHARE_OF_BUY,
                "market_available_tonnes_per_year": sim._material_market_tonnes(emp_key)}

    def price(self, material):
        """Money to buy one tonne now, or None when the material has no price."""
        quote = self.quote(material)
        return None if quote is None else quote["buy_per_tonne"]

    def purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as
        the order is filled. None when it has no price."""
        sim = self._sim
        unit_price = sim._material_price_per_kg(material)
        if unit_price is None:
            return None
        emp_key, tag = sim._material_tag(material)
        per_tonne = (unit_price / tonnes_per_unit(material) * sim.price_index
                     * sim.market_price_ratio(emp_key))
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
        seller = seller or self.founder
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
