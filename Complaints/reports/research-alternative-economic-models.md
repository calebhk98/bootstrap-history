# Alternative economic models, and a proposed input-output plus shadow-price architecture

Research report for the owner. It builds on, and does not repeat, `Complaints/reports/research-reference-economy-models.md`
(Capitalism Lab, Eurace@Unibi, Econ-ARK HARK, Caiani et al. 2016), `Complaints/reports/research-agent-based-economy-design.md`
(Lengnick, Caiani, Wiese, Peters, Lavoie) and `docs/architecture/ECONOMY_MODEL_SURVEY.md` (input-output, CGE, agent-based,
games). No code was changed.

## Sourcing key

- OPENED: I fetched the page in this session and read what it returned. The URL is given.
- SNIPPET ONLY: seen only in a web search result summary. Treat as unverified.
- NO SOURCE FOUND: I looked and found nothing for the name; I do not guess what it is.
- "Reading" marks my inference, not a claim by the source.
- Repo claims were measured on branch `research-alternative-economic-models` (from `section5-bugs-and-eurace-review`) with
  the command shown. The Eurace clone is the scratchpad one named in the task.
- GitHub's API (`gh`) was refused in this session, so I have repository dates only where a page showed them. Most
  repository pages I opened did not show a release or commit date; "maintained" below is a reading from the page
  (open issues, commit counts, a recent copyright year), never a confirmed date.
- No figure below is recalled from memory. Names of models that I could not open are listed at the end.

---

## Per-model notes

Each note: what it is, language, licence, maintained, then the mechanism tied to a problem here or "nothing applicable".

### BeforeIT.jl (OPENED, https://github.com/bancaditalia/BeforeIT.jl)
Behavioural agent-based macro forecasting package from the Bank of Italy, built on the model of Poledna et al. Julia,
Apache-2.0. Appears maintained (many commits; releases list empty, no dates shown). Built from `parameters` and
`initial_conditions`, run for a number of quarters, with an Austria and an Italy parametrisation and counterfactual scenarios.
The page does not describe a shock mechanism or the model's rules. Mechanism: the initial conditions come from national
accounts and input-output tables (SNIPPET ONLY, https://pure.iiasa.ac.at/18339/1/1-s2.0-S0014292122001891-main%20%281%29.pdf
via search), so the opening is calibrated to a data stationary state. This is the same idea Caiani et al. give for
Complaint 473 and `opening_runs`, with nothing new. Nothing applicable beyond that: its sectors are modern national-accounts
categories (Reading: they cannot be reused for a tenth-century opening without authoring the data, which is the job
`data/production/` already does).

