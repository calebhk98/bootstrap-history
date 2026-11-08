"""The recipes a producers' turn works from, flattened to arrays once per recipe set: what `goods_turn_kernel.produce_turn` and
`goods_turn_kernel.offer_pairs` read in place of `Recipe` objects.

Everything is indexed by the year arrays' numbering (`RecipeMatrices`): recipe rows, good rows, trade columns. A good's row follows
the sorted names, so walking rows in order walks goods in the order `sorted(...)` gives names.

Per recipe row, in compressed form (`*_ptr[row]:*_ptr[row + 1]` are the row's entries):
    hard        the inputs a run cannot go ahead without (`Recipe.hard_inputs_sorted`): good row, units per run
    wear        the tool wear (`Recipe.tool_wear_sorted`): good row, units per run, and per entry its fallback steps in order
    steps       a fallback step: good row (`NO_GOOD` for working by hand), units per run, hours factor, and its trades as slots of
                the recipe's labour list
    draw goods  every good a draw can use (wear goods and fallback goods), sorted: good row, and whether the recipe lists it as an
                input (a draw reads the stock held only of those)
    labour      the recipe's trades in the order of `Recipe.labour_hours`: trade column, booked hours per run
    outputs     the outputs sorted: good row, units per run, units of the same good the recipe's own inputs use per run
`spoilage` is per good from the goods' specs. `build` answers None when a name is outside the matrices (the old per-producer path then runs)."""
from dataclasses import dataclass
from typing import Mapping, Optional

import numpy

NO_GOOD = -1


@dataclass(frozen=True)
class TurnSpec:
    hard_ptr: numpy.ndarray
    hard_good: numpy.ndarray
    hard_per_run: numpy.ndarray
    wear_ptr: numpy.ndarray
    wear_draw: numpy.ndarray          # the wear good's place among the recipe's draw goods
    wear_per_run: numpy.ndarray
    step_ptr: numpy.ndarray           # per wear entry (not per recipe): its steps
    step_draw: numpy.ndarray          # the step good's place among the recipe's draw goods, or NO_GOOD
    step_units: numpy.ndarray
    step_factor: numpy.ndarray
    step_trade_ptr: numpy.ndarray
    step_trade_slot: numpy.ndarray    # a slot of the recipe's labour list
    draw_ptr: numpy.ndarray
    draw_good: numpy.ndarray
    draw_listed: numpy.ndarray        # 1 where the recipe lists the good among its inputs
    labour_ptr: numpy.ndarray
    labour_trade: numpy.ndarray
    labour_hours: numpy.ndarray
    output_ptr: numpy.ndarray
    output_good: numpy.ndarray
    output_per_run: numpy.ndarray
    output_kept: numpy.ndarray        # per output: units a run of the recipe uses of the same good
    lines_most: numpy.ndarray         # per recipe: the most moves one producer's run can post
    has_output: numpy.ndarray         # recipe by good: whether the good is an output
    spoilage: numpy.ndarray           # per good: the share of it lost in a year (zero for a good with no spec)


def _pointer(counts) -> numpy.ndarray:
    pointer = numpy.zeros(len(counts) + 1, dtype=numpy.int64)
    pointer[1:] = numpy.cumsum(counts)
    return pointer


