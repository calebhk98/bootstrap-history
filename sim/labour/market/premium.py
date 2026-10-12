"""The wage multiple that repays a trade's training years; pure arithmetic, so the market core can use it."""
import math


def training_premium(training_years: float, discount_rate: float, career_years: float) -> float:
    """Wage multiple that leaves a trainee indifferent to skipping training.

    An unskilled worker earns the unit wage for the whole career. A trainee
    earns nothing for `training_years`, then the premium for the rest, with
    both streams discounted continuously. Zero training gives exactly 1.
    """
    training_years = min(max(0.0, training_years), career_years * 0.9)
    if training_years == 0.0:
        return 1.0
    discounted_career = 1.0 - math.exp(-discount_rate * career_years)
    discounted_after_training = (math.exp(-discount_rate * training_years)
                                 - math.exp(-discount_rate * career_years))
    return discounted_career / discounted_after_training
