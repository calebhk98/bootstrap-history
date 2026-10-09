# Negative value for a waste by-product: research and recommendation

Context: Complaints/309, owner decision of 2026-10-06 (a waste by-product may carry a negative value, a disposal cost). Research only; no code was changed. Source strength labels: **A** = primary or peer-reviewed or standard textbook (cited from a search result summary, not read in full unless said); **B** = working paper, conference paper, or reputable secondary summary; **C** = popular article, forum, game developer post, or blog (a lead, not evidence). No source below was read in full text; every citation rests on a search result summary, so verify the exact claims before quoting them in design documents.

## 1. Summary of the recommendation

1. Do not store a negative price as a special case of a by-product. Model disposal as a physical sink technique: a recipe that takes the by-product plus labour, freight and dump land and outputs nothing. Its computed cost per kilogram is the disposal cost. A by-product price is then the better of its demand-based or reuse value and the negative of the cheapest disposal cost. This is the von Neumann / linear-programming "costly disposal" case and needs no table of prices (CLAUDE.md 4.1, 4.3, 4.5).
2. The disposal cost comes from mass, distance to a dump, land occupied by the heap, handling labour, and a legal or nuisance distance rule, each a physical or institutional input already present or addable as data.
3. The existing floor (`JOINT_BYPRODUCT_FLOOR_SHARE` in `sim/engine/joint_floor.py`) is a labelled temporary heuristic standing in for exactly this handling cost; the new term replaces it, and the floor can be deleted once every glutted by-product has a disposal technique.
4. The solver can carry a negative price in principle (it damps linearly, not in log space; see section 5) but several places silently assume positive prices. A first code step is small: compute a per-kilogram disposal cost from labour inputs for one by-product (wood_tar_kg), use it as the lower bound in `lift_to_floor` in place of the share-of-standalone-cost floor, and test that the batch is still recovered and the main product's price rises.

## 2. How economic models treat zero or negative joint products

**Free disposal versus costly disposal is the decisive assumption.** In a linear-programming or activity-analysis model, a surplus output enters as an inequality (produced at least used, so the excess can be discarded at no cost). Complementary slackness then forces the shadow price of any slack good to be zero, and its sign is restricted to non-negative. If disposal is not free (the balance is an equality, or disposal is itself an activity that uses inputs), the dual variable is unrestricted in sign and can be negative: each extra unit lowers the objective. Sources:
- Dorfman, Samuelson, Solow, *Linear Programming and Economic Analysis*, 1958, McGraw-Hill (standard textbook, strength A; chapters on the valuation problem and on market solutions; I could not confirm the free-disposal passage from search results). Catalogue entry: https://catalogo.biblio.unc.edu.ar/Record/economicas.7159/TOC
- Standard LP duality notes on sign rules for equality versus inequality constraints, e.g. Chapter 4, Duality in Linear Programming, Univ. of Porto course notes, undated, https://web.fe.up.pt/~mac/ensino/docs/OT20122013/Chapter%204%20-%20Duality%20in%20Linear%20Programming.pdf (strength B, lecture notes). The sign reading in the search summary is textbook duality theory, not a claim made by that source about by-products.

**Von Neumann and Sraffa joint production.** Von Neumann's model prices a good in surplus at zero (free good) and requires that no active process earns above the going rate; Sraffa-style square joint-production systems have no such rule and can return negative prices for some outputs. Findings:
- Salvadori and Steedman (1988), survey of joint production including conditions for positive prices and free disposal, Bulletin of Economic Research 40(3), 165-195, https://ideas.repec.org/a/bla/buecrs/v40y1988i3p165-95.html (strength A, peer-reviewed; read via abstract only).
- Woods, J. E. (1987), cited in the search summary: negative prices and quantities arise in square multiple-product models through row or column dominance in the net output matrix (strength B, known only second hand here; the full reference was not retrieved).
- Schefold, B. (2005), "Joint production: Triumph of economic over mathematical logic?", European Journal of the History of Economic Thought 12(3), 525-552, https://ideas.repec.org/a/taf/eujhet/v12y2005i3p525-552.html (strength A; truncation and dynamic approaches; I did not read the rule itself).
- Kurz and Salvadori (1995), *Theory of Production: A Long-Period Analysis*, Cambridge University Press, joint production chapter, https://www.cambridge.org/core/books/theory-of-production/24F59E209D9F472AA5E679C78FC30F96 (strength A; the chapter was not read).
- Lager, C., paper at the 16th International Input-Output Conference, https://www.iioa.org/conferences/16th/files/Papers/LAGER.pdf (strength B): negative elements in the Leontief inverse under the commodity technology assumption, handled with the von Neumann free-goods rule via a linear programme.
- Cottrell and others, mailing-list thread "Negative values in pure joint production", https://users.wfu.edu/cottrell/OPE/archive/0410/0029.html (strength C, discussion list).

