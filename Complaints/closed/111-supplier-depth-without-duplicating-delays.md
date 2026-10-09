# Add supplier depth / tacit industrial competence, without duplicating existing delays

**Status:** closed - supplier depth is derived and automatic: tenure (worker-years by trade in a technique, held in the labour core and faded at the demography's leaving rate) drives ramp, failure risk (which absorbs the retry multiplier), reachable scale, founder-free running, scrap and unit labour along an experience curve, plant repair and input supply (producers, haul days from geography, supplier depth); `EXIT_GRACE_YEARS` is retired into the ramp. The whole-game seeding-order check is the slow topic `sim/tests/test_industry_depth_game.py`, written and not yet run

**Source:** playtest findings document, LATE-009. **Type:** Realism
refinement, medium size. Carries its own explicit warning against
duplicating a mechanism that already exists, the same shape as `ECON-001`
(`docs/architecture/DESIGN_PRINCIPLES.md`).

## The player's reasoning

The simulator already models much more than "know it, then instantly have
millions of parts": build time, adoption time, labour, materials, precision,
power, failure risk, ramp-up and specialist training. That should remain.
The missing refinement, per the player, is ecosystem depth specifically:
number of qualified suppliers, trained-worker density, maintenance
capability, quality-control culture, the ability to reproduce a process
without founder supervision, and learning-by-doing. These should influence
failure rate, cost, ramp speed and maximum production scale, but the player
is explicit: do not implement this as a blanket extra "+N years" on every
advanced technology, because that would duplicate the delays already
described under `ECON-001`.

## How this sits against CLAUDE.md

§3.1 is the right lens: "supplier depth" as a concept has to be derived from
something the model can already count (how many concerns of a given kind are
operating, how long they have been operating, how many specialists have been
trained in a trade) rather than asserted as a flat maturity score per
technology. §3.4 applies to whatever stand-in constant gets introduced while
that derivation does not exist yet: it must be declared through `sim/
constants.py` with `kind="temporary_heuristic"`, the same discipline
`ECONOMY_INDEX_PER_DIFFUSED_NODE` and its siblings already follow (see
`Complaints/101`).

## What already exists

`sim/labour/labour_market.py`'s own module docstring (read directly) already
names a version of this gap: `Workforce.hours_by_trade` is "hours actually
worked right now, an initial condition plus whatever `Workforce.step` has
moved since," and it is explicitly the module's job to make a trade's
`have_versus_need` gap visible rather than assumed away. A "learning-by-
doing" or "trained-worker density" effect on ramp speed and failure rate is
a natural extension of that module once it is wired in (see `Complaints/
106`), since it already tracks how long a trade has carried its current
workforce. There is no dedicated "supplier ecosystem" concept beyond that
today.

## Size

Medium. This is smaller than the other LATE findings because it can likely
attach to `labour_market.py`'s existing workforce-tenure tracking rather
than needing a new subsystem, but it should not be started before that
module is wired in (`Complaints/102`), since building supplier depth against
the current unwired, population-only `TRADE_DENSITY` classification would
mean deriving a refinement from a number the project already knows is wrong.

## Cross-references

`docs/architecture/DESIGN_PRINCIPLES.md` (ECON-001) for the "do not add a blanket delay" pattern
this finding explicitly echoes. `Complaints/102` (ECON-004) for the labour-
market wiring this depends on. `Complaints/44` and `Complaints/47` (open)
both independently point at the same underlying gap (professions do not
move in response to scarcity) that `labour_market.py` exists to close.

Owner decision (2026-10-09): supplier depth must come out of the simulation automatically (operating concerns, trained workers, years of running), never a manual or authored value per technology.

## Orchestrator decisions (2026-10-09)

- Delivery delay lives in geography: route days from the nearest producer of an input to the concern's tile, through geography's api. The agent economy carries no per-recipe lead time, so the engine counting geography's days is not double counting. One port method lists producers of a good by tile (`producers_by_good`, `sim/engine/economy_port_year.py`).
- Per-trade tenure: worker-years spent in a technique by a trade, held in the labour core (`sim/labour/tenure.py`); it decays at the demography's death and retirement rate (`sim/world/demography_turnover.py`, no new number). A worker moving trade carries nothing.
- Scrap and unit labour: an experience curve on the same worker-years stock; the progress ratio is a declared temporary_heuristic (`LEARNING_PROGRESS_RATIO`, Wright 1936; Argote and Epple 1990). Scrap share and labour per unit both fall along it toward the entry's stated figure.
- Founder-free running: a concern no longer needs its founder once the tenure its staff hold in the technique reaches the founding staff's hours for one year of running.
- Maintenance: plant repair labour, sized from the plant's stated service lives in production data; repair needs trades with tenure in that technique, and lacking them the concern loses running time in proportion.
- `EXIT_GRACE_YEARS` and the retry-risk multiplier retire into the tenure stock: a concern's exit grace is its ramp (which depth sets), and a diagnosed failed attempt adds its worker-years to the stock that the risk reads.
- The seeding-order check is a slow topic, not run here.

## Where it lives

`sim/engine/industry_depth.py` (stock, depth, seeding, founder-free, failure learning), `sim/engine/industry_learning.py` (pure curves, repair, input supply), `sim/engine/industry_concern.py` (the Sim side; applied in `concern_takings`), `sim/labour/tenure.py`. Tests: `test_labour_tenure`, `test_industry_depth`, `test_industry_learning` (quick), `test_industry_depth_game` (slow).