### K+S, Keynes plus Schumpeter (Dosi, Fagiolo, Roventini 2010) (SNIPPET ONLY, https://econpapers.repec.org/RePEc:eee:dyncon:v:34:y:2010:i:9:p:1748-1767)
Agent-based model joining Keynesian demand with Schumpeterian technology-driven growth; the abstract finds complementarities
between demand drivers and technological change. Language and licence: no source found (the earlier report also could
not open the paper, `research-agent-based-economy-design.md` section 1.7). A COMSES catalogue entry exists
(https://catalog.comses.net/publications/1770, SNIPPET ONLY). Mechanism that could matter: firm research and development
and imitation draws that move a capital-goods producer's productivity, and the demand-technology feedback. Tie: the
tech-adoption side of the founder's bootstrapping, not Complaint 473 (the opening). No complaint is open for it that I could
tie it to; nothing applicable to the spin-up.

### JMAB (Caiani, Godin) (OPENED, https://github.com/S120/jmab)
Java framework for stock-flow consistent agent-based macro models, configured through a Spring beans file. MIT-style text with
copyright 2016; Java 6 or later. Last updated September 2018 per a search summary (SNIPPET ONLY), so effectively
unmaintained. The README names no agents or markets. The benchmark model it runs is Caiani et al. 2016, which the earlier
report already read (stationary state solved before the run, section 4 of that report). Nothing new; as a library, nothing
applicable (Java, and the repo has its own engine).

### CATS and BAM (Delli Gatti, Gallegati and co-authors) (SNIPPET ONLY, https://exploring-economics.org/pl/study/books/macroeconomics-from-the-bottom-up, https://www.jasss.org/14/4/reviews/8.html)
CATS means Complex AdapTive Systems; BAM is Bottom-up Adaptive Macroeconomics, the book's basic model with a credit market
where firms borrow when their resources fall short. Code and licence: no source found. The earlier report records the
"bankruptcy avalanche when leverage is high" finding as a snippet. Mechanism: a financial accelerator with a credit network
(Reading: relevant to Complaint 641, lenders ask nothing for default, as an example of leverage-dependent lending, which
Caiani et al. already supply and the earlier report already opened). Nothing new.

### Mark-0 and Mark-I (Gualdi, Tarzia, Zamponi, Bouchaud) (OPENED abstract, https://arxiv.org/abs/1307.5319)
Paper studies the phase diagram of simple macro agent-based models, starting from Delli Gatti's "Mark I". Finds a
transition between a low-unemployment and a high-unemployment state, generically driven by an asymmetry between firms'
hiring and firing rates; a bankruptcy threshold adds endogenous crises. The abstract does not mention "Mark-0"; I could not
tell whether it means this paper's model or another (the Peters et al. paper, https://arxiv.org/abs/2205.00752, was opened
and does not mention Mark-0 either: it calls its model unnamed; the earlier report cites it as "Mak(h)ro 0").
Mechanism that could matter: hiring versus firing asymmetry as the source of a bad state, tied to Complaint 473's
unemployment and unsold-hours behaviour in the spin-up (the earlier design report item (d), hours unhired). The method
(map the phase diagram of the parameters, then place the opening on the good side) is a way to show the opening is not a
point on a cycle, not an engine feature. No code or licence found.

### Lagom generiC (Mandel, Jaeger, Fuerst and co-authors) (SNIPPET ONLY, https://globalclimateforum.org/2010/03/17/release-of-lagom-generic-2-0-an-agent-based-model-of-growing-economies/)
Prototype agent-based model of disaggregated growing economies with capital accumulation, building on Gintis' work on the
dynamics of general equilibrium; a three-sector German application is mentioned. Release 2.0 was in 2010; nothing newer
turned up, so likely unmaintained. Licence and language: no source found. Mechanism: agents that adjust prices
themselves with a general-equilibrium structure underneath (the Gintis line the earlier survey already covers in
`ECONOMY_MODEL_SURVEY.md` section 3). Nothing new.

### abcEconomics, ABCE (OPENED, https://abce.readthedocs.io/en/master/)
Python platform for agent-based trade and production models. Goods are physical objects: a transfer moves the good and the
giver no longer has it. Firm and Household archetypes, parallel execution, accounting in a separate package (abcFinance).
Licence: not stated on the page. Maintained: the page shows only a 2017 copyright; an organisation page exists at
https://github.com/ab-ce (SNIPPET ONLY). Mechanism: conservation by construction (a good cannot be created by a transfer).
Reading: this repo already has that through its ledger and settlement; nothing applicable. It states nothing on price
formation.

### sfctools (SNIPPET ONLY, https://pypi.org/project/sfctools; the PyPI page itself would not load)
Python toolbox for stock-flow consistent agent-based macro models from the German Aerospace Center (DLR): agents, a world
registry, balance sheets that enforce stock-flow consistency, a graphical interface. MIT licence, published in the Journal of
Open Source Software 2023 per the search summary. Appears maintained (releases through a late version). Mechanism: a
balance-sheet class that refuses unbalanced bookings. Tie: the repo's existing money and settlement checks (see the
one-owner-per-fact walls); a stock-flow consistency check at every transaction is a test idea, not a new mechanism.
Nothing applicable to a named complaint.

