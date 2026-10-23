"""Complaint 485, the rules: supply, attrition, battle, siege, march and conquest level each take built inputs and
call the rule. No game is built."""

QUICK_TOPIC = True

import random
import unittest

from sim.agents import army_raising
from sim.geography import tile_owners
from sim.world import battle, campaign_attrition, campaign_contest, campaign_supply, military_logistics
from sim.world.army_record import Army, fielded_soldiers

REFERENCE_KG = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()
RICH_TILE_KCAL = 5e10     # a tile's yearly food energy
GRAIN_KCAL = military_logistics.GRAIN_ENERGY_KCAL_PER_KG


def army(soldiers=1000.0, equipment=REFERENCE_KG, food=0.0, animals=0.0, owner="a", tile="t1", army_id="x"):
    return Army(army_id, owner, tile, soldiers, equipment, food_kg=food, animals=animals, home_tile=tile)


class SupplyTests(unittest.TestCase):

    def test_a_columns_delivery_falls_with_distance_and_ends_at_its_range(self):
        near = campaign_supply.carriage_kg_per_day(100.0, 1.0)
        far = campaign_supply.carriage_kg_per_day(100.0, 6.0)
        self.assertGreater(near, far)
        self.assertGreater(far, 0.0)
        self.assertEqual(campaign_supply.carriage_kg_per_day(100.0, campaign_supply.carriage_range_days() + 1.0), 0.0)

    def test_the_range_does_not_depend_on_how_many_animals(self):
        one, many = (campaign_supply.carriage_kg_per_day(count, 4.0) for count in (1.0, 50.0))
        self.assertAlmostEqual(many / one, 50.0)

    def test_a_tile_gives_a_share_of_its_yearly_food_and_what_is_taken_comes_off(self):
        full = campaign_supply.tile_stock_kg(RICH_TILE_KCAL, 0.0)
        self.assertAlmostEqual(full, RICH_TILE_KCAL * campaign_supply.SEIZABLE_SHARE_OF_TILE_FOOD / GRAIN_KCAL)
        half = campaign_supply.tile_stock_kg(RICH_TILE_KCAL, campaign_supply.kcal_of(full / 2.0))
        self.assertAlmostEqual(half, full / 2.0)
        self.assertEqual(campaign_supply.tile_stock_kg(RICH_TILE_KCAL, 1e30), 0.0)

    def test_an_army_eats_land_then_column_then_its_stock_and_is_short_when_all_fail(self):
        need = campaign_supply.daily_need_kg(1000.0) * 10.0
        fed = campaign_supply.feed(1000.0, 10.0, 0.0, need, 0.0, 0.0)
        self.assertEqual(fed.fed_share, 1.0)
        self.assertAlmostEqual(fed.taken_forage_kg, need)
        mixed = campaign_supply.feed(1000.0, 10.0, need / 4.0, need / 4.0, need / 4.0, 0.0)
        self.assertAlmostEqual(mixed.fed_share, 0.75)
        self.assertEqual(mixed.stock_after_kg, 0.0)
        hungry = campaign_supply.feed(1000.0, 10.0, 0.0, 0.0, 0.0, 0.0)
        self.assertEqual(hungry.fed_share, 0.0)

    def test_spare_land_and_column_grain_refills_the_stock_up_to_what_the_animals_carry(self):
        need = campaign_supply.daily_need_kg(1000.0) * 5.0
        fed = campaign_supply.feed(1000.0, 5.0, 0.0, need * 3.0, 0.0, need)
        self.assertEqual(fed.fed_share, 1.0)
        self.assertAlmostEqual(fed.stock_after_kg, need)
        self.assertAlmostEqual(fed.taken_forage_kg, 2.0 * need)


