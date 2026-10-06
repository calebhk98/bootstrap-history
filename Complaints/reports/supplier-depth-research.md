# Research: supplier depth and tacit industrial competence (Complaint 111)

**Status:** research report, no code changed. Written for Complaint 111 (LATE-009), which is on hold behind
Complaint 428 (one labour model sets wages and workforce).
**Marking:** every citation is tagged. *(snippet)* means the claim comes from search-result text seen in this
session; the page itself was not opened in full. *(recalled)* means it comes from memory of the literature and
has not been re-read. Nothing here is tagged *(read)*; no source was fetched in full, so every figure in the
tables should be re-checked against its paper before it becomes a constant. Where the report names code, it
was read on this branch (`structural-dedupe-and-owner-decisions`).

## 0. The question and the constraint

A playtester wants industrial ecosystem depth (qualified suppliers, trained-worker density, maintenance,
quality control, running a process without the founder, learning by doing) to move failure rate, cost, ramp
speed and maximum scale. The same playtester forbids a flat extra delay, and `DESIGN_PRINCIPLES.md` (research
is not manufacture) says the same: construction and adoption already run in parallel, risk is per node, and
a new concern already ramps. So the design test is: **every effect must replace or refine something that
exists, or be derived from a stock the simulator counts. Nothing may add a second clock on top of an existing
one.** CLAUDE.md 4.1 (no hardcoded outcomes), 4.4 (label heuristics), 4.5 (yields are physical, never tuned to
a price) and 4.7 (no content ids in the engine) apply.

## 1. What already exists

| Concern | Where | What it does today | Gap |
|---|---|---|---|
| Revenue ramp of a new concern | `sim/engine/economy_production.py` `venture_ramp`; `sim/engine/agents_port.py` `ramp`; config `revenue_ramp_years` in `sim/engine/data.py` | Takings climb linearly with calendar age since opening, the same for every technique, every area, every staff | A constant clock. Does not know whether anyone nearby has run the technique, nor whether the staff are experienced. This is the clock to replace, not to add to. |
| Output scaled by ramp and staffing | `sim/agents/supply.py` `concern_output_tonnes` (ramp times staffed share) | Output is declared output times ramp times share of staff found | Same constant ramp |
| Failure risk of a project | `sim/engine/projects_progress.py` `effective_risk`, `_retry_risk_multiplier`, `_control_relief_multiplier`, precaution relief | Node risk times retry learning (geometric decay toward a floor per failed attempt of this node) times a controller relief times precaution | Learning comes only from the founder's own failures of this node. Experience of other operators, of the area's workers, or of running the technique does not enter. No forgetting. Constants are labelled temporary (confidence D, no fitted curve). |
| Expected wait of a risky node | `projects_progress.py` expected-attempts sum | Reads `effective_risk` only | Fine: any new risk factor must enter through `effective_risk`, its stated single home. |
| Retained calendar after a failure | `_retry_calendar_retain` | Share of elapsed years banked | Separate social groundwork; leave alone. |
| Copy difficulty and tacit share | `sim/engine/society_disclosure.py` `copy_difficulty`; `copy_visibility` and `copy_visibility_reason` per node, checked by `sim/engine/validate_copy_visibility.py`; `sim/agents/firm_entry.py` `copy_ease`, `TACIT_SHARE_OF_COPYING` (`sim/agents/tuning.py`) | Complaint 376 (partly done). Per technique, the share an onlooker can recover from product or yard; a founder's literacy changes the copy chance | This is the chance to *acquire the design*. It is not the competence to *run it*. A firm that copies successfully still starts as a novice. The two must not be merged; but the declared visibility is the right data for how much of a technique lives in practice (section 3). Most nodes have no declared value yet. |
| Instant copying inside a line of business | `sim/engine/techniques_in_use.py` (labelled temporary heuristic) | One producer running a technique makes it available to every concern in the line | The explicit hole for producer-by-producer knowledge. Experience per area plugs it. |
| Entry, crowding, expansion | `sim/economy/entry*.py`, `sim/agents/firm_entry.py` (`entry_premium` per operator), `sim/engine/agents_port_capacity.py` (`span_factor`, `running_cost`, `MANAGEMENT_SPAN_EXPONENT`), `EXIT_GRACE_YEARS` ("stands in for the ramp-up") | Entry cost rises with operators; growth carries a span-of-control cost | `EXIT_GRACE_YEARS` is a second stand-in for the same ramp. Both retire when ramp is derived. |
| Labour core | `sim/labour/market/` (see `DESIGN.md`), `sim.labour.api`, `records.py` `MarketState` | People per area, trade and ability band; trainee cohorts as `[years_left, people per band, bonus]`; sticky wages; intake capped by `incumbents * APPRENTICES_PER_MASTER + school seats` (`training.py`, labelled); recruitment friction through a matching function | **No tenure.** Workers are anonymous counts per band. The complaint's wording ("how long a trade has carried its current workforce") describes the older `sim/labour/labour_market.py` `Workforce.hours_by_trade`, which holds hours now, not experience. Experienced versus novice workers cannot be told apart. This is the one structural addition the design needs. |
| Hire friction and trade supply | `sim/engine/projects_staffing*.py`, `staff_replacement.py`, `labour_staff_ledger.py` | A project fails on a deadline when trades are short; replacements hired through `hire` | Counts heads, not skill. |
| Plant upkeep | `sim/engine/node_upkeep.py` | Upkeep as a labelled share of build cost by kind, plus staff | No spare-parts or repair-trade dependence. Maintenance capability is a gap. |
| Recipe labour and inputs | `data/production/`, `sim/engine/concern_volume.py`, `producer_costs.py`, `solve_prices*.py` | Labour hours and inputs per unit are physical facts; price is solved | The recipe has no notion of the practice level at which the hours apply. |
| Input supply across distance | goods market (`sim/economy/`), freight (`sim/geography/`), `Sim.actors.active_firms()` in `sim/agents/registry.py` | Offers cleared at a price, freight priced | Price clears scarcity but not *variety and reliability*: a market with one thin seller of an input still has a price. Count of producers in reach is derivable from firm concerns and offers but is not read for any effect. |
| Capability tiers | `economy_production.py` `capability_factor` | Saturating method multiplier on the founder's own hours | Per household, not per area; leave alone. |

