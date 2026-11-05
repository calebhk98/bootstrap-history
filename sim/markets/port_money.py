"""The society's money figures the port reports: what its output and its coin are worth. Part of the port.

Once the economy is open the home country answers from the economy's own country figures, as a partner does
(`CountryAnswers`); the engine's own figures answer while it opens, and where the economy holds no record of the figure."""
from .port_country import home_answers


def opening_output_value(world):
    """The engine's own money worth of the society's yearly output: real output hours at the wage, times the output factor."""
    return world.finance.real_output_hours() * world.labour.money_per_labour_hour() * world.scenario.output_factor


def opening_coin_stock_value(world):
    """The engine's own money worth of the metal in the coin this society holds, from its coin standard, at the metal's
    price on the acting tile; None for a standard with no metal (fiat) and while the metal has no price."""
    coin = world.scenario.civ["coin_standard"]
    material = coin.get("material")
    if material is None:
        return None
    price = world.goods_market.offers.home_unit_price(material)
    return None if price is None else world.finance.coin_stock_units() * coin["kg_per_unit"] * price


def output_value_of(answers, world):
    """The economy's answer for the home country when `answers` (CountryAnswers) is given and holds a figure, else the engine's."""
    value = None if answers is None else answers.society_output()
    return opening_output_value(world) if value is None else value


def coin_stock_value_of(answers, world):
    """The economy's coin stock value for the home country when `answers` is given (None where the metal has no price there or
    the money is fiat); the engine's own figure when the economy is not open."""
    return opening_coin_stock_value(world) if answers is None else answers.coin_stock_value()


def output_value(port):
    """Money's worth of the society's yearly output."""
    return output_value_of(home_answers(port), port.world)


def coin_stock_value(port):
    """Money's worth of the metal in the coin the society holds; None while the metal has no price."""
    return coin_stock_value_of(home_answers(port), port.world)
