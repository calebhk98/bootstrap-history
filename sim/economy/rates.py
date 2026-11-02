"""What a plan charges for capital when the market remembers no interest rate."""

from typing import Optional


def charged_rate(remembered: Optional[float]) -> float:
    """The rate a plan charges capital at. The memory holds a rate for the economy's own currency from the opening on,
    and none for a currency it has never seen (`YearView.interest_rate` is None): a plan made without a rate charges
    nothing for waiting, which is this function's one stated decision; a remembered rate is returned as it is."""
    return 0.0 if remembered is None else remembered