Not duplicated by this design: build time, adoption time (`yrs` is the larger of build and adoption), the
retry-learning clock, calendar floors, span of control, entry premium. Duplicated if done naively: an extra
"maturity" delay, a per-technology maturity score, a second ramp beside `revenue_ramp_years`, a second risk
discount beside `_retry_risk_multiplier`.

## 2. What the literature says

All learning-rate numbers are in the tables below; the prose states only the shape.

### 2.1 Shape of the experience effect

* Cost per unit falls as a power law of **cumulative output**, not of calendar time (Wright 1936 for
  airframes, generalised by Alchian 1963 and Arrow 1962) *(recalled; Alchian's role as first empirical study
  in the snippet at econometricsociety.org/publications/econometrica/1963/10/01/reliability-progress-curves-airframe-production)*.
* Across dozens of technologies Wright's law forecasts about as well as a pure time trend, because output
  usually grows exponentially so the two are indistinguishable; the cumulative-output form is the causal one
  *(snippet: Nagy, Farmer, Bui, Trancik 2013, web.mit.edu/mitssrc/nsf/papers/Nagy_Farmer_Bui_Trancik_2013.pdf)*.
  In a simulator whose output is endogenous this matters: a stagnant economy must not improve with the
  calendar.
* Counter-evidence that cumulative output is not the whole story: Lundberg's Horndal works improved without
  investment for many years *(snippet: en.wikipedia.org/wiki/Erik_Lundberg)*, which argues for a modest
  within-plant experience effect that does not need new capital. Thompson's reanalysis of the Liberty
  shipyards finds most of the celebrated learning gain was capital deepening and falling quality, leaving
  little for learning *(snippet: econwpa.ub.uni-muenchen.de/econ-wp/dev/papers/9712/9712001.pdf)*. Design
  consequence: the experience term must be separable from capital and from a quality change (scrap), so that
  a test can show it is not counting plant twice.
* Experience depreciates. Organisational forgetting is large in practice and some of it travels with turnover
  *(snippet: Benkard 2000, nber.org/papers/w7127.pdf; Argote and Epple 1990 as summarised in
  proceedings.systemdynamics.org/2007/proceed/papers/LOPEZ502.pdf)*. The Liberty finding that hiring and
  firing did not matter much *(snippet, same summary of Argote, Beckman and Epple 1990)* says much of the
  knowledge sits in the organisation and its tools, not only in heads. So the stock needs a decay and a split
  between a part that persists in the organisation and a part that leaves with workers.
