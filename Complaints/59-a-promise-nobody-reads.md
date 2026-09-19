# Population-raising technology still writes to a number nothing reads

## What the player saw

Several food and population technologies are described, in their own notes
and in the tree, as raising population and thereby enlarging the labour
market. In play, and confirmed by reading the code, these effects still only
ever queue a change into `_pop_scale_base`, a scalar the live `pop_scale` and
`wage_index` properties no longer read at all. The promise the tech
descriptions make - better food, sanitation, etc. grow the country and ease
labour scarcity - is not kept by the live demographic model for the
technologies that still use this path.

## Verified against current code

Confirmed, and the code already says so about itself, at length.

`apply_tech_effects()` moved from `society.py` to
`sim/engine/society_adoption.py:96`. Its `population`-field branch
(`society_adoption.py:129-165`) still does exactly what the player
describes:

    if k not in self.DISEASE_BURDEN_TECH_IDS:
        self._pop_tech_pending.append(
            (delta / self.POP_TECH_RAMP_YEARS, self.POP_TECH_RAMP_YEARS))

`_advance_food_diffusion_population()` moved to
`sim/engine/society_diffusion.py:469`. It still does:

    self._pop_scale_base += add

Both write sites feed the same target, drained in `core.py`'s
`_demographic_recovery()` (`core.py:1420-1426`):

    if self._pop_tech_pending:
        still = []
        for per_year, years_left in self._pop_tech_pending:
            self._pop_scale_base += per_year
            ...

`pop_scale` and `wage_index`, both in `core.py`, are computed properties over
`self.population.total` (the real age-cohort model) and explicitly do
**not** read `_pop_scale_base`. The comment directly above `pop_scale`
(`core.py:701-713`) states this in its own voice:

    # DELIBERATELY NOT `self._pop_scale_base`: `_pop_scale_base` is
    # incremented by population-raising technology and food-technology
    # diffusion (`_pop_tech_pending`/`_advance_food_diffusion_population`,
    # society.py), but those two write sites do not yet feed
    # `self.population` itself (open design question - see docs/
    # architecture/WIRING_MILESTONE_4.md SS1.3).

A search for every reader of `_pop_scale_base` confirms the write-only
shape directly:

    grep -rn "_pop_scale_base" sim/engine/*.py sim/tests/*.py

turns up two production write sites (the ones above), the declaration
site, and four comments narrating the fact that it is inert - and no
production *read* site at all. The only readers are `sim/tests/` files
(`test_craftsmen_wording.py`, `test_demographics_and_plague.py`,
`test_disease_burden_wiring.py`) that assert the scalar itself still
*moves* when these mechanisms fire, i.e. tests written to keep the dead
write path alive and correct, not to prove it does anything to the live
game.

So this is not a hidden regression: it is a known, tracked, explicitly
`docs/architecture/WIRING_MILESTONE_4.md` SS1.3-labelled open design
question, and the code comments are honest about it wherever the mechanism
appears. What is not yet true is the player-facing claim in the tech notes
and in the game's own framing ("better food, sanitation and the like raise
the population, and that feeds back") for the technologies still on this
path.

Status: **confirmed in current code, and already self-labelled as
unfinished wiring** - filed anyway per this audit's instructions, so the
record shows it was independently checked rather than only cited from the
architecture doc.

One caveat worth stating precisely, because CLAUDE.md SS3.4 requires
distinguishing a labelled heuristic from an unlabelled one: `WIRING ONE`
(`Complaints/48-technology-cannot-stop-people-dying-young.md`) already gave
eight disease/sanitation technologies (`Sim.DISEASE_BURDEN_TECH_IDS`) a
*real*, live effect via `_disease_burden()`, which reads `self.has(...)`
every year rather than queuing into `_pop_scale_base` at all - the
`apply_tech_effects` branch quoted above explicitly skips those eight for
exactly this reason (`if k not in self.DISEASE_BURDEN_TECH_IDS`). This
complaint is about the remaining five food-effect technologies that still
carry a `population` field and still queue into the dead path: crop
rotation, three-field rotation, the seed drill, New World crops, and
canning (named in the same comment block, `society_adoption.py:158-161`).

## Cross-references

No existing open complaint names this specific write-only-scalar shape; it
overlaps in spirit with `Complaints/48` (the disease-burden wiring, already
closed/fixed) as the piece of the same milestone that was **not** finished
the same way. Also adjacent to `Complaints/58` (this same batch): both are
symptoms of `pop_scale`/the labour market not fully reflecting
`self.population`'s live state, but from opposite directions - `58` is
about a *floor* that stops a number from falling; this is about an
*addition* that never reaches the number that would need to rise.

## What would resolve it

The `wage_index` comment is explicit that the cheap fix is wrong: "Do not
simply make `wage_index` read `_pop_scale_base`... unless the live
population moves with the trend." That is correct and this complaint does
not dispute it - reading a scalar that has drifted independently of the
age-cohort model would create a *worse* inconsistency (a labour market that
thinks the population is larger than the cohort model, rather than smaller,
as `58` documents).

The player's own suggested fix is the right shape and is compatible with
CLAUDE.md SS3.1 (it does not hardcode an outcome; it routes an already-tree-
authored effect weight into the mechanism the tree already has for
population, rather than inventing a new one): translate what these five
technologies' `population` deltas mean into actual cohort-level parameters -
lower age-specific mortality, higher nutrition-dependent fertility/survival,
or a higher food-supported carrying capacity that the demography model's own
step function reads - rather than maintaining `_pop_scale_base` as a second,
disconnected population number. `docs/architecture/WIRING_MILESTONE_4.md`
SS1.3 already frames this as the open question; this complaint is evidence
from an independent playtest that the gap is visible in practice, not only
in the architecture doc.

## The invariant

    a technology whose _TECH_EFFECTS.json entry carries a `population` field
    should, once RAMP_YEARS has elapsed, measurably change self.population's
    own trajectory (births, deaths, or carrying capacity) - not only a
    scalar nothing downstream reads.

This is harder to write as a single-line assertion than the other findings
in this batch, because it is a "does this ever do anything" property rather
than a bound. The nearest testable version: assert that `_pop_scale_base`
has at least one live reader in `core.py`/`society*.py` production code
(not `sim/tests/`), which today is a `grep` a CI job could run rather than
a full behavioural test.
