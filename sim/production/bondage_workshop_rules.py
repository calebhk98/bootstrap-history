"""What a workshop's staff produce: the arithmetic, on values given."""


def workshop_craft_wages(employees, is_craft, annual_quote, unfree_equivalent, artisan_quote):
    """The yearly wages the workshop's craft staff would draw at the market: each craft trade at its own quote, and
    the freedmen and enslaved (counted as `unfree_equivalent` full workers) at the artisan quote."""
    wages = sum(count * annual_quote(trade) for trade, count in employees.items() if is_craft(trade))
    return wages + unfree_equivalent * artisan_quote


def workshop_output_value(craft_wages, markup, capability_factor):
    """What the staff produce and sell: their wages times the workshop's markup and the factor for what the
    society knows how to do."""
    return craft_wages * markup * capability_factor
