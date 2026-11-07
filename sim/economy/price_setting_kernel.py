"""The sellers' price search (price_setting.best_price) as a numba kernel over every seller of a market at once. The rules
and their constants are price_setting.py's; the constants arrive as arguments so this module imports nothing from it."""
import numpy

from sim.jit import njit


@njit(error_model="numpy")
def expected_earnings(price, unit_value, expected_sales, stock, months, discount_rate):
    """The year's discounted earnings at `price`, sold evenly by month out of `stock` (price_setting.expected_earnings)."""
    total, left = 0.0, stock
    for month in range(months):
        sold = min(left, expected_sales / months)
        left -= sold
        total += sold * (price - unit_value) / (1.0 + discount_rate) ** month
    return total


@njit(error_model="numpy")
def earnings_at(price, own, unit_value, market_size, rival_asks, rival_counts, stock, intensity, months, discount_rate):
    """Earnings of seller `own` of the market asking `price` against every other seller with a positive count."""
    others = 0.0
    for rival in range(len(rival_asks)):
        if rival != own and rival_counts[rival] > 0.0 and rival_asks[rival] > 0.0:
            others += rival_counts[rival] * numpy.exp(-intensity * numpy.log(rival_asks[rival] / price))
    share = 1.0 / (1.0 + others)
    return expected_earnings(price, unit_value, market_size * share, stock, months, discount_rate)


@njit(error_model="numpy")
def best_prices(rival_asks, rival_counts, own, current, unit_value, market_size, stock, floor, ceiling, intensity,
                grid_count, grid_start, grid_step, months, discount_rate):
    """For each seller i (position `own[i]` in the market's arrays; -1 for none): the price on the grid around its
    current price, kept between floor and ceiling, that earns most; a tie keeps the current price. `rival_counts` is
    zero for a seller that is no rival (nothing to sell, no ask)."""
    chosen = numpy.zeros(len(own))
    for seller in range(len(own)):
        best = current[seller]
        best_earnings = earnings_at(best, own[seller], unit_value[seller], market_size[seller], rival_asks,
                                    rival_counts, stock[seller], intensity, months, discount_rate)
        candidates = numpy.zeros(grid_count)
        for step in range(grid_count):
            price = current[seller] * (grid_start + step * grid_step)
            candidates[step] = min(max(price, floor[seller]), ceiling[seller])
        candidates.sort()
        previous = numpy.nan
        for step in range(grid_count):
            candidate = candidates[step]
            if candidate == previous:
                continue
            previous = candidate
            if candidate <= 0.0:
                continue
            earnings = earnings_at(candidate, own[seller], unit_value[seller], market_size[seller], rival_asks,
                                   rival_counts, stock[seller], intensity, months, discount_rate)
            if earnings > best_earnings + 1e-12 * max(abs(best_earnings), 1e-300):
                best, best_earnings = candidate, earnings
        chosen[seller] = best
    return chosen
