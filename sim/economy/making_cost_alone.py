"""What a good costs to make, as the market memory reads it in a year its market traded nothing (rule_sets.py).

A recipe with several outputs has one cost for all of them; `unit_cost.full_cost_per_unit` splits it by what each output
sells for. Read back as the price of an output nobody traded, that split is the output's own remembered price times the
recipe's cost over its revenue, so the price shrinks by that share every such year and ends at nothing. A joint product
has no cost of its own: under the clearing rules the memory reads a making cost only for a good some recipe makes
alone, and a market of a good with none keeps the price it had."""
from typing import Dict, Mapping

from .notional import making_costs


def goods_made_alone(recipes: Mapping[str, object]) -> frozenset:
    """The goods some recipe makes as its only output."""
    return frozenset(next(iter(recipe.outputs)) for recipe in recipes.values() if len(recipe.outputs) == 1)


def costs_of_goods_made_alone(costs: Mapping[str, float], recipes: Mapping[str, object]) -> Dict[str, float]:
    """`costs` (good -> making cost) without the goods that are only ever made beside another output."""
    alone = goods_made_alone(recipes)
    return {good: cost for good, cost in costs.items() if good in alone}


def of_every_good(setup, record) -> Dict[str, float]:
    """The making cost of every good that has one, joint products at their share by value (`notional.making_costs`)."""
    return making_costs(setup, record)


def of_goods_made_alone(setup, record) -> Dict[str, float]:
    """The making cost of the goods some recipe makes alone; a good made only as a joint product has none."""
    return costs_of_goods_made_alone(making_costs(setup, record), setup.recipes)


def no_cost(_old_price):
    """A market of a good with no making cost has none to plan from: with nothing traded and nothing quoted its price is forgotten."""
    return None


def the_price_it_had(old_price):
    """A market of a good with no making cost plans from the price it had: a year with nothing traded and nothing quoted
    taught it nothing (None where it had none)."""
    return old_price
