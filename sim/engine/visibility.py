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


def copy_difficulty_of(node: dict) -> float:
    """How hard a node's know-how is to copy from sight. A node declares `copy_visibility` (the share an onlooker
    can recover from the product or the yard) and difficulty is its reciprocal; a node that does not falls back
    to the trades and materials it needs, at least one (TRANSITIONAL, CLAUDE.md 4.4)."""
    if node.get("copy_visibility"):
        return 1.0 / float(node["copy_visibility"])
    trades = [trade for trade, hours in (node.get("lab") or {}).items() if hours > 0]
    materials = [material for material, amount in (node.get("mat") or {}).items() if amount]
    return max(1, len(trades) + len(materials))


def years_to_be_believed(mode: str, proof_years: float, secret_exposure: float) -> float:
    """Years a concern must run at a profit before outsiders believe it: none once published, longer in
    proportion to how little leaks past the door when it is a secret or a licensed one, else `proof_years`."""
    if mode == "publish":
        return 0.0
    if mode in ("secret", "license"):
        return proof_years / secret_exposure
    return float(proof_years)


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
