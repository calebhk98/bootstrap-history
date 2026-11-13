# No belief or intelligence model: countries see the true world, except for tech names under fog

**Status:** open - beliefs, news lag, espionage and a spy-and-contact-driven leak are built for seats; army-strength beliefs, battle reports, deception, and decisions reading beliefs remain.

## Built

- `sim/world/belief.py`: a belief is `{value, variance, year}`; news ages by distance over `NEWS_SPEED_KM_PER_YEAR`, an unrefreshed
  belief loses reliability at `VARIANCE_GROWTH_PER_YEAR`, signals merge by precision. `years_until_unreliable` is the memory rule;
  `MERCHANT_STRETCH_MEMORY_YEARS` (517) is retired and `merchants_stretch.memory_years()` derives the span from it.
- `sim/world/espionage.py`: `secret_exposure` replaces the fixed `SECRET_EXPOSURE / copy_difficulty` for seats: it rises with the
  holder's contacts (other seats) and the spies placed, `observation_variance` sharpens signals with spies.
- `sim/seats/intelligence*.py`: command `PlaceSpies` (any seat, debits a person-year of labour per spy each year, unpaid spies lapse),
  views `seat_beliefs` and `seat_spies`; each year `Sight.hear_of_other_seats` writes the acting seat's beliefs about every other
  seat's technique count and cash from noisy, lagged readings (noise is a keyed draw, the game's random stream is untouched).
- Tests: `sim/tests/test_belief.py`.

## What is left

- Beliefs about army size and strength (campaigns code is owned by 484/485), and battle reports reaching powers differently.
- No decision reads `seat_beliefs` yet (offers, trade, war choices still use true figures).
- Contacts are the count of other seats, not real trade contact volume; actors' own exposure (`sim/actors/world_disclosure.py`) still
  uses the fixed share; news does not yet ride freight routes.
- Deception (a deliberate false belief) and a cover story are not built.

- Fog is a per-seat set of revealed technology ids (`sim/knowledge/module.py`, `sim/seats/sight.py`). A seat hears of
  another seat's techniques when distance-scaled visibility passes a threshold (`sim/seats/visibility.py`).
- There is no record of what an actor believes about another (army size, wealth, techniques) with a
  value, a confidence and the date learned; no news that travels at route speed; no battle reports that
  reach different powers differently; no deception or cover story; no espionage.
- A secret technique leaks a fixed share (`SECRET_EXPOSURE / copy_difficulty`, `base_visibility` in `sim/seats/visibility.py`), not a
  per-year chance that rises with activity.

Why it matters: the group's third report makes this central (each faction acts on its own beliefs; a
classified route triggers interceptions recorded under a cover story). The first two reports rank it
lower and accept separate human players as a substitute, but only if beliefs can be derived reliably
(knowing a rival has gunpowder, how big it is, that it is lying).

What it would take: a beliefs table per actor filled by events (trade contact, battles, envoys) delivered
after the route time; a leak chance per year per secret scaled by the activity that exposes it; a
deception operation that writes a false belief. Lower priority than 481 to 486 by the group's own ranking.
