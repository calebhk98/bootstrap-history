"""The entry rules' costing as compiled loops over the year arrays: what a run of a recipe costs and returns on a tile, and
which tile a newcomer goes to.

`tables` is one tuple of arrays (built by entry_tables.py from the year arrays), indexed by recipe row, good column, trade
column and tile row:
    quantity      (3, recipes, goods)   inputs, outputs, plant goods a run takes in, makes, ties up
    hours         (2, recipes, trades)  the hours a run takes, the hours its plant takes to build
    slot_goods    (recipes, slots)      the good columns a recipe touches, -1 padded
    slot_trades   (recipes, slots)      the trade columns a recipe touches, -1 padded
    price         (2, tiles, goods)     the remembered price in each tile's market area, the price on offer there; NaN: none
    wage          (tiles, trades)       the wage rule's wage
    recipe_scalar (recipes, 2)          plant life in years, hectares a run takes
    tile_scalar   (tiles, 2)            the land market's rent per hectare, the mean value a hectare earns
    start_units   (recipes, trades)     the practice an entrant's crew starts at (entry_practice.entrant_crew)
    curve         (3,)                  the learning curve's exponent, its floor, the years an entrant is judged over
A missing price is NaN and makes a bill infinite, as in unit_cost.py. Each function is the rule of the same name there, in
entry.py, entry_trial.py, entry_practice.py, entrant_rent.py and location.py; sums run over a recipe's slots in sorted order
where the Python sums in dictionary order or with math.fsum, so the last digits differ (test_year_speed_entry_arrays)."""
import numpy as np

from sim.jit import njit

from .close_kernel_cost import capital_charge
from .year_arrays_costs import KERNEL, bill_goods, bill_hours, price_in, recovery_factor

NO_SLOT = -1


@njit
def hours_multiplier(units, exponent, floor):
    """practice.hours_multiplier: the hours a run takes over the booked ones at `units` of practice."""
    return max(floor, max(1.0, units) ** exponent) / floor


@njit
def planned_hours(booked, start, runs, years, exponent, floor):
    """entry_practice.planned_recipe for one trade: the mean over `years` years of an entrant's hours, starting at `start` units
    of practice and learning `runs` a year. A year's hours are the booked ones times the multiplier kept to a hundredth."""
    units = start
    total = 0.0
    for _year in range(years):
        multiplier = np.rint(hours_multiplier(units, exponent, floor) * 100.0) / 100.0
        total += booked * max(1.0, multiplier)
        units += max(0.0, runs)
    return total / years


@njit
def input_bill(r, t, quantity, slot_goods, price):
    """unit_cost.input_cost_per_run at the prices of tile `t`."""
    total = 0.0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[r, slot]
        if good == NO_SLOT:
            break
        amount = quantity[0, r, good]
        if amount <= 0.0:
            continue
        found = price[0, t, good]
        if np.isnan(found):
            return np.inf
        total += amount * found
    return total


@njit
def plant_goods_bill(r, t, quantity, slot_goods, price):
    total = 0.0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[r, slot]
        if good == NO_SLOT:
            break
        amount = quantity[2, r, good]
        if amount <= 0.0:
            continue
        found = price[0, t, good]
        if np.isnan(found):
            return np.inf
        total += amount * found
    return total


@njit
def labour_bill(r, t, kind, hours, slot_trades, wage, start_units, runs, planned, curve):
    """unit_cost.labour_cost_per_run (kind 0) or the plant's labour (kind 1) at the wages of tile `t`; with `planned`, the
    labour of kind 0 at an entrant's mean hours over the years it is judged (entry_practice.planned_recipe)."""
    total = 0.0
    for slot in range(slot_trades.shape[1]):
        trade = slot_trades[r, slot]
        if trade == NO_SLOT:
            break
        booked = hours[kind, r, trade]
        if booked <= 0.0:
            continue
        pay = wage[t, trade]
        if np.isnan(pay):
            return np.inf
        used = booked
        if planned and kind == 0:
            used = planned_hours(booked, start_units[r, trade], runs, int(curve[2]), curve[0], curve[1])
        total += used * pay
    return total


@njit
def revenue_at(r, t, which, quantity, slot_goods, price, layer=3):
    """unit_cost.revenue_per_run: every output at its price (`which` 0: the remembered price, 1: the price on offer), an output
    with none left out. `layer` picks the quantities: 3, what the run makes as it fetches after the state's harvest share; 1, what it makes."""
    total = 0.0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[r, slot]
        if good == NO_SLOT:
            break
        amount = quantity[layer, r, good]
        if quantity[1, r, good] <= 0.0:
            continue
        found = price[which, t, good]
        if not np.isnan(found):
            total += amount * found
    return total


