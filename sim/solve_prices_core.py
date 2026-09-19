"""The price algebra: resolvability, the two Ricardian rent mechanisms, the
capital and energy cost terms, choice of technique, and the damped
fixed-point `solve` loop itself.

sim/solve_prices.py is the thin composition point that every import and
every `python3 sim/solve_prices.py` invocation names, and ITS module
docstring - not this file's - is what every "see the module docstring"
comment below, and every one in sim/solve_prices_report.py, actually means:
that essay is the design reasoning for the whole tool (rent, energy,
capital, land, cycles, era gates, choice of technique), and splitting it
apart by function would break every one of those cross references for no
benefit. This file holds everything that computes a price: the
resolvability pass (`compute_resolvable_materials` and its helpers), the
ore and land rent mechanisms, `recipe_cost_and_allocation`, and `solve`
itself. sim/solve_prices_report.py holds everything that only formats and
prints a price once this file has computed it (`print_why`, the
`--compare` report, the default price table) plus the CLI's own `main`.
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# REPO_ROOT has to be on sys.path for `from sim.world import deposits` and
# `from sim.world import land` below - `sim` is a namespace package rooted
# at the repository (see sim/solve_prices.py's own sys.path setup, which
# this mirrors, so this file resolves those same imports whether it is
# reached through sim/solve_prices.py or, as sim/tests/ does, through
# `from sim import solve_prices` directly).
sys.path.insert(0, REPO_ROOT)
from sim.world import deposits                  # noqa: E402  (RENT ON EXTRACTED MATERIALS)
from sim.world import land                      # noqa: E402  (RENT ON ARABLE LAND)
# DAMPING_FACTOR, MAXIMUM_ITERATIONS, CONVERGENCE_TOLERANCE, INITIAL_PRICE_
# GUESS_HOURS and GROWTH_BOUND_HOURS live in sim/algorithm_parameters.py and
# are imported back here under their original names, so every existing
# `solve_prices_core.NAME` reference - including sim/solve_prices.py's and
# sim/solve_prices_report.py's own `from solve_prices_core import (...,
# DAMPING_FACTOR, CONVERGENCE_TOLERANCE, ...)` - keeps resolving unchanged.
# See that module's own docstring for the full reasoning, including the
# OUTCOME-SENSITIVE / safety-ceiling-only distinction each one is given
# there.
from sim.algorithm_parameters import (           # noqa: E402  (see sys.path above)
    DAMPING_FACTOR, MAXIMUM_ITERATIONS, CONVERGENCE_TOLERANCE,
    INITIAL_PRICE_GUESS_HOURS, GROWTH_BOUND_HOURS)


NUMERAIRE_TRADE = "labourer"

# The three energy carriers (see ENERGY in this module's docstring). Named
# once here rather than spelled out at each of the three call sites that
# would otherwise hand-write the tuple, so that adding a carrier cannot
# silently miss one of them - a real risk a bare tuple repeated three times
# invites.
ENERGY_CARRIER_FIELDS = ("thermal_mj", "mechanical_mj", "electrical_mj")

# PHYSICAL CAPABILITY CAPS (Complaints/44 - see TEMPERATURE in this
# module's own docstring for the full defect and the reasoning behind the
# number below). data/tech_tree.json's own `cap_heat_0700` node -
# "Sustained 700 C (pottery kiln)... Already available wherever there is
# an updraught pottery kiln, wood fired. Free starting capability. Glazes,
# bricks, lime, glass working" - carries no prerequisite at all (`pre:
# []`), so it is the lowest sustained-heat capability the tree considers
# universal: every civilisation this file prices for, however primitive,
# is assumed to already have SOME way to fire a pot or a brick. That is
# the genuine physical floor for what this file's own thermal_mj
# techniques already claim to be delivering (thermal_mj_charcoal's own
# yield_basis: "a still, a carbonating tower, a calciner" - real furnace
# apparatus, not ambient warmth), so it is reused here rather than an
# invented number - exactly the tree's own vocabulary, per the task that
# added this mechanism, instead of a parallel scale.
THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C = 700.0

# {carrier_material: (reached_field, needed_field, default_floor)}. A
# technique that OUTPUTS an energy carrier may state, on itself, the
# ceiling of some physical dimension it can reach (`temperature_reached_c`
# today); a recipe that CONSUMES that carrier may state, on itself, the
# floor it needs on the same dimension (`temperature_needed_c`). Both
# fields are optional - an entry that states neither is unconstrained (see
# this file's own `solve`, `capability_floor_by_carrier` and
# `capability_price_for_requirement` below, and TEMPERATURE in the module
# docstring for why grading is PER CONSUMER rather than one shared floor).
# Keyed by carrier rather than hand-written at each call site for the same
# reason ENERGY_CARRIER_FIELDS above is: so a second physical dimension -
# torque, pressure, whatever a future stakeholder names next - slots in as
# one more entry here, read by the same functions, rather than a second,
# parallel, hand-rolled comparison. See the module docstring's TEMPERATURE
# section for the worked example (a torque cap on mechanical_mj).
CAPABILITY_CAP_FIELDS = {
    "thermal_mj": ("temperature_reached_c", "temperature_needed_c",
                   THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C),
}


def capability_floor_by_carrier(production_entries):
    """{carrier_material: the carrier's own UNIVERSAL default floor} - one
    entry per carrier named in CAPABILITY_CAP_FIELDS.

    THIS FUNCTION RETURNS THE CARRIER'S OWN UNIVERSAL FLOOR, NOT "the
    largest requirement any consumer states" (see TEMPERATURE in the module
    docstring for why a single shared floor is a bug: it lets the hottest
    consumer anywhere in the economy lock every cooler consumer out of the
    cheap technique it could already use, and lets a newly cheap cold
    source push a hot consumer's own requirement down to nothing it never
    asked for). A specific consumer's own stated requirement is graded
    separately by `capability_price_for_requirement` below, so this
    function only has to return the one number every technique claiming to
    supply the carrier is checked against regardless of what any consumer
    needs - the free, universal minimum
    (THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C's own citation) - which
    decides `thermal_mj`'s own ordinary pool price, the one every consumer
    with no stated requirement of its own pays.

    `production_entries` is kept as a parameter, though unused, so every
    existing call site (and `_meets_capability_floor` below, which takes
    this function's own return value) can keep calling this function the
    same way regardless of what it computes internally.
    """
    return {carrier: default_floor
            for carrier, (_reached_field, _needed_field, default_floor)
            in CAPABILITY_CAP_FIELDS.items()}


def capability_required_grades(production_entries):
    """{carrier_material: sorted tuple of every distinct requirement this
    era's own (possibly gated) `production_entries` actually states for
    that carrier} - the carrier's own universal default floor, ALWAYS
    included (every civilisation this file prices for already clears
    it), plus each ACTIVE consumer's own `needed_field` value: an entry
    that draws a nonzero amount of the carrier (`entry.get(carrier)` is
    truthy) AND states a requirement on it (`entry.get(needed_field) is
    not None`) - "no stated requirement" still means exactly that, not
    zero.

    This is the PER-CONSUMER GRADING mechanism (see
    TEMPERATURE in the module docstring): every distinct value here gets
    its OWN price from `capability_price_for_requirement`, computed
    independently, so a 2500 C requirement existing somewhere in the
    economy neither raises nor lowers the price a 1000 C or a 700 C
    requirement gets - each is simply one more entry in the set this
    function returns.
    """
    required_by_carrier = {}
    for carrier, (_reached_field, needed_field, default_floor) in CAPABILITY_CAP_FIELDS.items():
        required_values = {default_floor}
        for entry in production_entries.values():
            if entry.get(carrier) and entry.get(needed_field) is not None:
                required_values.add(entry[needed_field])
        required_by_carrier[carrier] = tuple(sorted(required_values))
    return required_by_carrier


def capability_price_for_requirement(carrier, required_value, production_entries,
                                     current_prices, wage_by_trade,
                                     rent_hours_per_kg_by_material=None):
    """(price, recipe_id) for the CHEAPEST technique that both supplies
    `carrier` and clears `required_value` on the physical dimension
    CAPABILITY_CAP_FIELDS grades it by, costed at this round's own
    `current_prices` - or None if nothing eligible resolves this round
    (should not happen for any value `capability_required_grades` itself
    produced, since the default floor is always clearable by this file's
    own PRIMARY techniques, but a caller must still handle it the same
    way an ordinary unpriceable material is handled elsewhere in this
    file: propagate the failure rather than guess a price).

    THIS is the mechanism that replaces the single shared floor: called
    once per distinct required value (see `capability_required_grades`),
    not once per carrier, so a hot requirement and a cool one sharing the
    same carrier name get independently the cheapest technique that
    actually clears EACH one, rather than the cheapest technique that
    clears whichever requirement happens to be largest.

    A candidate technique that states no reach at all on this dimension
    is treated as unconstrained (it clears every requirement) - the same
    "no stated value, no new behaviour" rule `_meets_capability_floor`
    already applies; today every PRIMARY thermal_mj technique states one,
    so this only matters for a future carrier or a future technique added
    without one.

    Deliberately does NOT thread a capability-graded price into this
    inner cost calculation for the CANDIDATE techniques themselves (see
    `recipe_cost_and_allocation`'s own `capability_band_price_by_carrier`
    parameter) - a producer of one capped carrier drawing on ANOTHER
    capped carrier with its own stated requirement would need that too,
    but no entry in this file does that today (the only other carrier
    CAPABILITY_CAP_FIELDS could someday grade, `mechanical_mj`, is not
    graded yet - see the module docstring's torque example), so this is
    left as a plain `current_prices` lookup for now rather than solved
    for a case that does not exist. Tag: GAP, not a heuristic, per
    CLAUDE.md 3.4 - the day a second graded carrier feeds a first one,
    this function's own candidate costing needs the same banded lookup
    `recipe_cost_and_allocation` already has.
    """
    reached_field = CAPABILITY_CAP_FIELDS[carrier][0]
    best = None
    for recipe_id, entry in production_entries.items():
        outputs = entry.get("outputs") or {}
        if carrier not in outputs:
            continue
        reached = entry.get(reached_field)
        if reached is not None and reached < required_value:
            continue
        result = recipe_cost_and_allocation(
            recipe_id, entry, current_prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if result is None:
            continue
        _total_cost, output_prices = result
        price = output_prices[carrier]
        if best is None or price < best[0]:
            best = (price, recipe_id)
    return best


def _capability_graded_price(carrier, entry, current_prices,
                             capability_band_price_by_carrier):
    """The price a SPECIFIC consuming `entry` pays for `carrier` this
    round - PER-CONSUMER GRADING (see TEMPERATURE in the module
    docstring). An entry that states its own requirement on the
    dimension CAPABILITY_CAP_FIELDS grades `carrier` by pays whatever the
    cheapest technique clearing THAT requirement costs, read from
    `capability_band_price_by_carrier` (built once per round by `solve`,
    one entry per value `capability_required_grades` found - see
    `capability_price_for_requirement`); an entry that states no
    requirement - the overwhelming majority of every energy carrier's
    consumers - pays the carrier's own ordinary solved price
    (`current_prices[carrier]`), exactly as before this mechanism
    existed. Returns None (propagating an unpriceable recipe, exactly
    like a missing input price elsewhere in this file) only if the
    entry's own stated requirement cannot be met by anything this round -
    never by silently falling back to the wrong grade's price.

    `capability_band_price_by_carrier` is None outside `solve`'s own
    iteration (the one-off ore and wheat base-price calls in
    `rent_hours_per_kg_by_ore_material` and `land_rent_hours_per_iugerum`,
    neither of which ever states a capped-carrier requirement) and for
    any carrier CAPABILITY_CAP_FIELDS does not grade at all, in which
    case this always falls through to the plain, ungraded lookup.
    """
    capped = CAPABILITY_CAP_FIELDS.get(carrier)
    if capped and capability_band_price_by_carrier:
        _reached_field, needed_field, _default_floor = capped
        required_value = entry.get(needed_field)
        if required_value is not None:
            band = capability_band_price_by_carrier.get(carrier) or {}
            graded = band.get(required_value)
            return graded[0] if graded is not None else None
    return current_prices.get(carrier)


def _meets_capability_floor(material, entry, floor_by_carrier):
    """True unless `material` is a capability-capped carrier (see
    CAPABILITY_CAP_FIELDS) and `entry`'s own stated reach on that
    dimension falls short of `floor_by_carrier[material]`. An entry that
    states no reach at all (most entries, including every material that
    is not itself an energy-carrier-supplying technique) is treated as
    unconstrained - the same "no stated value, no new behaviour" rule
    this mechanism applies throughout.

    Used two ways: with `capability_floor_by_carrier`'s own output, to
    decide which technique wins the carrier's ORDINARY pool price (what
    an unlabelled consumer pays); and, inside `capability_price_for_
    requirement`'s own candidate loop in spirit (that function inlines
    the same comparison against a single `required_value` rather than a
    per-carrier dict, since it is testing one specific requirement at a
    time rather than every carrier's own floor at once).
    """
    capped = CAPABILITY_CAP_FIELDS.get(material)
    if capped is None:
        return True
    reached_field, _needed_field, _default_floor = capped
    reached = entry.get(reached_field)
    if reached is None:
        return True
    return reached >= floor_by_carrier[material]


# Damped Jacobi fixed-point iteration: every material's next price is a blend
# of its old price and what the current round's cheapest technique implies,
# so a technique flipping from one iteration to the next (a real possibility
# early on, when every price still carries the same seed guess) nudges the
# price rather than slamming it, which is what "damped" buys over a raw
# reassignment.
#
# DAMPING_FACTOR, MAXIMUM_ITERATIONS, CONVERGENCE_TOLERANCE, INITIAL_PRICE_
# GUESS_HOURS and GROWTH_BOUND_HOURS - five algorithmic parameters (0.5 not
# tuned against an outcome, the textbook midpoint; the iteration ceiling;
# the convergence definition; the seed guess; the divergence detector) -
# live in sim/algorithm_parameters.py and are imported back above, at these
# same names, so this section and every function below it read unchanged.
# See that module's own docstring for the full, unshortened paragraphs and
# for why algorithmic and computational parameters get their own file.


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


def load_starting_technologies(civilization_id):
    """The set of tech-tree node ids a civilization begins the game holding.

    This is read straight from `data/civilizations/<id>.json`'s
    `starting_techs`, which is an INITIAL CONDITION - what this society has
    already worked out by the year it starts in - and so is exactly the kind
    of input CLAUDE.md section 3.1 allows. It is not a schedule of when
    techniques were invented; there is no such table here and there must not
    be one.
    """
    path = os.path.join(HERE, os.pardir, "data", "civilizations",
                        "%s.json" % civilization_id)
    if not os.path.exists(path):
        available = sorted(name[:-len(".json")]
                           for name in os.listdir(os.path.dirname(path))
                           if name.endswith(".json") and not name.startswith("_"))
        raise FileNotFoundError(
            "no civilization %r - have: %s" % (civilization_id, ", ".join(available)))
    with open(path) as handle:
        civilization = json.load(handle)
    return set(civilization.get("starting_techs") or [])


def techniques_available_to(production_entries, reached_nodes):
    """Split the production entries into what this era can run and what it cannot.

    Returns (available, unreached, unclassified) - the first a dict in the
    same shape as `production_entries`, the other two sorted lists of recipe
    ids, kept apart because they mean different things and want different
    responses:

      unreached    - the entry names a node this civilization has not
                     reached. Working as intended. A Roman cannot electrolyse
                     zinc and the solve should not offer to.
      unclassified - the entry carries no `requires_node` at all, so nobody
                     has said when it becomes available. Dropped, because
                     admitting it is precisely how a photovoltaic panel ended
                     up pricing Roman electricity (Complaints/39), and
                     counted, because a silent drop is how that stayed
                     invisible for as long as it did.

    `requires_node: null` is a third, deliberate state: available with no
    technology whatever - gathering firewood, quarrying stone, growing wheat.
    It is admitted to every era, including the earliest.
    """
    available, unreached, unclassified = {}, [], []
    for recipe_id, entry in production_entries.items():
        if "requires_node" not in entry:
            unclassified.append(recipe_id)
            continue
        required = entry["requires_node"]
        if required is None or required in reached_nodes:
            available[recipe_id] = entry
        else:
            unreached.append(recipe_id)
    return available, sorted(unreached), sorted(unclassified)


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


def _dependency_materials(entry):
    """Every material one recipe's price computation needs a price FOR:
    its ordinary process `inputs`, plus every capital good's own
    `build_materials` (see the module docstring's CAPITAL section), plus
    `thermal_mj` and/or `mechanical_mj` themselves whenever the entry needs
    a nonzero amount of either (see ENERGY), plus `iugerum_land` itself
    whenever the entry states a nonzero `land_iugera_years` (see RENT ON
    GROWN AND LAND-LIMITED MATERIALS). Resolvability has to see all
    four, or a capital-only cycle - `iron_bar_kg` priced partly in
    `iron_bar_kg`, via its own finery hammer's iron fittings - or an energy
    or land dependency that happened not to resolve, would never appear in
    the graph that decides whether a price exists at all.
    """
    dependencies = set((entry.get("inputs") or {}).keys())
    for capital_good in (entry.get("capital") or []):
        dependencies.update((capital_good.get("build_materials") or {}).keys())
    for energy_key in ENERGY_CARRIER_FIELDS:
        if entry.get(energy_key):
            dependencies.add(energy_key)
    if entry.get("land_iugera_years"):
        dependencies.add("iugerum_land")
    return dependencies


def _grow_resolvable_by_topological_pass(production_entries, resolvable):
    """Add a recipe's outputs once every dependency is already resolvable,
    repeated until nothing new is added. This is a topological-order
    construction, so it is exactly right for the acyclic part of the graph
    (the great majority of it) and refuses every genuine cycle by
    construction - which is why `compute_resolvable_materials` runs it only
    as a first pass, then hands whatever it could not reach to the
    strongly-connected-component productiveness test below. `resolvable` is
    mutated in place so a cycle accepted by that test can call this again
    and let anything waiting only on it cascade through the same loop.
    """
    added_this_pass = True
    while added_this_pass:
        added_this_pass = False
        for entry in production_entries.values():
            outputs = entry.get("outputs") or {}
            if not outputs or all(output in resolvable for output in outputs):
                continue
            if all(dependency in resolvable for dependency in _dependency_materials(entry)):
                for output in outputs:
                    if output not in resolvable:
                        resolvable.add(output)
                        added_this_pass = True


def _pending_entries(production_entries, resolvable):
    """Entries with at least one output the topological pass above could not
    reach - the residual the strongly-connected-component pass runs over."""
    return {recipe_id: entry for recipe_id, entry in production_entries.items()
            if (entry.get("outputs") or {})
            and not all(output in resolvable for output in entry["outputs"])}


def _build_material_dependency_graph(pending_entries, resolvable):
    """{material: {materials it still depends on}}, over every output any
    pending entry still needs to resolve, restricted to dependencies that
    are not already resolved - a resolved dependency is a boundary
    condition for the productiveness test below, not part of the cycle
    structure, so it is not an edge here.
    """
    graph = collections.defaultdict(set)
    for entry in pending_entries.values():
        outputs = entry.get("outputs") or {}
        still_needed_outputs = [output for output in outputs if output not in resolvable]
        remaining_dependencies = [dependency for dependency in _dependency_materials(entry)
                                  if dependency not in resolvable]
        for output in still_needed_outputs:
            graph[output]  # a node even if this entry alone has no remaining dependency
            graph[output].update(remaining_dependencies)
    return graph


def _strongly_connected_components(graph):
    """Tarjan's algorithm, iterative to avoid a recursion limit on a large
    residual graph. Returns components such that if a component depends on
    another (an edge leaves it and lands somewhere else in the graph), the
    component it depends on is always emitted FIRST - so a single pass over
    the result can decide each component using only what earlier components,
    or the pre-existing resolved set, already settled.
    """
    next_index = [0]
    index_of = {}
    lowlink_of = {}
    on_stack = set()
    stack = []
    components = []

    for start in graph:
        if start in index_of:
            continue
        call_stack = [(start, iter(graph.get(start, ())))]
        index_of[start] = lowlink_of[start] = next_index[0]
        next_index[0] += 1
        stack.append(start)
        on_stack.add(start)

        while call_stack:
            node, neighbours = call_stack[-1]
            descended = False
            for neighbour in neighbours:
                if neighbour not in graph:
                    # Nothing in the residual graph depends on THIS - a
                    # dead end (a missing production entry, reported
                    # separately by the caller), not part of any cycle.
                    continue
                if neighbour not in index_of:
                    index_of[neighbour] = lowlink_of[neighbour] = next_index[0]
                    next_index[0] += 1
                    stack.append(neighbour)
                    on_stack.add(neighbour)
                    call_stack.append((neighbour, iter(graph.get(neighbour, ()))))
                    descended = True
                    break
                elif neighbour in on_stack:
                    lowlink_of[node] = min(lowlink_of[node], index_of[neighbour])
            if descended:
                continue

            call_stack.pop()
            if call_stack:
                parent = call_stack[-1][0]
                lowlink_of[parent] = min(lowlink_of[parent], lowlink_of[node])
            if lowlink_of[node] == index_of[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(component)
    return components


def _entries_relevant_to_component(production_entries, component, resolved_so_far):
    """Recipes usable when testing whether `component` is productive: every
    one of the recipe's outputs must lie inside the component (a recipe that
    also makes something outside it is not part of this cycle), and every
    dependency must already be resolved OR be another member of the same
    component - the only kind of "not yet resolved" a productiveness test is
    allowed to lean on. Anything else is a hole this component cannot paper
    over, and is reported as such by the caller.
    """
    relevant = {}
    for recipe_id, entry in production_entries.items():
        outputs = entry.get("outputs") or {}
        if not outputs or not all(output in component for output in outputs):
            continue
        if all(dependency in component or dependency in resolved_so_far
               for dependency in _dependency_materials(entry)):
            relevant[recipe_id] = entry
    return relevant


def _has_external_anchor(entry, resolved_so_far):
    """True if this recipe's cost includes something that is NOT another
    member of its own cycle: ordinary labour, capital build-labour, a
    material dependency that is already resolved (ultimately an extracted
    good, priced at labour plus zero rent), or land (ultimately priced by
    the Ricardian rent on `iugerum_land`, another extracted good in
    everything but name). A cycle where every relevant recipe fails this
    never bottoms out in labour or an extracted good at all - see the
    module docstring's CYCLES section - so there is nothing to price it
    FROM, independent of whether the arithmetic happens to converge.
    """
    if sum((entry.get("labour_hours") or {}).values()) > 0:
        return True
    if any(dependency in resolved_so_far for dependency in (entry.get("inputs") or {})):
        return True
    for capital_good in (entry.get("capital") or []):
        if sum((capital_good.get("build_labour_hours") or {}).values()) > 0:
            return True
        if any(material in resolved_so_far
               for material in (capital_good.get("build_materials") or {})):
            return True
    if entry.get("land_iugera_years") and "iugerum_land" in resolved_so_far:
        return True
    return False


def _productiveness_round_candidates(relevant, component, prices, dummy_wage_by_trade,
                                     rent_hours_per_kg_by_material):
    """One round's cheapest-technique candidates for every material inside
    `component`, from `relevant`'s recipes - the same per-round candidate
    step `solve()` itself runs (see `_solve_round_candidates`), restricted
    to just the recipes `_entries_relevant_to_component` found usable for
    this component. Returns {material: [price, ...]}, one entry per
    candidate recipe that resolves this round.
    """
    candidates_by_material = collections.defaultdict(list)
    for entry in relevant.values():
        result = recipe_cost_and_allocation(
            "<cycle productiveness test>", entry, prices, dummy_wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if result is None:
            continue
        _total_cost, output_prices = result
        for material, price in output_prices.items():
            if material in component:
                candidates_by_material[material].append(price)
    return candidates_by_material


def _update_productiveness_round_prices(component, prices, candidates_by_material):
    """Damp `prices` (mutated in place) toward this round's cheapest
    candidate for every material in `component`. Returns (diverged,
    max_relative_change): `diverged` is True the instant any material's
    damped price stops being finite or crosses GROWTH_BOUND_HOURS - the
    empirical Hawkins-Simon test `_component_is_productive`'s own docstring
    describes, checked here rather than left inline so that function's own
    loop reads as "run one round, then ask what happened" rather than
    interleaving the damping arithmetic with the divergence check.
    """
    max_relative_change = 0.0
    for material in component:
        candidates = candidates_by_material.get(material)
        if not candidates:
            continue
        best_price = min(candidates)
        previous_price = prices[material]
        damped_price = (1.0 - DAMPING_FACTOR) * previous_price + DAMPING_FACTOR * best_price
        if not math.isfinite(damped_price) or abs(damped_price) > GROWTH_BOUND_HOURS:
            return True, max_relative_change
        prices[material] = damped_price
        if previous_price > 0:
            max_relative_change = max(
                max_relative_change, abs(damped_price - previous_price) / previous_price)
    return False, max_relative_change


def _component_is_productive(component, production_entries, resolved_so_far,
                             rent_hours_per_kg_by_material=None):
    """Test the productiveness condition (Hawkins-Simon: the input-output
    matrix restricted to `component` has spectral radius under 1) the same
    way the module docstring says the design should work it out - by
    literally running the damped Jacobi iteration `solve()` uses below,
    restricted to this component, with every material outside it pinned at a
    nominal placeholder price.

    A placeholder is valid here because whether the restricted map CONTRACTS
    does not depend on it: for a single-output recipe the update rule is
    affine in prices (materials cost is linear in input prices; labour and
    rent are constants), so contraction is a property of the coefficients on
    component-internal materials alone. Joint-output recipes add a genuine
    nonlinearity through value-share allocation; this still runs the real
    `recipe_cost_and_allocation` rather than a separate linear
    approximation, so divergence for those is caught empirically, by the
    iteration actually crossing GROWTH_BOUND_HOURS, rather than assumed safe
    by an argument that no longer strictly applies.

    Returns (True, None) if it converges, or (False, explanation) naming the
    component - Complaints/31 asks for a non-contracting cycle to be
    reported by name, as clearly as a missing recipe already is, not
    silently folded into "no path to a price".
    """
    relevant = _entries_relevant_to_component(production_entries, component, resolved_so_far)
    produced = {output for entry in relevant.values() for output in (entry.get("outputs") or {})}
    missing = sorted(component - produced)
    if missing:
        return False, (
            "%s: no admissible recipe even counting the rest of this cycle "
            "(every recipe for it needs something outside {%s} with no "
            "price of its own)"
            % (", ".join(missing), ", ".join(sorted(component))))

    if not any(_has_external_anchor(entry, resolved_so_far) for entry in relevant.values()):
        return False, (
            "{%s}: every recipe in this cycle only consumes other members "
            "of the same cycle - it never bottoms out in labour or an "
            "extracted good, so there is nothing to price it from"
            % ", ".join(sorted(component)))

    dummy_wage_by_trade = collections.defaultdict(lambda: 1.0)
    prices = {material: 1.0 for material in resolved_so_far}
    prices.update({material: INITIAL_PRICE_GUESS_HOURS for material in component})

    for _iteration in range(1, MAXIMUM_ITERATIONS + 1):
        candidates_by_material = _productiveness_round_candidates(
            relevant, component, prices, dummy_wage_by_trade, rent_hours_per_kg_by_material)
        diverged, max_relative_change = _update_productiveness_round_prices(
            component, prices, candidates_by_material)
        if diverged:
            return False, (
                "{%s}: restricted iteration grew without bound instead "
                "of converging - this cycle consumes more of itself "
                "than it yields (spectral radius >= 1, Hawkins-Simon "
                "fails)" % ", ".join(sorted(component)))
        if max_relative_change < CONVERGENCE_TOLERANCE:
            return True, None

    return False, (
        "{%s}: restricted iteration neither converged nor visibly diverged "
        "within %d iterations - treated as unproductive rather than guessed "
        "at" % (", ".join(sorted(component)), MAXIMUM_ITERATIONS))


def compute_resolvable_materials(production_entries, producers_of, diagnostics=None,
                                 rent_hours_per_kg_by_material=None):
    """Which materials can, even in principle, bottom out in labour and rent.

    First, the acyclic part: a material is resolvable once it has at least
    one recipe every one of whose dependencies is itself resolvable
    (vacuously true for an extracted material, which has no inputs at all).
    Grown by `_grow_resolvable_by_topological_pass` until nothing new is
    added - a plain topological reachability computation that is exactly
    right for a DAG and, by construction, refuses every genuine cycle.

    Second, the part that pass cannot see: whatever is left is decomposed
    into strongly connected components (`_strongly_connected_components`),
    and each one is tested for PRODUCTIVENESS rather than refused outright -
    a component is resolvable when every dependency from outside it is
    already resolved AND the iteration restricted to the component actually
    contracts (`_component_is_productive`). This is what makes the
    docstring's own axe/iron example, and a material like seed corn that
    lists itself among its inputs, resolve when the numbers say they should
    - see Complaints/31 and `sim/tests/test_price_solver_cycles.py`.

    This is still deliberately separate from the numeric solve below. A
    material stuck in a genuinely UNPRODUCTIVE cycle (consuming more of a
    good than the cycle yields, or never touching labour or an extracted
    good at all) would otherwise get SOME floating-point price out of a
    damped iteration - fixed-point arithmetic does not know the difference
    between "converged" and "converged to a number that means nothing" -
    and this pass is what tells them apart, and names the cycle responsible
    in `diagnostics` (a list, if the caller wants the messages) rather than
    only reporting the materials downstream of it as having no path.
    """
    resolvable = set()
    _grow_resolvable_by_topological_pass(production_entries, resolvable)

    pending = _pending_entries(production_entries, resolvable)
    graph = _build_material_dependency_graph(pending, resolvable)
    for component in _strongly_connected_components(graph):
        component_set = set(component)
        if component_set <= resolvable:
            continue  # settled already, e.g. absorbed by an earlier component
        is_productive, explanation = _component_is_productive(
            component_set, production_entries, resolvable,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if is_productive:
            resolvable |= component_set
            # A newly-productive cycle can unlock ordinary, acyclic recipes
            # that were only waiting on it - let those cascade in before the
            # next component (which may depend on this one) is judged.
            _grow_resolvable_by_topological_pass(production_entries, resolvable)
        elif diagnostics is not None:
            diagnostics.append(explanation)
    return resolvable


def _material_cost_hours(inputs, current_prices):
    """Sum of `quantity_per_batch * input_price` over one recipe's `inputs`,
    or None the instant an input has no price yet - the same "propagate the
    failure" rule every cost component `recipe_cost_and_allocation` sums
    follows, so its caller can just check each component for None in turn.
    """
    material_cost_hours = 0.0
    for input_material, quantity_per_batch in inputs.items():
        input_price = current_prices.get(input_material)
        if input_price is None:
            return None
        material_cost_hours += quantity_per_batch * input_price
    return material_cost_hours


def _labour_cost_hours(labour_hours, wage_by_trade):
    """Sum of `hours_per_batch * wage_by_trade[trade]` over one recipe's
    `labour_hours`. Every trade a recipe names is assumed to already be in
    `wage_by_trade` (a missing one is a data bug, not a "no price yet"
    case, so this raises KeyError rather than returning None for it).
    """
    labour_cost_hours = 0.0
    for trade, hours_per_batch in labour_hours.items():
        labour_cost_hours += hours_per_batch * wage_by_trade[trade]
    return labour_cost_hours


def _extraction_rent_cost_hours(outputs, rent_by_kg):
    # RENT (see RENT ON EXTRACTED MATERIALS in the module docstring). A
    # material not named in `rent_hours_per_kg_by_material` - which is
    # everything except the six ores sim/world/deposits.py covers - still
    # prices at exactly 0.0 rent (see WHAT THIS DOES NOT REACH in the
    # module docstring). Summed over every output rather than assumed
    # single-output, so a hypothetical
    # future joint-output ore entry would be charged correctly on each of
    # its outputs rather than silently on only one.
    return sum(output_quantity * rent_by_kg.get(output_material, 0.0)
              for output_material, output_quantity in outputs.items())


def _land_cost_hours(entry, current_prices):
    # LAND (Complaints/49 - see RENT ON GROWN AND LAND-LIMITED MATERIALS in
    # the module docstring). `land_iugera_years` is a BATCH-level quantity,
    # exactly like `inputs` and `labour_hours` above, of iugera-years this
    # whole batch ties up `iugerum_land` for - priced through this same
    # `current_prices` vector rather than a separate rent table, because
    # `iugerum_land` is an ORDINARY material once its own price is set (by
    # the rent term above, on ITS OWN recipe in data/production/
    # 40_organics.json) and a crop paying for the land it grows on is no
    # different from a furnace paying for the ore it smelts. Kept as its
    # own named term rather than folded into `material_cost_hours` for the
    # same reason CAPITAL's build bill is not hand-added to `inputs`: this
    # is land OCCUPIED for a season, not a material CONSUMED making one
    # batch, and the field name should say so.
    land_iugera_years = entry.get("land_iugera_years") or 0.0
    if not land_iugera_years:
        return 0.0
    land_price = current_prices.get("iugerum_land")
    if land_price is None:
        return None
    return land_iugera_years * land_price


def _capital_cost_hours_per_unit(capital_goods, current_prices, wage_by_trade):
    capital_cost_hours = 0.0
    for capital_good in capital_goods:
        build_materials = capital_good.get("build_materials") or {}
        build_labour_hours = capital_good.get("build_labour_hours") or {}

        build_cost_hours = 0.0
        for build_material, quantity_per_build in build_materials.items():
            build_material_price = current_prices.get(build_material)
            if build_material_price is None:
                return None
            build_cost_hours += quantity_per_build * build_material_price
        for trade, hours_per_build in build_labour_hours.items():
            build_cost_hours += hours_per_build * wage_by_trade[trade]

        lifetime_output = capital_good["service_life_years"] * capital_good["annual_output_at_basis"]
        capital_cost_hours += build_cost_hours / lifetime_output
    return capital_cost_hours


def _energy_cost_hours(entry, current_prices, capability_band_price_by_carrier):
    # ENERGY (Complaints/32's third gap, now closed for all THREE carriers -
    # THERMAL, MECHANICAL and ELECTRICAL - see ENERGY in the module
    # docstring). All three are BATCH-level quantities, exactly like
    # `inputs` and `labour_hours` above (the MJ figure is already stated
    # against this same batch's basis output) - NOT a per-unit-of-output
    # charge the way `capital` is, so unlike capital_cost_hours none of
    # these terms gets multiplied by batch_output_quantity. PER-CONSUMER
    # GRADING (Complaints/44, continued - see TEMPERATURE in the module
    # docstring): the price paid is not always `current_prices[energy_key]`
    # any more - `_capability_graded_price` returns THIS recipe's own
    # graded price when it states its own requirement, and falls back to
    # the same flat lookup as before otherwise.
    energy_cost_hours = 0.0
    for energy_key in ENERGY_CARRIER_FIELDS:
        energy_quantity_per_batch = entry.get(energy_key) or 0.0
        if energy_quantity_per_batch:
            energy_price = _capability_graded_price(
                energy_key, entry, current_prices, capability_band_price_by_carrier)
            if energy_price is None:
                return None
            energy_cost_hours += energy_quantity_per_batch * energy_price
    return energy_cost_hours


def _allocate_output_prices(outputs, current_prices, total_process_cost_hours):
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
    return output_prices


def recipe_cost_and_allocation(recipe_id, entry, current_prices, wage_by_trade,
                               rent_hours_per_kg_by_material=None,
                               capability_band_price_by_carrier=None):
    """Cost one recipe's whole batch, then split it across its outputs.

    Returns (total_process_cost_hours, {output_material: price_per_unit}),
    or None if some input has no price yet (should not happen for a
    resolvable recipe fed resolvable inputs, but the caller does not assume
    that - see the module docstring on why most extracted materials still
    price at zero rent, why six ores do not, why `thermal_mj`/
    `mechanical_mj` are priced through the energy market in
    data/production/70_energy.json, and why `energy_mj` still is not).

    `capability_band_price_by_carrier` is {carrier: {required_value:
    (price, recipe_id)}}, built once per round by `solve` from
    `capability_required_grades` and `capability_price_for_requirement` -
    see TEMPERATURE in the module docstring and `_capability_graded_price`
    below for PER-CONSUMER GRADING, the mechanism this feeds. Omitted or
    None, every energy carrier this recipe draws on prices at
    `current_prices`'s own flat value for it, exactly the old behaviour -
    this is the default so every caller with no opinion about grading
    (the rent and land one-off calls, which never consume a graded
    carrier) is not forced to pass an empty dict everywhere.

    `rent_hours_per_kg_by_material` is {material_key: hours of rent per kg
    of that material's OWN output} - see RENT ON EXTRACTED MATERIALS in the
    module docstring and `rent_hours_per_kg_by_ore_material` below for how
    it is built. Omitted or None, every material's rent is zero, exactly
    the old RENT_IS_ZERO behaviour; this is the default so that the cycle-
    productiveness test and any other caller that has no opinion about rent
    is not forced to pass an empty dict everywhere.

    The split is net-realisable-value allocation: each output's share of the
    batch's total cost is its own current value (quantity times current
    price) divided by the batch's total value. This is the standard answer
    to "how much of a joint process's cost belongs to this one output" and it
    is why a single-output recipe needs no special case - its one output
    simply holds a 100% share.

    CAPITAL (see the module docstring): each item in `entry["capital"]` adds
    (cost of its build_materials + cost of its build_labour_hours) /
    (service_life_years * annual_output_at_basis) to the cost of ONE UNIT of
    this recipe's basis output, priced through this same `current_prices`
    vector rather than looked up - a furnace built partly from the metal it
    makes is exactly the kind of dependency `compute_resolvable_materials`
    has to see, which is why `_dependency_materials` counts these build
    materials too. Everything else this function sums (`material_cost_hours`,
    `labour_cost_hours`) is a cost for the WHOLE BATCH described by `inputs`
    and `labour_hours` (a batch of `batch_output_quantity` units, below), so
    the per-unit capital charge is scaled up by that same quantity before it
    is added in - otherwise it would silently get divided by the batch size
    a second time when `total_process_cost_hours` is turned back into a
    per-unit price further down.
    """
    inputs = entry.get("inputs") or {}
    labour_hours = entry.get("labour_hours") or {}
    outputs = entry.get("outputs") or {}
    # The batch size `annual_output_at_basis` (and every input/labour_hours
    # quantity above) is implicitly stated against: the recipe's own basis
    # output, always the largest quantity in `outputs` for every entry that
    # carries `capital` today (a byproduct like lead's silver or zinc's
    # germanium is always the tiny quantity, never the one a furnace's
    # annual output is quoted against).
    batch_output_quantity = max(outputs.values()) if outputs else 1.0
    material_cost_hours = _material_cost_hours(inputs, current_prices)
    if material_cost_hours is None:
        return None

    labour_cost_hours = _labour_cost_hours(labour_hours, wage_by_trade)

    rent_by_kg = rent_hours_per_kg_by_material or {}
    rent_hours = _extraction_rent_cost_hours(outputs, rent_by_kg)

    land_cost_hours = _land_cost_hours(entry, current_prices)
    if land_cost_hours is None:
        return None

    capital_cost_hours = _capital_cost_hours_per_unit(
        entry.get("capital") or [], current_prices, wage_by_trade)
    if capital_cost_hours is None:
        return None

    energy_cost_hours = _energy_cost_hours(entry, current_prices, capability_band_price_by_carrier)
    if energy_cost_hours is None:
        return None

    total_process_cost_hours = (material_cost_hours + labour_cost_hours + rent_hours
                                + land_cost_hours
                                + capital_cost_hours * batch_output_quantity
                                + energy_cost_hours)

    output_prices = _allocate_output_prices(outputs, current_prices, total_process_cost_hours)

    return total_process_cost_hours, output_prices


# {ore_material_key: (metal_name_in_deposits_METALS, (candidate_recipe_id,
# ...))} - see RENT ON EXTRACTED MATERIALS in the module docstring for what
# this table is, why gold is not in it (gold_kg has no extracted_from ore
# stage of its own for rent to attach to), and why the "dominant" recipe
# matters (it is the one whose own ore-to-metal ratio is used to convert a
# per-kg-of-metal rent into a per-kg-of-ore price, and the one that ratio
# is EXACT for - see rent_hours_per_kg_by_ore_material's own docstring).
# copper, tin, silver and mercury each have exactly one recipe that
# consumes their ore, so there is only one candidate for them. Iron has
# two - pig_iron_kg (blast furnace) and iron_bloom_kg (direct bloomery) -
# at different ore-to-metal ratios, and which of them an era can even RUN
# differs: `--civ rome_100ad` gates pig_iron_kg out entirely (blast_furnace
# is not a Roman technology) while leaving iron_bloom_kg available, so a
# single fixed recipe id here would silently leave iron at zero rent for
# every Roman-era gated solve - exactly the scenario this task's own VERIFY
# step runs. The tuple is tried in order and the first candidate present in
# THIS solve's (possibly gated) production_entries is used, so an ungated
# solve gets the blast-furnace ratio and a Roman-gated one falls back to
# the bloomery ratio - both real recipes, never an invented one.
RENT_BEARING_ORE_MATERIALS = {
    "iron_ore_kg": ("iron", ("pig_iron_kg", "iron_bloom_kg")),
    "copper_ore_kg": ("copper", ("copper_kg",)),
    "cassiterite_kg": ("tin", ("tin_kg",)),
    "galena_kg": ("lead", ("lead_kg",)),
    "silver_ore_kg": ("silver", ("silver_kg",)),
    "cinnabar_kg": ("mercury", ("mercury_kg",)),
}


def rent_hours_per_kg_by_ore_material(production_entries, wage_by_trade):
    """{ore_material_key: hours of rent per kg of that ore's own output},
    for every metal in RENT_BEARING_ORE_MATERIALS whose ore and dominant
    smelting recipe both survive this era's gate - see RENT ON EXTRACTED
    MATERIALS in the module docstring for the mechanism this implements and
    why it is only approximate for a metal with more than one ore-consuming
    recipe.

    THE ALGEBRA. `sim/world/deposits.py`'s `find_marginal_deposit` gives
    `price_at_margin_labour_hours_per_kg` - the Ricardian, rent-inclusive
    price of one kilogram of CONTAINED METAL, at the fixed quantity demanded
    this function reads from `data/world/resources.json`'s own
    `empire_output_100ad` (see the module docstring's own TEMPORARY
    HEURISTIC paragraph on why that quantity is fixed rather than derived
    from price). Call that `metal_price`.

    The dominant recipe's own `inputs[ore] / outputs[metal]` ratio
    (`ore_per_metal`, kg of ore per kg of metal) is what turns a kilogram of
    metal into a kilogram of ore in `data/production/`'s own accounting.
    The ore's own recipe carries no inputs, so its RENT-FREE price
    (`ore_base_price`, labour only) is fixed and does not depend on the
    solve's iteration at all - this function is therefore called once,
    before the iteration starts, not once per round.

    Setting `existing_extraction_proxy = ore_base_price * ore_per_metal`
    (what the dominant recipe already implies a kilogram of metal's
    extraction costs, with no rent), the rent this function attributes to
    the metal is `max(0, metal_price - existing_extraction_proxy)` - the
    Ricardian gap between the marginal deposit's true price and what the
    zero-rent recipe already charges - and dividing that back by
    `ore_per_metal` gives `rent_per_kg_ore`, the number this function
    returns for that ore. Added onto `ore_base_price` inside
    `recipe_cost_and_allocation` and multiplied back through the dominant
    recipe's own `ore_per_metal`, it reproduces `metal_price` on that
    recipe's output EXACTLY (the division and the later multiplication use
    the same ratio); every OTHER recipe that consumes the same ore at a
    DIFFERENT ratio gets an approximation instead, by design - see the
    module docstring.

    A metal whose marginal deposit is cheap enough that the existing
    zero-rent recipe already prices above it (which can happen: the two
    numbers come from unrelated sources, `data/production/`'s own generic
    grade assumption and `sim/world/deposits.py`'s specific named
    deposits) gets exactly 0.0 rent here, not a negative one - rent is a
    surplus over cost of production, never a discount below it.
    """
    with open(deposits.RESOURCES_FILE) as handle:
        resources_json = json.load(handle)

    rent_by_ore_material = {}
    for ore_material, (metal, candidate_recipe_ids) in RENT_BEARING_ORE_MATERIALS.items():
        ore_entry = production_entries.get(ore_material)
        if ore_entry is None:
            # Gated out of this era (--civ), or (should not happen for a
            # base material the tree already validates) simply absent -
            # either way there is nothing to attach a rent to, so this ore
            # keeps the RENT_IS_ZERO default rather than a guess.
            continue
        dominant_entry = next(
            (production_entries[recipe_id] for recipe_id in candidate_recipe_ids
             if recipe_id in production_entries),
            None)
        if dominant_entry is None:
            # Every candidate recipe is gated out of this era too - iron
            # under an ungated future-tech solve missing BOTH blast furnace
            # and bloomery would land here, which should not happen for
            # this project's own civilizations but is handled the same way
            # as any other missing recipe: zero rent, not a guess.
            continue
        dominant_inputs = dominant_entry.get("inputs") or {}
        dominant_outputs = dominant_entry.get("outputs") or {}
        if ore_material not in dominant_inputs or not dominant_outputs:
            continue
        ore_per_metal = dominant_inputs[ore_material] / max(dominant_outputs.values())
        if ore_per_metal <= 0:
            continue

        ore_outputs = ore_entry.get("outputs") or {}
        if ore_material not in ore_outputs:
            continue
        ore_output_quantity = ore_outputs[ore_material]
        base_cost = recipe_cost_and_allocation(ore_material, ore_entry, {}, wage_by_trade)
        if base_cost is None:
            continue
        ore_base_total_hours, _ = base_cost
        ore_base_price_per_kg = ore_base_total_hours / ore_output_quantity
        existing_extraction_proxy_per_kg_metal = ore_base_price_per_kg * ore_per_metal

        deposits_for_metal = deposits.load_deposits(metal)
        quantity_demanded_tonnes_per_year = (
            resources_json["empire_output_100ad"][metal]["t_per_yr"])
        outcome = deposits.find_marginal_deposit(
            deposits_for_metal, quantity_demanded_tonnes_per_year)
        metal_price_per_kg = outcome.price_at_margin_labour_hours_per_kg

        rent_per_kg_metal = max(
            0.0, metal_price_per_kg - existing_extraction_proxy_per_kg_metal)
        rent_by_ore_material[ore_material] = rent_per_kg_metal / ore_per_metal

    return rent_by_ore_material


# See sim/world/land.py's own module docstring for the mechanism (the
# margin of cultivation over a civilization's own regions, not an ore
# deposit's grade) and for why this defaults to Rome's own territory when
# no --civ is given: mirroring rent_hours_per_kg_by_ore_material's own
# Rome-anchored default (data/world/resources.json's empire_output_100ad
# has no per-civilization breakdown either), even though land's OWN
# mechanism, unlike ore's, is genuinely per-civilization the moment --civ
# names one.
DEFAULT_LAND_CIVILIZATION = "rome_100ad"


def land_rent_hours_per_iugerum(production_entries, wage_by_trade,
                                civilization_id=None):
    """{"iugerum_land": hours of rent per iugerum}, or {} if there is no
    reference crop price or no priceable land to convert into one this
    round - see sim/world/land.py's own module docstring for the mechanism
    (the Ricardian margin of cultivation over a civilization's own held
    regions) and for why a civilization holding only one region prices
    land at exactly zero (a real finding, not a bug: no differential rent
    without at least two regions of different quality to compare).

    THE ALGEBRA. sim/world/land.py's own `margin_outcome_for_civilization`
    returns a supply-weighted average rent in kilograms of grain-equivalent
    per iugerum - a PHYSICAL quantity, not a price (see that module's own
    WHY THE HOURS CONVERSION LIVES IN sim/solve_prices.py, NOT HERE
    section for why the conversion happens here rather than there).
    Multiplying by wheat_kg's own ZERO-LAND-RENT price (labour only, exactly
    like rent_hours_per_kg_by_ore_material's own `ore_base_price_per_kg`)
    turns that physical surplus into the labour-hour unit this file prices
    everything else in. `iugerum_land` itself has no `inputs` and no
    `labour_hours` of its own (data/production/40_organics.json's own
    entry says so directly), so this rent figure becomes its WHOLE solved
    price with nothing else added - see recipe_cost_and_allocation's own
    rent_hours term.

    THE ZERO-LAND-RENT REFERENCE PRICE, AND WHY IT STAYS ZERO-RENT EVEN NOW
    THAT wheat_kg CONSUMES LAND (Complaints/49). Before this round wheat_kg
    truly had no `inputs` at all, so calling `recipe_cost_and_allocation`
    with an empty price dict gave its labour-only price by construction.
    wheat_kg now also states a `land_iugera_years` (see RENT ON GROWN AND
    LAND-LIMITED MATERIALS above), so the SAME call would otherwise return
    None the moment it tries to look up a price for `iugerum_land` that this
    empty dict does not have. The fix is to seed exactly that one price at
    0.0 rather than leave it absent - `{"iugerum_land": 0.0}` - which
    reproduces the pre-Complaints/49 answer exactly (0.0 hours/iugerum times
    any `land_iugera_years` is 0.0, so the land term drops out and only
    labour remains) rather than changing what this reference price MEANS.
    This is deliberately NOT circular: the reference price answers "what
    would wheat cost if land were free", which this function needs as a
    pure UNIT CONVERSION for land.py's physical rent, and it is computed
    once, outside the main iteration, the same way it always was - wheat's
    ACTUAL solved price (what every other recipe that consumes wheat_kg
    pays, and what bread is costed from) is computed by the ordinary
    Jacobi iteration in `solve()` below, WITH land_iugera_years priced in,
    using `iugerum_land`'s price that THIS function's own return value
    fixes beforehand. See WHY NO NEW CYCLE in the module docstring.
    """
    civilization_id = civilization_id or DEFAULT_LAND_CIVILIZATION
    wheat_entry = production_entries.get("wheat_kg")
    if wheat_entry is None:
        # Gated out of this era, or (should not happen - wheat_kg carries
        # requires_node: null, admitted to every era) simply absent. Either
        # way there is no reference crop price to convert the physical rent
        # into hours with, so land keeps the old RENT_IS_ZERO answer.
        return {}
    wheat_cost = recipe_cost_and_allocation(
        "wheat_kg", wheat_entry, {"iugerum_land": 0.0}, wage_by_trade)
    if wheat_cost is None:
        return {}
    _wheat_total_hours, wheat_output_prices = wheat_cost
    wheat_price_per_kg = wheat_output_prices.get("wheat_kg")
    if not wheat_price_per_kg:
        return {}

    try:
        outcome = land.margin_outcome_for_civilization(civilization_id)
    except (FileNotFoundError, KeyError):
        # An unknown civilization id, or one missing a population field -
        # should not happen for this project's own data/civilizations/
        # files, handled the same way a missing ore recipe is: no rent
        # guessed, the old zero-rent answer stands.
        return {}
    if outcome.price_kg_grain_equivalent_per_iugerum <= 0.0:
        return {}
    rent_hours = outcome.price_kg_grain_equivalent_per_iugerum * wheat_price_per_kg
    return {"iugerum_land": rent_hours}


def _capability_band_prices_this_round(required_grades_by_carrier, production_entries,
                                       prices, wage_by_trade, rent_hours_per_kg_by_material):
    # PER-CONSUMER GRADING: re-solved every round, from THIS round's
    # own (pre-update) `prices`, exactly like every candidate recipe
    # below is costed against those same prices (Jacobi - see this
    # function's own docstring on why every material updates from the
    # same round's starting point).
    return {
        carrier: {
            required_value: capability_price_for_requirement(
                carrier, required_value, production_entries, prices,
                wage_by_trade,
                rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
            for required_value in required_values
        }
        for carrier, required_values in required_grades_by_carrier.items()
    }


def _solve_round_candidates(production_entries, recipe_ids_in_order, resolvable_materials,
                            prices, wage_by_trade, rent_hours_per_kg_by_material,
                            band_price_by_carrier, floor_by_carrier):
    candidates_by_material = collections.defaultdict(list)
    for recipe_id in recipe_ids_in_order:
        entry = production_entries[recipe_id]
        outputs = entry.get("outputs") or {}
        if not outputs or not all(output_material in resolvable_materials for output_material in outputs):
            continue
        result = recipe_cost_and_allocation(
            recipe_id, entry, prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
            capability_band_price_by_carrier=band_price_by_carrier)
        if result is None:
            continue
        _total_cost, output_prices = result
        for material, price in output_prices.items():
            if not _meets_capability_floor(material, entry, floor_by_carrier):
                continue
            candidates_by_material[material].append((price, recipe_id))
    return candidates_by_material


def _solve_round_update_prices(resolvable_materials, prices, candidates_by_material,
                               damping, chosen_recipe_by_material):
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
    return new_prices, max_relative_change


def solve(production_entries, producers_of, resolvable_materials, wage_by_trade,
         damping=DAMPING_FACTOR, max_iterations=MAXIMUM_ITERATIONS,
         tolerance=CONVERGENCE_TOLERANCE, rent_hours_per_kg_by_material=None):
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

    PHYSICAL CAPABILITY CAPS, PER CONSUMER (Complaints/44, continued; see
    CAPABILITY_CAP_FIELDS and TEMPERATURE in the module docstring). Two
    things are computed once, before the very first round, from THIS
    solve's own `production_entries` alone - exactly like
    `rent_hours_per_kg_by_ore_material` is computed once rather than every
    round, because neither depends on the price vector: `floor_by_carrier`
    (the carrier's own universal default floor, e.g. thermal_mj's
    cap_heat_0700 rung) and `required_grades_by_carrier` (every DISTINCT
    requirement this era's own consumers actually state, the default
    included - see `capability_required_grades`).

    Every round after that, TWO things happen with those, in order:
    `capability_price_for_requirement` is re-solved for each distinct
    required value at THIS round's current prices (a technique's own cost
    moves every round, so which one clears a given requirement most
    cheaply can too) into `band_price_by_carrier`, and THEN every recipe
    is costed with that dict threaded through
    `recipe_cost_and_allocation`, so a consumer that states its own
    requirement pays its own graded price rather than the flat pool
    price. Choice of technique for the carrier MATERIAL itself (`thermal_
    mj`'s own entry in `resolvable_materials`, what an unlabelled consumer
    pays) still uses `_meets_capability_floor` against the plain
    `floor_by_carrier` - the universal default only, exactly as before
    this mechanism existed, and now correctly UNAFFECTED by any other
    consumer's own higher requirement (see TEMPERATURE for why that used
    to be a bug).
    """
    prices = {material: INITIAL_PRICE_GUESS_HOURS for material in resolvable_materials}
    chosen_recipe_by_material = {}
    recipe_ids_in_order = sorted(production_entries)  # stable order; see above
    floor_by_carrier = capability_floor_by_carrier(production_entries)
    required_grades_by_carrier = capability_required_grades(production_entries)

    final_residual = float("inf")
    iterations_run = 0
    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration

        band_price_by_carrier = _capability_band_prices_this_round(
            required_grades_by_carrier, production_entries, prices, wage_by_trade,
            rent_hours_per_kg_by_material)

        candidates_by_material = _solve_round_candidates(
            production_entries, recipe_ids_in_order, resolvable_materials, prices,
            wage_by_trade, rent_hours_per_kg_by_material, band_price_by_carrier,
            floor_by_carrier)

        prices, final_residual = _solve_round_update_prices(
            resolvable_materials, prices, candidates_by_material, damping,
            chosen_recipe_by_material)
        if final_residual < tolerance:
            break

    return prices, iterations_run, final_residual, chosen_recipe_by_material


def minor_joint_byproducts_are_unanchored(production_entries, chosen_recipe_by_material,
                                          prices, wage_by_trade, share_threshold=0.5,
                                          rent_hours_per_kg_by_material=None):
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
        result = recipe_cost_and_allocation(
            recipe_id, entry, prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if result is None:
            continue
        total_process_cost, _output_prices = result
        if total_process_cost <= 0:
            continue
        value_share = (outputs[material] * prices[material]) / total_process_cost
        if value_share < share_threshold:
            unanchored[material] = value_share
    return unanchored
