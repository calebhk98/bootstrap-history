"""The yearly campaign phase's world rules (`world/campaign_year_rules.py`), one function per test on written-out armies, tiles,
food and treasury. The module's steps that call them are in test_campaigns_module; the world rules of battle and supply are
in test_campaign_rules."""
QUICK_TOPIC = True

import unittest

from sim.geography import tile_owners
from sim.world import campaign_supply, campaign_year_rules as rules
from sim.world.army_record import Army

SEASON = campaign_supply.CAMPAIGN_SEASON_DAYS
LEVELS = tile_owners.control_levels()


def army(soldiers=1000.0, owner="rome", tile="t_home", army_id="a1", food=0.0, target=None, home="t_home"):
    made = Army(army_id, owner, tile, soldiers, 10.0, food_kg=food, home_tile=home)
    made.target = target
    return made


class MarchCampsTests(unittest.TestCase):

    def test_the_legs_the_days_reach_are_camped_and_the_walk_into_the_next_is_camped_on_the_last_tile(self):
        camps, progress, used = rules.march_camps([("a", 10.0), ("b", 15.0), ("c", 20.0)], 0.0, 30.0)
        self.assertEqual(camps, [("a", 10.0), ("b", 15.0), (None, 5.0)])
        self.assertAlmostEqual(progress, 5.0)
        self.assertAlmostEqual(used, 30.0)

    def test_an_army_that_ends_the_season_on_a_tile_has_no_part_leg(self):
        camps, progress, used = rules.march_camps([("a", 10.0), ("b", 20.0)], 0.0, 30.0)
        self.assertEqual(camps, [("a", 10.0), ("b", 20.0)])
        self.assertAlmostEqual(used, 30.0)

    def test_days_already_marched_on_a_leg_count_toward_it(self):
        camps, progress, used = rules.march_camps([("a", 10.0)], 6.0, 30.0)
        self.assertEqual(camps, [("a", 4.0)])
        self.assertAlmostEqual(used, 4.0)


class BookLossesTests(unittest.TestCase):

    def test_each_cause_is_added_to_the_owners_dead_and_a_whole_soldier_is_logged(self):
        host, lost = army(), {"rome": 5.0, "han": 1.0}
        rules.book_losses(host, {"hunger": 12.4, "disease": 0.4, "desertion": 3.0}, lost)
        self.assertAlmostEqual(lost["rome"], 5.0 + 12.4 + 0.4 + 3.0)
        self.assertEqual(lost["han"], 1.0)
        self.assertEqual(host.log, [{"kind": "hunger", "tile": "t_home", "soldiers": 12},
                                    {"kind": "desertion", "tile": "t_home", "soldiers": 3}])


class ForceShareTests(unittest.TestCase):

    def test_armies_within_the_force_are_all_kept(self):
        self.assertEqual(rules.share_of_force_kept(300.0, 300.0), 1.0)
        self.assertEqual(rules.share_of_force_kept(300.0, 900.0), 1.0)

    def test_armies_over_the_force_are_stood_down_by_the_same_share(self):
        self.assertAlmostEqual(rules.share_of_force_kept(400.0, 100.0), 0.25)
        self.assertEqual(rules.share_of_force_kept(400.0, -50.0), 0.0)

    def test_a_record_shrinks_in_men_grain_animals_and_pay_owed_but_not_its_equipment(self):
        record = {"soldiers": 400.0, "food_kg": 80.0, "animals": 20.0, "pay_owed": 40.0, "equipment_kg": 10.0}
        rules.scale_army_record(record, 0.25)
        self.assertEqual(record, {"soldiers": 100.0, "food_kg": 20.0, "animals": 5.0, "pay_owed": 10.0,
                                  "equipment_kg": 10.0})


class ContestActionTests(unittest.TestCase):

    def test_a_won_tile_or_one_with_no_defenders_is_taken(self):
        self.assertEqual(rules.contest_action("attacker_won"), "take")
        self.assertEqual(rules.contest_action("defenders_gone"), "take")

    def test_a_lost_or_abandoned_siege_withdraws_the_attacker(self):
        self.assertEqual(rules.contest_action("attacker_lost"), "withdraw")
        self.assertEqual(rules.contest_action("attacker_withdraws"), "withdraw")

    def test_a_siege_that_continues_changes_nothing(self):
        self.assertIsNone(rules.contest_action("continues"))

    def test_a_garrison_is_the_free_soldiers_by_the_tiles_share_of_the_peoples(self):
        self.assertAlmostEqual(rules.garrison_strength(800.0, 0.25), 200.0)
        self.assertEqual(rules.garrison_strength(800.0, 0.0), 0.0)


class WithdrawAndRoutTests(unittest.TestCase):

    def test_a_withdrawn_army_drops_its_order_and_falls_back_home_if_home_is_still_its_owners(self):
        host = army(tile="t_far", target="t_further", home="t_home")
        host.progress_days = 7.0
        rules.withdraw(host, "attacker_lost", True)
        self.assertEqual((host.tile, host.target, host.progress_days), ("t_home", None, 0.0))
        self.assertEqual(host.log, [{"kind": "withdrew", "tile": "t_far", "why": "attacker_lost"}])

    def test_a_withdrawn_army_whose_home_is_lost_stays_where_it_stands(self):
        host = army(tile="t_far", target="t_further")
        rules.withdraw(host, "attacker_withdraws", False)
        self.assertEqual((host.tile, host.target), ("t_far", None))

    def test_a_routed_defender_falls_back_to_its_home_tile_and_stays_in_the_field(self):
        host = army(tile="t_far", target="t_x", home="t_home")
        self.assertFalse(rules.rout(host, True))
        self.assertEqual((host.tile, host.target, host.progress_days), ("t_home", None, 0.0))

    def test_a_routed_defender_with_no_home_to_go_to_is_stood_down(self):
        self.assertTrue(rules.rout(army(tile="t_far", home="t_home"), False))
        self.assertTrue(rules.rout(army(tile="t_home", home="t_home"), True))
        self.assertTrue(rules.rout(army(tile="t_far", home=""), True))


class ConsolidationTests(unittest.TestCase):

    def entry(self, year=100):
        return rules.conquest_entry(year, "rome", "han")

    def settle(self, current_owner="rome", garrisoned=True, year=100, current_level=None):
        return rules.consolidation(self.entry(), current_owner, garrisoned, year, current_level, LEVELS,
                                   tile_owners.conquest_level)

    def test_the_record_of_a_taking_names_the_year_the_taker_and_the_loser(self):
        self.assertEqual(self.entry(), {"year": 100, "by": "rome", "from": "han"})

    def test_a_tile_that_changed_hands_is_forgotten(self):
        self.assertEqual(self.settle(current_owner="han"), (False, None))
        self.assertEqual(self.settle(current_owner=None), (False, None))

    def test_a_tile_held_with_an_army_on_it_is_set_to_the_level_its_years_earn(self):
        keep, level = self.settle(year=100 + 1000, current_level=None)
        self.assertTrue(keep)
        self.assertEqual(level, tile_owners.conquest_level(1000.0))

    def test_a_tile_nobody_garrisons_is_kept_on_record_but_does_not_rise(self):
        self.assertEqual(self.settle(garrisoned=False, year=100 + 1000), (True, None))

    def test_a_tile_already_at_a_higher_level_is_never_lowered(self):
        top = max(LEVELS, key=lambda name: LEVELS[name]["rank"])
        self.assertEqual(self.settle(year=100, current_level=top), (True, None))


if __name__ == "__main__":
    unittest.main()
