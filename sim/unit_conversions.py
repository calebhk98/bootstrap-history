"""Unit conversions: definitional numbers, not modelled ones.

    python3 sim/unit_conversions.py     print every conversion this module
                                         declares, the same report format
                                         sim/constants.py itself prints

WHAT BELONGS HERE, AND WHY IT IS SEPARATE FROM sim/constants.py'S OWN
FORMULA-ADJACENT DECLARATIONS. sim/constants.py's own module docstring
argues, correctly, that a number wants to live beside the formula that
uses it, because moving it away loses the one thing that makes it
defensible - the paragraph explaining why it is that number. A unit
conversion has no such paragraph to lose: `KILOGRAMS_PER_TONNE = 1000.0`
is defensible from its own name and nothing else, the way `PERCENT_SCALE
= 100.0` or `METERS_PER_KILOMETER = 1000.0` are. There is no missing essay
a reader needs from the call site, so sim/constants.py's central argument
against centralising simply does not apply to this category, and this
module exists to hold exactly it - and only it.

WHY A NEW MODULE RATHER THAN sim/world/shared_constants.py, WHICH ALREADY
DOES THIS FOR sim/world/. Two reasons. First, scope: shared_constants.py's
own docstring states its boundary explicitly ("Every constant declared
here is a sim/world/ domain fact... no dependence on sim/engine/") and a
unit conversion is needed on both sides of that boundary - sim/engine/
economy_materials.py converts kilograms to tonnes exactly as often as
sim/world/deposits.py does, for the same reason (both work in kilograms
internally and report in tonnes/year). Putting mass and distance
conversions in a file that has declared itself sim/world/-only would
either violate that boundary or force a second, engine-side copy of the
exact same facts - the identical drift shared_constants.py exists to
prevent, one level up. Second, kind: shared_constants.py's own entries are
measured or estimated physical and biological facts (a calorie
requirement, a labour elasticity) that could in principle be revised by
better data; `1000.0` grams per kilogram cannot be revised by anything,
ever - it is a definition, not an estimate under a source and a
confidence grade in the same sense the rest of the registry uses those
words. Keeping the two apart means shared_constants.py's own "which
physical facts is more than one domain claiming independently" audit
never has to skip over entries that were never really in question.

THE ALTERNATIVE THIS MODULE REJECTS: DECLARING THE SAME NAME LOCALLY IN
EVERY CONSUMING FILE. `declare()` already refuses to register the same
name twice with two different values (see sim/constants.py's own
docstring), so nine independent `KILOGRAMS_PER_TONNE = declare(
"KILOGRAMS_PER_TONNE", 1000.0, ...)` call sites, one per consuming file,
would in fact be safe against VALUE drift - any file that got the number
wrong would fail importing at startup, not silently disagree. That was
seriously considered, and rejected anyway, for two reasons neither of
which is drift: (1) it means retyping the same one-line justification
nine times, which is not a paragraph worth defending nine times over, and
a future editor fixing a typo in one copy has eight more to find by hand;
(2) sim/world/shared_constants.py already established the "one shared
module, both directions import it" shape for exactly this kind of
cross-domain fact in this codebase, and a second shape solving the
identical problem a different way, right next to the first, would be its
own small inconsistency for the next reader to puzzle over. A single
declaration, imported everywhere, is simply less to maintain than nine
declarations `declare()`'s own dedup check merely PROTECTS from disagreeing.

WHY kind="physical_constant" RATHER THAN A NEW KIND. sim/constants.py's
own KINDS section does not list anything for "true by construction,
confidence beyond A." A new kind was considered and rejected: this
project's engine already has a working precedent, not a hypothetical one -
sim/engine/economy_electricity.py's HOURS_PER_YEAR (8,760.0, "365 days x 24
hours") and sim/world/demand.py's own DAYS_PER_YEAR (365.25, a calendar
fact) are BOTH already declared `kind="physical_constant", confidence="A"`,
and both are exactly this category: numbers fixed by definition rather
than by measurement. Every declaration below follows that same, already-
established precedent rather than inventing a parallel one. Definitional
exactness is captured by `confidence="A"` (the strongest grade the
registry already has), not by a new `kind` - a distinction sim/tests/,
`--burndown`'s own reasoning, and every future caller would otherwise have
to learn a whole new category to understand, for a difference the registry
can already say with the confidence grade alone.

WHAT DOES NOT BELONG HERE. A conversion used at exactly one call site,
where a bare literal is already perfectly readable and does not repeat
anywhere else, does not need to move here just because it happens to be a
unit conversion - this task's own report names two examples deliberately
left alone: sim/world/transport.py's GRAVITATIONAL_ACCELERATION_M_PER_S2
(already its own `declare()`, next to the one function that uses it, and
not touched by this module) and a rounding-to-the-nearest-hundred step in
sim/engine/economy_freight.py's own nitre-bed sizing, which divides and
re-multiplies by 100 to pick a round purchase quantity rather than to
convert a fraction to a percentage - the same number, a different job,
and CLAUDE.md's own naming section makes the identical argument for
identifiers generally. Formatting widths, retry counts and "how many rows
to show" are a different kind of number entirely - see sim/presentation.py
for those - and neither belongs on kind="physical_constant" just because
both are inputs to arithmetic.

HOW A CONSUMER USES ONE OF THESE. Imported fully qualified, `from
sim.unit_conversions import KILOGRAMS_PER_TONNE`, from EVERY caller -
sim/world/ and sim/engine/ files alike - never the bare `from
unit_conversions import ...` spelling sim/engine/ files use for sibling
engine modules. This mirrors sim/engine/core.py's own documented choice to
import sim/world/shared_constants.py fully qualified rather than bare (see
that file's own "Imported FULLY QUALIFIED" comment): a bare import from
sim/engine/ would load this file a SECOND time under a different
sys.modules key (`unit_conversions` vs `sim.unit_conversions`), and while
`declare()`'s own dedup keeps that safe (same name, same value, no error),
it would still mean every conversion below gets declared twice into the
registry for no reason. One spelling, one module object, one declaration
each - the same discipline core.py already established for
shared_constants.py, extended here rather than repeated a third way.

CONVERTING kg <-> g <-> TONNES: EACH DIRECTION KEEPS ITS OWN LITERAL, ON
PURPOSE. KILOGRAMS_PER_TONNE (1000.0) and GRAMS_PER_KILOGRAM (1000.0) share
a value but are NOT the same fact - a caller converting tonnes to kilograms
and a caller converting kilograms to grams are making two different claims
that happen to use the same number, exactly the way sim/world/
shared_constants.py's own module docstring already accepts two constants
sharing a value when they are not interchangeable. KILOGRAMS_PER_GRAM
(0.001) is the reciprocal of GRAMS_PER_KILOGRAM and is declared directly
rather than computed as `1.0 / GRAMS_PER_KILOGRAM`, so that a call site
migrating from a bare `* 0.001` literal keeps the exact same floating-point
operation (multiplication by the same literal, not division by its
reciprocal) - see this module's own FLOATING POINT note below for why that
distinction is load-bearing here in a way it would not be in ordinary code.

FLOATING POINT: WHY EVERY MIGRATED CALL SITE KEEPS ITS ORIGINAL OPERATION.
`x / 1000.0` and `x * 0.001` are mathematically the same number but are NOT
guaranteed to be the same float for every `x` - 0.001 is not exactly
representable in binary, so multiplying by the (also inexact) rounded
reciprocal can differ from dividing by the exact literal in the last bit,
for some values of `x`. sim/perf_fingerprint.py's byte-identical check
exists to catch precisely this class of change, so every call site this
task's report lists as migrated keeps whichever operation (multiply or
divide) the original bare literal was already part of, using whichever of
this module's constants makes that operation read correctly - never the
reverse operation on a reciprocal, even when the reciprocal is also
declared here for a different call site's own original direction.
"""
import os
import sys

