# The spin-up's interest rate decays toward zero, then jumps

**Status:** open

Found measuring 507 Stage 7 on top of Stage 2: in every civilisation's spin-up the market interest rate falls by the
same share each year toward zero and then jumps by a large factor in a single year (Mexica's rose more than
fiftyfold in one late spin-up year). Most of the spin-up's failure to settle in the last year is this rate jump, not
goods prices (`game.economy.spin_up_result()` gaps; `python3 sim/simulator.py opening-checks`). A rate that decays
by a fixed share a year looks like a smoothing or memory rule acting on an empty or near-empty credit market, not a
clearing of saving against borrowing.

What it would take: trace the rate's yearly path and what sets it (saving offered, loans asked, `bounded_rate`, the
capital market's memory), find why it decays geometrically and what makes it jump, and make it clear from the
year's funds and requests. Test: over a spin-up with no shock the rate moves by at most a bounded share a year, and
it rises when loan requests exceed funds offered.

Likely cause found since: the clearing uses ceilings below zero from requests that cannot borrow (547).
The settled test also cannot pass while the rate approaches zero (548).
