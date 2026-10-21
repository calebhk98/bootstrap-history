"""Scenario (Complaint 507, stage 3): in a running Rome game the founder's quote carries the agent economy's price on his tile, and the
coin metal is one number in the mint, in cargo and in the partners' payments. The pricing rules are in
test_purchase_reads_economy_price."""
from .harness import *  # noqa: F401,F403

from sim.engine.material_units import tonnes_per_unit

game = sim(civ="rome_100ad", capital=1e9)
market = game.goods_market
tile = game.economy.acting_tile()
paid = game.economy.agent_prices_at(tile)
check("the economy answers prices on the founder's tile", bool(paid), tile)

WHEAT = game.civ.get("staple") or "wheat_kg"
quote = market.quote(WHEAT)
check("the founder's quote of the staple has the economy's price on the tile in it",
      abs(quote["price_at_tile_per_tonne"] - paid[WHEAT] / tonnes_per_unit(WHEAT)) <= 1e-9 * quote["price_at_tile_per_tonne"],
      (quote["price_at_tile_per_tonne"], paid[WHEAT] / tonnes_per_unit(WHEAT)))

coin = game.civ["coin_standard"]
metal_price = market.home_unit_price(coin["material"])
check("the coin metal is priced at the economy's price on the tile",
      metal_price is not None and abs(metal_price - paid[coin["material"]]) <= 1e-9 * metal_price, (metal_price, paid.get(coin["material"])))
expected_stock = game.economy.coin_stock_units() * coin["kg_per_unit"] * metal_price
check("the coin the society holds is counted at that price",
      abs(game.economy.coin_stock_value() - expected_stock) <= 1e-9 * expected_stock, (game.economy.coin_stock_value(), expected_stock))
for partner in game.foreign_economies():
    standard = S.load_civ(partner)["coin_standard"]
    in_cargo = game._money_per_partner_coin(partner)
    price_of_metal = market.home_unit_price(standard["material"])
    check("a partner's coin in cargo is its metal at the economy's price: %s" % partner,
          (in_cargo is None and not price_of_metal)
          or abs(in_cargo - standard["kg_per_unit"] * price_of_metal) <= 1e-9 * in_cargo, (in_cargo, price_of_metal))