# Guarded, idempotent, and needed only for `python3 sim/unit_conversions.py`
# itself - run directly, only sim/ (this file's own directory) lands on
# sys.path for free, not the repository root `from sim.constants import
# declare` needs. Every OTHER entry point that reaches this file (core.py,
# commodities.py, and the rest) has already put the repository root on
# sys.path by the time it imports this module - see this file's own HOW A
# CONSUMER USES ONE OF THESE section - so this guard is a no-op for them.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sim.constants import declare

# ============================================================================
# MASS
# ============================================================================

KILOGRAMS_PER_TONNE = declare(
    "KILOGRAMS_PER_TONNE", 1000.0,
    kind="physical_constant",
    unit="kg/tonne (metric ton)",
    source="SI definition: 1 tonne = 1000 kg, exact.",
    confidence="A",
    why="Every material flow in sim/world/ and sim/engine/ is tracked "
        "internally in kilograms (the tech tree's own *_kg material keys) "
        "but reported, priced and traded in tonnes/year - this is the one "
        "number that turns one into the other, wherever that happens.")

GRAMS_PER_KILOGRAM = declare(
    "GRAMS_PER_KILOGRAM", 1000.0,
    kind="physical_constant",
    unit="g/kg",
    source="SI definition: 1 kg = 1000 g, exact.",
    confidence="A",
    why="Converts a *_g tech-tree material quantity (byproduct metals "
        "measured in grams, ammunition mass per shot) into kilograms by "
        "DIVISION, the direction sim/world/military_logistics.py's own "
        "ammunition-mass arithmetic already used as a bare literal.")