Lesson for us: the sign of a by-product's price is not an accident of a fixed point, it is a modelling choice about disposal. `docs/architecture/ECONOMY_MODEL_SURVEY.md` section 1 already says the fixed point must be allowed to return a price at or below zero rather than be clamped; this research agrees, with one addition: below zero is bounded below by the cheapest disposal activity, otherwise the price is unconstrained and the Sraffa negative-price pathologies appear.

**Input-output with waste.** Leontief's 1970 environmental model adds a pollution generation row and separate pollution elimination sectors; elimination sectors have their own input structure, so the cost of disposal is a computed sector cost, not a price table. Sources:
- Leontief, W. (1970), "Environmental repercussions and the economic structure: an input-output approach", Review of Economics and Statistics 52(3) (strength A; known from the secondary descriptions below, not retrieved).
- Luptacik and Bohm (1999), "A Consistent Formulation of the Leontief Pollution Model", Economic Systems Research (strength A; named in a search summary only).
- Kagawa, Inamura, Moriguchi, hybrid waste input-output with scraps as joint products under a mixed technology assumption, https://www.iioa.org/conferences/14th/files/KagawaMFP-018.doc (strength B).
- Brink and Idenburg, "Cost effective pollution abatement in an IO model", https://www.iioa.org/conferences/16th/files/Papers/Brink&Idenburg%20Cost%20effective%20pollution%20abatement%20in%20an%20IO%20model.pdf (strength B): abatement costs flow into intermediate prices and so into the price of the main product, which is the effect we want.
- Ayres and Kneese (1969), "Production, Consumption, and Externalities", American Economic Review 59(3), 282-297, https://www.jstor.org/stable/1808958 (strength A): mass balance, so residuals equal inputs by weight. Useful because it gives the physical quantity that sets the mass of waste to dispose of.

**Environmental economics and CGE.**
- A thermodynamics and economics of waste model with a waste supply and demand curve: in a "pay for trash removal" economy waste sells at a negative price, in a recycling economy at a positive price. arXiv cond-mat/9309029, https://arxiv.org/pdf/cond-mat/9309029 (strength B, preprint; author not captured by the search, check).
- CGE waste sectors (landfill, incineration, recycling, composting as separate sectors; flat fee gives households a zero marginal price): Bartelings, GTAP/MAGNET workshop paper, https://ftp.zew.de/pub/zew-docs/div/EMworkshop/Bartelings.pdf (strength B). A China waste CGE with a SAM that splits waste management sectors: https://cetjournal.it/index.php/cet/article/view/2416 (strength B). None of the CGE results retrieved discussed negative prices explicitly; they price waste services as a positive fee paid by the generator, which is the same thing seen from the other side (the generator's by-product has value minus the fee).

## 3. How a disposal cost is physically made up

