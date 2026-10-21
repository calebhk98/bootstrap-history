"""The arithmetic of a wage: cost-of-living factors and the annual figure, called with prices and not a game."""


def tools_factor(basket, price_factor_of, price_ratio_of):
    """The mean over a trade's tool basket of each material's demand factor times its market ratio; one with no tools is 1."""
    if not basket:
        return 1.0
    return sum(price_factor_of(material) * price_ratio_of(material) for material in basket) / len(basket)


def weighted_factor(share_food, share_housing, share_tools, share_skill, food, housing, tools):
    """The wage multiplier: each cost of living at its share of the wage, and skill and difficulty at its own."""
    return share_food * food + share_housing * housing + share_tools * tools + share_skill


def housing_factor(workers, room, start_occupancy, band, max_markup):
    """The housing multiplier on a wage: one while the town has room, rising across `band` of occupancy to the markup."""
    occupancy = workers / max(1.0, room)
    pressure = (occupancy - start_occupancy) / band
    return 1.0 + max_markup * max(0.0, min(1.0, pressure))


def annual_wage(base, weighted, price_index, wage_index, scarcity, pay_scale):
    """Money one person-year of a trade costs, from the opening schedule's base and every factor on it."""
    return base * weighted * price_index * wage_index * scarcity * pay_scale
