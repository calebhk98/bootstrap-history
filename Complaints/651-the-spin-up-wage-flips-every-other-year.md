# The spin-up's wage flips every other year

**Status:** open

A 60-year Rome spin-up trace (`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`) shows the unskilled
wage alternating year by year from about year 18: a low year, then a year several to many times higher, then low again,
for decades. A two-year alternation means a yearly adjustment that reacts to last year's value with a gain above one
(a cobweb), not a slow cycle.

Candidates, each a rule to test as a function on built inputs: the labour market's wage step against last year's
vacancies or unhired hours (`sim/labour/market/clearing.py`); households holding back hours for their own plots by last
year's wage (`sim/economy/households_own.py`, `withhold_hours`, now limited to held land, 551); producers' hiring sized
by last year's prices and sales (`sim/economy/producers*.py`, `labour_bids.py`).

What it would take: reproduce the alternation on the small economy fixture (`sim/tests/economy_fixture.py`) or a built
two-market case, find the rule whose response to its own last value overshoots, and damp or derive it. Test: under a
constant setting the rule's year-on-year response has gain below one, and the fixture's wage does not alternate.
