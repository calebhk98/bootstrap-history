"""What the state asks of a grown household: `requisition_report`, `office_report`, `military_demand_eligible` and
`confiscation_risk` each read the notice and the rule functions (`levy_shares`, `state_notice_rules`) and pass the household's
protection, dispersal and leverage on. The polity module on plain values."""

QUICK_TOPIC = True

import unittest

from sim.polity import constants
from sim.polity.state import PolitySeat
from sim.tests import polity_host

LINE = constants.STATE_NOTICE_THRESHOLD


def household(notice=0.5, protection=0.0, shares=(0.04, 0.02), civ=None):
    """The polity module with the notice as the one reading every report gates on; `levy_shares` records what it was asked."""
    module = polity_host.build(seat=PolitySeat(protection=protection), civilisation=civ or {})
    asked = []

    def levy_shares(scale, protection=0.0, state=None):
        asked.append((scale, protection))
        return shares
    module.state_notice = lambda: notice
    module.household_scale = lambda: 0.7
    module.levy_shares = levy_shares
    module.group_levy_reasons = lambda: ["a group asks too"]
    module.asked = asked
    return module


class RequisitionReport(unittest.TestCase):
    def test_below_the_notice_line_nothing_is_requisitioned(self):
        self.assertEqual(household(notice=LINE).requisition_report(), (0.0, []))

    def test_above_it_the_share_is_the_levys_requisition_at_the_households_scale_and_protection(self):
        module = household(protection=0.4)
        share, why = module.requisition_report()
        self.assertEqual(share, 0.04)
        self.assertEqual(module.asked, [(0.7, 0.4)])
        self.assertEqual(len(why), 2)   # the protection bargain, then the group's reason
        self.assertEqual(why[-1], "a group asks too")

    def test_with_no_protection_only_the_groups_reasons_are_given(self):
        self.assertEqual(household(protection=0.0).requisition_report()[1], ["a group asks too"])

    def test_a_negative_levy_share_is_no_requisition(self):
        self.assertEqual(household(shares=(-0.01, 0.0)).requisition_report()[0], 0.0)


class OfficeReport(unittest.TestCase):
    def test_below_the_notice_line_there_is_no_office(self):
        self.assertEqual(household(notice=LINE).office_report(), (0.0, None))

    def test_the_share_is_the_levys_office_share_and_protection_does_not_bargain_it(self):
        module = household(protection=0.9, civ={"state_pressure": {"office_name": "the decurionate"}})
        self.assertEqual(module.office_report(), (0.02, "the decurionate"))
        self.assertEqual(module.asked, [(0.7, 0.0)])

    def test_a_civilisation_that_names_no_office_gets_a_generic_one(self):
        self.assertEqual(household().office_report()[1], "a civic office")


class MilitaryDemandEligible(unittest.TestCase):
    def module(self, leverage, notice):
        module = polity_host.build()
        module.military_leverage = lambda: leverage
        module.state_notice = lambda: notice
        return module

    def test_it_needs_both_leverage_at_the_floor_and_notice_past_the_military_line(self):
        floor, line = constants.MIL_LEVERAGE_FLOOR_FOR_DEMAND, constants.STATE_NOTICE_THRESHOLD_MILITARY
        self.assertTrue(self.module(floor, line + 0.1).military_demand_eligible())
        self.assertFalse(self.module(floor / 2, line + 0.1).military_demand_eligible())
        self.assertFalse(self.module(0.5, line).military_demand_eligible())


class ConfiscationRisk(unittest.TestCase):
    def module(self, over, protection=0.0, dispersal=None, leverage=0.0):
        module = polity_host.build(seat=PolitySeat(protection=protection),
                                   effect_best=lambda effect: None if dispersal is None else (None, {"flat": dispersal}))
        module._notice_over = lambda threshold: over
        module.military_leverage = lambda: leverage
        return module

    def test_short_of_the_confiscation_line_there_is_no_risk(self):
        self.assertEqual(self.module(0.0).confiscation_risk(), (0.0, []))

    def test_unprotected_the_chance_is_the_maximum_rate_scaled_by_the_distance_past_the_line(self):
        chance, held = self.module(0.5).confiscation_risk()
        self.assertAlmostEqual(chance, 0.5 * constants.CONFISCATION_MAX_RATE)
        self.assertEqual(held, [])

    def test_dispersal_held_cuts_the_chance_and_is_named(self):
        chance, held = self.module(0.5, dispersal=0.5).confiscation_risk()
        self.assertAlmostEqual(chance, 0.5 * constants.CONFISCATION_MAX_RATE * 0.5)
        self.assertEqual(held, [constants.CONFISCATION_PROTECTION_LABELS[1]])

    def test_protection_and_usefulness_are_each_named_in_the_order_of_the_labels(self):
        _chance, held = self.module(0.5, protection=0.5, leverage=0.5).confiscation_risk()
        self.assertEqual(held, [constants.CONFISCATION_PROTECTION_LABELS[0], constants.CONFISCATION_PROTECTION_LABELS[2]])


if __name__ == "__main__":
    unittest.main()
