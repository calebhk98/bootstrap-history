"""The labour core's trade specs, ability bands and training pipeline, on plain records with invented
trade ids: a hard trade is finished mostly by the able, a school adds workers only after the training
years, a trade nobody practises cannot teach itself, and nobody is lost on the way."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import aptitude, records, trades, training

REGISTRY = {
    "digger": {"family": "toil", "training_years": 0},
    "carver": {"family": "craft", "training_years": 3},
    "healer": {"family": "lore", "training_years": 6, "difficulty": 1.0},
    "scrivener": {"family": "lore"},
}


def inputs(**extra):
    base = dict(trades=trades.trade_specs(REGISTRY), bids=[], subsistence_per_worker_year={"vale": 10.0},
                hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0)
    base.update(extra)
    return records.YearInputs(**base)


class TradeSpecTests(unittest.TestCase):
    def test_the_fallback_is_the_trade_needing_no_training(self):
        self.assertEqual(trades.fallback_trades(trades.trade_specs(REGISTRY)), ["digger"])

    def test_a_flag_in_the_data_overrides_the_fewest_years_rule(self):
        registry = dict(REGISTRY, carver={"family": "craft", "training_years": 3, "fallback": True})
        self.assertEqual(trades.fallback_trades(trades.trade_specs(registry)), ["carver"])

    def test_a_trade_stating_no_years_takes_its_familys_median(self):
        self.assertEqual(trades.trade_specs(REGISTRY)["scrivener"].training_years, 6.0)

    def test_a_stated_difficulty_is_kept(self):
        self.assertEqual(trades.trade_specs(REGISTRY)["healer"].difficulty, 1.0)


class AptitudeTests(unittest.TestCase):
    def test_bands_are_symmetric_and_ordered(self):
        abilities = aptitude.band_abilities()
        self.assertEqual(abilities, sorted(abilities))
        self.assertAlmostEqual(sum(abilities), 0.0)

    def test_a_hard_trade_is_finished_mostly_by_the_able(self):
        chances = aptitude.completion_by_band(1.0)
        self.assertEqual(chances, sorted(chances))
        self.assertLess(chances[0], 0.05)
        self.assertGreater(chances[-1], 0.5)

    def test_completion_never_overflows(self):
        self.assertEqual(aptitude.completion_chance(-1e6, 1e6), 0.0)
        self.assertEqual(aptitude.completion_chance(1e6, -1e6), 1.0)


class TrainingTests(unittest.TestCase):
    def test_a_trade_nobody_practises_and_no_school_teaches_takes_nobody(self):
        state = records.MarketState()
        left = training.enrol(state, inputs(), "vale", "carver", aptitude.split_evenly(10.0))
        self.assertAlmostEqual(sum(left), 10.0)
        self.assertEqual(state.trainees, {})

    def test_a_school_trains_workers_only_after_the_training_years(self):
        school = records.School(owner="founder", trade="carver", area="vale", seats=50.0)
        year_inputs = inputs(schools=[school])
        state = records.MarketState()
        left = training.enrol(state, year_inputs, "vale", "carver", aptitude.split_evenly(50.0))
        self.assertAlmostEqual(sum(left), 0.0)
        for _year in range(2):
            training.advance(state, year_inputs, records.YearReport())
            self.assertNotIn("carver", state.workers.get("vale", {}))
        training.advance(state, year_inputs, records.YearReport())
        self.assertGreater(sum(state.workers["vale"]["carver"]), 0.0)

    def test_those_who_do_not_finish_fall_back_and_nobody_is_lost(self):
        school = records.School(owner="guild", trade="healer", area="vale", seats=100.0)
        year_inputs = inputs(schools=[school])
        state = records.MarketState()
        training.enrol(state, year_inputs, "vale", "healer", aptitude.split_evenly(100.0))
        for _year in range(6):
            training.advance(state, year_inputs, records.YearReport())
        healers = sum(state.workers["vale"]["healer"])
        diggers = sum(state.workers["vale"]["digger"])
        self.assertAlmostEqual(healers + diggers, 100.0)
        self.assertLess(healers, 50.0)
        bands = state.workers["vale"]["healer"]
        self.assertGreater(bands[-1], bands[0] * 10)

    def test_a_better_school_graduates_more(self):
        def graduates(bonus):
            school = records.School(owner="guild", trade="healer", area="vale", seats=100.0, completion_bonus=bonus)
            year_inputs = inputs(schools=[school])
            state = records.MarketState()
            training.enrol(state, year_inputs, "vale", "healer", aptitude.split_evenly(100.0))
            for _year in range(6):
                training.advance(state, year_inputs, records.YearReport())
            return sum(state.workers["vale"]["healer"])
        self.assertGreater(graduates(0.5), graduates(0.0))

    def test_incumbents_teach_apprentices(self):
        state = records.MarketState(workers={"vale": {"carver": aptitude.split_evenly(100.0)}})
        places = training.open_places(state, inputs(), "vale", "carver")
        self.assertGreater(places, 0.0)
        self.assertLess(places, 100.0)

    def test_attrition_takes_the_same_share_of_everyone(self):
        state = records.MarketState(workers={"vale": {"digger": aptitude.split_evenly(100.0)}},
                                    trainees={"vale": {"carver": [[2.0, aptitude.split_evenly(10.0), 0.0]]}})
        report = records.YearReport()
        training.apply_attrition(state, inputs(attrition_share={"vale": 0.1}), report)
        self.assertAlmostEqual(records.people_in(state), 99.0)
        self.assertAlmostEqual(report.left_work["vale"], 11.0)

    def test_the_state_round_trips_through_plain_data(self):
        state = records.MarketState(workers={"vale": {"digger": aptitude.split_evenly(3.0)}},
                                    wages={"vale": {"digger": 0.5}})
        self.assertEqual(records.from_plain(records.to_plain(state)), state)


if __name__ == "__main__":
    unittest.main()
