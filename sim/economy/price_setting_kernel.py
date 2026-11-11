"""The sellers' price search (price_setting.best_price) as a numba kernel over every seller of a market at once. The rules
and their constants are price_setting.py's; the constants arrive as arguments so this module imports nothing from it."""
import numpy

from sim.jit import njit

STOCK_SLACK = 1e-9      # how far above a year's sales a stock must be for no month to run short, whatever the rounding


@njit(error_model="numpy")
def expected_earnings(price, unit_value, expected_sales, stock, months, discounts, annuity):
    """The year's discounted earnings at `price`, sold evenly by month out of `stock` (price_setting.expected_earnings);
    `discounts[month]` is (1 + discount rate) ** month and `annuity` the sum of their reciprocals. A stock that covers the
    year's sales sells the same each month, so the sum is one product."""
    monthly = expected_sales / months
    margin = price - unit_value
    if stock >= expected_sales * (1.0 + STOCK_SLACK):
        return monthly * margin * annuity
    total, left = 0.0, stock
    for month in range(months):
        sold = min(left, monthly)
        left -= sold
        total += sold * margin / discounts[month]
    return total


@njit(error_model="numpy")
def earnings_at(price, unit_value, market_size, rival_logs, rival_counts, active, active_count, stock, intensity, months,
                discounts, annuity):
    """Earnings of a seller asking `price` against the rivals listed in `active[:active_count]` (`rival_logs`: the
    logarithm of each rival's ask)."""
    others = 0.0
    log_price = numpy.log(price)
    for place in range(active_count):
        rival = active[place]
        others += rival_counts[rival] * numpy.exp(-intensity * (rival_logs[rival] - log_price))
    share = 1.0 / (1.0 + others)
    return expected_earnings(price, unit_value, market_size * share, stock, months, discounts, annuity)


@njit(error_model="numpy")
def best_prices(rival_asks, rival_counts, own, current, unit_value, market_size, stock, floor, ceiling, intensity,
                grid_count, grid_start, grid_step, months, discount_rate):
    """For each seller i (position `own[i]` in the market's arrays; -1 for none): the price on the grid around its
    current price, kept between floor and ceiling, that earns most; a tie keeps the current price. `rival_counts` is
    zero for a seller that is no rival (nothing to sell, no ask)."""
    chosen = numpy.zeros(len(own))
    discounts = numpy.zeros(months)
    for month in range(months):
        discounts[month] = (1.0 + discount_rate) ** month
    annuity = 0.0
    for month in range(months):
        annuity += 1.0 / discounts[month]
    rival_logs = numpy.zeros(len(rival_asks))
    for rival in range(len(rival_asks)):
        if rival_asks[rival] > 0.0:
            rival_logs[rival] = numpy.log(rival_asks[rival])
    active = numpy.zeros(len(rival_asks), dtype=numpy.int64)
    candidates = numpy.zeros(grid_count)
    for seller in range(len(own)):
        active_count = 0
        for rival in range(len(rival_asks)):
            if rival != own[seller] and rival_counts[rival] > 0.0 and rival_asks[rival] > 0.0:
                active[active_count] = rival
                active_count += 1
        best = current[seller]
        best_earnings = earnings_at(best, unit_value[seller], market_size[seller], rival_logs, rival_counts, active, active_count,
                                    stock[seller], intensity, months, discounts, annuity)
        ordered = True
        for step in range(grid_count):
            price = current[seller] * (grid_start + step * grid_step)
            candidates[step] = min(max(price, floor[seller]), ceiling[seller])
            if step > 0 and candidates[step] < candidates[step - 1]:
                ordered = False
        if not ordered:
            candidates.sort()
        previous = numpy.nan
        for step in range(grid_count):
            candidate = candidates[step]
            if candidate == previous:
                continue
            previous = candidate
            if candidate <= 0.0:
                continue
            earnings = earnings_at(candidate, unit_value[seller], market_size[seller], rival_logs, rival_counts, active, active_count,
                                   stock[seller], intensity, months, discounts, annuity)
            if earnings > best_earnings + 1e-12 * max(abs(best_earnings), 1e-300):
                best, best_earnings = candidate, earnings
        chosen[seller] = best
    return chosen
