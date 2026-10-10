"""How much of an invention an onlooker can learn, from the inventor's choice, the distance and the know-how itself.

Pure functions, used by the actors' view of the world and by one seat looking at another."""
from typing import Iterable

# how open each choice is, widest first: a published invention is open to all, a secret to nobody but by leaks
OPENNESS_ORDER = ("publish", "default", "license", "secret")


def base_visibility(mode: str, in_public_use: bool, copy_difficulty: float, secret_exposure: float) -> float:
    """Share of an invention that can be learned before distance counts, 0..1. A published one shows in full.
    One run in public shows what the product and the yard give away, which is the reciprocal of how hard its
    know-how is to copy from sight; one kept shut (a secret, a licensed one, or any not yet run in public) shows
    only what leaks past the door, `secret_exposure` of that."""
    if mode == "publish":
        return 1.0
    if mode == "default" and in_public_use:
        return 1.0 / copy_difficulty
    return secret_exposure / copy_difficulty


def seen_from(visibility: float, distance_km: float, observation_range_km: float) -> float:
    """What an onlooker `distance_km` away learns of an invention that shows `visibility` at its door."""
    return visibility / (1.0 + distance_km / observation_range_km)


def most_open_mode(modes: Iterable[str]) -> str:
    """The widest choice any maker of the same invention has made: one maker publishing opens it for everyone."""
    chosen = set(modes)
    for mode in OPENNESS_ORDER:
        if mode in chosen:
            return mode
    return "default"
