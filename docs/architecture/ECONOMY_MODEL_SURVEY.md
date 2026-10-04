# Survey: how other models price goods, clear labour and start the world

**Status:** research note, not a plan. Sources are linked inline. Statements
about games marked "(from memory)" were not checked against a source in this
survey. No numbers about this repository are asserted; measure them with the
commands in `CLAUDE.md` §5.

## 0. What we have, in one paragraph

Prices are solved as a damped fixed point over the recipes in
`data/production/` (`sim/engine/solve_prices_core.py`), in labour-hours with the
`labourer` trade as numeraire, plus two rent mechanisms (ore deposits, arable
land). Joint outputs split the shared cost using demand anchors
(`sim/engine/joint_allocation.py`, `sim/world/demand.py`). Labour moves between trades
through a gap-driven, skill-distance-weighted flow (`sim/labour/labour_market.py`,
`sim/labour/labour_allocation.py`): NEED comes from planned output, HAVE from a
workforce that drifts toward the gap. There is no wage bargaining, no
per-trade starting workforce (one temporary heuristic pools non-farm hours
into one trade), and household demand is a separate anchor rather than part of
one clearing loop.

Our constraints, abbreviated: no hardcoded historical outcomes; history is a
plausible draw, not the only path; interventions use the normal rules;
multiple actors; mods add goods, recipes and trades.

## 1. Input-output, labour values, joint production