KILOGRAMS_PER_GRAM = declare(
    "KILOGRAMS_PER_GRAM", 0.001,
    kind="physical_constant",
    unit="kg/g (reciprocal of GRAMS_PER_KILOGRAM)",
    source="SI definition: 1 g = 0.001 kg, exact. Declared directly rather "
           "than computed as 1.0 / GRAMS_PER_KILOGRAM so a call site that "
           "multiplies by this keeps the exact multiplication its original "
           "bare 0.001 literal already was - see this module's own "
           "FLOATING POINT section.",
    confidence="A",
    why="Turns a *_g-suffixed quantity into a kilogram-equivalent by "
        "MULTIPLICATION - the direction sim/world/demand.py's and "
        "sim/world/labour_market.py's own (until this task, independently "
        "declared) _KG_EQUIVALENT_PER_UNIT_SUFFIX dictionaries already "
        "used, mapping a material key's unit suffix to the multiplier that "
        "makes every material comparable by mass regardless of which unit "
        "its own tech-tree entry happens to be stated in.")

# ============================================================================
# DISTANCE
# ============================================================================

METERS_PER_KILOMETER = declare(
    "METERS_PER_KILOMETER", 1000.0,
    kind="physical_constant",
    unit="m/km",
    source="SI definition: 1 km = 1000 m, exact.",
    confidence="A",
    why="sim/world/transport.py's freight physics work in SI base units "
        "(newtons, joules, metres) internally because that is what the "
        "tractive-force and lifting-work equations are stated in, but "
        "every route this project prices is a distance in kilometres - "
        "this is the number every one of those physics functions applies "
        "to a route's own km figure before doing any actual mechanics.")

# ============================================================================
# FRACTION <-> PERCENT
# ============================================================================

PERCENT_SCALE = declare(
    "PERCENT_SCALE", 100.0,
    kind="physical_constant",
    unit="percentage points per unit fraction (dimensionless)",
    source="Definition of percent: per hundred, exact.",
    confidence="A",
    why="Every fraction this project computes internally (a budget share, "
        "a wage premium, a scandal hazard, a market-saturation gap) is "
        "reported to a player or a report reader as a percentage - this is "
        "the number that crosses between the two, in whichever direction "
        "(multiply a fraction to display it, or divide a stored percentage "
        "back to the fraction arithmetic actually needs) a given call site "
        "requires. Genuinely the same operation whether the fraction feeds "
        "a further computation (sim/engine/core.py's wage-shortfall "
        "recovery) or only a printed message - see this module's own "
        "docstring for why a display-only use is still a unit conversion, "
        "not a presentation parameter.")


def _print_report():
    print("UNIT CONVERSIONS - definitional, not modelled")
    print("=" * 72)
    from sim.constants import REGISTRY
    for name, meta in REGISTRY.items():
        if meta["declared_in"] not in ("sim.unit_conversions", "__main__",
                                        "unit_conversions"):
            continue
        print("   %-24s %-10s %-24s conf %s"
              % (name, meta["value"], meta["unit"], meta["confidence"]))


if __name__ == "__main__":
    _print_report()
