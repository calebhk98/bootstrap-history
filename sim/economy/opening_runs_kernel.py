"""Runs a year of each recipe that meet a final demand, over recipe matrices (the kernel of `opening_runs_pack.py`).

`opening_runs.required_runs` and `tool_fallback.shift_unmet_tools` written once over arrays: a recipe's inputs, plant wear
and tool wear are compressed rows, a good's ranked makers a compressed list. Goods and recipes are positions in sorted
order."""
import numpy as np

from sim.jit import njit

INPUT_OUTPUT_PASSES = 60


@njit
def _shift_unmet_tools(required, runs, ceil, has_ceil, rank_ptr, rank_recipe, rank_output, tool_ptr, tool_good,
                       tool_per_run, tool_fallback, tool_fallback_units, wearing):
    """tool_fallback.shift_unmet_tools: where every maker of a tool is held to a ceiling and the runs wear more than they
    make, the same share of every user's wear is met by its next tool."""
    wearing[:] = 0.0
    for recipe in range(runs.shape[0]):
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
        capacity = 0.0
        for slot in range(first, last):
            capacity += ceil[rank_recipe[slot]] * rank_output[slot]
        unmet = min(wear, required[good] - capacity)
        if unmet <= 0.0:
            continue
        share = unmet / wear
        for recipe in range(runs.shape[0]):
            for entry in range(tool_ptr[recipe], tool_ptr[recipe + 1]):
                if tool_good[entry] == good and tool_per_run[entry] > 0.0 and tool_fallback[entry] >= 0:
                    required[good] -= share * runs[recipe] * tool_per_run[entry]
                    required[tool_fallback[entry]] += share * runs[recipe] * tool_fallback_units[entry]


@njit
def required_runs(national, static_ceil, has_static, rank_ptr, rank_recipe, rank_made, rank_output, rank_main,
                  input_ptr, input_good, input_per_run, tool_ptr, tool_good, tool_per_run, tool_fallback,
                  tool_fallback_units, bp_ptr, bp_maker_ptr, bp_maker, bp_maker_made, bp_user_ptr, bp_user,
                  bp_user_needed, runs_out):
    """opening_runs.required_runs: fills `runs_out` (runs of each recipe) and returns the passes used. `national` is the final
    demand by good."""
    recipe_count = static_ceil.shape[0]
    good_count = national.shape[0]
    runs = np.zeros(recipe_count)
    driven = np.zeros(recipe_count)
    updated = np.zeros(recipe_count)
    ceil = np.zeros(recipe_count)
    has_ceil = np.zeros(recipe_count, dtype=np.bool_)
    required = np.zeros(good_count)
    wearing = np.zeros(good_count)
    for passes in range(INPUT_OUTPUT_PASSES):
        for recipe in range(recipe_count):
            ceil[recipe] = static_ceil[recipe]
            has_ceil[recipe] = has_static[recipe]
        for group in range(bp_ptr.shape[0] - 1):
            supply = 0.0
            for slot in range(bp_maker_ptr[group], bp_maker_ptr[group + 1]):
                supply += driven[bp_maker[slot]] * bp_maker_made[slot]
            for slot in range(bp_user_ptr[group], bp_user_ptr[group + 1]):
                user = bp_user[slot]
                limit = supply / bp_user_needed[slot]
                if not has_ceil[user] or limit < ceil[user]:
                    ceil[user] = limit
                has_ceil[user] = True
        for good in range(good_count):
            required[good] = national[good]
        for recipe in range(recipe_count):
            for entry in range(input_ptr[recipe], input_ptr[recipe + 1]):
                required[input_good[entry]] += runs[recipe] * input_per_run[entry]
        _shift_unmet_tools(required, runs, ceil, has_ceil, rank_ptr, rank_recipe, rank_output, tool_ptr, tool_good,
                           tool_per_run, tool_fallback, tool_fallback_units, wearing)
        updated[:] = 0.0
        driven[:] = 0.0
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
    for recipe in range(recipe_count):
        runs_out[recipe] = runs[recipe]
    return INPUT_OUTPUT_PASSES