* Transfer is partial and boundary-bound. Knowledge crossed shifts in one plant only partially *(snippet:
  Epple, Argote, Devadas 1991, ideas.repec.org/a/inm/ororsc/v2y1991i1p58-70.html)*, and crossed between
  stores of one franchisee but not between owners *(snippet: Darr, Argote, Epple 1995,
  ideas.repec.org/a/inm/ormnsc/v41y1995i11p1750-1762.html)*. Design consequence: experience is held per
  area (and per firm where firms exist), and leaks to neighbours through shared workers and visibility, not
  automatically to the whole society.
* Defect rates specifically: a new assembly plant's defects fell steeply within weeks, a tenfold increase in
  cumulative output halved them, and the second shift started below the first shift's starting rate, so part
  of the knowledge is embodied in the plant, not the workers *(snippet: Levitt, List, Syverson 2013,
  nber.org/papers/w18017)*.

### 2.2 Tacit knowledge and failed transfer

* Textile machinery: Britain banned the export of machines and the emigration of those who ran them, and
  Samuel Slater rebuilt Arkwright's spinning system in America from what he had learned working in a mill,
  because drawings alone did not carry it *(snippet: americanheritage.com/father-our-factory-system and
  .../technology-transfer)*. The lesson for the simulator: the founder's database is the equivalent of
  drawings. It conveys the explicit part. The rest is earned through operation.
* Early weaving in Lowell: productivity per worker rose substantially over decades with no change of
  machine; literate workers learned faster but short tenure limited the gain, and firm and social
  institutions had to change before deep skill could be built *(snippet: Bessen 2003, Journal of Economic
  History 63(1), ideas.repec.org/a/cup/jechis/v63y2003i01p33-64_00.html; the book argues skill with a new
  technology takes years and is mostly learned on the job, snippet: scholarship.law.bu.edu/books/342)*.
  Tenure is a stock (workers who stay) and literacy shifts the rate, which agrees with the existing
  `copy_ease` literacy term.
* Interchangeable parts: Springfield Armory is associated with the first volume production with
  interchangeable parts *(snippet: allaboutlean.com/230-years-interchangeability)*; Hounshell's account that
  true interchangeability took decades of gauges, fixtures and machine-tool makers, with a working supplier
  base of toolmakers as the binding constraint, is from memory *(recalled: Hounshell, From the American
  System to Mass Production, 1984)*. Relevant here: the missing input was a trade of experienced gauge and
  tool makers, and a producer of machine tools in reach, not a longer clock.