@njit
def rent_of(r, t, yield_factor, quantity, slot_goods, price, recipe_scalar, tile_scalar):
    """entrant_rent.site_rent_per_run: the tile's rent in proportion to the newcomer's use's value a hectare."""
    land = recipe_scalar[r, 1]
    if land <= 0.0:
        return 0.0
    revenue = revenue_at(r, t, 1, quantity, slot_goods, price) * yield_factor
    rent = tile_scalar[t, 0]
    mean_value = tile_scalar[t, 1]
    if not mean_value > 0.0:
        return rent * land
    return rent * max(0.0, revenue / land) / mean_value * land


@njit
def full_cost_one(r, t, good, runs, rate, tables):
    """unit_cost.full_cost_per_unit of `good` made by recipe row `r` on tile `t` at yield one, the rent the site asks, the
    hours booked (`runs` NaN) or an entrant's over the years it is judged on `runs` runs a year. NaN or infinite when it cannot be
    costed."""
    quantity, hours, slot_goods, slot_trades, price, wage, recipe_scalar, tile_scalar, start_units, curve = tables
    planned = not np.isnan(runs)
    made = quantity[1, r, good]
    if made <= 0.0:
        return np.inf
    rent = rent_of(r, t, 1.0, quantity, slot_goods, price, recipe_scalar, tile_scalar)
    variable = (input_bill(r, t, quantity, slot_goods, price)
                + labour_bill(r, t, 0, hours, slot_trades, wage, start_units, runs, planned, curve) + rent)
    plant = plant_goods_bill(r, t, quantity, slot_goods, price) + labour_bill(
        r, t, 1, hours, slot_trades, wage, start_units, runs, planned, curve)
    run_cost = variable + capital_charge(plant, recipe_scalar[r, 0], rate)
    if not np.isfinite(run_cost):
        return np.inf
    revenue = revenue_at(r, t, 0, quantity, slot_goods, price, 1)       # the cost is shared by what is made, not by what the tax leaves
    own_price = price[0, t, good]
    own_value = made * own_price if not np.isnan(own_price) else 0.0
    if revenue > 0.0 and own_value > 0.0:
        share = own_value / revenue
    else:
        total_made = 0.0
        for column in range(quantity.shape[2]):
            total_made += quantity[1, r, column]
        share = made / total_made
    return run_cost * share / made


@njit
def full_costs(recipe_rows, tile_rows, good_cols, runs, rate, tables):
    """`full_cost_one` for each request."""
    out = np.empty(recipe_rows.shape[0])
    for i in range(recipe_rows.shape[0]):
        out[i] = full_cost_one(recipe_rows[i], tile_rows[i], good_cols[i], runs[i], rate, tables)
    return out


@njit
def returns_many(recipe_rows, tile_rows, runs, rates, tables):
    """entry._returns_at for each request: (the yearly return on capital, the same after the plant's wear at `rates[i]`) of the
    recipe on the tile at the price on offer there and the rent the site asks, NaN where nothing is employed or it cannot be priced.
    `runs` NaN: the booked hours."""
    quantity, hours, slot_goods, slot_trades, price, wage, recipe_scalar, tile_scalar, start_units, curve = tables
    count = recipe_rows.shape[0]
    gross = np.full(count, np.nan)
    after = np.full(count, np.nan)
    for i in range(count):
        r, t = recipe_rows[i], tile_rows[i]
        planned = not np.isnan(runs[i])
        rent = rent_of(r, t, 1.0, quantity, slot_goods, price, recipe_scalar, tile_scalar)
        variable = (input_bill(r, t, quantity, slot_goods, price)
                    + labour_bill(r, t, 0, hours, slot_trades, wage, start_units, runs[i], planned, curve) + rent)
        plant = plant_goods_bill(r, t, quantity, slot_goods, price) + labour_bill(
            r, t, 1, hours, slot_trades, wage, start_units, runs[i], planned, curve)
        employed = plant + variable
        if not np.isfinite(employed) or employed <= 0.0:
            continue
        gross[i] = (revenue_at(r, t, 1, quantity, slot_goods, price) - variable) / employed
        wear = capital_charge(plant, recipe_scalar[r, 0], rates[i]) - rates[i] * plant
        after[i] = gross[i] - wear / employed
    return gross, after


