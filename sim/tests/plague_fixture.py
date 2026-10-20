"""Hazard fixtures for tests of the staff_loss machinery (mitigation, messages, risk screens, population shocks).

No civilisation file carries a dated plague any more (Complaint 490): epidemics come from the disease model. The
machinery that wars and famines still use is exercised here on a plague-shaped hazard added to a game's own copy of
its civilisation."""

ANTONINE = {"name": "Antonine plague", "staff_loss": 0.28, "years": [165, 180], "note": "a test fixture, not game data"}
BLACK_DEATH = {"name": "Black Death", "staff_loss": 0.45, "years": [1348, 1350], "note": "a test fixture, not game data"}


def with_hazard(game, hazard):
    """`game` with `hazard` added to its civilisation; returns `game`."""
    game.civ["hazards"] = list(game.civ.get("hazards", [])) + [dict(hazard)]
    return game
