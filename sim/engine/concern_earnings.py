"""What a concern earns in a year: the arithmetic every screen, the ledger and `revenue` share."""

LEDGER_ROW_FLOOR = 0.5


def takings_at(tree_revenue, ramp, output_factor, price_index, value_ratio, learning_ratio):
    """Yearly takings at a ramp: the tree's raw figure carried to today's price level and the techniques held,
    before the market's price for the goods. `output_factor` is the hazard and war factor (1.0 to leave it out)."""
    return tree_revenue * ramp * output_factor * price_index * value_ratio * learning_ratio


def quoted_ramp(running, fully_ramped, running_ramp_of):
    """A concern not yet open is quoted at its full ramp; an open one at its own (`running_ramp_of()`), unless
    asked for the full one."""
    return 1.0 if fully_ramped or not running else running_ramp_of()


def quoted_units(running, scalable, running_units_of, units_asked=None):
    """The units a quote covers: those asked; else those running (`running_units_of()`) for an open scalable
    concern; else one."""
    if units_asked is not None:
        return units_asked
    return running_units_of() if running and scalable else 1.0


def output_market_factor(market_prices_goods, market_factor_of):
    """The market's price over the long-run price for a concern's goods (`market_factor_of()`); one while nobody has
    sold them, so the quote stays at long-run takings rather than at nothing."""
    return market_factor_of() if market_prices_goods else 1.0


def forecast_basis(goods_have_market):
    """What a quote of earnings stands on: the market's price, or long-run cost while nobody has sold the goods."""
    return "market" if goods_have_market else "long_run_no_market_yet"


def ledger_row(earnings):
    """The ledger's figure for a concern's takings, rounded to a tenth; None when it earns too little to list."""
    return round(earnings, 1) if earnings > LEDGER_ROW_FLOOR else None
