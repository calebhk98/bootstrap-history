"""The arithmetic of real output (real_output.py) on plain values: the traded measure against the baseline year, and
the lines a society's output is the sum of. No game is read here."""


def traded_measure(basket, baseline, volumes):
    """({good: units traded last year}, scale) over the opening basket's goods that have a baseline. `basket` is
    {"prices", "units"}; the scale carries the baseline year onto the basket's value, so output starts at it. With no
    baseline (no year has closed) the basket's own units stand and the scale is one."""
    if not baseline:
        return dict(basket["units"]), 1.0
    goods = [good for good in basket["units"] if baseline.get(good, 0.0) > 0.0]
    then = sum(baseline[good] * basket["prices"][good] for good in goods)
    opening = sum(basket["units"][good] * basket["prices"][good] for good in goods)
    return {good: volumes.get(good, 0.0) for good in goods}, (opening / then if then > 0.0 else 0.0)


def output_lines(basket, traded, scale, introduction_prices, new_goods, volumes):
    """[(good, units a year sold now, price in labour hours)]: the traded goods at the opening prices, then each new
    good the economy trades at the price it was first offered at."""
    lines = [(good, units * scale, basket["prices"][good]) for good, units in traded.items()]
    for good in new_goods:
        if good in introduction_prices and volumes.get(good, 0.0) > 0.0:
            lines.append((good, volumes[good], introduction_prices[good]))
    return lines


def share_producing(working_age, under_arms):
    """The share of working people not under arms. TEMPORARY HEURISTIC (CLAUDE.md 4.4): the market's quantities do not
    yet fall when people are drawn off to arms, so this share scales them. One when there are no working people."""
    return max(0.0, working_age - under_arms) / working_age if working_age > 0.0 else 1.0
