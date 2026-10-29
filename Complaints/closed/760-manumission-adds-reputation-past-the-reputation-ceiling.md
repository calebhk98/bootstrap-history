# Manumission adds reputation past the reputation ceiling

**Status:** closed - fixed: `manumit` sends `GainReputation` (capped at `REPUTATION_CEILING`) and `AddReputation` is deleted. Test: `sim/tests/test_bondage_training_lag.py` `test_freeing_people_gains_reputation_that_stops_at_the_ceiling`; the ceiling itself is `test_polity_module.py` `test_reputation_gain_stops_at_the_ceiling`. Numbers change only for a household that frees people near the ceiling.

Every other gain of reputation stops at the top of the scale: a finished work (`GainReputation`, `sim/polity/appliers.py`,
`min(REPUTATION_CEILING, reputation + amount)`) and publishing an invention (`sim/diffusion/disclosure.py`, the same command).
Freeing people (`sim/labour/labour_bondage.py`, `manumit`) sends `AddReputation`, which adds with no ceiling, as the old code
did (`household.reputation += min(gain, MANUMISSION_REPUTATION_GAIN_CAP)`). A household already near the ceiling that frees people
climbs past it, and everything that reads reputation as a share of the scale (credit, protection, the wage bonus, the rate
discount) sees a figure the rest of the game cannot reach.

The move into the polity module kept this on purpose (the equivalence check compares reputation). The fix is one line: send
`GainReputation` instead of `AddReputation`, and delete `AddReputation`; the reproducing case is a household at the ceiling that
frees one person (reputation after is above `REPUTATION_CEILING`).
