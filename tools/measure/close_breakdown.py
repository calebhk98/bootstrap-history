"""Time inside `year_close.close_agents` by callee, by perf_counter: wall, kernel time and Python->kernel calls, inclusive and
exclusive of the callees timed below it.

    python3 tools/measure/close_breakdown.py SAVE [--repeat N]

A callee is wrapped in the module that calls it (the names below), so nothing else changes. Kernel time is taken at the
dispatcher call as in phase_ceiling.py. The save is read, never written."""
import importlib
import sys
import time

sys.path.insert(0, ".")
from tools.measure.phase_ceiling import wrap_kernels, _kernel   # noqa: E402
from tools.measure.warm_year_profile import warmed_game   # noqa: E402

WRAPPED = (
    ("sim.economy.year_close", "close_producers_of_year", "close_producers_of_year"),
    ("sim.economy.year_close", "learned_prices", "learned_prices"),
    ("sim.economy.year_close", "merchants.learn_year", "merchants.learn_year"),
    ("sim.economy.year_close", "merchants.close_all", "merchants.close_all"),
    ("sim.economy.year_close", "ownership.spread", "ownership.spread"),
    ("sim.economy.year_close", "carriage_hours.wage_loans", "carriage_hours.wage_loans"),
    ("sim.economy.year_close", "close_households", "close_households"),
    ("sim.economy.year_close_producers", "ProducerColumns.of", "ProducerColumns.of"),
    ("sim.economy.year_close_producers", "pack", "producers:pack"),
    ("sim.economy.year_close_producers", "close_producers", "producers:close_producers (kernel entry)"),
    ("sim.economy.year_close_producers", "_effects_by_row", "producers:_effects_by_row"),
    ("sim.economy.year_close_producers", "dividend_plan", "producers:dividend_plan"),
    ("sim.economy.year_close_producers", "post_dividends", "producers:post_dividends"),
    ("sim.economy.year_close_producers", "write_close", "producers:write_close"),
    ("sim.economy.year_close_producers", "add_property_income", "producers:add_property_income"),
    ("sim.economy.year_close_producers", "note_plant_worn", "producers:note_plant_worn"),
    ("sim.economy.year_close_producers", "shares.note_dividends", "producers:note_dividends"),
    ("sim.economy.year_close_producers", "expansion_price.price_share_of", "producers:price_share_of (builds)"),
    ("sim.economy.year_close_households", "households_close.closed_figures", "households:closed_figures"),
    ("sim.economy.year_close_households", "households_close_pack.PackedBaskets", "households:PackedBaskets"),
    ("sim.economy.year_close_households", "household_work_year.priced_basket_of", "households:priced_basket_of"),
    ("sim.economy.year_close_households", "household_work_year.basket_of_signature", "households:basket_of_signature"),
    ("sim.economy.year_close_households", "household_work_year.signatures_from_fields", "households:signatures"),
    ("sim.economy.year_close_households", "households_close_pack.unmet_by_cohort", "households:unmet_by_cohort"),
    ("sim.economy.year_close_households", "cohort_close_write.write_close", "households:cohort write_close"),
    ("sim.economy.year_close_households", "cohort_prime.prime_cohort_baskets", "households:prime_baskets"),
    ("sim.economy.year_close_households", "consumption_postings", "households:consumption_postings"),
    ("sim.economy.year_close_households", "_post_consumption", "households:_post_consumption"),
    ("sim.economy.year_close_households", "_number_unseen", "households:_number_unseen"),
    ("sim.economy.producer_close_write", "_write_crews", "write_close:_write_crews"),
    ("sim.economy.producer_close_write", "_write_expected_prices", "write_close:_write_expected_prices"),
    ("sim.economy.households_close", "next_own_plan", "households:next_own_plan"),
    ("sim.economy.households_close_pack", "PackedBaskets.add", "households:packed.add"),
)

stack = []
totals = {}
by_kernel = {}
inside = {"close": False}      # only calls made while close_agents runs are counted


