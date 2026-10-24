"""The yearly campaign phase, one function per test on written-out armies, tiles, food and treasury: the rules between the
world rules (`world/campaign_year_rules.py`), each step of `CampaignYearMixin` on a stand-in that holds only what it reads,
and the order `step_campaigns` calls them in, with recorders for every collaborator. The world rules themselves are in
test_campaign_rules."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents import army_raising
from sim.engine import campaign_year
from sim.engine.campaign_year import CampaignYearMixin
from sim.geography import tile_owners
from sim.world import campaign_contest, campaign_supply, campaign_year_rules as rules
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


class CampStandIn(CampaignYearMixin):
    """What a Sim gives the campaign methods: sites, a column, the year's draw record and owners."""

    def __init__(self, site_food=0.0, stock_kg_per_day=0.0, owners=None, arrears=0.0, force=5000.0, wage=10.0):
        self.site_food, self.column, self.arrears, self.force, self.wage = site_food, stock_kg_per_day, arrears, force, wage
        self.store = {"drawn": {}, "armies": {}, "held_since": {}}
        self.owners = owners or {}
        self.calls = []
        self.state = types.SimpleNamespace(scenario=types.SimpleNamespace(year=120))

    def campaign_store(self):
        return self.store

    def campaign_site(self, tile):
        return campaign_contest.Site(tile, self.site_food, self.store["drawn"].get(tile, 0.0))

    def campaign_column(self, host, modes):
        return self.column, None

    def tile_owner(self, tile):
        return self.owners.get(tile)

    def owner_force(self, owner):
        return self.force

    def owner_world(self, owner):
        government = types.SimpleNamespace(record=types.SimpleNamespace(arrears={"army": self.arrears}))
        return types.SimpleNamespace(government=lambda: government, pay_per_person_year=lambda kind: self.wage)


class CampTests(unittest.TestCase):

    def test_an_army_on_a_rich_tile_eats_the_land_and_the_draw_is_recorded_against_the_tile(self):
        game, host, lost = CampStandIn(site_food=5e10), army(1000.0), {}
        game._camp(host, 30.0, [], 0.0, lost)
        self.assertEqual(host.supply_state, 1.0)
        self.assertGreater(game.store["drawn"]["t_home"], 0.0)
        self.assertNotIn("hunger", [entry["kind"] for entry in host.log])

    def test_an_army_with_no_land_column_or_stock_goes_hungry_and_loses_men(self):
        game, host, lost = CampStandIn(site_food=0.0), army(1000.0, food=0.0), {}
        game._camp(host, 30.0, [], 0.0, lost)
        self.assertEqual(host.supply_state, 0.0)
        self.assertLess(host.soldiers, 1000.0)
        self.assertGreater(lost["rome"], 0.0)
        self.assertIn("hunger", [entry["kind"] for entry in host.log])

    def test_an_army_with_its_own_grain_eats_it_instead_of_losing_men_to_hunger(self):
        fed, starving = army(1000.0, food=1e6), army(1000.0, food=0.0)
        game = CampStandIn(site_food=0.0)
        game._camp(fed, 30.0, [], 0.0, {})
        game._camp(starving, 30.0, [], 0.0, {})
        self.assertEqual(fed.supply_state, 1.0)
        self.assertLess(fed.food_kg, 1e6)
        self.assertGreater(fed.soldiers, starving.soldiers)

    def test_unpaid_soldiers_desert(self):
        paid, unpaid = army(1000.0), army(1000.0, army_id="a2")
        game = CampStandIn(site_food=5e10)
        game._camp(paid, 30.0, [], 0.0, {})
        game._camp(unpaid, 30.0, [], 2.0, {})
        self.assertGreater(paid.soldiers, unpaid.soldiers)


class PayYearsTests(unittest.TestCase):

    def test_pay_owed_falls_to_an_army_by_head_and_is_read_in_years_of_its_pay(self):
        game, host = CampStandIn(arrears=1000.0, force=5000.0, wage=10.0), army(1000.0)
        years = game._pay_years(host)
        self.assertAlmostEqual(host.pay_owed, 200.0)
        self.assertAlmostEqual(years, 200.0 / (1000.0 * 10.0))

    def test_no_arrears_owe_nothing(self):
        game, host = CampStandIn(arrears=0.0), army(1000.0)
        self.assertEqual(game._pay_years(host), 0.0)
        self.assertEqual(host.pay_owed, 0.0)

    def test_an_army_of_no_soldiers_costs_nothing(self):
        game, host = CampStandIn(arrears=1000.0), army(0.0)
        self.assertEqual(game._pay_years(host), 0.0)
        self.assertEqual(host.pay_owed, 0.0)


