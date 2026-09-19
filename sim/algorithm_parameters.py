"""Algorithmic and computational parameters: numbers that control HOW a
computation runs, not what it claims about the simulated world.

    python3 sim/algorithm_parameters.py     print every parameter this
                                             module holds, with the outcome-
                                             sensitivity flag each one below
                                             states explicitly

WHAT BELONGS HERE. A fixed-point solver's damping factor, its convergence
tolerance, its iteration cap; a search's maximum period count. Gathered
from sim/solve_prices_core.py (the price solver's own damped-Jacobi loop)
and sim/world/labour_market.py (the labour-reallocation fixed point), the
two places in this project that run an iterative numerical search rather
than a closed-form calculation. The strongly-connected-components pass
sim/solve_prices_core.py's own resolvability check runs
(`_strongly_connected_components`, Tarjan's algorithm) was also examined
for this task and holds nothing that belongs here: it is deliberately
iterative rather than recursive specifically to avoid Python's recursion
limit on a large residual graph, which is a structural choice, not a
numeric parameter with a value someone might want to tune - there is
nothing to declare.

THE JUDGEMENT CALL THIS FILE MAKES EXPLICIT: NOT EVERY NUMBER HERE IS
OUTCOME-INERT, AND EACH ONE SAYS SO. Unlike sim/unit_conversions.py's own
conversions (which cannot change what a computation returns, only what
units it is stated in) and sim/presentation.py's own display values (which
cannot change a simulated result at all), SOME of the numbers below CAN
change a computed price or a labour allocation if pushed far enough - loosen
CONVERGENCE_TOLERANCE enough and the solver stops one step earlier, at a
price that has not fully settled; this is exactly the boundary sim/
constants.py's own registry draws around what counts as a modelling
commitment. The rule applied below, so a reader can tell at a glance rather
than having to reason it out fresh at each entry: a parameter is marked
OUTCOME-SENSITIVE if tightening or loosening it can change the VALUE a
converged run returns, and marked OUTCOME-INERT (SAFETY CEILING ONLY) if it
only changes how much room the search has before giving up, never what
answer it settles on once it has converged. A safety ceiling raised is pure
headroom; a tolerance loosened is a different definition of "close enough,"
which is a modelling choice by another name. Where a number is outcome-
sensitive, tuning it is equivalent to deciding how exact "solved" means,
which is a real decision this project should make on purpose, not by
leaving a magic number buried in solver code where nobody thinks to ask
whether it was ever chosen for a reason - which is exactly why the
stakeholder asked for these gathered in one place rather than left
scattered where changing one means grepping for it first.

WHY NOT sim/constants.py's OWN REGISTRY. These are not facts about the
world in CLAUDE.md SS3.1's sense - a damping factor is not a physical
constant, a biological parameter, an engineering estimate, an initial
condition, a calibration target, or (SS3.1's outright-forbidden case) a
hardcoded historical outcome; it is a property of the SEARCH, not of
Rome. Forcing one of `declare()`'s KINDS onto it would misdescribe it
either way: calling a damping factor `temporary_heuristic` implies a
future mechanism will DERIVE the right damping factor from history, which
makes no sense (a damping factor is not the kind of thing a historical
record could ever confirm or refute), and no other kind fits any better.
sim/constants.py's own `--burndown` is a progress bar for the MODEL - see
that module's docstring - and a solver's own knobs are not part of that
progress in either direction, so this file does not call `declare()` at
all, the same choice sim/presentation.py makes and for the same reason
(see that file's own NOT PART OF THE REGISTRY section).

WHY MOVED RATHER THAN LEFT AND MERELY GATHERED BY REFERENCE. The
stakeholder's stated reason ("if you want to tune them, they should be in
one place") means "one place to edit," not "one place to read about" -
gathering pointers here while the real assignment stayed in solve_prices_
core.py and labour_market.py would not let anyone tune anything from this
file. Each constant's own original comment moved WITH it, verbatim
(CLAUDE.md SS6: comments are load-bearing and this project does not strip
them), so nothing explaining WHY a value is what it is was lost in the
move - only WHERE it lives changed.

WHY THE OLD LOCATIONS STILL WORK UNCHANGED. sim/solve_prices.py and sim/
solve_prices_report.py both do `from solve_prices_core import (...,
DAMPING_FACTOR, CONVERGENCE_TOLERANCE, ...)` - a real, working import this
task did not want to edit two files, outside its own ownership boundary in
spirit if not in the letter of CLAUDE.md's file list, just to relocate a
number. sim/solve_prices_core.py therefore re-imports each moved name from
this file and keeps it bound at its own old attribute name (see that
file's own comment at the import), so `solve_prices_core.DAMPING_FACTOR`
still resolves exactly as it always did and neither sibling file needed to
change at all. sim/world/labour_market.py does the same for its own two
names, on the chance anything outside this file's own edits (a test, a
future caller) references `labour_market.MAXIMUM_REALLOCATION_PERIODS` or
`labour_market.CONVERGENCE_TOLERANCE_HOURS` directly.

HOW A CONSUMER USES ONE OF THESE. Imported fully qualified, `from
sim.algorithm_parameters import DAMPING_FACTOR`, the same convention sim/
unit_conversions.py and sim/presentation.py both use and for the same
reason (see sim/unit_conversions.py's own HOW A CONSUMER USES ONE OF
THESE section).
"""

