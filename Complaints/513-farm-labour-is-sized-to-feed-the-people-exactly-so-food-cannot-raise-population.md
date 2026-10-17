# Farm labour is sized to feed the people exactly, so a food technology cannot raise population while land is spare

**Status:** partly fixed - intake rises to a sourced satiation level and farm hands stay while a farm hour pays at least the wage; the food price is not yet cleared against farm effort (see Progress)

Found closing 480. `LabourAllocationMixin._allocate_farm_workforce` puts just enough people on the land to meet
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
and the demography reads the outcome. Owner decision: should a food surplus be able to raise intake above need
(and so fertility and survival), or is freeing labour for other work the intended response while land is
spare?

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
- Remaining: farm effort is a threshold on the price ratio, not a continuous response; the staple's price does not
  yet fall as intake nears satiation (the household basket caps food at the same level, but the farm sector does
  not see that demand curve), and surplus beyond satiation is not yet sold, stored or fed to animals by anyone.
