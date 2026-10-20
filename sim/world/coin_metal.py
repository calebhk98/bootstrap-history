"""Coin as metal: how a recorded metal ratio follows the market, what a purse of coin weighs, what guarding it costs
and what carrying it costs. Plain arithmetic over what the caller hands in; reads no simulation."""

KG_PER_TONNE = 1000.0


def revalued_ratio(held, measured, yearly_share, yearly_cap):
    """The recorded value of a coin metal after a year: the geometric blend of the held value toward the measured
    one (a measure that is not positive counts as one), moved by no more than `yearly_cap` either way."""
    if not measured > 0.0:
        measured = 1.0
    moved = held ** (1.0 - yearly_share) * measured ** yearly_share
    return min(held * yearly_cap, max(held / yearly_cap, moved))


def coin_tonnes(money, kg_per_unit):
    """The mass in tonnes of `money` held as coin of `kg_per_unit` metal each."""
    return max(0.0, money) * kg_per_unit / KG_PER_TONNE


def keeping_cost_per_year(money, kg_per_unit, guard_hours_per_tonne_year, money_per_hour):
    """Yearly cost of keeping `money` as coin under guard."""
    return coin_tonnes(money, kg_per_unit) * guard_hours_per_tonne_year * money_per_hour


def carriage_units(units, kg_per_unit, carriage_money_per_tonne, home_money_per_coin):
    """Coin units the carriers take to move `units` of coin of `kg_per_unit` metal each; never more than is moved."""
    cost = carriage_money_per_tonne * units * kg_per_unit / KG_PER_TONNE
    return min(units, cost / home_money_per_coin)
