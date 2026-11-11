"""Spying: an action any actor can fund against another. Spies sharpen what the actor learns of the target (its signals have
less variance) and raise how much of the target's kept secrets leaks, on top of what the target's own contacts let out."""
import math

from sim.constants import declare

CONTACT_LEAK_RATE = declare(
    "CONTACT_LEAK_RATE", 0.15, kind="temporary_heuristic", unit="leak hazard per contact per year", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="How much more of a kept secret gets out for each other party the holder deals with: every contact is a mouth. "
        "Stands in for the people who know the secret and who they talk to.")
SPY_LEAK_RATE = declare(
    "SPY_LEAK_RATE", 0.5, kind="temporary_heuristic", unit="leak hazard per spy per year", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="How much of a kept secret one spy placed with the holder gets out in a year, before the know-how's copy difficulty.")
SPY_PRECISION = declare(
    "SPY_PRECISION", 1.0, kind="temporary_heuristic", unit="precision added per spy", source=None, confidence="D",
    retire="Complaints/488-no-belief-or-intelligence-model.md",
    why="How much each spy adds to the precision (one over variance) of what the actor learns about the target.")


def secret_exposure(base_exposure: float, copy_difficulty: float, contacts: float, spies: float,
                    contact_leak_rate: float, spy_leak_rate: float) -> float:
    """Share of a kept invention an onlooker learns in a year, 0..1. With no contacts and no spies it is `base_exposure` over
    the copy difficulty; each contact and each spy leaves less of it hidden, a hard-to-copy invention leaks more slowly."""
    hidden = 1.0 - base_exposure / copy_difficulty
    return 1.0 - hidden * math.exp(-(contact_leak_rate * contacts + spy_leak_rate * spies) / copy_difficulty)


def observation_variance(base_variance: float, spies: float, spy_precision: float) -> float:
    """Relative variance of what an actor learns of a target it has `spies` placed with."""
    return 1.0 / (1.0 / base_variance + spy_precision * spies)


def affordable_spies(placed: int, balance: float, cost_per_spy: float) -> int:
    """How many of the `placed` spies a purse of `balance` can pay for a year (the rest lapse)."""
    if cost_per_spy <= 0.0:
        return placed
    return max(0, min(placed, int(balance // cost_per_spy)))
