# Entrants forecast takings that the firms do not realise

**Status:** open

In `firm_count_whole_game_scenario` (largest market), the firm count runs 23, 27, 27, 27, 27 and then falls to 8 by year 20,
where it stays. Entrants in one year count each other (`sim/agents/entry_round.py` `NicheEntry.found` passes `waiting + 1`
to `firm_entry.expected_entry_gross`), and a firm leaves only once its ramp ends and its margin is below the market's return
on its plant (`sim/agents/firm_exit.py`). So with 27 firms in, the realised margin falls short of what the entry forecast
(`AgentsPort.entry_gross` with those entrants, then the entry costs in `NicheEntry`) promised. One of the two sides
mis-states the takings or the costs of a firm among many.

Measure first: for the largest market, print per year each firm's forecast at entry (`last_margin` when founded) beside its
realised margin after the ramp, and the cost lines on each side (entry: `costs`, `stake_cost`; exit: plant times market rate,
interest). Then fix whichever side is wrong, with a rule test that builds both sides from the same inputs and asserts that a
firm admitted by entry is not one exit would close at full ramp in an unchanged market.

Command: `python3 -m sim.tests --slow --only firm_count_whole_game_scenario --jobs 1`.
