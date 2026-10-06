# Research: negative-value by-products and disposal (Complaint 309)

**Status:** research report, no code changed. Written for the owner decision of 2026-10-06 that a waste
by-product may carry a negative value, a disposal cost.
**Marking:** a claim marked *(read)* was checked against a page or PDF opened in the verification pass
(2026-10-06), with the citation given. *(snippet)* means only a search summary or listing was seen, or the
page could not be opened. *(recalled)* comes from memory of the literature and has not been re-read.
*(corrected)* marks a claim in the first draft that the source did not support, with what the source says.
*(disputed)* means sources disagree. An unmarked link was seen as a search result only.
Where this report names code, it was read on this branch.

## 0. What the code does today

* `sim/engine/joint_allocation.py` (`allocate_joint_cost`) splits one batch's cost over its outputs. An
  output with a demand anchor takes a share proportional to anchor price times quantity; an unanchored one is
  valued at the batch's standalone cost per kilogram (a labelled temporary heuristic).
* An anchored output whose anchor is at or below its `disposal_value_hours` is "in surplus": it prices at
  that value (default zero) and the others carry the batch. `disposal_value_hours` is read from the entry
  (`solve_prices_core.py`, passed as `entry.get("disposal_value_hours")`) and documented in
  `data/production/_SCHEMA.md`. The code caps the surplus revenue at the batch cost, so a negative disposal
  value is not reachable today.
* `sim/engine/joint_floor.py` (`JOINT_BYPRODUCT_FLOOR_SHARE`, temporary heuristic, confidence D) lifts every
  output to a share of the batch's standalone cost per kilogram, paid for by the outputs above it. Its own
  `why` says it "stands in for the handling and disposal cost" and "should come from a handling labour term
  in the recipe data". It exists to stop a glut by-product decaying to a denormal in the damped iteration.
* `sim/economy/goods_market.py` clears in log price (`goods_market_solve.py`), so prices are positive. A
  seller with a reservation at or below zero is moved to a token price
  (`MINIMUM_PRICE_SHARE_OF_REFERENCE`), and the comment says waste disposal charged to the seller "is not yet
  modelled". The market has no way for a seller to pay.
* `docs/architecture/ECONOMY_MODEL_SURVEY.md` sections 1 and 6 already conclude: let the fixed point
  return a price at or below zero rather than clamp it, and let a surplus by-product fall to its disposal or
  reuse value.

So two places forbid a negative value for different reasons: the solver floors it to keep iteration
stable; the market clears in log price. A design has to address both.

## 1. How each tradition represents a negative-value output

### 1.1 von Neumann and free disposal

