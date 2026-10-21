"""Serving out a debt in bondage, and what a workshop's staff produce: the arithmetic, on values given."""


def bondage_repayment(hours_per_year, labour_share, wage_markup, labourer_hour_quote):
    """What a year of the debtor's hours repays: the share of his hours that belong to the creditor, at the
    market's labourer hour and a markup."""
    return hours_per_year * labour_share * wage_markup * labourer_hour_quote


def serve_bondage_year(years_left, debt, repayment):
    """(years left, debt, whether the term ended this year) after one year of service. A debt repaid early ends the
    term; a term that runs out discharges the debt that is left."""
    years_left -= 1
    debt = max(0.0, debt - repayment)
    if debt <= 0 and years_left > 0:
        years_left = 0
    if years_left <= 0:
        return 0.0, 0.0, True
    return years_left, debt, False


def workshop_craft_wages(employees, is_craft, annual_quote, unfree_equivalent, artisan_quote):
    """The yearly wages the workshop's craft staff would draw at the market: each craft trade at its own quote, and
    the freedmen and enslaved (counted as `unfree_equivalent` full workers) at the artisan quote."""
    wages = sum(count * annual_quote(trade) for trade, count in employees.items() if is_craft(trade))
    return wages + unfree_equivalent * artisan_quote


def workshop_output_value(craft_wages, markup, capability_factor):
    """What the staff produce and sell: their wages times the workshop's markup and the factor for what the
    society knows how to do."""
    return craft_wages * markup * capability_factor
