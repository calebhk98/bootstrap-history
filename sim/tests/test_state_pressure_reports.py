"""What the state asks of a grown household: `requisition_report`, `office_report`, `military_demand_eligible` and
`confiscation_risk` each read the notice and the rule functions (`levy_shares`, `state_notice_rules`) and pass the household's
protection, dispersal and leverage on. Each is called on a stand-in `self` carrying only what it reads."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.engine.society_state_pressure import StatePressureMixin as Mixin

LINE = 0.05


def household(notice=0.5, protection=0.0, shares=(0.04, 0.02), civ=None, **more):
    """A stand-in game: notice is the one reading every report gates on; `levy_shares` records what it was asked."""
    asked = []

    def levy_shares(scale, protection=0.0, state=None):
        asked.append((scale, protection))
        return shares
    return SimpleNamespace(
        state_notice=lambda: notice, STATE_NOTICE_THRESHOLD=LINE, household_scale=lambda: 0.7,
        state=SimpleNamespace(household=SimpleNamespace(protection=protection)), levy_shares=levy_shares, asked=asked,
        group_levy_reasons=lambda: ["a group asks too"], civ=civ or {}, **more)


class RequisitionReport(unittest.TestCase):
    def test_below_the_notice_line_nothing_is_requisitioned(self):
        self.assertEqual(Mixin.requisition_report(household(notice=LINE)), (0.0, []))

    def test_above_it_the_share_is_the_levys_requisition_at_the_households_scale_and_protection(self):
        stand_in = household(protection=0.4)
        share, why = Mixin.requisition_report(stand_in)
        self.assertEqual(share, 0.04)
        self.assertEqual(stand_in.asked, [(0.7, 0.4)])
        self.assertEqual(len(why), 2)   # the protection bargain, then the group's reason
        self.assertEqual(why[-1], "a group asks too")

    def test_with_no_protection_only_the_groups_reasons_are_given(self):
        self.assertEqual(Mixin.requisition_report(household(protection=0.0))[1], ["a group asks too"])

    def test_a_negative_levy_share_is_no_requisition(self):
        self.assertEqual(Mixin.requisition_report(household(shares=(-0.01, 0.0)))[0], 0.0)


class OfficeReport(unittest.TestCase):
    def test_below_the_notice_line_there_is_no_office(self):
        self.assertEqual(Mixin.office_report(household(notice=LINE)), (0.0, None))

    def test_the_share_is_the_levys_office_share_and_protection_does_not_bargain_it(self):
        stand_in = household(protection=0.9, civ={"state_pressure": {"office_name": "the decurionate"}})
        self.assertEqual(Mixin.office_report(stand_in), (0.02, "the decurionate"))
        self.assertEqual(stand_in.asked, [(0.7, 0.0)])

    def test_a_civilisation_that_names_no_office_gets_a_generic_one(self):
        self.assertEqual(Mixin.office_report(household())[1], "a civic office")


class MilitaryDemandEligible(unittest.TestCase):
    def stand_in(self, leverage, notice):
        return SimpleNamespace(military_leverage=lambda: leverage, MIL_LEVERAGE_FLOOR_FOR_DEMAND=0.1, state_notice=lambda: notice,
                               STATE_NOTICE_THRESHOLD_MILITARY=0.2)

    def test_it_needs_both_leverage_at_the_floor_and_notice_past_the_military_line(self):
        self.assertTrue(Mixin.military_demand_eligible(self.stand_in(0.1, 0.3)))
        self.assertFalse(Mixin.military_demand_eligible(self.stand_in(0.05, 0.3)))
        self.assertFalse(Mixin.military_demand_eligible(self.stand_in(0.5, 0.2)))


class ConfiscationRisk(unittest.TestCase):
    def stand_in(self, over, protection=0.0, dispersal=None, leverage=0.0):
        return SimpleNamespace(
            _notice_over=lambda threshold: over, STATE_NOTICE_THRESHOLD_CONFISCATION=0.8,
            effect_best=lambda effect: None if dispersal is None else (None, {"flat": dispersal}),
            CONFISCATION_MAX_RATE=0.28, CONFISCATION_PROTECTION_DISCOUNT=0.5, CONFISCATION_MILITARY_USEFULNESS_DISCOUNT=0.4,
            state=SimpleNamespace(household=SimpleNamespace(protection=protection)), military_leverage=lambda: leverage,
            CONFISCATION_PROTECTION_LABELS=Mixin.CONFISCATION_PROTECTION_LABELS)

    def test_short_of_the_confiscation_line_there_is_no_risk(self):
        self.assertEqual(Mixin.confiscation_risk(self.stand_in(0.0)), (0.0, []))

    def test_unprotected_the_chance_is_the_maximum_rate_scaled_by_the_distance_past_the_line(self):
        self.assertAlmostEqual(Mixin.confiscation_risk(self.stand_in(0.5))[0], 0.14)
        self.assertEqual(Mixin.confiscation_risk(self.stand_in(0.5))[1], [])

    def test_dispersal_held_cuts_the_chance_and_is_named(self):
        chance, held = Mixin.confiscation_risk(self.stand_in(0.5, dispersal=0.5))
        self.assertAlmostEqual(chance, 0.07)
        self.assertEqual(held, [Mixin.CONFISCATION_PROTECTION_LABELS[1]])

    def test_protection_and_usefulness_are_each_named_in_the_order_of_the_labels(self):
        _chance, held = Mixin.confiscation_risk(self.stand_in(0.5, protection=0.5, leverage=0.5))
        self.assertEqual(held, [Mixin.CONFISCATION_PROTECTION_LABELS[0], Mixin.CONFISCATION_PROTECTION_LABELS[2]])


if __name__ == "__main__":
    unittest.main()