In the von Neumann growth model any good in surplus has price zero and any process that would lose money at
the going prices is not run; the surplus can always be thrown away at no cost. Salvadori and Kurz compare it
with Sraffa's joint production, where Sraffa has no free disposal and so the same system can need a
negative price *(snippet: [Kurz, Salvadori, "Sraffa and von Neumann"](https://econbiz.de/Record/sraffa-and-von-neumann-kurz-heinz/10005484711)
and [Kurz and Salvadori on Sraffa's early joint-production work](https://oreilly.com/library/view/competition-value-and/9781000453140/xhtml/ch11.xhtml);
both pages blocked the fetch, so neither was opened)*.
*(read)* Xu and Peskin, "The impact of universal recycling on the evolution of economic diversity", PLOS ONE
17(1): e0262184, 2022, abstract and introduction ([link](https://par.nsf.gov/servlets/purl/10343279)): in
their von Neumann extension, scenario one has non-negative prices and non-positive excess demand (any good in
excess supply becomes a free good); scenario two has enforced market clearing and prices allowed to be
negative, representing an economy where recycling is required so excess supply cannot be discarded. They
state that the solution to each of the two price equilibrium problems exists at any time, and that a firm may
have to pay another to take unwanted by-products away, which makes the good's price negative (the removal
service has a positive price Ps, the good a negative price Pg, and the payer pays Ps minus Pg per unit). I
did not read the proofs.

What goes wrong:
* Free disposal makes every unwanted output cost nothing to remove. That is false for slag heaps, whey or
  tar, and it hides exactly the cost we want the sim to show.
* Drop free disposal and require exact clearing and equilibrium can fail to exist or give negative prices
  and negative activity levels. A formal solution can have negative quantities or prices in square
multiple-product systems *(read, corrected)*: Nermuth, "The Linear Model of Production", University of Vienna
Working Paper 8401, January 1984 (reproduced 1990), section 1.1 remark "ad (e)" and section 1.2
([PDF](https://homepage.univie.ac.at/manfred.nermuth/NERMUTH1984.pdf)), says the possibility of negative prices
and labour values "was pointed out by Sraffa himself", and that the model requires nonnegative quantities as an
assumption. The paper calls itself a summary of known results. The first draft also cited a
[Cottrell OPE-L post](https://users.wfu.edu/cottrell/OPE/archive/0410/0029.html) for negative values; that page
(Philip Dunn, 26 October 2004) discusses indeterminacy of value under joint production and proposes a
composite commodity to keep value positive, and does not itself show negative values or quantities.
* Which process is run depends on prices and prices on which process is run (a non-convex choice), the
  same fixed-point difficulty our solver iterates through.

### 1.2 Sraffa and the classical joint-production literature

Sraffa's price system admits negative prices *(read: Nermuth 1984, section 1.1 "ad (e)", link in 1.1)*.
*(corrected)* The first draft attributed to Sraffa the reading that waste is an output with a possibly negative
price when the producer pays for removal, citing an
[OPE-L post](https://users.wfu.edu/cottrell/ope/archive/0410/0107.html). That post (Philip Dunn, 26 October
2004) only says the "Great Circular Flow of Torrens, Malthus, Ricardo, Marx and Sraffa treats everything present
at the start of a production period as input and everything present at the end, just before sales, as output";
it says nothing about waste or negative prices, so the waste-as-negative-price step is our inference. The price
system is square only if the number of processes equals the number of goods, which is rarely true once a
by-product exists; the system is then determined by choosing which processes run, as in von Neumann.

What goes wrong: with more goods than processes the price system is underdetermined (the code comment in
`solve_prices.py` names the same defect: "one equation short"); with a fixed set of processes a negative
price can flip which process is cheapest (dominance), so equilibrium may not exist.

### 1.3 Baumgartner, Faber and ecological economics

Baumgartner and colleagues use joint production as a foundation of ecological economics: many damages come
from substances that arise as undesired joint outputs, and whether an output is desired "is not an inherent
property of the substance itself but depends on the context of production"
([The concept of joint production and ecological economics](https://fis.leuphana.de/en/publications/the-concept-of-joint-production-and-ecological-economics-2/);
[Ambivalent joint production and the natural environment](https://fis.leuphana.de/de/publications/ambivalent-joint-production-and-the-natural-environment-an-econom/)).
*(read)* The quoted sentence is on the publisher listing of Baumgartner, "Ambivalent Joint Production and the
Natural Environment: An Economic and Thermodynamic Analysis", Physica-Verlag, Heidelberg, 2000 (Contributions
to Economics). *(corrected)* It is not in the abstract of Baumgartner, Dyckhoff, Faber, Proops and Schiller,
"The concept of joint production and ecological economics", Ecological Economics, 2001, whose abstract (read)
says only that joint production is a conceptual foundation of ecological economics, arises from
thermodynamics, and raises concerns of responsibility and knowledge. One chapter title in the listing is
"Waste Paper: Price Ambivalence" *(snippet)*. The specific claim that Baumgartner and Faber give a negative
price when disposal is costly, and zero or positive when a use exists, is *(recalled)*; no text of the book
was opened.

What goes wrong: the framework tells you the sign is a property of context, which is the behaviour we want,
but it supplies no algorithm to find the price in a model with many goods and techniques.

### 1.4 Leontief 1970 and the waste input-output family

Leontief adds pollution as an extra commodity (a "bad") produced jointly with the good, plus abatement
sectors that consume inputs to remove it; antipollution inputs are intermediate demand
*(snippet)* ([Miller and Blair, Input-Output Analysis, Cambridge University Press, 2009, ch. 10](https://www.cambridge.org/core/books/inputoutput-analysis/environmental-inputoutput-analysis/A1048A88EE6213301A079B741A43A7C2),
whose page only says Leontief (1970) "provided one of the key methodological extensions"; the
[Allan et al. 2007](https://storre.stir.ac.uk/bitstream/1893/7702/1/Allan%20et%20al%20ESR%202007_turner%20last.pdf)
PDF and the 1970 paper, Review of Economics and Statistics 52(3): 262-271, could not be opened, so the
detail of the model rests on search summaries that it adds pollution generation and separate pollution
elimination sectors). The shadow price of abatement is the price the bad carries *(recalled)*. Nakamura and Kondo's waste
input-output model (WIO) lets waste flows be allocated to treatment sectors (landfill, incineration,
recycling). *(read)* Nakamura, "Inter-industry analysis of the demand for landfill capacity"
([IIOA 13th conference paper](https://www.iioa.org/conferences/13th/files/Nakamura_landfill.pdf)): a WIO model
of the Japanese economy with fifty-two industrial sectors, three waste disposal sectors and twenty-four waste
types, run as scenarios of disposal and recycling options. Its conclusion says the treatment cost of
industrial waste is carried by the industry that emits it and has been rising as new landfill sites become
harder to open. *(corrected)* The first draft said the model uses linear programming to choose the cheapest
treatment mix; that paper does not describe linear programming, and Kagawa's
[WIO paper](https://www.iioa.org/conferences/15th/pdf/Kagawa1.pdf) (read, endogenous treatment sectors in a
standard WIO) did not show it in the text I searched either. The programming claim is *(recalled)* from the
Nakamura and Kondo book ([listing](https://www.nhbs.com/waste-input-output-analysis-book-2), *(snippet)*).

What goes wrong: the abatement and treatment sectors are fixed in the technology matrix, so a treatment that
is not in the matrix does not exist; if treatment is chosen by a linear programme (recalled, see above) the price of waste is its dual variable and can
jump when the optimal treatment mix changes; landfill capacity is a stock but the matrix is a flow. The
landfill-capacity paper is the useful part: it treats landfill volume as a binding capacity (it gives a figure
for national capacity and a rising treatment cost). That landfill volume should carry its own price is our design
inference, not a statement in the paper.

### 1.5 Physical and monetary supply and use tables (SEEA)

SEEA separates flows into natural inputs, products, and residuals; residuals (solid waste, emissions) are
recorded in physical units and flow from the economy to the environment, or between economic units
*(read)* ([SEEA Central Framework, ch. 3](https://unstats.un.org/unsd/statcom/doc12/SEEA%20Central%20Framework%20Ch3.pdf),
paragraphs 3.20 on flows within the economy being products or residuals and flows to the environment being
residuals, 3.64 on physical flow accounts of products being limited to those with positive monetary value,
3.75 and 3.76 below). Paragraph 3.75: where a discarder receives money or other benefits for a discarded
product, it is a transaction in a product, not a residual (3.85 gives scrap metal as the example). Paragraph
3.76: payments by a generator of residuals to establishments that collect, treat or transform them are payments
for services and transactions in products, while the residual flows are recorded separately. So the sign sits
on the service and the payment, not on the residual. [SEEA ch. 2](https://ecosoc.un.org/sites/default/files/documents/2023/SEEA-Central-Framework-Ch2-E.pdf)
was not opened.

What goes wrong: it is an accounting convention, not a price theory. It does tell us the right bookkeeping:
keep the residual in physical units, price the service of handling it.

### 1.6 CGE models with waste and recycling sectors

Typical CGE treatments *(recalled, not read; the search for CGE waste models returned only the WIO papers
above)* either (a) add a waste-collection and treatment industry whose output is a service bought by the
generating industry, so the waste has no negative price but its disposal cost is a positive input cost, or
(b) allow negative prices in a complementarity formulation. What goes wrong: in (a), a by-product that later
becomes useful needs a separate switch because the waste sector and the product market are separate; in (b),
complementarity solvers need a bounding rule.

### 1.7 Life-cycle assessment (ISO 14044)

ISO 14044 gives a hierarchy: avoid allocation by subdividing the process or by system expansion (credit the
co-product for the production it displaces); else allocate by physical relationships; else by economic value
*(read, secondary source)*: [dei.so practitioner article](https://dei.so/what-is-allocation-and-system-expansion-in-life-cycle-assessment-lca/)
citing ISO 14044 clause 4.3.4.2. The standard itself is paywalled and was not opened. The same article gives a
chlor-alkali worked example in which switching from mass to economic allocation moves hydrogen's share of the
burden by a factor of about five to six, so the result depends on the rule. The
[Springer paper](https://link.springer.com/doi/10.1007/s11367-014-0812-4) and the
[greencalculus glossary](https://greencalculus.com/glossary/allocation/) were not opened *(snippet)*.

What goes wrong: allocation is arbitrary (physical vs economic vs energy), and system expansion needs an
assumed displaced product, which is a modelling choice. The useful idea for us: system expansion is
exactly "price the by-product at the cost it saves the user", which the sim can compute because it has
real substitute techniques.

### 1.8 Cost accounting

Accounting offers physical units, sales value at split-off and net realisable value, and a by-product
method that credits the main product with the by-product's net realisable value
(`ECONOMY_MODEL_SURVEY.md` section 6 with its links). All allocation rules are arbitrary for truly joint
processes. Net realisable value goes negative when processing and disposal cost exceed the sale price, which
is the accountant's version of our case.

### 1.9 Markets where a good crosses zero

* Whey: *(read, partly corrected)* Amaral and da Silva, "Whey in the industry: environmental and valorization
  impacts" ([review](https://www.nucleodoconhecimento.com.br/?p=96244)), says that in the past whey was not used
  or only used in animal feed, and that knowledge of its composition and technology made it an ingredient of
  great value for food and pharmaceutical industry; it does not say its past price was negative, so
  "negative-value historically" is not supported there. Acid whey today: *(read)* [Bullvine, 9 June 2026](https://www.thebullvine.com/news/foremost-priced-its-acid-whey-in-2023-most-co-ops-still-havent/)
  says a plant moving one 6,000-gallon tanker a day pays roughly 300 dollars per load, about a nickel a
  gallon, to make it disappear.
* Blast-furnace slag: *(read)* [911 Metallurgist, slag cement](https://www.911metallurgist.com/?p=654964)
  quotes that the first use in cement was "to use an almost worthless and cumbersome by-product as a not readily
  detectable adulterant in Portland cement", and that the adulterated cement was found stronger, with ground
  chilled slag usually improving quality. The article is an old text reproduced; no author or date was shown.
* Coal tar: *(read)* [Scientific American, Toms River excerpt](https://www.scientificamerican.com/article/toms-river-excerpt-on-aniline-dye)
  calls it "arguably the first large-scale industrial waste", a by-product of coal gas and coke, dumped in pits
  or waterways; Perkin found mauve from aniline in 1856. The page does not state the benzene to aniline
  chemistry causal step beyond that. [ChemistryViews](https://chemistryviews.org/?p=72858) returned a server
  error and was not opened *(snippet)*.

In all three the sign flip is caused by a new technique (a user), not by a change in the producer's
process. That the same material can carry both signs in different places at once (transport) is *(recalled)*
general economics, not from these pages.

### 1.10 Agent-based simulators

A recent agent-based model of industrial symbiosis has firms trading by-products in a spatial double
auction, with transport costs, disposal penalties and resource scarcity in each firm's profit, and prices
and quantities emerging from local trades *(read, abstract only)*: Mastio, Saves, Gaudou and Verstaevel, "Adaptive Agents in Spatial Double-Auction
Markets: Modeling the Emergence of Industrial Symbiosis", AAMAS 2026 ([arXiv 2512.17979](https://arxiv.org/abs/2512.17979v1)).
The abstract names reinforcement-learning bidding, transportation costs and disposal penalties; "resource
scarcity" and "profit" are from the first-draft summary and are not in the abstract. A disposal penalty paid when a by-product is not sold is equivalent to a negative seller
reservation price. Most other agent models in this area treat disposal as an exogenous fee *(recalled)*.
What goes wrong: an exogenous fee is a hardcoded outcome by our rule 4.1.

### 1.11 Summary of failure modes

| Tradition | Negative value is | Failure |
|---|---|---|
| von Neumann | never (free disposal, price floor zero) | disposal is free, so hides the cost; without it, no equilibrium guarantee |
| Sraffa | allowed, a formal price | underdetermined or dominated systems; sign flips change technique |
| Baumgartner | context dependent | no algorithm |
| Leontief, WIO | dual of a treatment programme | fixed treatment menu; dual jumps; stocks vs flows |
| SEEA | none; waste is a physical residual | not a price theory |
| CGE | cost of a waste service | by-product turning useful needs a separate switch |
| LCA | credit from displaced product | allocation is a choice |
| Cost accounting | net realisable value | allocation is a choice |
| Agent models | exogenous fee | hardcoded |

## 2. Recommended model for this simulator

### 2.1 Principle

A by-product has no price of its own set by its process. Its price is the larger of two things, both
computed from other prices already in the solve:

    price_of_byproduct = max(
        value_to_best_user_of_byproduct,
        minus_cost_of_cheapest_disposal_of_byproduct)

and the main product carries the rest of the batch:

    price_of_main_product * quantity_of_main_product
        = total_batch_cost - sum over byproducts of (price_of_byproduct * quantity_of_byproduct)

This is the von Neumann rule with free disposal generalised: disposal is available but costs something, so
the zero floor becomes a negative floor. It is also LCA system expansion made computable, because the value
to a user is the cost that user saves.

### 2.2 What makes disposal cost physical

Disposal is not a fee; it is a set of ordinary techniques whose cost the solver already knows how to
compute.

* **A disposal technique is a normal production entry** whose input is the waste material and whose output
  is a service, or nothing but an obligation. Its recipe uses what real disposal uses: labour to load and
  tip, haulage (the freight code in `sim/geography/` already prices moving a kilogram over a route), and
  land (`land_hectare_years` is already a schema field). Examples, as data not engine: heap on spoil land,
  spread on fields, discharge to a watercourse, burn, dump at sea. Each is a recipe with `requires_node`
  where it needs a tool or knowledge.
* **Land is occupied, not consumed.** A heap holds land for as long as it lasts; the cost is land rent times
  the time the heap occupies the tile, so an expanding heap raises its own cost as nearby land is used.
* **Nuisance limit by tile.** Each tile has a carrying capacity per waste class (the amount that can be
  tipped before smell, leachate or fire makes the tile unusable for farming or housing). It is a physical
  stock on the tile, not a number in the price code. When the tile is full the next cheapest disposal is the
  next tile, so the cost rises with haulage; that makes the marginal cost of disposal increasing without
  any special rule.
* **Law or custom as a limit.** A state actor may forbid a technique on a tile class or charge a fee. That
  fee is state revenue and an input to the disposal technique's cost, so it is an actor's choice and not a
  hidden constant, usable by any actor as `CLAUDE.md` section 2 requires.
* **Feedback.** Dumped mass stays on the tile and acts through the existing domain models: fertility for
  spread waste, disease for putrescible waste, water for discharge. The sim then does not need to know that
  disposal is bad, only that a tile holds a stock that other models read. Whether `sim/world/` models can
  read such a stock is unchecked; until they do, the cost alone carries the signal.

### 2.3 How the solver prices it

1. Compute the cost of the cheapest disposal of each material that appears as a joint output, as the
   minimum over disposal techniques of that technique's costed recipe. This uses the same recipe costing
   (`solve_prices_core.py`) and depends on labour, haulage and land prices, not on the batch being split.
   That keeps it out of the feedback loop that the standalone-cost heuristic in `joint_allocation.py` was
   designed to avoid. Where a disposal technique itself has a joint output (burning gives ash), the ash is
   priced by the same rule one level down; the dependency graph of waste classes should be finite and
   acyclic, and a cycle is a data error that `compute_resolvable_materials` already reports for materials.
2. **Free disposal as a bound.** The price of a joint output is bounded below by minus the cheapest disposal
   cost. This replaces the numerical purpose of `JOINT_BYPRODUCT_FLOOR_SHARE`: the iteration cannot decay
   to a denormal because the price of a glut by-product settles at the negative floor, a finite number, not
   at zero. The main product's price is bounded above by the batch cost plus the disposal cost of all
   by-products, per unit, so the damped iteration moves inside a closed bounded box. This is the stability
   argument; confirm it by test (section 5).
3. **Use value.** A material's value to a user comes from two sources already in the codebase: a demand
   anchor (`sim/world/demand.py`), and the cheapest technique that consumes it as an input in place of a
   substitute. The second is system expansion: the value equals the substitute's price minus the extra
   processing cost, floored at the disposal floor. Slag becomes valuable when the slag-cement technique is
   known, because that technique then appears in the solve for that civilisation (`requires_node` gating is
   already how the solver restricts techniques) and its input saving is positive.
4. Active-set rule (von Neumann): a technique that would lose money at the solved prices is not chosen, as
   today. A technique that uses a negative-priced by-product is paid to run (its input has a negative
   price), which is how an abatement or recycling activity becomes viable without a subsidy rule.
5. Zero crossings. Because the price is a max of a use value and a negative floor, it is continuous in the
   use value. A use technique becoming available moves the price from the negative floor to a higher value,
   the behaviour of whey and slag in section 1.9.
6. Retire `lift_to_floor`. Keep `JOINT_BYPRODUCT_FLOOR_SHARE` only until every joint recipe in the data has
   a disposal route; then delete the constant, which shrinks the heuristic burndown
   (`python3 sim/constants.py --burndown`).

### 2.4 The agent economy market

`goods_market.py` clears in log price and so cannot represent a seller paying. Two options:

* **Option A (recommended): disposal is a service market with a positive price.** The waste seller pays a
  gate fee to a disposal operator (a firm or state actor running a disposal technique). The service has a
  positive price and clears in the existing market. The by-product's signed value is accounting: sale price
  minus gate fee. No change to the log-price solver; `MINIMUM_PRICE_SHARE_OF_REFERENCE` can be deleted
  because the token is no longer needed (a seller with a non-positive reservation instead buys a disposal
  service). The operator is an ordinary firm that takes waste in physical units and spends labour, land and
  haulage, so capacity limits and entry fall out of the existing firm model.
* **Option B: allow negative prices in the market.** The search would run on a shifted coordinate (price
  minus lowest reservation, in log), and demand schedules would have to be defined below zero. More
  invasive, since the budget-cap and tier logic assume positive prices. Not recommended first.

A material that gains a use appears as a bid in its own market (the user bids its saving), and the seller
then sells to whichever of the user and the disposal operator is the better counterparty, because both are
in the same set of offers. So the switch from waste to product needs no explicit rule.

A fallback is needed or no seller can ever be rid of a good: a universal low-capability technique (tip on
the nearest tile) that anyone can run with labour and haulage. It must be labelled as a temporary heuristic
(rule 4.4) until each waste class has real data.

### 2.5 Stability notes

* Disposal cost is computed from recipes that do not contain the batch's own joint outputs, so it is a
  constant of the iteration, not part of the fixed point.
* The main product price falls as by-product price rises and rises as it falls, so a damped update with one
  by-product in surplus moves monotonically into a bounded box; with several by-products the update stays
  bounded by the box above. This is an argument, not a proof; test it with the Rome solve and a synthetic
  two-by-product fixture.
* Today an unanchored output takes the standalone cost per kilogram. Under this model an unanchored
  by-product with no user and no demand takes the negative disposal floor, which is physically right:
  nothing wants it. This also resolves the `(*)` flag in `solve_prices.py` (platinum, coal tar and others
  that copy the main product's unit price): those need a use value, which is a data question about what
  consumes them.

## 3. Data needed (in terms of `data/production/_SCHEMA.md`)

No figures are proposed. Every number is to be read from a source and tagged with the existing
`yield_basis` and `conf` fields.

* **Waste class on a material or output:** a field naming the physical class (inert solid, putrescible,
  liquid, hazardous, gas). The class chooses which disposal techniques can handle it. It is a property of
  the material, so it belongs with the material or the output, not the engine.
* **Disposal techniques as production entries:** `inputs`, `labour_hours`, `land_hectare_years`,
  `capital` and `requires_node` cover almost everything. The gap is a way to say the entry consumes a waste
  material and delivers a service or a residual. Either let an entry output a service material
  `disposal_of_<class>` (needs only the new key and its `unit_dimension`) or add an optional `disposes`
  field of {material: quantity}.
* **`disposal_value_hours`:** already exists. Under this model it is redundant for the floor (the floor is
  computed). Keep it only as an author-observed value used as a validation target, or deprecate it; see the
  open questions.
* **Tile stocks:** a tile-level store of deposited mass by waste class, and a per-class capacity before the
  tile is unfit for other use. Capacity is geography and agriculture data with a source.
* **Use technique inputs:** a technique that consumes a by-product uses the existing `inputs` field with a
  `requires_node`. No new field, but the data must exist (slag cement, tar distillation and dyes). Check
  coverage of each example in `data/production/` with `grep` before stage 2.
* **State levy:** an optional per-class fee in a state's policy, expressed as an actor choice.

## 4. Historical examples as distribution checks, not dated targets

Each is a relationship the baseline should show in some runs, never in a given year.

* A heavy by-product of a metal industry (slag) accumulates near the works while no user technique is
  known, and its solved price is negative; once a user technique is in the solve the price rises to at least
  the disposal floor. Check: the by-product's price differs in sign between a solve gated before and after
  the user's `requires_node`.
* A putrescible by-product (whey, spent lees, dung) is negative far from farmland and positive near it where
  a feed or fertiliser use exists. Check: price falls with haulage distance to the nearest user.
* A tar-class by-product (wood or coal tar) is negative or at its floor without a distillation technique and
  higher with one.
* A heap-forming industry (mining spoil, smelter slag) shows disposal as a visible share of that industry's
  cost, rising as tiles near the works fill. The expected range is a distribution to be set from sources.
* The same material carries different signs in different places at one time (seller pays in one region,
  buyer pays in another).
* Rule 4.2: a baseline that reliably flips slag to a product in a particular decade is evidence of
  hardcoding; the flip time should vary across an ensemble because it depends on when the user technique is
  discovered.

## 5. Staged build plan

Each stage follows TDD (section 6 of `CLAUDE.md`): a regression test first showing today's behaviour.

1. **Stage 1, smallest increment: a computed disposal floor in the solver, no market change.**
   * Add one generic disposal technique (tip on land: labour, haulage, land) as data, labelled temporary,
     and compute the cheapest disposal cost for joint outputs.
   * In `allocate_joint_cost`, replace the `lift_to_floor` call with a floor at minus that cost, and let the
     surplus branch return negative prices for a by-product.
   * Tests: (a) a synthetic two-output recipe whose by-product has no anchor gives a by-product price equal
     to minus the disposal cost and a main price that recovers the batch; (b) the Rome solve in
     `test_joint_byproduct_floor` keeps `wood_tar_kg` finite and not a denormal, now negative; (c) batch
     cost is recovered exactly (sum of price times quantity equals total cost); (d) no NaN or denormal
     across a full solve; (e) `python3 sim/simulator.py validate` and a fingerprint comparison; (f) a
     convergence test: the damped iteration reaches the same fixed point from two starting guesses.
2. **Stage 2: use value flips the sign.** Add a user technique for one by-product (slag or tar, whichever
   the data already supports); solve with and without its `requires_node`. Test: negative before, at or above
   the floor after, monotone in the saving. Delete `JOINT_BYPRODUCT_FLOOR_SHARE`.
3. **Stage 3: disposal techniques as a menu per waste class,** cheapest chosen, joint outputs inside a
   disposal technique (ash). Test: a cycle in waste classes is reported.
4. **Stage 4: agent economy.** Disposal operator firms and the gate-fee service market (Option A). Delete
   the token price constant. Tests: a seller with a negative reservation buys the service while the goods
   price stays positive; operator capacity limits volume; a new use bid pulls the by-product off the
   operator.
5. **Stage 5: tile stocks and nuisance.** Deposited mass per tile, capacity, rising marginal cost as tiles
   fill, state levy as an actor choice. Tests: marginal disposal cost rises with deposited mass; a state and
   a firm can both be operator.
6. **Stage 6: feedback into domains** (fertility, health, water), once those models read a tile stock.

## 6. Open questions for the owner

1. Option A (disposal as a positive-price service market) versus Option B (negative prices in the market).
   A is recommended; confirm.
2. Is `disposal_value_hours` kept as an author-observed validation value or deprecated in favour of the
   computed floor?
3. Can a state forbid a disposal technique (a law), and may civilisations differ in what is legal?
4. Who bears disposal cost for a good that becomes waste after use (a worn tool, a dead animal)? This needs
   a rule for consumer waste, not only for joint production.
5. When no disposal technique is known for a class: a universal tip technique (labelled temporary), or
   refuse the recipe until data exists?
6. How should the nuisance limit be sourced (leachate, odour, fire) so it is data, not an engine constant?
7. Several consumers (`priced_goods_table`, national output, freight weight tables) may assume
   nonnegative prices; a sweep for such assumptions is a prerequisite for stage 1. Is a "pay to remove"
   quote acceptable in the player-facing screens?
8. Mod contract: do mods need a way to declare a disposal technique for a new material class?

## Sources

All links appear inline above. Verification pass of 2026-10-06: items marked *(read)* were opened (PDFs
converted to text); *(corrected)* items record where the first draft overstated a source. Still *(recalled)*
or *(snippet)*: Baumgartner and Faber's specific negative-price statement, the Leontief 1970 detail and the
shadow-price reading (Allan et al. and the 1970 paper could not be opened), the Kurz and Salvadori pages (fetch
blocked), the linear-programming claim for Nakamura and Kondo, typical CGE waste sectors, regional sign
differences, the claim about exogenous fees in agent models, the ISO 14044 text itself, and the ChemistryViews
page.
