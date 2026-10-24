"""Complaint 651: the market wage's year-on-year step has a gain below one against the wage it reacts to (a whole economy's
wage not saw-toothing is measured by `spin-up-trace`, see the complaint)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.labour.market.records import Bid

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


if __name__ == "__main__":
    unittest.main()
