"""Splits one joint process's cost across its outputs using demand.

A joint recipe (one smelt, several products) has one cost and several
prices, so cost alone cannot separate them. Outputs with a demand anchor
(a market-clearing price from `sim/world/demand.py`) take a share of the
cost proportional to anchor price times quantity. Outputs without one are
valued at the batch's standalone unit cost, which does not depend on any
solved output price, so the split cannot feed back into itself.
"""
import json
import os
import warnings

from sim.constants import declare
from sim.world import demand, deposits

DEFAULT_CIVILIZATION = "rome_100ad"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR = declare(
    "MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR", 550.0,
    kind="temporary_heuristic",
    unit="labour-hours/person/year",
    source=None,
    confidence="D",
    why="Household income scale for the demand anchors: hours worked per "
        "worker-year times a working share of the whole population. Should "
        "come from the labour market once it is wired; until then it is one "
        "number for every civilisation.")


def allocate_joint_cost(outputs, current_prices, total_cost,
                        anchor_price_by_material=None):
    """{material: price per unit} splitting `total_cost` over `outputs`.

    Outputs only have to recover the batch together; a bulk waste may carry
    far less than its mass share. Without an anchor an output is valued by
    its mass in kg. An output whose unit is not a mass is warned about,
    left out of the split and priced at zero.
    """
    if len(outputs) == 1:
        (name, quantity), = outputs.items()
        return {name: total_cost / quantity}
    anchors = anchor_price_by_material or {}
    mass = {name: demand.mass_in_kg_or_none(name, quantity)
            for name, quantity in outputs.items()}
    unconvertible = sorted(name for name, kilograms in mass.items() if kilograms is None)
    if unconvertible:
        warnings.warn("joint outputs with no mass unit are left out of the cost split: %s"
                      % ", ".join(unconvertible))
    split_outputs = {name: quantity for name, quantity in outputs.items()
                     if mass[name] is not None}
    prices = dict.fromkeys(unconvertible, 0.0)
    if not split_outputs:
        return prices
    anchored = {name for name in split_outputs if name in anchors}
    kilograms_per_unit = {name: mass[name] / quantity for name, quantity in split_outputs.items()}
    # TEMPORARY HEURISTIC: an unanchored output is valued at the batch's
    # standalone cost per kg, which does not depend on any solved output price.
    standalone_cost_per_kg = total_cost / (sum(mass[name] for name in split_outputs) or 1.0)
    reference_prices = {
        name: anchors[name] if name in anchored
        else standalone_cost_per_kg * kilograms_per_unit[name]
        for name in split_outputs}
    prices.update(_split_by_value(split_outputs, reference_prices, total_cost))
    return prices


def cap_anchors(anchor_price_by_material, direct_price_by_material):
    """Anchors, each held at or below the cheapest sole-output route's price.

    A joint recipe cannot value a byproduct above what making it directly
    costs. Sole-output routes never depend on an anchor, so the cap cannot
    feed back into the price it is capped by.
    """
    if anchor_price_by_material is None:
        return None
    return {name: min(price, direct_price_by_material.get(name, price))
            for name, price in anchor_price_by_material.items()}


def _split_by_value(outputs, reference_prices, total_cost):
    values = {name: quantity * reference_prices.get(name, 1.0)
              for name, quantity in outputs.items()}
    total_value = sum(values.values())
    if total_value <= 0:
        # Nothing has a value yet; split by quantity until prices exist.
        values = dict(outputs)
        total_value = sum(values.values())
    return {name: total_cost * values[name] / total_value / quantity
            for name, quantity in outputs.items()}


class DemandAnchors:
    """Market-clearing prices for goods with a household demand curve."""

    def __init__(self, bins, basket, supply_kg_by_material):
        self.bins = bins
        self.basket = basket
        self.supply_kg_by_material = supply_kg_by_material

    def prices(self, current_prices):
        """{material: clearing price} at this round's solved prices."""
        known = {}
        for good in self.basket:
            if good.name in current_prices:
                known[good.name] = current_prices[good.name]
            elif good.subsistence_quantity_per_capita_per_year > 0:
                return {}
            else:
                # No floor, so this price cannot move another good's clearing price.
                known[good.name] = 1.0
        anchors = {}
        for good in self.basket:
            supply = self.supply_kg_by_material.get(good.name)
            if not supply:
                continue
            others = {name: price for name, price in known.items() if name != good.name}
            try:
                anchors[good.name] = demand.market_clearing_price(
                    good, supply, others, self.bins, self.basket)
            except ValueError:
                continue
        return anchors


def _annual_supply_kg(material, resources):
    output = resources.get(material.rsplit("_", 1)[0])
    if not output:
        return None
    return output["t_per_yr"] * 1000.0


def build_demand_anchors(civilization_id=None, basket=None,
                         supply_kg_by_material=None):
    """DemandAnchors for a civilisation, or None when nothing is anchorable.

    Only basket goods with a known annual supply and no subsistence floor
    are anchored; staples are priced by their own recipes.
    """
    basket = basket or demand.DEFAULT_BASKET
    if supply_kg_by_material is None:
        with open(deposits.RESOURCES_FILE) as handle:
            resources = json.load(handle)["empire_output_100ad"]
        supply_kg_by_material = {}
        for good in basket:
            supply = _annual_supply_kg(good.name, resources)
            if supply:
                supply_kg_by_material[good.name] = supply
    supply_kg_by_material = {
        good.name: supply_kg_by_material[good.name] for good in basket
        if good.name in supply_kg_by_material
        and good.subsistence_quantity_per_capita_per_year == 0}
    if not supply_kg_by_material:
        return None
    path = os.path.join(_ROOT, "data", "civilizations", "%s.json" % civilization_id)
    if not civilization_id or not os.path.exists(path):
        path = os.path.join(
            _ROOT, "data", "civilizations", "%s.json" % DEFAULT_CIVILIZATION)
    with open(path) as handle:
        population = json.load(handle)["population"]
    bins = demand.income_bins(
        float(population), MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR)
    return DemandAnchors(bins, basket, supply_kg_by_material)