### AgentPy (OPENED, https://agentpy.readthedocs.io/en/latest/)
Python library for building and analysing agent-based models. Licence not named on the page. Latest changelog entry is
from December 2021, so likely unmaintained. A generic framework: nothing applicable (this repo has its own engine).

### Mesa (OPENED, https://github.com/projectmesa/mesa)
Python library for agent-based models, Apache-2.0, actively maintained by the page's signs (Mesa 3 stable, Mesa 4 in
pre-release, open issues and pull requests). A framework with visualisation; nothing applicable: the repo's engine is
already past the stage where a framework helps, and `sim/` forbids new loose scripts. Its experiment and batch tooling
could inform how the repo runs ensembles (CLAUDE.md 4.2) but I did not open that documentation.

### Agents.jl (OPENED, https://github.com/JuliaDynamics/Agents.jl)
Pure Julia agent-based framework, MIT, apparently maintained. Supports discrete-time and event-queue continuous-time
simulation, and spaces built from OpenStreetMap data. Julia is a language this repo does not use; nothing applicable.

### ACCEPTS (NO SOURCE FOUND)
Two searches returned nothing named ACCEPTS. Ambiguous; I do not guess. The closest unrelated hit was SABCEMM
(https://arxiv.org/abs/1801.01811, SNIPPET ONLY), a financial market simulator, which I do not claim is the intended one.

### ARIO and BoARIO (OPENED, https://spjuhel.github.io/BoARIO/boario-math.html and https://github.com/spjuhel/BoARIO/)
ARIO is the Adaptive Regional Input-Output model; BoARIO is its Python implementation, GPL-3.0, developed in a PhD
project in free time, with open issues and a build badge (so informal but alive). The model starts from a multi-regional
input-output table in equilibrium, each industry holding input stock for a set number of days, and applies shocks: a direct
cut in capacity, or loss of productive capital that must be rebuilt. When demand exceeds production, orders are rationed
proportionally; inventories buffer unfilled orders; capacity can rise above base when unmet demand is positive ("overproduction");
destroyed capital adds rebuilding demand. The page states that prices and the demand-side macro feedback are not
covered there (a separate monetary-factors page exists, not opened), and says nothing on stock-flow consistency.
Mechanisms that could matter: (a) the proportional rationing plus input stock buffer as a way a missing input cuts a
recipe's run by the share it is short, not to zero; this ties to CLAUDE.md section 5 ("a shortage of one input must not
silently stop everything"), and to the unmet-orders handling that the repo already has in settlement (I did not measure
it); (b) rebuilding demand after a loss, which is a shock test for the repo's investment rule
(`producers_close._investment`). It cannot serve as a price owner: it fixes final demand and does not model prices on the
page I read. Not usable for our opening (modern multi-regional tables), usable as a pattern for shock tests.

### ColonD (NO SOURCE FOUND)
One search returned nothing named ColonD. Ambiguous; I do not guess.

### GAMA Platform (OPENED, https://github.com/gama-platform/gama)
Open-source modelling and simulation environment for spatially explicit agent-based simulation, GPL-3.0, modelling language
GAML, Java and Eclipse based, extensions for shapefile and OSM data, apparently actively developed. A GIS-first framework.
Nothing applicable: the repo's map (`sim/geography/`) is its own and the engine is Python; GAMA offers a visualiser at most.

