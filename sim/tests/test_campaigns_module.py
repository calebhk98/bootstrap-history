"""The campaigns module on plain values (Complaints 485, 648, 484, 486): raising, ordering, recalling and disbanding an army, the
camp and the march, a tile taken and held, the order the campaign phase calls its steps in, captives, and what a rising does to
the state. Each test builds the module with `module_harness` and plain views for what it reads, and reads the commands it sent.
The rules it calls are in test_campaigns_rules, test_campaign_year_rules and test_stability_rules."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.actors.api import RecordConquestContact
from sim.agents import api as agents_api
from sim.campaigns import captives as captives_module, stability
from sim.campaigns.commands import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy
from sim.campaigns.module import Campaigns
from sim.campaigns.state import CampaignsWorld
from sim.demography.api import AddCaptives
from sim.geography import tile_owners
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.polity.api import (CloseSuccessionDispute, RecordRising, ReplaceRuler, StrikeFromForce)
from sim.agents import revolt
from sim.stores.api import WriteStore
from sim.tests import module_harness
from sim.world import campaign_supply, campaign_year_rules
from sim.world.army_record import Army

OWNER, RIVAL = "rome", "han"
HOME, BORDER, THEIRS = "t_home", "t_border", "t_theirs"
SEASON = campaign_supply.CAMPAIGN_SEASON_DAYS


def army(soldiers=1000.0, owner=OWNER, tile=HOME, army_id="a1", food=0.0, target=None, home=HOME):
    made = Army(army_id, owner, tile, soldiers, 10.0, food_kg=food, home_tile=home)
    made.target = target
    return made


def country_world(force=1000.0, equipment=12.5, arrears=0.0, wage=10.0, population=1000.0):
    government = SimpleNamespace(record=SimpleNamespace(army=force, arrears={"army": arrears}))
    return SimpleNamespace(equipment_kg_per_soldier=lambda: equipment, soldiers_under_arms=lambda: force,
                           government=lambda: government, pay_per_person_year=lambda kind: wage,
                           population_total=lambda: population, rng_for=lambda *key: SimpleNamespace(random=lambda: 0.25))


def build(module_class=Campaigns, owners=None, force=1000.0, site_food=0.0, arrears=0.0, population=1000.0, answers=None,
          extra=None, **world_arguments):
    """The module on plain views: a force for OWNER and RIVAL, who holds which tile, a map of four tiles."""
    owners = {HOME: OWNER, BORDER: OWNER, THEIRS: RIVAL} if owners is None else owners
    forces = {OWNER: force, RIVAL: 400.0}
    on_map = {HOME, BORDER, THEIRS, "t_unowned"}
    views = {
        "tile_owner": lambda tile: owners.get(tile),
        "tiles_owned_by": lambda owner: sorted(tile for tile, holder in owners.items() if holder == owner),
        "tile_facts": lambda tile: {"food_kcal_per_year": site_food, "working_age_endemic_loss": 0.0, "ruggedness": 0.0}
        if tile in on_map else None,
        "has_state": lambda owner: owner in forces,
        "country_world": lambda owner: country_world(forces[owner], arrears=arrears, population=population),
        "reach_from": lambda tile, modes, days: {},
        "civilisation": lambda: {"id": OWNER},
        "year": 100,
    }
    views.update(extra or {})
    return module_harness.build(module_class, views=views, answers=answers, world=CampaignsWorld(**world_arguments)), owners


def place(module, soldiers=300.0, owner=OWNER, tile=HOME, army_id="army_1", target=None):
    made = Army(army_id, owner, tile, soldiers, 12.5, home_tile=tile)
    made.target = target
    module.world.armies[army_id] = made.to_dict()
    return made


class RaisingAnArmy(unittest.TestCase):

    def test_a_raised_army_is_recorded_with_its_owner_tile_soldiers_and_equipment(self):
        module, _ = build()
        made = module.apply_raise_army(RaiseArmy(OWNER, 300.0, HOME))
        self.assertEqual((made.owner, made.tile, made.soldiers, made.equipment_kg, made.raised_year), (OWNER, HOME, 300.0, 12.5, 100))
        self.assertEqual(module.world.armies, {made.army_id: made.to_dict()})

    def test_free_soldiers_are_the_force_less_the_armies_in_the_field(self):
        module, _ = build()
        place(module, soldiers=300.0)
        self.assertEqual(module.free_soldiers(OWNER), 700.0)

    def test_the_armies_view_holds_the_owners_armies_and_its_free_soldiers(self):
        module, _ = build()
        place(module, soldiers=300.0)
        place(module, soldiers=50.0, owner=RIVAL, army_id="army_2")
        answer = module.armies_of_owner(OWNER)
        self.assertEqual(([found.army_id for found in answer["armies"]], answer["free_soldiers"]), (["army_1"], 700.0))

    def test_the_army_gets_the_next_id_and_the_counter_moves_on(self):
        module, _ = build(next_id=7)
        made = module.raise_army(OWNER, 100.0, HOME)
        self.assertEqual((made.army_id, module.world.next_id), ("army_7", 8))

    def test_more_than_the_free_soldiers_is_refused_with_a_cause_and_changes_nothing(self):
        module, _ = build()
        place(module, soldiers=600.0)
        refused = module.raise_army(OWNER, 401.0, HOME)
        self.assertEqual(refused.cause, "not_enough_soldiers")
        self.assertEqual(len(module.world.armies), 1)

    def test_a_tile_that_is_not_the_owners_or_not_on_the_map_is_refused(self):
        module, _ = build()
        self.assertEqual(module.raise_army(OWNER, 100.0, THEIRS).cause, "tile_not_yours")
        self.assertEqual(module.raise_army(OWNER, 100.0, "nowhere").cause, "unknown_tile")
        self.assertEqual(module.world.armies, {})

    def test_with_no_tile_named_the_army_is_raised_on_a_tile_the_owner_holds(self):
        module, _ = build()
        self.assertIn(module.raise_army(OWNER, 100.0).tile, (HOME, BORDER))

    def test_a_bare_owner_with_no_state_keeps_no_soldiers(self):
        module, _ = build()
        self.assertEqual(module.owner_force("nobody"), 0.0)

    def test_soldiers_who_die_in_the_field_are_struck_from_the_owners_army_line_by_a_command(self):
        module, _ = build()
        module.strike_from_force(OWNER, 120.0)
        module.strike_from_force("nobody", 50.0)
        module.strike_from_force(OWNER, -5.0)
        self.assertEqual(module_harness.sent(module), [StrikeFromForce(OWNER, 120.0)])


class OrdersAndStandingDown(unittest.TestCase):

    def setUp(self):
        self.module, self.owners = build()
        self.army = place(self.module)

    def test_an_order_sets_the_target_and_clears_progress(self):
        self.module.world.armies[self.army.army_id]["progress_days"] = 3.0
        ordered = self.module.apply_order_army(OrderArmy(OWNER, self.army.army_id, THEIRS))
        self.assertEqual((ordered.target, ordered.progress_days), (THEIRS, 0.0))
        self.assertEqual(self.module.army_of(self.army.army_id).target, THEIRS)

    def test_an_order_to_where_it_stands_clears_the_target(self):
        place(self.module, target=THEIRS)
        self.assertIsNone(self.module.order_army(OWNER, self.army.army_id, HOME).target)

    def test_an_order_to_a_tile_off_the_map_is_refused(self):
        self.assertEqual(self.module.order_army(OWNER, self.army.army_id, "nowhere").cause, "unknown_tile")

    def test_another_actor_cannot_give_the_army_orders_or_disband_it(self):
        self.assertEqual(self.module.order_army(RIVAL, self.army.army_id, THEIRS).cause, "not_your_army")
        self.assertEqual(self.module.apply_disband_army(DisbandArmy(RIVAL, self.army.army_id)).cause, "not_your_army")
        self.assertEqual(len(self.module.world.armies), 1)

    def test_an_unknown_army_is_refused_with_the_owners_armies_as_choices(self):
        refused = self.module.order_army(OWNER, "army_99", THEIRS)
        self.assertEqual((refused.cause, refused.choices), ("unknown_army", ["army_1"]))

    def test_recall_sends_the_army_back_to_the_tile_it_was_raised_on(self):
        place(self.module, tile=BORDER)
        self.module.world.armies["army_1"]["home_tile"] = HOME
        self.assertEqual(self.module.apply_recall_army(RecallArmy(OWNER, "army_1")).target, HOME)

    def test_a_recall_to_a_lost_home_tile_goes_to_a_tile_the_owner_still_holds(self):
        place(self.module, tile=THEIRS)
        self.module.world.armies["army_1"]["home_tile"] = HOME
        self.owners[HOME] = RIVAL
        self.assertEqual(self.module.recall_army(OWNER, "army_1").target, BORDER)

    def test_an_owner_who_holds_nothing_has_no_tile_to_recall_to(self):
        place(self.module, tile=THEIRS)
        self.module.world.armies["army_1"]["home_tile"] = HOME
        self.owners.clear()
        self.assertEqual(self.module.recall_army(OWNER, "army_1").cause, "no_tile_to_return_to")

    def test_disbanding_removes_the_armys_record_and_hands_it_back(self):
        disbanded = self.module.disband_army(OWNER, self.army.army_id)
        self.assertEqual(self.module.world.armies, {})
        self.assertEqual(disbanded.army_id, self.army.army_id)


class CampTests(unittest.TestCase):

    def test_an_army_on_a_rich_tile_eats_the_land_and_the_draw_is_recorded_against_the_tile(self):
        module, _ = build(site_food=5e10)
        host, lost = army(1000.0), {}
        module._camp(host, 30.0, [], 0.0, lost)
        self.assertEqual(host.supply_state, 1.0)
        self.assertGreater(module.world.drawn[HOME], 0.0)
        self.assertNotIn("hunger", [entry["kind"] for entry in host.log])

    def test_an_army_with_no_land_column_or_stock_goes_hungry_and_loses_men(self):
        module, _ = build(site_food=0.0)
        host, lost = army(1000.0, food=0.0), {}
        module._camp(host, 30.0, [], 0.0, lost)
        self.assertEqual(host.supply_state, 0.0)
        self.assertLess(host.soldiers, 1000.0)
        self.assertGreater(lost[OWNER], 0.0)
        self.assertIn("hunger", [entry["kind"] for entry in host.log])

    def test_an_army_with_its_own_grain_eats_it_instead_of_losing_men_to_hunger(self):
        fed, starving = army(1000.0, food=1e6), army(1000.0, food=0.0)
        module, _ = build(site_food=0.0)
        module._camp(fed, 30.0, [], 0.0, {})
        module._camp(starving, 30.0, [], 0.0, {})
        self.assertEqual(fed.supply_state, 1.0)
        self.assertLess(fed.food_kg, 1e6)
        self.assertGreater(fed.soldiers, starving.soldiers)

    def test_unpaid_soldiers_desert(self):
        paid, unpaid = army(1000.0), army(1000.0, army_id="a2")
        module, _ = build(site_food=5e10)
        module._camp(paid, 30.0, [], 0.0, {})
        module._camp(unpaid, 30.0, [], 2.0, {})
        self.assertGreater(paid.soldiers, unpaid.soldiers)

    def test_the_column_brings_grain_from_the_nearest_owned_tile_that_has_some(self):
        module, _ = build(site_food=5e10, extra={"reach_from": lambda tile, modes, days: {BORDER: 3.0, HOME: 1.0, THEIRS: 0.5}})
        host = army(1000.0, tile=HOME)
        host.animals = 50.0
        per_day, source = module.campaign_column(host, [])
        self.assertEqual(source, HOME)
        self.assertGreater(per_day, 0.0)


class PayYearsTests(unittest.TestCase):

    def test_pay_owed_falls_to_an_army_by_head_and_is_read_in_years_of_its_pay(self):
        module, _ = build(force=5000.0, arrears=1000.0)
        host = army(1000.0)
        years = module._pay_years(host)
        self.assertAlmostEqual(host.pay_owed, 200.0)
        self.assertAlmostEqual(years, 200.0 / (1000.0 * 10.0))

    def test_no_arrears_owe_nothing(self):
        module, _ = build(force=5000.0, arrears=0.0)
        host = army(1000.0)
        self.assertEqual(module._pay_years(host), 0.0)
        self.assertEqual(host.pay_owed, 0.0)

    def test_an_army_of_no_soldiers_costs_nothing(self):
        module, _ = build(force=5000.0, arrears=1000.0)
        host = army(0.0)
        self.assertEqual(module._pay_years(host), 0.0)
        self.assertEqual(host.pay_owed, 0.0)


class TakeAndHoldTests(unittest.TestCase):

    def test_a_tile_taken_changes_hands_at_the_conquest_level_and_is_recorded_as_held_since(self):
        module, _ = build(owners={}, answers={TransferTile: "han"})
        host = army(tile=BORDER)
        module._take(host, RIVAL, {})
        self.assertEqual(module_harness.sent(module), [
            TransferTile(BORDER, OWNER, "conquest", tile_owners.conquest_level(0.0)),
            RecordConquestContact(OWNER, RIVAL, BORDER)])
        self.assertEqual(module.world.held_since, {BORDER: {"year": 100, "by": OWNER, "from": RIVAL}})
        self.assertEqual(host.log, [{"kind": "conquest", "tile": BORDER, "from": RIVAL}])

    def test_a_tile_taken_first_takes_the_captives_of_the_tile_it_still_holds(self):
        module, _ = build(owners={BORDER: RIVAL}, answers={TransferTile: "han", AddCaptives: lambda command: command.people})
        with mock.patch.object(captives_module.settlement, "population_share", lambda owned, tile: 0.5):
            module._take(army(tile=BORDER), RIVAL, {})
        kinds = [type(command) for command in module_harness.sent(module)]
        self.assertEqual(kinds, [AddCaptives, RecordWorldEvent, TransferTile, RecordConquestContact])

    def consolidate(self, held_since, year, owners, armies, controls=None):
        module, _ = build(owners=owners, extra={"year": year, "store": lambda name: {"default": None, "values": controls or {}}})
        module.world.held_since = held_since
        module.world.armies = armies
        module._consolidate_conquests()
        return module

    def test_a_tile_held_with_an_army_on_it_rises_in_control_and_one_left_empty_does_not(self):
        entry = campaign_year_rules.conquest_entry(100, OWNER, RIVAL)
        module = self.consolidate({"t_held": dict(entry), "t_empty": dict(entry)}, 1100, {"t_held": OWNER, "t_empty": OWNER},
                                  {"a1": army(tile="t_held").to_dict()})
        self.assertEqual(module_harness.sent(module), [WriteStore("control", "t_held", tile_owners.conquest_level(1000.0))])
        self.assertEqual(sorted(module.world.held_since), ["t_empty", "t_held"])

    def test_a_tile_lost_again_leaves_the_held_record(self):
        module = self.consolidate({"t_held": campaign_year_rules.conquest_entry(100, OWNER, RIVAL)}, 120, {"t_held": RIVAL}, {})
        self.assertEqual((module.world.held_since, module_harness.sent(module)), ({}, []))


class Recording(Campaigns):
    """Every collaborator of the phase is a recorder."""

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

    def run_phase(self, armies):
        module, _ = build(Recording)
        module.calls = []
        module.world.armies = armies
        module.world.drawn = {"old": 1.0}
        module.step_campaigns([])
        return module

    def test_the_phase_defends_then_moves_armies_in_id_order_then_strikes_the_dead_then_keeps_within_force_then_consolidates(self):
        module = self.run_phase({"a3": army(300.0, army_id="a3").to_dict(), "a1": army(100.0, army_id="a1").to_dict(),
                                 "a2": army(200.0, army_id="a2").to_dict()})
        self.assertEqual(module.calls, [("defend", ["a1", "a2", "a3"]), ("army", "a1"), ("army", "a2"), ("army", "a3"),
                                        ("strike", OWNER, 21.0), ("keep", [OWNER]), ("consolidate",)])
        self.assertEqual(module.world.drawn, {})

    def test_an_army_reduced_below_one_soldier_is_not_kept_in_the_record(self):
        module = self.run_phase({"a1": army(100.0, army_id="a1").to_dict(), "a2": army(200.0, army_id="a2").to_dict()})
        self.assertEqual(sorted(module.world.armies), ["a1"])

    def test_with_no_armies_nothing_is_called_and_the_years_draw_is_cleared(self):
        module = self.run_phase({})
        self.assertEqual(module.calls, [])
        self.assertEqual(module.world.drawn, {})


class MarchingRecording(Campaigns):

    def _reference_equipment(self, owner):
        self.calls.append(("reference", owner))
        return 1.0

    def campaign_modes(self, owner):
        self.calls.append(("modes", owner))
        return ["foot"]

    def _pay_years(self, host):
        self.calls.append(("pay", host.army_id))
        return 0.5

    def _camp(self, host, days, modes, pay_years, lost):
        self.calls.append(("camp", host.tile, days, pay_years))

    def _contest(self, host, armies, defender, days_left, modes, pay_years, lost, reference):
        self.calls.append(("contest", host.tile, defender, days_left))


class CampaignArmyTests(unittest.TestCase):

    def run_army(self, host, owners, found):
        module, _ = build(MarchingRecording, owners=owners, extra={"route_between": lambda origin, target, modes: found})
        module.calls = []
        module._campaign_army(host, {host.army_id: host}, {}, {})
        return module

    def test_an_army_marches_the_routes_legs_camping_on_each_and_feeds_from_home_at_the_end(self):
        found = {"legs": [{"to": "t_a", "days": 10.0}, {"to": "t_b", "days": 15.0}]}
        host = army(tile=HOME, target="t_b")
        module = self.run_army(host, {HOME: OWNER, "t_a": OWNER, "t_b": OWNER}, found)
        self.assertEqual(module.calls, [("reference", OWNER), ("modes", OWNER), ("pay", "a1"),
                                        ("camp", "t_a", 10.0, 0.5), ("camp", "t_b", 15.0, 0.5)])
        self.assertEqual((host.tile, host.target, host.progress_days, host.supply_state), ("t_b", None, 0.0, 1.0))

    def test_an_army_part_way_along_a_leg_when_the_season_ends_keeps_its_progress_and_order(self):
        found = {"legs": [{"to": "t_a", "days": SEASON * 3}]}
        host = army(tile=HOME, target="t_a")
        module = self.run_army(host, {HOME: OWNER, "t_a": OWNER}, found)
        self.assertEqual(module.calls[-1], ("camp", HOME, SEASON, 0.5))
        self.assertAlmostEqual(host.progress_days, SEASON)
        self.assertEqual((host.tile, host.target), (HOME, "t_a"))

    def test_no_route_drops_the_order_with_a_log_line_and_no_camp(self):
        host = army(tile=HOME, target="t_far")
        module = self.run_army(host, {HOME: OWNER}, None)
        self.assertEqual([call[0] for call in module.calls], ["reference", "modes", "pay"])
        self.assertIsNone(host.target)
        self.assertEqual(host.log, [{"kind": "no_route", "tile": HOME, "target": "t_far"}])

    def test_an_army_standing_on_another_owners_tile_contests_it_with_the_days_the_march_left(self):
        found = {"legs": [{"to": "t_enemy", "days": 20.0}]}
        host = army(tile=HOME, target="t_enemy")
        module = self.run_army(host, {HOME: OWNER, "t_enemy": RIVAL}, found)
        self.assertEqual(module.calls[-2:], [("camp", "t_enemy", 20.0, 0.5), ("contest", "t_enemy", RIVAL, SEASON - 20.0)])

    def test_an_army_in_unowned_country_camps_the_rest_of_the_season_off_the_land(self):
        host = army(tile="t_wild", target=None)
        module = self.run_army(host, {}, None)
        self.assertEqual(module.calls[-1], ("camp", "t_wild", SEASON, 0.5))

    def test_an_army_with_no_soldiers_left_does_nothing_on_the_ground(self):
        host = army(0.0, tile="t_enemy")
        module = self.run_army(host, {"t_enemy": RIVAL}, None)
        self.assertEqual([call[0] for call in module.calls], ["reference", "modes", "pay"])


class CaptivesTests(unittest.TestCase):

    def captor(self, **arguments):
        return build(owners={"t1": RIVAL, "t2": RIVAL}, answers={AddCaptives: lambda command: command.people}, **arguments)[0]

    def test_the_winner_takes_a_share_of_the_losses_and_the_log_names_both_sides_and_the_cause(self):
        module = self.captor()
        taken = module.take_captives_from_battle(OWNER, RIVAL, 1000.0, "t1")
        self.assertAlmostEqual(taken, agents_api.captives_from_losses(1000.0))
        self.assertEqual(module_harness.sent(module), [
            AddCaptives(OWNER, taken),
            RecordWorldEvent("captives", actors=(OWNER, RIVAL), tiles=("t1",), cause="battle", facts={"people": taken})])

    def test_no_losses_take_no_captives_and_log_nothing(self):
        module = self.captor()
        self.assertEqual(module.take_captives_from_battle(OWNER, RIVAL, 0.0, "t1"), 0.0)
        self.assertEqual(module_harness.sent(module), [])

    def test_a_winner_with_no_bonded_stratum_takes_none_and_logs_nothing(self):
        module, _ = build(owners={"t1": RIVAL}, answers={AddCaptives: 0.0})
        self.assertEqual(module.take_captives_from_battle(OWNER, RIVAL, 1000.0, "t1"), 0.0)
        self.assertEqual(len(module_harness.sent(module)), 1)

    def test_a_conquered_tile_gives_a_share_of_the_people_standing_on_it(self):
        module = self.captor(population=2000.0)
        with mock.patch.object(captives_module.settlement, "population_share", lambda owned, tile: 0.25):
            taken = module.take_captives_from_conquest(OWNER, RIVAL, "t1")
        self.assertAlmostEqual(taken, agents_api.captives_from_conquest(500.0))
        event = module_harness.sent(module)[1]
        self.assertEqual((event.cause, event.actors, event.tiles), ("conquest", (OWNER, RIVAL), ("t1",)))

    def test_a_tile_the_loser_does_not_hold_gives_nothing(self):
        module = self.captor()
        self.assertEqual(module.take_captives_from_conquest(OWNER, RIVAL, "elsewhere"), 0.0)
        self.assertEqual(module_harness.sent(module), [])

    def test_a_loser_with_no_state_gives_nothing(self):
        module, _ = build(owners={"t1": "bare"})
        self.assertEqual(module.take_captives_from_conquest(OWNER, "bare", "t1"), 0.0)
        self.assertEqual(module_harness.sent(module), [])


def outcome(kind, rising_lost=3.0, garrison_lost=7.0, probability=0.6):
    return SimpleNamespace(kind=kind, rising_win_probability=probability, rising_lost=rising_lost, garrison_lost=garrison_lost)


class RisingTests(unittest.TestCase):

    def rise(self, kind, on_seat=False, cause="unrest", challenger="faction_a"):
        module, _ = build()
        record = SimpleNamespace(succession_challenger=challenger)
        world = SimpleNamespace(rng_for=lambda *key: SimpleNamespace(random=lambda: 0.25))
        with mock.patch.object(stability.revolt, "resolve", return_value=outcome(kind)) as resolve, \
                mock.patch.object(stability.ruler, "opening_age", return_value=21):
            result = module._rising(OWNER, world, record, "tile_a", 12.4, 2.0, SimpleNamespace(soldiers=40.0), 3.0, on_seat, 100, cause)
        return module, resolve, result

    def test_the_rule_is_given_the_risings_soldiers_and_strength_the_garrisons_whether_it_is_the_seat_and_the_tiles_draw(self):
        _, resolve, result = self.rise(revolt.TILE_LOST)
        self.assertEqual(resolve.call_args.args, (12.4, 2.0, 40.0, 3.0, False, 0.25))
        self.assertEqual(result, revolt.TILE_LOST)

    def test_a_won_rising_off_the_seat_is_logged_kept_on_record_strikes_the_garrisons_dead_and_takes_the_tile_from_every_owner(self):
        module, _, _ = self.rise(revolt.TILE_LOST)
        self.assertEqual(module_harness.sent(module), [
            RecordWorldEvent("revolt", actors=(OWNER,), tiles=("tile_a",), cause="unrest", facts={
                "outcome": revolt.TILE_LOST, "rising_win_probability": 0.6, "rising_lost": 3.0, "garrison_lost": 7.0}),
            RecordRising(OWNER, {"year": 100, "tile": "tile_a", "kind": revolt.TILE_LOST, "soldiers": 12}, stability.RISINGS_KEPT),
            StrikeFromForce(OWNER, 7.0),
            TransferTile("tile_a", None, "revolt")])

    def test_a_rising_put_down_changes_no_tile_and_no_ruler(self):
        module, _, _ = self.rise(revolt.PUT_DOWN)
        kinds = [type(command) for command in module_harness.sent(module)]
        self.assertEqual(kinds, [RecordWorldEvent, RecordRising, StrikeFromForce])

    def test_a_won_rising_at_the_seat_replaces_the_ruler_backed_by_the_rising(self):
        module, _, _ = self.rise(revolt.RULER_REPLACED, on_seat=True)
        self.assertEqual(module_harness.sent(module)[-1], ReplaceRuler(OWNER, 21, "rising"))

    def test_a_disputed_accession_won_puts_the_challenger_on_the_throne(self):
        module, _, _ = self.rise(revolt.RULER_REPLACED, on_seat=True, cause="disputed_accession")
        self.assertEqual(module_harness.sent(module)[-1], ReplaceRuler(OWNER, 21, "faction_a"))


class Accession(Campaigns):

    def _rising(self, *arguments):
        self.fought.append(arguments)

    def _garrison_on(self, owner, tile):
        return None

    def campaign_site(self, tile):
        return SimpleNamespace(ruggedness=0.0)

    def tile_fortification(self, tile):
        return 0.0


class DisputedAccessionTests(unittest.TestCase):

    def dispute(self, backing, seat="seat"):
        module, _ = build(Accession)
        module.fought = []
        record = SimpleNamespace(succession_challenger="faction_a")
        world = SimpleNamespace(faction_backing=lambda: backing)
        with mock.patch.object(stability.battle, "terrain_factor", return_value=1.0), \
                mock.patch.object(stability.unrest, "rising_soldiers", return_value=90.0) as soldiers, \
                mock.patch.object(stability.unrest, "rising_strength", return_value=5.0):
            module._disputed_accession(OWNER, world, record, seat, {"seat": 1000.0}, 0.0, 1.0, 100)
        return module, soldiers

    def test_a_challenger_no_faction_backs_raises_no_army_and_is_dropped(self):
        module, _ = self.dispute({"faction_b": 1.0})
        self.assertEqual((module.fought, module_harness.sent(module)), ([], [CloseSuccessionDispute(OWNER)]))

    def test_with_no_seat_there_is_no_accession_to_fight(self):
        module, _ = self.dispute({"faction_a": 1.0}, seat=None)
        self.assertEqual((module.fought, module_harness.sent(module)), ([], [CloseSuccessionDispute(OWNER)]))

    def test_a_backed_challenger_fights_at_the_seat_with_its_share_of_the_backing_and_the_dispute_is_closed(self):
        module, soldiers = self.dispute({"faction_a": 1.0, "faction_b": 3.0})
        self.assertEqual(soldiers.call_args.args, (1000.0, 0.25))
        self.assertEqual((len(module.fought), module.fought[0][3], module.fought[0][-2:]), (1, "seat", (100, "disputed_accession")))
        self.assertEqual(module_harness.sent(module), [CloseSuccessionDispute(OWNER)])


class RecordingStability(Campaigns):

    def _stability_of(self, owner):
        self.risen_against.append(owner)


class StepRevoltsTests(unittest.TestCase):

    def test_the_home_country_is_first_then_the_others_in_id_order_and_a_bare_owner_has_no_state_to_rise_against(self):
        module, _ = build(RecordingStability, extra={"countries": lambda: ["zed", "han", "bare"], "has_state": lambda owner: owner != "bare"})
        module.risen_against = []
        module.step_revolts([])
        self.assertEqual(module.risen_against, [OWNER, "han", "zed"])


if __name__ == "__main__":
    unittest.main()