# ============================================================================
# sim/solve_prices_core.py - the damped-Jacobi price solver
# ============================================================================
# Moved here verbatim, comments included, from sim/solve_prices_core.py's
# own "Damped Jacobi fixed-point iteration" section. See that file's own
# import of these five names for why its own module attributes still work
# unchanged.

# Damped Jacobi fixed-point iteration: every material's next price is a blend
# of its old price and what the current round's cheapest technique implies,
# so a technique flipping from one iteration to the next (a real possibility
# early on, when every price still carries the same seed guess) nudges the
# price rather than slamming it, which is what "damped" buys over a raw
# reassignment. 0.5 was not tuned against an outcome - it is the textbook
# midpoint - and the run below reports whether it actually converges rather
# than assuming a coefficient this arbitrary must be fine.
# OUTCOME-SENSITIVE: changes which price a converged run settles on when a
# cycle's arithmetic does not converge to a single fixed point regardless of
# damping (see solve_prices_core.py's own _component_is_productive) - for a
# component that DOES have one true fixed point, a different damping factor
# changes only how many iterations reaching it takes, not the fixed point
# itself; the sensitivity is real only for the components damping is there
# to steady in the first place.
DAMPING_FACTOR = 0.5

# OUTCOME-INERT (SAFETY CEILING ONLY): a component that would converge
# eventually converges identically whether the ceiling is 2,000 or 20,000
# iterations away; raising it only gives a slow-to-settle component more
# room before compute_resolvable_materials gives up and reports it as
# unresolved. Lowering it enough to cut off a component BEFORE it would
# have converged is the one way this stops being inert - see the loop at
# sim/solve_prices_core.py's own use of this name for where that boundary
# is checked.
MAXIMUM_ITERATIONS = 2000

# OUTCOME-SENSITIVE: this IS the definition of "close enough to call
# converged," so loosening it changes the price a run reports for any
# material that was still moving, however slowly, when the looser
# threshold would have already been satisfied. 1e-10 is tight enough that
# no price this project computes should ever be sensitive to it at that
# scale; the number itself is a definition of precision, not an estimate.
CONVERGENCE_TOLERANCE = 1e-10

