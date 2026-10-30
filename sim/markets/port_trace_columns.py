"""The spin-up trace's four macro columns, read from one year's `YearOutcome`, for a side-by-side with another
model's monthly statistics (price level, average wage, unemployment, real output)."""


def macro_columns(outcome, unskilled_trade, real_output):
    """{price_level, wage, unemployment, real_output} for the year.

    `price_level` is the fixed-basket level against the index base (`basket_price_level`), not a chained index.
    `wage` is the unskilled trade's mean money wage per hour over the hours hired (None when the trade did not trade).
    `unemployment` is the share of hours offered on the labour markets that nobody hired, idle over hired plus idle
    (None when none was offered); a household's work on its own plot is not offered, so it counts in neither.
    `real_output` is the year's output valued at the opening prices (`spin_up_state`), passed in."""
    offered = outcome.hired_hours + outcome.idle_hours
    return {"price_level": outcome.basket_price_level,
            "wage": outcome.wages.get(unskilled_trade),
            "unemployment": outcome.idle_hours / offered if offered > 0.0 else None,
            "real_output": real_output}
