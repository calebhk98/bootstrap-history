"""Complaint 371: between years the count of people firms and governments employ is what they
employ. Entry and group formation change staff after the last actor has acted, and the founder's
own turn reads the count before the next year's first actor recounts, so a count kept from before
those changes made an unbroken game read a different pool from the one a reloaded game reads."""
from .harness import *  # noqa: F401,F403
from sim.tests import fingerprint as perf_fingerprint

game = perf_fingerprint.build(dict(civ="rome_100ad", seed=1, years=3, events=True, fog=False))
actors_at_start = len(game.actors.actors)
stale = []
for year in range(1, 4):
    game.step()
    registry = game.actors
    for trade in sorted({trade for actor in registry.actors.values() for trade in actor.record.workforce}):
        held = registry.staff_fte(trade)
        actual = 0.0
        for actor_id in sorted(registry.actors):
            actual += registry.actors[actor_id].record.workforce.get(trade, 0.0)
        if held != max(0.0, actual):
            stale.append((year, trade))
check("the staff firms and governments employ is counted as they now stand, at the end of every year",
      not stale, "year and trade that differ: %s" % stale[:5])
check("...in a game where entry actually changed who employs people during those years",
      len(game.actors.actors) > actors_at_start, (actors_at_start, len(game.actors.actors)))