**How it works.** Leontief: the price of every good equals the cost of its
inputs plus labour plus profit. Written out:
`price_vector = transposed_input_matrix * price_vector + wage * labour_vector + profit`.
With labour only, `price_vector = labour_vector * inverse(identity - transposed_input_matrix)`,
which is exactly the embodied-labour value (Cockshott and Cottrell argue this
is computable at scale and usable for planning:
[Economic planning, computers and labor values](https://users.wfu.edu/cottrell/socialism_book/aer.pdf),
[Towards a New Socialism](https://users.wfu.edu/cottrell/socialism_book/)).
Sraffa's system is the same with a profit rate; joint production makes the
system have more products than processes' worth of equations and can give
negative labour values for some goods
([Cottrell 1996](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-999X.1996.tb00388.x),
[Salvadori, Sraffa and von Neumann](https://www.academia.edu/728236/Sraffa_and_von_Neumann)).
Von Neumann's model resolves the counting problem by choosing which
processes run: the price vector must make no process profitable above the
going rate, and every running process breaks even, with a free good priced at
zero when it is in surplus.

**What it gives us.** This is our current core, so it validates the choice.
The von Neumann move is the useful borrowing: joint outputs are priced by
which processes are active and which goods are in surplus, not by allocating a
cost. A surplus by-product gets a price of zero (or negative, disposal cost)
and the main product carries the process. Choice of technique (already in our
solver) is the same idea.

**What breaks.** Pure labour values ignore scarce land and ore, so they need
the rent terms we already added. Heterogeneous labour needs a reduction to
simple labour (we use wage ratios by trade, which is the standard answer).
Negative values under joint production are a real hazard for us: a fixed point
must be allowed to return a price at or below zero rather than being clamped
into an invented positive.

## 2. Computable general equilibrium

**How it works.** A social accounting matrix (SAM) gives a base year of all
flows; the model is calibrated so the base year is an exact equilibrium, then
shocked. The modeller chooses a closure: which variables are exogenous
(full employment with a flexible wage, or a fixed wage with unemployment,
savings-driven or investment-driven, fixed or floating exchange rate).
Prices come from making excess demand zero in every market, with one price as
numeraire and Walras' law dropping one equation
([CGE overview](https://en.wikipedia.org/wiki/Computable_general_equilibrium),
[Cambridge intro to CGE](https://assets.cambridge.org/97805217/66968/frontmatter/9780521766968_frontmatter.pdf),
[Boston University CGE chapter](https://people.bu.edu/isw/papers/cge_chapter.pdf)).

**What it gives us.** Two things: an explicit list of closure choices (we
currently make them implicitly and per module, which is why wage and price
code disagree about what is exogenous), and a clean way to write household
demand as a budget-share system whose income is the labour and rent
income of the same model, closing the loop between `demand.py` and the solver.

**What breaks.** Calibration to a SAM is exactly what "no hardcoded
outcomes" forbids: the base year is a historical outcome, and the model then
reproduces it by construction. There is no SAM for the ancient world, and
using one would make the baseline the only outcome. Static equilibrium also
has no transition dynamics. Use CGE for its structure (closure, budget
shares, numeraire), not its calibration.

## 3. Agent-based computational economics

**Sugarscape (trade).** Agents with different marginal rates of substitution
trade bilaterally; the trade price is a geometric mean of the two agents'
rates, and prices drift toward a common value with falling variance with no
auctioneer ([Epstein and Axtell summary](https://en.wikipedia.org/wiki/Sugarscape),
[book entry](https://mitpress.mit.edu/9780262550253/growing-artificial-societies/)).
Gives: prices from local exchange, wealth inequality, carrying capacity from
geography. Breaks: no production side, one or two goods; not a recipe graph.

**Gintis' Walrasian ABM.** Prices are each agent's private information and
are adjusted by agents themselves; imitation of successful agents
(a replicator dynamic) makes a system that is unstable under public-price
tatonnement converge
([Gintis 2007, Economic Journal](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0297.2007.02083.x),
[paper](https://www.umass.edu/preferen/gintis/General%20Equilibrium.pdf)).
Gives: the finding that tatonnement's instability comes from all agents seeing
and reacting to one price. Our global damped fixed point is a public-price
loop. Breaks: multi-sector but stylised, and convergence needs many agents.

**Lengnick baseline.** Households and firms only. Monthly: firms adjust wage
and price and headcount from their own inventory and vacancy signals;
households search a small set of shops and jobs; runs a long burn-in to
remove arbitrary starting conditions. Reproduces a Phillips curve, a
Beveridge curve and a right-skewed firm size distribution
([Lengnick 2013](https://www.sciencedirect.com/science/article/abs/pii/S0167268112002806),
[working paper PDF](https://www.econstor.eu/bitstream/10419/45012/1/654079951.pdf),
[summary](https://sim4edu.com/sims/20/description)).
Gives: the minimal loop we need for wages and prices: a firm raises its wage
when it has unfilled vacancies and lowers it when it is fully staffed with
spare applicants; raises its price when its stock runs out and lowers it when
stock piles up. Every rule is local and uses only the firm's own state.
Breaks: one consumption good and no intermediate goods.

**EURACE.** Full macro ABM with capital goods, consumer goods, banks, a labour
market and regions, run on a parallel framework
([Deissenberg et al.](https://www.sciencedirect.com/science/article/abs/pii/S0096300308003019),
[Eurace@Unibi model](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/eurace-unibi-model-2011-v1.pdf)).
Wage is a weighted average of a common wage and a firm-specific term that
depends on productivity and the tightness the firm has experienced; workers
have general and specific skills and apply where their wage expectation is
met ([wage-setting study](https://link.springer.com/chapter/10.1007/978-3-030-52970-3_9)).
Gives: skill-specific matching and the tightness-to-wage rule, close to what
we need for trades. Breaks: heavy, and it assumes a modern institutional set
(banks, unions).

**Axtell firm model.** Agents choose effort and can join or found firms; with
increasing returns to team production, firm size becomes power-law distributed
([Axtell, Brookings](https://www.brookings.edu/articles/the-emergence-of-firms-in-a-population-of-agents-local-increasing-returns-unstable-nash-equilibria-and-power-law-size-distributions/)).
Gives: a way for workshops to appear and vanish endogenously rather than being
authored, and a validation target that is a distribution, matching
`CLAUDE.md` §3.2. Breaks: needs a per-agent utility over leisure and income,
which is a large addition.

**Santa Fe artificial stock market.** Agents with evolving forecast rules
produce two regimes depending on how fast they learn: near rational-expectations
or bubbly and volatile
([Arthur et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2252),
[LeBaron on building it](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/blake.sfisum.pdf)).
Relevance for us is low (financial assets), but the lesson is that learning
speed is an outcome-sensitive parameter and should be labelled as such.

**Tatonnement versus search and matching.** Tatonnement needs a central
auctioneer and one price. Search and matching (Lengnick, EURACE, Sugarscape)
needs only local contact and stocks. Decentralised trade is the natural fit
for several actors, distance and transport cost, which is our multi-actor
requirement.

## 4. Labour-market models

**Search and matching (Diamond, Mortensen, Pissarides).** Vacancies and job
seekers meet through a matching function; tightness is
`tightness = vacancies / job_seekers`; the job-finding rate rises with
tightness; the wage is set by Nash bargaining so that the worker takes a
constant share of the match surplus, which makes wages rise with tightness
([Nobel advanced information](https://www.nobelprize.org/uploads/2018/06/advanced-economicsciences2010.pdf),
[Yashiv review](https://docs.iza.org/dp2743.pdf),
[DMP lecture notes](https://perso.univ-lemans.fr/~acheron/cours/M1_partie1.pdf)).
In words:
`wage = worker_share * (output_value_of_worker + hiring_cost_saved) + (1 - worker_share) * unemployment_income_or_subsistence`.

**Occupational choice.** Each worker compares expected income (wage times
probability of finding work) across trades net of a switching cost that depends
on skill distance, and moves stochastically (Roy-style choice). Our
`labour_market.Workforce` already has the skill-distance flow; what it lacks
is a wage signal to flow toward.

**What it gives us.** A wage per trade that comes from tightness rather than
from a static table, and a principled reason for unemployment and slow
adjustment (the friction is the matching, not an invented mobility constant).
The worker's outside option in a pre-industrial world is subsistence farming,
which gives a natural floor tied to our agriculture module: the floor is the
labour-hours needed to produce the household's food from land the household
can access.

**What breaks.** Nash bargaining share is a free parameter that is hard to
justify per civilisation; treat it as a labelled heuristic
(`CLAUDE.md` §3.4). Unfree labour (slaves, serfs, conscripts) is not a
bargained wage at all and needs its own rule set by the institution, not a
special case in the wage code.

## 5. Games

Sourced items first, the rest from memory and unchecked.

**Victoria 3.** Buildings employ pops; each building has a wage level it
adjusts over time from profitability, labour need and cash reserves; it
raises the wage if it cannot fill its hiring quota. Each week all buy and sell
orders in a market are matched, prices move within a band around a base price
when demand exceeds supply, and buildings that cannot pay drop out
([dev diary 57](https://www.paradoxinteractive.com/games/victoria-3/news/dev-diary-57-the-journey-so-far),
[Game Developer deep dive](https://www.gamedeveloper.com/design/deep-dive-modeling-the-global-economy-in-victoria-3),
[Dragon Tributary analysis](https://riverlimburg.substack.com/p/exploring-the-economic-engine-of)).
The designer's own description is a snapshot: "turn the taps on full blast" and
assign prices from the resulting quantities, then let stocks be
abstracted. Gives: a proven, cheap, multi-actor-friendly loop (per-building
wage adjustment plus per-market order matching) and the base-price-with-band
trick that keeps prices bounded. Breaks: the base price is authored per good
(exactly our `prices.json` problem) and starting pops, buildings and wealth
are authored per country. It is the best model for structure and the worst
for the no-hardcoding rule.

**Eco and EVE Online.** Both are real player economies: prices come from
posted orders, region-local markets, no central price
([Eco economy wiki](https://wiki.play.eco/en/Economy),
[Eco design news](https://www.moddb.com/games/eco-global-survival-game/news/how-the-player-run-economy-works-in-eco-75-funded-on-kickstarter),
[EVE economy overview](https://050nor.substack.com/p/eve-online-economic-system-design-player-motication-emotion)).
Eco has no default currency; one emerges and governments choose a tax
currency. Relevance: order books and regional markets are the natural way to
let countries be players later; the lesson from EVE is that regional markets
plus transport cost yield price differences without extra rules.

**Dwarf Fortress.** World generation simulates centuries of coarse history
(civilisations, sites, populations, events) and the game starts from that
record ([wiki](https://www.dwarffortresswiki.org/index.php/World_generation),
[advanced worldgen](https://dwarffortresswiki.org/index.php/DF2014:Advanced_world_generation)).
Its trade values are fixed per material and craft quality, not solved, so the
economy is a value table with production on top. Gives: the spin-up pattern for
starting conditions (section 7).

**From memory, unchecked.** Factorio and Satisfactory are pure recipe graphs
with no prices; useful only as evidence that a recipe graph plus rates
(items per minute) is a complete production description, and their ratio
calculators are the same linear algebra as our solve. Anno chains goods to
population tiers whose needs unlock more building types; consumption is
per-need saturation and there is no wage market. Patrician and Caesar/Pharaoh
use per-town price curves that move with stock and consumption, authored per
good. X4 has station-level order books with prices set by stock level against
target stock. Rimworld sets item value from material market value times
quality, with fixed base values. Settlers uses fixed logistic chains without
prices. Oxygen Not Included and Kenshi have no real price mechanism beyond
a value per item. Victoria 2 used a supply and demand price per good with an
authored base price, and its pops changed occupation by promotion and
demotion rules based on employment, which is a crude version of occupational
choice.

## 6. Joint products in accounting and economics

Accounting offers three splits: physical units (by mass or volume), sales
value at split-off, and net realisable value (sales price less further
processing cost), plus the by-product method that subtracts a minor product's
net realisable value from the main product's cost
([Horngren chapter](https://nscpolteksby.ac.id/ebook/files/Ebook/Accounting/Cost%20Accounting%20(2012)/Chapter16%20-%20Cost%20Allocation%20Joint%20Products%20and%20Byproducts.pdf),
[CSUN guide](http://www.csun.edu/~hcbus012/acct380/guides/chapter07.doc)).
Accounting texts say any allocation is arbitrary. Economists agree in a sharper
form: with a truly joint process there is no cost per output to find; the
process has one cost, and the outputs' prices are fixed by demand. The
textbook treatment is marginal: price each output so that revenue from all
outputs covers the joint cost, with each output's price set by its own demand;
if one output is in surplus its price falls to its disposal value (Marshall's
joint supply; the same result as the von Neumann free-good rule in section 1).

Relevance to our design: `engine/joint_allocation.py` already follows the economist's
view (demand anchors set the split, standalone cost for outputs with no
anchor). Its weak points are physical-units fallbacks (`mass_in_kg` treats
non-gram units as kilograms) and the single hand-set income scale. The
economically correct improvements are: let the process's active set be
decided by which outputs have positive net demand (von Neumann), allow a
by-product price to fall to its disposal or reuse value, and derive the income
scale from the labour market rather than one constant.

## 7. Starting conditions: authored versus simulated history

Authored (Victoria 3, Anno scenarios, most grand strategy): fast, predictable,
easy to test, but each starting state is a hardcoded outcome and adding a
country or a mod means adding data by hand. It is exactly what
`CLAUDE.md` §3.1 forbids for workforce shares, city sizes and wages.

Spin-up (Dwarf Fortress worldgen; the burn-in in Lengnick's runs,
[Lengnick](https://www.econstor.eu/bitstream/10419/45012/1/654079951.pdf);
the initialisation discussion in
[Dawid and Delli Gatti's ABM review](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3112074)):
start from allowed inputs (geography, population, known technologies,
open deposits), run the model with no player for a burn-in period, and start
play from the result. It produces a workforce in equilibrium with the
recipes, land and demand of that civilisation, and it works for a mod that
adds a trade or a good with no extra data. Cost: the start is only as good as
the model, the run costs time at load (cache it per civilisation and seed),
and a bad model gives a bad start. There is also a subtlety: a burn-in
produces a steady state, while real civilisations were on a trajectory; the
burn-in should therefore be run with the known technology set and slow
demographic change, and then validated against distributions (urban share, farm
share, wage-to-grain ratio), never against dates.

Middle path (recommended below): author only physical inputs and one seed
workforce (people, land, tools, tech), and let the labour market and price
solver produce the per-trade split.

## 8. Ranked recommendations, mapped to modules

1. **Keep the labour-hour fixed point for prices; change how it treats joint
   outputs and surpluses** (`engine/solve_prices_core.py`, `engine/joint_allocation.py`).
   Adopt von Neumann activity choice: a process runs only if it is not
   loss-making at the solved prices; an output in surplus prices to disposal
   value, including zero; do not clamp the solver into positive prices.
   Keep demand anchors for the split, but drop the mass fallback where
   a unit conversion exists. Rejected: SAM calibration (fails §3.1).
2. **Wages from tightness, per trade** (`labour_market.py`, new wage field on
   the workforce state). Use the Lengnick and EURACE local rule, which is
   cheaper than full DMP: `wage_next = wage * (1 + adjustment_rate * (vacancies - unfilled_applicants) / employed)`,
   with the floor set by the worker's outside option, the labour-hours to
   grow their own food. Feed the resulting relative wages back to the price
   solver as the trade weights it already accepts
   (`wage_ratios_by_trade`), so the solver and the market share one wage
   vector. Label `adjustment_rate` as a temporary heuristic.
   Add a DMP-style matching friction only if unemployment dynamics matter.
3. **Starting workforce per trade: spin up, do not author** (new burn-in
   step; `labour_allocation.py`, replace the pooled `artisan` heuristic).
   Seed with total population, land, tools and known technologies; run the
   labour and price loop with a fixed demand structure until the trade
   split is stable; cache per civilisation and seed; validate as
   distributions (farm share, urban share, wage-to-grain ratio). Interventions
   and mods then change inputs and re-spin instead of needing authored
   shares. This also answers §3.2: different seeds give an ensemble.
4. **Close the loop with CGE-style closure and budget shares** (`demand.py`).
   Household income becomes the wage bill plus rents from the same run,
   replacing the single household income constant in `engine/joint_allocation.py`.
   Write the closure (numeraire, what is exogenous, subsistence floor) in one
   place so every domain reads the same one.
5. **Decentralise clearing for multiple actors** (later, when countries become
   players). Region-local markets with order matching and transport cost,
   EVE and Victoria 3 style, on top of the same solved cost as a reference
   price: the solved price becomes a firm's expected cost and a starting
   quote, not the trade price. This is the Gintis result applied: private,
   locally adjusted prices avoid the instability of one public price.
6. **Endogenous workshops** (optional, after 2 and 3). Axtell-style entry and
   exit of producers, so the number of smiths is an outcome; validate on
   firm-size distributions.

## 9. Things not to borrow

- Victoria 3's authored base price per good and authored starting pops.
- CGE base-year calibration and any "shock relative to history" framing.
- Any curve tuned so the output matches a known historical price; the
  existing rule in `data/production/_SCHEMA.md` applies to coefficients too.
- Unlabelled learning or adjustment rates in agent rules; tag them per
  `CLAUDE.md` §3.4.