Physical components, which are the inputs the sim can compute:
1. Handling labour: loading, carting, tipping, per unit mass.
2. Haulage: mass times distance to the dump, priced by existing freight (`sim/geography/` routes and freight).
3. Land: a heap of fixed bulk density and stable height occupies area; area times the land rent the sim already computes, for as long as the heap exists. Heaps do not decay, so the land is occupied for the rest of the run, and rent accumulates; a one-off capitalised rent is the simple form.
4. Containment and nuisance: a rule that forbids the waste within some distance of settlement or water, which lengthens the haul. This is an institutional parameter, not a physical one, and should be a state-level rule (any actor's state can set it) with a labelled provenance.
5. Treatment (burning, neutralising, burying), when an available technique exists.

Historical evidence, with strength labels (mostly weak; the search turned up few primary sources, so these are leads):
- Coal tar before dyes. Dan Fagin's account of the aniline dye industry (*Toms River*, 2013), as excerpted at https://www.scientificamerican.com/article/toms-river-excerpt-on-aniline-dye (strength B, excerpt of a trade book) and summarised at https://www.inverse.com/article/42183-google-doodle-william-henry-perkin-aniline-dye-toxic-poison (strength C): gasworks coal tar was close to a waste, given away, with limited use as waterproofing, otherwise dumped in pits or water. Perkin's 1856 mauve (Science Museum Group biography, https://collection.sciencemuseumgroup.org.uk/people/ap17271/perkin-sir-william-henry, strength B) turned it into a feedstock. The dyes' own wastes then polluted waterways, so a waste solved by one industry created another.
- Slag to cement. Water-chilled slag found latently hydraulic in 1853, activation work in 1862, first dedicated blast-furnace cement works in 1888 and standards allowing slag fractions from 1909 and 1917, per de Rooij's conference presentation, https://webpages.mcgill.ca/staff/Group3/aboyd1/web/Conferences/AMW%20XI/Presentations/de%20Rooij.pdf (strength B). Early secret adulteration of Portland cement with ground slag: "Manufacture of cement from blast furnace slag", AusIMM Proceedings, 1918, https://www.ausimm.com/publications/conference-proceedings/the-ausimm-proceedings-1918/manufacture-of-cement-from-blast-furnace-slag/ (strength B, period source). Earlier uses as lime-mortar additive in Sweden from the late eighteenth century, with low reactivity, per the same search summaries. Japan's 1910 slag cement trials stated the aim of using the slag by-product, https://www.jci-net.or.jp/e/publish/bulletin/store/201011/01_e.html (strength B).
- Tanneries. The medieval London practice of banning tanning inside the walls because of smell, pushing it to Bermondsey, is attested only on weak sites (https://www.eamesfineart.com/blog/48/, strength C). Medieval attitudes to smell and miasma, and the tolerance threshold for pollution: Rouse, Massey University thesis (2013) and the Springer chapter at https://link.springer.com/chapter/10.1007/978-3-030-74443-4_7 and the summary https://www.medievalists.net/2014/05/environmental-management-medieval-london-london-filthy-city/ (strength B/C). The pattern matters more than the detail: the disposal cost of a smelly waste was set largely by a legal distance rule, which is item 4 above. Lime pits and bark waste were not found in these results; PCA or MOLA excavation reports for Southwark would be the next step.
- Mine spoil and distillery waste: the searches in this session did not return usable sources. Not covered; do not cite them from this report. For mine spoil the physical model is the same as slag heaps (mass, bulk density, heap area, rent); for distillery slops the nearby-farm feed use is a reuse value that turns the waste into a by-product with demand, but I have no source.

Transition rule that falls out of the history: a waste becomes a product when a technique exists that consumes it at a cost below its disposal cost, because the technique's buyer can then pay up to the avoided disposal cost. In the sim that happens automatically if the disposal technique is in the same recipe set and the by-product's price is the maximum of its disposal-cost floor and any demand price. No event script is needed (CLAUDE.md 4.2).

## 4. Other simulations and games

- Factorio. Machines with several outputs do not stall; per a Friday Facts post unwanted outputs become pollution automatically if not collected, https://forums.factorio.com/viewtopic.php?p=444987 (strength C, developer post, announced as a design direction; check it shipped). Older request threads asked for a burn-off with an extra pollution cost, https://forums.factorio.com/viewtopic.php?p=260074 (strength C). Pattern: disposal is an activity with a resource and pollution cost, not a negative price, because there is no price system.
- Victoria 3. Prices come from supply and demand around a base price, with oversupply selling at a discount (developer diary on national markets, https://forum.paradoxplaza.com/forum/developer-diary/victoria-3-dev-diary-9-national-markets.1484917/page-3, strength C). The summaries show nothing about negative values or waste.
- Anno and X4. Searches found nothing on waste in Anno. X4's scrap recycling is described only in forum posts (https://forum.egosoft.com/viewtopic.php?p=4912608, strength C). I found no documented negative-price handling in these games.
- Agent-based economics. Fraccascia, Giannoccaro and Albino (2017), "Policy measures for industrial symbiosis networks", Sustainability 9(4), 521 (title as recalled; confirm), https://www.mdpi.com/2071-1050/9/4/521 (strength A): landfill tax and subsidy as levers on whether by-product exchange forms. Mastio et al., spatial double-auction by-product market, arXiv 2512.17979, https://econpapers.repec.org/paper/arxpapers/2512.17979.htm (strength B, preprint): landfill penalties, transport cost and firm density shape circular performance. Both use landfill cost as the outside option that sets how low a by-product's price can go, which matches the recommended floor.

Conclusion: no game found uses a negative price in a price-solving economy. The agent-based literature uses landfill cost as an outside option, which is our recommendation in equation form.

## 5. Recommended model for this sim

### 5.1 What sets the disposal cost (all in labour hours per kilogram, the solver's unit)

    disposal_cost_per_kilogram =
          handling_labour_hours_per_kilogram
        + haul_labour_hours_per_kilogram_per_kilometre * distance_to_dump_in_kilometres
        + dump_land_rent_hours_per_square_metre * heap_area_square_metres_per_kilogram

where

    heap_area_square_metres_per_kilogram = 1 / (bulk_density_kilograms_per_cubic_metre * stable_heap_height_metres)

and

    distance_to_dump_in_kilometres = max(distance_to_nearest_free_land, state_rule_minimum_distance_from_settlement_or_water)

- handling_labour_hours_per_kilogram and the haul rate come from the freight and labour data already in `sim/geography/` and `sim/labour/` (check with `grep` for the existing freight rate per tonne-kilometre; I did not find it in this research pass).
- bulk_density and stable_heap_height are material properties (4.1 allows these); a recipe or material record should carry them, labelled temporary where authored.
- dump_land_rent_hours_per_square_metre comes from the existing land rent computation (`sim/world/land*`); heaps occupy land permanently, so use a capitalised rent, i.e. annual rent divided by the interest rate, which the solver already holds as `interest_rate`.
- state_rule_minimum_distance_from_settlement_or_water is a state-owned rule, default zero, so any actor can set it (CLAUDE.md "general actors"). Do not key it on a civilisation id (4.7).
- A treatment technique (burn, neutralise) is just another disposal recipe; the cheapest wins through the solver's existing choice of technique.

Do not put the per-kilogram number in a table: derive it by running the disposal sink recipe through the same cost routine as any recipe.

### 5.2 How the by-product price is set

    price_of_byproduct = max(price_from_demand_or_reuse, -disposal_cost_per_kilogram * kilograms_per_unit)

so the price is zero or positive when anyone wants it and bounded below by the cheapest way to get rid of it. The batch still recovers its total cost: the main product pays total cost plus the disposal cost, as `lift_to_floor` already redistributes a shortfall onto the other outputs in proportion to revenue.

Interpretation checks: the main product gets dearer when a by-product is costly to dump (Brink and Idenburg's abatement-cost pass-through); a buyer with a technique that uses the waste at a cost below the disposal cost pushes the price toward zero or positive (coal tar, slag).

### 5.3 What breaks in the price solver (read from `sim/engine/solve_prices_core.py`, `solve_prices.py`, `joint_allocation.py`)

The solver is not in log space in the code I read: damping is linear, `damped_price = (1 - damping) * previous + damping * best` (solve_prices_core.py near lines 620 and 1258), and the divergence test uses `abs(damped_price)`. A negative number passes through the damping. Things that do assume positive prices:

1. Convergence measure. Relative change is only computed when `previous_price > 0` (lines near 624 and 1261). A negative by-product price would be skipped, so the loop could report convergence while it is still moving. Fix: use absolute change scaled by a magnitude of the price, for example `abs(change) / max(abs(previous), small_scale)`.
2. Candidate choice. `min(candidates)` picks the cheapest route to a material. A negative candidate for the by-product always wins, even when it is below the disposal floor. The floor must be applied before the minimum, or the minimum must be taken over a set already clipped at `-disposal_cost`.
3. Cost split. `_split_by_value` in `joint_allocation.py` splits by `quantity * reference_price` and falls to another branch when `total_value <= 0`. Negative reference prices would corrupt shares. Keep the split on non-negative reference values (positive anchors and standalone cost) and apply the disposal floor after the split, as `lift_to_floor` does now. `lift_to_floor` itself keeps `floor` positive and stops when payer revenue is not large enough; the negative version must take the shortfall from the other outputs by the same rule, and declare what happens if no payer exists (the batch cannot be run at all; the main product's own price should absorb it).
4. Consumers of a price that raise it to a power or take a logarithm. Complaints/309 notes `economy_materials._generic_national_output_uncached` already guards a power on a near-zero price; a negative base raised to a fractional power is NaN. Also `prices.py` uses `math.log` for bands of farmed area, not prices, so that is unaffected. Run `grep -rn "\*\* \|math.log\|math.pow" sim/economy sim/engine sim/world` to list the rest (I did not enumerate them).
5. Recipes whose inputs include the by-product. With a negative input price the recipe's cost falls and could go below zero, which looks like free money. Bound it: the disposal sink recipe, and any recipe consuming the waste, must have its cost per output floored at what the same output costs by its other route; and the input-credit from taking a waste cannot exceed the avoided disposal cost (this follows from the price floor in 5.2).
6. Display and the player. A negative price is printed as a "price"; label it a disposal cost in the UI note (not an `_internal` field).
7. Reachability. `compute_resolvable_materials` assumes every material has a producing technique; a waste sink has no output material. The sink recipe needs a representation (an output of "disposed" mass, or a special no-output recipe that the cost routine understands) before it can be priced.

None of these needs a log-space rewrite. The most fragile are items 1, 2 and 7.

### 5.4 Minimal first code step and regression test (TDD per CLAUDE.md 6)

Step 1, narrowest useful change: in `sim/engine/joint_floor.py`, replace `JOINT_BYPRODUCT_FLOOR_SHARE` with a `disposal_cost_per_kilogram` argument supplied by the caller, computed from a new small module (for example `sim/engine/disposal_cost.py`) that implements the formula in 5.1 from handling labour, haul distance, bulk density, heap height and land rent. Keep the lower bound as `-disposal_cost` and fix items 1 and 2 above in the same change. Run `python3 sim/constants.py --burndown` to confirm one temporary heuristic is retired.

Regression tests (new file, `sim/tests/test_negative_byproduct_value.py`, `QUICK_TOPIC = True` because they use small fixtures):
1. A glutted by-product with no demand and a known disposal cost gets a price equal to the negative of that cost (to a tolerance), and the batch recovers its total cost (`sum(price * quantity) == total_cost`), with the main product's price higher than in a run where the by-product is free.
2. Same by-product with a demand anchor above the disposal cost keeps its positive price (the negative term must not override a value).
3. The disposal cost grows with distance to the dump and with the heap's land rent, and falls with bulk density (monotonic tests on the new function with literal small inputs).
4. Convergence: a solve containing a negative-priced output reports non-convergence while the negative price still moves (guards item 1 of 5.3).
5. The existing `test_solved_wood_tar_is_not_a_denormal` in `sim/tests/test_joint_byproduct_floor.py` should change to assert a finite price at or above the negative disposal bound, so no denormal appears.

Step 2 (later): the disposal sink recipe in `data/production/` with real labour and land inputs, so the number comes from the cost routine and not from the new module; then a state rule for minimum dump distance.

## 6. Open questions for the owner

- Does an actor ever choose not to dispose (dumping in a river, which pushes the cost onto others)? Environmental economics calls this the externality (Ayres and Kneese 1969); the sim could model it as a state-enforced rule with an enforcement cost, otherwise the dumping cost to the producer is zero. Not covered by the recommendation above.
- Whether heap land stays occupied forever (capitalised rent) or heaps can be reclaimed; affects the land term.
- Distillery slops and mine spoil lack sources here; a second research pass is needed if those two matter for the Rome and medieval starts.
