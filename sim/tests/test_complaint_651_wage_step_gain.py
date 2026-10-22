"""Complaint 651: the market wage's year-on-year step has a gain below one against the wage it reacts to, and the
small economy's labourer wage does not saw-tooth under a constant setting."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.labour.market.records import Bid
from sim.tests import economy_fixture as fixture

RESERVATION = 1.0
OFFERED = 1000.0
WORTH = 10.0       # an employer's maximum wage, far above the reservation


def bid(hours):
    return Bid("employer", "digger", "vale", hours, WORTH, 0.0)


def next_wage(last, wanted):
    return clearing.market_wage(last, RESERVATION, OFFERED, [bid(wanted)])


class StepAroundTheMargin(unittest.TestCase):
    def test_a_sliver_of_slack_barely_cuts_the_wage(self):
        last = 5.0
        cut = last - next_wage(last, OFFERED * 0.99)
        self.assertLess(cut, 0.05 * (last - RESERVATION))

    def test_a_sliver_of_scarcity_barely_raises_the_wage(self):
        last = 2.0
        raise_ = next_wage(last, OFFERED * 1.01) - last
        self.assertLess(raise_, 0.05 * (WORTH - last))

    def test_the_step_is_continuous_across_wanted_equals_offered(self):
        last = 5.0
        below, above = next_wage(last, OFFERED * 0.999), next_wage(last, OFFERED * 1.001)
        self.assertLess(abs(above - below), 0.02 * last)

    def test_gain_of_next_wage_on_last_wage_is_below_one_when_demand_follows_the_wage(self):
        # employers want fewer hours the higher last year's wage: wanted = OFFERED * (target / last)
        for last in (1.5, 3.0, 5.0, 8.0):
            step = 1e-3 * last
            gain = (next_wage(last + step, OFFERED * 4.0 / (last + step)) -
                    next_wage(last, OFFERED * 4.0 / last)) / step
            self.assertLess(abs(gain), 1.0, last)


class SmallEconomy(unittest.TestCase):
    # Complaint 473: the staple's producers run a period-two cobweb of adaptive expectations; the hours households offer follow
    # its price through the leisure anchor and the wage step follows those hours. It showed once demand stopped running far
    # above the offer (641's held rate where no loan clears). The wage step itself responds correctly (Complaint 641, trace).
    @unittest.expectedFailure
    def test_labourer_wage_does_not_sawtooth(self):
        series = {}
        original = clearing.clear_one

        def recording(state, inputs, trade, area, bids, import_costs=None):
            result = original(state, inputs, trade, area, bids, import_costs)
            if trade == fixture.LABOURER:
                series.setdefault(area, []).append(result.wage)
            return result

        clearing.clear_one = recording
        try:
            fixture.run(fixture.small_setup(), years=70)
        finally:
            clearing.clear_one = original
        self.assertTrue(series)
        for area, wages in sorted(series.items()):
            changes = [after - before for before, after in zip(wages, wages[1:])][12:]
            flips = sum(1 for before, after in zip(changes, changes[1:]) if before * after < 0.0)
            self.assertLess(flips, 0.15 * len(changes), (area, flips))
            falls = [change / before for change, before in zip(changes, wages[12:]) if change < 0.0]
            self.assertLess(min(falls, default=0.0) * -1.0, 0.15, area)


if __name__ == "__main__":
    unittest.main()