def timed(name, function):
    def call(*arguments, **keywords):
        if not inside["close"] and name != "CLOSE_AGENTS (whole)":
            return function(*arguments, **keywords)
        if name == "CLOSE_AGENTS (whole)":
            inside["close"] = True
        started, kernel_before, calls_before = time.perf_counter(), _kernel["seconds"], _kernel["calls"]
        stack.append([0.0, 0.0, 0])
        try:
            return function(*arguments, **keywords)
        finally:
            wall = time.perf_counter() - started
            inner_wall, inner_kernel, inner_calls = stack.pop()
            kernel, calls = _kernel["seconds"] - kernel_before, _kernel["calls"] - calls_before
            entry = totals.setdefault(name, [0.0, 0.0, 0, 0.0, 0.0, 0, 0])
            entry[0] += wall
            entry[1] += kernel
            entry[2] += calls
            entry[3] += wall - inner_wall                  # exclusive wall
            entry[4] += kernel - inner_kernel              # exclusive kernel
            entry[5] += calls - inner_calls
            entry[6] += 1
            if name == "CLOSE_AGENTS (whole)":
                inside["close"] = False
            if stack:
                stack[-1][0] += wall
                stack[-1][1] += kernel
                stack[-1][2] += calls
    return call


def wrap(module_name, dotted, label):
    module = importlib.import_module(module_name)
    owner, _, attribute = dotted.rpartition(".")
    if not owner:
        setattr(module, attribute, timed(label, getattr(module, attribute)))
        return
    holder = module
    for part in owner.split("."):
        holder = getattr(holder, part)
    if isinstance(holder, type):
        setattr(holder, attribute, timed(label, holder.__dict__[attribute]) if not isinstance(holder.__dict__[attribute], (classmethod, staticmethod))
                else type(holder.__dict__[attribute])(timed(label, holder.__dict__[attribute].__func__)))
    else:       # a sibling module: wrap it for this caller only, through a namespace of its own
        import types
        proxy = types.SimpleNamespace(**vars(holder))
        setattr(proxy, attribute, timed(label, getattr(holder, attribute)))
        setattr(module, owner, proxy)


def main(save_path, repeat):
    game = warmed_game(save_path)
    wrap_kernels()
    from numba.core.registry import CPUDispatcher
    timed_call = CPUDispatcher.__call__

    def counted(dispatcher, *arguments, **keywords):
        started = time.perf_counter()
        try:
            return timed_call(dispatcher, *arguments, **keywords)
        finally:
            if inside["close"]:
                entry = by_kernel.setdefault(dispatcher.py_func.__name__, [0.0, 0])
                entry[0] += time.perf_counter() - started
                entry[1] += 1
    CPUDispatcher.__call__ = counted
    for module_name, dotted, label in WRAPPED:
        wrap(module_name, dotted, label)
    from sim.economy import economy as economy_module
    close_name = "close_agents"
    setattr(economy_module, close_name, timed("CLOSE_AGENTS (whole)", getattr(economy_module, close_name)))
    for _ in range(repeat):
        game.step()
    print("per year, seconds; inclusive wall / kernel / python / kernel calls ; exclusive wall / kernel / python / calls ; n")
    for name, (wall, kernel, calls, ewall, ekernel, ecalls, count) in sorted(totals.items(), key=lambda item: -item[1][0]):
        print("%-46s incl %.4f %.4f %.4f %5d | excl %.4f %.4f %.4f %5d | n %d" % (
            name, wall / repeat, kernel / repeat, (wall - kernel) / repeat, calls // repeat,
            ewall / repeat, ekernel / repeat, (ewall - ekernel) / repeat, ecalls // repeat, count // repeat))
    print("\nkernels called from Python inside the close (per year): seconds, calls")
    for name, (seconds, calls) in sorted(by_kernel.items(), key=lambda item: -item[1][0]):
        print("  %-50s %.4f %5d" % (name, seconds / repeat, calls // repeat))


if __name__ == "__main__":
    arguments = sys.argv[1:]
    repeat = 1
    if "--repeat" in arguments:
        position = arguments.index("--repeat")
        repeat = int(arguments[position + 1])
        del arguments[position:position + 2]
    main(arguments[0], repeat)

