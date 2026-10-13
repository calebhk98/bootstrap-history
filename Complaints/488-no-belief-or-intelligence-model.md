# No belief or intelligence model: countries see the true world, except for tech names under fog

**Status:** open

- Fog is a per-seat set of revealed technology ids (`sim/engine/fog.py`, `seat_sight.py`). A seat hears of
  another seat's techniques when distance-scaled visibility passes a threshold (`sim/engine/visibility.py`,
  `view_share.py`).
- There is no record of what an actor believes about another (army size, wealth, techniques) with a
  value, a confidence and the date learned; no news that travels at route speed; no battle reports that
  reach different powers differently; no deception or cover story; no espionage.
- A secret technique leaks a fixed share (`SECRET_EXPOSURE / copy_difficulty`, `visibility.py`), not a
  per-year chance that rises with activity.

Why it matters: the group's third report makes this central (each faction acts on its own beliefs; a
classified route triggers interceptions recorded under a cover story). The first two reports rank it
lower and accept separate human players as a substitute, but only if beliefs can be derived reliably
(knowing a rival has gunpowder, how big it is, that it is lying).

What it would take: a beliefs table per actor filled by events (trade contact, battles, envoys) delivered
after the route time; a leak chance per year per secret scaled by the activity that exposes it; a
deception operation that writes a false belief. Lower priority than 481 to 486 by the group's own ranking.
