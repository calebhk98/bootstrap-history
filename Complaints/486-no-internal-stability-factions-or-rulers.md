# No internal stability: no unrest, revolt, provincial autonomy, factions, ruler competence or succession

**Status:** open

- Bonded strata exist (`sim/agents/stratum*.py`) and drive income only; there is no unrest, flight or
  revolt (`grep -rni "revolt\|unrest\|rebel" sim/agents sim/engine` finds hazard prose and a label).
- A ruler is a yearly dice roll, `ACCESSION_PROBABILITY_PER_YEAR` (`sim/agents/tuning_spending.py`), that
  makes a donative owed (`sim/agents/budget_works.py`). No ruler record, competence, or succession rule;
  `ForeignGovernment` has none at all.
- Interest groups (`sim/agents/group.py`, `sim/engine/interest_groups.py`) are people who lost income to a
  technique. There are no standing factions (crown, army, temples, merchants, provincial governors) that
  contest spending, appointments or reforms.
- Legitimacy is one scalar moved only by works (`sim/engine/legitimacy.py`).

Why it matters: the group wants "an averaged competent council" to be a setting they can turn off, and
needs revolt risk from slaves and resentment from badly held provinces to come out of the model.

What it would take: per-tile integration and unrest fed by stratum shortfall, bonded share, control (484)
and identity; a ruler or council record with a competence draw and a switch; faction actors that press
budget lines the way interest groups press bans.

**What 485 now gives this:** the army in the field is a body with `supply_state`, `pay_owed` (the army line's arrears shared
by head) and desertion that rises with the years of pay owed (`sim/world/campaign_attrition.py`). A faction of the army
(loyalty, mutiny, a ruler it backs) has a located force to act with; `group_servants.py` still acts on the headcount.
The heuristics `STARVATION_LOSS_PER_UNFED_DAY`, `DESERTION_PER_YEAR_OF_PAY_OWED`, `ASSAULT_MIN_CHANCE` and
`RETREAT_BELOW_FED_SHARE` retire to this complaint (morale and commanders as actors).
