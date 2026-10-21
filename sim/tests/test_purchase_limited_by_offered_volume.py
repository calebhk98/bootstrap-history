"""Complaint 507, stage 4: the founder cannot buy more of a material in a year than the sellers on his tile's market
offered at the last clearing; the quote's figure is the economy's own, not the engine's reference tonnes.
`GoodsMarket.quote` and `buy` run on a market whose price, partner and economy reads are stubbed; the live economy's offer
is test_purchase_limited_by_offered_volume_scenario."""
QUICK_TOPIC = True

import math
from types import SimpleNamespace

from .harness import check

from sim.engine.goods_market_api import GoodsMarket

OFFERED = 40.0
REFERENCE = 7.0


class _Buyer:
    party_id = "buyer"

    def __init__(self):
        self.paid, self.delivered = 0.0, 0.0

    def can_pay(self, money):
        return True

    def pay(self, money, purpose):
        self.paid += money

    def take_delivery(self, key, tonnes):
        self.delivered += tonnes


class _Market(GoodsMarket):
    """A market with one good at a flat price; the book of purchases is a dict."""

    def __init__(self, offered, brought=None):
        economy = SimpleNamespace(agent_offered_tonnes=lambda material, tile=None: offered)
        sim = SimpleNamespace(economy=economy, state=SimpleNamespace(acting_seat="seat"),
                              _material_tag=lambda material: (material, None),
                              _material_market_tonnes=lambda key: REFERENCE)
        super().__init__(sim)
        self.brought = brought
        self.book = {}
        self.acting_buyer = _Buyer()

    def price_at_tile_per_tonne(self, material):
        return 10.0

    def import_tonnes_available(self, material, partner=None):
        return self.brought

    def _carriage_per_tonne(self, material, price_per_tonne):
        return 1.0

    def making_cost_per_tonne(self, material):
        return 5.0

    def price_kind(self, material):
        return "traded"

    def purchase_cost(self, material, tonnes, already=0.0):
        return 11.0 * tonnes, 11.0

    def sale_proceeds(self, material, tonnes, already=0.0):
        return 10.0 * tonnes, 10.0

    def sold_tonnes(self, commodity, seller_id=None):
        return 0.0

    def bought_tonnes(self, commodity, buyer_id=None):
        return self.book.get(commodity, 0.0)

    def note_purchase(self, buyer_id, commodity, tonnes):
        self.book[commodity] = self.book.get(commodity, 0.0) + tonnes


market = _Market(OFFERED)
quote = market.quote("wheat")
check("the quote's market figure is the economy's offered quantity, not the reference tonnes",
      quote["market_available_tonnes_per_year"] == OFFERED, quote)
check("a partner's good is quoted at what the partner can bring",
      _Market(OFFERED, brought=12.5).quote("wheat")["market_available_tonnes_per_year"] == 12.5)
check("with no economy book and no partner the engine's reference tonnes stand",
      _Market(None).quote("wheat")["market_available_tonnes_per_year"] == REFERENCE)
check("a partner's unlimited supply is not cut", math.isinf(_Market(OFFERED, brought=math.inf).quote("wheat")["market_available_tonnes_per_year"]))

check("the room left is the offer less what the buyer already took",
      GoodsMarket.market_room_tonnes(quote, 15.0) == OFFERED - 15.0 and GoodsMarket.market_room_tonnes(quote, 99.0) == 0.0)

buyer = market.acting_buyer
bought = market.buy(buyer, "wheat", 10.0 * OFFERED)
check("an order of ten times the offer is cut to the offer", abs(bought - OFFERED) <= 1e-9 * OFFERED, bought)
check("...and is paid for and delivered at that quantity", buyer.delivered == OFFERED and buyer.paid == 11.0 * OFFERED,
      (buyer.delivered, buyer.paid))
check("...and nothing more can be bought that year", market.buy(buyer, "wheat", OFFERED) == 0.0)

partial = _Market(OFFERED)
partial.book["wheat"] = 30.0
check("a buyer who already took part of the offer can take only the rest",
      partial.buy(partial.acting_buyer, "wheat", OFFERED) == OFFERED - 30.0)
