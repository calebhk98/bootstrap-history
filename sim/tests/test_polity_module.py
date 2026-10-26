"""The polity module on plain values: what each command it applies writes, the seat's year of standing, and the rules the year
and the views take (protection, visible scale, familiarity, the scandal warning band). No game."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.polity import constants, rules
from sim.polity.api import (AddGovernance, AddReputation, AddScandal, GainReputation, RaiseScandal, RecordBribe, RecordRising,
                            RegisterPeople, ReplaceRuler, ResetStateUnrest, ScaleFamiliarity, ScaleProtection, SetReputation,
                            SetTileReading, ShiftValueWeight, StrikeFromForce)
from sim.polity.state import PolitySeat
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, polity_host


class SeatCommands(unittest.TestCase):
    def test_a_scandal_raised_moves_last_years_mark_with_it_and_an_added_one_does_not(self):
        seat = PolitySeat(scandal=4.0, scandal_last_year=4.0)
        module = polity_host.build(seat=seat)
        module.raise_scandal(RaiseScandal(3.0))
        self.assertEqual((seat.scandal, seat.scandal_last_year), (7.0, 7.0))
        module.add_scandal(AddScandal(1.0))
        self.assertEqual((seat.scandal, seat.scandal_last_year), (8.0, 7.0))

    def test_protection_and_familiarity_are_multiplied_by_the_share(self):
        seat = PolitySeat(protection=0.8, familiarity=0.5)
        module = polity_host.build(seat=seat)
        module.scale_protection(ScaleProtection(0.5))
        module.scale_familiarity(ScaleFamiliarity(0.5))
        self.assertEqual((seat.protection, seat.familiarity), (0.4, 0.25))

    def test_reputation_gain_stops_at_the_ceiling_and_a_plain_addition_does_not(self):
        seat = PolitySeat(reputation=9.5)
        module = polity_host.build(seat=seat, legacy_constant=lambda name: {"REPUTATION_CEILING": 10.0}[name])
        module.gain_reputation(GainReputation(2.0))
        self.assertEqual(seat.reputation, 10.0)
        module.add_reputation(AddReputation(2.0))
        self.assertEqual(seat.reputation, 12.0)
        module.set_reputation(SetReputation(1.0))
        self.assertEqual(seat.reputation, 1.0)

    def test_governance_standing_rises_by_what_the_work_serves(self):
        seat = PolitySeat()
        polity_host.build(seat=seat).add_governance(AddGovernance(1.5))
        self.assertEqual(seat.gov, 1.5)

    def test_a_bribe_sets_the_figures_and_works_protection_out_again_from_them(self):
        seat = PolitySeat(reputation=0.0)
        module = polity_host.build(seat=seat, revenue_estimate=100.0)
        module.record_bribe(RecordBribe(2.5, 60.0))
        self.assertEqual((seat.scandal, seat.bribes_ytd), (2.5, 60.0))
        self.assertGreater(seat.protection, 0.0)
        self.assertLessEqual(seat.protection, constants.PROTECTION_CEILING)


class ValueWeights(unittest.TestCase):
    def test_a_weight_moves_by_the_delta_and_is_held_between_the_floor_and_the_ceiling(self):
        weights = {"w_novelty": 0.9}
        module = polity_host.build(legacy_value_weights=weights)
        self.assertEqual(module.shift_value_weight(ShiftValueWeight("w_novelty", 0.1)), (0.9, 1.0))
        before, after = module.shift_value_weight(ShiftValueWeight("w_novelty", 100.0))
        self.assertEqual(after, weights["w_novelty"])
        self.assertGreater(after, 1.0)

    def test_a_weight_the_society_lacks_is_refused_with_a_cause(self):
        answer = polity_host.build(legacy_value_weights={}).shift_value_weight(ShiftValueWeight("w_nothing", 0.1))
        self.assertIsInstance(answer, Refusal)
        self.assertEqual(answer.cause, "not_a_value_weight")


class StateRecords(unittest.TestCase):
    def module(self):
        record = SimpleNamespace(registered_people={"a": 5.0}, unrest_by_tile={"x": 1.0}, hold_by_tile={"x": 1.0}, risings=[1, 2],
                                 ruler_age=0, ruler_backer="", accession_due=False, army=0.0, land_taken_by_tile={})
        world = SimpleNamespace(government=lambda: SimpleNamespace(record=record), soldiers_under_arms=lambda: 100)
        return polity_host.build(country_world=lambda owner: world), record

    def test_people_are_registered_by_the_larger_count(self):
        module, record = self.module()
        module.register_people(RegisterPeople("rome", {"a": 3.0, "b": 9.0}))
        self.assertEqual(record.registered_people, {"a": 5.0, "b": 9.0})

    def test_the_year_of_unrest_starts_again_and_a_tile_is_read(self):
        module, record = self.module()
        module.reset_state_unrest(ResetStateUnrest("rome"))
        self.assertEqual((record.unrest_by_tile, record.hold_by_tile), ({}, {}))
        module.set_tile_reading(SetTileReading("rome", "t", 0.3, 0.7))
        self.assertEqual((record.unrest_by_tile, record.hold_by_tile), ({"t": 0.3}, {"t": 0.7}))

    def test_risings_keep_the_latest_and_a_won_one_puts_a_new_ruler_on_the_throne(self):
        module, record = self.module()
        module.record_rising(RecordRising("rome", 3, 2))
        self.assertEqual(record.risings, [2, 3])
        module.replace_ruler(ReplaceRuler("rome", 30, "the army"))
        self.assertEqual((record.ruler_age, record.ruler_backer, record.accession_due), (30, "the army", True))

    def test_soldiers_lost_in_the_field_come_off_the_army_line(self):
        module, record = self.module()
        module.strike_from_force(StrikeFromForce("rome", 10.0))
        self.assertEqual(record.army, 90.0)


class YearOfStanding(unittest.TestCase):
    def test_the_year_opens_with_scandal_marked(self):
        seat = PolitySeat(scandal=6.0)
        polity_host.build(seat=seat).step_begin_seat_year("founder")
        self.assertEqual(seat.scandal_last_year, 6.0)

    def test_reputation_decays_toward_what_the_work_alone_earns_and_familiarity_follows_the_years_known(self):
        seat = PolitySeat(reputation=60.0)
        module = polity_host.build(seat=seat, standing_floor=20.0, year=140)
        module.renew_standing()
        self.assertEqual(seat.reputation, 20.0 + 40.0 * polity_host.CONSTANTS["REPUTATION_DECAY_TOWARD_FLOOR"])
        self.assertGreater(seat.familiarity, 0.0)

    def test_a_year_that_closes_without_trouble_decays_scandal_and_bribes_and_sends_no_event(self):
        seat = PolitySeat(scandal=10.0, bribes_ytd=8.0)
        module = polity_host.build(seat=seat, standing_floor=0.0, events_enabled=False, revenue_estimate=1.0)
        module.close_standing_year()
        self.assertEqual(seat.scandal, 10.0 * polity_host.CONSTANTS["SCANDAL_DECAY_RATE"])
        self.assertEqual(seat.bribes_ytd, 8.0 * polity_host.CONSTANTS["BRIBES_YTD_DECAY"])
        self.assertEqual([c for c in module_harness.sent(module) if isinstance(c, RecordEvent)], [])

    def test_scandal_past_the_line_with_the_means_is_bribed_down_and_paid_for(self):
        seat = PolitySeat(scandal=50.0)
        module = polity_host.build(seat=seat, acting_balance=10000.0, events_enabled=False, revenue_estimate=1.0)
        module.close_standing_year()
        spent = [c for c in module_harness.sent(module) if c.__class__.__name__ == "PayEdge"]
        self.assertEqual(len(spent), 1)
        self.assertLess(seat.scandal, 50.0 * polity_host.CONSTANTS["SCANDAL_DECAY_RATE"])
        self.assertGreater(seat.bribes_ytd, 0.0)


class Rules(unittest.TestCase):
    def test_protection_is_capped_and_each_of_its_parts_adds(self):
        base = rules.protection_total(0.0, False, 0.0, 0.0, 1.0, 0.5)
        self.assertEqual(base, 0.0)
        self.assertGreater(rules.protection_total(0.0, True, 0.0, 0.0, 1.0, 0.5), base)
        self.assertGreater(rules.protection_total(0.0, False, 50.0, 0.0, 1.0, 0.5), base)
        self.assertGreater(rules.protection_total(0.0, False, 0.0, 10.0, 1.0, 0.5), base)
        self.assertEqual(rules.protection_total(5.0, True, 1000.0, 1.0e6, 1.0, 1.0), constants.PROTECTION_CEILING)

    def test_a_larger_household_is_more_visible_and_a_defiant_one_more_still(self):
        small = rules.visible_scale(10.0, 1000.0, 1.0, 0.0, 100.0, 1.0)
        self.assertLess(small, rules.visible_scale(400.0, 1000.0, 1.0, 0.0, 100.0, 1.0))
        self.assertLess(small, rules.visible_scale(10.0, 1000.0, 1.0, 0.2, 100.0, 1.0))
        self.assertEqual(rules.visible_scale(1.0e9, 1.0e18, 1.0e9, 5.0, 100.0, 1.0), 1.0)

    def test_familiarity_rises_with_years_known_and_stops_at_its_ceiling(self):
        first = rules.familiarity_after(0.1, 0, 5.0, 0.9, 0.05, 0.01)
        self.assertLess(first, rules.familiarity_after(0.1, 0, 50.0, 0.9, 0.05, 0.01))
        self.assertEqual(rules.familiarity_after(10.0, 100, 1000.0, 0.9, 0.05, 0.01), 0.9)

    def test_scandal_is_announced_once_per_band_past_three_quarters_of_the_line_and_forgotten_below_half(self):
        self.assertEqual(rules.scandal_warning_band(80.0, 100.0, 0), (5, 5))
        self.assertEqual(rules.scandal_warning_band(80.0, 100.0, 5), (None, 5))
        self.assertEqual(rules.scandal_warning_band(60.0, 100.0, 5), (None, 5))
        self.assertEqual(rules.scandal_warning_band(40.0, 100.0, 5), (None, 0))

    def test_the_legitimacy_share_is_held_between_the_floor_and_the_ceiling(self):
        self.assertEqual(rules.legitimacy_share(1.0, 0.5, 1.25), 1.0)
        self.assertEqual(rules.legitimacy_share(-5.0, 0.5, 1.25), 0.5)
        self.assertEqual(rules.legitimacy_share(5.0, 0.5, 1.25), 1.25)


if __name__ == "__main__":
    unittest.main()
