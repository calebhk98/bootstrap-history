"""KeptAnswers works each figure of a country's economy out once and hands the kept answer on; a dict comes back as a
copy; anything else the economy offers passes through."""

QUICK_TOPIC = True

import unittest

from sim.agents.country_part import KeptAnswers


class Steps:
    years_stepped = 0


class CountingEconomy:
    def __init__(self):
        self.calls = []
        self._economy = Steps()

    def pay_per_person_year(self, trade):
        self.calls.append(("pay", trade))
        return 10.0 + len(trade)

    def need_floor_costs_per_person_year(self):
        self.calls.append(("floors",))
        return {"food": 3.0}

    def coin_regime(self):
        self.calls.append(("regime",))
        return "metal"


class KeptAnswersTest(unittest.TestCase):
    def test_each_figure_and_argument_is_worked_out_once(self):
        economy = CountingEconomy()
        kept = KeptAnswers(economy)
        self.assertEqual(kept.pay_per_person_year("smith"), 15.0)
        self.assertEqual(kept.pay_per_person_year("smith"), 15.0)
        self.assertEqual(kept.pay_per_person_year("mason"), 15.0)
        self.assertEqual(economy.calls, [("pay", "smith"), ("pay", "mason")])

    def test_a_dict_answer_is_a_copy(self):
        kept = KeptAnswers(CountingEconomy())
        kept.need_floor_costs_per_person_year()["food"] = 99.0
        self.assertEqual(kept.need_floor_costs_per_person_year(), {"food": 3.0})

    def test_other_questions_pass_through_unkept(self):
        economy = CountingEconomy()
        kept = KeptAnswers(economy)
        kept.coin_regime()
        kept.coin_regime()
        self.assertEqual(economy.calls, [("regime",), ("regime",)])

    def test_answers_are_dropped_once_the_economy_has_stepped(self):
        economy = CountingEconomy()
        kept = KeptAnswers(economy)
        kept.pay_per_person_year("smith")
        economy._economy.years_stepped += 1
        kept.pay_per_person_year("smith")
        self.assertEqual(economy.calls, [("pay", "smith"), ("pay", "smith")])


if __name__ == "__main__":
    unittest.main()
