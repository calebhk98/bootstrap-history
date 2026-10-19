"""Complaint 507, stage 3, whole game: what the founder pays and is paid is the agent economy's price on the founder's
tile plus carriage, a larger order costs more a tonne, a good no one sells has no price, and the coin metal is one
number wherever the game counts it. Slow topic: it builds a game on the agent economy."""
from .harness import *  # noqa: F401,F403

from unittest import mock

from sim.engine.material_units import tonnes_per_unit

game = sim(civ="rome_100ad", capital=1e9)
market = game.goods_market
tile = game.economy.acting_tile()
paid = game.economy.agent_prices_at(tile)
check("the economy answers prices on the founder's tile", bool(paid), tile)

# --- a tonne costs the economy's price on the tile plus carriage
WHEAT = game.civ.get("staple") or "wheat_kg"
quote = market.quote(WHEAT)
check("the founder's quote of the staple has the economy's price on the tile in it",
      abs(quote["price_at_tile_per_tonne"] - paid[WHEAT] / tonnes_per_unit(WHEAT)) <= 1e-9 * quote["price_at_tile_per_tonne"],
      (quote["price_at_tile_per_tonne"], paid[WHEAT] / tonnes_per_unit(WHEAT)))
check("...and a tonne costs that price plus carriage, climbed by what the seat has bought this year",
      quote["buy_per_tonne"] >= quote["price_at_tile_per_tonne"] + quote["carriage_per_tonne"] - 1e-9,
      (quote["buy_per_tonne"], quote["price_at_tile_per_tonne"], quote["carriage_per_tonne"]))
small = market.purchase_cost(WHEAT, 1e-6)[1]
check("a very small order costs the quote", abs(small / quote["buy_per_tonne"] - 1.0) < 1e-3, (small, quote["buy_per_tonne"]))
check("the cost of making is a cost: it is not what the quote asks",
      quote["making_cost_per_tonne"] is not None and abs(quote["buy_per_tonne"] - quote["making_cost_per_tonne"]) > 1e-9)

# --- the project bill is tonnes times that price
node_id = "case_hardening"
original_materials = game.nodes[node_id]["mat"]
try:
    game.nodes[node_id]["mat"] = {WHEAT: 10.0}      # ten units: a hundredth of a tonne, too little to move the price
    bill = game.project_material_bill(node_id)
    row = next(each for each in bill["rows"] if each["material"] == WHEAT)
    tonnes = row["missing_tonnes"]
    check("a project short of a material owes tonnes times the founder's price a tonne",
          tonnes > 0.0 and abs(row["cost_of_missing"] - tonnes * quote["buy_per_tonne"]) <= 1e-3 * row["cost_of_missing"],
          (tonnes, row["cost_of_missing"], tonnes * quote["buy_per_tonne"]))
    check("...and the mean it shows is the economy's price plus carriage",
          abs(row["price_per_tonne"] - (quote["price_at_tile_per_tonne"] + quote["carriage_per_tonne"])) <= 1e-3 * row["price_per_tonne"],
          (row["price_per_tonne"], quote["price_at_tile_per_tonne"], quote["carriage_per_tonne"]))
finally:
    game.nodes[node_id]["mat"] = original_materials

# --- a larger order costs more a tonne (the book of the founder's tile is kept once a year has closed with the seat watched)
game._step_market()
paid = game.economy.agent_prices_at(tile)
offered = game.economy.agent_offered_tonnes(WHEAT) or 0.0
check("the economy keeps the book of the founder's market for the staple", offered > 0.0, offered)
# sellers price at cost, so the schedule is flat until the book nears what they hold; the last order takes nearly all of it
means = [market.purchase_cost(WHEAT, offered * share)[1] for share in (0.001, 0.05, 0.3, 0.99)]
check("a larger order costs more a tonne", means == sorted(means) and means[-1] > means[0], means)
# the price holds while the sale is smaller than the sellers' slack at the clearing price, then falls: sell past it
sale_means = [market.sale_proceeds(WHEAT, offered * share)[1] for share in (0.01, 0.5, 5.0, 50.0)]
check("a sale fetches less a tonne the more is sold",
      sale_means == sorted(sale_means, reverse=True) and sale_means[-1] < sale_means[0], sale_means)
check("...and buying then selling the same tonne never makes the founder money",
      market.sale_proceeds(WHEAT, 1.0)[0] <= market.purchase_cost(WHEAT, 1.0)[0])

# --- a good no seller offers has no price
check("a good no home technique and no partner makes has no price and cannot be bought",
      market.quote("cobalt_kg") is None and market.purchase_cost("cobalt_kg", 1.0) is None
      and market.sale_proceeds("cobalt_kg", 1.0) == (0.0, 0.0) and not market.can_be_bought("cobalt_kg"))

# --- the coin metal is one number in the mint, in cargo and in the partners' payments
coin = game.civ["coin_standard"]
metal_price = market.home_unit_price(coin["material"])
check("the coin metal is priced at the economy's price on the tile",
      metal_price is not None and abs(metal_price - paid[coin["material"]]) <= 1e-9 * metal_price, (metal_price, paid.get(coin["material"])))
expected_stock = game.economy.coin_stock_units() * coin["kg_per_unit"] * metal_price
check("the coin the society holds is counted at that price",
      abs(game.economy.coin_stock_value() - expected_stock) <= 1e-9 * expected_stock, (game.economy.coin_stock_value(), expected_stock))
partners = game.foreign_economies()
for partner in partners:
    standard = S.load_civ(partner)["coin_standard"]
    in_cargo = game._money_per_partner_coin(partner)
    price_of_metal = market.home_unit_price(standard["material"])
    check("a partner's coin in cargo is its metal at the economy's price: %s" % partner,
          (in_cargo is None and not price_of_metal)
          or abs(in_cargo - standard["kg_per_unit"] * price_of_metal) <= 1e-9 * in_cargo, (in_cargo, price_of_metal))
home_equal = [partner for partner in partners if S.load_civ(partner)["coin_standard"]["material"] == coin["material"]]
for partner in home_equal:
    per_kg = game._money_per_partner_coin(partner) / S.load_civ(partner)["coin_standard"]["kg_per_unit"]
    check("a partner whose coin is the home coin's metal counts it at the same number as the mint: %s" % partner,
          abs(per_kg - metal_price) <= 1e-9 * metal_price, (per_kg, metal_price))

# --- the price follows the economy as it moves
before = market.quote(WHEAT)["price_at_tile_per_tonne"]
assert abs(before - paid[WHEAT] / tonnes_per_unit(WHEAT)) < 1e-9 * before
with mock.patch.object(type(game.economy), "agent_prices_at",
                       lambda self, tile=None: {good: price * 2.0 for good, price in paid.items()}):
    check("the founder pays twice the price when the economy's price on the tile doubles",
          abs(market.quote(WHEAT)["price_at_tile_per_tonne"] / before - 2.0) < 1e-9, (market.quote(WHEAT), before))
