#!/usr/bin/env python3
"""Solve for the price of every material from physical structure, not a book.

    python3 sim/solve_prices.py                        every price, in labour-hours
    python3 sim/solve_prices.py --why iron_bar_kg       full recursive cost breakdown
    python3 sim/solve_prices.py --compare               computed price vs prices.json,
                                                         as a ratio, worst disagreement first

STANDALONE AND READ-ONLY. This tool computes prices; nothing in `sim/engine/`
reads them yet. `data/prices.json` still runs the game. That wiring is a
separate, later change - this file only has to prove the calculation works
and say honestly where it does not.

THE MECHANISM, from docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md Part 2:
a material's price is what it costs to make one unit of it -

    price_of(material) =  sum over inputs of
                              quantity_per_unit(material, input) * price_of(input)
                        +  sum over trades of
                              hours_per_unit(material, trade) * wage_of(trade)
                        +  rent_per_unit(material)

Every input price on the right is defined by the same equation, so this is a
system of equations rather than a lookup, solved for the fixed point where
every price is consistent with every other. `data/production/` supplies
`quantity_per_unit` (its `inputs`) and `hours_per_unit` (its `labour_hours`)
for 182 materials once byproducts are counted; `data/prices.json`
`wage_rates_denarii_per_hour` supplies the wage ratios. Nothing here is a
lookup of a finished price - only of the physical recipe and the relative
wage, which is what the mechanism is allowed to take as given.

NUMERAIRE: one hour of UNSKILLED labour, per the design doc's Part 2.1. The
`labourer` trade is the unskilled one - it is the cheapest trade in the wage
table, and entries in data/production/ that need generic unskilled effort
(spinning thread, moving ore) already book it to `labourer` rather than to a
craft. Every wage is expressed as a ratio against `labourer`'s rate, so
`wage_of("labourer") == 1.0` by construction and every price this script
prints is "how many hours of unskilled labour", never denarii.

RENT_IS_ZERO. Extracted materials (ore at the pit head, timber in the forest,
salt in the pan) have no cost of production - nature made them, nobody's
labour did - so their price should be their labour cost plus a RENT on the
deposit or field, set by the quality of the worst source still worth working
(the extensive margin). That margin needs geography (competing sites of
different quality) and demand (something bidding for the marginal one), and
this branch has neither: `data/production/` is a flat recipe list with no
notion of "this ore body" versus "that poorer one". So this round sets
`rent_per_unit(material) = 0.0` for every extracted material, unconditionally,
and says so here rather than burying it in a comment nobody reads. Zero rent
is not "no answer" - it is the honest lower bound: whatever the true price is,
it is at least the labour it takes, and this is that floor. Tag: HEURISTIC,
not a physical fact, tracked against Milestone 1's provenance ledger.

ENERGY_MJ IS NOT PRICED. Ten entries in data/production/ carry a nonzero
`energy_mj` - process heat or mechanical work not already paid for by a fuel
in `inputs` (electrolytic aluminium is the biggest, at 46,000 MJ per tonne,
which is the real DC energy cost of Hall-Heroult reduction and is why the
metal stayed a curiosity until cheap hydroelectricity existed). Neither the
design doc's formula nor data/production/_SCHEMA.md's own "how the price
falls out" section gives energy a price - both name only inputs, labour and
rent - and inventing a denarii-per-megajoule conversion (say, by pegging it to
coal's calorific value) would be exactly the kind of tuned heuristic this
project is trying to stop adding, with no physical anchor for which fuel and
which efficiency to assume. So this script leaves `energy_mj` uncosted and
reports which materials it affects, rather than folding in a number nobody
asked for. Every price for those ten materials is consequently a LOWER BOUND,
understating the true cost by whatever that energy would add. Tag: GAP, not a
heuristic - there is no stand-in value being used, the term is simply absent.

CHOICE OF TECHNIQUE AND JOINT PRODUCTION, handled by the same rule. Several
materials have more than one recipe (salt from brine or from solar pans;
zinc by direct smelting or by electrolysis) and several recipes yield more
than one material (smelting galena yields lead AND silver; roasting coal
yields carbon AND coal tar). Both are the same underlying question - how much
of a process's cost belongs to a given unit of a given output - and this
script answers both with one mechanism: cost the whole process, then split
that cost across its outputs in proportion to each output's own current price
times its quantity (net-realisable-value allocation, the standard treatment
of joint cost in cost accounting). A single-output recipe is just the case
where one output holds 100% of the value share. Where a material has several
candidate recipes, its price is the CHEAPEST of what each recipe implies for
it - the solver picks the technique a rational producer would pick at current
prices, and because prices move as the solve iterates, technique choice
iterates alongside it exactly as the design doc's Part 2.1 says it must.

JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR ARE NOT REALLY PRICED, AND
THIS SCRIPT SAYS SO RATHER THAN PRINTING THE NUMBER AS IF THEY WERE. Running
the solve and inspecting every joint-production recipe shows the same thing
every time: a MINOR co-product (silver from lead smelting, platinum from
nickel refining, germanium and indium from zinc electrolysis, coal tar from
coke-making) converges to EXACTLY the same price per physical unit as its
DOMINANT co-product, no matter how the price search is seeded. That is not a
finding about silver and platinum being cheap - it is `recipe_cost_and_
allocation`'s net-realisable-value split degenerating to a plain mass split
whenever nothing else in the system independently prices the minor output.
The algebra: at a fixed point, value_i = quantity_i * price_i for every
output of one recipe, and the value split is itself computed FROM those same
prices, so "every output priced identically per unit" is a self-consistent
answer whenever no other equation constrains it - and for these five
materials, nothing else does, because their only OTHER recipe (if any, like
silver's direct patio-amalgamation route) turns out more expensive at the
degenerate price and is never selected. This is the textbook joint-production
result from classical price theory: a system with one process and two goods
has one equation short of pinning down both prices, and closing the gap needs
demand, or a second independent process that actually binds - this dataset
has neither yet. `minor_joint_byproducts_are_unanchored` finds exactly this
set by checking, on the CONVERGED, CHOSEN recipe for each material, whether
it is a joint recipe where this material holds under half the batch's value.
Flagged materials print with a `(*)` and a named warning, in every mode -
their number is a real lower bound on cost (the batch really did cost that
much to run) but not a real relative price, and treating it as one would be
worse than saying plainly that this round cannot separate it out.

CYCLES ARE EXPECTED BY THE ITERATION AND REFUSED BY THE PASS IN FRONT OF IT,
WHICH IS A DEFECT - see Complaints/31 and sim/tests/test_price_solver_cycles.py.
Iron needs charcoal; charcoal needs timber and labour; an axe needs an iron
edge. The damped fixed-point iteration below handles that the same way it
handles everything else, by converging to the prices where the equations
agree rather than requiring an acyclic graph. What the iteration CANNOT do is
resolve a material whose every path back through its own inputs never bottoms
out at something with no inputs (an extracted material, ultimately just
labour and zero rent) - a genuine hole in the data - and
`compute_resolvable_materials` below is the separate graph pass that finds
those before any numeric work starts.

That pass is currently STRICTER THAN IT SHOULD BE. It adds a recipe's outputs
only once every input is already resolvable, which is a topological ordering,
so it refuses every genuine cycle too - the axe-and-iron example in the
paragraph above included, and a material listing itself among its inputs
(seed corn) worst of all, since that takes everything downstream with it. The
right test is productiveness (spectral radius under 1 / Hawkins-Simon), not
reachability. This is latent rather than active: the dataset is acyclic today
and the solver reports no unresolved material. It is written down here
because the fix for it is a prerequisite for capital goods and for seed corn,
not because it is breaking anything now.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simulator                                # noqa: E402  (see sys.path above)
from validate_production import load_production, materials_the_tree_consumes  # noqa: E402

NUMERAIRE_TRADE = "labourer"

# Damped Jacobi fixed-point iteration: every material's next price is a blend
# of its old price and what the current round's cheapest technique implies,
# so a technique flipping from one iteration to the next (a real possibility
# early on, when every price still carries the same seed guess) nudges the
# price rather than slamming it, which is what "damped" buys over a raw
# reassignment. 0.5 was not tuned against an outcome - it is the textbook
# midpoint - and the run below reports whether it actually converges rather
# than assuming a coefficient this arbitrary must be fine.
DAMPING_FACTOR = 0.5
MAXIMUM_ITERATIONS = 2000
CONVERGENCE_TOLERANCE = 1e-10

# Every price starts equal, in labour-hours, before the first iteration.
# The seed value only matters for how many iterations convergence takes and
# for which technique looks cheapest in round one (see the joint-production
# note above); it does not bias where the fixed point ends up, because a
# fixed point is defined by the equations agreeing with each other, not by
# where the search started.
INITIAL_PRICE_GUESS_HOURS = 1.0


def wage_ratios_by_trade(prices_json):
    """{trade: hours of unskilled labour one hour of this trade is worth}.

    `prices.json`'s wage table is denarii per hour, one static number per
    trade with no notion of unskilled labour as a unit. Dividing every rate
    by the unskilled (`labourer`) rate turns it into what the design doc
    calls the numeraire: `wage_of("labourer")` is 1.0 by construction, and
    every other trade is stated as how many labourer-hours it is worth,
    which is a ratio the denarii happen to cancel out of.
    """
    wage_table = prices_json["wage_rates_denarii_per_hour"]
    unskilled_rate = wage_table[NUMERAIRE_TRADE]["rate"]
    return {trade: entry["rate"] / unskilled_rate
            for trade, entry in wage_table.items()
            if not trade.startswith("_")}


def build_producers_index(production_entries):
    """{material_key: [recipe_id, ...]} - every recipe that yields it.

    A recipe's id is not always the material it makes: `salt_solar_kg` and
    `salt_brine_kg` both yield `salt_kg`, and `zinc_electrolytic_kg` yields
    `zinc_kg` plus two byproducts that have no recipe of their own. Building
    this index from `outputs` rather than assuming id-equals-output is what
    makes both choice of technique and joint production visible at all - see
    the module docstring.
    """
    producers_of = collections.defaultdict(list)
    for recipe_id, entry in production_entries.items():
        for material_key in (entry.get("outputs") or {}):
            producers_of[material_key].append(recipe_id)
    return dict(producers_of)


def compute_resolvable_materials(production_entries, producers_of):
    """Which materials can, even in principle, bottom out in labour and rent.

    A material is resolvable once it has at least one recipe every one of
    whose inputs is itself resolvable (vacuously true for an extracted
    material, which has no inputs at all). Grown by repeated passes until
    nothing new is added - a plain graph reachability computation, done
    before any arithmetic, so that a material with NO path to a price is
    reported as exactly that rather than handed a number that looks real.

    This is deliberately separate from the numeric solve below. A material
    stuck in a genuine unresolvable cycle (its only route back to itself
    never touches anything with no inputs) would otherwise still get SOME
    floating-point price out of a damped iteration - fixed-point arithmetic
    does not know the difference between "converged" and "converged to a
    number that means nothing" - and this pass is what tells them apart.
    """
    resolvable = set()
    added_this_pass = True
    while added_this_pass:
        added_this_pass = False
        for entry in production_entries.values():
            outputs = entry.get("outputs") or {}
            if not outputs or all(output in resolvable for output in outputs):
                continue
            inputs = entry.get("inputs") or {}
            if all(input_material in resolvable for input_material in inputs):
                for output in outputs:
                    if output not in resolvable:
                        resolvable.add(output)
                        added_this_pass = True
    return resolvable


def recipe_cost_and_allocation(recipe_id, entry, current_prices, wage_by_trade):
    """Cost one recipe's whole batch, then split it across its outputs.

    Returns (total_process_cost_hours, {output_material: price_per_unit}),
    or None if some input has no price yet (should not happen for a
    resolvable recipe fed resolvable inputs, but the caller does not assume
    that - see the module docstring on why energy_mj and rent are handled the
    way they are).

    The split is net-realisable-value allocation: each output's share of the
    batch's total cost is its own current value (quantity times current
    price) divided by the batch's total value. This is the standard answer
    to "how much of a joint process's cost belongs to this one output" and it
    is why a single-output recipe needs no special case - its one output
    simply holds a 100% share.
    """
    inputs = entry.get("inputs") or {}
    labour_hours = entry.get("labour_hours") or {}
    outputs = entry.get("outputs") or {}

    material_cost_hours = 0.0
    for input_material, quantity_per_batch in inputs.items():
        input_price = current_prices.get(input_material)
        if input_price is None:
            return None
        material_cost_hours += quantity_per_batch * input_price

    labour_cost_hours = 0.0
    for trade, hours_per_batch in labour_hours.items():
        labour_cost_hours += hours_per_batch * wage_by_trade[trade]

    # RENT_IS_ZERO - see the module docstring. Written out as a term, rather
    # than simply left out of the sum, so that the day rent stops being zero
    # this is the one line that changes.
    rent_hours = 0.0

    total_process_cost_hours = material_cost_hours + labour_cost_hours + rent_hours

    total_batch_value = sum(quantity * current_prices.get(material, INITIAL_PRICE_GUESS_HOURS)
                            for material, quantity in outputs.items())

    output_prices = {}
    for output_material, output_quantity in outputs.items():
        if total_batch_value > 0:
            output_value = output_quantity * current_prices.get(
                output_material, INITIAL_PRICE_GUESS_HOURS)
            value_share = output_value / total_batch_value
        else:
            # Every output priced at exactly zero (only possible before the
            # first real iteration, or for a recipe whose every output is
            # otherwise worthless) - split the cost evenly rather than divide
            # by zero, and let the next iteration's real prices take over.
            value_share = 1.0 / len(outputs)
        output_prices[output_material] = (total_process_cost_hours * value_share) / output_quantity

    return total_process_cost_hours, output_prices


def solve(production_entries, producers_of, resolvable_materials, wage_by_trade,
         damping=DAMPING_FACTOR, max_iterations=MAXIMUM_ITERATIONS,
         tolerance=CONVERGENCE_TOLERANCE):
    """Damped Jacobi fixed-point iteration over every resolvable material.

    Every material updates from the SAME round's starting prices (Jacobi,
    not Gauss-Seidel) so that the result does not depend on dict iteration
    order - a determinism concern this repository has been burned by before
    (see CLAUDE.md section 6 on `id()` and stale caches). Each round: cost
    every recipe against the current price vector, take the cheapest
    technique for each material, and blend it into that material's price by
    `damping`. Stop when the largest relative change across all materials
    drops below `tolerance`, or after `max_iterations`.

    Returns (prices, iterations_run, final_residual, chosen_recipe_by_material).
    """
    prices = {material: INITIAL_PRICE_GUESS_HOURS for material in resolvable_materials}
    chosen_recipe_by_material = {}
    recipe_ids_in_order = sorted(production_entries)  # stable order; see above

    final_residual = float("inf")
    iterations_run = 0
    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration
        candidates_by_material = collections.defaultdict(list)
        for recipe_id in recipe_ids_in_order:
            entry = production_entries[recipe_id]
            outputs = entry.get("outputs") or {}
            if not outputs or not all(o in resolvable_materials for o in outputs):
                continue
            result = recipe_cost_and_allocation(recipe_id, entry, prices, wage_by_trade)
            if result is None:
                continue
            _total_cost, output_prices = result
            for material, price in output_prices.items():
                candidates_by_material[material].append((price, recipe_id))

        new_prices = {}
        max_relative_change = 0.0
        for material in resolvable_materials:
            candidates = candidates_by_material.get(material)
            if not candidates:
                new_prices[material] = prices[material]
                continue
            best_price, best_recipe = min(candidates, key=lambda pair: pair[0])
            chosen_recipe_by_material[material] = best_recipe
            damped_price = (1.0 - damping) * prices[material] + damping * best_price
            new_prices[material] = damped_price
            previous_price = prices[material]
            if previous_price > 0:
                relative_change = abs(damped_price - previous_price) / previous_price
                max_relative_change = max(max_relative_change, relative_change)

        prices = new_prices
        final_residual = max_relative_change
        if max_relative_change < tolerance:
            break

    return prices, iterations_run, final_residual, chosen_recipe_by_material


def minor_joint_byproducts_are_unanchored(production_entries, chosen_recipe_by_material,
                                          prices, wage_by_trade, share_threshold=0.5):
    """{material: value_share} for every material whose CONVERGED, CHOSEN
    recipe is a joint-production recipe in which this material holds under
    `share_threshold` of the batch's value.

    See JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in the module
    docstring for why this matters: these are not ordinary low-value
    materials, they are materials whose printed price is a mass-split
    artifact rather than an independently derived number, and every caller
    that prints a price must be able to say so next to it.
    """
    unanchored = {}
    for material, recipe_id in chosen_recipe_by_material.items():
        entry = production_entries[recipe_id]
        outputs = entry.get("outputs") or {}
        if len(outputs) <= 1:
            continue
        result = recipe_cost_and_allocation(recipe_id, entry, prices, wage_by_trade)
        if result is None:
            continue
        total_process_cost, _output_prices = result
        if total_process_cost <= 0:
            continue
        value_share = (outputs[material] * prices[material]) / total_process_cost
        if value_share < share_threshold:
            unanchored[material] = value_share
    return unanchored


def format_hours(value):
    if value >= 100:
        return "%.1f" % value
    if value >= 1:
        return "%.3f" % value
    return "%.5f" % value


def print_why(material, production_entries, producers_of, resolvable_materials,
              prices, wage_by_trade, chosen_recipe_by_material, indent=0, ancestors=()):
    """Recursive cost breakdown for one material: how much of its price is
    which input, which labour, which rent - recursing into every priced
    input in turn, with a cycle guard so a recipe graph that legitimately
    loops (iron needs charcoal needs an axe needs iron) prints once per
    branch and then says so, rather than recursing forever.
    """
    pad = "  " * indent
    if material not in resolvable_materials:
        print("%s%s: NO PATH TO A PRICE (see the unpriceable-materials list)"
              % (pad, material))
        return
    if material in ancestors:
        print("%s%s: (cycle back to an ancestor already shown above)" % (pad, material))
        return

    recipe_id = chosen_recipe_by_material.get(material)
    if recipe_id is None:
        print("%s%s: resolvable but never chosen by any recipe - this should "
              "not happen and is worth reporting as a bug" % (pad, material))
        return
    entry = production_entries[recipe_id]
    price = prices[material]
    outputs = entry.get("outputs") or {}
    other_outputs = [key for key in outputs if key != material]

    header = "%s%s = %s labour-hours" % (pad, material, format_hours(price))
    if recipe_id != material:
        header += "   [technique: %s]" % recipe_id
    conf = entry.get("conf", "?")
    header += "   (conf %s)" % conf
    print(header)

    if entry.get("extracted_from"):
        print("%s  EXTRACTED from %s - no cost of production, only labour "
              "and a rent this round fixed at 0.0 (see RENT_IS_ZERO)."
              % (pad, entry["extracted_from"]))

    candidates = sorted(set(producers_of.get(material, [])) - {recipe_id})
    if candidates:
        print("%s  other techniques considered and rejected as more "
              "expensive at current prices: %s" % (pad, ", ".join(candidates)))

    if other_outputs:
        print("%s  joint output of this batch, also yielding: %s - cost "
              "split across outputs by current value share" % (
              pad, ", ".join("%s (%.4g)" % (key, outputs[key]) for key in other_outputs)))

    result = recipe_cost_and_allocation(recipe_id, entry, prices, wage_by_trade)
    total_process_cost, output_prices = result
    output_quantity = outputs[material]
    this_output_value_share = (output_prices[material] * output_quantity) / total_process_cost \
        if total_process_cost > 0 else 0.0

    inputs = entry.get("inputs") or {}
    if inputs:
        print("%s  inputs, per %.4g unit(s) of output batch:" % (pad, output_quantity))
        for input_material, quantity_per_batch in sorted(inputs.items()):
            input_price = prices.get(input_material)
            cost = quantity_per_batch * input_price if input_price is not None else None
            share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                         if cost is not None and total_process_cost > 0 else "n/a")
            print("%s    %-24s x %10.4g  @ %10s h/unit = %10s h  (%s)" % (
                pad, input_material, quantity_per_batch,
                format_hours(input_price) if input_price is not None else "NO PRICE",
                format_hours(cost) if cost is not None else "?",
                share_text))

    labour_hours = entry.get("labour_hours") or {}
    if labour_hours:
        print("%s  labour:" % pad)
        for trade, hours_per_batch in sorted(labour_hours.items()):
            wage = wage_by_trade[trade]
            cost = hours_per_batch * wage
            share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                         if total_process_cost > 0 else "n/a")
            print("%s    %-24s %10.4g h  @ %6.3fx unskilled wage = %10s h  (%s)" % (
                pad, trade, hours_per_batch, wage, format_hours(cost), share_text))

    energy_mj = entry.get("energy_mj") or 0.0
    if energy_mj:
        print("%s  ENERGY NOT PRICED: this recipe also needs %.4g MJ of "
              "process heat/work that no fuel in `inputs` accounts for. "
              "The price above is a LOWER BOUND by that much - see "
              "ENERGY_MJ IS NOT PRICED in this file's module docstring."
              % (pad, energy_mj))

    if other_outputs:
        print("%s  this output's value share of the batch: %.1f%%  ->  "
              "%s h of %s h total process cost, / %.4g unit(s) = %s h/unit"
              % (pad, 100.0 * this_output_value_share,
                 format_hours(output_prices[material] * output_quantity),
                 format_hours(total_process_cost), output_quantity,
                 format_hours(price)))
        if this_output_value_share < 0.5:
            print("%s  (*) MINOR JOINT BYPRODUCT: this share is under half the "
                  "batch's value, and every material in that position converges "
                  "to the SAME price per unit as its dominant co-product - a "
                  "mass-split artifact of net-realisable-value allocation with "
                  "no independent price to anchor it, not a derived number. "
                  "See JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in this "
                  "file's module docstring." % pad)
    else:
        print("%s  process total: %s h  /  %.4g unit(s) of output = %s h/unit"
              % (pad, format_hours(total_process_cost), output_quantity, format_hours(price)))

    next_ancestors = ancestors + (material,)
    for input_material in sorted(inputs):
        print()
        print_why(input_material, production_entries, producers_of, resolvable_materials,
                  prices, wage_by_trade, chosen_recipe_by_material,
                  indent=indent + 1, ancestors=next_ancestors)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--why", metavar="MATERIAL",
                        help="full recursive cost breakdown for one material")
    parser.add_argument("--compare", action="store_true",
                        help="computed price vs prices.json book price, as a "
                             "ratio, worst disagreement first")
    parser.add_argument("--damping", type=float, default=DAMPING_FACTOR,
                        help="fixed-point damping factor (default %.1f)" % DAMPING_FACTOR)
    arguments = parser.parse_args(argv)

    _tree, prices_json, nodes, _wages_unused, _goods_unused = simulator.load()
    if not isinstance(nodes, dict):
        nodes = {node["id"]: node for node in nodes}

    production_entries, duplicates = load_production()
    if duplicates:
        print("REFUSING TO SOLVE: data/production/ has duplicate material "
              "keys, which validate_production.py should never let through:")
        for duplicate in duplicates:
            print("  %s" % duplicate)
        return 1

    wage_by_trade = wage_ratios_by_trade(prices_json)
    producers_of = build_producers_index(production_entries)
    resolvable_materials = compute_resolvable_materials(production_entries, producers_of)

    tree_consumed = materials_the_tree_consumes(nodes)
    all_referenced_materials = set(tree_consumed) | set(producers_of)
    for entry in production_entries.values():
        all_referenced_materials |= set((entry.get("inputs") or {}).keys())
    unpriceable = sorted(all_referenced_materials - resolvable_materials)

    prices, iterations_run, residual, chosen_recipe_by_material = solve(
        production_entries, producers_of, resolvable_materials, wage_by_trade,
        damping=arguments.damping)

    converged = residual < CONVERGENCE_TOLERANCE
    unanchored_byproducts = minor_joint_byproducts_are_unanchored(
        production_entries, chosen_recipe_by_material, prices, wage_by_trade)

    if arguments.why:
        material = arguments.why
        if material not in all_referenced_materials:
            print("%r is not a material this tree consumes, nor one "
                  "data/production/ produces or references. Typo?" % material)
            return 1
        print_why(material, production_entries, producers_of, resolvable_materials,
                  prices, wage_by_trade, chosen_recipe_by_material)
        return 0

    if arguments.compare:
        book_prices = {k: v["p"] for k, v in prices_json["purchase_prices_denarii"].items()
                       if not k.startswith("_")}
        unskilled_wage_denarii_per_hour = \
            prices_json["wage_rates_denarii_per_hour"][NUMERAIRE_TRADE]["rate"]
        rows = []
        for material in sorted(resolvable_materials):
            if material not in book_prices:
                continue
            computed_hours = prices[material]
            book_hours = book_prices[material] / unskilled_wage_denarii_per_hour
            if book_hours <= 0 or computed_hours <= 0:
                continue
            disagreement = (computed_hours / book_hours if computed_hours >= book_hours
                           else book_hours / computed_hours)
            higher = "book" if book_hours > computed_hours else "computed"
            rows.append((disagreement, material, computed_hours, book_hours, higher))
        rows.sort(reverse=True)
        print("computed price (labour-hours) vs data/prices.json book price "
              "(converted to labour-hours via the labourer wage), sorted by "
              "disagreement - THIS IS A VALIDATION READ, NOT A CALIBRATION "
              "TARGET. The book is 91.8%% author estimate; this exists to "
              "replace it, so a big ratio is a finding about one of the two "
              "numbers, not automatically a bug in the computed one. Rows "
              "marked (*) are minor joint byproducts whose computed price is "
              "a mass-split artifact, not an independent number - see "
              "JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR above; for "
              "those the book is the more informative number this round.")
        print()
        print("%-26s %14s %14s %16s" % ("material", "computed h", "book h", "disagreement"))
        for disagreement, material, computed_hours, book_hours, higher in rows:
            flag = " (*)" if material in unanchored_byproducts else ""
            print("%-26s %14s %14s %12sx %s higher%s" % (
                material, format_hours(computed_hours), format_hours(book_hours),
                format_hours(disagreement), higher, flag))
        return 0

    # Default: every material's price, in labour-hours.
    print("PRICE SOLVER - numeraire is one hour of unskilled (%r trade) "
          "labour. Rent on extracted materials is fixed at 0.0 this round "
          "(RENT_IS_ZERO); energy_mj is not priced (see module docstring)."
          % NUMERAIRE_TRADE)
    print()
    print("convergence: %s after %d iteration(s), final max relative change "
          "%.3e (tolerance %.0e, damping %.2f)"
          % ("CONVERGED" if converged else "DID NOT CONVERGE",
             iterations_run, residual, CONVERGENCE_TOLERANCE, arguments.damping))
    print("%d of %d referenced materials have a path to a price (%d resolved "
          "via data/production/, %d with NO path)"
          % (len(resolvable_materials), len(all_referenced_materials),
             len(resolvable_materials), len(unpriceable)))
    if unpriceable:
        print()
        print("MATERIALS WITH NO PATH TO A PRICE - a missing input entry, or "
              "a cycle with no extracted/labour-only material to bottom out "
              "at:")
        for material in unpriceable:
            reason = "no production entry at all" if material not in producers_of \
                else "every producing recipe needs an input with no path of its own"
            print("   %-26s consumed by %4d tree node(s) - %s"
                  % (material, tree_consumed.get(material, 0), reason))

    energy_affected = sorted(
        material for recipe_id, entry in production_entries.items()
        for material in (entry.get("outputs") or {})
        if entry.get("energy_mj") and material in resolvable_materials)
    if energy_affected:
        print()
        print("%d material(s) are UNDERPRICED because their recipe needs "
              "energy_mj this script does not cost (a real lower bound, not "
              "a wrong answer - see the module docstring): %s"
              % (len(energy_affected), ", ".join(energy_affected)))

    if unanchored_byproducts:
        print()
        print("%d material(s) marked (*) below are MINOR JOINT BYPRODUCTS "
              "whose printed price is a mass-split artifact of joint-cost "
              "allocation, not an independently derived number - see JOINT "
              "BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in this file's "
              "module docstring, and run --why on one of them:"
              % len(unanchored_byproducts))
        for material in sorted(unanchored_byproducts):
            print("   %-26s value share of its batch: %5.1f%%"
                  % (material, 100.0 * unanchored_byproducts[material]))

    print()
    print("%-30s %16s  %s" % ("material", "price (hours)", ""))
    for material in sorted(resolvable_materials):
        recipe_id = chosen_recipe_by_material.get(material, "?")
        technique_note = "" if recipe_id == material else ("  [%s]" % recipe_id)
        flag = " (*)" if material in unanchored_byproducts else ""
        print("%-30s %16s%s%s" % (
            material, format_hours(prices[material]), flag, technique_note))

    return 0 if converged else 2


if __name__ == "__main__":
    sys.exit(main())
