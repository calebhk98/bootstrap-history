"""Complaint 553: variants of the controlled spin-up and the statistics that compare them.

A measurement run on demand (`simulator.py spin-up-sensitivity`), not a check. A variant is a context manager that
changes how the economy adjusts (speeds of the declared adjustment constants, the order of two phases in the year,
a seeded speed per producer) by patching the running modules; no constant is edited. `statistics_of(series)` gives
a series' drift, cycle amplitude and cycle period; `table` prints one line per variant. The finding it recorded
(Complaint 553): no variant removes the cycle and the amplitude moves by well under a factor of two, so the cycle
is the economy's and not the shared yearly step's; the period moves with the speeds.
"""
import contextlib
import hashlib
import math
import sys
from unittest import mock

from . import economy as economy_module, producers, producers_close

SPEED_GROUPS = {
    "producer_plans": ("EXPANSION_SHARE_PER_YEAR", "OUTPUT_CHANGE_SHARE_PER_YEAR", "EXPECTATION_ADJUSTMENT_SHARE"),
    "ask_prices": ("SOLD_OUT_ASK_RAISE_SHARE", "USUAL_PRICE_SPEED"),
    "wages": ("TIGHTNESS_ADJUSTMENT_RATE_PER_YEAR", "TIGHTNESS_REVERSION_RATE_PER_YEAR"),
    "interest_rate": ("RATE_ADJUSTMENT_SHARE_PER_YEAR",),
}
ALL_SPEEDS = tuple(name for names in SPEED_GROUPS.values() for name in names)
SPEED_CEILING = 1.0         # a share of a gap closed in a year cannot exceed the whole gap


def _holders(name):
    """Every loaded sim module with an attribute `name`, and its value (a constant is imported by name)."""
    return [(module, getattr(module, name)) for key, module in sorted(sys.modules.items())
            if key.startswith("sim.") and module is not None and hasattr(module, name)]


@contextlib.contextmanager
def scaled_speeds(names, factor):
    """Within the block, each declared constant in `names` is `factor` times its value in every module that holds it."""
    with contextlib.ExitStack() as stack:
        for name in names:
            for module, value in _holders(name):
                stack.enter_context(mock.patch.object(module, name, min(value * factor, SPEED_CEILING)))
        yield


def speed_factor_of(agent_id, seed, spread):
    """A number in [1 - spread, 1 + spread], fixed by the seed and the agent's id."""
    digest = hashlib.sha256(("%s:%s" % (seed, agent_id)).encode()).digest()
    return 1.0 + spread * (2.0 * int.from_bytes(digest[:4], "big") / 0xFFFFFFFF - 1.0)


@contextlib.contextmanager
def speeds_set_by_producer(seed, spread, names=SPEED_GROUPS["producer_plans"] + SPEED_GROUPS["ask_prices"][:1]):
    """Within the block, the functions that take a producer run with each of `names` scaled by that producer's
    own factor (speed_factor_of), so producers do not all react at one speed. The constants are module
    globals, so the functions are wrapped to set them for the length of one producer's call."""
    base = {name: _holders(name) for name in names}

    def wrapped(function):
        def call(producer, *args, **kwargs):
            factor = speed_factor_of(producer.agent_id, seed, spread)
            with contextlib.ExitStack() as stack:
                for name, holders in base.items():
                    for module, value in holders:
                        stack.enter_context(mock.patch.object(module, name, min(value * factor, SPEED_CEILING)))
                return function(producer, *args, **kwargs)
        return call

    targets = [(module, name, value) for name in ("plan", "next_expectations", "_expansion")
               for module, value in _holders(name)
               if getattr(value, "__module__", "") in (producers.__name__, producers_close.__name__)]
    with contextlib.ExitStack() as stack:
        for module, name, value in targets:
            stack.enter_context(mock.patch.object(module, name, wrapped(value)))
        yield


@contextlib.contextmanager
def exit_before_entry():
    """Within the block, idle producers close before entrants open instead of after (two phases of the year's
    close swapped)."""
    original_open, original_close = economy_module.open_entrants, economy_module.close_idle_producers

    def open_after_closing(setup, record, *args, **kwargs):
        original_close(setup, record)
        return original_open(setup, record, *args, **kwargs)

    with mock.patch.object(economy_module, "open_entrants", open_after_closing), \
            mock.patch.object(economy_module, "close_idle_producers", lambda setup, record: None):
        yield


