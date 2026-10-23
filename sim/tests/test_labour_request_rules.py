"""Complaint 640: what a request to teach, dismiss or commission must satisfy (`labour.request_rules`), on built inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.labour.request_rules import (commission_request_refusal, fire_refusal, teaching_fee, teaching_hours_refusal,
                                      train_request_refusal)
from sim.refusal import cause_of


def ask(trade_known=True, trade="machinist", count=2, source="smith", absent=False):
    asked = []

    def find_source():
        asked.append(True)
        return source

    result = train_request_refusal(trade_known, trade, count, find_source, lambda found: absent)
    return result, asked


class TrainRequest(unittest.TestCase):
    def test_a_good_request_names_its_source_lowered_and_has_no_refusal(self):
        (source, refusal), _asked = ask(source=" Smith ")
        self.assertEqual((source, refusal), ("smith", None))

    def test_an_unknown_trade_is_refused_before_anything_else(self):
        (source, refusal), asked = ask(trade_known=False, count=-1)
        self.assertEqual(cause_of(refusal), "no_such_trade")
        self.assertIsNone(source)
        self.assertEqual(asked, [])

    def test_a_count_that_is_not_positive_is_refused(self):
        self.assertEqual(cause_of(ask(count=0)[0][1]), "count_not_positive")
        self.assertEqual(cause_of(ask(count=-3)[0][1]), "count_not_positive")

    def test_people_are_whole_so_a_fraction_is_refused_and_a_whole_float_is_not(self):
        self.assertEqual(cause_of(ask(count=2.5)[0][1]), "count_not_whole")
        self.assertIsNone(ask(count=3.0)[0][1])
        self.assertIsNone(ask(count=3.0000001)[0][1])

    def test_the_source_is_looked_for_only_once_the_count_passes(self):
        self.assertEqual(ask(count=0)[1], [])
        self.assertEqual(ask(count=2)[1], [True])

    def test_no_source_trade_is_refused(self):
        self.assertEqual(cause_of(ask(source=None)[0][1]), "no_source_trade")
        self.assertEqual(cause_of(ask(source="  ")[0][1]), "no_source_trade")

    def test_a_source_trade_that_does_not_exist_here_is_refused(self):
        self.assertEqual(cause_of(ask(absent=True)[0][1]), "source_trade_absent")


class TeachingCosts(unittest.TestCase):
    def test_teaching_that_takes_more_than_the_uncommitted_hours_is_refused_with_the_figures(self):
        refusal = teaching_hours_refusal(500.0, 400.0, 3, "machinist")
        self.assertEqual(cause_of(refusal), "founder_hours_short")
        self.assertIsNone(teaching_hours_refusal(400.0, 400.0, 3, "machinist"))

    def test_the_fee_keeps_the_pupils_at_the_source_wage_for_the_years_kept(self):
        self.assertAlmostEqual(teaching_fee(4, 100.0, 1.5, False, 0.0, 2000.0), 600.0)

    def test_an_outside_teacher_is_paid_for_his_hours_at_the_same_wage(self):
        own = teaching_fee(4, 100.0, 1.5, False, 1000.0, 2000.0)
        taught = teaching_fee(4, 100.0, 1.5, True, 1000.0, 2000.0)
        self.assertAlmostEqual(taught - own, 1000.0 * 100.0 / 2000.0)


class Fire(unittest.TestCase):
    def test_dismissing_a_trade_nobody_holds_or_is_learning_is_refused(self):
        self.assertEqual(cause_of(fire_refusal("smith", 0, 0)), "nobody_to_dismiss")

    def test_employed_people_or_apprentices_are_enough_to_dismiss(self):
        self.assertIsNone(fire_refusal("smith", 2, 0))
        self.assertIsNone(fire_refusal("smith", 0, 3))


class Commission(unittest.TestCase):
    def refusal(self, **overrides):
        inputs = dict(trade_known=True, trade="smith", hours=100.0, trade_exists=True, trade_note="", spare_hours=500.0)
        inputs.update(overrides)
        return commission_request_refusal(**inputs)

    def test_a_job_the_trade_can_spare_is_not_refused(self):
        self.assertIsNone(self.refusal())
        self.assertIsNone(self.refusal(hours=500.0))

    def test_the_refusals_come_in_order(self):
        self.assertEqual(cause_of(self.refusal(trade_known=False, hours=-1.0)), "no_such_trade")
        self.assertEqual(cause_of(self.refusal(hours=0.0, trade_exists=False)), "hours_not_positive")
        self.assertEqual(cause_of(self.refusal(trade_exists=False, hours=900.0)), "trade_absent")
        self.assertEqual(cause_of(self.refusal(hours=500.01)), "hours_over_spare")

    def test_a_trade_with_nothing_spare_is_refused_whatever_is_asked(self):
        self.assertEqual(cause_of(self.refusal(spare_hours=-20.0, hours=1.0)), "hours_over_spare")


if __name__ == "__main__":
    unittest.main()
