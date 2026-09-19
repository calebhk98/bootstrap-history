# Add supplier depth / tacit industrial competence, without duplicating existing delays

**Source:** playtest findings document, LATE-009. **Status:** Realism
refinement, medium size. Carries its own explicit warning against
duplicating a mechanism that already exists, the same shape as `ECON-001`
(`Complaints/103`).

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
`Complaints/104`).

## What already exists

`sim/world/labour_market.py`'s own module docstring (read directly) already
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
module is wired in (`Complaints/106`), since building supplier depth against
the current unwired, population-only `TRADE_DENSITY` classification would
mean deriving a refinement from a number the project already knows is wrong.

## Cross-references

`Complaints/103` (ECON-001) for the "do not add a blanket delay" pattern
this finding explicitly echoes. `Complaints/106` (ECON-004) for the labour-
market wiring this depends on. `Complaints/45` and `Complaints/48` (open)
both independently point at the same underlying gap (professions do not
move in response to scarcity) that `labour_market.py` exists to close.