### CGE models: GTAP, MPSGE, Envisage, GEMPACK (SNIPPET ONLY for all; the web summary is https://en.wikipedia.org/wiki/GTAP, https://gtap.agecon.purdue.edu/models/envisage.aspx, https://gams.com/53/docs/UG_MPSGE_Intro.html)
GTAP is a multiregion, multisector CGE model and database coordinated at Purdue; the standard model is implemented in
GEMPACK (Monash) and also in GAMS; Envisage is a recursive-dynamic CGE model first built at the World Bank for climate
questions; MPSGE is a GAMS subsystem for general equilibrium on nested constant-elasticity production and utility functions,
reducing to mixed complementarity problems, with a JuMP-based port MPSGE.jl under development. Licences: no source
found. Mechanism: the base year is calibrated to be an exact equilibrium and then shocked, with a closure choice;
prices come from zero excess demand with a numeraire. `ECONOMY_MODEL_SURVEY.md` section 2 already covers CGE and rates
it as fitting poorly (a calibrated base year does not exist for an opening that is itself a model output). Nothing new.

### HABITAT and IIASA models, MESSAGEix (MESSAGEix OPENED, https://github.com/iiasa/message_ix; HABITAT NO SOURCE FOUND)
MESSAGEix is a linear programming model framework for strategic energy planning and integrated assessment, a GAMS core with a
Python package and an R interface, Apache-2.0, maintained by the page's signs (copyright through 2026, many commits), and it
can link to the MACRO general equilibrium model to feed prices back to demand. The page does not mention dual prices.
HABITAT: searching returned nothing under that name (only the MESSAGEix-GLOBIOM combination); ambiguous, not guessed.
Mechanism: a cost-minimising dispatch over a technology list with vintages and capacity, solved as an LP, and a
price-demand iteration with a macro model. Tie: only as the cost-minimising choice of technique, which the repo's
`opening_runs.choose_recipes` already does with a ranking (see below). Nothing else applicable.

### 1:1 synthetic firm networks, Poledna and CSH Vienna
The Poledna forecasting model is OPENED only as a search result summary (SNIPPET ONLY, https://irihs.ihs.ac.at/id/eprint/6453/):
an agent-based model of a small open economy at 1:1 scale with sectors, input-output and financial links, calibrated from
national accounts, input-output tables and business demography; it claims forecasting competitive with VAR and DSGE. A
related CSH Vienna line builds a firm-level production network of a whole country from VAT data
(https://link.springer.com/10.1038/s41598-022-11522-z, SNIPPET ONLY); I could not confirm that Poledna is an author of
that paper, and I found no 1:1 synthetic-network paper under his name. Both depend on modern administrative micro data, which
does not exist for a tenth-century opening. Mechanism: one agent per real firm, which this repo cannot calibrate. Nothing
applicable to the opening; the idea of reporting indirect losses by tracing a firm's removal through the network is a
possible check for the bankruptcy-cascade question the proposal raises.

### PyPSA (OPENED, https://github.com/PyPSA/PyPSA)
Python framework for optimising and simulating power and energy systems, MIT code licence, solvers HiGHS (default), GLPK,
CBC, Gurobi, Xpress; many commits, appears maintained. The pages I opened did not describe how marginal prices are
exposed (the repository page names `marginal_cost` and `n.statistics()`; the documentation front page did not mention
marginal prices). I therefore cannot cite that PyPSA returns nodal shadow prices; Reading: it is a standard property of
network LPs, but not verified here. Mechanism that fits: a network of buses and links with capacities, balance at each node,
solved as a linear programme. Tie: the proposal's step two. It is built for electricity (a single homogeneous commodity per
carrier), not for hundreds of goods with recipe vectors, so it would be a misfit as a dependency; the equivalent
for our case is a small linear programme written in whatever solver the repo accepts as a dependency (the repo's
`requirements.txt` lists numpy only, measured with `grep -n -i 'scipy\|numpy' requirements.txt`).

### Calliope (OPENED, https://github.com/calliope-project/calliope)
Python multi-scale energy systems modelling framework (Pyomo based, YAML and CSV model definitions), Apache-2.0, appears
active. Spatial and temporal resolution, many runs from one base model. Mechanism: data-defined technologies and
locations kept apart from the framework code. That is already this repo's approach (data in `data/`, engine without content
ids, CLAUDE.md 4.7). Nothing applicable.

