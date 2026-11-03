"""Complaint 507, stage 4: the quote's market figure is the economy's own offered quantity, not the engine's reference tonnes.
`GoodsMarket.quote` runs on a market whose price, partner and economy reads are stubbed."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.markets.goods_market import GoodsMarket

OFFERED = 40.0
REFERENCE = 7.0


class _Market(GoodsMarket):
    """A market with one good at a flat price."""

    def __init__(self, offered):
        economy = SimpleNamespace(agent_offered_tonnes=lambda material, tile=None: offered)
        sim = SimpleNamespace(economy=economy, state=SimpleNamespace(acting_seat="seat"),
                              _material_tag=lambda material: (material, None),
                              _material_market_tonnes=lambda key: REFERENCE)
        super().__init__(sim)
        self.pricing = SimpleNamespace(
            price_at_tile_per_tonne=lambda material: 10.0, carriage_per_tonne=lambda material, price_per_tonne: 1.0,
            making_cost_per_tonne=lambda material: 5.0, price_kind=lambda material: "traded",
            purchase_cost=lambda material, tonnes, already=0.0: (11.0 * tonnes, 11.0),
            sale_proceeds=lambda material, tonnes, already=0.0: (10.0 * tonnes, 10.0))

    def posted_tonnes(self, side, commodity, seat_id=None):
        return 0.0


market = _Market(OFFERED)
quote = market.quote("wheat")
check("the quote's market figure is the economy's offered quantity, not the reference tonnes",
      quote["market_available_tonnes_per_year"] == OFFERED, quote)
check("with no economy book the engine's reference tonnes stand",
      _Market(None).quote("wheat")["market_available_tonnes_per_year"] == REFERENCE)
