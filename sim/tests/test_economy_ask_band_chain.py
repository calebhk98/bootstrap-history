"""Complaint 473 (cost-plus ask against Caiani et al. 2016 eq 3.6-3.7, a markup on unit cost): the band above cost marks up
what a seller adds, and inputs it buys pass through at their cost, so a chain of makers' ceilings grows by a sum and not
by the band to the power of the stages."""

QUICK_TOPIC = True

import unittest

from sim.economy import ask_adjust

MULTIPLE = ask_adjust.ASK_BAND_CEILING
VALUE_ADDED = 1.0       # what each stage adds in labour and plant, per unit of its output


def chain_ceilings(stages, input_share_applies):
    """Each stage buys the one before at that stage's ceiling and adds VALUE_ADDED; returns the ceilings."""
    ceilings, input_price = [], 0.0
    for _stage in range(stages):
        cost = input_price + VALUE_ADDED
        share = input_price / cost if input_share_applies else 0.0
        ceilings.append(ask_adjust.band_edge(cost, share, MULTIPLE))
        input_price = ceilings[-1]
    return ceilings


class BandOnChainTests(unittest.TestCase):
    def test_a_band_on_the_whole_cost_compounds_along_the_chain(self):
        # the shape that runs prices away: each stage marks up inputs already marked up
        first, second, third = chain_ceilings(3, input_share_applies=False)
        self.assertAlmostEqual(third / first, MULTIPLE ** 2 + MULTIPLE + 1.0)
        self.assertGreater(third, 10.0 * first)

    def test_the_band_on_what_a_stage_adds_grows_a_chain_by_a_sum(self):
        ceilings = chain_ceilings(3, input_share_applies=True)
        for stage, ceiling in enumerate(ceilings, start=1):
            self.assertAlmostEqual(ceiling, MULTIPLE * VALUE_ADDED * stage)
        self.assertLess(ceilings[2], chain_ceilings(3, input_share_applies=False)[2])

    def test_a_maker_with_no_bought_inputs_keeps_the_whole_band(self):
        self.assertAlmostEqual(ask_adjust.band_edge(4.0, 0.0), 4.0 * MULTIPLE)

    def test_a_maker_that_only_resells_inputs_is_not_marked_up_at_all(self):
        self.assertAlmostEqual(ask_adjust.band_edge(4.0, 1.0), 4.0)

    def test_a_sold_out_seller_stops_at_the_edge_of_the_band_on_what_it_adds(self):
        cost, share = 4.0, 0.75
        ask = cost
        for _year in range(500):
            ask = ask_adjust.adjusted_within_band(ask, cost, 0.0, 1.0, MULTIPLE, share)
        self.assertAlmostEqual(ask, ask_adjust.band_edge(cost, share, MULTIPLE))
        self.assertLess(ask, MULTIPLE * cost)


if __name__ == "__main__":
    unittest.main()
