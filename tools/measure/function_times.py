"""Wall time of named functions in the second (warm) year of a saved game, by perf_counter (no profiler inflation).

    python3 tools/measure/function_times.py SAVE [module:Class.function ...]

Each name is `sim.economy.module:function` or `sim.economy.module:Class.method`; a function the economy imported by name must be
named where it is bound (`sim.economy.economy:cohort_orders`). Times are inclusive and counted again inside a caller that is also
listed. With no names it times the cohort orders and what they call. The save is read, never written. Compare with
`simulator.py year-time` for the whole year; cProfile (`warm_year_profile.py`) says where, this says how long."""
import importlib
import random
import sys
import time

sys.path.insert(0, ".")
from sim.engine.ui_port import Sim, load, load_civ   # noqa: E402
from sim.ui.protocol import civ_of_save, load_state   # noqa: E402

COHORT_ORDERS = [
    "sim.economy.economy:cohort_orders", "sim.economy.households_orders_pack:kernel_orders",
    "sim.economy.households_orders_pack:_Arrays.add_template", "sim.economy.households_store:store_holding",
    "sim.economy.households_orders_pack:_orders_of", "sim.economy.households_orders_kernel:year_orders",
    "sim.economy.credit_view:CreditView.equity", "sim.economy.land_bid_year:land_bids", "sim.economy.tool_wear:tool_bids",
    "sim.economy.households_cohort:change_cohort", "sim.economy.opening_bid_memory:BidMemory.priced"]


def timed_copy(name, totals):
    module_name, attribute = name.split(":")
    owner = importlib.import_module(module_name)
    method = attribute
    if "." in attribute:
        class_name, method = attribute.split(".")
        owner = getattr(owner, class_name)
    function = getattr(owner, method)

    def timed(*arguments, **keywords):
        started = time.perf_counter()
        try:
            return function(*arguments, **keywords)
        finally:
            entry = totals.setdefault(name, [0.0, 0])
            entry[0] += time.perf_counter() - started
            entry[1] += 1
    setattr(owner, method, timed)


def main(save_path, names):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_of_save(save_path)), defer_economy=True)
    load_state(game, save_path)
    game.step()
    totals = {}
    for name in names or COHORT_ORDERS:
        timed_copy(name, totals)
    started = time.perf_counter()
    game.step()
    whole = time.perf_counter() - started
    print("whole step %.3f s" % whole)
    for name, (seconds, calls) in sorted(totals.items(), key=lambda item: -item[1][0]):
        print("%-62s %8.4f s %6d calls %6.2f%% of the step" % (name, seconds, calls, 100.0 * seconds / whole))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