@njit
def supply_by_tile(recipe_rows, tile_rows, capacity, yield_factor, outputs, tile_count):
    """location_inputs.supply_tiles for every good: the units a year each tile's producers (in the order given) can make, and
    whether any producer there makes the good with capacity."""
    weight = np.zeros((outputs.shape[1], tile_count))
    present = np.zeros((outputs.shape[1], tile_count), dtype=np.bool_)
    for p in range(recipe_rows.shape[0]):
        if capacity[p] <= 0.0:
            continue
        for good in range(outputs.shape[1]):
            made = outputs[recipe_rows[p], good]
            if made > 0.0:
                weight[good, tile_rows[p]] += capacity[p] * yield_factor[p] * made
                present[good, tile_rows[p]] = True
    return weight, present


@njit
def idle_output(recipe_rows, tile_rows, capacity, last_runs, pending, land_run_cap, yield_factor, outputs, area_of_good_tile,
                area_count):
    """entry_year._spare_output as a grid over good and area: the output the idle capacity of each market's makers could add
    (entry_spare.idle_runs), in the order the producers are given."""
    spare = np.zeros((outputs.shape[1], area_count))
    for p in range(recipe_rows.shape[0]):
        room = capacity[p] - max(0.0, last_runs[p]) + pending[p]
        if not np.isnan(land_run_cap[p]):
            room = min(room, land_run_cap[p] - max(0.0, last_runs[p]))
        idle = max(0.0, room)
        if idle <= 0.0:
            continue
        for good in range(outputs.shape[1]):
            made = outputs[recipe_rows[p], good]
            if made > 0.0 and area_of_good_tile[good, tile_rows[p]] >= 0:
                spare[good, area_of_good_tile[good, tile_rows[p]]] += idle * made * yield_factor[p]
    return spare


@njit
def reach_by_area(recipe_rows, tile_rows, capacity, yield_factor, pending, outputs, area_of_good_tile, area_count):
    """entry_trial.capacity_terms_by_good summed over each market area: the output of each good the makers in the area could
    reach, the plant to come counted (producers in the order given)."""
    reach = np.zeros((outputs.shape[1], area_count))
    for p in range(recipe_rows.shape[0]):
        for good in range(outputs.shape[1]):
            made = outputs[recipe_rows[p], good]
            if made > 0.0 and area_of_good_tile[good, tile_rows[p]] >= 0:
                reach[good, area_of_good_tile[good, tile_rows[p]]] += (capacity[p] * yield_factor[p] + pending[p]) * made
    return reach


@njit
def input_haul(r, t, tonnes, supply_weight, supply_present, carriage):
    """location_inputs.input_haul_cost: the carriage of one run's inputs into tile `t` from where each is made, each good's
    carriage the mean over its makers' tiles weighted by what they make."""
    haul = 0.0
    for good in range(tonnes.shape[1]):
        carried = tonnes[r, good]
        if carried <= 0.0:
            continue
        total = 0.0
        moved = 0.0
        for source in range(supply_weight.shape[1]):
            if supply_present[good, source]:
                total += supply_weight[good, source]
                moved += supply_weight[good, source] * carriage[source, t]
        if total > 0.0:
            haul += carried * (moved / total)
    return haul


@njit
def site_choice(r, anchor, candidates, runs, tonnes_out, tables, tonnes, supply_weight, supply_present, carriage, hauls, yield_rt,
                limit_rt, takes_land, short_of_land, hands_hours, capacity, committed, hours_per_run):
    """location.entry_siting for the candidate tiles (rows, in the order tried): each tile's cost per run (inputs and labour at
    its prices, its rent, the carriage of the output to `anchor` and of the inputs in, over its yield), the runs its idle hands
    can staff and its site still allows, and `location.choose` among them. Returns (tile row or -1, runs); the runs are booked
    in `capacity` and `committed` (location.claim_site). `hauls` keeps each (recipe, tile) input haul once read (NaN: not yet)."""
    quantity, hours, slot_goods, slot_trades, price, wage, recipe_scalar, tile_scalar, start_units, curve = tables
    count = candidates.shape[0]
    cost = np.empty(count)
    staffable = np.empty(count)
    headroom = np.empty(count)
    for i in range(count):
        t = candidates[i]
        factor = yield_rt[r, t]
        room = max(0.0, limit_rt[r, t] - capacity[r, t])
        headroom[i] = 0.0 if takes_land and short_of_land[t] else room
        spare = max(0.0, hands_hours[t] - committed[t])
        staffable[i] = np.inf if hours_per_run <= 0.0 else spare / hours_per_run
        if factor <= 0.0:
            cost[i] = np.inf
            continue
        if np.isnan(hauls[r, t]):
            hauls[r, t] = input_haul(r, t, tonnes, supply_weight, supply_present, carriage)
        variable = (input_bill(r, t, quantity, slot_goods, price)
                    + labour_bill(r, t, 0, hours, slot_trades, wage, start_units, 0.0, False, curve)
                    + rent_of(r, t, factor, quantity, slot_goods, price, recipe_scalar, tile_scalar))
        carried = carriage[t, anchor] * tonnes_out if tonnes_out > 0.0 else 0.0
        cost[i] = (variable + carried + hauls[r, t]) / factor
    best = -1
    for i in range(count):
        if headroom[i] > 0.0 and staffable[i] >= runs:
            if best < 0:
                best = i
                continue
            t, held = candidates[i], candidates[best]
            if cost[i] < cost[best]:
                best = i
            elif cost[i] == cost[best]:
                if (t != anchor, t) < (held != anchor, held):
                    best = i
    if best < 0:
        for i in range(count):
            if headroom[i] > 0.0 and staffable[i] > 0.0:
                if best < 0 or staffable[i] > staffable[best] or (staffable[i] == staffable[best] and -cost[i] > -cost[best]):
                    best = i
    if best < 0:
        return -1, 0.0
    taken = min(runs, staffable[best], headroom[best])
    tile = candidates[best]
    capacity[r, tile] += taken
    committed[tile] += taken * hours_per_run
    return tile, taken