# Every price starts equal, in labour-hours, before the first iteration.
# The seed value only matters for how many iterations convergence takes and
# for which technique looks cheapest in round one (see the joint-production
# note above); it does not bias where the fixed point ends up, because a
# fixed point is defined by the equations agreeing with each other, not by
# where the search started.
# OUTCOME-INERT for any component that converges to a unique fixed point
# (the whole point of the comment above); the docstring's own hedge -
# "which technique looks cheapest in round one" - is the one channel a
# different seed could matter through, if a tie in round one were ever
# broken differently by a different starting guess, which 1.0 chosen
# uniformly for every material avoids by construction (no material starts
# ahead of any other).
INITIAL_PRICE_GUESS_HOURS = 1.0

# Used only by the cycle-productiveness test in compute_resolvable_materials:
# a price the restricted iteration crosses only if the component is growing
# without bound rather than converging. Not a plausible real price for
# anything - see _component_is_productive.
# OUTCOME-INERT (SAFETY CEILING ONLY): this is a divergence DETECTOR, not a
# price input - it only decides how early an actually-diverging component is
# flagged as such, never what a converging component's own price comes out
# to.
GROWTH_BOUND_HOURS = 1e9

# ============================================================================
# sim/world/labour_market.py - the labour-reallocation fixed point
# ============================================================================
# Moved here verbatim, comments included, from sim/world/labour_market.py's
# own "THE FIXED POINT: REPEAT THE STEP UNTIL THE ALLOCATION STOPS MOVING"
# section. See that file's own import of these two names for why its own
# module attributes still work unchanged.

# An algorithmic ceiling on the search, exactly like sim.solve_prices.py's
# own MAXIMUM_ITERATIONS - not a claim about how long a real reallocation
# takes (that claim is THE FRICTION section's job), only a guard against a
# pathological input (a proximity of exactly zero everywhere, say) looping
# forever without ever registering as stabilised.
# OUTCOME-INERT (SAFETY CEILING ONLY): the same reasoning as solve_prices_
# core.py's own MAXIMUM_ITERATIONS above - a real allocation that would
# stabilise does so at the same allocation whether given 500 periods or
# 5,000 to do it in.
MAXIMUM_REALLOCATION_PERIODS = 500

# Absolute hours, not a ratio - a trade required at 0.0 hours must be able
# to reach exactly 0.0 tightness, which a ratio-based tolerance cannot
# express cleanly at that boundary. Used for BOTH stopping conditions
# `solve_to_stable_allocation` checks - see its own docstring.
# OUTCOME-SENSITIVE: the same reasoning as solve_prices_core.py's own
# CONVERGENCE_TOLERANCE above - this defines "stabilised," so loosening it
# reports a workforce as settled while real hours are still moving between
# trades.
CONVERGENCE_TOLERANCE_HOURS = 1e-6


def _print_report():
    entries = (
        ("DAMPING_FACTOR", DAMPING_FACTOR, "OUTCOME-SENSITIVE"),
        ("MAXIMUM_ITERATIONS", MAXIMUM_ITERATIONS, "safety ceiling only"),
        ("CONVERGENCE_TOLERANCE", CONVERGENCE_TOLERANCE, "OUTCOME-SENSITIVE"),
        ("INITIAL_PRICE_GUESS_HOURS", INITIAL_PRICE_GUESS_HOURS,
         "outcome-inert (see docstring)"),
        ("GROWTH_BOUND_HOURS", GROWTH_BOUND_HOURS, "safety ceiling only"),
        ("MAXIMUM_REALLOCATION_PERIODS", MAXIMUM_REALLOCATION_PERIODS,
         "safety ceiling only"),
        ("CONVERGENCE_TOLERANCE_HOURS", CONVERGENCE_TOLERANCE_HOURS,
         "OUTCOME-SENSITIVE"),
    )
    print("ALGORITHM PARAMETERS - how a computation runs, not what it claims")
    print("=" * 72)
    for name, value, sensitivity in entries:
        print("   %-30s %-12s %s" % (name, value, sensitivity))


if __name__ == "__main__":
    _print_report()