### SpineOpt (OPENED, https://github.com/spine-tools/SpineOpt.jl)
Julia framework for multi-energy systems; GPL-3.0 and LGPL-3.0 are listed and the README states LGPL-3.0 or later; EU
funded project through 2026 per the page; appears maintained. Energy-only; nothing applicable.

### JuMP (OPENED, https://jump.dev/JuMP.jl/stable/manual/solutions/)
Julia modelling language for mathematical optimisation. Its manual states how dual values are read (`dual`,
`shadow_price`, `reduced_cost`) and notes that duals are available only if the solver returns them. Licence not stated on
the page I opened. Julia, so not a dependency candidate; useful as the statement of what a dual is.

---

## Evaluation of the proposed architecture

The proposal has three parts: (1) a spatial input-output hypergraph of physical recipe vectors, location nodes with
endowments and transport edges; (2) before agents trade, a linear or convex feasibility and shadow-price pass whose
duals give each commodity's marginal value at each node as the starting economy; (3) dynamic shocks on top (a new recipe or
mine, a gold injection with stock-flow consistency and mass balance, a Cantillon effect along trade routes). It also
claims Eurace@Unibi hardcodes modern sectors.

### What the repo already has (measured)

| Proposal part | In the repo | Evidence |
|---|---|---|
| Recipe vectors | Yes. Each production method has inputs, outputs, labour hours by trade, heat, work, plant goods and life, yields | `data/production/_SCHEMA.md` (fields table); `data/production/*.json` |
| Joint production, rents, technique choice | Yes, in the solver | `sim/prices/solve_prices.py`; `docs/architecture/ECONOMY_MODEL_SURVEY.md` section 1 |
| Nodes with endowments | Yes. Tiles with soils, climate, deposits and a provisions layer | `sim/geography/` (resources_endowment.py, food_land.py and others) |
| Transport edges with distance and terrain | Yes. Freight cost from a carrier's feed, crew, capital and return leg, per tonne-km, by mode | `sim/geography/freight_cost.py`, `cargo_cost.py`, `carriage_reach.py` |
| A stationary input-output pass over final demand by tile | Yes. `opening_runs.choose_recipes` solves the runs that meet final demand (x equals matrix times x plus demand) and ranks recipes by cost, and `opening_stationary.solve` returns runs, hours by trade, wage bill and incomes | `sim/economy/opening_runs.py`, `sim/economy/opening_stationary.py` (module docstring); called from `sim/economy/opening.py` around lines 105 to 134 |
| Cost-price dual | Yes, as cost-of-making fixed point | `sim/economy/unit_cost.py` (named in the stationary module docstring), `sim/prices/` |
| Shocks that reallocate capital and bankrupt producers | Yes, as agent-economy rules: entry and exit on expected sales and loss years, investment | `Complaints/473` line about `LOSS_YEARS_BEFORE_EXIT`; `sim/economy/producers_close.py` |
| Money injection raising prices | Partly. A coin-metal money with mint and a price-level test existed ("more metal raises the price level"), now drowned by the unsettled economy | `Complaints/473` Finding, and the restored slow-only baseline validation naming 473 |

### What it lacks

1. **A global feasibility or shadow-price pass over the spatial network.** `opening_runs.choose_recipes` handles the
   recipe system by an input-output solve and ranking with ceilings, but trade between tiles is not solved jointly as a
   network problem: no transport-aware linear programme returns a marginal value of each good at each tile (the route
   prices are applied afterwards by carriers and merchants). I measured this by reading the module docstrings, not by
   running anything; `grep -rn "linprog\|scipy" sim --include=*.py` finds scipy only in the map layer build
   (`sim/geography/layer_build/sea_links.py`: ndimage and graph routines) and no linear-programme call; `requirements.txt` lists numpy only.
2. **A dependency for linear programmes.** None. Adding one is an owner decision.
3. **Spatial Cantillon spreading as an explicit check.** There is a price-level test, but no test that a gold
   injection at one tile raises prices there before it raises them elsewhere.

