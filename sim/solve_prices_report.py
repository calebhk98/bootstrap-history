"""The reporting front end: `print_why`'s recursive cost breakdown, the
default price-table report, the `--compare` report, and the CLI's own
`main`.

See sim/solve_prices.py's own module docstring for why "the module
docstring" in every comment and docstring below means sim/solve_prices.py's
own module docstring, not either sibling file's - that essay is the design
reasoning for the whole tool and lives there rather than divided by
function; and see sim/solve_prices_core.py's own module docstring for the
composition-point structure the three files form. This file only formats
and prints a price sim/solve_prices_core.py has already computed: every
`_print_*` helper below, `print_why`, `_run_compare_report`, and `main`
(the argparse CLI `python3 sim/solve_prices.py` runs).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from sim.validate_production import load_production, materials_the_tree_consumes  # noqa: E402
from sim.world import land                      # noqa: E402  (RENT ON ARABLE LAND, in _print_rent_summary)

from sim.solve_prices_core import (                 # noqa: E402
    CAPABILITY_CAP_FIELDS,
    CONVERGENCE_TOLERANCE,
    DAMPING_FACTOR,
    DEFAULT_LAND_CIVILIZATION,
    ENERGY_CARRIER_FIELDS,
    NUMERAIRE_TRADE,
    RENT_BEARING_ORE_MATERIALS,
    _capability_graded_price,
    _meets_capability_floor,
    build_producers_index,
    capability_floor_by_carrier,
    capability_price_for_requirement,
    capability_required_grades,
    compute_resolvable_materials,
    land_rent_hours_per_iugerum,
    load_starting_technologies,
    minor_joint_byproducts_are_unanchored,
    recipe_cost_and_allocation,
    rent_hours_per_kg_by_ore_material,
    solve,
    techniques_available_to,
    wage_ratios_by_trade,
)


def format_hours(value):
    if value >= 100:
        return "%.1f" % value
    if value >= 1:
        return "%.3f" % value
    return "%.5f" % value


def _default_capability_band_price_by_carrier(production_entries, prices, wage_by_trade,
                                                rent_hours_per_kg_by_material):
    # The same {carrier: {required_value: (price, recipe_id)}} shape `solve`
    # builds each round - see print_why's own docstring for why this is
    # computed once at the top-level call and threaded through recursion
    # rather than rebuilt at every level.
    return {
        carrier: {
            required_value: capability_price_for_requirement(
                carrier, required_value, production_entries, prices,
                wage_by_trade,
                rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
            for required_value in required_values
        }
        for carrier, required_values in capability_required_grades(production_entries).items()
    }


def _print_extraction_rent_explanation(pad, material, entry, rent_by_kg):
    # Why this material's price does or does not carry a Ricardian rent -
    # see RENT ON EXTRACTED MATERIALS and RENT ON GROWN AND LAND-LIMITED
    # MATERIALS in the module docstring.
    if entry.get("extracted_from"):
        material_rent_per_kg = rent_by_kg.get(material)
        if material_rent_per_kg and material == "iugerum_land":
            print("%s  EXTRACTED from %s - no cost of production, only a "
                  "Ricardian rent of %s h/iugerum from sim/world/land.py's "
                  "margin of cultivation over a civilization's own held "
                  "regions (see RENT ON ARABLE LAND)."
                  % (pad, entry["extracted_from"], format_hours(material_rent_per_kg)))
        elif material_rent_per_kg:
            print("%s  EXTRACTED from %s - labour plus a Ricardian rent of "
                  "%s h/kg from sim/world/deposits.py's marginal-deposit "
                  "supply curve (see RENT ON EXTRACTED MATERIALS)."
                  % (pad, entry["extracted_from"], format_hours(material_rent_per_kg)))
        elif entry.get("land_iugera_years"):
            # GROWN/land-limited (Complaints/49): this material's OWN
            # extracted_from rent term (the ore-style mechanism above) is
            # zero, as it always is for anything that is not one of the six
            # named ores - but that is not the same as "no rent at all" any
            # more, because this recipe also consumes iugerum_land, whose
            # own rent shows up in the LAND line below rather than here.
            print("%s  EXTRACTED from %s - no separate cost of production "
                  "of its own; its land cost is priced through iugerum_land "
                  "(see the LAND line below and RENT ON GROWN AND LAND-"
                  "LIMITED MATERIALS)."
                  % (pad, entry["extracted_from"]))
        else:
            print("%s  EXTRACTED from %s - no cost of production, only "
                  "labour and a rent this round fixed at 0.0 (see RENT ON "
                  "EXTRACTED MATERIALS - this material is not one of the "
                  "six ores sim/world/deposits.py covers, nor a material "
                  "that consumes iugerum_land - see sim/world/land.py)."
                  % (pad, entry["extracted_from"]))


def _print_rejected_techniques(pad, material, recipe_id, production_entries, producers_of):
    # Split rejections by REASON (Complaints/44) - see print_why's call site
    # for why a capability floor and a price comparison are different findings.
    candidates = sorted(set(producers_of.get(material, [])) - {recipe_id})
    if candidates:
        # Split rejections by REASON (Complaints/44) - a technique that
        # cannot physically reach what this material needs is a different
        # finding from one that merely costs more today, and conflating
        # them is exactly how "thermal_mj_friction should never be chosen"
        # stopped being verifiable as anything but a hope. See
        # CAPABILITY_CAP_FIELDS and _meets_capability_floor above.
        floor_by_carrier = capability_floor_by_carrier(production_entries)
        capped = CAPABILITY_CAP_FIELDS.get(material)
        notes = []
        for candidate_id in candidates:
            candidate_entry = production_entries[candidate_id]
            if capped and not _meets_capability_floor(material, candidate_entry, floor_by_carrier):
                reached_field, _needed_field, _default_floor = capped
                notes.append("%s (reaches %s, this era needs >= %s - see "
                             "CAPABILITY_CAP_FIELDS)" % (
                             candidate_id, candidate_entry.get(reached_field),
                             floor_by_carrier[material]))
            else:
                notes.append("%s (more expensive at current prices)" % candidate_id)
        print("%s  other techniques considered and rejected: %s"
              % (pad, ", ".join(notes)))


def _print_joint_output_note(pad, other_outputs, outputs):
    if other_outputs:
        print("%s  joint output of this batch, also yielding: %s - cost "
              "split across outputs by current value share" % (
              pad, ", ".join("%s (%.4g)" % (key, outputs[key]) for key in other_outputs)))


def _print_inputs(pad, inputs, output_quantity, prices, total_process_cost):
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


def _print_labour(pad, entry, wage_by_trade, total_process_cost):
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


def _print_rent_this_batch(pad, outputs, rent_by_kg, total_process_cost):
    rent_this_batch = sum(quantity * rent_by_kg.get(output_material, 0.0)
                          for output_material, quantity in outputs.items())
    if rent_this_batch > 0:
        share_text = ("%.1f%% of process cost" % (100.0 * rent_this_batch / total_process_cost)
                     if total_process_cost > 0 else "n/a")
        print("%s  rent (Ricardian, see RENT ON EXTRACTED MATERIALS): "
              "%10s h  (%s)" % (pad, format_hours(rent_this_batch), share_text))


def _print_land(pad, entry, prices, total_process_cost):
    land_iugera_years = entry.get("land_iugera_years") or 0.0
    if land_iugera_years:
        land_price = prices.get("iugerum_land")
        land_cost = land_iugera_years * land_price if land_price is not None else None
        share_text = ("%.1f%% of process cost" % (100.0 * land_cost / total_process_cost)
                     if land_cost is not None and total_process_cost > 0 else "n/a")
        print("%s  land (see RENT ON GROWN AND LAND-LIMITED MATERIALS): "
              "%10.4g iugera-yrs @ %10s h/iugerum-yr = %10s h  (%s)" % (
              pad, land_iugera_years,
              format_hours(land_price) if land_price is not None else "NO PRICE",
              format_hours(land_cost) if land_cost is not None else "?", share_text))
    return land_iugera_years


def _print_capital(pad, entry, prices, wage_by_trade, outputs, total_process_cost):
    capital_goods = entry.get("capital") or []
    if capital_goods:
        print("%s  capital (amortised build cost, see CAPITAL in the module "
              "docstring):" % pad)
        for capital_good in capital_goods:
            build_materials = capital_good.get("build_materials") or {}
            build_labour_hours = capital_good.get("build_labour_hours") or {}
            build_cost = sum(quantity * prices.get(build_material, 0.0)
                             for build_material, quantity in build_materials.items())
            build_cost += sum(hours * wage_by_trade.get(trade, 0.0)
                              for trade, hours in build_labour_hours.items())
            lifetime_output = (capital_good["service_life_years"]
                               * capital_good["annual_output_at_basis"])
            charge = build_cost / lifetime_output
            # `charge` is per unit of OUTPUT (see recipe_cost_and_allocation);
            # total_process_cost is per BATCH, so scale by the batch quantity
            # before comparing them, the same way the real cost sum does.
            batch_output_quantity = max(outputs.values()) if outputs else 1.0
            share_text = ("%.2f%% of process cost"
                         % (100.0 * charge * batch_output_quantity / total_process_cost)
                         if total_process_cost > 0 else "n/a")
            print("%s    %-40s %10s h build / %.4g lifetime units = %10s h/unit  (%s)"
                  % (pad, capital_good.get("good", "?"), format_hours(build_cost),
                     lifetime_output, format_hours(charge), share_text))


def _print_energy(pad, entry, prices, capability_band_price_by_carrier,
                   chosen_recipe_by_material, total_process_cost):
    energy_labels = {"thermal_mj": "thermal (heat) energy",
                     "mechanical_mj": "mechanical (shaft) energy",
                     "electrical_mj": "electrical energy"}
    graded_energy_keys = set()
    for energy_key, label in energy_labels.items():
        energy_quantity = entry.get(energy_key) or 0.0
        if not energy_quantity:
            continue
        # PER-CONSUMER GRADING (see print_why's own docstring and
        # TEMPERATURE in the module docstring): THIS recipe's own graded
        # price if it states a requirement, not necessarily the same as
        # the carrier's flat pool price shown for `--why thermal_mj`
        # itself.
        energy_price = _capability_graded_price(
            energy_key, entry, prices, capability_band_price_by_carrier)
        capped = CAPABILITY_CAP_FIELDS.get(energy_key)
        graded_note = ""
        if capped:
            _reached_field, needed_field, _default_floor = capped
            required_value = entry.get(needed_field)
            if required_value is not None:
                graded_energy_keys.add(energy_key)
                band = (capability_band_price_by_carrier.get(energy_key) or {})
                graded = band.get(required_value)
                graded_recipe_id = graded[1] if graded is not None else "NOTHING THIS ERA"
                pool_recipe_id = chosen_recipe_by_material.get(energy_key, "?")
                graded_note = ("  [graded: this recipe needs >= %s, met by "
                               "%s, vs the shared pool's own choice %s]"
                               % (required_value, graded_recipe_id, pool_recipe_id))
        cost = energy_quantity * energy_price if energy_price is not None else None
        share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                     if cost is not None and total_process_cost > 0 else "n/a")
        print("%s  %-24s x %10.4g MJ @ %10s h/MJ = %10s h  (%s)%s" % (
            pad, label, energy_quantity,
            format_hours(energy_price) if energy_price is not None else "NO PRICE",
            format_hours(cost) if cost is not None else "?", share_text, graded_note))
    return graded_energy_keys


def _print_energy_gap(pad, entry):
    residual_energy_mj = entry.get("energy_mj") or 0.0
    if residual_energy_mj:
        print("%s  ENERGY GAP: this recipe also needs %.4g MJ that neither "
              "the thermal nor the mechanical energy market prices (a "
              "technology this file cannot yet cost - see ENERGY in this "
              "file's module docstring). The price above is a LOWER BOUND "
              "by that much." % (pad, residual_energy_mj))


def _print_value_share_or_total(pad, other_outputs, this_output_value_share, output_prices,
                                 material, output_quantity, total_process_cost, price):
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


def _resolved_recipe_id_or_none(pad, material, resolvable_materials, ancestors,
                                 chosen_recipe_by_material):
    # The three ways print_why has nothing further to print for this
    # material - no path to a price, a cycle back to an ancestor already
    # shown, or (a bug) resolvable but never actually chosen - all end the
    # same way for the caller: print the reason, return None, stop.
    if material not in resolvable_materials:
        print("%s%s: NO PATH TO A PRICE (see the unpriceable-materials list)"
              % (pad, material))
        return None
    if material in ancestors:
        print("%s%s: (cycle back to an ancestor already shown above)" % (pad, material))
        return None
    recipe_id = chosen_recipe_by_material.get(material)
    if recipe_id is None:
        print("%s%s: resolvable but never chosen by any recipe - this should "
              "not happen and is worth reporting as a bug" % (pad, material))
        return None
    return recipe_id


def _next_recursion_targets(inputs, entry, graded_energy_keys, land_iugera_years, material):
    # A GRADED energy dependency (this recipe stated its own requirement)
    # was already shown above, by name and by price, next to the pool's
    # own choice for comparison - recursing into the generic carrier
    # material here would print the POOL's chosen technique instead,
    # which is not necessarily the one this recipe actually pays for (see
    # PER-CONSUMER GRADING) and would be misleading rather than merely
    # redundant, so it is skipped rather than recursed into.
    energy_dependencies = [energy_key for energy_key in ENERGY_CARRIER_FIELDS
                          if entry.get(energy_key) and energy_key not in graded_energy_keys]
    land_dependencies = ["iugerum_land"] if land_iugera_years and material != "iugerum_land" else []
    return sorted(inputs) + energy_dependencies + land_dependencies


def print_why(material, production_entries, producers_of, resolvable_materials,
              prices, wage_by_trade, chosen_recipe_by_material, indent=0, ancestors=(),
              rent_hours_per_kg_by_material=None, capability_band_price_by_carrier=None):
    """Recursive cost breakdown for one material: how much of its price is
    which input, which labour, which rent - recursing into every priced
    input in turn, with a cycle guard so a recipe graph that legitimately
    loops (iron needs charcoal needs an axe needs iron) prints once per
    branch and then says so, rather than recursing forever.

    `capability_band_price_by_carrier` is the same {carrier: {required_
    value: (price, recipe_id)}} shape `solve` builds each round (see
    PER-CONSUMER GRADING there and `_capability_graded_price`) - computed
    ONCE here, at the top-level call, from the final converged `prices`,
    and threaded through every recursive call rather than rebuilt at each
    level, so a recipe that states its own energy requirement (a heat
    engine's `temperature_needed_c`, say) is costed and displayed at ITS
    OWN graded price rather than the carrier's flat pool price - the same
    distinction `solve` itself now makes, shown here rather than hidden
    behind a single scalar `prices[carrier]`.
    """
    if capability_band_price_by_carrier is None:
        capability_band_price_by_carrier = _default_capability_band_price_by_carrier(
            production_entries, prices, wage_by_trade, rent_hours_per_kg_by_material)
    pad = "  " * indent
    recipe_id = _resolved_recipe_id_or_none(pad, material, resolvable_materials, ancestors,
                                            chosen_recipe_by_material)
    if recipe_id is None:
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

    rent_by_kg = rent_hours_per_kg_by_material or {}
    _print_extraction_rent_explanation(pad, material, entry, rent_by_kg)

    candidates = sorted(set(producers_of.get(material, [])) - {recipe_id})
    if candidates:
        _print_rejected_techniques(pad, material, recipe_id, production_entries, producers_of)

    _print_joint_output_note(pad, other_outputs, outputs)

    result = recipe_cost_and_allocation(
        recipe_id, entry, prices, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
        capability_band_price_by_carrier=capability_band_price_by_carrier)
    total_process_cost, output_prices = result
    output_quantity = outputs[material]
    this_output_value_share = (output_prices[material] * output_quantity) / total_process_cost \
        if total_process_cost > 0 else 0.0

    inputs = entry.get("inputs") or {}
    if inputs:
        _print_inputs(pad, inputs, output_quantity, prices, total_process_cost)

    _print_labour(pad, entry, wage_by_trade, total_process_cost)

    _print_rent_this_batch(pad, outputs, rent_by_kg, total_process_cost)

    land_iugera_years = _print_land(pad, entry, prices, total_process_cost)

    _print_capital(pad, entry, prices, wage_by_trade, outputs, total_process_cost)

    graded_energy_keys = _print_energy(pad, entry, prices, capability_band_price_by_carrier,
                                        chosen_recipe_by_material, total_process_cost)

    _print_energy_gap(pad, entry)

    _print_value_share_or_total(pad, other_outputs, this_output_value_share, output_prices,
                                 material, output_quantity, total_process_cost, price)

    next_ancestors = ancestors + (material,)
    for input_material in _next_recursion_targets(inputs, entry, graded_energy_keys,
                                                  land_iugera_years, material):
        print()
        print_why(input_material, production_entries, producers_of, resolvable_materials,
                  prices, wage_by_trade, chosen_recipe_by_material,
                  indent=indent + 1, ancestors=next_ancestors,
                  rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
                  capability_band_price_by_carrier=capability_band_price_by_carrier)


def _apply_era_gate(arguments, production_entries):
    """Restricts production_entries to the techniques `arguments.civ` can
    actually run, before anything else looks at them - see THE ERA GATE
    comment this replaces below. Returns (all_production_entries,
    production_entries, unreached_techniques, unclassified_techniques) on
    success, or None if arguments.civ names an unknown civilization (the
    message is already printed).
    """
    # THE ERA GATE. Applied before anything else looks at the entries, so
    # that resolvability, the fixed point, choice of technique, --why and
    # --compare all see the same, single set of techniques. Filtering later
    # - say, only inside `solve` - would leave the resolvability pass
    # reporting materials as priceable that this era has no way to make.
    unreached_techniques, unclassified_techniques = [], []
    all_production_entries = production_entries
    if arguments.civ:
        try:
            reached_nodes = load_starting_technologies(arguments.civ)
        except FileNotFoundError as problem:
            # A CLI typo deserves the list of real names, not a traceback.
            print(problem)
            return None
        entries_before_gate = len(production_entries)
        (production_entries, unreached_techniques,
         unclassified_techniques) = techniques_available_to(
            production_entries, reached_nodes)
        print("ERA GATE: %s holds %d technologies; %d of %d techniques are "
              "available to it (%d need a node it has not reached, %d carry "
              "no requires_node and are dropped unclassified)."
              % (arguments.civ, len(reached_nodes), len(production_entries),
                 entries_before_gate, len(unreached_techniques),
                 len(unclassified_techniques)))
        if unclassified_techniques:
            print("       An unclassified technique is an unanswered "
                  "question, not a universal one - see WHEN A TECHNIQUE "
                  "BECOMES AVAILABLE in data/production/_SCHEMA.md.")
        print()
    return (all_production_entries, production_entries, unreached_techniques,
            unclassified_techniques)


def _run_why_report(material, all_referenced_materials, production_entries, producers_of,
                     resolvable_materials, prices, wage_by_trade, chosen_recipe_by_material,
                     rent_hours_per_kg_by_material):
    if material not in all_referenced_materials:
        print("%r is not a material this tree consumes, nor one "
              "data/production/ produces or references. Typo?" % material)
        return 1
    print_why(material, production_entries, producers_of, resolvable_materials,
              prices, wage_by_trade, chosen_recipe_by_material,
              rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    return 0


def _run_compare_report(prices_json, resolvable_materials, prices, unanchored_byproducts):
    book_prices = {material: entry["p"] for material, entry in prices_json["purchase_prices_denarii"].items()
                   if not material.startswith("_")}
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


def _print_default_report_header(arguments):
    print("PRICE SOLVER - numeraire is one hour of unskilled (%r trade) "
          "labour. Rent on the ore of iron, copper, tin, lead, silver and "
          "mercury is now priced from sim/world/deposits.py's Ricardian "
          "marginal-deposit supply curve (see RENT ON EXTRACTED MATERIALS "
          "in the module docstring); rent on iugerum_land is now priced "
          "from sim/world/land.py's margin of cultivation over %s's own "
          "held regions (pass --civ to price another civilization's "
          "territory instead); every other extracted material (forest, "
          "quarry, salt pan, gold's placer-and-amalgamation step) still "
          "prices at zero rent. thermal_mj, mechanical_mj and electrical_mj "
          "are all priced via the three-way energy market and its "
          "conversion recipes in data/production/70_energy.json; energy_mj "
          "is still not priced (see module docstring)."
          % (NUMERAIRE_TRADE, arguments.civ or DEFAULT_LAND_CIVILIZATION))
    print()


def _print_rent_summary(arguments, rent_hours_per_kg_by_material):
    if rent_hours_per_kg_by_material:
        ore_rent = {material: rent_hours for material, rent_hours in rent_hours_per_kg_by_material.items()
                   if material in RENT_BEARING_ORE_MATERIALS}
        land_rent = {material: rent_hours for material, rent_hours in rent_hours_per_kg_by_material.items()
                    if material not in RENT_BEARING_ORE_MATERIALS}
        print("RENT NOW PRICED for %d of the %d ore materials named in "
              "RENT_BEARING_ORE_MATERIALS this era's gate leaves reachable "
              "(the rest fell out of the gate along with every recipe that "
              "would have consumed them):"
              % (len(ore_rent), len(RENT_BEARING_ORE_MATERIALS)))
        for ore_material in sorted(ore_rent):
            print("   %-26s %10s h/kg rent"
                  % (ore_material, format_hours(ore_rent[ore_material])))
        if land_rent:
            # "tile(s)", NOT "region(s)". cultivable_land_for_civilization
            # now resolves a civilisation's home_regions through
            # geography.json's land_tiles and returns one parcel per 150,000
            # km2 TILE, so this count has not meant regions since that
            # migration. It printed "rome_100ad (88 region(s) held)" for a
            # civilisation holding seven regions, which is the same
            # region-label-as-physical-unit confusion Complaints/46 and /50
            # were each about, surviving in a label after the mechanism
            # underneath it had been fixed.
            print("RENT NOW PRICED on land, for %s (%d tile(s) held):"
                  % (arguments.civ or DEFAULT_LAND_CIVILIZATION,
                     len(land.cultivable_land_for_civilization(
                         arguments.civ or DEFAULT_LAND_CIVILIZATION))))
            for land_material in sorted(land_rent):
                print("   %-26s %10s h/iugerum rent"
                      % (land_material, format_hours(land_rent[land_material])))
        elif "iugerum_land" not in rent_hours_per_kg_by_material:
            civilization_for_land = arguments.civ or DEFAULT_LAND_CIVILIZATION
            region_count = len(land.cultivable_land_for_civilization(civilization_for_land))
            print("iugerum_land priced at zero rent this run - %s holds "
                  "%d region(s), and none of its worse ones are needed to "
                  "feed its own stated population, so nothing better-than-"
                  "the-margin is actually being worked yet (see sim/world/"
                  "land.py's own module docstring - a single held region "
                  "always lands here too, since it has no worse region of "
                  "its own to earn a differential rent over)."
                  % (civilization_for_land, region_count))
        print()


def _print_convergence_summary(converged, iterations_run, residual, arguments,
                                resolvable_materials, all_referenced_materials, unpriceable):
    print("convergence: %s after %d iteration(s), final max relative change "
          "%.3e (tolerance %.0e, damping %.2f)"
          % ("CONVERGED" if converged else "DID NOT CONVERGE",
             iterations_run, residual, CONVERGENCE_TOLERANCE, arguments.damping))
    print("%d of %d referenced materials have a path to a price (%d resolved "
          "via data/production/, %d with NO path)"
          % (len(resolvable_materials), len(all_referenced_materials),
             len(resolvable_materials), len(unpriceable)))


def _print_unpriceable_materials(unpriceable, unreached_techniques, unclassified_techniques,
                                  all_production_entries, producers_of, tree_consumed):
    if unpriceable:
        print()
        print("MATERIALS WITH NO PATH TO A PRICE - a missing input entry, or "
              "a cycle with no extracted/labour-only material to bottom out "
              "at:")
        # UNDER A GATE, "no production entry at all" would be a lie: the
        # entry exists and this era simply cannot run it, which is a
        # completely different finding and wants a different response
        # (nothing, if the gate is right). Separate the two so a gated run
        # does not read as a hole in the data.
        # AND "GATED OUT" IS NOT "UNLABELLED", WHICH THIS CONFLATED. A
        # technique this era cannot reach is a correct answer and wants no
        # action. A technique nobody has classified yet is an unanswered
        # question that happens to LOOK the same from here, and calling it
        # "correctly gated out" told the reader the opposite of the truth -
        # copper_kg read as correctly unavailable to Rome when in fact its
        # file had not been labelled.
        unreached_materials, unclassified_materials = set(), set()
        for recipe_id in unreached_techniques:
            unreached_materials |= set(
                (all_production_entries[recipe_id].get("outputs") or {}))
        for recipe_id in unclassified_techniques:
            unclassified_materials |= set(
                (all_production_entries[recipe_id].get("outputs") or {}))
        # A material with both an unreached and an unlabelled recipe is an
        # open question, so the weaker claim wins.
        unreached_materials -= unclassified_materials
        for material in unpriceable:
            if material not in producers_of and material in unclassified_materials:
                reason = ("something makes it, but no recipe for it says when "
                          "it becomes available - UNLABELLED, not gated out")
            elif material not in producers_of and material in unreached_materials:
                reason = ("something makes it, but nothing this era can run "
                          "- correctly gated out, not a missing entry")
            elif material not in producers_of:
                reason = "no production entry at all"
            else:
                reason = "every producing recipe needs an input with no path of its own"
            print("   %-26s consumed by %4d tree node(s) - %s"
                  % (material, tree_consumed.get(material, 0), reason))


def _print_unproductive_cycles(unproductive_cycles):
    if unproductive_cycles:
        print()
        print("UNPRODUCTIVE CYCLES (Complaints/31) - a material with a path "
              "back to itself that consumes more of a good than the cycle "
              "yields, or that never bottoms out in labour or an extracted "
              "good, named rather than only reported through the materials "
              "it takes down with it:")
        for message in unproductive_cycles:
            print("   %s" % message)


def _print_energy_summaries(production_entries, resolvable_materials):
    # A set, not a list: a CONVERSION recipe's own output can be one of the
    # three carrier names themselves (mechanical_mj_motor outputs
    # mechanical_mj while consuming electrical_mj to do it), and several
    # conversion techniques compete for the same carrier, so without
    # deduping this would print "mechanical_mj" once per competing
    # technique rather than once.
    energy_priced = sorted(set(
        material for recipe_id, entry in production_entries.items()
        for material in (entry.get("outputs") or {})
        if any(entry.get(energy_key) for energy_key in ENERGY_CARRIER_FIELDS)
        and material in resolvable_materials))
    if energy_priced:
        print()
        print("%d material(s) draw on the energy market (thermal_mj, "
              "mechanical_mj and/or electrical_mj, priced via "
              "data/production/70_energy.json - see ENERGY in the module "
              "docstring) - their price above already includes it: %s"
              % (len(energy_priced), ", ".join(energy_priced)))

    energy_affected = sorted(
        material for recipe_id, entry in production_entries.items()
        for material in (entry.get("outputs") or {})
        if entry.get("energy_mj") and material in resolvable_materials)
    if energy_affected:
        print()
        print("%d material(s) are still UNDERPRICED because their recipe "
              "needs energy_mj that none of the three energy markets can "
              "supply - a technology this script cannot yet cost, not the general gap "
              "the other %d materials above just closed (a real lower "
              "bound, not a wrong answer - see ENERGY in the module "
              "docstring): %s"
              % (len(energy_affected), len(energy_priced), ", ".join(energy_affected)))


def _print_unanchored_byproducts_summary(unanchored_byproducts):
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


def _print_price_table(resolvable_materials, chosen_recipe_by_material, unanchored_byproducts, prices):
    print()
    print("%-30s %16s  %s" % ("material", "price (hours)", ""))
    for material in sorted(resolvable_materials):
        recipe_id = chosen_recipe_by_material.get(material, "?")
        technique_note = "" if recipe_id == material else ("  [%s]" % recipe_id)
        flag = " (*)" if material in unanchored_byproducts else ""
        print("%-30s %16s%s%s" % (
            material, format_hours(prices[material]), flag, technique_note))


def _run_default_report(arguments, rent_hours_per_kg_by_material, converged, iterations_run,
                         residual, resolvable_materials, all_referenced_materials, unpriceable,
                         unreached_techniques, unclassified_techniques, all_production_entries,
                         producers_of, tree_consumed, unproductive_cycles, production_entries,
                         unanchored_byproducts, chosen_recipe_by_material, prices):
    _print_default_report_header(arguments)
    _print_rent_summary(arguments, rent_hours_per_kg_by_material)
    _print_convergence_summary(converged, iterations_run, residual, arguments,
                                resolvable_materials, all_referenced_materials, unpriceable)
    _print_unpriceable_materials(unpriceable, unreached_techniques, unclassified_techniques,
                                  all_production_entries, producers_of, tree_consumed)
    _print_unproductive_cycles(unproductive_cycles)
    _print_energy_summaries(production_entries, resolvable_materials)
    _print_unanchored_byproducts_summary(unanchored_byproducts)
    _print_price_table(resolvable_materials, chosen_recipe_by_material, unanchored_byproducts, prices)
    return 0 if converged else 2


def main(argv=None):
    from sim import simulator
    # `description` is a literal copy of sim/solve_prices.py's own module
    # docstring's first line, not `__doc__.splitlines()[0]`: `main` lives
    # in this file while the mechanism essay lives in sim/solve_prices.py
    # (see this file's own module docstring), so keeping `--help`'s output
    # byte identical needs the string here to track that docstring's first
    # line by hand. If sim/solve_prices.py's own docstring's first line
    # ever changes, this string has to change with it.
    parser = argparse.ArgumentParser(
        description="Solve for the price of every material from physical structure, not a book.")
    parser.add_argument("--why", metavar="MATERIAL",
                        help="full recursive cost breakdown for one material")
    parser.add_argument("--compare", action="store_true",
                        help="computed price vs prices.json book price, as a "
                             "ratio, worst disagreement first")
    parser.add_argument("--damping", type=float, default=DAMPING_FACTOR,
                        help="fixed-point damping factor (default %.1f)" % DAMPING_FACTOR)
    parser.add_argument("--civ", metavar="CIVILIZATION",
                        help="solve using only the techniques this civilization "
                             "can actually run, from its starting_techs (e.g. "
                             "rome_100ad). Without this the solve is UNDATED and "
                             "will happily price Roman electricity off a "
                             "photovoltaic panel - see THE SOLVER NOW HAS A "
                             "NOTION OF WHEN, above, and Complaints/39")
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

    era_gate_result = _apply_era_gate(arguments, production_entries)
    if era_gate_result is None:
        return 1
    (all_production_entries, production_entries, unreached_techniques,
     unclassified_techniques) = era_gate_result

    wage_by_trade = wage_ratios_by_trade(prices_json)
    producers_of = build_producers_index(production_entries)

    # RENT ON EXTRACTED MATERIALS (see the module docstring). Computed once,
    # against this solve's own (possibly era-gated) production_entries and
    # wage table, before the iteration starts - see
    # rent_hours_per_kg_by_ore_material's own docstring for why it does not
    # need to be recomputed every round.
    rent_hours_per_kg_by_material = rent_hours_per_kg_by_ore_material(
        production_entries, wage_by_trade)

    # RENT ON ARABLE LAND (see sim/world/land.py's own module docstring).
    # A separate mechanism from ore's - the margin of cultivation over a
    # civilization's own held regions, not a deposit's grade - but wired in
    # the SAME dict, because recipe_cost_and_allocation does not care which
    # mechanism produced a material's rent, only that one exists. Uses
    # `arguments.civ` when given (land, unlike ore, is genuinely per-
    # civilization) and Rome's own territory otherwise - see
    # land_rent_hours_per_iugerum's own docstring for why.
    rent_hours_per_kg_by_material.update(
        land_rent_hours_per_iugerum(production_entries, wage_by_trade,
                                    civilization_id=arguments.civ))

    unproductive_cycles = []
    resolvable_materials = compute_resolvable_materials(
        production_entries, producers_of, diagnostics=unproductive_cycles,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    tree_consumed = materials_the_tree_consumes(nodes)
    all_referenced_materials = set(tree_consumed) | set(producers_of)
    for entry in production_entries.values():
        all_referenced_materials |= set((entry.get("inputs") or {}).keys())
    unpriceable = sorted(all_referenced_materials - resolvable_materials)

    prices, iterations_run, residual, chosen_recipe_by_material = solve(
        production_entries, producers_of, resolvable_materials, wage_by_trade,
        damping=arguments.damping,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    converged = residual < CONVERGENCE_TOLERANCE
    unanchored_byproducts = minor_joint_byproducts_are_unanchored(
        production_entries, chosen_recipe_by_material, prices, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    if arguments.why:
        return _run_why_report(arguments.why, all_referenced_materials, production_entries,
                                producers_of, resolvable_materials, prices, wage_by_trade,
                                chosen_recipe_by_material, rent_hours_per_kg_by_material)

    if arguments.compare:
        return _run_compare_report(prices_json, resolvable_materials, prices, unanchored_byproducts)

    # Default: every material's price, in labour-hours.
    return _run_default_report(arguments, rent_hours_per_kg_by_material, converged, iterations_run,
                                residual, resolvable_materials, all_referenced_materials, unpriceable,
                                unreached_techniques, unclassified_techniques, all_production_entries,
                                producers_of, tree_consumed, unproductive_cycles, production_entries,
                                unanchored_byproducts, chosen_recipe_by_material, prices)
