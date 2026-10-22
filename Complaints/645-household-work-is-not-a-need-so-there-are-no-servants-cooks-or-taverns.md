# Household work is not a need, so there are no servants, cooks or taverns

**Status:** mostly done: the household chooses by the worth of its hour, own hours are kept out of the labour offered, a cohort with no hearth buys cooked food, and a hearth burns cooking fuel; land after the opening (473), a whole-game re-measure and an urban marker remain

Owner decision (530, 2026-10-20): cooking, fetching water and fuel, cleaning, grinding and childcare take hours every
household spends, and they are a need met by the household's own hours or by hiring. Religion as a need is out of scope;
it is a mod (`mods/TASKS.md`).

## What is built

- `data/world/household_work.json`: hours a person's share of household work takes, by task. Water, fuel and grinding
  come from Blackden and Wodon (eds), Gender, Time Use, and Poverty in Sub-Saharan Africa, World Bank Working Paper 73,
  2006, overview p. 9 (opened): an average adult female spends from just under 1 hour to 2 hours 20 minutes a day carrying
  water, firewood and crops for grinding. Cooking, cleaning and childcare hours: no source found, labelled estimates
  (confidence D) with a `retire`. Cooking fuel (`cooking_fuel_mj_per_person_per_day`): Johnson and Bryden 2012 (abstract
  opened).
- `household_work` need in `data/world/needs.json`, no floor, met by `domestic_service_hour`
  (`data/production/95_household_services.json`), made by the `domestic_servant` trade (group `services_state`).
  `cooked_meal_kg` is the cooked food a cook or eating house makes.
- `sim/economy/households_work.py` and `household_work_year.py`: a cohort hires all its household work when an hour of its own
  labour (the wage it faces, averaged over the hours it would sell) is worth more than the servant's price, otherwise none, so
  hiring follows income and the wage with no typed share (the earlier typed budget share is retired). The servant's price is
  last year's `domestic_servant` wage, else the tile's subsistence wage per hour.
- Own hours are kept back: `labour_supply.HourSupply` (earlier `Economy._shortfall_hours`) adds each cohort's own household-work hours to its own-plot hours, so
  `withhold_hours` cuts the offers; `_grow_own` does not count them as spare hours.
- Hearth: a cohort has one when it holds a title or a tenancy on its tile (`has_hearth`). A hearth-less cohort gets
  `without_hearth_basket` (food only from goods marked `ready_to_eat`, no cooking in its household work) and burns no fuel;
  a cohort with one pays the cooking fuel added to its warmth floor (`households_work.with_cooking_fuel`).
- Tests: `sim/tests/test_economy_household_work_year.py`, `sim/tests/test_economy_households_work.py`.

## Still to do

- Land after the opening settles (473), since a new need moves the opening's demand.
- Re-measure with a whole game: the hours kept back are a large share of the offered hours, and the fuel price moves; compare
  `simulator.py economy-check` hired share, wage over floor and fuel prices before and after.
- No urban marker exists in the economy; when one does, it should also remove the hearth.

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
- Servants per household (the historical servant literature) was not searched; the hire switch rests on wages, not on a count.

## Update: household work shares the choice

Household work's own hours and the hours kept for the plot are the same kind of choice (an hour at home against the wage).
`HourSupply` keeps the larger of the plan and the plot choice, then adds household work. The fixture has no
household-work data, so only the plot side is exercised there; leisure is not modelled.

## Update: leisure is modelled, household work still enters at the servant's price (473 Update 8)

A household's hours are shared by `labour_supply.HourSupply`: own-plot plan and household work first (the work still hired or done
by the all-or-nothing rule against the servant's wage), then the plot by its marginal return, then leisure by a declared
preference (675), then sale. At the opening the leisure anchor is solved so offered equals hired, so what household work and
leisure each take of Rome's 2000 hours a worker is still not measured separately: Rome's household-work hours come from the data
file's estimates (cooking, cleaning and childcare confidence D) and are not re-measured here. The hire/own switch is still a
step in the wage (households differ in the wage they face, so the aggregate rises step by step); it was not made smooth.
Cooked food, cleaning and childcare as bought substitutes are not yet data in `household_work.json`.

## Effect measured after the sourced hours (PM)

The opening's typical traded good now sells below its making cost (`price_over_making_cost_band_validation`, see 558). The
cause is traced in 473 Update 11: the opening is unchanged and the cycle takes a different path. The sourced figures stay.

