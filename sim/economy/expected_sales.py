"""What a producer learns its demand from at the year's close."""

# Stock left below this share of the year's sales counts as sold out (rounding in settlement leaves a hair).
SOLD_OUT_LEFT_SHARE = 1e-6


def demand_seen(sold: float, left: float, market_sold: float, market_unmet: float) -> float:
    """Quantity a producer takes as the year's demand: what it sold, plus, when it sold out (stock left is a hair or
    nothing), its share of what buyers in its market wanted and did not get (share: its sales over the market's)."""
    if market_sold <= 0.0 or market_unmet <= 0.0 or left > SOLD_OUT_LEFT_SHARE * sold:
        return sold
    return sold + sold / market_sold * market_unmet