class TakeAndHoldTests(unittest.TestCase):

    def test_a_tile_taken_changes_hands_at_the_conquest_level_and_is_recorded_as_held_since(self):
        game, host = CampStandIn(), army(tile="t_border")
        transfers = []
        game.take_captives_from_conquest = lambda *args: transfers.append(("captives", args))
        game.transfer_tile = lambda tile, owner, level, cause: transfers.append(("transfer", tile, owner, level, cause)) or "han"
        with mock.patch.object(campaign_year.contact_events, "after_conquest") as after:
            game._take(host, "han", {})
        self.assertEqual(transfers, [("captives", ("rome", "han", "t_border")),
                                     ("transfer", "t_border", "rome", tile_owners.conquest_level(0.0), "conquest")])
        self.assertEqual(game.store["held_since"], {"t_border": {"year": 120, "by": "rome", "from": "han"}})
        self.assertEqual(host.log, [{"kind": "conquest", "tile": "t_border", "from": "han"}])
        after.assert_called_once_with(game, "rome", "han", "t_border")

    def test_a_tile_held_with_an_army_on_it_rises_in_control_and_one_left_empty_does_not(self):
        game = CampStandIn(owners={"t_held": "rome", "t_empty": "rome"})
        game.store["held_since"] = {"t_held": rules.conquest_entry(100, "rome", "han"),
                                    "t_empty": rules.conquest_entry(100, "rome", "han")}
        game.state.scenario.year = 1100
        set_calls = {}
        controls = types.SimpleNamespace(get=lambda tile: None, set=lambda tile, level: set_calls.update({tile: level}))
        game.stores = types.SimpleNamespace(view=lambda name: controls)
        game.army_records = lambda: {"a1": army(tile="t_held").to_dict()}
        game._consolidate_conquests()
        self.assertEqual(set_calls, {"t_held": tile_owners.conquest_level(1000.0)})
        self.assertEqual(sorted(game.store["held_since"]), ["t_empty", "t_held"])

    def test_a_tile_lost_again_leaves_the_held_record(self):
        game = CampStandIn(owners={"t_held": "han"})
        game.store["held_since"] = {"t_held": rules.conquest_entry(100, "rome", "han")}
        game.stores = types.SimpleNamespace(view=lambda name: types.SimpleNamespace(get=lambda tile: None))
        game.army_records = lambda: {}
        game._consolidate_conquests()
        self.assertEqual(game.store["held_since"], {})


class PhaseOrderStandIn(CampStandIn):
    """Every collaborator of `step_campaigns` is a recorder."""

    def __init__(self, armies):
        super().__init__()
        self.store["armies"] = armies
        self.calls = []

    def _defend(self, armies):
        self.calls.append(("defend", sorted(armies)))

    def _campaign_army(self, host, armies, lost, references):
        self.calls.append(("army", host.army_id))
        lost[host.owner] = lost.get(host.owner, 0.0) + 7.0
        if host.army_id == "a2":
            host.soldiers = 0.0

    def strike_from_force(self, owner, killed):
        self.calls.append(("strike", owner, killed))

    def _keep_within_force(self, owners):
        self.calls.append(("keep", owners))

    def _consolidate_conquests(self):
        self.calls.append(("consolidate",))


class StepCampaignsTests(unittest.TestCase):

    def test_the_phase_defends_then_moves_armies_in_id_order_then_strikes_the_dead_then_keeps_within_force_then_consolidates(self):
        game = PhaseOrderStandIn({"a3": army(300.0, army_id="a3").to_dict(), "a1": army(100.0, army_id="a1").to_dict(),
                                  "a2": army(200.0, army_id="a2").to_dict()})
        game.store["drawn"] = {"old": 1.0}
        game.step_campaigns()
        self.assertEqual(game.calls, [("defend", ["a1", "a2", "a3"]), ("army", "a1"), ("army", "a2"), ("army", "a3"),
                                      ("strike", "rome", 21.0), ("keep", ["rome"]), ("consolidate",)])
        self.assertEqual(game.store["drawn"], {})

    def test_an_army_reduced_below_one_soldier_is_not_kept_in_the_record(self):
        game = PhaseOrderStandIn({"a1": army(100.0, army_id="a1").to_dict(), "a2": army(200.0, army_id="a2").to_dict()})
        game.step_campaigns()
        self.assertEqual(sorted(game.store["armies"]), ["a1"])

    def test_with_no_armies_nothing_is_called_and_the_years_draw_is_cleared(self):
        game = PhaseOrderStandIn({})
        game.store["drawn"] = {"old": 1.0}
        game.step_campaigns()
        self.assertEqual(game.calls, [])
        self.assertEqual(game.store["drawn"], {})


