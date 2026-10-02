# No final score when the goal is missed, although every component is computed

**Status:** closed - `score` always shows the total, flagged "goal not reached"

At the horizon `score` prints "no score: the goal was not reached" and then every component (technology coverage 0.857, literacy 0.970, workforce 0.849, institutions 0.828, ...). A run that transforms the society but misses the headline goal gets no number.

What it would take: always show the total, flagged "goal not reached".

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
