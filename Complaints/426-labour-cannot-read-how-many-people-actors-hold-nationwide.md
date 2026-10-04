# Labour cannot read how many people actors hold nationwide, so soldiers leave production only approximately

**Status:** open

People under arms now leave the society's labour allocation (Complaint 314,
`sim/labour/labour_allocation.py` `_people_under_arms`). Labour reads actors' staff only through
`LabourWorld.actor_staff_fte(trade)`. That is the slice of the staff drawn from the founder's reachable
pool (`sim/engine/agents_port_budget.py` `BudgetView.local_staff`: the nation's share of the trade
applied to the reach), not the nationwide headcount. Labour scales the slice back up by nation over its
own reach. The reach the state used when it booked the slice differs from the reach labour sees later
in the year, so the recovered army is off.

Measured on rome_100ad after two years:
- the government record holds 307,800 soldiers;
- labour's inversion gives about 186,000.

Command:
`python3 -c "from sim.tests.harness import sim; ..."` (no command prints both yet; the figures came from a
scratch script reading `state.actors.records['government:rome_100ad'].army` and `labour._people_under_arms()`).

What it would take:
- `LabourWorld` gains `actors_staff_nationwide(trade)`, read from the actors' records (the government's
  `army` for its soldiers, every actor's staff for the rest).
- `_people_under_arms` reads that member and drops the inversion.
