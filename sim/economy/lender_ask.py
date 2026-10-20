"""The lowest rate a lender takes: the best return among its alternatives, plus the loss it expects.

Alternatives are its own time preference (on top of the inflation it expects), the yield of land it could buy
(rent over title price), and the yield of public debt where a state sells it. The expected loss is the lender's
remembered yearly loss rate on what it has put out (loss_memory), read from its own record. Nothing here is typed per
civilisation: every input is a lender's own state or a market figure.
"""
from typing import Optional


def loss_rate(remembered_rate: float) -> float:
    """The loss the lender expects per year of exposure: its remembered rate (loss_memory), which ages."""
    return min(1.0, max(0.0, remembered_rate))


def land_yield(rent_per_hectare: float, price_per_hectare: Optional[float]) -> float:
    """Rent over title price on land the lender could buy; nothing when the land has no price to buy at."""
    if price_per_hectare is None or price_per_hectare <= 0.0 or rent_per_hectare <= 0.0:
        return 0.0
    return rent_per_hectare / price_per_hectare


def lowest_ask(time_preference: float, expected_inflation: float, land_yield_available: float = 0.0,
               public_yield_available: float = 0.0, expected_loss_rate: float = 0.0) -> float:
    """The best nominal return among the lender's alternatives, plus its expected loss rate."""
    best_alternative = max(0.0, time_preference + expected_inflation, land_yield_available, public_yield_available)
    return best_alternative + max(0.0, expected_loss_rate)
