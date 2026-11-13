# No internal stability: no unrest, revolt, provincial autonomy, factions, ruler competence or succession

**Status:** partly - unrest (strata included), risings against the garrison, a ruler's life, competence and accession, disputed accession, the army as a faction, confiscation and land reform are built; open: the remainders below

- Bonded strata exist (`sim/agents/stratum*.py`) and drive income only; there is no unrest, flight or
  revolt (`grep -rni "revolt\|unrest\|rebel" sim/agents sim/engine` finds hazard prose and a label).
- A ruler is a yearly dice roll, `ACCESSION_PROBABILITY_PER_YEAR` (`sim/agents/tuning_spending.py`), that
  makes a donative owed (`sim/agents/budget_works.py`). No ruler record, competence, or succession rule;
  `ForeignGovernment` has none at all.
- Interest groups (`sim/agents/group.py`, `sim/actors/world_groups.py`) are people who lost income to a
  technique. There are no standing factions (crown, army, temples, merchants, provincial governors) that
  contest spending, appointments or reforms.
- Legitimacy is one scalar moved only by works (`sim/polity/reach.py`).

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

**Built (tests `sim/tests/test_stability_rules.py`, also `test_stability_tile_passes.py`, `test_stability_kernels.py`, `test_stability_phase_and_save_rule.py`; the earlier scenario test `test_stability_scenario.py` is gone):**
- Unrest (`sim/agents/unrest.py`): grievance is what the state took (taxes, levies) and owes beyond what it gave (the dole), over
  its taxpayers' income, felt only above the take people are used to (`adapted`, `adapt`), plus the interest groups' own
  grievances (people-weighted), plus land taken off holders on the tile (fading), plus hunger from the tile's own food
  (`regional_eaten_over_need`) and the burden of a collective liability rule (`liability_burden`, from the people registered
  against those left). `unrest = 1 - exp(-pressure)`.
- A rising forms on a tile when its armed, organised discontented would more likely than not beat the garrison (`unrest.rises`),
  so no frequency of revolt is typed. It fights through `battle.fight` (`sim/agents/revolt.py`); a won rising releases the tile
  from the state, at the seat it replaces the ruler. The phase is `step_revolts` in `sim/campaigns/stability.py`, after the campaigns.
- Rulers (`sim/agents/ruler.py`, `Government.accede`): the ruler ages a year at a time and dies at the demography's baseline
  mortality of his age band; the heir is born a childbearing age before; the strongest faction backs him and the runner-up
  disputes the accession with a chance that rises as the two are evenly matched, settled at the seat as a rising.
  `ACCESSION_PROBABILITY_PER_YEAR` is retired.
- Levers `confiscation` (once) and `land_reform` (a cap per holder, the excess to his tenants): `sim/agents/government_levers_land.py`,
  planned by `sim/agents/land_moves.py`, applied by the economy's title rule (`sim/economy/titles_moves.py`, `YearInputs.title_moves`);
  the land taken is the tile's grievance.
- Heuristics added, each retiring here: `ARMED_SHARE_OF_DISCONTENTED`, `RISING_EQUIPMENT_SHARE_OF_REFERENCE`,
  `GRIEVANCE_ADAPTATION_PER_YEAR`, `ORGANISED_FLOOR`, `CONFISCATION_MEMORY_PER_YEAR`.
- Source search: no source opened gives revolts per century for pre-modern states (a search for Turchin and Nefedov, Secular Cycles
  returned reviews and listings without a count; Scheidel was not opened). So no range check is made; the frequency in a
  baseline run is to be measured and printed, not asserted.

- Ruler competence (`sim/agents/ruler.py`): drawn at each accession (and once for the ruler found at the opening) as a lognormal of
  median one (`COMPETENCE_LOG_SPREAD`); `record.council_averaged` makes every draw one (the averaged council). It scales the state's
  reach (`authority.levy_reach`) and what officials keep (`authority.kept_on`) through `reach_factor` and `keep_factor`.
- The army as a faction (`sim/agents/army_faction.py`, `group_servants.py`): plunder from captives taken (`AddArmyPlunder`) is set
  against the pay owed before the loyalty step; below the mutiny line the defecting share of the army counts in the accession
  backing, backs a disputed accession as a challenger, and rises at the seat against a garrison weaker by those soldiers
  (`Stability._army_rises`). Heuristics `COMPETENCE_LOG_SPREAD`, `ARMY_WEIGHT_SHARE_OF_FACTIONS`, `CAPTIVE_VALUE_IN_YEARS_OF_UNSKILLED_PAY`.
- Strata feed unrest: every stratum's welfare (real income in baskets) below its remembered reference, the bonded included
  (`country_rules.stratum_grievances`, view `stratum_grievances`), enters the felt grievance as the larger of it and the groups' own.
  Tests: `sim/tests/test_stability_remainder.py`.

**Left:** temples or governors as factions; a baseline ensemble of risings per century against a source; the rebels' dead are not taken off the people;
a won rising leaves the tile unowned (no rebel state or secession); the ruler's health is the band's baseline; state-held land
rent is booked to the state's account in the economy, not yet to its treasury; the decree reaches the home state's tiles only;
the liability rule's heavier take is read as unrest but is not charged to payers (657 wires it only through the migration
comparison); a full-game run of decades has not been checked for how often the baseline rises.
