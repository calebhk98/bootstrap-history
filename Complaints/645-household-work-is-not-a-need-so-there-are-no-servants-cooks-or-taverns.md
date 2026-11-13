# Household work is not a need, so there are no servants, cooks or taverns

**Status:** partly - household choice by logit, own-hours withholding, hearth and cooked food, grinding make-or-buy, full-cost hiring, an urban marker and whole-servant hiring are built; landing after the opening settles (blocked on 473) and a whole-game re-measure (the orchestrator's) remain

Owner decision (530, 2026-10-20): cooking, fetching water and fuel, cleaning, grinding and childcare take hours every
household spends, and they are a need met by the household's own hours or by hiring. Religion as a need is out of scope;
it is a mod (`mods/TASKS.md`).

## What is built

- `data/world/household_work.json`: hours a person's share of household work takes, by task, with sources and labelled
  estimates (see Research needed). Cooking fuel (`cooking_fuel_mj_per_person_per_day`): Johnson and Bryden 2012 (abstract opened).
- `household_work` need in `data/world/needs.json`, no floor, met by `domestic_service_hour`
  (`data/production/95_household_services.json`), made by the `domestic_servant` trade (group `services_state`).
  `cooked_meal_kg` is the cooked food a cook or eating house makes.
- Hire or do: `households_work.hired_hours` hires the share of a cohort's household work given by a logit on the service
  price against the worth of an own hour (`price_setting.choice_shares`, `WORK_CHOICE_INTENSITY`, a labelled heuristic), so
  the share falls smoothly with income and the wage. `household_work_year.service_price_per_hour` reads the price of the goods
  that serve the need per need unit, the servant's wage only when none is posted. `household_work_year.work_terms` values an
  own hour at the wage its offers face, weighted by the share of hours expected to sell (`households_work.smoothed_sold_share`
  over the years; year 0 from the opening's own sizing, `households_work.expected_sold_share` via
  `household_work_year.expected_shares`) and less the hours spent directing the servant (`households_work.net_hour_value`,
  `supervision_hours_per_hired_hour` in the data file, no source found, confidence D, with a `retire`).
- The opening settles the hired share on a cycle by bisecting over households ranked by what an hour hired gains them
  (`opening_plans._by_margin`) and posts the price at which the servants there are enough
  (`households_work.service_price_that_fits`).
- Own hours are kept back: `HourSupply` in `sim/economy/labour_supply.py` adds each cohort's own household-work hours to its own-plot hours, so
  `withhold_hours` cuts the offers. Every other hour is offered to the market (no leisure split); household work is fixed
  against the labour offer, not chosen against leisure.
- Urban marker (`sim/economy/household_urban.py`): a tile is urban when the people of its cohorts who work no land are at least
  `URBAN_LANDLESS_SHARE` of its people (a labelled heuristic, retire in the declaration). A cohort on an urban tile has no hearth.
- Whole servants (`sim/economy/household_servants.py`): with `servant_year_hours` in the data file (absent: hiring stays divisible), each
  household of a cohort hires a whole servant's year or none. It hires none if last year's income per household is below the cost
  of that year; of those that can pay, the share that hires is a logit of the cost against the worth of the hours freed (at most
  the household's own work). Tests: `sim/tests/test_economy_household_servants.py`.
- Hearth: a cohort has one when it holds a title or a tenancy on its tile and the tile is not urban (`household_work_year.has_hearth`). A hearth-less
  cohort gets `without_hearth_basket` (food only from goods marked `ready_to_eat`, no cooking in its household work) and burns
  no fuel; a cohort with one pays the cooking fuel added to its warmth floor (`households_work.with_cooking_fuel`).
- Grinding is make-or-buy (`sim/economy/household_grinding.py`, used by `household_work_year.grinding_plan`): the needs file
  marks a grain `milled_as` its flour; a cohort buys the grain milled when the milled good costs less per need unit than the
  grain plus the grinding hours at the worth of its hour. Hours fall only on the share it grinds by hand. The full load is a
  labelled heuristic (the source gives no kilograms), `retire` in the data.
- Tests: `sim/tests/test_economy_household_work_year.py`, `test_economy_households_work.py`,
  `test_economy_household_grinding.py` (`test_economy_opening_household_plans.py` no longer exists).

## What is wrong now

- Land after the opening settles (473): blocked. The shipped openings fail `spin_up_settled` for every civilisation (Complaint 970,
  473 Status), so the opening is a point on a cycle and the household-work split it fixes moves with that cycle. This lands when 473
  closes; nothing here can settle it.
- No whole-game re-measure since the logit hiring, the Eurace rules, the urban marker and whole servants: hired hours a person, the
  service share of the opening basket, the market rate and fuel prices have not been measured together. Measure on a default Rome game with
  `python3 sim/simulator.py economy-check` and `PYTHONPATH=. python3 -W ignore -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').market_rate())"`.
  Check that the hired share falls within the range sources give (below).
- The worth of a freed hour is the average wage its offers face, not the marginal one.
- Cooked food, cleaning and childcare as bought substitutes are not yet data in `household_work.json`.
- A whole servant's year is paid in full while only the hours the household needs count toward its floor; the unused rest of a
  servant's year is not shared with another household.

## Research needed

Done in part. The hours in `data/world/household_work.json` now come from opened sources, per adult woman: water, fuel and
grinding from a rural Burkina Faso time allocation table (Carr and Sandhu 1988, as reproduced in Gordon, Swetman and Albright,
Issues Paper 6, 2002, Box 1); cooking, cleaning, laundry and care from the Ghana 2009 time-use diary (Dinkelman and Ngai, JEP
36(1), 2022, Online Data Appendix, Table A.1). Both are confidence C. What is still open:

- The share of adult women among a household's people is still a labelled estimate (confidence D); every task multiplies by it.
- The Ghana diary is a national sample with some piped water and mills, not a pure subsistence household, and its cooking
  category includes some wood and water fetching that the first task also counts. A time allocation study of a society
  without either (Minge-Klevana 1980, the UCLA Time Allocation project) was not found open online.
- The Burkina Faso table is a secondary reproduction with no survey year or sample size, and its "Household" line (cooking
  among it) is not broken down.
- Servants per household: only two secondary sources opened (below); the hire switch rests on wages, not on a count.

Sources opened: `humanprogress.org/grim-old-days-peter-lasletts-the-world-we-have-lost/` (a summary of Laslett, The World We Have
Lost): servants "varied from as low as 4 percent to as high as a third of the population", the high end "in relatively wealthy
times and places, such as London and parts of Norwich in the 1690s"; `johnhearfield.com/History/Breadt.htm` (King's 1688 table):
no servants line, only "Labourers & Outservants" and the households above them, whose counts include their servants. Not found
open: Massie 1759, Laslett's own tables, Roman household slaves. So only a range and the point that the wealthy kept servants
rest on a source (secondary).