VARIANTS = {
    "baseline": contextlib.nullcontext,
    "producer_plans x0.5": lambda: scaled_speeds(SPEED_GROUPS["producer_plans"], 0.5),
    "producer_plans x2": lambda: scaled_speeds(SPEED_GROUPS["producer_plans"], 2.0),
    "ask_prices x0.5": lambda: scaled_speeds(SPEED_GROUPS["ask_prices"], 0.5),
    "ask_prices x2": lambda: scaled_speeds(SPEED_GROUPS["ask_prices"], 2.0),
    "wages x0.5": lambda: scaled_speeds(SPEED_GROUPS["wages"], 0.5),
    "wages x2": lambda: scaled_speeds(SPEED_GROUPS["wages"], 2.0),
    "interest_rate x0.5": lambda: scaled_speeds(SPEED_GROUPS["interest_rate"], 0.5),
    "interest_rate x2": lambda: scaled_speeds(SPEED_GROUPS["interest_rate"], 2.0),
    "all speeds x0.5": lambda: scaled_speeds(ALL_SPEEDS, 0.5),
    "all speeds x2": lambda: scaled_speeds(ALL_SPEEDS, 2.0),
    "exit before entry": exit_before_entry,
    "per-producer speed seed 1": lambda: speeds_set_by_producer(1, 0.5),
    "per-producer speed seed 2": lambda: speeds_set_by_producer(2, 0.5),
}


def _least_squares_line(values):
    count = len(values)
    mean_x, mean_y = (count - 1) / 2.0, sum(values) / count
    spread = sum((i - mean_x) ** 2 for i in range(count))
    slope = sum((i - mean_x) * (value - mean_y) for i, value in enumerate(values)) / spread
    return slope, mean_y - slope * mean_x


def period_of(residuals, shortest=3.0, longest=None, step=0.25):
    """The period (years) of the sinusoid that best fits `residuals`, searched from `shortest` to `longest`
    (default: half the series); 0.0 for a series with no variation."""
    longest = longest or len(residuals) / 2.0
    best_period, best_power = 0.0, 0.0
    period = shortest
    while period <= longest:
        angle = 2.0 * math.pi / period
        cosine = sum(value * math.cos(angle * i) for i, value in enumerate(residuals))
        sine = sum(value * math.sin(angle * i) for i, value in enumerate(residuals))
        if cosine * cosine + sine * sine > best_power:
            best_period, best_power = period, cosine * cosine + sine * sine
        period += step
    return best_period


def statistics_of(series, skip=0):
    """Drift, amplitude and period of the log of a positive series, after its first `skip` years.
    `drift` is the least-squares slope of the log per year; `amplitude` the standard deviation of the log
    around that line; `period` the best-fitting sinusoid's period in years; `flips` the share of year-to-year
    moves that reverse the one before (a high share is a two-year alternation)."""
    logs = [math.log(value) for value in series[skip:]]
    slope, intercept = _least_squares_line(logs)
    residuals = [value - (intercept + slope * i) for i, value in enumerate(logs)]
    amplitude = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    moves = [later - earlier for earlier, later in zip(logs, logs[1:])]
    flips = sum(1 for earlier, later in zip(moves, moves[1:]) if earlier * later < 0.0) / max(len(moves) - 1, 1)
    return {"drift": slope, "amplitude": amplitude, "period": period_of(residuals) if amplitude > 0.0 else 0.0,
            "flips": flips}


def table(series_of, years, skip, variants=None):
    """One line per variant: the price level's and the wage's drift per year, amplitude and period in years."""
    lines = []
    for variant in (variants or VARIANTS):
        prices, wages = series_of(variant, years)
        found = {"price": statistics_of(prices, skip), "wage": statistics_of(wages, skip)}
        lines.append("%-28s %s" % (variant, " | ".join(
            "%s drift %+.4f amplitude %.3f period %5.2f" % (name, stats["drift"], stats["amplitude"], stats["period"])
            for name, stats in found.items())))
    return "\n".join(lines)
