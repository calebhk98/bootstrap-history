"""The `education` screen's enrolment (Complaint 94): each running school shows its share of the schooling flow, its pupils
made literate next year are that share of the whole society's literacy gain, and the limit on literacy is named by an
enumerated field. `screen_education._enrolment` and `_limited_by` are called on a stub society, and the screen's
rendering on a built reply."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.ui.proto import screen_education
from sim.ui.proto.render_screens_world import render_education
from sim.tests.ui_stand_in import Game
from sim.tests.ui_stand_in import FactViews

POPULATION = 1_000_000.0


class StubSociety(FactViews):
    """What the enrolment reads of a game: today's literacy, next year's, the population and the schooling flow."""

    def __init__(self, today=0.20, next_year=0.21, effective_flow=1.0):
        self.population = Game(total=POPULATION)
        self._today, self._next_year, self._flow = today, next_year, effective_flow

    def literacy(self, name):
        return self._today

    def literacy_next_year(self):
        return {"literacy_general": self._next_year}

    def effective_schooling_flow(self):
        return self._flow


def school(flow, name="school"):
    return {"id": name, "name": name, "built": True, "running": flow > 0, "flow_added": flow}


class EnrolmentTests(unittest.TestCase):
    def enrolled(self, flows, **society):
        rows = [school(flow, "school %d" % number) for number, flow in enumerate(flows)]
        screen_education._enrolment(StubSociety(**society), rows)
        return rows

    def test_shares_of_the_running_schools_sum_to_one(self):
        rows = self.enrolled([1.0, 3.0, 4.0])
        self.assertAlmostEqual(sum(row["share_of_schooling_flow"] for row in rows), 1.0, places=3)

    def test_each_share_is_the_schools_flow_over_the_total(self):
        rows = self.enrolled([1.0, 3.0, 4.0])
        for row, expected in zip(rows, (1 / 8, 3 / 8, 4 / 8)):
            self.assertAlmostEqual(row["share_of_schooling_flow"], expected, places=3)

    def test_pupils_made_literate_sum_to_the_whole_societys_gain(self):
        rows = self.enrolled([1.0, 3.0, 4.0], today=0.20, next_year=0.21)
        gain = 0.01 * POPULATION
        self.assertAlmostEqual(sum(row["people_made_literate_next_year"] for row in rows), gain, delta=1.0 + 0.01 * gain)

    def test_a_bigger_school_makes_more_pupils_literate(self):
        small, big = self.enrolled([1.0, 3.0])
        self.assertLess(small["people_made_literate_next_year"], big["people_made_literate_next_year"])

    def test_a_school_that_is_not_running_has_no_share_and_no_pupils(self):
        idle, running = self.enrolled([0.0, 2.0])
        self.assertEqual(idle["share_of_schooling_flow"], 0.0)
        self.assertEqual(idle["people_made_literate_next_year"], 0.0)
        self.assertAlmostEqual(running["share_of_schooling_flow"], 1.0)

    def test_with_no_school_running_nobody_is_credited(self):
        rows = self.enrolled([0.0, 0.0])
        self.assertTrue(all(row["share_of_schooling_flow"] == 0.0 for row in rows))


class LiteracyLimitTests(unittest.TestCase):
    def test_with_no_school_running_literacy_is_limited_by_the_missing_schools(self):
        self.assertEqual(screen_education._limited_by(StubSociety(effective_flow=0.0), 0.5), "no school running")

    def test_near_the_ceiling_it_is_limited_by_the_ceiling(self):
        self.assertEqual(screen_education._limited_by(StubSociety(), 0.99), "the ceiling (farm share and unschooled share)")

    def test_otherwise_it_is_limited_by_the_flow(self):
        self.assertEqual(screen_education._limited_by(StubSociety(), 0.5), "the schooling flow")


class RenderTests(unittest.TestCase):
    def reply(self):
        schools = [school(2.0, "grammar school")]
        screen_education._enrolment(StubSociety(), schools)
        literacy = {kind + suffix: 0.2 for kind in ("general", "elite")
                    for suffix in ("", "_ceiling", "_next_year", "_share")}
        literacy.update({"share_of_ceiling_general": 0.5, "share_of_ceiling_elite": 0.5})
        return {"literacy": literacy, "schooling_flow": 2.0, "effective_schooling_flow": 2.0, "printing_adopted": 0.0,
                "farm_share_of_hours": 0.5, "schools": schools, "literate_trades": [], "trainees": [], "not_held": []}

    def test_the_screen_prints_the_enrolment_column(self):
        self.assertIn("PUPILS", render_education(self.reply()).upper())  # presentation: the column's header word


if __name__ == "__main__":
    unittest.main()