def build(recipes: Mapping[str, object], specs: Mapping[str, object], matrices) -> Optional[TurnSpec]:
    """The spec of the recipes, in the order of `matrices.recipes`; None when a recipe names a good or trade the matrices lack."""
    goods, trades = matrices.goods.row, matrices.trades.row
    columns = {name: [] for name in ("hard_good", "hard_per_run", "wear_draw", "wear_per_run", "step_draw", "step_units", "step_factor",
                                     "step_trade_slot", "draw_good", "draw_listed", "labour_trade", "labour_hours", "output_good",
                                     "output_per_run", "output_kept")}
    counts = {name: [] for name in ("hard", "wear", "draw", "labour", "output")}
    step_counts, step_trade_counts = [], []
    most = []
    has_output = numpy.zeros((len(matrices.recipes.ids), len(matrices.goods.ids)), dtype=bool)
    try:
        for recipe_row, recipe_id in enumerate(matrices.recipes.ids):
            recipe = recipes[recipe_id]
            hard = recipe.hard_inputs_sorted
            wear = recipe.tool_wear_sorted
            drawn = set(good for good, _per_run in wear) | {step.good for steps in recipe.tool_fallbacks.values() for step in steps
                                                           if step.good}
            draw_goods = sorted(drawn)
            where = {good: place for place, good in enumerate(draw_goods)}
            slots = {trade: slot for slot, trade in enumerate(recipe.labour_hours)}
            for good, per_run in hard:
                columns["hard_good"].append(goods[good])
                columns["hard_per_run"].append(per_run)
            for good, per_run in wear:
                columns["wear_draw"].append(where[good])
                columns["wear_per_run"].append(per_run)
                steps = recipe.tool_fallbacks.get(good, ())
                step_counts.append(len(steps))
                for step in steps:
                    columns["step_draw"].append(where[step.good] if step.good else NO_GOOD)
                    columns["step_units"].append(step.units_per_run)
                    columns["step_factor"].append(step.hours_factor)
                    step_trade_counts.append(len(step.trades))
                    columns["step_trade_slot"].extend(slots[trade] for trade in step.trades)
            for good in draw_goods:
                columns["draw_good"].append(goods[good])
                columns["draw_listed"].append(1 if good in recipe.inputs else 0)
            for trade, hours in recipe.labour_hours.items():
                columns["labour_trade"].append(trades[trade])
                columns["labour_hours"].append(hours)
            for good, per_run in recipe.outputs_sorted:
                columns["output_good"].append(goods[good])
                columns["output_per_run"].append(per_run)
                columns["output_kept"].append(recipe.inputs.get(good, 0.0))
                has_output[recipe_row, goods[good]] = True
            for good in recipe.outputs:
                has_output[recipe_row, goods[good]] = True
            counts["hard"].append(len(hard))
            counts["wear"].append(len(wear))
            counts["draw"].append(len(draw_goods))
            counts["labour"].append(len(recipe.labour_hours))
            counts["output"].append(len(recipe.outputs_sorted))
            most.append(len(hard) + len(draw_goods) + len(recipe.outputs_sorted))
    except KeyError:
        return None
    floats = ("hard_per_run", "wear_per_run", "step_units", "step_factor", "labour_hours", "output_per_run", "output_kept")
    made = {name: numpy.array(values, dtype=float if name in floats else numpy.int64) for name, values in columns.items()}
    return TurnSpec(
        _pointer(counts["hard"]), made["hard_good"], made["hard_per_run"], _pointer(counts["wear"]), made["wear_draw"],
        made["wear_per_run"], _pointer(step_counts), made["step_draw"], made["step_units"], made["step_factor"],
        _pointer(step_trade_counts), made["step_trade_slot"], _pointer(counts["draw"]), made["draw_good"], made["draw_listed"],
        _pointer(counts["labour"]), made["labour_trade"], made["labour_hours"], _pointer(counts["output"]), made["output_good"],
        made["output_per_run"], made["output_kept"], numpy.array(most, dtype=numpy.int64), has_output,
        numpy.array([specs[good].spoilage_per_year if good in specs else 0.0 for good in matrices.goods.ids], dtype=float))


_KEPT: dict = {}


def of(setup, matrices) -> Optional[TurnSpec]:
    """`build` of the setup's recipes, kept while the same matrices and recipe records serve."""
    key = id(matrices)
    kept = _KEPT.get(key)
    if kept is not None and kept[0] is matrices and kept[1] is setup.recipes and kept[3] is setup.specs:
        return kept[2]
    spec = build(setup.recipes, setup.specs, matrices)
    if len(_KEPT) > 8:
        _KEPT.clear()
    _KEPT[key] = (matrices, setup.recipes, spec, setup.specs)
    return spec
