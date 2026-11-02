"""Complaint 556: the labour core holds every trade the society's need names, and Rules called on built inputs: trade_seed.seed_hours, labour_state.seeded_hours with the opening placing the people."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import labour_state, workforce_settle
from sim.labour import trade_seed
from sim.labour.market import aptitude, opening, records, trades
from sim.labour.market.records import MarketState

HOURS = 2000.0
REGISTRY = {
    "labourer": {"family": "toil", "training_years": 0, "fallback": True},
    "farmer": {"family": "toil", "training_years": 1},
    "carter": {"family": "toil", "training_years": 1},
    "porter": {"family": "toil", "training_years": 0},
    "smith": {"family": "craft", "training_years": 3},
}
SHARES = {"smith": 0.20, "carter": 0.02, "porter": 0.30}


class SeedHoursTests(unittest.TestCase):

    def test_a_trade_no_run_staffs_gets_hours_in_the_ratio_of_its_share_to_a_staffed_trades(self):
        seeds = trade_seed.seed_hours(SHARES, {"smith": 400 * HOURS}, REGISTRY)
        self.assertAlmostEqual(seeds["carter"], 400 * HOURS * 0.02 / 0.20)
        self.assertAlmostEqual(seeds["porter"], 400 * HOURS * 0.30 / 0.20)

    def test_porters_and_carters_get_different_hours_because_their_work_differs(self):
        seeds = trade_seed.seed_hours(SHARES, {"smith": 400 * HOURS}, REGISTRY)
        self.assertNotEqual(seeds["carter"], seeds["porter"])

    def test_a_staffed_trade_is_not_seeded_and_a_left_out_trade_is_not_either(self):
        seeds = trade_seed.seed_hours(SHARES, {"smith": 400 * HOURS}, REGISTRY, left_out=("porter",))
        self.assertNotIn("smith", seeds)
        self.assertNotIn("porter", seeds)

    def test_a_trade_with_no_share_is_not_seeded(self):
        self.assertNotIn("farmer", trade_seed.seed_hours(SHARES, {"smith": 400 * HOURS}, REGISTRY))

    def test_with_no_staffed_trade_to_scale_from_nothing_is_seeded(self):
        self.assertEqual(trade_seed.seed_hours(SHARES, {}, REGISTRY), {})
        self.assertEqual(trade_seed.seed_hours(SHARES, {"farmer": 9 * HOURS}, REGISTRY), {})


class SeedBoundedByHirersTests(unittest.TestCase):
    """Complaint 556: a trade's seed is bounded by the work its hirers will give it (producers' plans and last
    year's hires, the state's bids), and people beyond it go to the fallback trade."""
    SEEDS = {"merchant": 500 * HOURS, "porter": 40 * HOURS}

    def test_a_trade_with_a_need_share_and_no_hirer_is_seeded_no_hours(self):
        self.assertEqual(trade_seed.bound_by_hirers(self.SEEDS, {}), {})

    def test_a_trade_is_seeded_no_more_than_its_hirers_hours(self):
        bounded = trade_seed.bound_by_hirers(self.SEEDS, {"merchant": 30 * HOURS})
        self.assertEqual(bounded, {"merchant": 30 * HOURS})

    def test_a_trade_whose_hirers_bid_more_keeps_its_need_share_seed(self):
        bounded = trade_seed.bound_by_hirers(self.SEEDS, {"porter": 90 * HOURS})
        self.assertEqual(bounded, {"porter": 40 * HOURS})

    def test_the_kept_hours_of_a_seeded_trade_are_its_hirers_hours_when_they_are_below_the_seed(self):
        wanted = {("vale", "merchant"): 20 * HOURS}
        state_bids = {("vale", "merchant"): 5 * HOURS}
        kept = workforce_settle.hours_kept({"vale": self.SEEDS}, wanted, state_bids, {})
        self.assertEqual(kept[("vale", "merchant")], 25 * HOURS)
        self.assertNotIn(("vale", "porter"), kept)

    def test_a_trade_whose_only_hirer_is_planned_carriage_keeps_the_hours_carriage_plans_for_it(self):
        carriage_plans = {("vale", "porter"): 25 * HOURS}
        kept = workforce_settle.hours_kept({"vale": self.SEEDS}, {}, {}, carriage_plans)
        self.assertEqual(kept[("vale", "porter")], 25 * HOURS)
        self.assertNotIn(("vale", "merchant"), kept)

    def test_carriage_plans_add_to_the_producers_and_the_states_hours_up_to_the_seed(self):
        carriage_plans = {("vale", "porter"): 30 * HOURS}
        kept = workforce_settle.hours_kept({"vale": self.SEEDS}, {("vale", "porter"): 5 * HOURS},
                                           {("vale", "porter"): 20 * HOURS}, carriage_plans)
        self.assertEqual(kept[("vale", "porter")], 40 * HOURS)

    def test_the_hours_merchants_plan_for_carriage_are_summed_by_area_and_trade(self):
        bids = [SimpleNamespace(area="vale", trade="porter", hours=10 * HOURS),
                SimpleNamespace(area="vale", trade="porter", hours=5 * HOURS),
                SimpleNamespace(area="dale", trade="porter", hours=2 * HOURS)]
        self.assertEqual(workforce_settle.hours_by_area_and_trade(bids),
                         {("vale", "porter"): 15 * HOURS, ("dale", "porter"): 2 * HOURS})

    def test_the_people_a_seed_no_hirer_wants_go_to_the_fallback_trade(self):
        state = MarketState()
        state.workers = {"vale": {"merchant": [300.0, 200.0], "labourer": [100.0, 100.0]}}
        state.trainees = {}
        kept = workforce_settle.hours_kept({"vale": self.SEEDS}, {("vale", "merchant"): 50 * HOURS}, {}, {})
        workforce_settle.trim_people(state, kept, "labourer", HOURS)
        self.assertAlmostEqual(sum(state.workers["vale"]["merchant"]), 50.0)
        self.assertAlmostEqual(sum(state.workers["vale"]["labourer"]), 650.0)


class OpeningHoldsSeededTradesTests(unittest.TestCase):

    def test_the_core_holds_carters_and_porters_in_proportion_to_their_work(self):
        setup = SimpleNamespace(need_share_by_trade=SHARES, trades=trades.trade_specs(REGISTRY),
                                recipes={}, land_per_run={})
        needed = {"vale": {"smith": 400 * HOURS}}
        seeded = labour_state.seeded_hours(setup, needed)
        needed["vale"].update(seeded["vale"])
        state = opening.opening_state(setup.trades, {"vale": 10000.0}, needed, HOURS, "farmer")
        people = labour_state.people_by_trade(state, "vale")
        self.assertAlmostEqual(people["carter"], 40.0)
        self.assertAlmostEqual(people["porter"], 600.0)
        self.assertAlmostEqual(records.people_in(state), 10000.0)
        self.assertGreater(people["porter"], 10.0 * people["carter"])


if __name__ == "__main__":
    unittest.main()