class AttritionTests(unittest.TestCase):

    def test_a_fed_army_on_a_healthy_tile_with_its_pay_loses_nobody(self):
        lost = campaign_attrition.losses(1000.0, 100.0, 1.0, 0.0, 0.0)
        self.assertEqual(sum(lost.values()), 0.0)

    def test_hunger_costs_in_proportion_to_the_ration_unmet_and_the_days(self):
        half = campaign_attrition.losses(1000.0, 20.0, 0.5, 0.0, 0.0)["hunger"]
        none = campaign_attrition.losses(1000.0, 20.0, 0.0, 0.0, 0.0)["hunger"]
        longer = campaign_attrition.losses(1000.0, 40.0, 0.5, 0.0, 0.0)["hunger"]
        self.assertGreater(none, half)
        self.assertGreater(longer, half)

    def test_a_diseased_tile_costs_more_than_a_clean_one(self):
        sick = campaign_attrition.losses(1000.0, 60.0, 1.0, 0.02, 0.0)["disease"]
        self.assertGreater(sick, 0.0)
        self.assertGreater(sick, campaign_attrition.losses(1000.0, 60.0, 1.0, 0.002, 0.0)["disease"])

    def test_pay_owed_makes_soldiers_desert(self):
        owed = campaign_attrition.losses(1000.0, 90.0, 1.0, 0.0, 1.0)["desertion"]
        self.assertGreater(owed, 0.0)
        self.assertEqual(campaign_attrition.losses(1000.0, 90.0, 1.0, 0.0, 0.0)["desertion"], 0.0)

    def test_all_causes_together_never_take_more_than_the_force(self):
        lost = campaign_attrition.losses(100.0, 5000.0, 0.0, 1.0, 5.0)
        self.assertLessEqual(sum(lost.values()), 100.0 + 1e-9)


class BattleTests(unittest.TestCase):

    def test_better_equipment_counts_for_more_and_a_rifle_burden_far_more(self):
        sword = battle.equipment_quality(REFERENCE_KG, REFERENCE_KG)
        rifle = battle.equipment_quality(
            military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier(military_logistics.MODERN_SERVICE_RIFLE, 10.0),
            REFERENCE_KG)
        self.assertAlmostEqual(sword, 1.0)
        self.assertGreater(rifle, 2.0 * sword)

    def test_strength_is_numbers_times_quality_times_supply_times_terrain(self):
        base = battle.effective_strength(1000.0, REFERENCE_KG, REFERENCE_KG, 1.0, 1.0)
        self.assertAlmostEqual(base, 1000.0)
        self.assertAlmostEqual(battle.effective_strength(1000.0, REFERENCE_KG, REFERENCE_KG, 0.5, 1.0), 500.0)
        self.assertAlmostEqual(battle.effective_strength(1000.0, REFERENCE_KG, REFERENCE_KG, 1.0, 1.4), 1400.0)
        self.assertAlmostEqual(battle.effective_strength(1000.0, 4.0 * REFERENCE_KG, REFERENCE_KG, 1.0, 1.0),
                               1000.0 * 4.0 ** battle.EQUIPMENT_QUALITY_EXPONENT)

    def test_rough_ground_and_works_help_the_defender_flat_ground_does_not(self):
        self.assertEqual(battle.terrain_factor(0.0), 1.0)
        self.assertGreater(battle.terrain_factor(400.0), battle.terrain_factor(100.0))
        self.assertLess(battle.terrain_factor(1e9), 1.0 + battle.TERRAIN_DEFENCE_MAX + 1e-6)
        self.assertGreater(battle.terrain_factor(100.0, 0.5), battle.terrain_factor(100.0))

    def test_the_stronger_side_is_likelier_to_win_but_not_certain(self):
        even = battle.attacker_win_probability(100.0, 100.0)
        self.assertAlmostEqual(even, 0.5)
        stronger = battle.attacker_win_probability(200.0, 100.0)
        self.assertGreater(stronger, 0.5)
        self.assertLess(stronger, 1.0)
        self.assertEqual(battle.attacker_win_probability(0.0, 100.0), 0.0)

    def test_the_draw_not_a_type_decides_the_winner(self):
        low = battle.fight(150.0, 100.0, 1000.0, 1000.0, 0.01)
        high = battle.fight(150.0, 100.0, 1000.0, 1000.0, 0.99)
        self.assertTrue(low.attacker_won)
        self.assertFalse(high.attacker_won)
        self.assertEqual(low.attacker_win_probability, high.attacker_win_probability)

    def test_both_sides_lose_men_and_the_loser_loses_more(self):
        won = battle.fight(150.0, 100.0, 1000.0, 1000.0, 0.01)
        self.assertGreater(won.attacker_lost, 0.0)
        self.assertGreater(won.defender_lost, won.attacker_lost)
        lost = battle.fight(150.0, 100.0, 1000.0, 1000.0, 0.99)
        self.assertGreater(lost.attacker_lost, 0.0)
        self.assertGreater(lost.defender_lost, 0.0)
        self.assertGreater(lost.attacker_lost, won.attacker_lost)

    def test_an_underfed_army_loses_a_battle_it_would_have_won(self):
        site = campaign_contest.Site("t1", RICH_TILE_KCAL)
        fed, hungry = army(1000.0), army(1000.0)
        hungry.supply_state = 0.4
        foe = army(800.0, owner="b")
        self.assertGreater(campaign_contest.strength_of(fed, REFERENCE_KG), campaign_contest.strength_of(foe, REFERENCE_KG))
        self.assertLess(campaign_contest.strength_of(hungry, REFERENCE_KG), campaign_contest.strength_of(foe, REFERENCE_KG))
        outcome = campaign_contest.engage(hungry, foe, site, REFERENCE_KG, 0.5)
        self.assertFalse(outcome.attacker_won)
        self.assertLess(hungry.soldiers, 1000.0)
        self.assertLess(foe.soldiers, 800.0)


