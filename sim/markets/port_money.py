"""The society's money figures the port reports: what its output and its coin are worth at today's prices. Part of the port."""


def output_value(world):
    """Money's worth of the society's yearly output at today's prices."""
    return world.finance.real_output_hours() * world.labour.money_per_labour_hour() * world.output_factor


def coin_stock_value(world):
    """Money's worth of the metal in the coin this society holds, from its coin standard, at the metal's price (the same one
    cargo and the partners' coin are counted at); None while the metal has no price."""
    coin = world.civ["coin_standard"]
    price = world.goods_market.offers.home_unit_price(coin["material"])
    return None if price is None else world.finance.coin_stock_units() * coin["kg_per_unit"] * price