## Grinding is charged to households that can buy flour (PM, measured)

A default Rome game's market rate is 0.199 at 1cd50f79 and 0.48 (the ceiling) after the sourced hours merged (e72b36c0):
households have nothing left to save and no lender can be met (state scenarios restated around it; credit work 641).
Command: `PYTHONPATH=. python3 -W ignore -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').market_rate())"`.
Most of `water_fuel_and_grinding` is hand grinding (the Burkina Faso table), charged to every household of every civilisation,
while the economy also mills grain into flour (`data/production/95_grain_milling.json`) (whether a household can buy it is being checked). Grinding is a
way of making flour, so it belongs with the household's choice of making or buying (the rule this complaint already has for
cooked food), not in a fixed daily charge. Water and fuel fetching stay household work.

## Update: grinding is make-or-buy (measured)

- Verified: households eat grain and flour as well as bread. The food need lists wheat, millet and maize (grain), `flour_kg`
  and `bread_kg` (ready to eat) among others; they buy a mix by cost per unit. `flour_kg` is an ordinary household good in
  the goods market (priced at the Rome opening; milled by `data/production/95_grain_milling.json`), so no new flour path
  was needed. What was missing was the weighing of a grain against its milled good.
- `water_fuel_and_grinding` is split in `data/world/household_work.json` into `water_and_fuel` (44 minutes, fixed) and
  `grinding` (108 minutes, flagged `scales_with_ground_grain`), from the same Burkina Faso table. The two sum to 152
  minutes; the old figure rounded that to 2.5 hours, so the needs file satiation moved with it.
- The rule (`sim/economy/household_grinding.py`, used by `household_work_year.cohort_plan`): the needs file marks a grain
  `milled_as` its flour. A cohort buys a grain milled when the milled good costs less per need unit than the grain plus
  the sourced grinding hours per need unit at the worth of its hour (`Cohort.milled_grains`; the grain leaves its food
  basket). Hours fall only on the share of food it grinds by hand. With no priced milled good, it grinds at the sourced load.
- Labelled heuristic (`retire` in the data): the table gives no kilograms, so the full load is taken as grinding a diet
  wholly of grain at the food floor.
- Tests: `sim/tests/test_economy_household_grinding.py`.
- Measured market rate (command above), before then after: rome_100ad 0.48 then 0.48; han_china_100ad 0.8 then 0.8;
  england_1300 0.1919 then 0.147; mexica_1500 0.4 then 0.3. Rome stays at the ceiling: at its opening most cohorts now buy
  wheat and millet milled, but they still hire nearly all the remaining household work (about 470 hours a person), so
  grinding was not what held the rate up. Nothing was tuned.

## Why Rome saved nothing: the hire rule priced an hour at the servant's wage, the household paid the service's price (measured)

Trace (scratch probe, not kept; Rome opening, one stepped year, per person, aggregated by income class): at the branch tip and at
1cd50f79 alike, households spent nearly their whole income on the `household_work` floor (`domestic_service_hour` bids took 231 to
921 a person of an income of 234 to 887 at 1cd50f79; 237 to 891 of 239 to 905 at the tip), left almost nothing in goods or the
store, and offered savings of about one thousandth of their cash (cohorts offering: 1 and 3 of 312). The hire switch compared the
worth of the household's hour with the servant's wage (0.40 to 0.42 an hour), but the household paid the market price of the hour
of service (9.1 at 1cd50f79, 2.9 at the tip, for a hired 378 and 439 hours a person). So the rule hired at a price it did not pay.
The rate itself: scarcity wage (8e354ebe) moved it from 0.126 to 0.147; the sourced hours (e72b36c0) took it to 0.48; the second
credit clearing, with savings of about a millionth of requests, returns the ceiling in both builds (1cd50f79 read 0.199 by where the
spin-up stopped).
Fix: `household_work_year.service_price_per_hour` reads the price of the goods that serve the household-work need per need unit,
the servant's wage only when none is posted. Rule tests in `sim/tests/test_economy_household_work_year.py`. The sourced hours are
unchanged. After: Rome hires almost nothing (6 of 312 cohorts), does about 466 hours a person itself, offers about a quarter of
its cash as savings, and the clearings lend at 0.07 to 0.08. Market rate (command above): rome_100ad 0.016, han_china_100ad 0.132,
england_1300 0.049, mexica_1500 0.375. Rome now reads below the households' own ask floor (the loss share): the opening is
unsettled, not tuned. Mexica stays high and is not traced here.
