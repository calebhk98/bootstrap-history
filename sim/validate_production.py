#!/usr/bin/env python3
"""Check data/production/ against the tree, the trades and itself.

    python3 sim/validate_production.py            errors, then a coverage line
    python3 sim/validate_production.py --todo     what is still missing, worst first
    python3 sim/validate_production.py --entry copper_kg

Exit 0 when every entry present is well formed. Missing entries are reported
as coverage, not as errors: this file is being filled in, and a validator that
fails until it is finished is a validator nobody can run.

WHAT IT CHECKS, and why each one is here rather than left to review:

  * Every material key names something. A typo in an input key is invisible
    otherwise - the entry looks complete and the price system quietly treats a
    real input as free.
  * Every trade exists in the wage table. Same failure, same invisibility.
  * No entry produces nothing, and no manufactured entry consumes nothing.
    An entry with neither inputs nor `extracted_from` is claiming a material
    appears from nowhere, which is the one thing physical accounting exists to
    forbid.
  * `yield_basis` is present and says something. This is the field that
    separates a derived number from a guess, and an entry without it is a
    guess whether or not it is correct. Fifty characters is a low bar and it
    is deliberately low - it catches "TODO" and "estimate", not honest brevity.
  * No cycle a material cannot escape. Iron needs charcoal needs an axe needs
    iron is FINE and normal - the price system solves that as a system of
    equations. What is not fine is a material that is its own only input, which
    is an authoring slip rather than an economy.
  * `thermal_mj`, `mechanical_mj`, `electrical_mj` and `energy_mj`, if
    present, are non-negative numbers. See data/production/70_energy.json
    and ENERGY in sim/solve_prices.py's module docstring for what the first
    three are priced against, and why the fourth stays deliberately
    uncosted.
  * `capital`, if present, is held to the same standard as everything else:
    every `build_materials` key is a real material, every `build_labour_hours`
    trade is in the wage table, a capital good is built from SOMETHING (not
    nothing), `service_life_years` and `annual_output_at_basis` are positive
    physical facts rather than absent or zero, and `capital_basis` says why -
    fifty characters minimum, same bar as `yield_basis`. See
    data/production/_SCHEMA.md's CAPITAL section for the field's shape.

SHAPE OF THIS MODULE. `check()` runs one material entry at a time through a
sequence of independent checks - a typo'd material key, a missing yield_basis,
an ill-formed capital good, and so on - each of which can append its own
problems to the list for that entry. Below, each of those checks is its own
function, taking exactly the data it needs and returning the problems it
found; `check()` itself just walks the sorted entries and calls each check
function in a fixed order, so the order problems are reported in is stable.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRODUCTION_DIR = os.path.join(ROOT, "data", "production")

# The three energy carriers (see ENERGY in sim/solve_prices.py's module
# docstring). Kept as a separate copy of the same tuple that file declares
# as ENERGY_CARRIER_FIELDS, rather than imported from it, because
# sim/solve_prices.py imports FROM this module - importing the other way
# too would be circular.
ENERGY_CARRIER_FIELDS = ("thermal_mj", "mechanical_mj", "electrical_mj")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def load_production():
    """Load the one canonical base-and-enabled-mod production graph."""
    from sim.engine.catalog import load_production_catalog
    return load_production_catalog(ROOT), []


def materials_the_tree_consumes(nodes):
    counts = collections.Counter()
    for node in nodes.values():
        for material_key in (node.get("mat") or {}):
            counts[material_key] += 1
    return counts


def check_outputs(where, entry, known_materials):
    """No entry produces nothing, and every output is a known material."""
    problems = []
    outputs = entry.get("outputs") or {}
    if not outputs:
        problems.append("%s: produces nothing" % where)
    for key in outputs:
        if key not in known_materials:
            problems.append("%s: output '%s' is not a material the tree "
                            "uses and has no entry of its own" % (where, key))
    return problems


def check_inputs(where, entry, known_materials):
    """Every input is a known material key with a sane, non-negative quantity."""
    problems = []
    inputs = entry.get("inputs") or {}
    for key, quantity in inputs.items():
        if key not in known_materials:
            problems.append("%s: input '%s' is not a known material - a "
                            "typo here reads as 'this input is free'"
                            % (where, key))
        if not isinstance(quantity, (int, float)) or quantity < 0:
            problems.append("%s: input '%s' has quantity %r"
                            % (where, key, quantity))
    return problems


def check_has_source(where, entry):
    """A manufactured entry must consume SOMETHING - inputs, extraction, or energy."""
    problems = []
    inputs = entry.get("inputs") or {}

    # A CONVERSION technique (data/production/70_energy.json's
    # heat-engine, dynamo, motor, resistance/arc and friction entries)
    # consumes a real physical input - another energy carrier - through
    # one of the three energy sibling fields instead of `inputs`, which
    # is exactly as real a consumption as an ordinary material and must
    # count the same way here, or every conversion recipe would wrongly
    # read as claiming its output appears from nothing.
    draws_on_energy_carrier = any(
        entry.get(energy_field) for energy_field in ENERGY_CARRIER_FIELDS)
    if not inputs and not entry.get("extracted_from") and not draws_on_energy_carrier:
        problems.append("%s: no inputs, no extracted_from and no energy "
                        "carrier field - this material appears from "
                        "nowhere" % where)
    return problems


def check_labour_hours(where, entry, known_trades):
    """Every labour trade has registered identity and sane non-negative hours."""
    problems = []
    for trade, hours in (entry.get("labour_hours") or {}).items():
        if trade not in known_trades:
            problems.append("%s: trade '%s' is not in the trade registry"
                            % (where, trade))
        if not isinstance(hours, (int, float)) or hours < 0:
            problems.append("%s: trade '%s' has %r hours"
                            % (where, trade, hours))
    return problems


def check_energy_carrier_fields(where, entry):
    """thermal_mj, mechanical_mj, electrical_mj and energy_mj, if present, are non-negative numbers."""
    problems = []

    # ENERGY. thermal_mj, mechanical_mj and electrical_mj are all priced,
    # through sim/solve_prices.py's three-way energy market
    # (data/production/70_energy.json) - a typo turning one into a
    # string or a negative number would silently vanish into `or 0.0`
    # there exactly like a bad `inputs` quantity would. energy_mj is the
    # residual field for a genuine gap (a technology none of the three
    # energy markets reaches) and gets the same type check even though
    # solve_prices.py deliberately leaves it uncosted.
    for energy_field in ENERGY_CARRIER_FIELDS + ("energy_mj",):
        if energy_field in entry:
            value = entry[energy_field]
            if not isinstance(value, (int, float)) or value < 0:
                problems.append("%s: '%s' must be a non-negative number, "
                                "not %r" % (where, energy_field, value))
    return problems


def check_requires_node(where, entry, known_nodes):
    """WHEN this technique becomes available, verified against the tree."""
    problems = []

    # REQUIRES_NODE. Which tech-tree node has to be reached before
    # anyone can run this technique. Three states, and the difference
    # between them is the whole point of the field:
    #
    #   absent      - nobody has classified this entry yet. It is
    #                 admitted to an ungated solve and EXCLUDED from a
    #                 gated one, and counted in the coverage line so the
    #                 gap is a number rather than a silence.
    #   null        - available to anyone, anywhere, with no technology
    #                 at all: gathering firewood, quarrying stone,
    #                 growing wheat. A deliberate statement, not a gap.
    #   "node_id"   - available once that node is reached.
    #
    # This exists because sim/solve_prices.py had no notion of WHEN: a
    # 100 AD scenario priced its electricity off a photovoltaic panel,
    # which is the defect Complaints/39 records. A typo here reads as
    # "this technique is never available", which is why the id is
    # checked against the tree rather than taken on trust.
    if "requires_node" in entry:
        required = entry["requires_node"]
        if required is not None:
            if not isinstance(required, str):
                problems.append("%s: requires_node must be a tech-tree "
                                "node id or null, not %r"
                                % (where, required))
            elif known_nodes is not None and required not in known_nodes:
                problems.append("%s: requires_node '%s' is not a node in "
                                "the tech tree - a typo here silently "
                                "removes this technique from every gated "
                                "solve" % (where, required))
    return problems


def check_capital_build_materials(good_where, build_materials, known_materials):
    """Every build_materials key is a real material with a sane quantity."""
    problems = []
    for key, quantity in build_materials.items():
        if key not in known_materials:
            problems.append(
                "%s: build_materials '%s' is not a known "
                "material - a typo here reads as 'this "
                "capital good is free'" % (good_where, key))
        if not isinstance(quantity, (int, float)) or quantity < 0:
            problems.append(
                "%s: build_materials '%s' has quantity %r"
                % (good_where, key, quantity))
    return problems


def check_capital_build_labour(good_where, build_labour, known_trades):
    """Every build_labour_hours trade is in the wage table with a sane hours figure."""
    problems = []
    for trade, hours in build_labour.items():
        if trade not in known_trades:
            problems.append(
                "%s: trade '%s' is not in the wage table"
                % (good_where, trade))
        if not isinstance(hours, (int, float)) or hours < 0:
            problems.append(
                "%s: trade '%s' has %r hours"
                % (good_where, trade, hours))
    return problems


def check_capital_physical_facts(good_where, good):
    """service_life_years, annual_output_at_basis, capital_basis and conf."""
    problems = []
    service_life = good.get("service_life_years")
    if not isinstance(service_life, (int, float)) or service_life <= 0:
        problems.append(
            "%s: service_life_years must be a positive "
            "number of years, not %r - it is a physical fact "
            "about wear (how long before it is rebuilt or "
            "relined), not a bookkeeping convention"
            % (good_where, service_life))

    annual_output = good.get("annual_output_at_basis")
    if not isinstance(annual_output, (int, float)) or annual_output <= 0:
        problems.append(
            "%s: annual_output_at_basis must be a positive "
            "number, not %r" % (good_where, annual_output))

    capital_basis = (good.get("capital_basis") or "").strip()
    if len(capital_basis) < 50:
        problems.append(
            "%s: capital_basis is missing or too short to be "
            "a reason. Say where the build bill, service "
            "life and annual output come from in physical "
            "terms." % good_where)

    if good.get("conf") not in ("A", "B", "C", "D"):
        problems.append(
            "%s: conf must be A, B, C or D, not %r"
            % (good_where, good.get("conf")))
    return problems


def check_one_capital_good(good_where, good, known_materials, known_trades):
    """One item of a capital list: real materials, real trades, built from something, and why."""
    problems = []
    if not isinstance(good, dict):
        problems.append("%s is not an object" % good_where)
        return problems

    if not (good.get("good") or "").strip():
        problems.append(
            "%s: 'good' is missing or empty - say what the "
            "capital good IS (a furnace, a mill, a pan)"
            % good_where)

    build_materials = good.get("build_materials") or {}
    problems.extend(check_capital_build_materials(good_where, build_materials, known_materials))

    build_labour = good.get("build_labour_hours") or {}
    problems.extend(check_capital_build_labour(good_where, build_labour, known_trades))

    if not build_materials and not build_labour:
        problems.append(
            "%s: no build_materials and no "
            "build_labour_hours - this capital good is built "
            "from nothing" % good_where)

    problems.extend(check_capital_physical_facts(good_where, good))
    return problems


def check_capital(where, entry, known_materials, known_trades):
    """capital, if present, is a non-empty list of well-formed capital goods."""
    problems = []

    # CAPITAL, if present. Same standard as everything else in this file:
    # real material keys, real trades, a positive physical service life
    # and annual output rather than a bookkeeping placeholder, and a
    # stated reason - build bills that are silently free or silently
    # eternal are exactly as invisible as a free input would be.
    capital_goods = entry.get("capital")
    if capital_goods is not None:
        if not isinstance(capital_goods, list) or not capital_goods:
            problems.append(
                "%s: capital is present but is not a non-empty list - "
                "remove the field entirely if there is nothing to "
                "capitalise here" % where)
        else:
            for index, good in enumerate(capital_goods):
                good_where = "%s: capital[%d]" % (where, index)
                problems.extend(check_one_capital_good(
                    good_where, good, known_materials, known_trades))
    return problems


def check_yield_basis(where, entry):
    """yield_basis is present and says something, not just holds the field."""
    problems = []
    basis = (entry.get("yield_basis") or "").strip()
    if len(basis) < 50:
        problems.append("%s: yield_basis is missing or too short to be a "
                        "reason. Say where the numbers come from in "
                        "physical terms." % where)
    return problems


def check_conf(where, entry):
    """conf is one of the four defined grades."""
    problems = []
    if entry.get("conf") not in ("A", "B", "C", "D"):
        problems.append("%s: conf must be A, B, C or D, not %r"
                        % (where, entry.get("conf")))
    return problems


def check_self_referential_input(where, entry):
    """No material is its own only input."""
    problems = []
    outputs = entry.get("outputs") or {}
    inputs = entry.get("inputs") or {}
    for key in outputs:
        if key in inputs and len(inputs) == 1:
            problems.append("%s: its only input is its own output" % where)
    return problems


def check_mass_conservation(where, entry):
    """A manufactured entry cannot yield more kilograms than it consumes."""
    problems = []
    outputs = entry.get("outputs") or {}
    inputs = entry.get("inputs") or {}

    # CONSERVATION OF MASS, where the units allow it to be checked.
    #
    # Matter does not appear. A manufactured entry cannot yield more
    # kilograms than the kilograms it consumes - not "should not", cannot.
    # The reverse is normal and expected: most of the input mass leaves as
    # slag, as CO2, as water, as scale, and a smelt that turns 50 tonnes of
    # ore into one tonne of metal is doing exactly what it should.
    #
    # Only checked where every output and at least one input is quoted in
    # kilograms, because this file also carries cubic metres of timber,
    # grams of platinum, thousands of bricks and an iugerum of land, and
    # adding those together would be arithmetic about nothing. An entry
    # that fails this has either an inverted ratio or a unit slip, and both
    # are invisible on a read-through: the numbers look like numbers.
    kilogram_inputs = sum(quantity for key, quantity in inputs.items()
                          if key.endswith("_kg")
                          and isinstance(quantity, (int, float)))
    if outputs and all(key.endswith("_kg") for key in outputs) and inputs:
        kilogram_outputs = sum(quantity for quantity in outputs.values()
                               if isinstance(quantity, (int, float)))
        if kilogram_inputs > 0:
            if kilogram_outputs > kilogram_inputs:
                problems.append(
                    "%s: yields %.0f kg from %.0f kg of inputs. Matter "
                    "does not appear - check for an inverted ratio or a "
                    "unit slip." % (where, kilogram_outputs, kilogram_inputs))
        else:
            # THE CHECK ABOVE CAN BE DODGED, AND ONCE WAS, BY ACCIDENT.
            #
            # An entry producing kilograms whose every input is quoted in
            # some other unit - cubic metres of timber, cubic metres of
            # hydrogen - has nothing to weigh, so the conservation test
            # simply did not run and the entry passed in silence. That is
            # how wood_pulp_kg was briefly written to make pulp out of
            # timber_m3: matter appearing from nowhere, and a clean bill of
            # health, because the only check that would have noticed
            # measured a quantity the entry did not have.
            #
            # Reported rather than passed. Usually the honest fix is the
            # one that entry took - source the mass from a material that is
            # actually weighed - and where it genuinely is not possible,
            # saying so out loud is still better than silence, which reads
            # exactly like success.
            problems.append(
                "%s: yields %.0f kg but no input is quoted in kilograms "
                "(%s), so conservation of mass cannot be checked at all. "
                "Source the mass from a weighed material, or say in "
                "yield_basis why it cannot be."
                % (where, kilogram_outputs, ", ".join(sorted(inputs))))
    return problems


def check(entries, known_materials, known_trades, known_nodes=None):
    problems = []
    for name, entry in sorted(entries.items()):
        where = "%s" % name
        problems.extend(check_outputs(where, entry, known_materials))
        problems.extend(check_inputs(where, entry, known_materials))
        problems.extend(check_has_source(where, entry))
        problems.extend(check_labour_hours(where, entry, known_trades))
        problems.extend(check_energy_carrier_fields(where, entry))
        problems.extend(check_requires_node(where, entry, known_nodes))
        problems.extend(check_capital(where, entry, known_materials, known_trades))
        problems.extend(check_yield_basis(where, entry))
        problems.extend(check_conf(where, entry))
        problems.extend(check_self_referential_input(where, entry))
        problems.extend(check_mass_conservation(where, entry))

    return problems


def run_entry_mode(arguments, entries, known_materials, known_trades, nodes):
    """--entry: show one entry and check only it."""
    entry = entries.get(arguments.entry)
    if entry is None:
        print("no entry for %r" % arguments.entry)
        return 1
    print(json.dumps(entry, indent=1))
    problems = check({arguments.entry: entry}, known_materials, known_trades,
                     known_nodes=set(nodes))
    for problem in problems:
        print("  PROBLEM %s" % problem)
    return 1 if problems else 0


def run_todo_mode(consumed, entries):
    """--todo: list materials with no entry yet, worst first."""
    missing = [(name, count) for name, count in consumed.most_common()
               if name not in entries]
    print("%d materials still have no production entry, worst first:"
          % len(missing))
    for name, count in missing:
        print("   %-26s consumed by %4d nodes" % (name, count))
    return 0


def run_default_mode(entries, duplicates, known_materials, known_trades, nodes, consumed):
    """No flags: run every check, then report coverage."""
    problems = check(entries, known_materials, known_trades,
                     known_nodes=set(nodes)) + duplicates
    for problem in problems:
        print("  %s" % problem)

    # conf D IS A DELETION QUEUE, NOT A REFINEMENT QUEUE. It marks an entry
    # that is wrong in kind - the thing it describes is not a material, has no
    # mass, or is a person - rather than one whose number is merely uncertain.
    # Listed separately because the two call for opposite responses and the
    # first round of authoring had no way to say which it meant.
    placeholders = sorted(name for name, entry in entries.items()
                          if entry.get("conf") == "D")
    if placeholders:
        print()
        print("%d entry(s) marked conf D - PLACEHOLDERS, wrong in kind rather "
              "than uncertain in degree." % len(placeholders))
        print("These want DELETING once whatever consumes them is fixed, not "
              "refining:")
        for name in placeholders:
            print("   %s" % name)

    covered = sum(count for name, count in consumed.items() if name in entries)
    total = sum(consumed.values())
    print()
    print("%d of %d materials have a production entry (%.1f%%)"
          % (len(set(entries) & set(consumed)), len(consumed),
             100.0 * len(set(entries) & set(consumed)) / max(1, len(consumed))))
    print("weighted by how often the tree consumes them: %.1f%% (%d of %d "
          "consumption sites)" % (100.0 * covered / max(1, total), covered, total))
    # ERA COVERAGE. Separate from material coverage and deliberately printed
    # next to it: an entry can be complete in every physical respect and
    # still be unusable by a gated solve, because nothing says when the
    # technique becomes available. Unclassified entries are silently
    # DROPPED from a gated solve, so this number is the one that says how
    # much of the cost base a dated question can actually see.
    classified = [name for name, entry in entries.items()
                  if "requires_node" in entry]
    always = [name for name in classified if entries[name]["requires_node"] is None]
    print("%d of %d entries say when they become available (%.1f%%); %d of "
          "those need no technology at all"
          % (len(classified), len(entries),
             100.0 * len(classified) / max(1, len(entries)), len(always)))
    print("%d problem(s)" % len(problems))
    return 1 if problems else 0


def main(argv=None):
    from sim import simulator
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--todo", action="store_true",
                        help="list materials with no entry yet, worst first")
    parser.add_argument("--entry", help="show one entry and check only it")
    arguments = parser.parse_args(argv)

    _tree, prices, nodes, _wages, _goods = simulator.load()
    if not isinstance(nodes, dict):
        nodes = {node["id"]: node for node in nodes}

    entries, duplicates = load_production()
    consumed = materials_the_tree_consumes(nodes)
    from sim.engine.catalog import load_trade_registry, material_namespace
    known_trades = set(load_trade_registry(ROOT, entries))
    # A material is known if the tree consumes it, if some entry's own key
    # names it (true for most single-technique materials), OR if some
    # entry's `outputs` produces it - the case a recipe-id-vs-material-key
    # split (salt_solar_kg -> salt_kg, zinc_electrolytic_kg -> zinc_kg) had
    # been getting right only by accident, because those materials also
    # happen to be tree-consumed. data/production/70_energy.json's
    # thermal_mj, mechanical_mj and electrical_mj are produced by entries
    # keyed thermal_mj_charcoal/_coal/_electrical_resistance/_friction,
    # mechanical_mj_waterwheel/_human_muscle/_motor/_heat_engine_* and
    # electrical_mj_dynamo/_photovoltaic, consumed only by OTHER production
    # entries rather than by the tree, so they need the `outputs` half of
    # this union to be seen as known at all.
    known_materials = material_namespace(entries, nodes.values())

    for duplicate in duplicates:
        print("  DUPLICATE %s" % duplicate)

    if arguments.entry:
        return run_entry_mode(arguments, entries, known_materials, known_trades, nodes)

    if arguments.todo:
        return run_todo_mode(consumed, entries)

    return run_default_mode(entries, duplicates, known_materials, known_trades, nodes, consumed)


if __name__ == "__main__":
    sys.exit(main())
