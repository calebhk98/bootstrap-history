"""`opening_runs.required_runs` over arrays, packed once for the recipes, rankings and ceilings of one settlement.

The settlement asks for the runs a final demand takes many times with the same recipes; `RunSolver` packs them (goods and
recipes as positions in sorted order, the chosen makers of each good as a compressed list) and asks the kernel
(`opening_runs_kernel.required_runs`) for the runs of a demand given as a vector over its goods."""
import math
from typing import Dict, List, Mapping, Optional

import numpy as np

from . import opening_runs, opening_runs_kernel as kernel, unit_cost


class RunSolver:
    def __init__(self, recipes: Mapping[str, object], ranked: Mapping[str, List[str]], ceilings: Mapping[str, float],
                 yields: Mapping[str, float], main: Optional[Mapping[str, str]], wages: Mapping[str, float]) -> None:
        recipe_ids = sorted({recipe_id for choices in ranked.values() for recipe_id in choices})
        recipe_position = {recipe_id: position for position, recipe_id in enumerate(recipe_ids)}
        users = opening_runs.by_product_users(recipes, main) if main is not None else {}
        goods = set(ranked)
        for recipe_id in recipe_ids:
            recipe = recipes[recipe_id]
            goods.update(recipe.inputs, recipe.plant_goods, recipe.tool_wear, recipe.outputs)
            for steps in recipe.tool_fallbacks.values():
                goods.update(step.good for step in steps if step.good)
        goods.update(users)
        self.goods = sorted(goods)
        self.good_position = {good: position for position, good in enumerate(self.goods)}
        self.recipe_ids = recipe_ids
        self.static_ceil = np.array([ceilings.get(recipe_id, math.inf) for recipe_id in recipe_ids])
        self.has_static = np.array([recipe_id in ceilings for recipe_id in recipe_ids], dtype=np.bool_)
        rank_ptr, rank_recipe, rank_made, rank_output, rank_main = [0], [], [], [], []
        for good in self.goods:
            for recipe_id in ranked.get(good, ()):
                output = recipes[recipe_id].outputs.get(good, 0.0)
                rank_recipe.append(recipe_position[recipe_id])
                rank_output.append(output)
                rank_made.append(output * yields.get(recipe_id, 1.0))
                rank_main.append(main is not None and main.get(recipe_id) == good)
            rank_ptr.append(len(rank_recipe))
        input_ptr, input_good, input_per_run, input_life = [0], [], [], []
        tool_ptr, tool_good, tool_per_run, tool_fallback, tool_fallback_units = [0], [], [], [], []
        for recipe_id in recipe_ids:
            recipe = recipes[recipe_id]
            for good, quantity in recipe.inputs.items():
                input_good.append(self.good_position[good])
                input_per_run.append(quantity)
                input_life.append(0.0)
            if recipe.plant_life_years > 0.0:
                for good, quantity in recipe.plant_goods.items():
                    input_good.append(self.good_position[good])
                    input_per_run.append(quantity)
                    input_life.append(recipe.plant_life_years)
            input_ptr.append(len(input_good))
            for good, per_run in recipe.tool_wear.items():
                step = next((step for step in recipe.tool_fallbacks.get(good, ()) if step.good), None)
                tool_good.append(self.good_position[good])
                tool_per_run.append(per_run)
                tool_fallback.append(-1 if step is None else self.good_position[step.good])
                tool_fallback_units.append(0.0 if step is None else step.units_per_run)
            tool_ptr.append(len(tool_good))
        bp_ptr, bp_maker_ptr, bp_maker, bp_maker_output, bp_maker_yield, bp_user_ptr, bp_user, bp_user_needed = [0], [0], [], [], [], [0], [], []
        for good, (makers, users_of) in users.items():
            for maker in makers:
                if maker in recipe_position:
                    bp_maker.append(recipe_position[maker])
                    bp_maker_output.append(recipes[maker].outputs[good])
                    bp_maker_yield.append(yields.get(maker, 1.0))
            for user, needed in users_of:
                if user in recipe_position:
                    bp_user.append(recipe_position[user])
                    bp_user_needed.append(needed)
            bp_ptr.append(len(bp_ptr))
            bp_maker_ptr.append(len(bp_maker))
            bp_user_ptr.append(len(bp_user))
        self.arguments = (
            self.static_ceil, self.has_static, np.array(rank_ptr, dtype=np.int64), np.array(rank_recipe, dtype=np.int64),
            np.array(rank_made), np.array(rank_output), np.array(rank_main, dtype=np.bool_),
            np.array(input_ptr, dtype=np.int64), np.array(input_good, dtype=np.int64), np.array(input_per_run), np.array(input_life),
            np.array(tool_ptr, dtype=np.int64), np.array(tool_good, dtype=np.int64), np.array(tool_per_run),
            np.array(tool_fallback, dtype=np.int64), np.array(tool_fallback_units),
            np.array(bp_ptr, dtype=np.int64), np.array(bp_maker_ptr, dtype=np.int64), np.array(bp_maker, dtype=np.int64),
            np.array(bp_maker_output), np.array(bp_maker_yield), np.array(bp_user_ptr, dtype=np.int64), np.array(bp_user, dtype=np.int64),
            np.array(bp_user_needed))
        self.hours_per_run = np.array([math.fsum(recipes[recipe_id].labour_hours.values()) for recipe_id in recipe_ids])
        self.labour_cost_per_run = np.array([unit_cost.labour_cost_per_run(recipes[recipe_id], wages) for recipe_id in recipe_ids])

    def mapping(self, goods: List[str]):
        """(positions in `goods`, the solver's position of each): the goods of a demand that some recipe touches."""
        pairs = [(position, self.good_position[good]) for position, good in enumerate(goods) if good in self.good_position]
        return np.array([pair[0] for pair in pairs], dtype=np.int64), np.array([pair[1] for pair in pairs], dtype=np.int64)

    def national_vector(self, mapping, totals: np.ndarray) -> np.ndarray:
        """A demand given as totals over some goods as a vector over the solver's goods (`mapping` from `mapping`)."""
        vector = np.zeros(len(self.goods))
        vector[mapping[1]] = totals[mapping[0]]
        return vector

    def runs(self, national: np.ndarray) -> np.ndarray:
        """Runs a year of each recipe (`recipe_ids`) that meet the demand `national`."""
        runs = np.zeros(len(self.recipe_ids))
        kernel.required_runs(national, *self.arguments, runs, np.zeros(kernel.PARTIALS))
        return runs

    def runs_by_recipe(self, runs: np.ndarray) -> Dict[str, float]:
        return {recipe_id: float(count) for recipe_id, count in zip(self.recipe_ids, runs)}
