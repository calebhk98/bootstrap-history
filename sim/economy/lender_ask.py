"""The lowest rate a lender takes: the best return among what else its money earns, plus the loss it expects.

What else the money earns: the lender's own time preference on top of the inflation it expects, the yield of a title to land
(rent over the price titles change hands at) and the yield of the state's bonds where the society has a bond market. The
expected loss is the lender's remembered yearly loss rate on what it has put out (loss_memory), read from its own record.
Nothing here is typed per civilisation: every input is a lender's own state or a market figure.
"""
from typing import Optional


def loss_rate(remembered_rate: float) -> float:
    """The loss the lender expects per year of exposure: its remembered rate (loss_memory), which ages."""
    return min(1.0, max(0.0, remembered_rate))


def land_yield(rent_per_hectare: float, price_per_hectare: Optional[float]) -> Optional[float]:
    """What a title earns its holder a year: the rent over the price a hectare changed hands at; None where none did.
    The rent is never read over a price built from the rate (that is the rate itself, a circle)."""
    if price_per_hectare is None or price_per_hectare <= 0.0:
        return None
    return max(0.0, rent_per_hectare) / price_per_hectare


def reachable_public_yield(state_yield: Optional[float], bond_market_held: bool) -> Optional[float]:
    """The yield a household can earn on the state's bonds: the state's, where the society holds a bond market; None otherwise."""
    return state_yield if bond_market_held else None


def lowest_ask(time_preference: float, expected_inflation: float, expected_loss_rate: float = 0.0,
               land_yield: Optional[float] = None, public_yield: Optional[float] = None) -> float:
    """The nominal return the lender's best alternative earns (its time preference plus expected inflation, the land
    yield, the public yield), plus its expected loss rate."""
    alternatives = [time_preference + expected_inflation]
    alternatives.extend(each for each in (land_yield, public_yield) if each is not None)
    return max(0.0, *alternatives) + max(0.0, expected_loss_rate)
