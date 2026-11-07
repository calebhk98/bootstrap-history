"""Runs a year of each recipe that meet a final demand, over recipe matrices (the kernel of `opening_runs_pack.py`).

`opening_runs.required_runs` and `tool_fallback.shift_unmet_tools` written once over arrays: a recipe's inputs, plant wear
and tool wear are compressed rows, a good's ranked makers a compressed list. Goods and recipes are positions in sorted
order. The old code held the recipes it had given runs to in a dict, in the order it first gave them any, and summed what
they use in that order; the sums here run in that order too (`runs_order`), and the sums it made with `math.fsum` are exact
(`_add`, `_total`), so that a demand at the edge of a ceiling is on the same side of it."""
import numpy as np

from sim.jit import njit
from sim.economy.opening_demand_kernel import PARTIALS, _add, _total

INPUT_OUTPUT_PASSES = 60
__all__ = ["required_runs", "PARTIALS"]


@njit
def _shift_unmet_tools(required, runs, runs_order, runs_count, ceil, has_ceil, rank_ptr, rank_recipe, rank_output, tool_ptr,
                       tool_good, tool_per_run, tool_fallback, tool_fallback_units, wearing, partials):
    """tool_fallback.shift_unmet_tools: where every maker of a tool is held to a ceiling and the runs wear more than they
    make, the same share of every user's wear is met by its next tool."""
    wearing[:] = 0.0
    for slot in range(runs_count):
        recipe = runs_order[slot]
        for entry in range(tool_ptr[recipe], tool_ptr[recipe + 1]):
            wearing[tool_good[entry]] += runs[recipe] * tool_per_run[entry]
    for good in range(wearing.shape[0]):
        wear = wearing[good]
        if wear <= 0.0:
            continue
        first = rank_ptr[good]
        last = rank_ptr[good + 1]
        if last == first:
            continue
        held = True
        for slot in range(first, last):
            if not has_ceil[rank_recipe[slot]]:
                held = False
        if not held:
            continue
        count = 0
        for slot in range(first, last):
            count = _add(partials, count, ceil[rank_recipe[slot]] * rank_output[slot])
        capacity = _total(partials, count)
        unmet = min(wear, required[good] - capacity)
        if unmet <= 0.0:
            continue
        share = unmet / wear
        for recipe in range(runs.shape[0]):
            if runs[recipe] == 0.0:
                continue
            for entry in range(tool_ptr[recipe], tool_ptr[recipe + 1]):
                if tool_good[entry] == good and tool_per_run[entry] > 0.0 and tool_fallback[entry] >= 0:
                    required[good] -= share * runs[recipe] * tool_per_run[entry]
                    required[tool_fallback[entry]] += share * runs[recipe] * tool_fallback_units[entry]


@njit
def required_runs(national, static_ceil, has_static, rank_ptr, rank_recipe, rank_made, rank_output, rank_main,
                  input_ptr, input_good, input_per_run, input_life, tool_ptr, tool_good, tool_per_run, tool_fallback,
                  tool_fallback_units, bp_ptr, bp_maker_ptr, bp_maker, bp_maker_output, bp_maker_yield, bp_user_ptr, bp_user,
                  bp_user_needed, runs_out, partials):
    """opening_runs.required_runs: fills `runs_out` (runs of each recipe) and returns the passes used. `national` is the final
    demand by good."""
    recipe_count = static_ceil.shape[0]
    good_count = national.shape[0]
    runs = np.zeros(recipe_count)
    runs_order = np.zeros(recipe_count, dtype=np.int64)
    runs_count = 0
    new_order = np.zeros(recipe_count, dtype=np.int64)
    driven = np.zeros(recipe_count)
    updated = np.zeros(recipe_count)
    touched = np.zeros(recipe_count, dtype=np.bool_)
    ceil = np.zeros(recipe_count)
    has_ceil = np.zeros(recipe_count, dtype=np.bool_)
    required = np.zeros(good_count)
    wearing = np.zeros(good_count)
    for passes in range(INPUT_OUTPUT_PASSES):
        for recipe in range(recipe_count):
            ceil[recipe] = static_ceil[recipe]
            has_ceil[recipe] = has_static[recipe]
        for group in range(bp_ptr.shape[0] - 1):
            count = 0
            for slot in range(bp_maker_ptr[group], bp_maker_ptr[group + 1]):
                count = _add(partials, count, driven[bp_maker[slot]] * bp_maker_output[slot] * bp_maker_yield[slot])
            supply = _total(partials, count)
            for slot in range(bp_user_ptr[group], bp_user_ptr[group + 1]):
                user = bp_user[slot]
                limit = supply / bp_user_needed[slot]
                if not has_ceil[user] or limit < ceil[user]:
                    ceil[user] = limit
                has_ceil[user] = True
        for good in range(good_count):
            required[good] = national[good]
        for slot in range(runs_count):
            recipe = runs_order[slot]
            for entry in range(input_ptr[recipe], input_ptr[recipe + 1]):
                if input_life[entry] > 0.0:
                    required[input_good[entry]] += runs[recipe] * input_per_run[entry] / input_life[entry]
                else:
                    required[input_good[entry]] += runs[recipe] * input_per_run[entry]
        _shift_unmet_tools(required, runs, runs_order, runs_count, ceil, has_ceil, rank_ptr, rank_recipe, rank_output,
                           tool_ptr, tool_good, tool_per_run, tool_fallback, tool_fallback_units, wearing, partials)
        updated[:] = 0.0
        driven[:] = 0.0
        touched[:] = False
        new_count = 0
        for good in range(good_count):
            quantity = required[good]
            remaining = quantity
            for slot in range(rank_ptr[good], rank_ptr[good + 1]):
                if quantity <= 0.0:
                    break
                made = rank_made[slot]
                if made <= 0.0:
                    continue
                recipe = rank_recipe[slot]
                for_good = remaining / made
                if has_ceil[recipe] and ceil[recipe] < for_good:
                    for_good = ceil[recipe]
                runs_now = max(updated[recipe], for_good)
                updated[recipe] = runs_now
                if not touched[recipe]:
                    touched[recipe] = True
                    new_order[new_count] = recipe
                    new_count += 1
                if rank_main[slot]:
                    driven[recipe] = max(driven[recipe], for_good)
                remaining = quantity - runs_now * made
                if remaining <= 1e-9 * quantity:
                    break
        same = True
        for recipe in range(recipe_count):
            if abs(updated[recipe] - runs[recipe]) > 1e-9 * max(1.0, updated[recipe]):
                same = False
        if same:
            for recipe in range(recipe_count):
                runs_out[recipe] = updated[recipe]
            return passes + 1
        for recipe in range(recipe_count):
            runs[recipe] = updated[recipe]
        for slot in range(new_count):
            runs_order[slot] = new_order[slot]
        runs_count = new_count
    for recipe in range(recipe_count):
        runs_out[recipe] = runs[recipe]
    return INPUT_OUTPUT_PASSES
