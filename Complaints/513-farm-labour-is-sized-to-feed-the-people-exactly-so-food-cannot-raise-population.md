# Farm labour is sized to feed the people exactly, so a food technology cannot raise population while land is spare

**Status:** open - owner decision (2026-10-14): a surplus may raise intake up to a biological satiation level, not without limit

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