@njit(**KERNEL)
def pays_after_recovery(recipe, tile, rent, held_expected, slot_goods, inputs, outputs, revenue_outputs, plant_goods, labour_hours, plant_labour_hours,
                        plant_life, price, offered, wage, area_of, rate):
    """Whether `unit_cost.return_after_recovery` of a run of the recipe on the tile beats `rate`: the surplus (revenue at the
    producer's expected prices, else the price on offer in its market, less the variable cost) less the part of the plant's
    capital charge that repays the plant, over the capital a run employs (its plant and its variable cost). A run that cannot be
    priced, or employs nothing, does not pay."""
    variable = bill_goods(inputs[recipe], price, area_of, tile) + bill_hours(labour_hours[recipe], wage, tile) + rent
    plant = bill_goods(plant_goods[recipe], price, area_of, tile) + bill_hours(plant_labour_hours[recipe], wage, tile)
    employed = plant + variable
    if not np.isfinite(employed) or employed <= 0.0:
        return False
    revenue = 0.0
    for slot in range(slot_goods.shape[1]):
        good = slot_goods[recipe, slot]
        if good == NO_SLOT:
            break
        if outputs[recipe, good] > 0.0:
            found = held_expected[slot]
            if np.isnan(found):
                found = price_in(offered, area_of, good, tile)
            if not np.isnan(found):
                revenue += revenue_outputs[recipe, good] * found
    if plant == 0.0:
        charge = 0.0
    elif plant_life[recipe] <= 0.0:
        charge = plant
    else:
        charge = plant * recovery_factor(rate, plant_life[recipe])
    return (revenue - variable) / employed - (charge - rate * plant) / employed > rate


@njit(**KERNEL)
def restake_amounts(recipe_row, tile_row, shortfall, rent, held_expected, owner_of, owner_cash, slot_goods, inputs, outputs,
                    revenue_outputs, plant_goods, labour_hours, plant_labour_hours, plant_life, price, offered, wage, area_of, rate, stake_share):
    """What each producer row is restaked with (zero for the rows without a shortfall, `shortfall` <= 0), in row order:
    `entry.restake` (the shortfall, from the stake share of the owner's cash now, only where the run pays after recovery), not
    above the owner's budget, which is the stake share of the cash it held when its first producer came up and is spent down.
    `owner_cash` (by owner) is spent as the stakes are made, and is written to."""
    amounts = np.zeros(len(shortfall))
    budget = np.full(len(owner_cash), np.nan)
    for row in range(len(shortfall)):
        if not shortfall[row] > 0.0:
            continue
        owner = owner_of[row]
        if np.isnan(budget[owner]):
            budget[owner] = stake_share * max(0.0, owner_cash[owner])
        if not pays_after_recovery(recipe_row[row], tile_row[row], rent[row], held_expected[row], slot_goods, inputs, outputs,
                                   revenue_outputs, plant_goods, labour_hours, plant_labour_hours, plant_life, price, offered, wage, area_of, rate):
            continue
        amount = min(min(shortfall[row], stake_share * max(0.0, owner_cash[owner])), budget[owner])
        if amount > 0.0:
            budget[owner] -= amount
            owner_cash[owner] -= amount
            amounts[row] = amount
    return amounts
