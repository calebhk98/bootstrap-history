"""Splits one joint process's cost across its outputs by their value at reference prices.

A joint recipe (one smelt, several products) has one cost and several prices, so cost alone cannot separate
them. Each output takes a share of the batch proportional to its reference price times its quantity. The
caller supplies reference prices (what each output is worth, or costs to make another way); an output with
none is valued by its mass, unless it is a waste (tipped when nobody takes it), which is worth nothing until
someone bids. The split reads no demand.
"""
import warnings

from sim.constants import declare
from sim.world import demand

UNPRICED_OUTPUT_VALUE_PER_KILOGRAM_SHARE = declare(
    "UNPRICED_OUTPUT_VALUE_PER_KILOGRAM_SHARE", 1.0, kind="temporary_heuristic",
    unit="value of a kilogram of an output with no reference price, over the batch's mean cost per kilogram",
    source=None, confidence="D", retire="Complaints/507 stage 2: reference prices from the economy",
    why="Where no reference price is given a kilogram of any such output is worth the same as a kilogram of "
        "any other, so the batch splits by mass. Physical, and unit-consistent (a gram is not priced like a "
        "kilogram), but it ignores what the output is worth, which only a price can say.")


UNPRICED_WASTE_VALUE = declare(
    "UNPRICED_WASTE_VALUE", 0.0, kind="temporary_heuristic",
    unit="value of a waste with no reference price, per unit",
    source=None, confidence="D", retire="Complaints/507 stage 3 and 7: the economy's bid for waste",
    why="A material the data records a waste heap for is tipped when nobody takes it. With no reference price "
        "to say someone does, it carries no share of the batch that made it, as it did while a demand search "
        "judged it in glut; the other outputs carry the batch. A co-product that is a waste is the economy's "
        "to price (a seller offers it below zero), not a cost to spread over the product it comes with.")


def allocate_joint_cost(outputs, total_cost, reference_price_by_material=None, disposal_cost_by_material=None,
                        waste_materials=frozenset()):
    """{material: price per unit} splitting `total_cost` over `outputs`.

    The outputs together recover the batch exactly. An output is valued at its reference price when the
    caller gives one, otherwise by its mass in kilograms; an output with neither is warned about, left out
    of the split and priced at zero. An output in `waste_materials` with no reference is valued at
    UNPRICED_WASTE_VALUE. An output the caller values below zero is a waste nobody will take: it
    is priced at that value but no lower than minus its disposal cost (`disposal_cost_by_material`, per
    unit), and the others carry the batch and what it costs to be rid of the waste.
    """
    if len(outputs) == 1:
        (name, quantity), = outputs.items()
        return {name: total_cost / quantity}
    references = dict(reference_price_by_material or {})
    for name in outputs:
        if name in waste_materials and name not in references:
            references[name] = UNPRICED_WASTE_VALUE
    disposal_costs = disposal_cost_by_material or {}
    wastes = {name: max(references[name], -disposal_costs.get(name, 0.0))
              for name in outputs if references.get(name, 0.0) < 0.0}
    if wastes and len(wastes) < len(outputs):
        carried = total_cost - sum(price * outputs[name] for name, price in wastes.items())
        prices = dict(wastes)
        prices.update(allocate_joint_cost(
            {name: quantity for name, quantity in outputs.items() if name not in wastes}, carried,
            {name: price for name, price in references.items() if name not in wastes}))
        return prices
    mass = {name: demand.mass_in_kg_or_none(name, quantity) for name, quantity in outputs.items()}
    unvalued = sorted(name for name in outputs if name not in references and mass[name] is None)
    if unvalued:
        warnings.warn("joint outputs with no reference price and no mass unit are left out of the cost split: %s"
                      % ", ".join(unvalued))
    split_outputs = {name: quantity for name, quantity in outputs.items() if name not in unvalued}
    prices = dict.fromkeys(unvalued, 0.0)
    if not split_outputs:
        return prices
    # TEMPORARY HEURISTIC (UNPRICED_OUTPUT_VALUE_PER_KILOGRAM_SHARE): an output with no reference price is
    # valued by mass at the batch's mean cost per kilogram, which depends on no solved output price.
    standalone_cost_per_kg = total_cost / (sum(mass[name] for name in split_outputs if mass[name] is not None)
                                           or 1.0)
    reference_prices = {
        name: references[name] if name in references
        else (UNPRICED_OUTPUT_VALUE_PER_KILOGRAM_SHARE * standalone_cost_per_kg * mass[name] / split_outputs[name])
        for name in split_outputs}
    prices.update(_split_by_value(split_outputs, reference_prices, total_cost))
    return prices


def outputs_split_by_mass(outputs, reference_price_by_material, waste_materials=frozenset()):
    """The outputs of a joint batch that were valued by mass, because no reference price was given."""
    references = reference_price_by_material or {}
    return sorted(name for name in outputs
                  if len(outputs) > 1 and name not in references and name not in waste_materials
                  and demand.mass_in_kg_or_none(name, 1.0) is not None)


def _split_by_value(outputs, reference_prices, total_cost):
    values = {name: quantity * max(reference_prices.get(name, 1.0), 0.0)
              for name, quantity in outputs.items()}
    total_value = sum(values.values())
    if total_value <= 0:
        # Nothing has a value yet; split by quantity until prices exist.
        values = dict(outputs)
        total_value = sum(values.values())
    return {name: total_cost * values[name] / total_value / quantity
            for name, quantity in outputs.items()}
