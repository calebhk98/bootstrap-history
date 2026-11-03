"""The lowest rate a lender takes: its own time preference (on top of the inflation it expects), plus the loss it expects.

The expected loss is the lender's remembered yearly loss rate on what it has put out (loss_memory), read from its own
record. Nothing here is typed per civilisation: every input is a lender's own state or a market figure.
"""


def loss_rate(remembered_rate: float) -> float:
    """The loss the lender expects per year of exposure: its remembered rate (loss_memory), which ages."""
    return min(1.0, max(0.0, remembered_rate))


def lowest_ask(time_preference: float, expected_inflation: float, expected_loss_rate: float = 0.0) -> float:
    """The nominal return the lender's time preference asks, plus its expected loss rate."""
    return max(0.0, time_preference + expected_inflation) + max(0.0, expected_loss_rate)