class SiegeTests(unittest.TestCase):

    def small_stores_site(self, days_of_food_for_defenders, defenders):
        stock_kg = campaign_supply.daily_need_kg(defenders) * days_of_food_for_defenders
        kcal = campaign_supply.kcal_of(stock_kg) / campaign_supply.SEIZABLE_SHARE_OF_TILE_FOOD
        return campaign_contest.Site("t1", kcal)

    def test_shut_in_defenders_eat_the_tiles_stores_and_go_hungry_when_they_are_gone(self):
        site = self.small_stores_site(30.0, 1000.0)
        defenders = army(1000.0, owner="b")
        campaign_contest.camp(defenders, 20.0, site, 0.0, 0.0)
        self.assertEqual(defenders.supply_state, 1.0)
        campaign_contest.camp(defenders, 20.0, site, 0.0, 0.0)
        self.assertLess(defenders.supply_state, 1.0)
        self.assertGreater(site.drawn_kcal, 0.0)

    def test_the_siege_waits_while_the_defence_is_stronger_then_the_storm_comes_when_stores_fail(self):
        site = self.small_stores_site(45.0, 800.0)
        site.ruggedness, site.fortification = 300.0, 0.5
        besiegers, defenders = army(1000.0, food=1e9, animals=250.0), army(800.0, owner="b")
        first = campaign_contest.siege_turn(besiegers, defenders, site, 0.0, REFERENCE_KG, 0.99)
        self.assertEqual(first["result"], "continues")
        self.assertEqual(first["defender_fed"], 1.0)
        second = campaign_contest.siege_turn(besiegers, defenders, site, 0.0, REFERENCE_KG, 0.0)
        self.assertLess(second["defender_fed"], 1.0)
        for _ in range(4):
            if second["result"] != "continues":
                break
            second = campaign_contest.siege_turn(besiegers, defenders, site, 0.0, REFERENCE_KG, 0.0)
        self.assertEqual(second["result"], "attacker_won")
        self.assertLess(defenders.soldiers, 800.0)

    def test_a_besieger_that_cannot_feed_itself_goes_home(self):
        site = campaign_contest.Site("t1", 0.0)
        besiegers, defenders = army(1000.0, food=0.0), army(500.0, owner="b", food=1e9)
        turn = campaign_contest.siege_turn(besiegers, defenders, site, 0.0, REFERENCE_KG, 0.5)
        self.assertEqual(turn["result"], "attacker_withdraws")

    def test_a_column_from_held_tiles_keeps_a_besieger_fed_where_the_land_gives_nothing(self):
        site = campaign_contest.Site("t1", 0.0)
        animals = 400.0
        per_day = campaign_supply.carriage_kg_per_day(animals, 3.0)
        self.assertGreater(per_day, campaign_supply.daily_need_kg(1000.0))
        besiegers, defenders = army(1000.0, animals=animals), army(500.0, owner="b", food=1e9)
        turn = campaign_contest.siege_turn(besiegers, defenders, site, per_day, REFERENCE_KG, 0.5)
        self.assertEqual(turn["attacker_fed"], 1.0)
        self.assertGreater(turn["carriage_taken_kg"], 0.0)

    def test_armies_on_one_tile_fight_as_one_and_share_the_losses_out(self):
        first, second = army(600.0, food=100.0, army_id="a1"), army(400.0, food=300.0, army_id="a2")
        combined = campaign_contest.combine([first, second])
        self.assertEqual(combined.soldiers, 1000.0)
        combined.soldiers = 500.0
        combined.food_kg = 200.0
        campaign_contest.share_out([first, second], 1000.0, combined)
        self.assertAlmostEqual(first.soldiers + second.soldiers, 500.0)
        self.assertAlmostEqual(first.food_kg + second.food_kg, 200.0)