* Soviet and Japanese cases: Gorky and later Togliatti were large imports of plant and engineers; outcomes
  varied with how much operating and supplier capacity was transferred or built *(snippet:
  conversableeconomist.com/2021/08/25/how-stalin-and-the-nazis-tried-to-copy-henry-ford; details of each
  plant's ramp are recalled and not checked)*. Japan's absorption is tied to prior codification of technical
  knowledge and to a trained workforce *(snippet: core.ac.uk/works/156032773, Codification, Technology
  Absorption, and the Globalization of the Industrial Revolution)*. Use these as qualitative validation
  (ensembles, not dates; CLAUDE.md 4.2).

### 2.3 Suppliers, agglomeration and capabilities

* Marshall's three sources of agglomeration (input sharing, labour pooling, knowledge spillovers) all have
  support in co-location data, with input-output links the strongest and labour pooling next *(snippet:
  Ellison, Glaeser, Kerr 2010, AER 100(3), nber.org/papers/w13068)*. Design consequence: the two stocks to
  count are the number of operating producers of a concern's inputs in reach, and the experienced workers of
  the trades it uses in its area.
* Hidalgo and Hausmann treat a country's output as the set of capabilities it holds; a product needs a bundle
  of capabilities, and a country that lacks one cannot make the products needing it *(snippet:
  hks.harvard.edu/centers/cid/publications/faculty-working-papers/building-blocks-economic-complexity)*.
  The mapping is natural here: a technique's recipe already names its trades, materials and plant, so its
  capability bundle is derived from the recipe, never authored.

### 2.4 Rates found

| Quantity | Value as found | Tag and source | How it would be used |
|---|---|---|---|
| Typical progress ratio (cost after a doubling of cumulative output) | about four fifths, which is an exponent of about one third | snippet, ourworldindata.org/learning-curve and Nagy et al. | Prior for the unit-labour experience exponent |
| Range of learning rates across studies | between a twentieth and two fifths per doubling | snippet, arxiv.org/pdf/0907.0036 | Bounds for a sensitivity range in tests |
| Defects versus cumulative output | halved per tenfold of output (exponent about three tenths) | snippet, Levitt, List, Syverson | Prior for the scrap (defect) exponent |
| Defects in the opening weeks of a new plant | fell by more than four fifths in eight weeks | snippet, same | Shape check: steep early, flat late |
| Depreciation of organisational experience | about four percent a month for one aircraft programme | snippet, Benkard 2000 | Order of magnitude for stock decay; widely varying by industry, so a range, not a point |
| Learning without investment | about two percent a year of output per head | snippet, Lundberg on Horndal | Lower bound check: experience alone gives modest, not dramatic, gains |
| Transfer across owners in one franchise | none measured across owners; some across same owner | snippet, Darr, Argote, Epple | Boundary for leakage between firms |
| Transfer across shifts | substantial but incomplete | snippet, Epple, Argote, Devadas | Share held in plant versus workers |
| Share of Liberty-yard gain attributable to learning | small once capital and quality are controlled | snippet, Thompson | Warning, not a parameter |

These are the cross-industry priors. The simulator has no right to author a per-technique rate (section 4); it
may declare a single cross-technique prior as a labelled temporary heuristic (`kind="temporary_heuristic"`,
confidence stated, source as above) and let per-technique spread arise from recipe structure.

## 3. Recommended mechanism: experience stocks, three of them

One principle: **competence at a technique in an area is a stock of accumulated, depreciating experience, and
every effect reads that stock.** There is no per-technology maturity number. Three stocks, each already
countable or one small field away.

### 3.1 The stocks

1. **Cumulative output per technique per area** (`area_experience[area][technique]`). Updated yearly by the
   production the economy already computes: add the units each operating concern made, then multiply the
   stock by a retention factor below one. Technique means the entry (or its line of product) in
   `concern_volume.py`, so several nodes that make the same outputs share it, which is how the real
   experience carries across generations of a design (Benkard found partial carry-over). Experience of a firm
   (an operator's own stock) is a second vector of the same shape, so a firm that opens in a district with
   experience starts above a firm in an empty district but below its own incumbents. The stock must be a
   plain dict of floats in the save so that dynamic-over-enumerated save detection holds (CLAUDE.md 5, 4.6).
2. **Experienced workers per trade per area**, from the labour core. The core holds people per band but not
   tenure. Add one parallel count, `experienced[area][trade]`, a subset of `workers[area][trade]`: graduates
   and new hires join as inexperienced; each year a share of the inexperienced become experienced at a rate
   of one over the trade's own training years plus a working-years term; attrition, switching and migration
   move both counts in proportion to their share (conserve people; the core already has a conservation test).
   Two stocks per trade is enough; a full age distribution is not needed. This is the "workforce tenure" the
   complaint refers to. It must be added in `sim/labour/market/` after Complaint 428 lands so the agent
   economy and the core are one model; do not build it against the old `TRADE_DENSITY` classification.
3. **Operating producers of each input in reach** (`input_producers[area][material]`). Count of concerns
   (firms and the founder's) currently making each input a technique's recipe names, within freight reach of
   the area, read from `registry.active_firms()` concerns and the production entries; weighted by the
   concern's capacity share so a toy operator does not count as a supplier. No new state is needed: it is a
   derived read each year, cached by `techniques_epoch()`.

### 3.2 How each effect reads the stocks

Let `practice_level` of a concern be a single number in the unit interval, built from the stocks:

    practice_level_of_concern = organisational_experience_share * experienced_staff_share * input_reliability_share

with

    organisational_experience_share = area_experience_of_technique / (area_experience_of_technique + experience_for_mature_practice_of_technique)
    experienced_staff_share = experienced_workers_hired_in_trades_of_recipe / workers_hired_in_trades_of_recipe
    input_reliability_share = for each input of the recipe, producers_in_reach / (producers_in_reach + producers_for_reliable_supply), combined across inputs by the weakest input

`experience_for_mature_practice_of_technique` and `producers_for_reliable_supply` are not authored per technique.
The first scales with the recipe's size of operation (labour hours per unit times units in a founding-size
concern), the second is one cross-technique labelled constant. Which of the three is smallest is the binding
constraint, so the ceiling reported to the player names its cause.

Effects, each replacing an existing term:

* **Ramp speed.** Replace the age-only `venture_ramp` and the config `revenue_ramp_years` with the concern's
  `practice_level` driven ramp: a concern opened in a district with experienced staff and nearby suppliers
  reaches full takings quickly; a first-of-kind concern in an empty district climbs only as its own cumulative
  output and its own staff's tenure accrue. The old behaviour is the special case where the stocks start at
  the scenario's default. `EXIT_GRACE_YEARS` then reads the same ramp. One clock, not two.
* **Unit labour.** Recipe hours are the practised cost (physical fact; CLAUDE.md 4.5 says never tune yields
  to a price). A concern runs at `recipe_hours * novice_multiplier`, where
  `novice_multiplier = 1 + tacit_share * (1 / practice_level^exponent - 1)`-shaped, bounded above, and equals
  one at full practice. The `tacit_share` is derived: it is the part of the know-how not recoverable from
  documents and sight. Where `copy_visibility` is declared it is `1 - copy_visibility`; elsewhere the
  existing count-of-trades-and-materials stand-in (labelled transitional). The founder's database reduces
  the explicit part, not this one (open question 1).
* **Failure rate.** Enter through `effective_risk` (its stated single home), as a factor
  `risk_from_practice = floor + (1 - floor) * (1 - practice_level)`-shaped. To avoid duplication, the existing
  retry learning becomes one input of the same stock rather than a parallel discount: a failed attempt that
  teaches adds to the technique's experience (as does each unit of success), and `_retry_risk_multiplier`
  is retired once the stock reproduces its behaviour in a test. Until then the two must not both apply at full
  strength; use the stricter of the two, not their product, during the transition.
* **Scrap (quality control culture).** Do not author a quality score. Model it as a physical yield loss: the
  share of output that is scrap, falling with experience on the Levitt shape, applied to the output the
  economy already counts (`concern_output_tonnes`). Higher scrap also raises the cost per good unit through
  the existing price solver, so quality shows up as cost with no new price rule. Measurement tools
  (precision tiers already in the tree) set how fast a firm can see its own defects; the exponent can be
  stepped by whether the precision-instrument nodes are held (open question 4).
* **Capacity ceiling.** A concern's maximum scale is the smallest of: staffed share (exists), experienced
  workers available divided by the experienced workers the concern needs per novice (the same
  `APPRENTICES_PER_MASTER` ratio the training intake already uses, so no new constant), and the supply of
  its inputs in reach. This replaces nothing but adds a bound the engine does not have; it reuses
  `span_factor` for administrative cost and does not touch it.
* **Running without the founder.** The existing concern needs the founder's hours as a project input
  (research the exact gate in `projects_staffing.py` before building; it was not traced in this report).
  Rule: the founder's hours needed to keep a concern open shrink as the experienced staff share rises, with
  the same single `experienced_staff_share` the other effects read. A concern whose staff are all novices
  needs the founder or an equivalent director; one with an experienced staff does not. Same stock, a third
  reading.
* **Maintenance.** Plant upkeep today is a labelled share of build cost. Replace its labelled constant
  gradually: breakdown downtime falls with experienced workers in the trades that appear in the plant's
  maintenance recipe and with producers in reach of its renewed parts (the `capital` entries named in
  `node_upkeep.py`). Without the repair trade or a parts producer, downtime rises and output falls. Do this
  last (stage 5); it is the least supported by the existing data.

### 3.3 Why this is not a flat delay

* Every effect is a function of a stock, so a technology run by many experienced hands with nearby suppliers
  carries no extra cost, and the first of its kind carries a lot. The same technique is slow in one area and
  quick in another, which is what the record shows (section 2.2).
* The ramp, risk and scrap terms replace an age clock, a retry-only discount and a flat figure; they do not
  sit on top of them.
* Nothing is paid or waited in calendar years that the existing seam already charges. A reader can check this
  with the same command as the principle names: `python3 sim/simulator.py why <node>`, which should gain a
  line naming the binding practice factor.

## 4. What must not be authored

* A maturity level, a "supplier depth" score, a learning rate, or a ramp length per technology or per
  civilisation. CLAUDE.md 4.1 and 4.7.
* Any dated outcome: when a district gets a gauge-making trade, when scrap falls, when a country becomes
  self-sufficient in a good. Validate against ensembles (CLAUDE.md 4.2): the order of magnitude of
  learning exponents, the correlation of area experience with defect rate, the spread of ramp times across
  areas.
* A yield or price tuned so a computed cost matches the book (CLAUDE.md 4.5). Recipe hours stay the practised
  physical figure; the novice multiplier sits on top and is bounded.
* A per-trade experience length. It comes from the trade's own training years in the labour core.
* A quality score or "QC culture" field. It is the scrap fraction, derived.
* `if node == "..."` anywhere (CLAUDE.md 4.7). The recipe supplies the trades, materials and plant a technique
  needs; the stocks are keyed by technique id as data.
* A save-format shim (CLAUDE.md 4.6). New stocks are plain fields; old saves are not read.
* The cross-technique constants are the only authored numbers: retention of experience, experience needed for
  mature practice relative to a founding concern, producers for reliable supply, the floor of the risk term.
  Each is declared with `kind="temporary_heuristic"`, a source from section 2.4 and confidence, so
  `python3 sim/constants.py --burndown` lists them. This is the labelled-heuristics discipline of 4.4.

## 5. Staged build plan with tests

Order is by dependency and by how much existing mechanism each stage replaces. Each stage first adds a
regression test that shows today's behaviour (CLAUDE.md 6), then changes code.

**Stage 0 (blocking): wait for Complaint 428.** The agent economy's wages and workforce must come from the
labour core. Nothing below attaches to the old density classification.

**Stage 1: cumulative output per technique per area.** Add the stock, its yearly update from realised
production, depreciation, and a read function. No effect yet.
Tests: the stock grows with output and decays with none; two techniques sharing outputs share the stock; the
stock round-trips through save and load; a stagnant economy (zero output) shows no learning however many
years pass (the calendar-versus-output distinction). Fingerprint check unchanged
(`python3 -m sim.tests.fingerprint check`).

**Stage 2: experienced workers per trade in the labour core.** Add `experienced` beside `workers`; graduates
join inexperienced; yearly maturation; attrition and switching conserve both counts.
Tests: a conservation test extending the existing people-conserved test; a trade whose intake is cut keeps
a falling experienced share; a switcher into a trade joins inexperienced (switching within a skill family
keeps part, matching the existing retraining rule).

**Stage 3: derived ramp, retiring the constant.** Replace `venture_ramp` and the `revenue_ramp_years` reading
in `agents_port.py` `ramp` and `agents_port_capacity.py` with the `practice_level` ramp; retire
`EXIT_GRACE_YEARS` as a separate stand-in. Calibrate the default scenario so a typical first concern
reproduces today's ramp, to keep this refactor behaviour-neutral (fingerprint, then deliberate change).
Tests: same technique, area with experience versus area without: former ramps faster; a copy by a firm in
an experienced district reaches full takings sooner than the founder's first; ramp never exceeds one.

**Stage 4: unit labour and scrap.** Apply the novice multiplier to the hours a concern uses (in
`concern_volume.py` or its callers) and scrap to output (`supply.py`); the solver prices both.
Tests: cost per unit falls with cumulative output at the stated exponent within tolerance (a recovery test of
the prior, not a validation of history); the recipe's hours are the asymptote; a doubled input scrap raises
cost per good unit; capital added without output leaves the experience effect unchanged (guards against the
Thompson double count).

**Stage 5: failure rate and the retry-learning merge.** Add `risk_from_practice` through `effective_risk`;
fold `_retry_risk_multiplier` into the same stock; use the stricter of the two while both exist.
Tests: first attempt in an empty area has the bare risk; the same attempt in a practised area has less; the
stricter-of rule never makes risk lower than either alone; an uninformative failure adds nothing to
experience (the existing `uninformed_failures` rule).

**Stage 6: input reliability and capacity ceiling.** Count producers of inputs in reach and bound capacity
by experienced staff and suppliers; report the binding constraint on the screen and in `why`.
Tests: removing the only producer of an input in reach lowers the practice level; adding a second raises it
with diminishing return; the binding constraint named matches the smallest factor.

**Stage 7: founder supervision and maintenance.** Reduce founder hours needed with the experienced share;
tie downtime to repair trades and parts producers. Tests: a concern with a full experienced staff stays open
without the founder; with none, it does not; downtime rises when the repair trade is absent.

**Throughout:** `python3 sim/simulator.py validate` after any data touch; `python3 -m sim.tests --slow` before
a pull request; an ensemble test (many seeds) checking only the relationships in section 4.

## 6. Open questions

1. **What does the founder's database buy?** A reasonable reading is that documentation covers the explicit
   share of know-how and so lowers the starting novice multiplier and risk of the founder's first concern,
   but not the tacit share. How large a head start, and does it apply only to the founder or to anyone with a
   copy of a manual? The simulator has no document stock yet; this ties to Complaint 376's `copy_visibility`.
2. **Where does experience live, in heads or in the plant?** Evidence says both (section 2.1). A split
   parameter is a labelled heuristic; the alternative is to hold the embodied part on the plant stock and the
   rest in the workforce, so it can be lost differently on turnover. Which is simpler to save and test?
3. **Per-firm versus per-area stocks.** Franchise evidence argues for firm boundaries, Marshall evidence for
   area spillover. Start with area only and add a per-firm vector once firms (Complaint 103) carry their own
   history?
4. **Quality measurement.** Should instruments (a precision-measurement node held in the society) change the
   scrap exponent, or only the start point? Needs a read of how precision is represented in the tree.
5. **Does the existing founder-hours gate for operating concerns exist as stated?** Not traced here
   (`projects_staffing.py` should be read first).
6. **Interaction with Complaint 112 (sector diffusion) and 101 (growth curve).** Both touch adoption timing.
   The area stock is a natural carrier for 112 but they must not each add a clock.
7. **Calibration burden.** One cross-technique exponent versus an exponent shifted by recipe complexity.
   The cited spread is wide, so a sensitivity test (rate range from section 2.4) is needed before defaults.
8. **Who counts as a supplier?** Weighted by capacity share (proposed), or by number of independent firms
   (Marshall's variety)? The latter needs the firm identity from Complaint 103.
9. **Source checking.** Every citation is snippet or recalled. Before any constant is declared, open the
   papers for Wright, Benkard, Levitt and colleagues, Bessen and Epple and colleagues and record the figure
   with its context.

## 7. Sources

* Our World in Data, learning curve: https://ourworldindata.org/learning-curve (snippet)
* Nagy, Farmer, Bui, Trancik, Statistical basis for predicting technological progress:
  https://web.mit.edu/mitssrc/nsf/papers/Nagy_Farmer_Bui_Trancik_2013.pdf (snippet)
* McNerney, Farmer, Trancik, role of design complexity: https://arxiv.org/pdf/0907.0036 (snippet)
* Alchian 1963: https://www.econometricsociety.org/publications/econometrica/1963/10/01/reliability-progress-curves-airframe-production (snippet)
* Arrow 1962 and Wright 1936 (recalled)
* Lundberg, Horndal effect: https://en.wikipedia.org/wiki/Erik_Lundberg (snippet)
* Argote and Epple 1990 and Argote, Beckman, Epple 1990, as summarised at
  https://proceedings.systemdynamics.org/2007/proceed/papers/LOPEZ502.pdf (snippet)
* Benkard 2000, Learning and Forgetting: https://www.nber.org/papers/w7127.pdf (snippet)
* Thompson, Liberty ships: https://econwpa.ub.uni-muenchen.de/econ-wp/dev/papers/9712/9712001.pdf (snippet)
* Epple, Argote, Devadas 1991: https://ideas.repec.org/a/inm/ororsc/v2y1991i1p58-70.html (snippet)
* Darr, Argote, Epple 1995: https://ideas.repec.org/a/inm/ormnsc/v41y1995i11p1750-1762.html (snippet)
* Levitt, List, Syverson 2013: https://nber.org/papers/w18017 (snippet)
* Bessen 2003: https://ideas.repec.org/a/cup/jechis/v63y2003i01p33-64_00.html (snippet); Bessen 2015 book:
  https://scholarship.law.bu.edu/books/342 (snippet)
* Slater and British export controls: https://www.americanheritage.com/father-our-factory-system (snippet)
* Springfield Armory: https://www.allaboutlean.com/230-years-interchangeability/ (snippet); Hounshell 1984 (recalled)
* Soviet transfer: https://conversableeconomist.com/2021/08/25/how-stalin-and-the-nazis-tried-to-copy-henry-ford (snippet)
* Japanese absorption: https://core.ac.uk/works/156032773 (snippet)
* Ellison, Glaeser, Kerr 2010: https://nber.org/papers/w13068 (snippet); Marshall 1890 (recalled)
* Hidalgo and Hausmann 2009: https://www.hks.harvard.edu/centers/cid/publications/faculty-working-papers/building-blocks-economic-complexity (snippet)