### Where the proposal conflicts with CLAUDE.md or the 507 decision

- **507 (one price owner).** `Complaints/507` and `docs/architecture/ONE_PRICE_OWNER_PLAN.md` decide that the agent economy
  owns prices and traded volumes and the solver is a cost-of-making calculator, "used for entry decisions, quotes and the
  opening's seed prices". Part (2) of the proposal makes a solver's duals the starting economy. Whether that conflicts depends
  on one word: the plan already allows the calculator to seed the opening, but the plan's stage 2 seeds with the
  *cost of making at the economy's own wages*, which is a cost-price dual of a system without a demand side. A shadow price
  from a feasibility pass with scarce endowments and fixed final demand is a *scarcity* price, which includes a demand-side
  rent. That is exactly the "demand" job the plan removes from the solver (the plan's section 1, jobs 2 and 3: demand and rent).
  So a shadow-price pass as the source of opening prices re-creates the second price owner; it is the very seam
  507 closes. As a seed that the agent economy then overwrites in the first trading round, it is tolerable only if
  nothing reads it afterwards.
- **"Calculated, not looked up" (CLAUDE.md 4.5).** Shadow prices are calculated, from physical vectors, endowments and a
  stated final demand, so they pass the letter of 4.5. Two cautions. The final demand that feeds them must itself be a
  derived basket (the repo's `opening_basket`) or the dual inherits a looked-up input. And the marginal value of a good that
  is in surplus is zero, which CLAUDE.md section 5 forbids as an in-band "none"; the pass would return a price of "no
  scarcity" that a caller must read as `None`, not free.
- **4.1 and 4.2.** A solved optimum is a planner's equilibrium. Using it as the opening's starting price biases the baseline
  toward a market-clearing outcome, which is the cobweb problem of Complaint 473 in reverse (the opening would be too settled
  to show the real instability the agent economy produces). Section 4.2 says the real trajectory should be a plausible
  draw from an ensemble, and a deterministic dual always lies in one point.
- **4.7.** No conflict: recipes and tiles are data.
- **Dependency and size rules.** Julia (JuMP, BeforeIT.jl, MPSGE.jl) and the energy frameworks (PyPSA, Calliope, SpineOpt)
  are outside the project's Python-with-numpy stack; none of them represents hundreds of goods with joint production
  and per-tile endowments.

### The Eurace claim, checked against the clone

Clone: `/tmp/claude-0/-home-user-bootstrap-history/5d7f8e03-7271-5935-85ab-84cd283dc951/scratchpad/eurace`.
Commands run there:

- `grep -rn -i -E 'sector|industr|good_type|goods_type|homogeneous|single (type|good)' --include=*.xml --include=*.md --include=*.c --include=*.h .`
  (excluding unit tests and the public-sector role names) returned no list of sectors or goods.
- The model definition files list agent types (consumption goods firms, an investment goods firm, banks, central bank,
  government, a clearing house, malls, households) and the variable list for malls describes one offered good per firm
  with price and quality (`Cons_Goods/model.xml` line 154). The earlier report, section 2, lists the same agent types.

Reading: Eurace does not hardcode modern sectors; it has no sectors. It has one consumption good, differentiated by firm
through price and quality, and one capital good in vintages that differ in productivity. That is an economy too thin to have
a recipe graph at all, which is why this repo ported the rules (market protocols, rationing, wage and price rules) and not the
goods. The claim as stated is not supported by the clone. The thin good space is a limitation for the founder scenario, not a
set of modern sectors baked in.

### Could a feasibility pass serve as a check, not a price source

Yes, and this is the version I would recommend. Use the linear programme only to answer feasibility questions and discard
its duals as prices:

1. **Run-pays test.** For the opening's chosen runs and producers, check that at the economy's own seed prices and wages every
   chosen recipe covers its input cost, plant wear and wages, and that the sum of runs does not exceed a site ceiling. The
   opening already computes `StationaryFlows.profit` and `sales_value` against `wage_bill` and `input_cost`; a per-recipe
   (not just in total) negative-margin report would catch the case where an opening sizes producers whose runs cannot
   pay. The Norse spin-up collapse this week is the motivating case (I have not reproduced it; I read only the commit log
   and `Complaints/473`; `python3 sim/simulator.py spin-up-trace --civ norse_900ad --years 7` is the measure that
   exists). A repo-native version needs no new solver: it is a loop over `opening_stationary.solve` output.
2. **Mass-balance and endowment feasibility.** Check that the final demand is producible from tile endowments and the
   freight network (a feasibility linear programme with zero objective). A phase-one infeasibility certificate names which good
   or tile binds. This is the part that needs a solver dependency.
3. **Shock regression tests.** After a shock (a mine opens, gold arrives), check mass balance and stock-flow consistency
   as invariants of the agent economy. This is the useful part of sfctools and BoARIO's pattern, as a test.

A check that returns pass or fail with a `cause` fits CLAUDE.md section 6's "a refusal's `cause`" and does not create a
second price owner.

---

## Recommendation (one line each, for possible later complaints)

1. **Opening run-pays check.** Add a per-recipe report, in the opening validation, of producers whose planned runs cannot
   pay input cost, plant wear and wages at the seed prices; the check, not a solver, is the fix for sizing producers that
   cannot pay (reads `opening_stationary.solve`; no new dependency; link Complaint 473).
2. **Feasibility check as a test, not a price source.** If the owner accepts a linear-programme dependency, use it to prove
   a stated final demand is producible over the tile network and to name the binding good or tile; discard its duals.
3. **Reject shadow prices as opening prices.** Record in `ONE_PRICE_OWNER_PLAN.md` that a scarcity dual is a second price
   owner (507) and biases the baseline toward equilibrium (4.2); keep the cost-of-making calculator as the only seed.
4. **Spatial Cantillon test.** Add a slow-tier relationship test that a gold injection at one tile raises local prices
   before distant ones, along route cost, once the spin-up settles (blocked by Complaint 473).
5. **Proportional rationing with input buffers.** Check, against BoARIO's rule, that an input shortage cuts a recipe's runs
   by the share it is short and not to zero (CLAUDE.md section 5); a rule test on the settlement function.
6. **Phase-diagram method for the opening.** Use the Gualdi et al. approach (map the economy's behaviour over the hiring
   and firing asymmetry parameters) to show where the opening sits relative to the good-to-bad transition; this is
   analysis for Complaint 473, not an engine feature.
7. **Drop the Eurace claim.** The clone has no sectors; no complaint, but the thin good space deserves a note in
   `NOTICE.md` or the economy architecture docs.

Nothing else surveyed deserves a complaint: the Julia and energy frameworks (BeforeIT.jl, Agents.jl, JuMP, PyPSA,
Calliope, SpineOpt, MESSAGEix), the Python frameworks (AgentPy, Mesa, GAMA, abcEconomics) and the CGE family offer
nothing the repo lacks that fits its stack and its rules.

## Models I could not open or identify

- ACCEPTS: NO SOURCE FOUND (ambiguous).
- ColonD: NO SOURCE FOUND (ambiguous).
- HABITAT (IIASA): NO SOURCE FOUND (ambiguous).
- JMAB 2.0: no repository found.
- Mark-0: no source named it; only Mark I and Peters et al. were found.
- Not opened (snippet only): K+S paper, CATS and BAM, Lagom generiC, sfctools (PyPI page failed), GTAP, GEMPACK, Envisage,
  MPSGE, Poledna 1:1 forecasting paper, CSH Vienna VAT network paper, PyPSA marginal-price documentation.
- The earlier report's HARK, Eurace and Caiani sources remain the only fully read ones for the agent-based design.
