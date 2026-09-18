# The game cannot express the most important thing it simulates

**Status (project-wide audit, 2026-09-18): RESOLVED, verified - but in an
UNCOMMITTED working-tree change at the time of this audit.** `_disease_burden()`
(`sim/engine/core.py`) is defined and is passed into
`self.population.step(..., disease_burden=self._disease_burden())`. This
wiring was present in the live working tree (another agent's in-progress
edit, one of several running concurrently in this checkout) but had not yet
been committed. Re-check that it has actually landed before relying on it.
See `docs/architecture/STATE_OF_THE_PROJECT.md`.

Found by the stakeholder, who put the whole argument in one paragraph:

> We have been building the demographics based on historical society. But
> that's not what we need to do. Historically the population has been stable
> and grows slowly. But that's not because of humans, that's because of
> food. [...] Historically was limited by food and had disease, but we are
> showing here that without food limits and without disease or child deaths,
> it's still not growing well.

They are right, and the measurement is unambiguous.

## What was wrong

    mortality multiplier   ratio 1.0 -> 1.0000   ratio 5.0 -> 1.0000   ratio 1000 -> 1.0000
    SURVIVAL_TO_WORKING_AGE = 0.5, a plain constant

Mortality could only ever go UP. With literally unlimited food, half of all
children still never reached working age. Fifty per cent child mortality is a
consequence of pre-industrial disease and undernutrition, not a biological
constant of the species; with clean water and germ theory it is nearer 5%.

And the technology side could not reach it either. `_TECH_EFFECTS.json`
carries eight medical entries - germ theory, sanitation and antisepsis,
aqueducts and latrines, quarantine, vector control, obstetric antisepsis,
asepsis, vaccination. `sanitation_antisepsis`'s own note names the mechanism
exactly: "Boiled water and handwashing cut exactly the childhood diarrhoeal
and puerperal mortality that kept pre-modern populations flat for
centuries." It then models that as `population: 0.02` - a two per cent
adjustment to a population LEVEL rather than a change to a mortality RATE.
And that value flows into `Sim._pop_scale_base`, which the milestone-4 work
established is read by nothing.

So a project whose entire subject is bootstrapping a civilisation to a modern
frontier could not express the single most important human consequence of
doing it: that people stop dying young.

## What it does now

Disease burden is a second axis beside nutrition, 1.0 being the full
pre-industrial infectious environment already baked into every existing
constant and 0.0 being clean water, sanitation, germ-theory hygiene and
vaccination all present. Measured:

                                                    growth
    unlimited food, pre-industrial disease         +2.209%/year
    unlimited food, modern disease                 +5.661%/year
    exact subsistence, pre-industrial disease      +0.086%/year
    exact subsistence, modern disease              +2.100%/year

The last row is the one worth looking at twice: with no more food than bare
subsistence, removing disease alone takes a population from barely holding
its own to 2.1% a year. That is the epidemiologic transition, and the model
can now show it.

## The calibration trap, which the stakeholder caught twice

The first framing given to the agent named the Hutterites' 4.1% a year as the
target for "unlimited food, no disease". The stakeholder rejected it:

> No, unlimited food and no disease would go past Hutterites. They still had
> limited food, land, and had disease. 4% thus is the floor.

Correct. The Hutterites farmed finite land, split colonies when they outgrew
it, and lived through the pre-antibiotic early twentieth century. Their rate
is the highest OBSERVED natural increase, achieved with every constraint
still binding - a floor for the unconstrained case, not a ceiling. The real
frame is 4.1% observed floor, 9.06% biological bound (zero mortality, a birth
every year with no gestation interval), and the answer in between. 5.66%
sits there.

AND THE SAME ERROR WAS ONE LEVEL DOWN, which is why this is worth recording
as a method note rather than just a number. The fertility ramp's own ceiling
was anchored to the Hutterite total fertility rate. So a disease-only fix
landed at 4.03% - reproducing the Hutterite rate BY CONSTRUCTION, because the
constant that capped it was derived from the Hutterites in the first place.
The new mechanism looked like it had failed when the real limit was a
calibration anchored to a constrained population and then used as if it were
a species maximum. Anchoring a bound to an observation only works if the
observation was itself unbounded.

## What is still not done

The engine does not pass a disease burden. `Sim` calls `Population.step`
without one, so every game still runs at the pre-industrial default and the
eight medical technologies still do nothing. The wiring is small and
specified: sum the `population` weights of whichever of those eight are
unlocked (they total exactly 0.15), and pass
`1.0 - unlocked_weight / 0.15`. That reuses the tree author's own relative
weights - half-size for germ theory as an idea, full size for each practice -
and needs no schema change.

Until that lands, the unshocked rome_100ad century stays at 85.51%, unchanged
and provably so: every new formula is the identity at burden 1.0. The
stakeholder's bar is that it should exceed 100%, and the rest of that gap is
`Complaints/47` - one weather draw for a whole continent, which pooling
across regions takes from 76% to 98%.

## Sourcing, and where it is weak

Child survival's modern ceiling of 0.95 comes from UN IGME under-five figures
for Niger and Uganda, the same fastest-growing populations this complaint
argues from, and the child mortality floor multiplier is then DERIVED from
those two sourced points rather than chosen. The working-age and elderly
floors are judgement at confidence D, directionally supported by
tuberculosis, typhoid and dysentery's documented dominance among adult deaths
but with no clean isolating study behind them. The fertility uplift uses the
sub-Saharan infertility belt, which is sexually transmitted infection causing
sterility - a real documented effect and a related rather than identical
mechanism to general sanitation. All three are labelled and are the first
things to replace.
