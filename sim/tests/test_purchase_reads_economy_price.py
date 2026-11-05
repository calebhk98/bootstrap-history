"""Complaint 507, stage 3: what the founder pays and is paid is the agent economy's price on the founder's tile plus
carriage, a larger order costs more a tonne, a good no one sells has no price, and the coin metal is one number wherever the
game counts it. The market runs on a stub sim (its economy's prices, book and carriage set by the test). The project bill (tonnes times the founder's price) is
test_complaint_147_project_materials::test_the_missing_part_is_priced_at_the_market_quote."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.data import load_civ
from sim.tests import market_stand_in
from sim.markets import port_money
from sim.markets.goods_market import GoodsMarket
from sim.markets.goods_offers import GoodsOffers
from sim.markets.unit_mass import tonnes_per_unit
from sim.foreign_trade.module import ForeignTrade
from sim.tests import module_harness

WHEAT = "wheat_kg"
COIN_METAL = "silver_kg"
OFFERED_TONNES = 100.0
CARRIAGE = 1.5


class _Economy:
    """An economy whose prices on the acting tile are `paid` (money a unit) and whose book of the staple offers
    OFFERED_TONNES; buying adds to the price in proportion to the share of the offer taken, selling takes it off."""

    def __init__(self, paid):
        self.paid = paid

    def agent_prices_at(self, tile=None):
        return self.paid

    def agent_price_kind(self, good):
        return "traded" if self.paid is not None and good in self.paid else None

    def acting_tile(self):
        return "tile"

    def agent_offered_tonnes(self, good, tile=None):
        return OFFERED_TONNES

    def agent_price_response(self, good, sold, bought, tile=None):
        return 1.0 + bought / OFFERED_TONNES - 0.5 * sold / OFFERED_TONNES / (1.0 + sold / OFFERED_TONNES)


class _Offers(GoodsOffers):
    def offered_by(self, material):
        return "home" if material in self._sim.materials.prices() else None

    def household_prices(self):
        return {}


class _Market(GoodsMarket):
    """The market on a stub sim; the table of who sells what is a home seller for every priced good."""

    def __init__(self, paid, cost_table=None):
        self.economy = _Economy(paid)
        sim = SimpleNamespace(
            economy=self.economy, **market_stand_in.market_memory(), state=SimpleNamespace(acting_seat="seat"),
            materials=SimpleNamespace(
                prices=lambda: dict(cost_table if cost_table is not None else paid),
                priced_key=lambda material, prices: material if material in prices else None,
                tag=lambda material: (material, None),
                price_per_unit=lambda material: (cost_table if cost_table is not None else paid).get(material)),
            foreign=SimpleNamespace(material_carriage_per_tonne=lambda key, price: CARRIAGE))
        super().__init__(sim)
        self.offers = _Offers(sim)
        self.bought = {}

    def posted_tonnes(self, side, commodity, seat_id=None):
        return self.bought.get(commodity, 0.0) if side == "buy" else 0.0

    def drawn_tonnes(self, commodity):
        return 0.0


PAID = {WHEAT: 0.004, COIN_METAL: 0.9}
market = _Market(PAID)
per_tonne = PAID[WHEAT] / tonnes_per_unit(WHEAT)

# a tonne costs the economy's price on the tile plus carriage
quote = market.quote(WHEAT)
check("the founder's quote of the staple has the economy's price on the tile in it",
      abs(quote["price_at_tile_per_tonne"] - per_tonne) <= 1e-9 * per_tonne, (quote["price_at_tile_per_tonne"], per_tonne))
check("...and a tonne costs that price plus carriage, climbed by what the seat has bought this year",
      quote["buy_per_tonne"] >= quote["price_at_tile_per_tonne"] + quote["carriage_per_tonne"] - 1e-9
      and quote["carriage_per_tonne"] == CARRIAGE, quote)
small = market.pricing.purchase_cost(WHEAT, 1e-6)[1]
check("a very small order costs the quote", abs(small / quote["buy_per_tonne"] - 1.0) < 1e-3, (small, quote["buy_per_tonne"]))
check("the cost of making is a cost: it is not what the quote asks",
      quote["making_cost_per_tonne"] is not None and abs(quote["buy_per_tonne"] - quote["making_cost_per_tonne"]) > 1e-9, quote)
priced_dearer = _Market(PAID, cost_table={WHEAT: 0.001, COIN_METAL: 0.9})
check("the price is the economy's where it has a market, whatever the cost table says",
      abs(priced_dearer.quote(WHEAT)["price_at_tile_per_tonne"] - per_tonne) <= 1e-9 * per_tonne)
costed_only = _Market({COIN_METAL: 0.9}, cost_table={WHEAT: 0.002, COIN_METAL: 0.9})
check("a good the economy has no market for has no price, whatever the cost table says", costed_only.quote(WHEAT) is None)
opening = _Market(None, cost_table={WHEAT: 0.002, COIN_METAL: 0.9})
check("while the economy opens, the cost table's price answers",
      abs(opening.quote(WHEAT)["price_at_tile_per_tonne"] - 0.002 / tonnes_per_unit(WHEAT)) < 1e-9)

# a larger order costs more a tonne; a larger sale fetches less
means = [market.pricing.purchase_cost(WHEAT, OFFERED_TONNES * share)[1] for share in (0.001, 0.05, 0.3, 0.99)]
check("a larger order costs more a tonne", means == sorted(means) and means[-1] > means[0], means)
earlier = _Market(PAID)
earlier.bought[WHEAT] = 50.0
check("tonnes the seat ordered earlier in the year count toward the climb",
      earlier.pricing.purchase_cost(WHEAT, 10.0)[1] > market.pricing.purchase_cost(WHEAT, 10.0)[1])
sale_means = [market.pricing.sale_proceeds(WHEAT, OFFERED_TONNES * share)[1] for share in (0.01, 0.5, 5.0, 50.0)]
check("a sale fetches less a tonne the more is sold",
      sale_means == sorted(sale_means, reverse=True) and sale_means[-1] < sale_means[0], sale_means)
check("...and buying then selling the same tonne never makes the founder money",
      market.pricing.sale_proceeds(WHEAT, 1.0)[0] <= market.pricing.purchase_cost(WHEAT, 1.0)[0])

# a good no seller offers has no price
check("a good no seller offers has no price and cannot be bought",
      market.quote("cobalt_kg") is None and market.pricing.purchase_cost("cobalt_kg", 1.0) is None
      and market.pricing.sale_proceeds("cobalt_kg", 1.0) is None and not market.offers.can_be_bought("cobalt_kg"))

# the coin metal is one number in the mint, in cargo and in the partners' payments
metal_price = market.offers.home_unit_price(COIN_METAL)
check("the coin metal is priced at the economy's price on the tile",
      metal_price is not None and abs(metal_price - PAID[COIN_METAL]) <= 1e-9 * metal_price, metal_price)
check("a good no home seller offers has no home unit price", market.offers.home_unit_price("cobalt_kg") is None)
coin = {"material": COIN_METAL, "kg_per_unit": 0.0035}
world = SimpleNamespace(scenario=SimpleNamespace(civ={"coin_standard": coin}), goods_market=market, finance=SimpleNamespace(coin_stock_units=lambda: 2000.0))
expected_stock = 2000.0 * coin["kg_per_unit"] * metal_price
check("the coin the society holds is counted at that price",
      abs(port_money.coin_stock_value_of(None, world) - expected_stock) <= 1e-9 * expected_stock, (port_money.coin_stock_value_of(None, world), expected_stock))
def trade_over(goods_market):
    return module_harness.build(ForeignTrade, views={"civilisation_record": load_civ,
                                                     "home_unit_price": goods_market.offers.home_unit_price})


for partner in ("han_china_100ad", "mexica_1500"):
    standard = load_civ(partner)["coin_standard"]
    own_price = 0.5
    in_cargo = trade_over(_Market({standard["material"]: 0.5})).money_per_partner_coin(partner)
    check("a partner's coin in cargo is its metal at the economy's price: %s" % partner,
          abs(in_cargo - standard["kg_per_unit"] * own_price) <= 1e-9 * in_cargo, (in_cargo, own_price))
check("a partner's coin whose metal has no price is not counted",
      trade_over(_Market({})).money_per_partner_coin("han_china_100ad") is None)

# the price follows the economy as it moves
before = market.quote(WHEAT)["price_at_tile_per_tonne"]
market.economy.paid = {good: price * 2.0 for good, price in PAID.items()}
check("the founder pays twice the price when the economy's price on the tile doubles",
      abs(market.quote(WHEAT)["price_at_tile_per_tonne"] / before - 2.0) < 1e-9, before)