class MarchAndCampTests(unittest.TestCase):

    def test_an_army_finishes_the_legs_its_days_reach_and_is_part_way_into_the_next(self):
        steps, progress, used = campaign_contest.march([("a", 10.0), ("b", 15.0), ("c", 20.0)], 0.0, 30.0)
        self.assertEqual([tile for tile, _ in steps], ["a", "b"])
        self.assertAlmostEqual(progress, 5.0)
        self.assertAlmostEqual(used, 30.0)

    def test_days_already_marched_on_a_leg_count_toward_it(self):
        steps, progress, used = campaign_contest.march([("a", 10.0)], 6.0, 30.0)
        self.assertEqual(steps, [("a", 4.0)])
        self.assertAlmostEqual(used, 4.0)

    def test_legs_come_from_a_route_with_handling_and_waiting_added(self):
        legs = campaign_contest.legs_of({"legs": [{"to": "a", "days": 3.0, "handling_days": 1.0, "wait_days": 2.0},
                                                  {"to": "b", "days": 4.0}]})
        self.assertEqual(legs, [("a", 6.0), ("b", 4.0)])

    def test_camping_feeds_from_the_land_and_strikes_the_dead_off(self):
        site = campaign_contest.Site("t1", RICH_TILE_KCAL, disease_per_year=0.05)
        host = army(1000.0, animals=250.0)
        result = campaign_contest.camp(host, 30.0, site, 0.0, 0.0)
        self.assertEqual(result["fed_share"], 1.0)
        self.assertLess(host.soldiers, 1000.0)
        self.assertGreater(host.food_kg, 0.0)
        self.assertGreater(site.drawn_kcal, 0.0)


class ConquestAndDefenceTests(unittest.TestCase):

    def test_a_tile_is_held_at_the_conquest_level_and_rises_with_the_years_held(self):
        levels = tile_owners.control_levels()
        taken = tile_owners.conquest_level(0.0)
        later = tile_owners.conquest_level(1000.0)
        self.assertIn(taken, levels)
        self.assertGreater(levels[later]["rank"], levels[taken]["rank"])
        self.assertEqual(tile_owners.conquest_level(None), taken)

    def test_a_raise_is_refused_unless_the_soldiers_are_free_and_the_tile_is_yours(self):
        self.assertIsNone(army_raising.raise_refusal(100.0, 500.0, "a", "a", True))
        for requested, free, tile_owner, known, cause in (
                (0.0, 500.0, "a", True, "army_size_not_positive"), (100.0, 50.0, "a", True, "not_enough_soldiers"),
                (100.0, 500.0, "b", True, "tile_not_yours"), (100.0, 500.0, "a", False, "unknown_tile")):
            self.assertEqual(army_raising.raise_refusal(requested, free, tile_owner, "a", known).cause, cause)

    def test_the_field_armies_are_a_slice_of_the_force_and_their_dead_come_off_it(self):
        records = {"1": army(300.0, army_id="1").to_dict(), "2": army(200.0, owner="b", army_id="2").to_dict()}
        self.assertEqual(fielded_soldiers(records, "a"), 300.0)
        self.assertEqual(army_raising.available_soldiers(1000.0, 300.0), 700.0)
        self.assertEqual(army_raising.struck_from_force(1000.0, 120.0), 880.0)

    def test_pay_owed_falls_to_an_army_by_head_and_is_read_in_years_of_its_pay(self):
        owed = army_raising.pay_owed_share(1000.0, 5000.0, 1000.0)
        self.assertAlmostEqual(owed, 200.0)
        self.assertAlmostEqual(army_raising.pay_owed_years(owed, 1000.0, 0.4), 0.5)
        self.assertEqual(army_raising.pay_owed_years(owed, 0.0, 0.4), 0.0)

    def test_a_state_defends_its_threatened_tile_with_its_free_army_and_never_attacks(self):
        owners = {"mine1": "a", "mine2": "a", "theirs": "b"}
        records = {"h": army(500.0, owner="b", tile="theirs", army_id="h").to_dict(),
                   "g": army(300.0, owner="a", tile="mine1", army_id="g").to_dict()}
        records["h"]["target"] = "mine2"
        self.assertEqual(army_raising.threats_to("a", owners, records), {"mine2": 500.0})
        self.assertEqual(army_raising.defence_orders("a", owners, records), [("g", "mine2")])
        self.assertEqual(army_raising.defence_orders("b", owners, records), [])
        self.assertEqual(army_raising.defence_musters("a", owners, records, 800.0), [("mine2", 500.0)])
        self.assertEqual(army_raising.defence_musters("a", owners, records, 200.0), [("mine2", 200.0)])

    def test_the_same_seed_gives_the_same_battle(self):
        draws = [random.Random(7).random() for _ in range(2)]
        outcomes = [battle.fight(120.0, 100.0, 500.0, 500.0, draw) for draw in draws]
        self.assertEqual(outcomes[0], outcomes[1])


if __name__ == "__main__":
    unittest.main()
