"""A merchant house: the carriers it owns, the people it keeps, and the capital the class holds.

A house owns the carriers its capital buys, keeps a resident factor at each end of the route that
the carriers share, and the number of houses on a route is the carriers over those it owns, as many
as the labour market can staff. The class's own capital is its share of the funds households save,
and what it uses beyond that is borrowed from the pool.

Standalone: counts and money in; counts and money out.
"""
import math

ROUTE_ENDS = 2          # a route runs between two places; geometry, not a tunable
FACTORS_PER_END = 1     # a house keeps at least one resident factor where it buys and where it sells


def carriers_per_house(house_capital, carrier_value):
    """Carriers a house owns: its capital over a carrier's price, never fewer than one (a house
    with less borrows for its one)."""
    if carrier_value <= 0.0:
        return 1.0
    return max(1.0, house_capital / carrier_value)


def agents_per_house():
    """Resident agents a house keeps on a route, whatever the carriers it owns."""
    return float(ROUTE_ENDS * FACTORS_PER_END)


def people_per_house():
    """People a house takes from the labour market: its principal and its agents."""
    return 1.0 + agents_per_house()


def agents_per_carrier(carriers_in_house):
    """Agents kept per carrier: the house's agents shared among the carriers it owns."""
    return agents_per_house() / max(1.0, carriers_in_house)


def houses_on_route(carriers, carriers_in_house, merchants_available):
    """Houses on a route: its carriers over those a house owns, and no more than the merchants the
    labour market has can staff. Endless carriers mean endless houses."""
    if math.isinf(carriers):
        return math.inf
    by_carriers = carriers / max(1.0, carriers_in_house)
    by_labour = max(0.0, merchants_available) / people_per_house()
    return min(by_carriers, by_labour)


def class_own_capital(household_funds, merchants, merchant_wage, working_people, labourer_wage):
    """Funds merchants hold of their own: households save in proportion to income, so the class holds
    the share of the funds that its wage bill is of the working population's (priced at the labourer's
    wage), never more than the funds."""
    if household_funds <= 0.0 or merchants <= 0.0 or working_people <= 0.0 or labourer_wage <= 0.0:
        return 0.0
    share = merchants * merchant_wage / (working_people * labourer_wage)
    return household_funds * min(1.0, share)


def borrowing(capital_used, own_capital):
    """Money the class has borrowed: what it put into goods beyond its own."""
    return max(0.0, capital_used - own_capital)
