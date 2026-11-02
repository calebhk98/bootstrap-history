"""Complaint 507, stage 4: the quote's market figure is the economy's own offered quantity, not the engine's reference tonnes.
`GoodsMarket.quote` runs on a market whose price, partner and economy reads are stubbed."""
QUICK_TOPIC = True

import math
from types import SimpleNamespace

from .harness import check

from sim.markets.goods_market import GoodsMarket

OFFERED = 40.0
REFERENCE = 7.0


class _Market(GoodsMarket):
    """A market with one good at a flat price."""

    def __init__(self, offered, brought=None):
        economy = SimpleNamespace(agent_offered_tonnes=lambda material, tile=None: offered)
        sim = SimpleNamespace(economy=economy, state=SimpleNamespace(acting_seat="seat"),
                              _material_tag=lambda material: (material, None),
                              _material_market_tonnes=lambda key: REFERENCE)
        super().__init__(sim)
        self.brought = brought

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

    def posted_tonnes(self, side, commodity, seat_id=None):
        return 0.0


market = _Market(OFFERED)
quote = market.quote("wheat")
check("the quote's market figure is the economy's offered quantity, not the reference tonnes",
      quote["market_available_tonnes_per_year"] == OFFERED, quote)
check("a partner's good is quoted at what the partner can bring",
      _Market(OFFERED, brought=12.5).quote("wheat")["market_available_tonnes_per_year"] == 12.5)
check("with no economy book and no partner the engine's reference tonnes stand",
      _Market(None).quote("wheat")["market_available_tonnes_per_year"] == REFERENCE)
check("a partner's unlimited supply is not cut", math.isinf(_Market(OFFERED, brought=math.inf).quote("wheat")["market_available_tonnes_per_year"]))
