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
  * `capital`, if present, is held to the same standard as everything else:
    every `build_materials` key is a real material, every `build_labour_hours`
    trade is in the wage table, a capital good is built from SOMETHING (not
    nothing), `service_life_years` and `annual_output_at_basis` are positive
    physical facts rather than absent or zero, and `capital_basis` says why -
    fifty characters minimum, same bar as `yield_basis`. See
    data/production/_SCHEMA.md's CAPITAL section for the field's shape.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRODUCTION_DIR = os.path.join(ROOT, "data", "production")

sys.path.insert(0, HERE)
import simulator


def load_production():
    """Merge every file in data/production/ by material key.

    One file per material family so that several authors can work at once
    without colliding, exactly like data/branches/. A key defined in two files
    is an ERROR rather than a silent overwrite - that is the failure mode the
    branch merge has, where treetool keeps the first and the second author's
    work disappears without a word.
    """
    merged, defined_in, duplicates = {}, {}, []
    for filename in sorted(os.listdir(PRODUCTION_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(PRODUCTION_DIR, filename)
        with open(path) as handle:
            batch = json.load(handle)
        for name, entry in (batch.get("materials") or {}).items():
            if name in merged:
                duplicates.append("%s is defined in both %s and %s"
                                  % (name, defined_in[name], filename))
                continue
            merged[name] = entry
            defined_in[name] = filename
    return merged, duplicates


def materials_the_tree_consumes(nodes):
    counts = collections.Counter()
    for node in nodes.values():
        for material_key in (node.get("mat") or {}):
            counts[material_key] += 1
    return counts


def check(entries, known_materials, known_trades):
    problems = []
    for name, entry in sorted(entries.items()):
        where = "%s" % name

        outputs = entry.get("outputs") or {}
        if not outputs:
            problems.append("%s: produces nothing" % where)
        for key in outputs:
            if key not in known_materials:
                problems.append("%s: output '%s' is not a material the tree "
                                "uses and has no entry of its own" % (where, key))

        inputs = entry.get("inputs") or {}
        for key, quantity in inputs.items():
            if key not in known_materials:
                problems.append("%s: input '%s' is not a known material - a "
                                "typo here reads as 'this input is free'"
                                % (where, key))
            if not isinstance(quantity, (int, float)) or quantity < 0:
                problems.append("%s: input '%s' has quantity %r"
                                % (where, key, quantity))

        if not inputs and not entry.get("extracted_from"):
            problems.append("%s: no inputs and no extracted_from - this "
                            "material appears from nowhere" % where)

        for trade, hours in (entry.get("labour_hours") or {}).items():
            if trade not in known_trades:
                problems.append("%s: trade '%s' is not in the wage table"
                                % (where, trade))
            if not isinstance(hours, (int, float)) or hours < 0:
                problems.append("%s: trade '%s' has %r hours"
                                % (where, trade, hours))

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
                    if not isinstance(good, dict):
                        problems.append("%s is not an object" % good_where)
                        continue

                    if not (good.get("good") or "").strip():
                        problems.append(
                            "%s: 'good' is missing or empty - say what the "
                            "capital good IS (a furnace, a mill, a pan)"
                            % good_where)

                    build_materials = good.get("build_materials") or {}
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

                    build_labour = good.get("build_labour_hours") or {}
                    for trade, hours in build_labour.items():
                        if trade not in known_trades:
                            problems.append(
                                "%s: trade '%s' is not in the wage table"
                                % (good_where, trade))
                        if not isinstance(hours, (int, float)) or hours < 0:
                            problems.append(
                                "%s: trade '%s' has %r hours"
                                % (good_where, trade, hours))

                    if not build_materials and not build_labour:
                        problems.append(
                            "%s: no build_materials and no "
                            "build_labour_hours - this capital good is built "
                            "from nothing" % good_where)

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

        basis = (entry.get("yield_basis") or "").strip()
        if len(basis) < 50:
            problems.append("%s: yield_basis is missing or too short to be a "
                            "reason. Say where the numbers come from in "
                            "physical terms." % where)

        if entry.get("conf") not in ("A", "B", "C", "D"):
            problems.append("%s: conf must be A, B, C or D, not %r"
                            % (where, entry.get("conf")))

        for key in outputs:
            if key in inputs and len(inputs) == 1:
                problems.append("%s: its only input is its own output" % where)

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
            kilogram_outputs = sum(q for q in outputs.values()
                                   if isinstance(q, (int, float)))
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


def main(argv=None):
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
    known_trades = set(prices.get("wage_rates_denarii_per_hour") or {})
    known_materials = set(consumed) | set(entries)

    for duplicate in duplicates:
        print("  DUPLICATE %s" % duplicate)

    if arguments.entry:
        entry = entries.get(arguments.entry)
        if entry is None:
            print("no entry for %r" % arguments.entry)
            return 1
        print(json.dumps(entry, indent=1))
        problems = check({arguments.entry: entry}, known_materials, known_trades)
        for problem in problems:
            print("  PROBLEM %s" % problem)
        return 1 if problems else 0

    if arguments.todo:
        missing = [(name, count) for name, count in consumed.most_common()
                   if name not in entries]
        print("%d materials still have no production entry, worst first:"
              % len(missing))
        for name, count in missing:
            print("   %-26s consumed by %4d nodes" % (name, count))
        return 0

    problems = check(entries, known_materials, known_trades) + duplicates
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
    print("%d problem(s)" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
