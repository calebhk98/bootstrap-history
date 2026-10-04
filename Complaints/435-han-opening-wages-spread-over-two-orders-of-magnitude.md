# Han's opening wages spread over two orders of magnitude, and the two wage models disagree

**Status:** open

In a new han_china_100ad game the agent economy quotes these hourly wages
(`economy.agent_wage_per_hour`, which every employer's quote follows):

| Trade | Agent economy | Labour schedule |
|---|---|---|
| labourer | 1.79 | 83.4 |
| potter | 2.06 | 152.3 |
| mason | 5.0 | 227.6 |
| smith | 119.9 | 227.6 |
| carpenter | 308.1 | 227.6 |

A carpenter earns 172 times a labourer and a smith 67 times. Rome, England, the Norse and the Mexica keep
the smith at about 1.3 to 1.4 times the labourer (main and this branch alike). The labour package's own
opening schedule (`sim/labour/wages.py`, training premium over a subsistence floor) is within a few times
across these trades, but is on another scale from the economy's figures altogether.

Command:
`python3 -c "from sim.tests.harness import sim; g=sim(civ='han_china_100ad'); [print(t, g.labour.market.quote(t), g.labour.wage_per_hour(t)) for t in ('labourer','smith','mason','potter','carpenter')]"`

Why it matters: hiring in Han costs whatever the economy's tile wage memory holds, so a smith
crew is priced like a fortune. The schedule the price solver reads says something else entirely.

What it would take:
- Find why the economy's Han wages diverge (untraded seed wages per tile? a trade nobody offers hours
  in?). `sim/economy/labour_asks.py` and `year_labour.py` are the places to look.
- One authoritative wage model (Complaint 428) removes the second number.