class ArmyOrderStandIn(CampStandIn):
    def __init__(self, owners):
        super().__init__(owners=owners)
        self.calls = []
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace(improvements={}))
        self.world_map = object()

    def _reference_equipment(self, owner):
        self.calls.append(("reference", owner))
        return 1.0

    def campaign_modes(self, owner):
        self.calls.append(("modes", owner))
        return ["foot"]

    def _pay_years(self, host):
        self.calls.append(("pay", host.army_id))
        return 0.5

    def held_and_running(self):
        return set()

    def _camp(self, host, days, modes, pay_years, lost):
        self.calls.append(("camp", host.tile, days, pay_years))

    def _contest(self, host, armies, defender, days_left, modes, pay_years, lost, reference):
        self.calls.append(("contest", host.tile, defender, days_left))


class CampaignArmyTests(unittest.TestCase):

    def run_army(self, host, owners, found):
        game = ArmyOrderStandIn(owners)
        with mock.patch.object(campaign_year, "route", return_value=found):
            game._campaign_army(host, {host.army_id: host}, {}, {})
        return game

    def test_an_army_marches_the_routes_legs_camping_on_each_and_feeds_from_home_at_the_end(self):
        found = {"legs": [{"to": "t_a", "days": 10.0}, {"to": "t_b", "days": 15.0}]}
        host = army(tile="t_home", target="t_b")
        game = self.run_army(host, {"t_home": "rome", "t_a": "rome", "t_b": "rome"}, found)
        self.assertEqual(game.calls, [("reference", "rome"), ("modes", "rome"), ("pay", "a1"),
                                      ("camp", "t_a", 10.0, 0.5), ("camp", "t_b", 15.0, 0.5)])
        self.assertEqual((host.tile, host.target, host.progress_days, host.supply_state), ("t_b", None, 0.0, 1.0))

    def test_an_army_part_way_along_a_leg_when_the_season_ends_keeps_its_progress_and_order(self):
        found = {"legs": [{"to": "t_a", "days": SEASON * 3}]}
        host = army(tile="t_home", target="t_a")
        game = self.run_army(host, {"t_home": "rome", "t_a": "rome"}, found)
        self.assertEqual(game.calls[-1], ("camp", "t_home", SEASON, 0.5))
        self.assertAlmostEqual(host.progress_days, SEASON)
        self.assertEqual((host.tile, host.target), ("t_home", "t_a"))

    def test_no_route_drops_the_order_with_a_log_line_and_no_camp(self):
        host = army(tile="t_home", target="t_far")
        game = self.run_army(host, {"t_home": "rome"}, None)
        self.assertEqual([call[0] for call in game.calls], ["reference", "modes", "pay"])
        self.assertIsNone(host.target)
        self.assertEqual(host.log, [{"kind": "no_route", "tile": "t_home", "target": "t_far"}])

    def test_an_army_standing_on_another_owners_tile_contests_it_with_the_days_the_march_left(self):
        found = {"legs": [{"to": "t_enemy", "days": 20.0}]}
        host = army(tile="t_home", target="t_enemy")
        game = self.run_army(host, {"t_home": "rome", "t_enemy": "han"}, found)
        self.assertEqual(game.calls[-2:], [("camp", "t_enemy", 20.0, 0.5), ("contest", "t_enemy", "han", SEASON - 20.0)])

    def test_an_army_in_unowned_country_camps_the_rest_of_the_season_off_the_land(self):
        host = army(tile="t_wild", target=None)
        game = self.run_army(host, {}, None)
        self.assertEqual(game.calls[-1], ("camp", "t_wild", SEASON, 0.5))

    def test_an_army_with_no_soldiers_left_does_nothing_on_the_ground(self):
        host = army(0.0, tile="t_enemy")
        game = self.run_army(host, {"t_enemy": "han"}, None)
        self.assertEqual([call[0] for call in game.calls], ["reference", "modes", "pay"])


if __name__ == "__main__":
    unittest.main()
