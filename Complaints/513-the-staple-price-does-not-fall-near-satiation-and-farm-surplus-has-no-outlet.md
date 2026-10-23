# The staple price does not fall near satiation and a farm surplus has no outlet: need-sized hands remain the floor

**Status:** partly fixed - intake rises to a sourced satiation level and farm effort follows the staple price against the wage; need-sized hands are still the floor, the staple price does not fall near satiation, and surplus beyond satiation is not sold, stored or fed to animals

Found closing 480. Originally `LabourAllocationMixin._allocate_farm_workforce` put just enough people on the land to meet
the population's food need (`farm_workers_needed`): a better technique frees hands, a shortfall calls for hands
and then for clearing. Nutrition therefore sits at need every year, and the fertility and mortality responses
that read it never move. In a default Rome a food technology leaves population unchanged to the person over
decades; only once all arable land is cleared does it raise population
(`test_population_farm_technique.py`, both checks).

Why it matters (CLAUDE.md 4.1, 4.2): no household decides how much to farm; the allocation is a rule that holds
food at need, so the food side of the demography can only bind at the land ceiling. A society with spare land
and a better plough should eat somewhat better, or keep the same hours and sell a surplus, or grow, depending
on prices and the households' choices.

What it would take: farm work chosen by households and farms against the price of food and the wage
elsewhere (the agent economy already prices both), so a cheaper calorie raises consumption toward satiation
and the demography reads the outcome.

## Finding: a food technique on fully worked land leaves no surplus

With the sourced wheat labour per hectare (646's Columella figures) the Rome opening's cleared land is fully worked:
farm hands times hectares a hand works equals the farm land. A food toolkit then saves only a small share of hours per
hectare and adds almost no yield, so intake stays at need whatever the technique. The slow check
`farm_surplus_intake` ("a better technique with spare land raises nutrition") is red for this and names 513; making
the cleared land larger in both runs does not change it. Measure: `python3 -m sim.tests --slow --only
farm_surplus_intake --jobs 1`, and read the farm workers, hectares per worker and `farm_land` of a Rome opening. Open
question for this complaint: is the opening's farm sized to exactly the land (then no technique can show a surplus
until clearing answers the price), or is spare land expected at an opening? Section 3 of
`Complaints/reports/research-urban-share.md` and the farm-share band in 619 bear on it.

## Owner decision (2026-10-14)

Food beyond need can raise intake, up to a satiation level (on the order of what well-fed modern people eat, not
several times need); beyond that, extra food is stored, sold, fed to animals or wasted. The satiation level is a
biological limit and should be declared as one, with a source. The needs kernel already has `limit_satiation`
(`sim/world/need_basket.py`); farming effort should follow the food price against the wage elsewhere, so farmers
leave farming when food is cheap and the price recovers.

## Progress

- The food need declares `satiation_per_capita_per_year` in `data/world/needs.json`, a biological limit with a
  source (FAO food balance sheets, dietary energy supply in high-income countries), held equal to
  `agriculture.MAXIMUM_INTAKE_MULTIPLE_OF_SUBSISTENCE` by `test_farm_satiation.py`.
- `sim/labour/farm_intake.py`: hands stay on the land past need while an hour of farm work, at the agent
  economy's staple price, is worth at least an hour of the unskilled wage, up to the hands that feed the people
  to satiation and the hands the cleared land can use. Where food is cheap against the wage, or no price exists
  yet, the farm is sized to need and farmers leave, as before. The surplus is eaten through the granary's
  existing rule (grain beyond the reserve, up to the satiation level), so nutrition and the demography that reads
  it respond (`test_farm_surplus_intake.py`).
- Farm effort is now continuous in the price ratio (`kept_farm_workers`: today's hands times the ratio to the power
  1 / (1 - labour elasticity), from the diminishing marginal product of hands on fixed cleared land, capped at
  satiation and the cleared land); `test_farm_effort_follows_price.py`.
- Remaining: need-sized hands are still the floor under that response; the staple's price does not
  yet fall as intake nears satiation (the household basket caps food at the same level, but the farm sector does
  not see that demand curve), and surplus beyond satiation is not yet sold, stored or fed to animals by anyone.

## Tried and not merged

Branch `farm-effort-follows-food-price` (deleted unmerged, commit `37bb6313`): effort as the share `value / (1 + value)` of
surplus hands. Rejected: an invented functional form, neither derived nor labelled, and it lowered intake after a food
technique. The waste count (`carry_forward_and_waste_kg`, `holdings.farm_wasted_kg`) was worth keeping. A continuous
response should come from households' own allocation of hours (each cohort comparing the farm hour with its own wage),
and the surplus should reach the agent economy as supply.
