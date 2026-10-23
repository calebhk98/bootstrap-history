"""A goods category is one market shared by every seller: one seller's revenue is the market's price times volume over the
number of sellers, lifted or dampened by the income effect where the good is not an essential."""


def seller_revenue_factor(price_ratio, quantity_ratio, active_sellers, income_factor=1.0):
    """One seller's revenue relative to day one: the category's price ratio times quantity ratio shared among the
    active sellers, times `income_factor` (one for an essential category)."""
    return price_ratio * quantity_ratio / active_sellers * income_factor
